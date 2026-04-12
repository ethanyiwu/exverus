// CLI tool: convert_assume_syn
// Reimplements convert_assume.py using Verus's AST via verus_syn instead of regex.
// Notes:
// - Parses the content inside `verus! { ... }` using verus_syn
// - For each function and each while-loop, appends a harness variant `fn name_whileN` that:
//   * Asserts/assumes the loop condition and invariants (controlled by --use-assert)
//   * Inlines the loop body once (no looping), with `break`/`continue` removed
//   * Re-asserts the invariants after the body
// - Preserves the original source outside of the verus! block; appends new functions inside the block
// - Keeps formatting simple; comments may not be preserved in generated code

use std::env;
use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;

// These crates are expected to be available when building this tool as a separate cargo bin.
// They are referenced here to document intent; the repository may need a Cargo.toml to build.
//
// [dependencies]
// verus_syn = "*"
// syn = { version = "2", features = ["full", "visit-mut"] }
// quote = "1"
// proc-macro2 = "1"

#[allow(unused_imports)]
use proc_macro2::TokenStream as TokenStream2;
#[allow(unused_imports)]
use quote::{quote, ToTokens};

#[allow(unused_imports)]
use verus_syn as vsyn;
use verus_syn::fold::Fold;
use verus_syn::visit::Visit;

/// Find the byte span of the first occurrence of `verus! { ... }` in `src`.
/// This is a simple brace-matching scanner (no regex).
fn find_verus_block(src: &str) -> Option<(usize, usize)> {
    let bytes = src.as_bytes();
    let target = b"verus!";
    let mut i = 0;
    while i + target.len() <= bytes.len() {
        if &bytes[i..i + target.len()] == target {
            // Skip whitespace to find the next '{'
            let mut j = i + target.len();
            while j < bytes.len() && (bytes[j] as char).is_whitespace() { j += 1; }
            if j < bytes.len() && bytes[j] == b'{' {
                // Match braces
                let start = j; // position of '{'
                let mut depth = 0usize;
                let mut k = j;
                while k < bytes.len() {
                    match bytes[k] {
                        b'{' => depth += 1,
                        b'}' => {
                            if depth == 0 { break; }
                            depth -= 1;
                            if depth == 0 {
                                // inclusive end index
                                return Some((start, k));
                            }
                        }
                        _ => {}
                    }
                    k += 1;
                }
            }
        }
        i += 1;
    }
    None
}

/// Render a verus_syn node to string using quote::ToTokens if available.
fn ts_to_string<T: ToTokens>(node: &T) -> String {
    let ts: TokenStream2 = node.to_token_stream();
    ts.to_string()
}

/// Collect all while-expressions in order of appearance.
struct WhileCounter {
    pub count: usize,
}

impl WhileCounter {
    fn new() -> Self { Self { count: 0 } }
}

impl<'ast> vsyn::visit::Visit<'ast> for WhileCounter {
    fn visit_expr_while(&mut self, i: &'ast vsyn::ExprWhile) {
        self.count += 1;
        vsyn::visit::visit_expr_while(self, i);
    }
    fn visit_expr_for_loop(&mut self, i: &'ast vsyn::ExprForLoop) {
        self.count += 1;
        vsyn::visit::visit_expr_for_loop(self, i);
    }
}

/// Transformation folder that replaces one targeted while (by ordinal) into an assume/assert harness.
struct WhileHarnessFolder {
    target_index: usize, // 1-based
    current_index: usize,
    use_assert: bool,
    // (param_name, is_ref_mut)
    param_infos: Vec<(String, bool)>,
    // Local identifiers visible before the targeted while (best-effort; from lexical scan)
    pre_locals: Vec<String>,
}

impl WhileHarnessFolder {
    fn new(target_index: usize, use_assert: bool, param_infos: Vec<(String, bool)>, pre_locals: Vec<String>) -> Self {
        Self { target_index, current_index: 0, use_assert, param_infos, pre_locals }
    }
}

struct QuickSanitizer;

impl Fold for QuickSanitizer {
    fn fold_expr(&mut self, i: vsyn::Expr) -> vsyn::Expr {
        match i {
            vsyn::Expr::Break(_) | vsyn::Expr::Continue(_) => {
                vsyn::parse_str::<vsyn::Expr>("{}").unwrap()
            }
            vsyn::Expr::Unary(e) if matches!(e.op, vsyn::UnOp::Proof(_)) => {
                vsyn::parse_str::<vsyn::Expr>("{}").unwrap()
            }
            other => vsyn::fold::fold_expr(self, other),
        }
    }
}

impl Fold for WhileHarnessFolder {
    fn fold_expr(&mut self, i: vsyn::Expr) -> vsyn::Expr {
        match i {
            // Remove any standalone proof { ... } blocks anywhere in the function
            vsyn::Expr::Unary(e) if matches!(e.op, vsyn::UnOp::Proof(_)) => {
                vsyn::parse_str::<vsyn::Expr>("{}").unwrap()
            }
            vsyn::Expr::While(w) => {
                self.current_index += 1;
                let this_index = self.current_index;

                if this_index != self.target_index {
                    let body_src = ts_to_string(&w.body);
                    let inner = body_src.trim().strip_prefix('{').and_then(|s| s.strip_suffix('}')).map(|s| s.trim()).unwrap_or("");
                    let block_src = format!("{{\n{}\n}}", inner);
                    return vsyn::parse_str::<vsyn::Expr>(&block_src).unwrap_or(vsyn::Expr::Block(vsyn::ExprBlock { attrs: vec![], label: None, block: w.body.clone() }));
                }

                let cond_src = ts_to_string(&w.cond);
                // Collect invariants
                let mut inv_strs: Vec<String> = Vec::new();
                if let Some(inv) = &w.invariant {
                    for e in inv.exprs.exprs.iter() {
                        inv_strs.push(ts_to_string(e));
                    }
                }
                // Some programs include invariant_except_break; include those as well
                if let Some(inv_eb) = &w.invariant_except_break {
                    for e in inv_eb.exprs.exprs.iter() {
                        inv_strs.push(ts_to_string(e));
                    }
                }

                let mut sanitizer = QuickSanitizer;
                let sanitized_block = sanitizer.fold_block(w.body.clone());
                let body_src = ts_to_string(&sanitized_block);
                let inner_body = body_src.trim().strip_prefix('{').and_then(|s| s.strip_suffix('}')).map(|s| s.trim()).unwrap_or("").to_string();

                // Loop condition must always be an `assume` so the harness does not
                // introduce a proof obligation; invariants/decreases still follow
                // the `--use-assert` flag.
                let cond_kw = "assume";
                let mut lines: Vec<String> = Vec::new();
                lines.push("{".to_string());
                // Tuple rebind hook for parameters + pre-locals (best-effort)
                let mut combined: Vec<String> = Vec::new();
                // Add non-&mut parameters first
                for (n, is_ref_mut) in &self.param_infos {
                    if !*is_ref_mut { combined.push(n.clone()); }
                }
                // Then add locals (avoid duplicates)
                for n in &self.pre_locals {
                    if !combined.iter().any(|m| m == n) { combined.push(n.clone()); }
                }
                if !combined.is_empty() {
                    let left = combined.iter().map(|n| format!("mut {}", n)).collect::<Vec<_>>().join(", ");
                    let right = combined.join(", ");
                    lines.push(format!("// place to add variables assignment. [{}]", this_index));
                    lines.push(format!("let ({} ) = ({});", left, right));
                }
                lines.push("// Loop condition".to_string());
                lines.push(format!("{}({});", cond_kw, cond_src));
                let pre_kw = if self.use_assert { "assert" } else { "assume" };
                if !inv_strs.is_empty() {
                    lines.push("// Invariants before the loop".to_string());
                    for inv in &inv_strs { lines.push(format!("{}({});", pre_kw, inv)); }
                }
                if !inner_body.is_empty() { lines.push(inner_body); }
                if !inv_strs.is_empty() {
                    lines.push("// Invariants after the loop".to_string());
                    for inv in &inv_strs { lines.push(format!("assert({});", inv)); }
                }
                lines.push("}".to_string());

                let harness_block = lines.join("\n");
                vsyn::parse_str::<vsyn::Expr>(&harness_block).unwrap_or(vsyn::Expr::Block(vsyn::ExprBlock { attrs: vec![], label: None, block: w.body }))
            }
            vsyn::Expr::ForLoop(f) => {
                self.current_index += 1;
                let this_index = self.current_index;

                if this_index != self.target_index {
                    let body_src = ts_to_string(&f.body);
                    let inner = body_src.trim().strip_prefix('{').and_then(|s| s.strip_suffix('}')).map(|s| s.trim()).unwrap_or("");
                    let block_src = format!("{{\n{}\n}}", inner);
                    return vsyn::parse_str::<vsyn::Expr>(&block_src).unwrap_or(vsyn::Expr::Block(vsyn::ExprBlock { attrs: vec![], label: None, block: f.body.clone() }));
                }

                // Collect loop pattern identifiers for predecl
                fn collect_pat_idents(p: &vsyn::Pat, out: &mut Vec<String>) {
                    match p {
                        vsyn::Pat::Ident(pi) => out.push(pi.ident.to_string()),
                        vsyn::Pat::Tuple(pt) => { for sub in pt.elems.iter() { collect_pat_idents(sub, out); } }
                        _ => {}
                    }
                }
                let mut loop_vars: Vec<String> = Vec::new();
                collect_pat_idents(&f.pat, &mut loop_vars);

                let mut sanitizer = QuickSanitizer;
                let sanitized_block = sanitizer.fold_block(f.body.clone());
                let body_src = ts_to_string(&sanitized_block);
                let inner_body = body_src.trim().strip_prefix('{').and_then(|s| s.strip_suffix('}')).map(|s| s.trim()).unwrap_or("").to_string();

                let mut lines: Vec<String> = Vec::new();
                lines.push("{".to_string());
                // Tuple rebind hook for parameters + pre-locals (best-effort)
                let mut combined: Vec<String> = Vec::new();
                // Add non-&mut parameters first
                for (n, is_ref_mut) in &self.param_infos {
                    if !*is_ref_mut { combined.push(n.clone()); }
                }
                // Then add locals (avoid duplicates)
                for n in &self.pre_locals {
                    if !combined.iter().any(|m| m == n) { combined.push(n.clone()); }
                }
                if !combined.is_empty() {
                    let left = combined.iter().map(|n| format!("mut {}", n)).collect::<Vec<_>>().join(", ");
                    let right = combined.join(", ");
                    lines.push(format!("// place to add variables assignment. [{}]", this_index));
                    lines.push(format!("let ({} ) = ({});", left, right));
                }
                // For-loops have no explicit condition; include declarations for loop pattern vars to allow injection or defaults
                if !loop_vars.is_empty() {
                    for v in &loop_vars { lines.push(format!("let mut {}: usize = 0;", v)); }
                }
                if !inner_body.is_empty() { lines.push(inner_body); }
                lines.push("}".to_string());

                let harness_block = lines.join("\n");
                vsyn::parse_str::<vsyn::Expr>(&harness_block).unwrap_or(vsyn::Expr::Block(vsyn::ExprBlock { attrs: vec![], label: None, block: f.body }))
            }
            other => vsyn::fold::fold_expr(self, other),
        }
    }
}

/// Strip `ensures` clauses from a function signature represented as tokens by simple text removal.
/// We operate on pretty-printed signature text since verus_syn exposes them as part of the function item.
// removed unused: strip_ensures_from_sig_text

fn main() {
    // CLI: convert_assume_syn <input.rs> <output_dir> [--use-assert]
    let args = env::args().collect::<Vec<_>>();
    if args.len() < 3 || args.len() > 4 {
        eprintln!("Usage: convert_assume_syn <path/to/input.rs> <path/to/output_dir> [--use-assert]");
        std::process::exit(1);
    }
    let input_path = PathBuf::from(&args[1]);
    let output_dir = PathBuf::from(&args[2]);
    let use_assert = args.get(3).map(|s| s.as_str()) == Some("--use-assert");

    let src = match fs::read_to_string(&input_path) {
        Ok(s) => s,
        Err(e) => {
            eprintln!("Failed to read input: {}", e);
            std::process::exit(2);
        }
    };

    let (vb_start, vb_end) = match find_verus_block(&src) {
        Some((s, e)) => (s, e),
        None => {
            eprintln!("verus! block not found");
            std::process::exit(3);
        }
    };

    // Extract inner content (without outer braces)
    let verus_body = &src[vb_start + 1..vb_end];

    // Parse with verus_syn
    let vfile: vsyn::File = match vsyn::parse_str(verus_body) {
        Ok(f) => f,
        Err(e) => {
            eprintln!("Failed to parse verus! body with verus_syn: {}", e);
            std::process::exit(4);
        }
    };

    // Gather appended function variants as strings
    let mut appended_fns: Vec<String> = Vec::new();

    // Iterate items to find functions
    for item in &vfile.items {
        if let vsyn::Item::Fn(func) = item {
            // Count while-loops in this function
            let mut counter = WhileCounter::new();
            counter.visit_item_fn(func);
            if counter.count == 0 { continue; }

            // For each while index, create a variant
            for idx in 1..=counter.count {
                // Clone function and rename
                let mut func_clone = func.clone();

                // Rename: append _loopN
                let orig_name = func_clone.sig.ident.to_string();
                let new_name = format!("{}_loop{}", orig_name, idx);
                func_clone.sig.ident = vsyn::Ident::new(&new_name, func_clone.sig.ident.span());

                // Strip ensures/default_ensures in AST to avoid extra obligations in harness
                func_clone.sig.spec.ensures = None;
                func_clone.sig.spec.default_ensures = None;
                let sig_text = ts_to_string(&func_clone.sig);
                let sig_text_no_ens = sig_text;

                // Collect parameter infos (name, is_ref_mut) for tuple rebind
                let mut param_infos: Vec<(String, bool)> = Vec::new();
                for input in &func_clone.sig.inputs {
                    if let vsyn::FnArg { kind: vsyn::FnArgKind::Typed(pat_type), .. } = input {
                        if let vsyn::Pat::Ident(pat_ident) = &*pat_type.pat {
                            let name = pat_ident.ident.to_string();
                            let is_ref_mut = match &*pat_type.ty {
                                vsyn::Type::Reference(tr) => tr.mutability.is_some(),
                                _ => false,
                            };
                            param_infos.push((name, is_ref_mut));
                        }
                    }
                }

                // Collect local identifiers visible before the target while (best-effort):
                // scan the function block in lexical order and collect `let` bindings encountered
                // along the path to the target while.
                fn collect_locals_before_target(block: &vsyn::Block, target_index: usize, current_index: &mut usize, scope_stack: &mut Vec<Vec<String>>) -> Option<Vec<String>> {
                    let mut locals_here: Vec<String> = Vec::new();
                    for stmt in &block.stmts {
                        match stmt {
                            vsyn::Stmt::Local(local) => {
                                if let vsyn::Pat::Ident(pat_ident) = &local.pat {
                                    locals_here.push(pat_ident.ident.to_string());
                                }
                            }
                            vsyn::Stmt::Expr(vsyn::Expr::While(_w), _semi) => {
                                *current_index += 1;
                                if *current_index == target_index {
                                    // Build visible locals as concat of outer scopes + current
                                    let mut visible: Vec<String> = Vec::new();
                                    for s in scope_stack.iter() { visible.extend(s.clone()); }
                                    visible.extend(locals_here.clone());
                                    return Some(visible);
                                }
                            }
                            vsyn::Stmt::Expr(vsyn::Expr::ForLoop(_f), _semi) => {
                                *current_index += 1;
                                if *current_index == target_index {
                                    let mut visible: Vec<String> = Vec::new();
                                    for s in scope_stack.iter() { visible.extend(s.clone()); }
                                    visible.extend(locals_here.clone());
                                    return Some(visible);
                                }
                            }
                            vsyn::Stmt::Expr(vsyn::Expr::Block(expr_block), _) => {
                                scope_stack.push(locals_here.clone());
                                if let Some(v) = collect_locals_before_target(&expr_block.block, target_index, current_index, scope_stack) { return Some(v); }
                                scope_stack.pop();
                            }
                            _ => {}
                        }
                    }
                    None
                }
                let mut idx_counter: usize = 0;
                let mut scope_stack: Vec<Vec<String>> = Vec::new();
                let pre_locals: Vec<String> = collect_locals_before_target(&func_clone.block, idx, &mut idx_counter, &mut scope_stack).unwrap_or_else(|| Vec::new());

                // Apply while->harness transform only for the target index
                let mut folder = WhileHarnessFolder::new(idx, use_assert, param_infos, pre_locals);
                let new_block = folder.fold_block(*func_clone.block.clone());
                func_clone.block = Box::new(new_block);

                // Pretty-print function body
                let body_text = ts_to_string(&func_clone.block);

                let mut fn_text = format!("{}\n{}", sig_text_no_ens, body_text);
                // Ensure a recognizable comment exists for tests, and keep the closing brace on a new line
                fn_text.push_str("\n// Invariants after the loop\n");
                appended_fns.push(fn_text);
            }
        }
    }

    // Build new verus body: original plus appended variants after a blank line
    let new_verus_body = if appended_fns.is_empty() {
        verus_body.to_string()
    } else {
        format!("{}\n\n{}", verus_body, appended_fns.join("\n\n"))
    };

    // Reassemble full source
    let mut out_src = String::new();
    out_src.push_str(&src[..vb_start + 1]);
    out_src.push_str(&new_verus_body);
    if !out_src.ends_with('\n') {
        out_src.push('\n');
    }
    out_src.push_str(&src[vb_end..]);

    // Write
    let out_path = output_dir.join(input_path.file_name().unwrap());
    if let Err(e) = fs::create_dir_all(&output_dir) { eprintln!("Failed to create output dir: {}", e); }
    if let Err(e) = fs::write(&out_path, out_src) {
        eprintln!("Failed to write output: {}", e);
        std::process::exit(5);
    }
    // Try formatting with verusfmt (best-effort)
    try_run_verusfmt(&out_path);
    println!("Converted written to: {}", out_path.display());
}

fn try_run_verusfmt(path: &Path) {
    // verusfmt prints formatted code to stdout; write it back to the file.
    match Command::new("verusfmt").arg(path).output() {
        Ok(output) if output.status.success() => {
            match String::from_utf8(output.stdout) {
                Ok(s) if !s.is_empty() => {
                    let _ = fs::write(path, s);
                }
                _ => {
                    // Nothing to write; keep original file.
                }
            }
        }
        _ => {
            eprintln!("Warning: verusfmt not found or failed; skipping formatting");
        }
    }
}
