from pathlib import Path

import pytest

from vinv.pipeline.cex_harness_v2 import load_extracted_harness_v2
from vinv.pipeline.cex_validation_backend import canonicalize_generated_cex_results
from vinv.pipeline.validator_extracted_v2 import (
    _blocking_decision,
    normalize_counterexample_v2,
)


@pytest.fixture
def extracted_harness_file(tmp_path: Path) -> Path:
    path = tmp_path / "extracted_loop.rs"
    path.write_text(
        """
fn binary_search_loop1(v: &Vec<u64>, k: u64) {
    let mut i1: usize = 0;
    let mut i2: usize = v.len() - 1;
    let mut output_arr: Vec<u64> = Vec::new();
    // before loop body START
    assert(i1 <= i2);
    // before loop body END
    let ix = i1 + (i2 - i1) / 2;
    // after loop body START
    assert(i1 <= i2);
    // after loop body END
}
""".strip()
        + "\n",
        encoding="utf-8",
    )
    return path


def test_load_extracted_harness_v2_discovers_only_pre_loop_targets(
    extracted_harness_file: Path,
):
    harness = load_extracted_harness_v2(extracted_harness_file)

    assert harness.function_name == "binary_search_loop1"
    assert harness.injection_target_names == {"v", "k", "i1", "i2", "output_arr"}


def test_normalize_counterexample_v2_cleans_binary_search_style_aliases(
    extracted_harness_file: Path,
):
    harness = load_extracted_harness_v2(extracted_harness_file)
    normalized = normalize_counterexample_v2(
        {
            "3": 3,
            "__vec__v__0": 1,
            "__vec__v__1": 3,
            "__vec__v__len": 2,
            "i1_pre": 0,
            "i1_post": 1,
            "i2_pre": 2,
            "i2_post": 1,
            "ix": 1,
            "k": 3,
        },
        harness,
    )

    assert normalized.injected_assignments == {"v": "vec![1, 3]", "i1": 0, "i2": 2, "k": 3}
    assert normalized.post_state_hints == {"i1_after": 1, "i2_after": 1}
    assert normalized.dropped_keys == ["3", "ix"]


def test_canonicalize_generated_cex_results_supports_vector_pre_post_forms(
    extracted_harness_file: Path,
):
    cleaned, diagnostics = canonicalize_generated_cex_results(
        [
            {
                "__vec__output_arr_pre__0": 7,
                "__vec__output_arr_pre__len": 1,
                "__vec__output_arr__0_post": 9,
                "__vec__output_arr__len_post": 1,
                "i1": 0,
            }
        ],
        extracted_harness_file,
        backend="v2",
    )

    assert cleaned == [{"output_arr": "vec![7]", "i1": 0, "output_arr_after": "vec![9]"}]
    assert diagnostics[0]["kept"] is True
    assert diagnostics[0]["dropped_keys"] == []


def test_canonicalize_generated_cex_results_rejects_entries_without_injectable_state(
    extracted_harness_file: Path,
):
    cleaned, diagnostics = canonicalize_generated_cex_results(
        [{"3": 3, "ix": 1}],
        extracted_harness_file,
        backend="v2",
    )

    assert cleaned == []
    assert diagnostics == [
        {
            "index": 0,
            "kept": False,
            "reason": "no_injectable_assignments",
            "canonical_state": {},
            "injected_names": [],
            "post_state_hints": {},
            "alias_map": {},
            "dropped_keys": ["3", "ix"],
        }
    ]


@pytest.mark.parametrize(
    ("orig_region", "compilation_error", "detected", "failure_region", "expected"),
    [
        ("after", False, False, None, (True, "target_disappeared")),
        ("after", False, True, "before", (True, "moved_before")),
        ("before", False, True, "before", (False, "target_still_before")),
        ("after", True, False, None, (False, "compilation_error")),
    ],
)
def test_blocking_decision(
    orig_region: str | None,
    compilation_error: bool,
    detected: bool,
    failure_region: object,
    expected: tuple[bool, str],
):
    assert _blocking_decision(
        orig_failure_region=orig_region,
        compilation_error=compilation_error,
        detected=detected,
        failure_region=failure_region,
    ) == expected
