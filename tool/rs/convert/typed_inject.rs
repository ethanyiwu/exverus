use serde_json::Value;
use verus_syn as vsyn;

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum SimpleType {
    Bool,
    Char,
    Int,
    UInt,
    Usize,
    U128,
    StringT,
    VecChar,
    VecInt,
    VecUInt,
    // Fallback for vectors when element type is unclear; treat as VecInt
    Unknown,
}

fn type_is_vec_of_char(ty: &vsyn::Type) -> bool {
    match ty {
        vsyn::Type::Path(tp) => {
            if let Some(seg) = tp.path.segments.last() {
                let ident = seg.ident.to_string();
                if ident == "Vec" || ident.ends_with("::Vec") {
                    if let vsyn::PathArguments::AngleBracketed(ab) = &seg.arguments {
                        if let Some(vsyn::GenericArgument::Type(inner_ty)) = ab.args.first() {
                            return match inner_ty {
                                vsyn::Type::Path(inner_tp) => {
                                    inner_tp.path.segments.last().map(|s| s.ident.to_string() == "char").unwrap_or(false)
                                }
                                _ => false,
                            };
                        }
                    }
                }
            }
            false
        }
        _ => false,
    }
}

fn type_is_vec_of_numeric(ty: &vsyn::Type) -> Option<SimpleType> {
    match ty {
        vsyn::Type::Path(tp) => {
            if let Some(seg) = tp.path.segments.last() {
                if seg.ident.to_string() == "Vec" || seg.ident.to_string().ends_with("::Vec") {
                    if let vsyn::PathArguments::AngleBracketed(ab) = &seg.arguments {
                        if let Some(vsyn::GenericArgument::Type(inner_ty)) = ab.args.first() {
                            if let vsyn::Type::Path(inner_tp) = inner_ty {
                                if let Some(last) = inner_tp.path.segments.last() {
                                    let ident = last.ident.to_string();
                                    return match ident.as_str() {
                                        "usize" => Some(SimpleType::VecUInt),
                                        "u8" | "u16" | "u32" | "u64" | "u128" => Some(SimpleType::VecUInt),
                                        "i8" | "i16" | "i32" | "i64" | "i128" => Some(SimpleType::VecInt),
                                        _ => None,
                                    };
                                }
                            }
                        }
                    }
                }
            }
            None
        }
        _ => None,
    }
}

fn lit_is_char(e: &vsyn::Expr) -> bool {
    match e {
        vsyn::Expr::Lit(l) => {
            match &l.lit {
                vsyn::Lit::Char(_) => true,
                _ => false,
            }
        }
        _ => false,
    }
}

fn expr_indexee_is_var(e: &vsyn::Expr, var: &str) -> bool {
    if let vsyn::Expr::Index(ix) = e {
        if let vsyn::Expr::Path(p) = &*ix.expr {
            if p.path.segments.len() == 1 {
                return p.path.segments[0].ident.to_string() == var;
            }
        }
    }
    false
}

fn expr_index_expr_is_var(e: &vsyn::Expr, var: &str) -> bool {
    if let vsyn::Expr::Index(ix) = e {
        if let vsyn::Expr::Path(p) = &*ix.index {
            if p.path.segments.len() == 1 {
                return p.path.segments[0].ident.to_string() == var;
            }
        }
    }
    false
}

fn expr_is_path_ident(e: &vsyn::Expr, var: &str) -> bool {
    if let vsyn::Expr::Path(p) = e {
        return p.path.segments.len() == 1 && p.path.segments[0].ident.to_string() == var;
    }
    false
}

fn pat_contains_ident(p: &vsyn::Pat, target: &str) -> bool {
    match p {
        vsyn::Pat::Ident(pi) => pi.ident.to_string() == target,
        vsyn::Pat::Tuple(pt) => pt.elems.iter().any(|sub| pat_contains_ident(sub, target)),
        vsyn::Pat::Type(pt) => pat_contains_ident(&pt.pat, target),
        _ => false,
    }
}

fn type_from_local_for_ident<'a>(loc: &'a vsyn::Local, var: &str) -> Option<&'a vsyn::Type> {
    match &loc.pat {
        vsyn::Pat::Type(pt) => {
            if pat_contains_ident(&pt.pat, var) { Some(&pt.ty) } else { None }
        }
        _ => None,
    }
}

fn infer_from_local_init(loc: &vsyn::Local, var: &str) -> Option<SimpleType> {
    if !pat_contains_ident(&loc.pat, var) { return None; }
    if let Some(init) = &loc.init {
        if let vsyn::Expr::Lit(l) = &*init.expr {
            if let vsyn::Lit::Int(li) = &l.lit {
                let s = li.to_string();
                if s.ends_with("usize") { return Some(SimpleType::Usize); }
                if s.ends_with("u128") { return Some(SimpleType::U128); }
                if s.ends_with("u64") || s.ends_with("u32") || s.ends_with("u16") || s.ends_with("u8") { return Some(SimpleType::UInt); }
                if s.ends_with("i128") || s.ends_with("i64") || s.ends_with("i32") || s.ends_with("i16") || s.ends_with("i8") { return Some(SimpleType::Int); }
                // no suffix: leave undecided
            }
        }
    }
    None
}

pub fn infer_var_simple_type(block: &vsyn::Block, var: &str) -> SimpleType {
    // 1) Direct local declaration with a type annotation
    for stmt in &block.stmts {
        if let vsyn::Stmt::Local(loc) = stmt {
            if let Some(ty) = type_from_local_for_ident(loc, var) {
                if type_is_vec_of_char(ty) { return SimpleType::VecChar; }
                if let Some(num_vec) = type_is_vec_of_numeric(ty) { return num_vec; }
            } else if let Some(t) = infer_from_local_init(loc, var) {
                return t;
            } else if pat_contains_ident(&loc.pat, var) {
                // No explicit type available via Pat::Type; continue
            }
        }
    }

    // 2) Usage-based inference: if we see `var[idx]` compared with a char literal, infer Vec<char>
    struct UseFinder<'a> { var: &'a str, saw_vec_char: bool }
    impl<'a, 'ast> vsyn::visit::Visit<'ast> for UseFinder<'a> {
        fn visit_expr_binary(&mut self, i: &'ast vsyn::ExprBinary) {
            let l_is_indexee = expr_indexee_is_var(&i.left, self.var);
            let r_is_indexee = expr_indexee_is_var(&i.right, self.var);
            if (l_is_indexee && lit_is_char(&i.right)) || (r_is_indexee && lit_is_char(&i.left)) {
                self.saw_vec_char = true;
            }
            verus_syn::visit::visit_expr_binary(self, i);
        }
    }
    let mut finder = UseFinder { var, saw_vec_char: false };
    vsyn::visit::Visit::visit_block(&mut finder, block);
    if finder.saw_vec_char { return SimpleType::VecChar; }

    // 3) If used as index somewhere, prefer usize
    struct IndexFinder<'a> { var: &'a str, used_as_index: bool }
    impl<'a, 'ast> vsyn::visit::Visit<'ast> for IndexFinder<'a> {
        fn visit_expr_index(&mut self, i: &'ast vsyn::ExprIndex) {
            if expr_index_expr_is_var(&vsyn::Expr::Index(i.clone()), self.var) { self.used_as_index = true; }
            verus_syn::visit::visit_expr_index(self, i);
        }
        fn visit_expr_binary(&mut self, i: &'ast vsyn::ExprBinary) {
            // index < arr.len() etc. If var appears, assume usize
            let side_has_var = |e: &vsyn::Expr| match e { vsyn::Expr::Path(p) if p.path.segments.len() == 1 && p.path.segments[0].ident.to_string() == self.var => true, _ => false };
            let side_is_len = |e: &vsyn::Expr| match e { vsyn::Expr::MethodCall(mc) => mc.method.to_string() == "len", _ => false };
            if (side_has_var(&i.left) && side_is_len(&i.right)) || (side_has_var(&i.right) && side_is_len(&i.left)) {
                self.used_as_index = true;
            }
            verus_syn::visit::visit_expr_binary(self, i);
        }
    }
    let mut idx_finder = IndexFinder { var, used_as_index: false };
    vsyn::visit::Visit::visit_block(&mut idx_finder, block);
    if idx_finder.used_as_index { return SimpleType::Usize; }

    // 4) If variable is indexed anywhere (as indexee), assume it's a numeric vector by default
    struct IndexeeFinder<'a> { var: &'a str, indexed: bool }
    impl<'a, 'ast> vsyn::visit::Visit<'ast> for IndexeeFinder<'a> {
        fn visit_expr_index(&mut self, i: &'ast vsyn::ExprIndex) {
            if expr_indexee_is_var(&vsyn::Expr::Index(i.clone()), self.var) { self.indexed = true; }
            verus_syn::visit::visit_expr_index(self, i);
        }
    }
    let mut indexee = IndexeeFinder { var, indexed: false };
    vsyn::visit::Visit::visit_block(&mut indexee, block);
    if indexee.indexed { return SimpleType::VecInt; }

    // 5) If we see `var.len()`, also assume a vector
    struct LenCallFinder<'a> { var: &'a str, saw_len: bool }
    impl<'a, 'ast> vsyn::visit::Visit<'ast> for LenCallFinder<'a> {
        fn visit_expr_method_call(&mut self, i: &'ast vsyn::ExprMethodCall) {
            if i.method.to_string() == "len" && expr_is_path_ident(&i.receiver, self.var) {
                self.saw_len = true;
            }
            verus_syn::visit::visit_expr_method_call(self, i);
        }
    }
    let mut len_finder = LenCallFinder { var, saw_len: false };
    vsyn::visit::Visit::visit_block(&mut len_finder, block);
    if len_finder.saw_len { return SimpleType::VecInt; }

    SimpleType::Unknown
}

fn rust_char_lit(ch: char) -> String {
    match ch {
        '\'' => "'\\\''".to_string(),
        '"' => "'\"'".to_string(),
        '\\' => "'\\\\'".to_string(),
        c if (c as u32) >= 0x20 && (c as u32) <= 0x7e && c != '\'' && c != '"' && c != '\\' => format!("'{}'", c),
        c => format!("'\\u{{{:x}}}'", c as u32),
    }
}

fn rust_char_lit_from_codepoint(cp: i128) -> String {
    let u = if cp < 0 { 0 } else { cp as u32 };
    if let Some(ch) = std::char::from_u32(u) {
        rust_char_lit(ch)
    } else {
        format!("'\\u{{{:x}}}'", u)
    }
}

fn to_rust_string_literal(s: &str) -> String {
    // Use serde_json to escape as JSON string, then replace surrounding quotes with Rust quotes
    serde_json::to_string(s).unwrap_or_else(|_| format!("\"{}\"", s))
}

fn parse_numbers_from_vec_like_string(s: &str) -> Option<Vec<i128>> {
    let bytes = s.as_bytes();
    let mut start = None;
    for (i, &b) in bytes.iter().enumerate() {
        if b == b'[' { start = Some(i + 1); break; }
    }
    let start = start?;
    let mut end = None;
    for (i, &b) in bytes.iter().enumerate().rev() {
        if i >= start && b == b']' { end = Some(i); break; }
    }
    let end = end?;
    let inner = &s[start..end];
    let mut out: Vec<i128> = Vec::new();
    for tok in inner.split(',') {
        let t = tok.trim();
        if t.is_empty() { continue; }
        if let Ok(v) = t.parse::<i128>() { out.push(v); } else { return None; }
    }
    Some(out)
}

pub fn emit_expr_for_type(ty: &SimpleType, val: &Value) -> String {
    match ty {
        SimpleType::Bool => match val {
            Value::Bool(b) => if *b { "true".to_string() } else { "false".to_string() },
            Value::String(s) => {
                if s.eq_ignore_ascii_case("true") { "true".to_string() } else if s.eq_ignore_ascii_case("false") { "false".to_string() } else { s.clone() }
            }
            _ => format!("{}", val),
        },
        SimpleType::Char => match val {
            Value::String(s) => {
                if s.chars().count() == 1 { rust_char_lit(s.chars().next().unwrap()) } else { rust_char_lit(s.chars().next().unwrap_or('\u{0}')) }
            }
            Value::Number(n) => {
                if let Some(i) = n.as_i64() { rust_char_lit_from_codepoint(i as i128) } else if let Some(u) = n.as_u64() { rust_char_lit_from_codepoint(u as i128) } else { rust_char_lit_from_codepoint(0) }
            }
            _ => format!("{}", val),
        },
        SimpleType::VecChar => match val {
            Value::String(s) => {
                if let Some(nums) = parse_numbers_from_vec_like_string(s) {
                    let elems: Vec<String> = nums.into_iter().map(|cp| rust_char_lit_from_codepoint(cp)).collect();
                    return format!("vec![{}]", elems.join(", "));
                }
                let elems: Vec<String> = s.chars().map(rust_char_lit).collect();
                format!("vec![{}]", elems.join(", "))
            }
            Value::Array(a) => {
                let mut elems: Vec<String> = Vec::new();
                for x in a.iter() {
                    match x {
                        Value::String(s) => {
                            for ch in s.chars() { elems.push(rust_char_lit(ch)); }
                        }
                        Value::Number(n) => {
                            if let Some(i) = n.as_i64() { elems.push(rust_char_lit_from_codepoint(i as i128)); }
                            else if let Some(u) = n.as_u64() { elems.push(rust_char_lit_from_codepoint(u as i128)); }
                        }
                        _ => {
                            // Fallback: stringize and expand chars
                            for ch in x.to_string().chars() { elems.push(rust_char_lit(ch)); }
                        }
                    }
                }
                format!("vec![{}]", elems.join(", "))
            }
            _ => {
                // Fallback: treat as string and expand
                let s = val.to_string();
                let elems: Vec<String> = s.chars().map(rust_char_lit).collect();
                format!("vec![{}]", elems.join(", "))
            }
        },
        SimpleType::VecInt | SimpleType::VecUInt => match val {
            Value::Array(a) => {
                let elems: Vec<String> = a.iter().map(|x| match x {
                    Value::Number(n) => n.to_string(),
                    Value::String(s) => s.clone(),
                    Value::Bool(b) => if *b { "1".to_string() } else { "0".to_string() },
                    _ => x.to_string(),
                }).collect();
                format!("vec![{}]", elems.join(", "))
            }
            Value::String(s) => {
                if let Some(nums) = parse_numbers_from_vec_like_string(s) {
                    let elems: Vec<String> = nums.into_iter().map(|cp| cp.to_string()).collect();
                    return format!("vec![{}]", elems.join(", "));
                }
                // If looks like vec![...] already, pass through
                let t = s.trim();
                if t.starts_with("vec![") && t.ends_with("]") { return t.to_string(); }
                if t.starts_with('[') && t.ends_with(']') { return format!("vec!{}", t); }
                s.clone()
            }
            other => other.to_string(),
        },
        SimpleType::StringT => match val {
            Value::String(s) => to_rust_string_literal(s),
            Value::Array(a) => {
                // Try to convert an array of codepoints to a string literal
                let mut s = String::new();
                for x in a {
                    match x {
                        Value::Number(n) => {
                            let cp = n.as_u64().unwrap_or(0) as u32;
                            if let Some(ch) = std::char::from_u32(cp) { s.push(ch); }
                        }
                        Value::String(ss) if ss.chars().count() == 1 => s.push(ss.chars().next().unwrap()),
                        _ => {}
                    }
                }
                to_rust_string_literal(&s)
            }
            other => other.to_string(),
        },
        SimpleType::Usize => match val {
            Value::Number(n) => format!("{}usize", n),
            Value::String(s) => {
                let ds = s.trim();
                if ds.chars().all(|c| c.is_ascii_digit()) { format!("{}usize", ds) } else { ds.to_string() }
            }
            Value::Bool(b) => if *b { "1usize".to_string() } else { "0usize".to_string() },
            other => other.to_string(),
        },
        SimpleType::U128 => match val {
            Value::Number(n) => format!("{}u128", n),
            Value::String(s) => {
                let ds = s.trim();
                if ds.chars().all(|c| c.is_ascii_digit()) { format!("{}u128", ds) } else { ds.to_string() }
            }
            Value::Bool(b) => if *b { "1u128".to_string() } else { "0u128".to_string() },
            other => other.to_string(),
        },
        SimpleType::Int | SimpleType::UInt => match val {
            Value::Number(n) => n.to_string(),
            Value::String(s) => s.clone(),
            Value::Bool(b) => if *b { "1".to_string() } else { "0".to_string() },
            other => other.to_string(),
        },
        SimpleType::Unknown => {
            // Conservative with smart fallbacks: pass through obvious literal-like strings
            match val {
                Value::String(s) => {
                    let t = s.trim();
                    if t.eq_ignore_ascii_case("true") || t.eq_ignore_ascii_case("false") { return t.to_ascii_lowercase(); }
                    if t.chars().all(|c| c.is_ascii_digit()) { return t.to_string(); }
                    if t.starts_with("vec![") && t.ends_with("]") { return t.to_string(); }
                    if t.starts_with('[') && t.ends_with(']') { return format!("vec!{}", t); }
                    to_rust_string_literal(s)
                }
                Value::Number(n) => n.to_string(),
                Value::Bool(b) => if *b { "true".to_string() } else { "false".to_string() },
                _ => val.to_string(),
            }
        }
    }
}

pub fn emit_for_var(block: &vsyn::Block, var: &str, val: &Value) -> String {
    let ty = infer_var_simple_type(block, var);
    emit_expr_for_type(&ty, val)
}
