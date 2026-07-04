#!/usr/bin/env python3
"""
TRACE_GEN 主程序 - Verus 代码符号化转写与 LM 生成工具

功能说明：
1. 将 Verus 代码转换为符号化转写版本（删除 proof 代码，插入 TRACE 语句）
2. 调用 DeepSeek LM 生成测试用的 main 函数
3. 自动编译并运行生成的代码，捕获执行轨迹

调用方法：
    python3 trace_gen_stage.py <input_rs_file> <output_directory>

参数说明：
    input_rs_file: 输入的 Verus Rust 文件路径（如 benchmarks/CloverBench/verified/example.rs）
    output_directory: 输出目录路径（如 results/trace_gen_20250914_210343/example）

文件管理：
    输出目录结构：
    output_directory/
    ├── delete.rs          # 符号化转写版本（空 main 函数）
    ├── trace-gen.rs       # 包含 LM 生成的 main 函数
    ├── LM-input.txt       # 发送给 LM 的 prompt
    ├── LM-output.txt      # LM 生成的 main 函数内容
    ├── output.txt         # 编译和执行输出（包含 TRACE 轨迹）
    ├── final.json         # 循环信息元数据
    └── LM-extract.json    # 提取信息

环境要求：
    1. 设置 DeepSeek API Key: export DEEPSEEK_API_KEY=your_api_key
    2. 安装 verus 工具链
    3. Python 依赖：requests

输出结果：
    - delete.rs: 可用于进一步分析的符号化转写代码
    - trace-gen.rs: 可直接运行的完整程序
    - output.txt: 包含完整的执行轨迹，格式如下：
        COMPILATION STDOUT: [编译输出]
        COMPILATION STDERR: [编译错误]
        EXECUTION STDOUT: [执行输出，包含 TRACE 信息]
        
    执行输出示例：
        Starting program with a = [1, 2, 3], b = [4, 5]
        TRACE (loop1): a = [1, 2, 3], b = [4, 5], c = [], n = 0, len = 5
        TRACE (loop1): a = [1, 2, 3], b = [4, 5], c = [1], n = 1, len = 5
        ...
        Final result: [1, 2, 3, 4, 5]

批量处理示例：
    # 处理单个文件
    python3 trace_gen_stage.py benchmarks/CloverBench/verified/cal_div.rs results/test/cal_div
    
    # 批量处理所有文件
    for f in benchmarks/CloverBench/verified/*.rs; do
        name=$(basename "$f" .rs)
        python3 trace_gen_stage.py "$f" "results/batch/$name"
    done

注意事项：
    - 确保输入文件包含 verus!{} 块
    - LM 生成的代码可能包含语法错误，需要手动修复
    - 编译失败的文件会在 output.txt 中显示错误信息
"""

import argparse
import json
import os
import re
import requests
import subprocess
import sys
from pathlib import Path

from convert_assume import (
    read_text,
    write_text,
    find_matching_brace,
    find_functions,
    find_while_loops,
    parse_params,
    parse_lets_before,
)


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def find_verus_block(src: str):
    m = re.search(r"verus!\s*\{", src)
    if not m:
        return None
    token_start = m.start()
    open_idx = m.end() - 1
    close_idx = find_matching_brace(src, open_idx)
    if close_idx == -1:
        return None
    return (open_idx, close_idx, token_start)


def strip_specs_from_signature(signature: str) -> str:
    # Remove requires/ensures blocks from the signature chunk
    s = signature
    s = re.sub(r"\n\s*ensures[\s\S]*$", "", s, flags=re.MULTILINE)
    s = re.sub(r"\n\s*requires[\s\S]*$", "", s, flags=re.MULTILINE)
    s = normalize_return_types(s)
    return s


def normalize_return_types(signature: str) -> str:
    """Convert named return like -> (c: T) to -> T; for multi-returns -> (x:T, y:U) to -> (T, U)."""
    # Find the return type part after ->
    arrow_pos = signature.find('->')
    if arrow_pos == -1:
        return signature
    
    # Find the opening parenthesis after ->
    paren_start = signature.find('(', arrow_pos)
    if paren_start == -1:
        return signature
    
    # Find matching closing parenthesis
    depth = 0
    paren_end = -1
    for i in range(paren_start, len(signature)):
        if signature[i] == '(':
            depth += 1
        elif signature[i] == ')':
            depth -= 1
            if depth == 0:
                paren_end = i
                break
    
    if paren_end == -1:
        return signature
    
    # Extract content between parentheses
    content = signature[paren_start+1:paren_end]
    
    # Remove "name: " pattern at the beginning
    cleaned_content = re.sub(r"^[A-Za-z_][A-Za-z0-9_]*\s*:\s*", "", content.strip())
    
    return signature[:paren_start] + "(" + cleaned_content + ")"


def while_header_without_specs(func_inner: str, start_idx: int):
    """Return (cond, body_start, body_end) for a while starting at start_idx in func_inner."""
    # Determine condition similar to convert_assume
    if func_inner[start_idx + 5:start_idx + 6] == '(':
        cond_start = start_idx + 6
        depth = 1
        i = cond_start
        while i < len(func_inner) and depth > 0:
            if func_inner[i] == '(':
                depth += 1
            elif func_inner[i] == ')':
                depth -= 1
            i += 1
        cond_end = i - 1
    else:
        cond_start = start_idx + 5
        while cond_start < len(func_inner) and func_inner[cond_start].isspace():
            cond_start += 1
        cond_end = cond_start
        while cond_end < len(func_inner):
            if func_inner[cond_end] in '{' or func_inner[cond_end:cond_end+9] == 'invariant':
                break
            cond_end += 1
    condition = func_inner[cond_start:cond_end].strip()

    header_tail_start = cond_end + 1 if func_inner[start_idx + 5:start_idx + 6] == '(' else cond_end
    brace_header_idx = func_inner.find('{', header_tail_start)
    body_end = find_matching_brace(func_inner, brace_header_idx)
    return condition, brace_header_idx, body_end


def clean_while_headers_recursively(text: str) -> str:
    """Recursively clean all while headers in the text, including nested ones."""
    result = []
    i = 0
    while i < len(text):
        m = re.search(r"\bwhile\b", text[i:])
        if not m:
            result.append(text[i:])
            break
        
        start = i + m.start()
        result.append(text[i:start])
        
        # Find the while condition and opening brace
        cond, brace_idx, body_end = while_header_without_specs(text, start)
        cond = strip_wrapping_parens(cond)
        
        # Get the body content
        body_content = text[brace_idx+1:body_end]
        
        # Recursively clean nested while loops in the body
        cleaned_body = clean_while_headers_recursively(body_content)
        
        # Determine indentation
        line_start = text.rfind('\n', 0, start) + 1
        indent = re.match(r"[ \t]*", text[line_start:]).group(0)
        
        # Rebuild the while loop
        result.append(f"{indent}while ({cond})" + "{\n" + cleaned_body + "}")
        
        i = body_end + 1
    
    return ''.join(result)


def strip_proofs_from_body(body: str) -> str:
    # Remove proof statements like assert(...); assume(...); entire lines only
    body = re.sub(r"(?m)^[ \t]*assert!?\s*\([^;]*\);\s*$", "", body)
    body = re.sub(r"(?m)^[ \t]*assume\s*\([^;]*\);\s*$", "", body)
    return body


def is_vec_type(typ: str) -> bool:
    t = typ.replace('&', '').replace('mut', '').strip()
    return t.startswith('Vec<') or 'Vec<' in t


def infer_let_vec_names(pre_region: str, let_names: list[str]) -> set[str]:
    vec_names: set[str] = set()
    for name in let_names:
        # Pattern: let [mut] name: Vec<...>
        if re.search(rf"\blet\s+(?:mut\s+)?{re.escape(name)}\s*:\s*Vec<", pre_region):
            vec_names.add(name)
            continue
        # Pattern: let [mut] name = vec![...]
        if re.search(rf"\blet\s+(?:mut\s+)?{re.escape(name)}\s*=\s*vec!\[", pre_region):
            vec_names.add(name)
            continue
        # Pattern: let [mut] name = Vec::with_capacity(...)
        if re.search(rf"\blet\s+(?:mut\s+)?{re.escape(name)}\s*=\s*Vec::with_capacity\s*\(", pre_region):
            vec_names.add(name)
            continue
        # Pattern: let [mut] name = Vec::new() or Vec::<T>::new()
        if re.search(rf"\blet\s+(?:mut\s+)?{re.escape(name)}\s*=\s*Vec::(?:<[^>]+>::)?new\s*\(\s*\)", pre_region):
            vec_names.add(name)
            continue
    return vec_names


def build_trace_line(indent: str, loop_idx: int, param_name_types, let_names, pre_region: str) -> str:
    # Determine print spec and variables order: params then lets (no duplicates)
    seen: set[str] = set()
    parts: list[str] = []
    args: list[str] = []

    # Param types known
    for name, typ in param_name_types:
        if name in seen:
            continue
        seen.add(name)
        if is_vec_type(typ):
            parts.append(f"{name} = {{:?}}")
        else:
            parts.append(f"{name} = {{}}")
        args.append(name)

    # Infer let vector types heuristically from pre-region
    let_vecs = infer_let_vec_names(pre_region, let_names)
    for n in let_names:
        if n in seen:
            continue
        seen.add(n)
        if n in let_vecs:
            parts.append(f"{n} = {{:?}}")
        else:
            parts.append(f"{n} = {{}}")
        args.append(n)

    # Build println line
    fmt = ", ".join(parts)
    arglist = ", ".join(args)
    return f"{indent}println!(\"TRACE (loop{loop_idx}): {fmt}\", {arglist});"


def strip_wrapping_parens(text: str) -> str:
    s = text.strip()
    # Remove redundant single layer of wrapping parentheses: ((x)) -> x
    while len(s) >= 2 and s[0] == '(' and s[-1] == ')':
        depth = 0
        ok = True
        for i, ch in enumerate(s):
            if ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
                if depth == 0 and i != len(s) - 1:
                    ok = False
                    break
        if ok:
            s = s[1:-1].strip()
        else:
            break
    return s


def convert_vec_set_to_index(text: str) -> str:
    # Replace patterns like: name.set(idx, value); -> name[idx] = value;
    pattern = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\.\s*set\s*\(\s*([^,]+?)\s*,\s*([^)]+?)\s*\)\s*;")
    return pattern.sub(r"\1[\2] = \3;", text)


def rewrite_remove_verus_proofs(verus_body: str) -> str:
    # Process each function: drop requires/ensures; normalize while headers; drop proof stmts
    fns = find_functions(verus_body)
    if not fns:
        # Also remove top-level comments if any
        return remove_comment_only_lines(verus_body)

    out = []
    idx = 0
    for fn in fns:
        # Copy text between previous end and this function start untouched
        out.append(verus_body[idx:fn['sig_start']])
        # Build new signature
        sig = strip_specs_from_signature(fn['signature'])
        out.append(sig)
        out.append('{')

        inner = fn['body'][1:-1]

        # First clean all while headers recursively (removes all invariants/decreases)
        cleaned_inner = clean_while_headers_recursively(inner)
        
        # Then add trace lines to the cleaned version
        whiles = find_while_loops(cleaned_inner)
        rebuilt = []
        cursor = 0
        loop_idx = 1
        param_name_types = parse_params(sig)
        for wl in whiles:
            # Preceding segment
            rebuilt.append(cleaned_inner[cursor:wl['start']])
            # Compute indentation at while line
            line_start = cleaned_inner.rfind('\n', 0, wl['start']) + 1
            indent = re.match(r"[ \t]*", cleaned_inner[line_start:]).group(0)
            # While header without proofs
            cond, header_brace_idx, body_end = while_header_without_specs(cleaned_inner, wl['start'])
            cond = strip_wrapping_parens(cond)

            # Names in scope before while: lets
            pre_region = cleaned_inner[:wl['start']]
            let_names = parse_lets_before(pre_region)

            # Build trace line
            trace_line = build_trace_line(indent + "    ", loop_idx, param_name_types, let_names, pre_region)

            # Loop body content as-is
            body_inner = cleaned_inner[header_brace_idx+1:body_end]
            # Assemble
            rebuilt.append(f"{indent}while ({cond})" + "{\n" + trace_line + "\n" + body_inner + "}")

            cursor = body_end + 1
            loop_idx += 1

        rebuilt.append(cleaned_inner[cursor:])
        new_inner = ''.join(rebuilt)
        # Remove proof-only statements outside of while headers
        new_inner = strip_proofs_from_body(new_inner)
        # Convert Vec::set(i, v) to indexing assignment
        new_inner = convert_vec_set_to_index(new_inner)
        out.append(new_inner)
        out.append('}')
        idx = fn['end']

    out.append(verus_body[idx:])
    combined = ''.join(out)
    return remove_comment_only_lines(combined)


def remove_comment_only_lines(src: str) -> str:
    lines = src.splitlines()
    kept = []
    for ln in lines:
        if ln.strip().startswith('//'):
            continue
        kept.append(ln)
    return '\n'.join(kept)


def strip_vstd_and_verus_from_header(header: str) -> str:
    # Remove vstd import lines entirely
    lines = header.splitlines()
    kept = []
    for ln in lines:
        if 'use vstd::prelude::*' in ln:
            continue
        # also drop a bare 'verus!' token if present in header lines
        if 'verus!' in ln:
            continue
        if ln.strip().startswith('//'):
            continue
        kept.append(ln)
    return '\n'.join(kept)


def generate_trace(src_path: Path, out_dir: Path) -> None:
    ensure_dir(out_dir)
    src = read_text(src_path)
    span = find_verus_block(src)
    if not span:
        # just copy
        cleaned = strip_vstd_and_verus_from_header(remove_comment_only_lines(src))
        write_text(out_dir / 'convert.rs', cleaned)
        write_text(out_dir / 'delete.rs', cleaned)
        write_text(out_dir / 'output.txt', "no verus block found")
        write_text(out_dir / 'final.json', json.dumps({"loops": []}, indent=2))
        return

    s, e, tstart = span
    header = src[:tstart]
    body = src[s+1:e]
    # ignore after (closing brace and beyond) for plain Rust rebuild

    rewritten_body = rewrite_remove_verus_proofs(body)
    # Drop the verus! wrapper and vstd import. This is the symbolic rewrite (delete.rs)
    header_clean = strip_vstd_and_verus_from_header(header)
    delete_src = (header_clean + "\n" + rewritten_body).strip() + "\n"

    write_text(out_dir / 'delete.rs', delete_src)

    # Prepare LM prompt/files (LM-input.txt, LM-output.txt placeholder)
    lm_input = build_lm_prompt_for_main_only(original_src=src)
    write_text(out_dir / 'LM-input.txt', lm_input)

    # Generate trace-gen.rs with LM-generated main function
    lm_main_content = call_lm_for_main(lm_input, delete_src)
    
    # Save LM output
    print(f"LM output length: {len(lm_main_content)}")
    print(f"LM output preview: {lm_main_content[:100]}...")
    write_text(out_dir / 'LM-output.txt', lm_main_content)
    
    # Generate trace-gen.rs with the LM-generated main
    trace_gen_src = replace_main_in_code(delete_src, lm_main_content)
    write_text(out_dir / 'trace-gen.rs', trace_gen_src)

    # Compile trace-gen.rs with verus and save output
    print("Compiling trace-gen.rs with verus...")
    try:
        result = subprocess.run([
            'verus', '--no-verify', '--compile', 
            str(out_dir / 'trace-gen.rs')
        ], capture_output=True, text=True, timeout=60)
        
        # Save compilation output to output.txt
        output_content = f"COMPILATION STDOUT:\n{result.stdout}\n\nCOMPILATION STDERR:\n{result.stderr}\n\n"
        
        if result.returncode == 0:
            print("Verus compilation successful")
            
            # Try to run the compiled executable
            print("Running compiled executable...")
            try:
                # The executable should be in the same directory as the source file
                executable_path = out_dir / 'trace-gen'
                
                # Wait a moment for the executable to be created
                import time
                time.sleep(2.0)
                
                if executable_path.exists():
                    run_result = subprocess.run(
                        [str(executable_path)], 
                        capture_output=True, text=True, timeout=30
                    )
                    output_content += f"EXECUTION STDOUT:\n{run_result.stdout}\n\nEXECUTION STDERR:\n{run_result.stderr}"
                    print("Executable ran successfully")
                else:
                    output_content += "EXECUTION ERROR: Executable not found after compilation"
                    print("Executable not found after compilation")
            except subprocess.TimeoutExpired:
                output_content += "EXECUTION ERROR: Executable timed out after 30 seconds"
                print("Executable timed out")
            except Exception as e:
                output_content += f"EXECUTION ERROR: {e}"
                print(f"Error running executable: {e}")
        else:
            print(f"Verus compilation failed with return code {result.returncode}")
            
        write_text(out_dir / 'output.txt', output_content)
            
    except subprocess.TimeoutExpired:
        error_msg = "Verus compilation timed out after 60 seconds"
        print(error_msg)
        write_text(out_dir / 'output.txt', error_msg)
    except Exception as e:
        error_msg = f"Error running verus: {e}"
        print(error_msg)
        write_text(out_dir / 'output.txt', error_msg)

    # Empty placeholder for final.json
    if not (out_dir / 'final.json').exists():
        write_text(out_dir / 'final.json', "")

    # For now, produce a structural summary of loops
    loops = []
    for m in re.finditer(r"\bwhile\b", body):
        loops.append({"offset": m.start()})
    # Note: output.txt is now written by verus compilation above
    write_text(out_dir / 'final.json', json.dumps({"loops": loops}, indent=2))

    # Prepare LM prompt to rewrite 0-code.rs into delete.rs
    lm_input = build_lm_prompt(src)
    write_text(out_dir / 'LM-input.txt', lm_input)

    # LM-output.txt is now written by the LM call above

    # Minimal extract info for LM guidance/debug
    write_text(out_dir / 'LM-extract.json', json.dumps({
        "source_file": str(src_path),
        "loop_count": len(loops),
    }, indent=2))


def build_lm_prompt(original_src: str) -> str:
    """
    Construct a strict instruction prompt for the LM to transform verus code
    into a runnable Rust program named delete.rs, with proof code removed and
    a main function containing diverse labeled inputs.
    """
    # Extract the verus block content for the few-shot BEFORE
    span = find_verus_block(original_src)
    verus_before = original_src
    if span:
        # Keep a concise BEFORE including the surrounding imports and empty main
        header = original_src[:span[0]].strip()
        body = original_src[span[0]+1:span[1]].strip()
        verus_before = f"{header}\n\nverus!{{\n\n{body}\n}}\n"

    # Few-shot AFTER example (as specified by user)
    after_example = (
        "// use vstd::prelude::*\n"
        "fn main()  {\n"
        "    // input 1\n"
        "    let mut a = vec![1, 2, 3, 4, 5];\n"
        "    let mut sum = vec![0]; // 初始化为0而不是1，因为后面会重新设置\n"
        "    let N = 5;\n\n"
        "    println!(\"Starting program with a = {:?}, sum = {:?}, N = {}\", a, sum, N);\n\n"
        "    myfun(&mut a, &mut sum, N);\n\n"
        "    println!(\"Final result: a = {:?}, sum = {:?}\", a, sum);\n\n"
        "    // input 2\n"
        "    let mut a = vec![11, 22, 241980];\n"
        "    let mut sum = vec![32]; \n"
        "    let N = 3;\n\n"
        "    println!(\"Starting program with a = {:?}, sum = {:?}, N = {}\", a, sum, N);\n\n"
        "    myfun(&mut a, &mut sum, N);\n\n"
        "    println!(\"Final result: a = {:?}, sum = {:?}\", a, sum);\n\n"
        "    // input 3\n"
        "    let mut a = vec![12234112, 2312413];\n"
        "    let mut sum = vec![32231322]; \n"
        "    let N = 2;\n\n"
        "    println!(\"Starting program with a = {:?}, sum = {:?}, N = {}\", a, sum, N);\n\n"
        "    myfun(&mut a, &mut sum, N);\n\n"
        "    println!(\"Final result: a = {:?}, sum = {:?}\", a, sum);\n\n"
        "    // input 4\n"
        "    let mut a = vec![12312342, 21232413, 212312312, 231231232, 231212312, 231212312, 212312312, 231312312, 231231212, 231231212, 231231312, 231212312, 231232312, 231231212, 231231212, 212312312, 231232312, 231232312, 212312312, 1];\n"
        "    let mut sum = vec![3221322]; \n"
        "    let N = 20;\n\n"
        "    println!(\"Starting program with a = {:?}, sum = {:?}, N = {}\", a, sum, N);\n\n"
        "    myfun(&mut a, &mut sum, N);\n\n"
        "    println!(\"Final result: a = {:?}, sum = {:?}\", a, sum);\n\n"
        "    // input 5\n"
        "    let mut a = vec![124112, 21232413, 231232312, 231312312, 231212312, 23123312, 23122312, 23123123, 231231312, 2312312];\n"
        "    let mut sum = vec![231322]; \n"
        "    let N = 10;\n\n"
        "    println!(\"Starting program with a = {:?}, sum = {:?}, N = {}\", a, sum, N);\n\n"
        "    myfun(&mut a, &mut sum, N);\n\n"
        "    println!(\"Final result: a = {:?}, sum = {:?}\", a, sum);\n"
        "}\n\n\n"
        "pub fn myfun(a: &mut Vec<i32>, sum: &mut Vec<i32>, N: i32)\n"
        "{\n"
        "    let mut i: usize = 0;\n"
        "    while (i < N as usize)\n"
        "    {    // TRACE: variables at loop head could be printed here\n"
        "        println!(\"TRACE (loop1): i = {}, N = {}, a = {:?}, sum = {:?}\", i, N, a, sum);\n\n"
        "        if (i % 1 == 0) {\n"
        "            a[i] = 1;\n"
        "        } else {\n"
        "            a[i] = 0;\n"
        "        }\n"
        "        i = i + 1;\n"
        "    }\n\n"
        "    i = 0;\n"
        "    while (i < N as usize)\n"
        "    {    // TRACE: variables at loop head could be printed here\n"
        "        println!(\"TRACE (loop1): i = {}, N = {}, a = {:?}, sum = {:?}\", i, N, a, sum);\n"
        "        if (i == 0) {\n"
        "            sum[0] = 0;\n"
        "        } else {\n"
        "            let temp = sum[0];\n"
        "\t\t\tsum[0] = temp + a[i];\n"
        "        }\n"
        "        i = i + 1;\n"
        "    }\n"
        "}\n"
    )

    rules = (
        "指令（必须严格遵守）：\n"
        "1) 删除 verus 相关内容：`verus!{}` 包裹、`use vstd::prelude::*`（可改为注释）、`requires/ensures/invariant/decreases/forall/old/assume/assert` 等证明代码与规范。\n"
        "2) 不允许修改任何 while 循环体内部的操作与控制流（仅允许把 `a.set(i, v)` 改成 `a[i] = v`、`sum.set(0, v)` 改成 `sum[0] = v` 这类等价语法替换）。\n"
        "3) 删除形如 `_while1/_while2/...` 的派生函数，只保留原始函数签名与实现（去掉规范）。\n"
        "4) 生成完整 `fn main()`，包含至少 5 组多样化样例输入，严格使用如下格式与缩进：每组用 `// input k` 标注，随后三行依次是 `let mut a = ...;`、`let mut sum = ...;`、`let N = ...;`，其后三行是开头 `println!`、函数调用、结尾 `println!`，与示例一字不差（仅替换具体取值）。\n"
        "5) 所有样例输入必须满足原程序 pre-condition：`N > 0`、`a.len() == N`、`sum.len() == 1`。覆盖多样性：小 N（1）、较大 N、包含 0/负/正/边界值（接近 `i32::MIN` 和 `i32::MAX`）等。\n"
        "6) 输出必须是纯 Rust 代码，不允许任何解释性文字。输出格式必须与示例完全对齐（空行与缩进也需一致）。\n"
    )

    prompt = (
        "你是一个将 Verus/Rust 验证代码转写为可运行 Rust 的专家。\n\n"
        "【待转写（BEFORE）】\n" + verus_before + "\n\n"
        "【转写要求】\n" + rules + "\n\n"
        "【少样本演示（AFTER 示例，仅作格式参考）】\n" + after_example + "\n\n"
        "请直接输出最终的 Rust 代码（不包含任何说明文字）。\n"
    )
    return prompt


def build_lm_prompt_for_main_only(original_src: str) -> str:
    """
    Prompt that asks LM to ONLY write the main() function content, leaving all
    other functions (symbolic-transformed) intact.
    """
    span = find_verus_block(original_src)
    code_before = original_src
    if span:
        s, e, tstart = span
        header = original_src[:tstart]
        body = original_src[s+1:e]
        code_before = (strip_vstd_and_verus_from_header(header) + "\n" + rewrite_remove_verus_proofs(body)).strip()

    guidance = (
        "你是一个 Rust 代码生成专家。请为以下代码生成一个完整的 main() 函数。\n\n"
        "【要求】\n"
        "1) 只生成 main() 函数的内容（不包含 fn main() 声明）\n"
        "2) 生成至少 5 组多样化样例输入，按如下格式：\n"
        "   // input 1\n"
        "   let mut a = vec![1, 2, 3];\n"
        "   let mut b = vec![4, 5];\n"
        "   println!(\"Starting program with a = {:?}, b = {:?}\", a, b);\n"
        "   let result = function_name(&mut a, &b);\n"
        "   println!(\"Final result: {:?}\", result);\n\n"
        "3) 保证输入满足函数的 requires 约束（长度匹配、数值范围等）\n"
        "4) 只输出 main 函数体内容，不要其他解释\n\n"
        "【参考代码】\n" + code_before + "\n\n"
        "请直接输出 main 函数体内容："
    )

    return guidance


def call_deepseek_api(prompt: str) -> str:
    """
    Call DeepSeek API to generate main function content.
    """
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if not api_key:
        print("Warning: DEEPSEEK_API_KEY environment variable not set, using fallback")
        return None
    
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "deepseek-chat",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.7,
        "max_tokens": 2000
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        content = result['choices'][0]['message']['content'].strip()
        
        # Clean up markdown code blocks if present
        if content.startswith('```rust'):
            content = content[7:]  # Remove ```rust
        if content.startswith('```'):
            content = content[3:]   # Remove ```
        if content.endswith('```'):
            content = content[:-3]  # Remove trailing ```
        
        return content.strip()
    except Exception as e:
        print(f"Error calling DeepSeek API: {e}")
        # Fallback to placeholder
        return None


def call_lm_for_main(prompt: str, delete_src: str) -> str:
    """
    Call LM to generate main function content.
    """
    # Try to call DeepSeek API first
    print("Calling DeepSeek API...")
    lm_output = call_deepseek_api(prompt)
    
    if lm_output:
        print("DeepSeek API call successful")
        return lm_output
    
    # Fallback to placeholder if API fails
    print("Using fallback placeholder main function")
    fns = find_functions(delete_src)
    fn_name = "function_name"
    if fns:
        for fn in fns:
            if fn['name'] != 'main':
                fn_name = fn['name']
                break
    
    return f"""    // input 1
    let mut a = vec![1, 2, 3];
    let mut b = vec![4, 5];
    println!("Starting program with a = {{:?}}, b = {{:?}}", a, b);
    let result = {fn_name}(&mut a, &b);
    println!("Final result: {{:?}}", result);

    // input 2
    let mut a = vec![10, 20];
    let mut b = vec![30];
    println!("Starting program with a = {{:?}}, b = {{:?}}", a, b);
    let result = {fn_name}(&mut a, &b);
    println!("Final result: {{:?}}", result);

    // input 3
    let mut a = vec![100];
    let mut b = vec![200, 300, 400];
    println!("Starting program with a = {{:?}}, b = {{:?}}", a, b);
    let result = {fn_name}(&mut a, &b);
    println!("Final result: {{:?}}", result);

    // input 4
    let mut a = vec![0, 1, 2, 3, 4];
    let mut b = vec![5, 6];
    println!("Starting program with a = {{:?}}, b = {{:?}}", a, b);
    let result = {fn_name}(&mut a, &b);
    println!("Final result: {{:?}}", result);

    // input 5
    let mut a = vec![42];
    let mut b = vec![24, 35];
    println!("Starting program with a = {{:?}}, b = {{:?}}", a, b);
    let result = {fn_name}(&mut a, &b);
    println!("Final result: {{:?}}", result);"""


def replace_main_in_code(code: str, new_main_content: str) -> str:
    """
    Replace the main function content in the code with new content.
    """
    # Find the main function
    main_match = re.search(r"fn\s+main\s*\(\s*\)\s*\{", code)
    if not main_match:
        # If no main function, add one
        return code + "\n\nfn main() {\n" + new_main_content + "\n}"
    
    main_start = main_match.start()
    brace_start = main_match.end() - 1  # position of '{'
    brace_end = find_matching_brace(code, brace_start)
    if brace_end == -1:
        # Malformed main function, add new one
        return code + "\n\nfn main() {\n" + new_main_content + "\n}"
    
    # Replace main function content
    before = code[:main_start]
    main_header = code[main_start:brace_start]
    after = code[brace_end+1:]
    
    return before + main_header + "{\n" + new_main_content + "\n}" + after


def main():
    parser = argparse.ArgumentParser(description='trace_gen stage runner')
    parser.add_argument('input_rs', type=Path, help='path to source rs for LM rewrite (e.g., convert/0-code.rs)')
    parser.add_argument('out_dir', type=Path, help='trace_gen/ output directory')
    args = parser.parse_args()

    generate_trace(args.input_rs.resolve(), args.out_dir.resolve())
    print(f"trace_gen stage complete: {args.out_dir}")


if __name__ == '__main__':
    main()


