import argparse
import json
from collections import defaultdict
from pathlib import Path


def _load_config_datasets():
    """
    Load known sub-dataset names from config. Returns a set of lowercase names.
    """
    try:
        # Local import to avoid import-time overhead for callers that do not need config
        from vinv import config as cfg
    except Exception:
        # Fall back to a sensible default set when config import fails
        return {
            # Additional datasets
            "leetcode",
            "obfuscated_verusbench",
            "humaneval_alphaverus",
            "dafnybench",
            # Verusbench subsets (useful when keys embed them)
            "cloverbench",
            "diffy",
            "mbpp",
            "misc",
        }

    dataset_name_sets = [
        getattr(cfg, "VB_BENCHMARK_VERIFIED_ENTRY_POINTS", {}).keys(),
        getattr(cfg, "VB_BENCHMARK_UNVERIFIED_ENTRY_POINTS", {}).keys(),
        getattr(cfg, "CLEANED_VB_BENCHMARK_VERIFIED_ENTRY_POINTS", {}).keys(),
        getattr(cfg, "CLEANED_VB_BENCHMARK_UNVERIFIED_ENTRY_POINTS", {}).keys(),
        getattr(cfg, "ADDITIONAL_BENCHMARK_VERIFIED_ENTRY_POINTS", {}).keys(),
        getattr(cfg, "ADDITIONAL_BENCHMARK_UNVERIFIED_ENTRY_POINTS", {}).keys(),
    ]
    known = set()
    for names in dataset_name_sets:
        for n in names:
            known.add(str(n).strip().lower())
    # Ensure defaults present even if not listed in config
    defaults = {
        "leetcode",
        "obfuscated_verusbench",
        "humaneval_alphaverus",
        "dafnybench",
        "cloverbench",
        "diffy",
        "mbpp",
        "misc",
    }
    return known.union(defaults)


def _build_dataset_token_map(known_datasets: set[str]) -> dict[str, str]:
    """
    Build a mapping from token -> canonical dataset name.
    Includes aliases to handle common abbreviations in task identifiers.
    All keys/values are lowercase.
    """
    token_to_canonical: dict[str, str] = {}
    for d in known_datasets:
        token_to_canonical[d] = d

    # Add common aliases
    if "humaneval_alphaverus" in known_datasets:
        token_to_canonical.setdefault("humaneval", "humaneval_alphaverus")
    if "obfuscated_verusbench" in known_datasets:
        token_to_canonical.setdefault("obfuscated", "obfuscated_verusbench")
    if "dafnybench" in known_datasets:
        token_to_canonical.setdefault("dafny", "dafnybench")
    if "leetcode" in known_datasets:
        token_to_canonical.setdefault("leet", "leetcode")

    return token_to_canonical


def _json_load_any(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _entry_is_verified(entry: dict) -> bool:
    status = entry.get("verification_status")
    if isinstance(status, str):
        return status.strip() == "verification_pass"
    return False


def _infer_group_from_candidates(candidates: list[str]) -> str | None:
    for c in candidates:
        if not c:
            continue
        s = str(c).lower()
        if s.startswith("additional_") or "/additional/" in s:
            return "additional"
    return None


def _infer_dataset_from_strings(
    known_datasets: set[str], candidates: list[str], group_hint: str | None = None
) -> str | None:
    # Restrict allowed datasets by group when known
    additional_set = {
        "humaneval_alphaverus",
        "leetcode",
        "obfuscated_verusbench",
        "dafnybench",
    }
    cleaned_vb_set = {"cloverbench", "diffy", "mbpp", "misc"}

    if group_hint == "additional":
        allowed = known_datasets.intersection(additional_set)
    elif group_hint == "cleaned_vb":
        allowed = known_datasets.intersection(cleaned_vb_set)
    else:
        allowed = known_datasets

    token_map = _build_dataset_token_map(allowed)
    tokens = sorted(token_map.keys(), key=len, reverse=True)
    for c in candidates:
        if not c:
            continue
        s = str(c).lower()
        for t in tokens:
            if t and t in s:
                return token_map[t]
    return None


def _infer_dataset(entry: dict, known_datasets: set[str]) -> str | None:
    # Prefer explicit fields first
    for key in ("dataset", "benchmark", "group", "sub_dataset", "entry_point"):
        if key in entry and isinstance(entry[key], str):
            inferred = _infer_dataset_from_strings(known_datasets, [entry[key]], None)
            if inferred:
                return inferred

    # Try to infer from identifiers or paths
    id_like = []
    for key in (
        "task_id",
        "id",
        "name",
        "file",
        "path",
        "source_path",
        "last_repaired_code_path",
    ):
        val = entry.get(key)
        if isinstance(val, str):
            id_like.append(val)
    group_hint = _infer_group_from_candidates(id_like)
    if group_hint is None:
        concat = " ".join(id_like).lower()
        if any(tok in concat for tok in ("cloverbench", "diffy", "mbpp", "misc")):
            group_hint = "cleaned_vb"
    inferred = _infer_dataset_from_strings(known_datasets, id_like, group_hint)
    if inferred:
        return inferred

    # Look into nested containers for dataset hints
    for container_key in ("meta", "summary", "details"):
        nested = entry.get(container_key)
        if isinstance(nested, dict):
            nested_inferred = _infer_dataset(nested, known_datasets)
            if nested_inferred:
                return nested_inferred

    return None


def _iter_records(data) -> list[dict]:
    # Normalize to a list of dict entries
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]

    if isinstance(data, dict):
        # Common containers
        for key in ("results", "data", "items"):
            v = data.get(key)
            if isinstance(v, list):
                return [x for x in v if isinstance(x, dict)]

        # If dict maps task_id -> result
        # Convert to uniform entries with the id carried along
        entries = []
        for k, v in data.items():
            if isinstance(v, dict):
                e = dict(v)
                if "task_id" not in e:
                    e["task_id"] = k
                entries.append(e)
            elif isinstance(v, str):
                # Handle schema: { task_id: "verification_pass" | "verification_error" | "compilation_error" }
                entries.append({"task_id": k, "verification_status": v})
        if entries:
            return entries

    return []


def compute_pass_counts(
    json_path: Path,
) -> tuple[dict[str, int], dict[str, int], int, int]:
    data = _json_load_any(json_path)
    known_datasets = _load_config_datasets()

    # Handle the case where top-level keys are dataset names
    if isinstance(data, dict):
        top_keys_lower = {str(k).lower(): k for k in data.keys()}
        if any(k in known_datasets for k in top_keys_lower.keys()):
            pass_counts = defaultdict(int)
            total_counts = defaultdict(int)
            total_entries = 0
            total_pass = 0
            for lower_key, original_key in top_keys_lower.items():
                if lower_key not in known_datasets:
                    continue
                bucket = data.get(original_key)
                entries = _iter_records(bucket)
                total_counts[lower_key] += len(entries)
                for e in entries:
                    total_entries += 1
                    if _entry_is_verified(e):
                        pass_counts[lower_key] += 1
                        total_pass += 1
            return dict(pass_counts), dict(total_counts), total_pass, total_entries

    # Generic flat entries
    entries = _iter_records(data)
    pass_counts = defaultdict(int)
    total_counts = defaultdict(int)
    total_entries = 0
    total_pass = 0

    for e in entries:
        total_entries += 1
        dataset = _infer_dataset(e, known_datasets) or "unknown"
        total_counts[dataset] += 1
        if _entry_is_verified(e):
            total_pass += 1
            pass_counts[dataset] += 1

    return dict(pass_counts), dict(total_counts), total_pass, total_entries


def main():
    parser = argparse.ArgumentParser(
        description="Parse pipeline result JSON and print verification pass counts per sub-dataset."
    )
    parser.add_argument(
        "--json",
        type=str,
        default=None,
        help="Path to result JSON file. Defaults to config.PIPELINE_RESULT_JSON_FILE if available.",
    )
    args = parser.parse_args()

    json_path = Path(args.json)

    if not json_path.exists():
        print(f"Error: JSON file not found: {json_path}")
        return

    pass_counts, total_counts, total_pass, total_entries = compute_pass_counts(
        json_path
    )

    if not pass_counts and not total_counts:
        print("No pass entries found or unrecognized JSON schema.")
        print(f"Scanned entries: {total_entries}")
        return

    print("Verification pass counts per sub-dataset:")
    # Use union of keys so datasets with 0 pass but >0 total are shown
    all_datasets = sorted(set(total_counts.keys()) | set(pass_counts.keys()))
    for dataset in all_datasets:
        p = pass_counts.get(dataset, 0)
        t = total_counts.get(dataset, 0)
        print(f"- {dataset}: {p} / {t}")
    print(f"Total PASS: {total_pass} / {total_entries}")


if __name__ == "__main__":
    main()
