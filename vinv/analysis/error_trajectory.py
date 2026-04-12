import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from vinv.config import PIPELINE_RESULTS_DIR


def _read_text_safe(path: Path) -> str:
    if path.is_file():
        try:
            return path.read_text(errors="ignore")
        except Exception:
            return ""
    return ""


def _summarize_text(text: str, max_len: int = 160) -> str:
    t = " ".join(line.strip() for line in text.strip().splitlines() if line.strip())
    if len(t) <= max_len:
        return t
    return t[: max_len - 3] + "..."


def _parse_targeted_error_from_prompt(
    prompt_text: str,
) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse the targeted verification error from a prompt text.

    Expected section (robust to minor formatting differences):
    ## Targeted Verification Error:
    - **Error Type of the Targeted Error**: <TYPE>
    - **Error Message of the Targeted Error**: <MESSAGE>\n  <possibly indented continuation lines>
    """
    if not prompt_text:
        return None, None

    type_pattern = re.compile(r"\*\*Error Type of the Targeted Error\*\*:\s*(.*)")
    msg_header_pattern = re.compile(
        r"\*\*Error Message of the Targeted Error\*\*:\s*(.*)"
    )

    lines = prompt_text.splitlines()
    targeted_section_found = False
    error_type: Optional[str] = None
    error_msg_lines: List[str] = []

    for i, line in enumerate(lines):
        if not targeted_section_found:
            if line.strip().startswith("## Targeted Verification Error"):
                targeted_section_found = True
            continue

        # Once in targeted section, try to parse type and message with some tolerance
        if error_type is None:
            m = type_pattern.search(line)
            if m:
                error_type = m.group(1).strip()
                continue

        m = msg_header_pattern.search(line)
        if m:
            # Start collecting message lines (including this line's captured tail)
            first = m.group(1).rstrip()
            if first:
                error_msg_lines.append(first)

            # Collect following lines until a blank line or another markdown header starts
            for j in range(i + 1, len(lines)):
                nxt = lines[j]
                if nxt.strip() == "" or nxt.strip().startswith("##"):
                    break
                error_msg_lines.append(nxt.rstrip())
            break

    error_msg: Optional[str] = None
    if error_msg_lines:
        # Normalize whitespace and dedent simple indentations
        joined = "\n".join(error_msg_lines).strip("\n")
        error_msg = joined

    return error_type, error_msg


def _extract_targeted_error(
    try_dir: Path,
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Return (source_file, error_type, error_message) for the targeted error of this attempt.
    It tries several known prompt files.
    """
    candidate_files = [
        "z3_prompt.txt",
        "z3_genz_prompt.txt",
        "simple_genz_prompt.txt",
        "simple_cex_prompt.txt",
    ]

    for name in candidate_files:
        p = try_dir / name
        if p.is_file():
            etype, emsg = _parse_targeted_error_from_prompt(_read_text_safe(p))
            if etype or emsg:
                return name, etype, emsg

    return None, None, None


def _extract_input_errors(try_dir: Path) -> str:
    """Read the verifier errors before repair for this attempt (input_err.txt)."""
    input_err = try_dir / "input_err.txt"
    content = _read_text_safe(input_err)
    if not content:
        # Fallback to input_out.txt if exists
        content = _read_text_safe(try_dir / "input_out.txt")
    return content


def _iter_try_dirs(gen_dir: Path) -> List[Path]:
    tries = []
    for child in gen_dir.iterdir():
        if child.is_dir() and child.name.startswith("try_"):
            try:
                _ = int(child.name.split("_")[-1])
            except ValueError:
                continue
            tries.append(child)
    tries.sort(key=lambda p: int(p.name.split("_")[-1]))
    return tries


def _collect_for_gen_dir(gen_dir: Path) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for tdir in _iter_try_dirs(gen_dir):
        input_err = _extract_input_errors(tdir)
        src, tgt_type, tgt_msg = _extract_targeted_error(tdir)
        target_type = (tgt_type or "").strip() or "CompilationError"

        rows.append(
            {
                "try": tdir.name,
                "pre_error": input_err or "",
                "target_src": src or "",
                "target_type": target_type,
                "target_msg": (tgt_msg or ""),
            }
        )
    return rows


def _find_cex_dir(
    task_dir: Path, cex_generation_strategy: str, cex_generalization_strategy: str, num_cex: int
) -> Path:
    cex_dir = (
        task_dir / f"cex_repair_{cex_generation_strategy}_{cex_generalization_strategy}_{num_cex}"
    )
    if not cex_dir.is_dir():
        raise FileNotFoundError(f"CEX repair directory not found: {cex_dir}")
    return cex_dir


def _iter_gen_dirs(cex_dir: Path) -> List[Path]:
    gens = []
    for child in cex_dir.iterdir():
        if child.is_dir() and child.name.startswith("gen_"):
            try:
                _ = int(child.name.split("_")[-1])
            except ValueError:
                continue
            gens.append(child)
    gens.sort(key=lambda p: int(p.name.split("_")[-1]))
    return gens


def _render_markdown_table(
    rows: List[Dict[str, str]], hide_messages: bool = False
) -> str:
    if not rows:
        return "No attempts found."

    headers = [
        "Try",
        "Pre-Repair Errors",
        "Targeted Error Type",
        "Targeted Error Message",
        "Source",
    ]
    md = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for r in rows:
        md.append(
            "| "
            + " | ".join(
                [
                    r["try"],
                    "" if hide_messages else _summarize_text(r["pre_error"]),
                    r["target_type"],
                    "" if hide_messages else _summarize_text(r["target_msg"]),
                    r["target_src"],
                ]
            )
            + " |"
        )
    return "\n".join(md)


def _render_log(
    rows: List[Dict[str, str]],
    task_id: Optional[str] = None,
    hide_messages: bool = False,
) -> str:
    parts: List[str] = []
    if task_id:
        parts.append(f"==== TASK: {task_id} ====")
    for r in rows:
        parts.append(f"-- {r['try']} --")
        pre = r.get("pre_error", "").rstrip()
        if pre and not hide_messages:
            parts.append("Pre-Repair Errors:")
            parts.append(pre)
        ttype = r.get("target_type", "").strip()
        tsrc = r.get("target_src", "").strip()
        tmsg = r.get("target_msg", "").rstrip()
        if ttype or tmsg or tsrc:
            parts.append("Targeted Error:")
            if ttype:
                parts.append(f"Type: {ttype}")
            if tsrc:
                parts.append(f"Source: {tsrc}")
            if tmsg and not hide_messages:
                parts.append("Message:")
                parts.append(tmsg)
        parts.append("")
    return "\n".join(parts).rstrip() + "\n"


def _collect_rows_for_task(
    task_dir: Path | str,
    cex_generation_strategy: str,
    cex_generalization_strategy: str,
    num_cex: int,
    gen_id: Optional[str] = None,
) -> List[Dict[str, str]]:
    task_path = task_dir if isinstance(task_dir, Path) else Path(task_dir)
    cex_dir = _find_cex_dir(
        task_path, cex_generation_strategy, cex_generalization_strategy, num_cex
    )

    gen_dirs: List[Path]
    if gen_id:
        gd = cex_dir / gen_id
        if not gd.is_dir():
            return []
        gen_dirs = [gd]
    else:
        gen_dirs = _iter_gen_dirs(cex_dir)

    all_rows: List[Dict[str, str]] = []
    for gd in gen_dirs:
        rows = _collect_for_gen_dir(gd)
        if not rows:
            continue
        for r in rows:
            r["try"] = f"{gd.name}/{r['try']}"
        all_rows.extend(rows)

    return all_rows


def analyze(
    task_dir: Path | str,
    cex_generation_strategy: str,
    cex_generalization_strategy: str,
    num_cex: int,
    gen_id: Optional[str] = None,
    output_format: str = "log",
    write_file: bool = False,
    output_path: Optional[Path | str] = None,
    output_append: bool = False,
    print_stdout: bool = True,
    hide_messages: bool = False,
) -> str:
    """
    Visualize the error trajectory for a task.

    Args:
        task_dir: Path to a single task's working directory under results/pipeline/<model>/<task_id>
        cex_generation_strategy: One of: "z3", "simple"
        cex_generalization_strategy: One of: "simple", "z3", "mut_val"
        gen_id: Optional specific generation id like "gen_0"; if None, include all
        output_markdown: Save a Markdown summary to the cex dir
        print_stdout: Also print the Markdown to stdout

    Returns:
        The generated Markdown content.
    """
    task_path = task_dir if isinstance(task_dir, Path) else Path(task_dir)
    all_rows = _collect_rows_for_task(
        task_path, cex_generation_strategy, cex_generalization_strategy, num_cex, gen_id
    )

    if output_format == "md":
        content = _render_markdown_table(all_rows, hide_messages=hide_messages)
    else:
        content = _render_log(
            all_rows,
            task_id=task_dir.name
            if isinstance(task_dir, Path)
            else Path(task_dir).name,
            hide_messages=hide_messages,
        )

    if write_file and output_path is not None:
        out_p = output_path if isinstance(output_path, Path) else Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        mode = "a" if output_append else "w"
        with open(out_p, mode) as f:
            f.write(content)

    if print_stdout:
        print(content, end="")

    return content


def _get_task_dir(model: str, task_id: str) -> Path:
    base = PIPELINE_RESULTS_DIR / model
    task_dir = base / task_id
    if not task_dir.is_dir():
        raise FileNotFoundError(f"Task directory not found: {task_dir}")
    return task_dir


def _iter_task_ids(model: str) -> List[str]:
    base = PIPELINE_RESULTS_DIR / model
    if not base.is_dir():
        raise FileNotFoundError(f"Model directory not found: {base}")
    return sorted([p.name for p in base.iterdir() if p.is_dir()])


def main():
    parser = argparse.ArgumentParser(
        description="Visualize error trajectory for one or all tasks."
    )
    parser.add_argument(
        "--model", required=True, help="Model directory name under results/pipeline"
    )
    parser.add_argument(
        "--task_id", default=None, help="Specific task id under the model"
    )
    parser.add_argument(
        "--all_tasks", action="store_true", help="Analyze all tasks under the model"
    )
    parser.add_argument(
        "--cex_generation_strategy",
        default="z3",
        choices=["z3", "simple"],
        help="CEX generation strategy",
    )
    parser.add_argument(
        "--cex_generalization_strategy",
        default="z3",
        choices=["simple", "z3", "mut_val"],
        help="CEX generalization strategy",
    )
    parser.add_argument(
        "--num_cex",
        default=1,
        type=int,
        help="Number of counter examples to generate",
    )
    parser.add_argument("--gen_id", default=None, help="Specific gen id like gen_0")
    parser.add_argument(
        "--format",
        default="log",
        choices=["log", "md"],
        help="Output format (default: log)",
    )
    parser.add_argument(
        "--no_messages",
        action="store_true",
        help="Do not include error message bodies in output",
    )
    parser.add_argument(
        "--output_path",
        default=None,
        help="If set, write output to this path (no writes to task dirs)",
    )
    parser.add_argument(
        "--only_success_with_verif_err",
        action="store_true",
        help=(
            "When analyzing all tasks, only include tasks that are finally verified and "
            "that fixed at least one verification error (non-compilation) along the way"
        ),
    )
    parser.add_argument(
        "--no_output_file",
        action="store_true",
        help="Do not write output file to disk",
    )
    # Backward-compat flag
    parser.add_argument(
        "--no_output_markdown", action="store_true", help=argparse.SUPPRESS
    )
    parser.add_argument(
        "--no_print",
        action="store_true",
        help="Do not print markdown to stdout",
    )

    args = parser.parse_args()

    if args.all_tasks:
        combined_md_parts: List[str] = []
        # If output_path is set and writing is enabled, clear file once
        out_path: Optional[Path] = None
        if args.output_path and not (args.no_output_file or args.no_output_markdown):
            out_path = Path(args.output_path)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text("")

        for tid in _iter_task_ids(args.model):
            task_dir = PIPELINE_RESULTS_DIR / args.model / tid
            # Only analyze tasks that contain the selected cex dir
            try:
                _find_cex_dir(
                    task_dir,
                    args.cex_generation_strategy,
                    args.cex_generalization_strategy,
                    args.num_cex,
                )
            except FileNotFoundError:
                continue

            if args.only_success_with_verif_err:
                # Check final success
                status_file = (
                    task_dir
                    / f"repair_status_{args.cex_generation_strategy}_{args.cex_generalization_strategy}.json"
                )
                final_success = False
                if status_file.is_file():
                    try:
                        data = json.loads(status_file.read_text())
                        if isinstance(data, dict) and data:
                            # take the first (and only) key
                            first = next(iter(data.values()))
                            final_success = (
                                isinstance(first, dict)
                                and first.get("verification_status")
                                == "verification_pass"
                            )
                    except Exception:
                        final_success = False

                if not final_success:
                    continue

                # Check at least one verification error targeted
                rows = _collect_rows_for_task(
                    task_dir,
                    args.cex_generation_strategy,
                    args.cex_generalization_strategy,
                    args.gen_id,
                )
                has_verif_err = any(
                    r.get("target_type") and r["target_type"] != "CompilationError"
                    for r in rows
                )
                if not has_verif_err:
                    continue

            content = analyze(
                task_dir=task_dir,
                cex_generation_strategy=args.cex_generation_strategy,
                cex_generalization_strategy=args.cex_generalization_strategy,
                gen_id=args.gen_id,
                output_format=args.format,
                write_file=bool(out_path)
                and not (args.no_output_file or args.no_output_markdown),
                output_path=out_path,
                output_append=True,
                print_stdout=not args.no_print,
                hide_messages=args.no_messages,
            )
            if not args.no_print and args.format == "md":
                combined_md_parts.append(f"\n\n### {tid}\n\n{content}")

        if combined_md_parts and not args.no_print and args.format == "md":
            print("\n".join(combined_md_parts))
        return

    if not args.task_id:
        raise SystemExit("Either --task_id or --all_tasks must be provided.")

    task_dir = _get_task_dir(args.model, args.task_id)
    # Configure single-output path if provided
    out_path_single: Optional[Path] = None
    if args.output_path and not (args.no_output_file or args.no_output_markdown):
        out_path_single = Path(args.output_path)
        out_path_single.parent.mkdir(parents=True, exist_ok=True)

    analyze(
        task_dir=task_dir,
        cex_generation_strategy=args.cex_generation_strategy,
        cex_generalization_strategy=args.cex_generalization_strategy,
        gen_id=args.gen_id,
        output_format=args.format,
        write_file=bool(out_path_single)
        and not (args.no_output_file or args.no_output_markdown),
        output_path=out_path_single,
        output_append=False,
        print_stdout=not args.no_print,
        hide_messages=args.no_messages,
    )


if __name__ == "__main__":
    main()
