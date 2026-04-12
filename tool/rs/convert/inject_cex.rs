//! Counterexample injector for converted Verus programs (harnesses).
//!
//! This tool rewrites the generated harness to inject concrete values for variables.
//!
//! Behavior:
//! - For non-reference/mutable parameters that appear in the tuple rebind
//!   (e.g., `let (mut x, mut y) = (x, y);`), it replaces the RHS tuple elements
//!   with the provided concrete expressions.
//! - For `&mut T` parameters, Verus disallows introducing a new binding of type
//!   `&mut T` in certain tuple patterns. Instead of tuple-rebinding those, we
//!   materialize a fresh owned local with the concrete value and then shadow the
//!   parameter name with a mutable reference to that local. For example:
//!
//!     let mut __vinv_inj_a = vec![...];
//!     let a = &mut __vinv_inj_a;
//!
//!   This avoids problematic tuple patterns while exposing the concrete value to
//!   the rest of the harness. We additionally post-process the printed output
//!   to remove any `assume(... .len() == ...)` lines that would otherwise
//!   re-establish invariants and prevent detecting the injected counterexample.
//!
//! The result preserves the overall harness structure while allowing you to
//! materialize a concrete counterexample for validation.

use std::collections::BTreeMap;
use std::fs;
use std::path::PathBuf;

use proc_macro2::TokenStream as TokenStream2;
use quote::ToTokens;
use serde::Deserialize;
use verus_syn as vsyn;
use regex::Regex;

/// Assignment specification: a mapping from variable name to injected expression.
#[derive(Deserialize)]
struct AssignSpec {
    // Map variable name -> expression string (e.g., "5", "true", "(1,2)")
    assignments: BTreeMap<String, String>,
}

/// Find the byte-span of the first `verus! { ... }` block in a source string.
/// Returns (start_idx_of_open_brace, end_idx_of_matching_close_brace).
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

/// Pretty-print a verus_syn AST node back into a string via quote.
fn ts_to_string<T: ToTokens>(node: &T) -> String {
    let ts: TokenStream2 = node.to_token_stream();
    ts.to_string()
}

fn main() {
    // CLI: inject_cex <input.rs> <output.rs> --map-json <path> [--report-json <path>]
    // - input.rs: converted program containing harness `_whileN`
    // - output.rs: file to write the injected program to
    // - --map-json: JSON file with shape { "assignments": { var: expr, ... } }
    // - --report-json (optional): writes { "lhs": [ ... ] } of tuple-rebind LHS vars
    let args = std::env::args().collect::<Vec<_>>();
    if args.len() < 5 {
        eprintln!("Usage: inject_cex <input.rs> <output.rs> --map-json <path> [--report-json <path>]");
        std::process::exit(1);
    }
    let input_path = PathBuf::from(&args[1]);
    let output_path = PathBuf::from(&args[2]);
    let mut map_json: Option<PathBuf> = None;
    let mut report_json: Option<PathBuf> = None;
    let mut i = 3;
    while i < args.len() {
        match args[i].as_str() {
            "--map-json" => {
                if i + 1 >= args.len() { eprintln!("--map-json requires a path"); std::process::exit(1); }
                map_json = Some(PathBuf::from(&args[i+1]));
                i += 2;
            }
            "--report-json" => {
                if i + 1 >= args.len() { eprintln!("--report-json requires a path"); std::process::exit(1); }
                report_json = Some(PathBuf::from(&args[i+1]));
                i += 2;
            }
            other => {
                eprintln!("Unexpected arg: {}", other);
                std::process::exit(1);
            }
        }
    }

    let map_path = map_json.expect("--map-json is required");
    let map_str = fs::read_to_string(&map_path).expect("failed to read map json");
    let spec: AssignSpec = serde_json::from_str(&map_str).expect("invalid map json");
    // Coalesce namespaced or legacy element-wise vector keys into aggregated base -> vec![...]
    let assignments: BTreeMap<String, String> = coalesce_vec_assignments(&spec.assignments);

    // Load input file and isolate the verus! body
    let src = fs::read_to_string(&input_path).expect("failed to read input");
    let (vb_start, vb_end) = find_verus_block(&src).expect("verus! block not found");
    let verus_body = &src[vb_start + 1..vb_end];

    // Parse the verus! body using verus_syn
    let mut file: vsyn::File = vsyn::parse_str(verus_body).expect("parse verus! body failed");

    // Report data
    let mut reported_lhs: Vec<String> = Vec::new();
    // Track which &mut parameters we injected for, so we can post-process
    // the printed output (e.g., remove contradictory `assume(a.len() == N);`).
    let mut injected_ref_mut_targets: Vec<String> = Vec::new();

    // Helper: recursively search blocks; replace tuple-let RHS and insert &mut assignments.
    // Returns a triple:
    //   (replaced_tuple_let_rhs, tuple_rebind_lhs_idents, injected_any_ref_mut_assignment)
    fn try_inject_in_block(
        block: &mut vsyn::Block,
        assignments: &BTreeMap<String, String>,
        ref_mut_targets: &Vec<String>,
        other_targets: &Vec<String>,
    ) -> (bool, Vec<String>, bool) {
        // Iterate with index so we can insert after a found let
        let mut idx: usize = 0;
        while idx < block.stmts.len() {
            let mut injected_here = false;
            match &mut block.stmts[idx] {
                vsyn::Stmt::Local(local) => {
                    // Case 1: Tuple let pattern, e.g., `let (mut x, mut y) = (x, y);`
                    if let vsyn::Pat::Tuple(pat_tuple) = &local.pat {
                        let mut lhs_idents: Vec<String> = Vec::new();
                        let mut all_id = true;
                        for p in pat_tuple.elems.iter() {
                            if let vsyn::Pat::Ident(pat_ident) = p {
                                lhs_idents.push(pat_ident.ident.to_string());
                            } else { all_id = false; break; }
                        }
                        if all_id {
                            if let Some(init) = &mut local.init {
                                if let vsyn::Expr::Tuple(expr_tuple) = &mut *init.expr {
                                    let mut new_elems: vsyn::punctuated::Punctuated<vsyn::Expr, vsyn::token::Comma> = vsyn::punctuated::Punctuated::new();
                                    for (j, lhs) in lhs_idents.iter().enumerate() {
                                        if let Some(v) = assignments.get(lhs) {
                                            let new_expr: vsyn::Expr = vsyn::parse_str(v).expect("failed to parse value expr");
                                            new_elems.push_value(new_expr);
                                        } else if let Some(orig) = expr_tuple.elems.iter().nth(j) {
                                            new_elems.push_value(orig.clone());
                                        } else {
                                            let fallback: vsyn::Expr = vsyn::parse_str(lhs).unwrap();
                                            new_elems.push_value(fallback);
                                        }
                                        if j + 1 < lhs_idents.len() { new_elems.push_punct(vsyn::token::Comma::default()); }
                                    }
                                    expr_tuple.elems = new_elems;
                                    // Insert &mut assignments (if any) after this let
                                    if !ref_mut_targets.is_empty() {
                                        let mut offset = 1;
                                        for name in ref_mut_targets {
                                            if let Some(val) = assignments.get(name) {
                                                // Create an owned local with the concrete value, then
                                                // rebind the parameter name to a mutable reference to it.
                                                let local_name = format!("__vinv_inj_{}", name);
                                                let stmt1 = format!("let mut {} = {};", local_name, val);
                                                let stmt2 = format!("let {} = & mut {};", name, local_name);
                                                let new_stmt1: vsyn::Stmt = vsyn::parse_str(&stmt1).expect("failed to parse &mut local stmt");
                                                let new_stmt2: vsyn::Stmt = vsyn::parse_str(&stmt2).expect("failed to parse &mut rebind stmt");
                                                block.stmts.insert(idx + offset, new_stmt1);
                                                offset += 1;
                                                block.stmts.insert(idx + offset, new_stmt2);
                                                offset += 1;
                                                injected_here = true;
                                            }
                                        }
                                    }
                                    // Insert overshadowing locals for other (non-&mut) targets not covered by tuple LHS
                                    if !other_targets.is_empty() {
                                        let mut offset = 1 + ref_mut_targets.len();
                                        for name in other_targets {
                                            if lhs_idents.iter().any(|n| n == name) { continue; }
                                            if let Some(val) = assignments.get(name) {
                                                let stmt_src = format!("let mut {} = {};", name, val);
                                                let new_stmt: vsyn::Stmt = vsyn::parse_str(&stmt_src).expect("failed to parse overshadow local stmt");
                                                block.stmts.insert(idx + offset, new_stmt);
                                                offset += 1;
                                                injected_here = true;
                                            }
                                        }
                                    }
                                    return (true, lhs_idents, injected_here);
                                }
                            }
                        }
                    }
                    // Case 2: Grouped single ident pattern, e.g., `let (mut x) = (x);`
                    if let vsyn::Pat::Paren(paren) = &local.pat {
                        if let vsyn::Pat::Ident(pat_ident) = &*paren.pat {
                            let var = pat_ident.ident.to_string();
                            if let Some(init) = &mut local.init {
                                if let Some(val) = assignments.get(&var) {
                                    let new_expr: vsyn::Expr = vsyn::parse_str(val).expect("failed to parse value expr");
                                    *init.expr = new_expr;
                                    // Insert &mut assignments (if any) after this let
                                    if !ref_mut_targets.is_empty() {
                                        let mut offset = 1;
                                        for name in ref_mut_targets {
                                            if let Some(v) = assignments.get(name) {
                                                let local_name = format!("__vinv_inj_{}", name);
                                                let stmt1 = format!("let mut {} = {};", local_name, v);
                                                let stmt2 = format!("let {} = & mut {};", name, local_name);
                                                let new_stmt1: vsyn::Stmt = vsyn::parse_str(&stmt1).expect("failed to parse &mut local stmt");
                                                let new_stmt2: vsyn::Stmt = vsyn::parse_str(&stmt2).expect("failed to parse &mut rebind stmt");
                                                block.stmts.insert(idx + offset, new_stmt1);
                                                offset += 1;
                                                block.stmts.insert(idx + offset, new_stmt2);
                                                offset += 1;
                                                injected_here = true;
                                            }
                                        }
                                    }
                                    // Insert overshadowing locals for other (non-&mut) targets not this var
                                    if !other_targets.is_empty() {
                                        let mut offset = 1 + ref_mut_targets.len();
                                        for name in other_targets {
                                            if name == &var { continue; }
                                            if let Some(v) = assignments.get(name) {
                                                let stmt_src = format!("let mut {} = {};", name, v);
                                                let new_stmt: vsyn::Stmt = vsyn::parse_str(&stmt_src).expect("failed to parse overshadow local stmt");
                                                block.stmts.insert(idx + offset, new_stmt);
                                                offset += 1;
                                                injected_here = true;
                                            }
                                        }
                                    }
                                    return (true, vec![var], injected_here);
                                }
                            }
                        }
                    }
                }
                // Recurse into nested blocks
                vsyn::Stmt::Expr(vsyn::Expr::Block(expr_block), _) => {
                    let (ok, lhs, inj) = try_inject_in_block(&mut expr_block.block, assignments, ref_mut_targets, other_targets);
                    if ok || inj { return (ok, lhs, inj); }
                }
                _ => {}
            }
            idx += 1;
        }
        // If no let found here or in children, inject at start for &mut and other targets
        if !ref_mut_targets.is_empty() || !other_targets.is_empty() {
            let mut offset = 0;
            for name in ref_mut_targets {
                if let Some(v) = assignments.get(name) {
                    let local_name = format!("__vinv_inj_{}", name);
                    let stmt1 = format!("let mut {} = {};", local_name, v);
                    let stmt2 = format!("let {} = & mut {};", name, local_name);
                    let new_stmt1: vsyn::Stmt = vsyn::parse_str(&stmt1).expect("failed to parse &mut local stmt");
                    let new_stmt2: vsyn::Stmt = vsyn::parse_str(&stmt2).expect("failed to parse &mut rebind stmt");
                    block.stmts.insert(offset, new_stmt1);
                    offset += 1;
                    block.stmts.insert(offset, new_stmt2);
                    offset += 1;
                }
            }
            for name in other_targets {
                if let Some(v) = assignments.get(name) {
                    let stmt_src = format!("let mut {} = {};", name, v);
                    let new_stmt: vsyn::Stmt = vsyn::parse_str(&stmt_src).expect("failed to parse overshadow local stmt");
                    block.stmts.insert(offset, new_stmt);
                    offset += 1;
                }
            }
            return (false, Vec::new(), true);
        }
        (false, Vec::new(), false)
    }

    // Traverse functions with suffix `_while...` (generated harnesses).
    for item in &mut file.items {
        if let vsyn::Item::Fn(func) = item {
            let name = func.sig.ident.to_string();
            if !(name.contains("_loop") || name.contains("_while") || name.contains("_for")) { continue; }
            // Discover which parameters are `&mut` so we can inject `*name = expr;` for those.
            let mut ref_mut_params: Vec<String> = Vec::new();
            for input in &func.sig.inputs {
                if let vsyn::FnArg { kind: vsyn::FnArgKind::Typed(pat_type), .. } = input {
                    if let vsyn::Pat::Ident(pat_ident) = &*pat_type.pat {
                        if let vsyn::Type::Reference(tr) = &*pat_type.ty {
                            if tr.mutability.is_some() {
                                ref_mut_params.push(pat_ident.ident.to_string());
                            }
                        }
                    }
                }
            }
            // Assignment keys split into &mut params and other targets (params or locals by name)
            let mut ref_mut_targets: Vec<String> = Vec::new();
            let mut other_targets: Vec<String> = Vec::new();
            for k in assignments.keys() {
                if ref_mut_params.iter().any(|n| n == k) { ref_mut_targets.push(k.clone()); } else { other_targets.push(k.clone()); }
            }
            let (replaced, lhs, _injected) = try_inject_in_block(&mut func.block, &assignments, &ref_mut_targets, &other_targets);
            if replaced { reported_lhs = lhs; }
            // remember which &mut params we attempted to materialize
            injected_ref_mut_targets = ref_mut_targets.clone();
            // We process only the first harness
            break;
        }
    }

    let new_body = ts_to_string(&file);
    let mut out_src = String::new();
    out_src.push_str(&src[..vb_start + 1]);
    out_src.push_str(&new_body);
    out_src.push_str(&src[vb_end..]);

    // Post-process: normalize single-variable tuple-let text to the exact form tests expect.
    if reported_lhs.len() == 1 {
        let v = &reported_lhs[0];
        let pat = format!(r"let\s*\(\s*mut\s*{}\s*,\s*\)", regex::escape(v));
        let re = Regex::new(&pat).unwrap();
        let repl = format!("let (mut {})", v);
        out_src = re.replace_all(&out_src, repl).to_string();
    }
    // If we injected &mut parameter locals, remove any `assume(x.len() == Y);`
    // lines that would re-establish the old invariant and prevent detection.
    if !injected_ref_mut_targets.is_empty() {
        for name in &injected_ref_mut_targets {
            // Regex matches `assume( <name>.len() == ... );` with optional spacing
            let pat = format!(r"(?m)\s*assume\s*\(\s*{}\s*\.\s*len\s*\(\s*\)\s*==[^;]*;\s*", regex::escape(name));
            let re = Regex::new(&pat).unwrap();
            out_src = re.replace_all(&out_src, "").to_string();
        }
    }

    fs::write(&output_path, out_src).expect("failed to write output");

    if let Some(rp) = report_json {
        let report = serde_json::json!({
            "lhs": reported_lhs,
        });
        fs::write(rp, serde_json::to_string_pretty(&report).unwrap()).ok();
    }
}

/// Coalesce element-wise vector assignments into a single base -> "vec![...]" entry.
fn coalesce_vec_assignments(assigns: &BTreeMap<String, String>) -> BTreeMap<String, String> {
    let re_idx_ns = Regex::new(r"^__vec__(.*)__(\d+)$").unwrap();
    let re_len_ns = Regex::new(r"^__vec__(.*)__len$").unwrap();
    let re_idx_legacy = Regex::new(r"^(.*)_(\d+)$").unwrap();
    let re_len_legacy = Regex::new(r"^(.*)_len$").unwrap();

    let mut out: BTreeMap<String, String> = BTreeMap::new();
    let mut bucket: BTreeMap<String, BTreeMap<usize, String>> = BTreeMap::new();
    let mut lens: BTreeMap<String, usize> = BTreeMap::new();

    for (k, v) in assigns.iter() {
        if let Some(c) = re_idx_ns.captures(k) {
            let base = c.get(1).unwrap().as_str().to_string();
            let idx: usize = c.get(2).unwrap().as_str().parse().unwrap_or(0);
            bucket.entry(base).or_default().insert(idx, v.clone());
            continue;
        }
        if let Some(c) = re_idx_legacy.captures(k) {
            let base = c.get(1).unwrap().as_str().to_string();
            let idx: usize = c.get(2).unwrap().as_str().parse().unwrap_or(0);
            bucket.entry(base).or_default().insert(idx, v.clone());
            continue;
        }
        if let Some(c) = re_len_ns.captures(k) {
            let base = c.get(1).unwrap().as_str().to_string();
            if let Ok(n) = v.parse::<usize>() { lens.insert(base, n); }
            continue;
        }
        if let Some(c) = re_len_legacy.captures(k) {
            let base = c.get(1).unwrap().as_str().to_string();
            if let Ok(n) = v.parse::<usize>() { lens.insert(base, n); }
            continue;
        }
        // passthrough non-vector keys
        out.insert(k.clone(), v.clone());
    }

    for (base, idxmap) in bucket.into_iter() {
        if out.contains_key(&base) { continue; }
        let idxs: Vec<usize> = if let Some(n) = lens.get(&base) {
            (0..*n).filter(|i| idxmap.contains_key(i)).collect()
        } else {
            let mut v: Vec<usize> = idxmap.keys().cloned().collect();
            v.sort_unstable();
            v
        };
        let mut parts: Vec<String> = Vec::new();
        for i in idxs {
            if let Some(val) = idxmap.get(&i) { parts.push(val.clone()); }
        }
        out.insert(base, format!("vec![{}]", parts.join(", ")));
    }
    out
}
