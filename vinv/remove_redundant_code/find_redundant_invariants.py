#!/usr/bin/env python3
"""Utility to identify redundant Verus invariants in verusbench_cleaned."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from itertools import islice
from pathlib import Path
from typing import List, Sequence


class DummyLogger:
    def info(self, *args, **kwargs) -> None:  # pragma: no cover
        pass

    def error(self, *args, **kwargs) -> None:  # pragma: no cover
        pass

    def warning(self, *args, **kwargs) -> None:  # pragma: no cover
        pass


@dataclass
class Candidate:
    kind: str
    block_index: int
    clause_index: int
    line_indices: Sequence[int]
    preview: str


def discover_subdirs(root: Path) -> List[Path]:
    return sorted(
        [path for path in root.iterdir() if path.is_dir()],
        key=lambda path: path.name,
    )


def load_veval(workspace_root: Path):
    veval_dir = workspace_root / "verus-proof-synthesis" / "code"
    if not veval_dir.exists():
        raise SystemExit(f"veval.py not found at {veval_dir}")
    sys.path.insert(0, str(veval_dir))
    try:
        from veval import VEval  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise SystemExit(f"Unable to import VEval: {exc}") from exc
    return VEval


def leading_ws(line: str) -> int:
    stripped = line.lstrip(" \t")
    return len(line) - len(stripped)


def is_invariant_header(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("invariant") and not stripped.startswith("//")


def collect_invariant_block(lines: Sequence[str], start_idx: int) -> List[int]:
    result: List[int] = []
    indent_ref = leading_ws(lines[start_idx])
    j = start_idx + 1
    while j < len(lines):
        line = lines[j]
        stripped = line.strip()
        indent = leading_ws(line)
        if stripped == "":
            break
        if stripped.startswith("//"):
            j += 1
            continue
        if indent <= indent_ref:
            break
        lowered = stripped.split("(", 1)[0].strip()
        lowered = lowered.split(" ", 1)[0]
        if lowered in {
            "decreases",
            "ensures",
            "requires",
            "assert",
            "while",
            "for",
            "loop",
            "if",
            "match",
            "return",
            "break",
            "continue",
            "proof",
            "lemma",
            "calc",
            "open",
            "close",
            "fold",
            "unfold",
            "spec",
            "exec",
            "ghost",
            "let",
        }:
            break
        if stripped.startswith("{") or stripped.startswith("}"):
            break
        result.append(j)
        j += 1
    return result


def split_clauses(lines: Sequence[str], block_indices: Sequence[int]) -> List[Sequence[int]]:
    clauses: List[List[int]] = []
    current: List[int] = []
    for idx in block_indices:
        stripped = lines[idx].strip()
        if not stripped or stripped.startswith("//"):
            continue
        current.append(idx)
        trimmed = stripped.split("//", 1)[0].rstrip()
        if trimmed.endswith(","):
            clauses.append(current)
            current = []
    if current:
        clauses.append(current)
    return clauses


def extract_invariants(lines: Sequence[str]) -> List[Candidate]:
    invariants: List[Candidate] = []
    block_counter = 0
    for idx, line in enumerate(lines):
        if not is_invariant_header(line):
            continue
        block = collect_invariant_block(lines, idx)
        if not block:
            block_counter += 1
            continue
        clauses = split_clauses(lines, block)
        for clause_idx, clause in enumerate(clauses):
            preview = " ".join(lines[i].strip() for i in clause)
            invariants.append(
                Candidate(
                    kind="invariant",
                    block_index=block_counter,
                    clause_index=clause_idx,
                    line_indices=tuple(clause),
                    preview=preview,
                )
            )
        block_counter += 1
    return invariants


def line_without_comment(line: str) -> str:
    return line.split("//", 1)[0]


def is_proof_block_start(line: str) -> bool:
    stripped = line.strip()
    if not stripped or stripped.startswith("//"):
        return False
    without_comment = line_without_comment(line).strip()
    if not without_comment.startswith("proof"):
        return False
    remainder = without_comment[len("proof") :].lstrip()
    return remainder.startswith("{")


def collect_proof_block(lines: Sequence[str], start_idx: int) -> List[int]:
    indices = [start_idx]
    without_comment = line_without_comment(lines[start_idx])
    open_braces = without_comment.count("{") - without_comment.count("}")
    idx = start_idx
    while open_braces > 0 and idx + 1 < len(lines):
        idx += 1
        indices.append(idx)
        without_comment = line_without_comment(lines[idx])
        open_braces += without_comment.count("{")
        open_braces -= without_comment.count("}")
    return indices


def collect_statement_until_semicolon(
    lines: Sequence[str],
    start_idx: int,
) -> List[int]:
    indices = [start_idx]
    if ";" in line_without_comment(lines[start_idx]):
        return indices
    j = start_idx + 1
    while j < len(lines):
        indices.append(j)
        if ";" in line_without_comment(lines[j]):
            break
        j += 1
    return indices


def is_assert_line(stripped: str) -> bool:
    if not stripped.startswith("assert"):
        return False
    rest = stripped[len("assert") :]
    if not rest:
        return False
    first = rest[0]
    if first == "!":
        return False
    if first not in {"(", " ", "\t"}:
        return False
    return True


def extract_asserts(lines: Sequence[str]) -> List[Candidate]:
    results: List[Candidate] = []
    counter = 0
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            idx += 1
            continue
        if not is_assert_line(stripped):
            idx += 1
            continue
        statement = collect_statement_until_semicolon(lines, idx)
        preview = " ".join(lines[i].strip() for i in statement)
        results.append(
            Candidate(
                kind="assert",
                block_index=counter,
                clause_index=0,
                line_indices=tuple(statement),
                preview=preview,
            )
        )
        counter += 1
        idx = statement[-1] + 1
    return results


def extract_proof_function_attrs(lines: Sequence[str]) -> List[Candidate]:
    results: List[Candidate] = []
    counter = 0
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("//"):
            continue
        if stripped.startswith("#[verifier::proof_function"):
            results.append(
                Candidate(
                    kind="proof_function",
                    block_index=counter,
                    clause_index=0,
                    line_indices=(idx,),
                    preview=stripped,
                )
            )
            counter += 1
    return results


def extract_proof_blocks(lines: Sequence[str]) -> List[Candidate]:
    results: List[Candidate] = []
    counter = 0
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        if not is_proof_block_start(line):
            idx += 1
            continue
        block_indices = collect_proof_block(lines, idx)
        preview = lines[block_indices[0]].strip()
        results.append(
            Candidate(
                kind="proof_block",
                block_index=counter,
                clause_index=0,
                line_indices=tuple(block_indices),
                preview=preview,
            )
        )
        counter += 1
        idx = block_indices[-1] + 1
    return results


def collect_candidates(
    lines: Sequence[str],
    include_asserts: bool,
    include_proof_functions: bool,
    include_proof_blocks: bool,
) -> List[Candidate]:
    candidates: List[Candidate] = list(extract_invariants(lines))
    if include_asserts:
        candidates.extend(extract_asserts(lines))
    if include_proof_functions:
        candidates.extend(extract_proof_function_attrs(lines))
    if include_proof_blocks:
        candidates.extend(extract_proof_blocks(lines))
    candidates.sort(key=lambda cand: (cand.line_indices[0], cand.kind))
    return candidates


def comment_line(line: str) -> str:
    if line.lstrip().startswith("//"):
        return line
    indent = line[: leading_ws(line)]
    remainder = line[len(indent) :]
    if remainder.startswith("//"):
        return line
    prefix = "// " if remainder and not remainder.startswith("//") else "//"
    return f"{indent}{prefix}{remainder}"


def comment_clause(lines: Sequence[str], clause: Candidate) -> List[str]:
    updated = list(lines)
    for idx in clause.line_indices:
        updated[idx] = comment_line(updated[idx])
    return updated


def render_without_clauses(
    lines: Sequence[str],
    clauses: Sequence[Candidate],
) -> List[str]:
    remove_indices = set()
    for clause in clauses:
        remove_indices.update(clause.line_indices)
    return [line for idx, line in enumerate(lines) if idx not in remove_indices]


def evaluate(code: str, veval_cls, logger: DummyLogger) -> bool:
    try:
        evaluator = veval_cls(code, logger=logger)
        evaluator.eval(max_errs=1, json_mode=True)
    except Exception:
        return False
    result = evaluator.verus_result
    if not result:
        return False
    verification = result.get("verification-results", {})
    if not verification:
        return False
    if evaluator.compilation_error:
        return False
    if evaluator.verus_errors:
        return False
    errors = verification.get("errors")
    if errors is None:
        return False
    return errors == 0


def write_variant(
    output_root: Path,
    root: Path,
    original_path: Path,
    clause: Candidate,
    content: Sequence[str],
) -> Path:
    rel_parent = original_path.parent.relative_to(root)
    filename = original_path.name
    variant_path = output_root / rel_parent / filename
    variant_path.parent.mkdir(parents=True, exist_ok=True)
    variant_path.write_text("".join(content))
    return variant_path


def write_combined_variant(
    output_root: Path,
    root: Path,
    original_path: Path,
    clauses: Sequence[Candidate],
    content: Sequence[str],
) -> Path:
    rel_parent = original_path.parent.relative_to(root)
    filename = original_path.name
    variant_path = output_root / rel_parent / filename
    variant_path.parent.mkdir(parents=True, exist_ok=True)
    variant_path.write_text("".join(content))
    return variant_path


def maximize_component_removal(
    lines: Sequence[str],
    clauses: Sequence[Candidate],
    veval_cls,
    logger: DummyLogger,
) -> tuple[List[Candidate], List[str]]:
    accepted: List[Candidate] = []
    current_lines: List[str] = list(lines)
    for clause in clauses:
        candidate_lines = comment_clause(current_lines, clause)
        code = "".join(candidate_lines)
        if not evaluate(code, veval_cls, logger):
            continue
        accepted.append(clause)
        current_lines = candidate_lines
    return accepted, current_lines


def process_file(
    path: Path,
    root: Path,
    output_root: Path,
    veval_cls,
    logger: DummyLogger,
    dry_run: bool,
    verbose: bool,
    include_asserts: bool,
    include_proof_functions: bool,
    include_proof_blocks: bool,
):
    text = path.read_text()
    lines = text.splitlines(keepends=True)
    candidates = collect_candidates(
        lines,
        include_asserts=include_asserts,
        include_proof_functions=include_proof_functions,
        include_proof_blocks=include_proof_blocks,
    )
    if not candidates:
        if verbose:
            print(f"[skip] {path.relative_to(root)} (no candidates)")
        return candidates, []
    individually_redundant: List[Candidate] = []
    for clause in candidates:
        modified_lines = comment_clause(lines, clause)
        code = "".join(modified_lines)
        passes = evaluate(code, veval_cls, logger)
        if not passes:
            continue
        individually_redundant.append(clause)
    if not individually_redundant:
        if verbose:
            print(
                f"[done] {path.relative_to(root)}: 0/{len(candidates)} candidates redundant"
            )
        return candidates, []

    accepted_clauses, combined_lines = maximize_component_removal(
        lines,
        individually_redundant,
        veval_cls,
        logger,
    )
    if not accepted_clauses:
        if verbose:
            print(
                f"[done] {path.relative_to(root)}: 0/{len(candidates)} candidates removable in combination"
            )
        return candidates, []

    output_path: Path | None = None
    final_lines = render_without_clauses(lines, accepted_clauses)
    final_code = "".join(final_lines)
    if not evaluate(final_code, veval_cls, logger):
        if verbose:
            print(
                f"[warn] {path.relative_to(root)}: removal-only variant failed verification, keeping commented version"
            )
        final_lines = combined_lines
        final_code = "".join(final_lines)
        if not evaluate(final_code, veval_cls, logger):
            if verbose:
                print(
                    f"[warn] {path.relative_to(root)}: commented variant no longer verifies; skipping write"
                )
            return candidates, []
    if not dry_run:
        output_path = write_combined_variant(
            output_root,
            root,
            path,
            accepted_clauses,
            final_lines,
        )
    successes = [
        {
            "clause": clause,
            "path": output_path,
        }
        for clause in accepted_clauses
    ]
    if verbose:
        total = len(candidates)
        ok = len(accepted_clauses)
        indiv = len(individually_redundant)
        print(
            f"[done] {path.relative_to(root)}: {ok}/{total} stored (individually redundant: {indiv})"
        )
    return candidates, successes


def main() -> None:
    workspace_root = Path(__file__).resolve().parent

    parser = argparse.ArgumentParser(
        description="Comment out Verus invariants one at a time and re-verify",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Root directory containing the verusbench_cleaned data (defaults to dataset root)",
    )
    parser.add_argument(
        "--file",
        type=Path,
        help="Process a single Verus source file instead of discovering directories",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=workspace_root / "verusbench_redundant_invariants",
        help="Destination for variants that still verify",
    )
    parser.add_argument(
        "--limit-files",
        type=int,
        default=0,
        help="Optional limit on the number of files to process",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run verification without writing out variants",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print progress information",
    )
    parser.add_argument(
        "--no-asserts",
        dest="include_asserts",
        action="store_false",
        default=True,
        help="Skip checking assert statements for redundancy",
    )
    parser.add_argument(
        "--no-proof-functions",
        dest="include_proof_functions",
        action="store_false",
        default=True,
        help="Skip checking #[verifier::proof_function] attributes for redundancy",
    )
    parser.add_argument(
        "--no-proof-blocks",
        dest="include_proof_blocks",
        action="store_false",
        default=True,
        help="Skip checking proof { ... } blocks for redundancy",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker threads for parallel file processing (default: 1)",
    )
    args = parser.parse_args()

    default_root = workspace_root / "verusbench_cleaned"

    single_file: Path | None = None
    if args.file is not None:
        single_file = args.file.resolve()
        if not single_file.exists():
            raise SystemExit(f"Specified file does not exist: {single_file}")
        if not single_file.is_file():
            raise SystemExit(f"Specified path is not a file: {single_file}")
        if single_file.suffix != ".rs":
            raise SystemExit(f"Specified file is not a .rs source: {single_file}")

    if args.root is None:
        if single_file is not None:
            root = single_file.parent
        else:
            root = default_root
    else:
        root = args.root.resolve()

    if not root.exists():
        raise SystemExit(f"Root path does not exist: {root}")

    if single_file is not None and not single_file.is_relative_to(root):
        raise SystemExit(
            f"File {single_file} is not located within root {root}. "
            "Pass an explicit --root that is an ancestor of the file.",
        )

    output_root = args.output.resolve()
    if not args.dry_run:
        output_root.mkdir(parents=True, exist_ok=True)

    veval_cls = load_veval(workspace_root)
    logger = DummyLogger()

    summary = []
    files_processed = 0

    def iter_rs_files():
        if single_file is not None:
            yield single_file
            return
        for subdir_path in discover_subdirs(root):
            verified_dir = subdir_path / "verified"
            if not verified_dir.exists():
                continue
            for rs_path in sorted(verified_dir.glob("*.rs")):
                yield rs_path
    if args.limit_files and args.limit_files > 0:
        rs_paths = list(islice(iter_rs_files(), args.limit_files))
    else:
        rs_paths = list(iter_rs_files())

    if not rs_paths and args.verbose:
        print("No files found to process.")

    max_workers = args.workers if args.workers and args.workers > 0 else (os.cpu_count() or 1)

    def worker(rs_path: Path):
        candidates, successes = process_file(
            rs_path,
            root,
            output_root,
            veval_cls,
            logger,
            args.dry_run,
            args.verbose,
            args.include_asserts,
            args.include_proof_functions,
            args.include_proof_blocks,
        )
        return rs_path, candidates, successes

    def handle_result(rs_path: Path, candidates, successes):
        nonlocal files_processed
        files_processed += 1
        entry = {
            "file": str(rs_path.relative_to(root)),
            "total_candidates": len(candidates),
            "redundant": [
                {
                    "kind": item["clause"].kind,
                    "block_index": item["clause"].block_index,
                    "clause_index": item["clause"].clause_index,
                    "preview": item["clause"].preview,
                    "output_path": str(item["path"])
                    if item["path"] is not None
                    else None,
                }
                for item in successes
            ],
        }
        summary.append(entry)

    if max_workers <= 1 or len(rs_paths) <= 1:
        for rs_path, candidates, successes in map(worker, rs_paths):
            handle_result(rs_path, candidates, successes)
    else:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for rs_path, candidates, successes in executor.map(worker, rs_paths):
                handle_result(rs_path, candidates, successes)

    redundant_counts = [len(entry["redundant"]) for entry in summary]
    total_redundant = sum(redundant_counts)
    files_with_redundant = sum(1 for count in redundant_counts if count > 0)
    redundant_by_kind: Counter[str] = Counter()
    files_with_kind: Counter[str] = Counter()
    for entry in summary:
        if not entry["redundant"]:
            continue
        kinds_in_file = set()
        for item in entry["redundant"]:
            kind = item["kind"]
            redundant_by_kind[kind] += 1
            kinds_in_file.add(kind)
        for kind in kinds_in_file:
            files_with_kind[kind] += 1

    stats = {
        "files_processed": files_processed,
        "files_with_redundant": files_with_redundant,
        "total_redundant_components": total_redundant,
        "redundant_by_kind": dict(redundant_by_kind),
        "files_with_redundant_by_kind": dict(files_with_kind),
    }
    if summary:
        stats["average_redundant_per_file"] = (
            total_redundant / len(summary)
        )
        stats["max_redundant_in_file"] = max(redundant_counts)
    else:
        stats["average_redundant_per_file"] = 0.0
        stats["max_redundant_in_file"] = 0
    if files_with_redundant:
        stats["average_redundant_per_redundant_file"] = (
            total_redundant / files_with_redundant
        )
    else:
        stats["average_redundant_per_redundant_file"] = 0.0

    if summary and not args.dry_run:
        summary_path = output_root / "summary.json"
        summary_path.write_text(json.dumps(summary, indent=2))
        stats_path = output_root / "summary_stats.json"
        stats_path.write_text(json.dumps(stats, indent=2))
        if args.verbose:
            print(f"Summary written to {summary_path}")
            print(f"Statistics written to {stats_path}")
    elif args.dry_run and summary:
        print(json.dumps(summary, indent=2))
        print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
