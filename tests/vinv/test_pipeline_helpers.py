import json

import pytest

from vinv.pipeline.mut_val_generalization import parse_verdict_response
from vinv.pipeline.trajectory import TrajectoryRecorder


@pytest.mark.parametrize(
    ("text", "expected_verdict", "expected_rationale"),
    [
        (
            '{"verdict":"wrong_fact","rationale":"reachable counterexample"}',
            "wrong_fact",
            "reachable counterexample",
        ),
        (
            '{"verdict":"too_weak","rationale":"needs strengthening"}',
            "too_weak",
            "needs strengthening",
        ),
        (
            "not json",
            "other",
            "No JSON found in verdict response; defaulting to 'other'.",
        ),
    ],
)
def test_parse_verdict_response(text, expected_verdict, expected_rationale):
    assert parse_verdict_response(text) == (expected_verdict, expected_rationale)


def test_parse_verdict_response_rejects_brace_less_json_fragment():
    assert parse_verdict_response(
        '  "verdict": "too_weak",\n  "rationale": "needs strengthening"\n}'
    ) == ("other", "No JSON found in verdict response; defaulting to 'other'.")


def test_trajectory_recorder_init_run_isolates_tasks_and_preserves_resume(tmp_path):
    recorder = TrajectoryRecorder()
    recorder.enable(True)

    run1 = tmp_path / "run1"
    recorder.init_run(run1, "z3", "mut_val", 10)
    recorder.begin_iteration(1, "InvFailEnd", ["InvFailEnd"])
    recorder.record_selection(1, "mutant_1", str(run1 / "mutant.rs"), 0)

    run2 = tmp_path / "run2"
    recorder.init_run(run2, "z3", "mut_val", 10)
    assert json.loads((run2 / "trajectory.json").read_text())["iterations"] == []

    recorder.init_run(run1, "z3", "mut_val", 10)
    payload = json.loads((run1 / "trajectory.json").read_text())

    assert payload["iterations"] == [
        {
            "attempt": 1,
            "target_error": "InvFailEnd",
            "all_errors": ["InvFailEnd"],
            "mutator": None,
            "cex": {"generated": None, "validated_true": None},
            "mutants": {
                "generated": None,
                "compilable": None,
                "selected": {
                    "id": "mutant_1",
                    "path": str(run1 / "mutant.rs"),
                    "blocked_cex": 0,
                },
            },
            "status": {
                "verification_passed": None,
                "compilation_error": None,
            },
        }
    ]
