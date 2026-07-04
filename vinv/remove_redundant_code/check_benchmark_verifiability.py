#!/usr/bin/env python3
"""Verify benchmark files with Veval and emit a JSON report."""

from __future__ import annotations

import argparse
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Tuple


class DummyLogger:
    """Minimal logger compatible with Veval expectations."""

    def info(self, *args, **kwargs) -> None:  # pragma: no cover
        pass

    def error(self, *args, **kwargs) -> None:  # pragma: no cover
        pass

    def warning(self, *args, **kwargs) -> None:  # pragma: no cover
        pass


def load_veval(workspace_root: Path):
    """Import and return the VEval class."""

    veval_dir = workspace_root / "verus-proof-synthesis" / "code"
    if not veval_dir.exists():
        raise SystemExit(f"veval.py not found at {veval_dir}")
    sys.path.insert(0, str(veval_dir))
    try:
        from veval import VEval  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise SystemExit(f"Unable to import VEval: {exc}") from exc
    return VEval


_VEVAL_CACHE_ROOT: Optional[Path] = None
_VEVAL_CACHE_CLS = None


def get_cached_veval_cls(workspace_root: Path):
    """Load VEval once per process and cache it."""

    global _VEVAL_CACHE_ROOT, _VEVAL_CACHE_CLS
    workspace_root = workspace_root.resolve()
    if _VEVAL_CACHE_CLS is None or _VEVAL_CACHE_ROOT != workspace_root:
        _VEVAL_CACHE_CLS = load_veval(workspace_root)
        _VEVAL_CACHE_ROOT = workspace_root
    return _VEVAL_CACHE_CLS


@dataclass(frozen=True)
class VerificationResult:
    benchmark: str
    file_path: str
    verifiable: bool
    errors: Optional[List[Dict]] = None
    compilation_error: bool = False
    rustc_stderr: Optional[str] = None
    verus_stdout: Optional[str] = None
    verification_summary: Optional[Dict] = None

    def to_json(self) -> Dict:
        payload: Dict[str, object] = {
            "benchmark": self.benchmark,
            "file": self.file_path,
            "verifiable": self.verifiable,
        }
        if self.errors:
            payload["errors"] = self.errors
        if self.compilation_error:
            payload["compilation_error"] = True
        if self.rustc_stderr:
            payload["rustc_stderr"] = self.rustc_stderr
        if self.verus_stdout:
            payload["verus_stdout"] = self.verus_stdout
        if self.verification_summary:
            payload["verification_summary"] = self.verification_summary
        return payload


@dataclass(frozen=True)
class WorkItem:
    index: int
    root_name: str
    benchmark: str
    rs_path: str
    relative_path: str


def discover_verified_files(root: Path) -> Iterator[Tuple[str, Path]]:
    """Yield (benchmark_name, rs_path) pairs for every verified/*.rs under root."""

    if not root.exists():
        raise SystemExit(f"Root path does not exist: {root}")

    for verified_dir in sorted(root.rglob("verified")):
        if not verified_dir.is_dir():
            continue
        benchmark = verified_dir.parent.relative_to(root)
        for rs_path in sorted(verified_dir.glob("*.rs")):
            yield (str(benchmark).replace(os.sep, "/"), rs_path)


def evaluate_file(
    rs_path: Path,
    benchmark: str,
    workspace_root: Path,
    max_errors: int,
) -> VerificationResult:
    veval_cls = get_cached_veval_cls(workspace_root)
    logger = DummyLogger()
    code = rs_path.read_text()
    evaluator = veval_cls(code, logger=logger)
    try:
        evaluator.eval(max_errs=max_errors, json_mode=True)
    except Exception as exc:
        error_payload = [
            {
                "message": f"Exception while running Veval: {exc}",
                "type": "PYTHON_EXCEPTION",
            }
        ]
        return VerificationResult(
            benchmark=benchmark,
            file_path=str(rs_path),
            verifiable=False,
            errors=error_payload,
        )

    verification_summary: Optional[Dict] = None
    if evaluator.verus_result:
        verification_summary = evaluator.verus_result.get("verification-results")

    errors_zero = False
    if verification_summary:
        errors = verification_summary.get("errors")
        if isinstance(errors, int) and errors == 0:
            errors_zero = True

    success = (
        errors_zero
        and not evaluator.compilation_error
        and not evaluator.verus_errors
    )
    if success:
        return VerificationResult(
            benchmark=benchmark,
            file_path=str(rs_path),
            verifiable=True,
            verification_summary=verification_summary,
        )

    error_entries: List[Dict] = []
    for err in evaluator.verus_errors:
        error_entries.append(
            {
                "message": err.error_text,
                "type": err.error.name,
                "trace": err.get_text(snippet=False),
                "spans": err.spans,
            }
        )

    rustc_stderr = evaluator.rustc_out.strip() or None
    verus_stdout = evaluator.verus_out.strip() or None

    return VerificationResult(
        benchmark=benchmark,
        file_path=str(rs_path),
        verifiable=False,
        errors=error_entries or None,
        compilation_error=evaluator.compilation_error,
        rustc_stderr=rustc_stderr,
        verus_stdout=verus_stdout,
        verification_summary=verification_summary,
    )


def parse_args(workspace_root: Path) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check if benchmark verified files still verify with Veval."
    )
    parser.add_argument(
        "--root",
        action="append",
        type=Path,
        required=True,
        help=(
            "Root directory containing benchmark subdirectories, each with a verified/ folder. "
            "May be supplied multiple times."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=workspace_root / "_output" / "benchmark_verification_report.json",
        help="Path to write the JSON result.",
    )
    parser.add_argument(
        "--max-errors",
        type=int,
        default=5,
        help="Maximum number of errors Veval should report per file (default: 5).",
    )
    parser.add_argument(
        "--limit-files",
        type=int,
        default=0,
        help="Optional limit on the total number of files to process.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the JSON output with indentation.",
    )
    parser.add_argument(
        "--show-verbose",
        action="store_true",
        help="Print verification progress for each processed file.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker processes to use (default: 1).",
    )
    return parser.parse_args()


def _worker_process(
    item: WorkItem,
    workspace_root: str,
    max_errors: int,
) -> Tuple[int, str, str, VerificationResult]:
    workspace = Path(workspace_root)
    rs_path = Path(item.rs_path)
    result = evaluate_file(rs_path, item.benchmark, workspace, max_errors)
    return (item.index, item.root_name, item.relative_path, result)


def _process_sequential(
    work_items: List[WorkItem],
    workspace_root: Path,
    max_errors: int,
    show_verbose: bool,
) -> List[Optional[Dict]]:
    buffer: List[Optional[Dict]] = [None] * len(work_items)
    for item in work_items:
        result = evaluate_file(
            Path(item.rs_path),
            item.benchmark,
            workspace_root,
            max_errors,
        )
        if show_verbose:
            status = "ok" if result.verifiable else "fail"
            print(f"[{status}] {item.root_name}/{item.relative_path}")
        record = result.to_json()
        record["file"] = f"{item.root_name}/{item.relative_path}"
        buffer[item.index] = record
    return buffer


def _process_parallel(
    work_items: List[WorkItem],
    workspace_root: Path,
    max_errors: int,
    show_verbose: bool,
    workers: int,
) -> List[Optional[Dict]]:
    buffer: List[Optional[Dict]] = [None] * len(work_items)
    workspace_root_str = str(workspace_root)
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(
                _worker_process,
                item,
                workspace_root_str,
                max_errors,
            ): item
            for item in work_items
        }
        for future in as_completed(futures):
            item = futures[future]
            try:
                idx, root_name, relative_file, result = future.result()
            except Exception as exc:
                if show_verbose:
                    print(f"[error] {item.root_name}/{item.relative_path}")
                record = {
                    "benchmark": item.benchmark,
                    "file": f"{item.root_name}/{item.relative_path}",
                    "verifiable": False,
                    "errors": [
                        {
                            "message": f"Worker exception: {exc}",
                            "type": "WORKER_EXCEPTION",
                        }
                    ],
                }
                buffer[item.index] = record
                continue

            if show_verbose:
                status = "ok" if result.verifiable else "fail"
                print(f"[{status}] {root_name}/{relative_file}")
            record = result.to_json()
            record["file"] = f"{root_name}/{relative_file}"
            buffer[idx] = record
    return buffer


def main() -> None:
    workspace_root = Path(__file__).resolve().parent
    args = parse_args(workspace_root)

    roots: List[Path] = [root.resolve() for root in args.root]

    work_items: List[WorkItem] = []
    for root in roots:
        for benchmark, rs_path in discover_verified_files(root):
            relative_file = (
                str(rs_path.relative_to(root))
                if rs_path.is_relative_to(root)
                else rs_path.name
            )
            work_items.append(
                WorkItem(
                    index=len(work_items),
                    root_name=root.name,
                    benchmark=benchmark,
                    rs_path=str(rs_path),
                    relative_path=relative_file,
                )
            )
            if args.limit_files and len(work_items) >= args.limit_files:
                break
        if args.limit_files and len(work_items) >= args.limit_files:
            break

    if not work_items:
        if args.show_verbose:
            print("No files found to process.")
        results: List[Dict] = []
    else:
        use_parallel = args.workers and args.workers > 1
        results_buffer: List[Optional[Dict]]
        if use_parallel:
            try:
                results_buffer = _process_parallel(
                    work_items,
                    workspace_root,
                    args.max_errors,
                    args.show_verbose,
                    args.workers,
                )
            except (PermissionError, OSError) as exc:
                if args.show_verbose:
                    print(
                        f"[warn] Parallel verification unavailable ({exc}); falling back to sequential."
                    )
                results_buffer = _process_sequential(
                    work_items,
                    workspace_root,
                    args.max_errors,
                    args.show_verbose,
                )
        else:
            results_buffer = _process_sequential(
                work_items,
                workspace_root,
                args.max_errors,
                args.show_verbose,
            )

        results = [record for record in results_buffer if record is not None]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    failures = [record for record in results if not record.get("verifiable", False)]
    with args.output.open("w", encoding="utf-8") as fh:
        if args.pretty:
            json.dump(failures, fh, indent=2, ensure_ascii=False)
        else:
            json.dump(failures, fh, separators=(",", ":"), ensure_ascii=False)


if __name__ == "__main__":
    main()
