// Simple injector for extracted harness files produced by `extract_loop_syn`.
// It finds the region delimited by:
//   // before loop body START
//   // before loop body END
// and inserts shadowing `let` statements for assignments from a JSON map.

use std::collections::BTreeMap;
use std::fs;
use std::path::PathBuf;

use serde::Deserialize;
use serde_json::Value;
use verus_syn as vsyn;

mod typed_inject;

#[derive(Deserialize)]
#[serde(untagged)]
enum AssignPayload {
    Wrapped { assignments: BTreeMap<String, Value> },
    Flat(BTreeMap<String, Value>),
}

fn load_map(p: &PathBuf) -> BTreeMap<String, Value> {
    let s = fs::read_to_string(p).expect("failed to read map json");
    let payload: AssignPayload = serde_json::from_str(&s).expect("invalid map json");
    match payload {
        AssignPayload::Wrapped { assignments } => assignments,
        AssignPayload::Flat(m) => m,
    }
}

fn coalesce_vec_assignments(assigns: &BTreeMap<String, Value>) -> BTreeMap<String, Value> {
    let mut out: BTreeMap<String, Value> = BTreeMap::new();
    let mut bucket: BTreeMap<String, BTreeMap<usize, Value>> = BTreeMap::new();
    let mut lens: BTreeMap<String, usize> = BTreeMap::new();

    for (k, v) in assigns.iter() {
        // Recognize vector encodings without regex
        // __vec__NAME__IDX
        if k.starts_with("__vec__") {
            if k.ends_with("__len") {
                let base = &k[7..k.len()-5];
                if let Some(n) = v.as_u64() { lens.insert(base.to_string(), n as usize); }
                continue;
            }
            if let Some(last) = k.rsplit_once("__") {
                let (base_full, idx_str) = last;
                if let Ok(idx) = idx_str.parse::<usize>() {
                    let base = &base_full[7..];
                    bucket.entry(base.to_string()).or_default().insert(idx, v.clone());
                    continue;
                }
            }
        }
        // Legacy: NAME_IDX or NAME_len
        if let Some((name, suf)) = k.rsplit_once('_') {
            if suf == "len" {
                if let Some(n) = v.as_u64() { lens.insert(name.to_string(), n as usize); }
                continue;
            }
            if let Ok(idx) = suf.parse::<usize>() {
                bucket.entry(name.to_string()).or_default().insert(idx, v.clone());
                continue;
            }
        }
        // Store value directly
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
        let mut parts: Vec<Value> = Vec::new();
        for i in idxs {
            if let Some(val) = idxmap.get(&i) { parts.push(val.clone()); }
        }
        // store as JSON array
        out.insert(base, Value::Array(parts));
    }
    out
}

fn value_is_noneish(val: &Value) -> bool {
    match val {
        Value::Null => true,
        Value::String(s) => {
            let t = s.trim();
            t.eq_ignore_ascii_case("none") || t.eq_ignore_ascii_case("null") || t.contains("None")
        }
        _ => false,
    }
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

fn name_is_harness(name: &str) -> bool {
    if let Some(pos) = name.rfind("_loop") {
        let digits = &name[pos + 5..];
        !digits.is_empty() && digits.chars().all(|c| c.is_ascii_digit())
    } else { false }
}

fn block_has_let_ident(block: &vsyn::Block, target: &str) -> bool {
    fn pat_contains_ident(p: &vsyn::Pat, target: &str) -> bool {
        match p {
            vsyn::Pat::Ident(pi) => pi.ident.to_string() == target,
            vsyn::Pat::Tuple(pt) => pt.elems.iter().any(|sub| pat_contains_ident(sub, target)),
            _ => false,
        }
    }
    for stmt in &block.stmts {
        if let vsyn::Stmt::Local(loc) = stmt {
            if pat_contains_ident(&loc.pat, target) { return true; }
        }
    }
    false
}

fn main() {
    // inject_cex_extracted <input.rs> <output.rs> --map-json <path>
    let args = std::env::args().collect::<Vec<_>>();
    if args.len() < 5 {
        eprintln!("Usage: inject_cex_extracted <input.rs> <output.rs> --map-json <path>");
        std::process::exit(1);
    }
    let input_path = PathBuf::from(&args[1]);
    let output_path = PathBuf::from(&args[2]);
    let mut map_json: Option<PathBuf> = None;
    let mut i = 3;
    while i < args.len() {
        match args[i].as_str() {
            "--map-json" => { map_json = Some(PathBuf::from(&args[i+1])); i += 2; }
            _ => { i += 1; }
        }
    }
    let map_path = map_json.expect("--map-json is required");
    let assigns_raw = load_map(&map_path);
    let assigns = coalesce_vec_assignments(&assigns_raw);

    let src = fs::read_to_string(&input_path).expect("failed to read input");
    let (vb_start, vb_end) = find_verus_block(&src).expect("verus! block not found");
    let verus_body = &src[vb_start + 1..vb_end];
    let file: vsyn::File = vsyn::parse_str(verus_body).expect("parse verus! failed");
    // Find last harness function *_loopN
    let mut harness_name: Option<String> = None;
    for item in &file.items {
        if let vsyn::Item::Fn(f) = item {
            let fname = f.sig.ident.to_string();
            if name_is_harness(&fname) { harness_name = Some(fname); }
        }
    }
    let harness_name = harness_name.expect("no harness function *_loopN found");
    let start_tag = "// before loop body START";
    let end_tag = "// before loop body END";
    let insertion_pos: usize = if let (Some(sp), Some(ep)) = (src.find(start_tag), src.find(end_tag)) {
        let start_pos = sp;
        let after_start_line = src[start_pos..]
            .find('\n')
            .map(|off| start_pos + off + 1)
            .unwrap_or(start_pos + start_tag.len());
        let end_pos = ep;
        if after_start_line > end_pos { eprintln!("Tag order invalid"); std::process::exit(2); }
        after_start_line
    } else {
        // No tags (base case): insert at start of the harness function body
        // Locate function definition textually inside verus_body
        let search_from = 0usize;
        let mut fn_pos: Option<usize> = None;
        let needle = format!("fn {}", harness_name);
        while let Some(off) = verus_body[search_from..].find(&needle) {
            fn_pos = Some(search_from + off);
            break;
        }
        let fn_pos = fn_pos.expect("harness function text not found");
        // Find the opening '{' of the function from the end of name
        let mut i = fn_pos + needle.len();
        let bytes = verus_body.as_bytes();
        while i < verus_body.len() && bytes[i] as char != '{' { i += 1; }
        if i >= verus_body.len() { eprintln!("could not find function body start"); std::process::exit(3); }
        // Insert after the opening brace's newline if present
        let after_open = if let Some(nl) = verus_body[i..].find('\n') { i + nl + 1 } else { i + 1 };
        vb_start + 1 + after_open
    };

    // Build injected lines.
    // Keep insertion before existing pre-body facts so user values are visible to asserts/assumes.
    let mut injected = String::new();
    // Special-case: predeclare `i` if no top-level let `i` exists in the harness block.
    let mut harness_block_has_i = false;
    for item in &file.items {
        if let vsyn::Item::Fn(f) = item {
            if f.sig.ident.to_string() == harness_name {
                harness_block_has_i = block_has_let_ident(&f.block, "i");
                break;
            }
        }
    }
    if !harness_block_has_i {
        injected.push_str("let mut i: usize = 0usize;\n");
    }
    // Find the harness block for type inference
    let mut harness_block_opt: Option<vsyn::Block> = None;
    for item in &file.items {
        if let vsyn::Item::Fn(f) = item {
            if f.sig.ident.to_string() == harness_name {
                harness_block_opt = Some((*f.block.clone()).clone());
                break;
            }
        }
    }
    let harness_block = harness_block_opt.expect("harness block not found");
    for (k, v) in &assigns {
        if value_is_noneish(v) { continue; }
        let expr = typed_inject::emit_for_var(&harness_block, k, v);
        injected.push_str(&format!("let mut {} = {};\n", k, expr));
    }

    let mut out = String::new();
    out.push_str(&src[..insertion_pos]);
    out.push_str(&injected);
    out.push_str(&src[insertion_pos..]);

    fs::write(&output_path, out).expect("failed to write output");
}
