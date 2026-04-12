// CLI tool: extract_loop_syn
// Extract a single loop (while/for) from a Verus file into a standalone harness file.
// The loop body is converted to a single-step harness where:
//  - For while: loop condition is assumed, invariants are assumed before and asserted after
//  - For for: pattern vars are declared; body is inlined once
//  - proof { ... } blocks, break/continue are removed

use std::env;
use std::fs;
use std::path::PathBuf;
use std::process::Command;
use std::collections::BTreeSet;

use proc_macro2::TokenStream as TokenStream2;
use quote::ToTokens;
use verus_syn as vsyn;
use verus_syn::fold::Fold;
use verus_syn::visit::Visit;
use syn as rustsyn;

fn ts_to_string<T: ToTokens>(node: &T) -> String {
    let ts: TokenStream2 = node.to_token_stream();
    ts.to_string()
}

#[derive(Clone, Copy, PartialEq, Eq)]
enum CheckMode {
    BaseCase,
    Inductiveness,
}

fn find_verus_block(src: &str) -> Option<(usize, usize)> {
    let bytes = src.as_bytes();
    let target = b"verus!";
    let mut i = 0;
    while i + target.len() <= bytes.len() {
        if &bytes[i..i + target.len()] == target {
            let mut j = i + target.len();
            while j < bytes.len() && (bytes[j] as char).is_whitespace() { j += 1; }
            if j < bytes.len() && bytes[j] == b'{' {
                let start = j;
                let mut depth = 0usize;
                let mut k = j;
                while k < bytes.len() {
                    match bytes[k] {
                        b'{' => depth += 1,
                        b'}' => {
                            if depth == 0 { break; }
                            depth -= 1;
                            if depth == 0 { return Some((start, k)); }
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

// Collect `use` items from a verus_syn File, including nested modules
fn collect_uses_from_verus_items(items: &[vsyn::Item], out: &mut BTreeSet<String>) {
    for it in items {
        match it {
            vsyn::Item::Use(u) => {
                out.insert(ts_to_string(u) + ";");
            }
            vsyn::Item::Mod(m) => {
                if let Some((_, content_items)) = &m.content {
                    collect_uses_from_verus_items(content_items, out);
                }
            }
            _ => {}
        }
    }
}

// Naively collect top-level Rust `use ...;` statements from a text snippet.
// This scans by lines and groups multi-line uses until a ';' is encountered.
fn collect_outer_use_statements(_snippet: &str) -> Vec<String> { Vec::new() }

// Collect Rust `use` items from the outer file using the Rust syn parser (not inside verus!).
fn collect_rust_uses_with_syn(full_src: &str) -> Vec<String> {
    fn collect(items: &[rustsyn::Item], out: &mut Vec<String>) {
        for it in items {
            match it {
                rustsyn::Item::Use(u) => { out.push(ts_to_string(u)); }
                rustsyn::Item::Mod(m) => {
                    if let Some((_, content)) = &m.content { collect(content, out); }
                }
                _ => {}
            }
        }
    }
    match rustsyn::parse_file(full_src) {
        Ok(file) => {
            let mut v = Vec::new();
            collect(&file.items, &mut v);
            v
        }
        Err(_) => Vec::new(),
    }
}

// Baseline imports we want in every extracted harness
const BASELINE_IMPORTS: &[&str] = &[
    "vstd::prelude::*",
    "vstd::slice::*",
    "vstd::math::abs",
];

// Ensure required imports exist, without duplicating existing ones
fn ensure_imports(import_set: &mut BTreeSet<String>, required_imports: &[&str]) {
    for req in required_imports {
        let marker_use = format!("use {}", req);
        let marker_pub_use = format!("pub {}", marker_use);
        let exists = import_set.iter().any(|u| u.contains(&marker_use) || u.contains(&marker_pub_use));
        if !exists {
            import_set.insert(format!("{};", marker_use));
        }
    }
}

// Ensure that the last non-empty, non-comment code line ends with a semicolon;
// this is needed because we insert post-body facts after the loop body, so the
// body's final expression can no longer be the block's tail expression.
fn ensure_last_stmt_terminated(snippet: &str) -> String {
    let mut s = snippet.to_string();
    let bytes = s.as_bytes();
    let mut end = s.len();
    while end > 0 && bytes[end - 1].is_ascii_whitespace() { end -= 1; }
    if end == 0 { return s; }

    // Scan lines from the end to find the last line that has code (ignoring // comments and whitespace)
    let mut cursor = end;
    loop {
        let line_start = match s[..cursor].rfind('\n') { Some(p) => p + 1, None => 0 };
        let line = &s[line_start..cursor];
        let code_part_len = match line.find("//") { Some(p) => p, None => line.len() };
        // Trim trailing whitespace from the code part
        let mut code_end = line_start + code_part_len;
        while code_end > line_start && s.as_bytes()[code_end - 1].is_ascii_whitespace() { code_end -= 1; }

        if code_end > line_start {
            // We found the last code. If it does not end with ';', insert one.
            let last_char = s[code_end - 1..code_end].chars().next().unwrap();
            if last_char != ';' {
                s.insert(code_end, ';');
            }
            break;
        } else {
            // This line has no code (only comment/whitespace). Move to previous line.
            if line_start == 0 { break; }
            // Set cursor to the newline before this line to search previous line on next iteration
            cursor = line_start - 1;
        }
    }
    s
}

// Remove specific spec clauses (like requires/ensures) from a function signature string.
// This operates on the textual signature and removes from the keyword until the next
// clause/boundary (another spec kw, where, or the start of the body '{').
// (removed) Previously, we used textual stripping of spec clauses. We now modify the AST directly.

struct LoopCounter { count: usize }
impl LoopCounter { fn new() -> Self { Self { count: 0 } } }
impl<'ast> Visit<'ast> for LoopCounter {
    fn visit_expr_while(&mut self, i: &'ast vsyn::ExprWhile) {
        self.count += 1;
        verus_syn::visit::visit_expr_while(self, i);
    }
    fn visit_expr_for_loop(&mut self, i: &'ast vsyn::ExprForLoop) {
        self.count += 1;
        verus_syn::visit::visit_expr_for_loop(self, i);
    }
}

struct QuickSanitizer;
impl Fold for QuickSanitizer {
    fn fold_expr(&mut self, i: vsyn::Expr) -> vsyn::Expr {
        match i {
            vsyn::Expr::Break(_) | vsyn::Expr::Continue(_) | vsyn::Expr::Return(_) => vsyn::parse_str::<vsyn::Expr>("{}").unwrap(),
            vsyn::Expr::Unary(e) if matches!(e.op, vsyn::UnOp::Proof(_)) => vsyn::parse_str::<vsyn::Expr>("{}").unwrap(),
            other => verus_syn::fold::fold_expr(self, other),
        }
    }
}

struct InlineLoops { mode: CheckMode }
impl Fold for InlineLoops {
    fn fold_expr(&mut self, i: vsyn::Expr) -> vsyn::Expr {
        match i {
            vsyn::Expr::While(w) => {
                let body_src = ts_to_string(&w.body);
                let inner = body_src.trim().strip_prefix('{').and_then(|s| s.strip_suffix('}')).map(|s| s.trim()).unwrap_or("");
                let mut lines: Vec<String> = Vec::new();
                lines.push("{".to_string());
                let mut invs: Vec<String> = Vec::new();
                if let Some(inv) = &w.invariant { for e in inv.exprs.exprs.iter() { invs.push(ts_to_string(e)); } }
                if let Some(inv_eb) = &w.invariant_except_break { for e in inv_eb.exprs.exprs.iter() { invs.push(ts_to_string(e)); } }
                match self.mode {
                    CheckMode::BaseCase => {
                        if !invs.is_empty() {
                            lines.push("// Invariants (base case)".to_string());
                            for inv in &invs { lines.push(format!("assert({});", inv)); }
                        }
                    }
                    CheckMode::Inductiveness => {
                        if !invs.is_empty() {
                            lines.push("// Invariants before the loop, MUST be satisfied".to_string());
                            for inv in &invs { lines.push(format!("assert({});", inv)); }
                        }
                        let inner_body = ensure_last_stmt_terminated(inner);
                        if !inner_body.trim().is_empty() { lines.push(inner_body); }
                        if !invs.is_empty() {
                            lines.push("// Invariants after the loop, the one of the target error MUST fail".to_string());
                            for inv in &invs { lines.push(format!("assert({});", inv)); }
                        }
                    }
                }
                lines.push("}".to_string());
                let block_src = lines.join("\n");
                vsyn::parse_str::<vsyn::Expr>(&block_src).unwrap_or(vsyn::Expr::Block(vsyn::ExprBlock { attrs: vec![], label: None, block: w.body }))
            }
            vsyn::Expr::ForLoop(f) => {
                let body_src = ts_to_string(&f.body);
                let inner = body_src.trim().strip_prefix('{').and_then(|s| s.strip_suffix('}')).map(|s| s.trim()).unwrap_or("");
                // Synthesize pattern var declaration from range start if possible
                let mut header: Vec<String> = Vec::new();
                let pat_src = ts_to_string(&f.pat);
                if let vsyn::Expr::Range(r) = *f.expr.clone() {
                    if let Some(start_expr) = r.start {
                        let start_src = ts_to_string(&start_expr);
                        header.push(format!("let {} = {};", pat_src, start_src));
                    }
                }
                let mut lines: Vec<String> = Vec::new();
                lines.push("{".to_string());
                for h in header { lines.push(h); }
                // Assert invariants for nested for-loops using AST if present
                let mut invs: Vec<String> = Vec::new();
                if let Some(inv) = f.invariant.as_ref() { for e in inv.exprs.exprs.iter() { invs.push(ts_to_string(e)); } }
                match self.mode {
                    CheckMode::BaseCase => {
                        if !invs.is_empty() {
                            lines.push("// Invariants (base case)".to_string());
                            for inv in &invs { lines.push(format!("assert({});", inv)); }
                        }
                    }
                    CheckMode::Inductiveness => {
                        if !invs.is_empty() {
                            lines.push("// Invariants before the loop, MUST be satisfied".to_string());
                            for inv in &invs { lines.push(format!("assert({});", inv)); }
                        }
                        let inner_body = ensure_last_stmt_terminated(inner);
                        if !inner_body.trim().is_empty() { lines.push(inner_body); }
                        if !invs.is_empty() {
                            lines.push("// Invariants after the loop, the one of the target error MUST fail".to_string());
                            for inv in &invs { lines.push(format!("assert({});", inv)); }
                        }
                    }
                }
                lines.push("}".to_string());
                let block_src = lines.join("\n");
                vsyn::parse_str::<vsyn::Expr>(&block_src).unwrap_or(vsyn::Expr::Block(vsyn::ExprBlock { attrs: vec![], label: None, block: f.body }))
            }
            other => verus_syn::fold::fold_expr(self, other),
        }
    }
}

struct WhileHarnessFolder {
    target_idx: usize,
    seen: usize,
    mode: CheckMode,
    // Capture the exact harness block string (with comments) for the target while
    pub harness_block_src: Option<String>,
    // Lines to inject at the beginning of the harness block (e.g., preceding lets)
    header_lines: Vec<String>,
}
impl WhileHarnessFolder {
    fn new(target_idx: usize, mode: CheckMode, header_lines: Vec<String>) -> Self {
        Self { target_idx, seen: 0, mode, harness_block_src: None, header_lines }
    }
}
impl Fold for WhileHarnessFolder {
    fn fold_expr(&mut self, i: vsyn::Expr) -> vsyn::Expr {
        match i {
            vsyn::Expr::Unary(e) if matches!(e.op, vsyn::UnOp::Proof(_)) => vsyn::parse_str::<vsyn::Expr>("{}").unwrap(),
            vsyn::Expr::While(w) => {
                self.seen += 1;
                if self.seen != self.target_idx {
                    // Replace non-target while with its body (single-step)
                    let body_src = ts_to_string(&w.body);
                    let inner = body_src.trim().strip_prefix('{').and_then(|s| s.strip_suffix('}')).map(|s| s.trim()).unwrap_or("");
                    let block_src = format!("{{\n{}\n}}", inner);
                    return vsyn::parse_str::<vsyn::Expr>(&block_src).unwrap_or(vsyn::Expr::Block(vsyn::ExprBlock { attrs: vec![], label: None, block: w.body.clone() }));
                }
                let cond_src = ts_to_string(&w.cond);
                let mut invs: Vec<String> = Vec::new();
                if let Some(inv) = &w.invariant { for e in inv.exprs.exprs.iter() { invs.push(ts_to_string(e)); } }
                if let Some(inv_eb) = &w.invariant_except_break { for e in inv_eb.exprs.exprs.iter() { invs.push(ts_to_string(e)); } }
                let mut sanitizer = QuickSanitizer;
                let sanitized_block = sanitizer.fold_block(w.body.clone());
                let body_src = ts_to_string(&sanitized_block);
                let inner = body_src.trim().strip_prefix('{').and_then(|s| s.strip_suffix('}')).map(|s| s.trim()).unwrap_or("");
                let mut lines: Vec<String> = Vec::new();
                lines.push("{".to_string());
                for h in &self.header_lines { lines.push(h.clone()); }
                match self.mode {
                    CheckMode::BaseCase => {
                        // Only assert invariants once; no loop condition, no body, no after section
                        if !invs.is_empty() {
                            lines.push("// Invariants (base case)".to_string());
                            for inv in &invs { lines.push(format!("assert({});", inv)); }
                        }
                    }
                    CheckMode::Inductiveness => {
                        // Pre-body section: assert loop condition and invariants
                        lines.push("// before loop body START".to_string());
                        lines.push("// Loop condition, MUST be satisfied".to_string());
                        lines.push(format!("assert({});", cond_src));
                        if !invs.is_empty() {
                            lines.push("// Invariants before the loop, MUST be satisfied".to_string());
                            for inv in &invs { lines.push(format!("assert({});", inv)); }
                        }
                        lines.push("// before loop body END".to_string());
                        let inner_body = ensure_last_stmt_terminated(inner);
                        if !inner_body.trim().is_empty() { lines.push(inner_body); }
                        // Post-body section: assert invariants again
                        lines.push("// after loop body START".to_string());
                        if !invs.is_empty() {
                            lines.push("// Invariants after the loop, the one of the target error MUST fail".to_string());
                            for inv in &invs { lines.push(format!("assert({});", inv)); }
                        }
                        lines.push("// after loop body END".to_string());
                    }
                }
                lines.push("}".to_string());
                let block_src = lines.join("\n");
                self.harness_block_src = Some(block_src.clone());
                vsyn::parse_str::<vsyn::Expr>(&block_src).unwrap_or(vsyn::Expr::Block(vsyn::ExprBlock { attrs: vec![], label: None, block: w.body }))
            }
            vsyn::Expr::ForLoop(f) => {
                self.seen += 1;
                if self.seen != self.target_idx {
                    // Replace non-target for with its body (single-step)
                    let body_src = ts_to_string(&f.body);
                    let inner = body_src.trim().strip_prefix('{').and_then(|s| s.strip_suffix('}')).map(|s| s.trim()).unwrap_or("");
                    let block_src = format!("{{\n{}\n}}", inner);
                    return vsyn::parse_str::<vsyn::Expr>(&block_src).unwrap_or(vsyn::Expr::Block(vsyn::ExprBlock { attrs: vec![], label: None, block: f.body.clone() }));
                }
                let mut sanitizer = QuickSanitizer;
                let sanitized_block = sanitizer.fold_block(f.body.clone());
                // Inline nested loops inside the target body
                let mut inliner = InlineLoops { mode: self.mode };
                let inlined_block = inliner.fold_block(sanitized_block);
                let body_src = ts_to_string(&inlined_block);
                let inner = body_src.trim().strip_prefix('{').and_then(|s| s.strip_suffix('}')).map(|s| s.trim()).unwrap_or("");

                let mut lines: Vec<String> = Vec::new();
                lines.push("{".to_string());
                for h in &self.header_lines { lines.push(h.clone()); }
                // Declare the pattern variable from range lower bound if possible
                let pat_src = ts_to_string(&f.pat);
                if let vsyn::Expr::Range(r) = *f.expr.clone() {
                    if let Some(start_expr) = r.start {
                        let start_src = ts_to_string(&start_expr);
                        lines.push(format!("let {} = {};", pat_src, start_src));
                    }
                }
                // Assert invariants extracted from AST (for-loop invariants)
                let mut invs: Vec<String> = Vec::new();
                if let Some(inv) = f.invariant.as_ref() { for e in inv.exprs.exprs.iter() { invs.push(ts_to_string(e)); } }
                match self.mode {
                    CheckMode::BaseCase => {
                        if !invs.is_empty() {
                            lines.push("// Invariants (base case)".to_string());
                            for inv in &invs { lines.push(format!("assert({});", inv)); }
                        }
                    }
                    CheckMode::Inductiveness => {
                        if !invs.is_empty() {
                            lines.push("// Invariants before the loop, MUST be satisfied".to_string());
                            for inv in &invs { lines.push(format!("assert({});", inv)); }
                        }
                        let inner_body = ensure_last_stmt_terminated(inner);
                        if !inner_body.trim().is_empty() { lines.push(inner_body); }
                        if !invs.is_empty() {
                            lines.push("// Invariants after the loop, the one of the target error MUST fail".to_string());
                            for inv in &invs { lines.push(format!("assert({});", inv)); }
                        }
                    }
                }
                lines.push("}".to_string());
                let block_src = lines.join("\n");
                self.harness_block_src = Some(block_src.clone());
                vsyn::parse_str::<vsyn::Expr>(&block_src).unwrap_or(vsyn::Expr::Block(vsyn::ExprBlock { attrs: vec![], label: None, block: f.body }))
            }
            other => verus_syn::fold::fold_expr(self, other),
        }
    }
}

fn try_run_verusfmt(path: &PathBuf) {
    match Command::new("verusfmt").arg(path).output() {
        Ok(output) if output.status.success() => {
            if let Ok(s) = String::from_utf8(output.stdout) { if !s.is_empty() { let _ = fs::write(path, s); } }
        }
        _ => {}
    }
}

// Removed manual scanning helpers for collecting let-bindings; no longer needed.

// Collect simple let-bindings that appear textually before the target loop occurrence
// within the top-level statements of the function block. This is a heuristic but
// sufficient for many cases where locals are prepared before the loop.
fn collect_preceding_lets(block: &vsyn::Block, target_idx: usize) -> Vec<String> {
    let mut header: Vec<String> = Vec::new();
    let mut encountered_loops: usize = 0;
    for stmt in &block.stmts {
        // Count loops in this statement
        let mut lc = LoopCounter::new();
        lc.visit_stmt(stmt);
        // If this statement contains (or is) the target-th loop, stop before it
        if encountered_loops + lc.count >= target_idx { break; }
        // Otherwise, if it's a let-binding, capture it
        if let vsyn::Stmt::Local(_) = stmt {
            header.push(ts_to_string(stmt));
        }
        encountered_loops += lc.count;
    }
    header
}

fn main() {
    // extract_loop_syn <input.rs> <output.rs> (--line <N> | --fn <name> --loop-index <N>) --mode <check_base_case|check_inductiveness>
    let args = env::args().collect::<Vec<_>>();
    if args.len() < 6 {
        eprintln!("Usage: extract_loop_syn <input.rs> <output.rs> (--line <N> | --fn <name> --loop-index <N>) --mode <check_base_case|check_inductiveness>");
        std::process::exit(1);
    }
    let input_path = PathBuf::from(&args[1]);
    let output_path = PathBuf::from(&args[2]);
    let mut fn_name: Option<String> = None;
    let mut loop_idx: Option<usize> = None;
    let mut line_no: Option<usize> = None;
    let mut mode: Option<CheckMode> = None;
    let mut i = 3;
    while i < args.len() {
        match args[i].as_str() {
            "--fn" => { fn_name = Some(args.get(i+1).cloned().expect("--fn needs value")); i += 2; }
            "--loop-index" => { let v = args.get(i+1).expect("--loop-index needs value").parse::<usize>().expect("invalid index"); loop_idx = Some(v); i += 2; }
            "--line" => { let v = args.get(i+1).expect("--line needs value").parse::<usize>().expect("invalid line number"); line_no = Some(v); i += 2; }
            "--mode" => {
                let v = args.get(i+1).cloned().expect("--mode needs value");
                mode = Some(match v.as_str() {
                    "check_base_case" => CheckMode::BaseCase,
                    "check_inductiveness" => CheckMode::Inductiveness,
                    _ => { eprintln!("invalid --mode: {}", v); std::process::exit(2); }
                });
                i += 2;
            }
            _ => { i += 1; }
        }
    }
    let mode = mode.expect("--mode MUST be provided: check_base_case | check_inductiveness");
    let src = fs::read_to_string(&input_path).expect("read input failed");
    let (vb_start, vb_end) = find_verus_block(&src).expect("verus! block not found");
    let verus_body = &src[vb_start + 1..vb_end];
    let file: vsyn::File = vsyn::parse_str(verus_body).expect("parse verus! failed");

    // If a line number is provided, compute the 1-based line number within verus_body
    // and resolve to the ordinal index of the loop whose header/invariant section
    // contains that line.
    if loop_idx.is_none() {
        if let Some(abs_line) = line_no {
            // Count lines before the verus! body to translate absolute -> relative
            let prefix = &src[..vb_start+1];
            let base_lines = prefix.bytes().filter(|&b| b == b'\n').count() + 1;
            let rel_line = if abs_line > base_lines { abs_line - base_lines } else { 1 };

            // Precompute line starts within verus_body
            let mut line_starts: Vec<usize> = vec![0];
            for (idx, ch) in verus_body.char_indices() { if ch == '\n' { line_starts.push(idx + 1); } }
            line_starts.push(verus_body.len());
            // byte_of_line helper not used; keep only line_of_byte
            let line_of_byte = |pos: usize| -> usize {
                match line_starts.binary_search(&pos) { Ok(i) => i+1, Err(i) => i }
            };

            // Find all loop occurrences (while/for) in source in order
            let mut loop_starts: Vec<usize> = Vec::new();
            let mut search_from = 0usize;
            // Scan for 'while'
            while let Some(off) = verus_body[search_from..].find("while") {
                let pos = search_from + off;
                let prev_ok = pos==0 || !verus_body.as_bytes()[pos-1].is_ascii_alphanumeric();
                let mut iter = verus_body[pos+5..].chars().skip_while(|c| c.is_whitespace());
                let next_c = iter.next();
                let cond_ok = match next_c { Some('(') => true, Some(c) if c.is_ascii_alphanumeric() || c=='_' || c=='!' || c=='-' => true, _ => false };
                if prev_ok && cond_ok { loop_starts.push(pos); }
                search_from = pos + 5;
            }
            // Scan for 'for'
            let mut search_from_for = 0usize;
            while let Some(off) = verus_body[search_from_for..].find("for") {
                let pos = search_from_for + off;
                let prev_ok = pos==0 || !verus_body.as_bytes()[pos-1].is_ascii_alphanumeric();
                let j = pos + 3;
                let next_ok = j < verus_body.len() && (verus_body.as_bytes()[j] as char).is_whitespace();
                if prev_ok && next_ok { loop_starts.push(pos); }
                search_from_for = pos + 3;
            }
            loop_starts.sort_unstable();

            // For each loop start, compute the full loop span lines from keyword to matching '}'
            let mut loop_line_ranges: Vec<(usize, usize)> = Vec::new();
            for &ws in &loop_starts {
                if let Some(brace_rel) = verus_body[ws..].find('{') {
                    let open_byte = ws + brace_rel;
                    let mut depth: isize = 0;
                    let mut k = open_byte;
                    let bytes = verus_body.as_bytes();
                    while k < verus_body.len() {
                        match bytes[k] {
                            b'{' => depth += 1,
                            b'}' => {
                                depth -= 1;
                                if depth == 0 { break; }
                            }
                            _ => {}
                        }
                        k += 1;
                    }
                    let start_ln = line_of_byte(ws);
                    let end_ln = line_of_byte(k);
                    loop_line_ranges.push((start_ln, end_ln));
                }
            }
            // If possible, resolve the function containing rel_line and compute the while index within it
            if fn_name.is_none() {
                let mut fn_ranges: Vec<(usize, usize, String)> = Vec::new();
                let mut search_fn_from = 0usize;
                let vbytes = verus_body.as_bytes();
                while let Some(off) = verus_body[search_fn_from..].find("fn") {
                    let pos = search_fn_from + off;
                    let prev_ok = pos == 0 || !vbytes[pos - 1].is_ascii_alphanumeric();
                    let mut j = pos + 2;
                    while j < verus_body.len() && (verus_body.as_bytes()[j] as char).is_whitespace() { j += 1; }
                    if prev_ok && j < verus_body.len() {
                        let ch = verus_body.as_bytes()[j] as char;
                        if ch.is_ascii_alphabetic() || ch == '_' {
                            let name_start = j;
                            let mut name_end = j;
                            while name_end < verus_body.len() {
                                let c = verus_body.as_bytes()[name_end] as char;
                                if c.is_ascii_alphanumeric() || c == '_' { name_end += 1; } else { break; }
                            }
                            let fname = verus_body[name_start..name_end].to_string();
                            if let Some(fn_brace_rel) = verus_body[name_end..].find('{') {
                                let fn_open_byte = name_end + fn_brace_rel;
                                let mut d: isize = 0;
                                let mut p = fn_open_byte;
                                while p < verus_body.len() {
                                    match vbytes[p] {
                                        b'{' => d += 1,
                                        b'}' => {
                                            d -= 1;
                                            if d == 0 { break; }
                                        }
                                        _ => {}
                                    }
                                    p += 1;
                                }
                                let f_start_ln = line_of_byte(pos);
                                let f_end_ln = line_of_byte(p);
                                fn_ranges.push((f_start_ln, f_end_ln, fname));
                            }
                        }
                    }
                    search_fn_from = pos + 2;
                }
                let mut chosen_fn_name: Option<String> = None;
                let mut chosen_fn_range: Option<(usize, usize)> = None;
                for (sln, eln, name) in &fn_ranges {
                    if rel_line >= *sln && rel_line <= *eln {
                        chosen_fn_name = Some(name.clone());
                        chosen_fn_range = Some((*sln, *eln));
                        break;
                    }
                }
                if let (Some(fname), Some((fsln, feln))) = (chosen_fn_name, chosen_fn_range) {
                    let mut local_loops: Vec<(usize, usize)> = Vec::new();
                    for (sln, eln) in loop_line_ranges.iter() {
                        if *sln >= fsln && *eln <= feln {
                            local_loops.push((*sln, *eln));
                        }
                    }
                    let mut found_local_idx: Option<usize> = None;
                    for (i_local, (sln, eln)) in local_loops.iter().enumerate() {
                        if rel_line >= *sln && rel_line <= *eln {
                            found_local_idx = Some(i_local + 1);
                            break;
                        }
                    }
                    if let Some(li) = found_local_idx {
                        loop_idx = Some(li);
                        fn_name = Some(fname);
                    }
                }
            }
            if loop_idx.is_none() && fn_name.is_none() {
                for (idx, (sln, eln)) in loop_line_ranges.iter().enumerate() {
                    if rel_line >= *sln && rel_line <= *eln { loop_idx = Some(idx + 1); break; }
                }
            }
            if loop_idx.is_none() {
                eprintln!("No loop containing line {} (relative {}) found", abs_line, rel_line);
                std::process::exit(3);
            }
        }
    }

    let mut target_fn: Option<vsyn::ItemFn> = None;
    // Helper: recursively search for function by name or first-with-loops
    fn find_fn_by_name_recursive(items: &[vsyn::Item], name: &str) -> Option<vsyn::ItemFn> {
        for it in items {
            match it {
                vsyn::Item::Fn(f) if f.sig.ident.to_string() == name => return Some(f.clone()),
                vsyn::Item::Mod(m) => {
                    if let Some((_, content_items)) = &m.content {
                        if let Some(found) = find_fn_by_name_recursive(content_items, name) { return Some(found); }
                    }
                }
                _ => {}
            }
        }
        None
    }
    fn find_first_fn_with_loops_recursive(items: &[vsyn::Item]) -> Option<vsyn::ItemFn> {
        for it in items {
            match it {
                vsyn::Item::Fn(f) => {
                    let mut counter = LoopCounter::new();
                    counter.visit_item_fn(f);
                    if counter.count > 0 { return Some(f.clone()); }
                }
                vsyn::Item::Mod(m) => {
                    if let Some((_, content_items)) = &m.content {
                        if let Some(found) = find_first_fn_with_loops_recursive(content_items) { return Some(found); }
                    }
                }
                _ => {}
            }
        }
        None
    }
    // If we have a global loop index but no explicit function name, map it to a specific function in order
    fn list_functions_in_order(items: &[vsyn::Item], out: &mut Vec<vsyn::ItemFn>) {
        for it in items {
            match it {
                vsyn::Item::Fn(f) => out.push(f.clone()),
                vsyn::Item::Mod(m) => { if let Some((_, content)) = &m.content { list_functions_in_order(content, out); } }
                _ => {}
            }
        }
    }

    let mut local_loop_idx: Option<usize> = None;
    if let Some(ref name) = fn_name {
        target_fn = find_fn_by_name_recursive(&file.items, name);
        if target_fn.is_none() {
            eprintln!("target function '{}' not found", name);
            std::process::exit(2);
        }
        local_loop_idx = loop_idx; // Treat provided index as local to the named function
    } else if let Some(global_idx) = loop_idx {
        // Map global loop occurrence to a containing function and local index
        let mut funcs: Vec<vsyn::ItemFn> = Vec::new();
        list_functions_in_order(&file.items, &mut funcs);
        let mut cumulative: usize = 0;
        for f in funcs.into_iter() {
            let mut c = LoopCounter::new();
            c.visit_item_fn(&f);
            if global_idx <= cumulative + c.count {
                target_fn = Some(f);
                local_loop_idx = Some(global_idx - cumulative);
                break;
            }
            cumulative += c.count;
        }
    } else {
        target_fn = find_first_fn_with_loops_recursive(&file.items);
        local_loop_idx = Some(1);
    }

    let mut func = target_fn.expect("target function not found");
    // Preserve the original function (name and body) so we can include it in the output
    let original_func_src: String = ts_to_string(&func);
    let mut counter = LoopCounter::new();
    counter.visit_item_fn(&func);
    let idx = local_loop_idx.unwrap_or(1);
    if idx == 0 || idx > counter.count { eprintln!("invalid loop index"); std::process::exit(2); }

    let orig_name = func.sig.ident.to_string();
    let new_name = format!("{}_loop{}", orig_name, idx);
    func.sig.ident = vsyn::Ident::new(&new_name, func.sig.ident.span());
    func.sig.spec.ensures = None;
    func.sig.spec.default_ensures = None;
    func.sig.spec.requires = None;
    // Ensure no return type for the extracted loop function
    func.sig.output = vsyn::ReturnType::Default;

    // Prepare header lines from preceding let-bindings before the target loop
    let header_lines = collect_preceding_lets(&*func.block, idx);

    let mut folder = WhileHarnessFolder::new(idx, mode, header_lines);
    let new_block = folder.fold_block(*func.block.clone());
    func.block = Box::new(new_block);

    let func_sig = ts_to_string(&func.sig);

    let func_body = if let Some(ref s) = folder.harness_block_src { s.clone() } else { ts_to_string(&func.block) };

    // Collect support items recursively: include all functions (exec/spec/proof) except the original
    // target function, and include ghost/spec consts anywhere in the file (including modules)
    fn collect_support_items(items: &[vsyn::Item], skip_fn_name: &str, out: &mut Vec<String>) {
        for it in items {
            match it {
                vsyn::Item::Fn(f) => {
                    let fname = f.sig.ident.to_string();
                    if fname != skip_fn_name && fname != "main" {
                        out.push(ts_to_string(f));
                    }
                }
                vsyn::Item::Const(c) => {
                    if !matches!(c.mode, vsyn::FnMode::Default) { out.push(ts_to_string(c)); }
                }
                vsyn::Item::Mod(m) => {
                    if let Some((_, content_items)) = &m.content { collect_support_items(&content_items, skip_fn_name, out); }
                }
                _ => {}
            }
        }
    }
    let mut support_src: Vec<String> = Vec::new();
    collect_support_items(&file.items, &orig_name, &mut support_src);
    // Also include the unmodified original function that contains the target loop
    support_src.push(original_func_src);

    let mut out_src = String::new();
    // Faithfully import dependencies from the original file
    let mut import_set: BTreeSet<String> = BTreeSet::new();
    collect_uses_from_verus_items(&file.items, &mut import_set);
    // Parse the outer Rust file with syn to collect `use` items robustly
    for u in collect_rust_uses_with_syn(&src) { import_set.insert(u); }
    // Ensure baseline vstd imports are present without duplicating existing ones
    ensure_imports(&mut import_set, BASELINE_IMPORTS);
    if !import_set.is_empty() {
        for u in &import_set { out_src.push_str(u); out_src.push('\n'); }
    }
    out_src.push_str("fn main() {}\n");
    out_src.push_str("verus! {\n\n");
    if !support_src.is_empty() {
        out_src.push_str(&support_src.join("\n\n"));
        out_src.push_str("\n\n");
    }
    out_src.push_str(&func_sig);
    out_src.push_str("\n");
    out_src.push_str(&func_body);
    out_src.push_str("\n\n} // verus!\n");

    fs::write(&output_path, out_src).expect("write output failed");
    try_run_verusfmt(&output_path);
    println!("Extracted written to: {}", output_path.display());
}
