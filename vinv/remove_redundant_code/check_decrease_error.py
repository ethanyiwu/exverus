#!/usr/bin/env python3
"""Summarize Verus verification status for 1-*.rs files and emit JSON results."""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Callable, Dict, List, Optional

VERIFY_MODULE_REL = Path("..") / "verus-proof-synthesis" / "code" / "verify.py"
VEVAL_MODULE_REL = Path("..") / "verus-proof-synthesis" / "code" / "veval.py"
REPAIR_RE = re.compile(r"\bstart repair\b", re.IGNORECASE)
REFINING_RE = re.compile(r"\binfo:\s*refining\b", re.IGNORECASE)
INPUT_TOKENS_RE = re.compile(r"\binfo:\s*input tokens:\s*(\d+)\b", re.IGNORECASE)
OUTPUT_TOKENS_RE = re.compile(r"\binfo:\s*output tokens:\s*(\d+)\b", re.IGNORECASE)


@dataclass
class TimeMetadata:
    stage: str
    input_tokens: int
    output_tokens: int


class NullLogger:
    """Minimal logger stub used by VEval when no logger is provided."""

    def error(self, _msg: str) -> None:  # pragma: no cover - trivial
        pass

    def info(self, _msg: str) -> None:  # pragma: no cover - trivial
        pass

    def debug(self, _msg: str) -> None:  # pragma: no cover - trivial
        pass

@dataclass
class VerificationOutcome:
    status: str
    error_messages: List[str]
    error_traces: List[str]
    decrease_error_messages: List[str]

    @property
    def has_decreases_error(self) -> bool:
        return bool(self.decrease_error_messages)


def load_verify_module(base_dir: Path) -> ModuleType:
    verify_path = (base_dir / VERIFY_MODULE_REL).resolve()
    spec = importlib.util.spec_from_file_location("verify_module", verify_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load verify module from {verify_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_veval_module(base_dir: Path) -> ModuleType:
    veval_path = (base_dir / VEVAL_MODULE_REL).resolve()
    spec = importlib.util.spec_from_file_location("veval_module", veval_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load VEval module from {veval_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def evaluate_with_verus(result_path: Path, veval_module: ModuleType) -> VerificationOutcome:
    verus_runtime = getattr(veval_module, "verus", None)
    if verus_runtime is not None and getattr(verus_runtime, "verus_path", None) is None:
        print("Verus binary not found in PATH; marking verification as error.", file=sys.stderr)
        return VerificationOutcome(
            status="verification_error",
            error_messages=[],
            error_traces=[],
            decrease_error_messages=[],
        )

    try:
        code = result_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        print(f"Failed to read {result_path}: {exc}", file=sys.stderr)
        return VerificationOutcome(
            status="verification_error",
            error_messages=[],
            error_traces=[],
            decrease_error_messages=[],
        )

    try:
        evaluator = veval_module.VEval(code, logger=NullLogger())
        score = evaluator.eval_and_get_score(max_errs=5, json_mode=True)
    except Exception as exc:  # pragma: no cover - defensive against subprocess issues
        print(f"Verus evaluation failed for {result_path}: {exc}", file=sys.stderr)
        return VerificationOutcome(
            status="verification_error",
            error_messages=[],
            error_traces=[],
            decrease_error_messages=[],
        )

    verus_errors = getattr(evaluator, "verus_errors", [])
    error_messages: List[str] = []
    error_traces: List[str] = []
    decrease_error_messages: List[str] = []

    for err in verus_errors:
        try:
            message = getattr(err, "error_text", "")
        except Exception:
            message = ""
        if message:
            error_messages.append(message)

        trace = ""
        try:
            trace = err.get_text(snippet=False, topdown=True)
        except Exception:
            trace = message
        if trace:
            error_traces.append(trace)

        if "must have a decreases" in message.lower() or "must have a decreases" in trace.lower():
            decrease_error_messages.append(message or trace)

    if getattr(score, "compilation_error", False):
        status = "compilation_error"
    elif score.is_correct():
        status = "verification_pass"
    else:
        status = "verification_error"

    return VerificationOutcome(
        status=status,
        error_messages=error_messages,
        error_traces=error_traces,
        decrease_error_messages=decrease_error_messages,
    )


def parse_time_metadata(result_path: Path) -> Optional[TimeMetadata]:
    time_path = result_path.with_suffix(".time")
    if not time_path.exists():
        return None

    text = time_path.read_text(encoding="utf-8", errors="replace")

    if REPAIR_RE.search(text):
        stage = "Repair"
    elif REFINING_RE.search(text):
        stage = "Refinement"
    else:
        stage = "Generation"

    input_tokens = sum(int(match) for match in INPUT_TOKENS_RE.findall(text))
    output_tokens = sum(int(match) for match in OUTPUT_TOKENS_RE.findall(text))

    return TimeMetadata(stage=stage, input_tokens=input_tokens, output_tokens=output_tokens)


def parse_intermediate_dir_name(name: str) -> tuple[Optional[int], str]:
    if not name.startswith("intermediate-"):
        return (None, name)

    remainder = name[len("intermediate-"):]
    parts = remainder.split("-", 1)
    if len(parts) == 2 and parts[0].isdigit():
        return (int(parts[0]), parts[1])
    return (None, remainder)


def find_latest_final_for_case(directory: Path, case_base: str) -> Optional[Path]:
    candidates: list[tuple[int, str, Path]] = []
    for child in directory.iterdir():
        if not child.is_dir():
            continue
        stage, name = parse_intermediate_dir_name(child.name)
        if name != case_base:
            continue
        final_path = child / "final.rs"
        if final_path.exists():
            stage_key = stage if stage is not None else -1
            candidates.append((stage_key, child.name, final_path))

    if not candidates:
        return None

    candidates.sort(key=lambda item: (item[0], item[1]))
    return candidates[-1][2]


def scan_subdir(
    directory: Path,
    base_dir: Path,
    veval_module: ModuleType,
    check_fn: Callable[[Path], bool],
) -> Dict[str, Dict[str, object]]:
    results: Dict[str, Dict[str, object]] = {}
    final_cache: Dict[str, Optional[Path]] = {}

    for entry in sorted(directory.iterdir()):
        if entry.is_file() and entry.name.startswith("1-") and entry.suffix == ".rs":
            metadata = parse_time_metadata(entry)
            outcome = evaluate_with_verus(entry, veval_module)
            is_correct = check_fn(entry)

            if outcome.status == "verification_pass" and not is_correct:
                status = "verification_illegal"
            else:
                status = outcome.status

            relative_path = entry.relative_to(base_dir)
            absolute_path = base_dir / relative_path
            case_base = entry.stem[2:] if entry.stem.startswith("1-") else entry.stem

            if case_base not in final_cache:
                final_cache[case_base] = find_latest_final_for_case(directory, case_base)
            final_path = final_cache[case_base]
            final_outcome: Optional[VerificationOutcome] = None
            final_status: Optional[str] = None
            final_is_correct: Optional[bool] = None

            if final_path is not None:
                final_outcome = evaluate_with_verus(final_path, veval_module)
                final_is_correct = check_fn(final_path)
                if (
                    final_outcome.status == "verification_pass"
                    and final_is_correct is False
                ):
                    final_status = "verification_illegal"
                else:
                    final_status = final_outcome.status

            result_entry: Dict[str, object] = {
                "verification_status": status,
                "last_phase": metadata.stage.lower() if metadata else "unknown",
                "last_repaired_code_path": str(absolute_path),
                "case_name": case_base,
                "total_input_tokens": metadata.input_tokens if metadata else 0,
                "total_output_tokens": metadata.output_tokens if metadata else 0,
                "error_messages": outcome.error_messages,
                "error_traces": outcome.error_traces,
                "has_decreases_error": outcome.has_decreases_error,
                "decrease_error_messages": outcome.decrease_error_messages,
            }

            if final_path is not None and final_outcome is not None:
                result_entry.update(
                    {
                        "final_code_path": str(final_path.resolve()),
                        "final_verification_status": final_status,
                        "final_is_correct": final_is_correct,
                        "final_error_messages": final_outcome.error_messages,
                        "final_error_traces": final_outcome.error_traces,
                        "final_has_decreases_error": final_outcome.has_decreases_error,
                        "final_decrease_error_messages": final_outcome.decrease_error_messages,
                    }
                )
            else:
                result_entry.update(
                    {
                        "final_code_path": None,
                        "final_verification_status": None,
                        "final_is_correct": None,
                        "final_error_messages": [],
                        "final_error_traces": [],
                        "final_has_decreases_error": None,
                        "final_decrease_error_messages": [],
                    }
                )

            case_key = case_base
            if case_key in results:
                case_key = f"{directory.name}:{case_base}"
            results[case_key] = result_entry

    return results


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "base",
        nargs="?",
        default=Path.cwd(),
        type=Path,
        help="Base directory containing the benchmark subdirectories",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Destination JSON file (defaults to stdout)",
    )
    args = parser.parse_args(argv)

    base_dir = args.base.resolve()
    verify_module = load_verify_module(base_dir)
    veval_module = load_veval_module(base_dir)
    check_fn = verify_module.is_correct

    subdirs = sorted(
        (entry for entry in base_dir.iterdir() if entry.is_dir()),
        key=lambda path: path.name,
    )

    if not subdirs:
        print(f"No subdirectories found under {base_dir}", file=sys.stderr)
        return 1

    all_results: Dict[str, Dict[str, object]] = {}

    for subdir in subdirs:
        sub_results = scan_subdir(subdir, base_dir, veval_module, check_fn)
        for key, value in sub_results.items():
            final_key = key
            if final_key in all_results:
                print(
                    f"Warning: duplicate case entry for {key}, assigning subdirectory-qualified key",
                    file=sys.stderr,
                )
                final_key = f"{subdir.name}:{key}"
            all_results[final_key] = value

    if args.output:
        output_path = args.output.resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as out_f:
            json.dump(all_results, out_f, indent=2, sort_keys=True)
            out_f.write("\n")
    else:
        json.dump(all_results, sys.stdout, indent=2, sort_keys=True)
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
