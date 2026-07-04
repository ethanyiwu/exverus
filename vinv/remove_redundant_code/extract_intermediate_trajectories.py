#!/usr/bin/env python3
"""Collect ordered trajectories of intermediate `.rs` files for each AutoVerus case.

Given a results root containing `intermediate-*` directories, this script
records (in JSON) the creation timeline of every Rust snapshot that was saved
throughout the pipeline.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Iterable, List


def sanitize_relpath(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def gather_rs_files(directory: Path) -> List[tuple[Path, int]]:
    items: List[tuple[Path, int]] = []
    for rs_path in directory.rglob("*.rs"):
        try:
            mtime = rs_path.stat().st_mtime_ns
        except FileNotFoundError:
            continue
        items.append((rs_path, mtime))
    items.sort(key=lambda x: (x[1], x[0].as_posix()))
    return items


def find_intermediate_dirs(root: Path, only_pass1: bool) -> List[Path]:
    directories = [p for p in root.glob("**/intermediate-*") if p.is_dir()]
    if only_pass1:
        directories = [p for p in directories if p.name.startswith("intermediate-1-")]
    return sorted(directories)


def main(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="AutoVerus results root (contains intermediate-* directories)")
    parser.add_argument("--output", type=Path, default=Path("intermediate_trajectories.json"), help="Output JSON file")
    parser.add_argument("--include-human-time", action="store_true", help="Add ISO8601 timestamp alongside nanoseconds")
    parser.add_argument("--only-pass1", action="store_true", help="Limit to directories whose name starts with 'intermediate-1-' (pass@1 results)")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    if not root.exists():
        raise SystemExit(f"Results root {root} does not exist")

    trajectories = {}
    for inter_dir in find_intermediate_dirs(root, args.only_pass1):
        rel_dir = sanitize_relpath(inter_dir, root)
        entries = []
        for rs_path, mtime_ns in gather_rs_files(inter_dir):
            rel_file = sanitize_relpath(rs_path, root)
            record = {"path": rel_file, "timestamp_ns": mtime_ns}
            if args.include_human_time:
                record["timestamp"] = datetime.fromtimestamp(mtime_ns / 1e9).isoformat(timespec="seconds")
            entries.append(record)
        if entries:
            trajectories[rel_dir] = entries

    args.output.write_text(json.dumps(trajectories, indent=2))
    print(f"Wrote trajectories for {len(trajectories)} cases to {args.output}")


if __name__ == "__main__":
    main()
