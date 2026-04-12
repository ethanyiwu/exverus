use std::env;
use std::fs;
use std::path::PathBuf;

use verus_syn as vsyn;

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

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() != 2 {
        eprintln!("Usage: read_loop_id_syn <extracted.rs>");
        std::process::exit(2);
    }
    let input_path = PathBuf::from(&args[1]);
    let src = match fs::read_to_string(&input_path) {
        Ok(s) => s,
        Err(e) => { eprintln!("read failed: {}", e); std::process::exit(3); }
    };
    let (vb_start, vb_end) = match find_verus_block(&src) {
        Some(p) => p,
        None => { eprintln!("verus! block not found"); std::process::exit(4); }
    };
    let verus_body = &src[vb_start + 1..vb_end];
    let file: vsyn::File = match vsyn::parse_str(verus_body) {
        Ok(f) => f,
        Err(e) => { eprintln!("parse verus! failed: {}", e); std::process::exit(5); }
    };
    // Find first function with name matching <orig>_loop<idx>
    for item in &file.items {
        if let vsyn::Item::Fn(f) = item {
            let name = f.sig.ident.to_string();
            if let Some(pos) = name.rfind("_loop") {
                let (orig, idx_str) = (&name[..pos], &name[pos+5..]);
                if !orig.is_empty() && !idx_str.is_empty() && idx_str.chars().all(|c| c.is_ascii_digit()) {
                    println!("{} {}", orig, idx_str);
                    return;
                }
            }
        }
    }
    eprintln!("no _loop function found");
    std::process::exit(6);
}
