import json

from typer.testing import CliRunner

from vinv.cli import app

runner = CliRunner()


def test_root_help_lists_groups():
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "analysis" in result.stdout
    assert "assume" in result.stdout
    assert "pipeline" in result.stdout


def test_parse_pipeline_json_output(tmp_path):
    json_path = tmp_path / "pipeline.json"
    json_path.write_text(
        json.dumps(
            {
                "task_a": {"verification_status": "verification_pass", "dataset": "mbpp"},
                "task_b": {"verification_status": "verification_error", "dataset": "mbpp"},
                "task_c": {"verification_status": "verification_pass", "dataset": "diffy"},
            }
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        ["analysis", "parse-pipeline", str(json_path), "--format", "json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["pass_counts"] == {"diffy": 1, "mbpp": 1}
    assert payload["total_counts"] == {"diffy": 1, "mbpp": 2}
    assert payload["total_pass"] == 2
    assert payload["total_entries"] == 3
