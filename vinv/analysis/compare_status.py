#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple, Union

PASS_FIELD = "verification_pass"

CANDIDATE_TASK_KEYS: Tuple[str, ...] = (
    "task",
    "name",
    "id",
    "task_id",
    "benchmark",
    "example",
)


def read_json_file(path: Path) -> Union[dict, list]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def read_json_lines_file(path: Path) -> List[dict]:
    raise ValueError("Only JSON files are supported.")


def coerce_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return value != 0
    s = str(value).strip().lower()
    if s in {
        "true",
        "t",
        "yes",
        "y",
        "1",
        "pass",
        "passed",
        "ok",
        "success",
        "succeeded",
    }:
        return True
    if s in {"false", "f", "no", "n", "0", "fail", "failed"}:
        return False
    return False


def load_status_map(path: Path) -> Dict[str, bool]:
    """
    Returns a mapping: task_id -> bool(verification_pass)
    Supports JSON only.
    Expected formats (top-level dict):
      - { "<task_id>": { "verification_status": "verification_pass" | ... , ... }, ... }
      - { "<task_id>": { "status": "verification_pass" | ... , ... }, ... }
      - { "<task_id>": { "verification_passed": true | false, ... }, ... }
    """
    if path.suffix.lower() != ".json":
        raise ValueError(f"Only JSON files are supported: {path}")

    data = read_json_file(path)
    if not isinstance(data, dict):
        raise ValueError(
            f"Expected a JSON object mapping task_id -> status dict in {path}"
        )

    status_map: Dict[str, bool] = {}
    for task_id, row in data.items():
        passed = False
        if isinstance(row, dict):
            if "verification_status" in row:
                passed = (
                    str(row.get("verification_status", "")).strip()
                    == "verification_pass"
                )
            elif "status" in row:
                passed = str(row.get("status", "")).strip() == "verification_pass"
            elif "verification_passed" in row:
                passed = coerce_bool(row.get("verification_passed", False))
            elif PASS_FIELD in row:
                passed = coerce_bool(row.get(PASS_FIELD, False))
        elif isinstance(row, str):
            passed = row.strip() == "verification_pass"
        elif isinstance(row, bool):
            passed = row

        if task_id and task_id != "None":
            status_map[str(task_id)] = bool(passed)

    return status_map


def compute_a_only_pass(a_map: Dict[str, bool], b_map: Dict[str, bool]) -> List[str]:
    return sorted(
        [t for t, a_passed in a_map.items() if a_passed and not b_map.get(t, False)]
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="List tasks solved by A only (verification_pass)."
    )
    parser.add_argument("a_path", type=Path, help="Status file A (JSON)")
    parser.add_argument("b_path", type=Path, help="Status file B (JSON)")
    args = parser.parse_args()

    a_map = load_status_map(args.a_path)
    b_map = load_status_map(args.b_path)

    only_a = compute_a_only_pass(a_map, b_map)
    for task in only_a:
        print(task)


if __name__ == "__main__":
    main()
