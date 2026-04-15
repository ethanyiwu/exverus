import json
import os
import shutil

from typer.testing import CliRunner

from vinv.autoverus import (
    build_autoverus_runtime_config,
    is_correct_autoverus_output,
    parse_phase1_examples,
)
from vinv.cli import app

runner = CliRunner()


def test_parse_phase1_examples():
    assert parse_phase1_examples("3, 6 7") == ("3", "6", "7")


def test_is_correct_autoverus_output(tmp_path):
    output_file = tmp_path / "sample.rs"
    output_file.write_text("Score: (1, 0)\n", encoding="utf-8")
    assert is_correct_autoverus_output(output_file)
    output_file.write_text("Score: (0, 0)\n", encoding="utf-8")
    assert not is_correct_autoverus_output(output_file)
    output_file.write_text("Score: (1, 0)\nadmit()\n", encoding="utf-8")
    assert not is_correct_autoverus_output(output_file)


def test_build_autoverus_runtime_config_rewrites_local_paths(tmp_path):
    tool_dir = tmp_path / "tool"
    (tool_dir / "code" / "examples").mkdir(parents=True)
    (tool_dir / "code" / "lemmas").mkdir(parents=True)
    (tool_dir / "utils").mkdir(parents=True)
    config_file = tmp_path / "config.json"
    config_file.write_text(
        json.dumps(
            {
                "verus_path": "/old/verus",
                "example_path": "/old/examples",
                "lemma_path": "/old/lemmas",
                "util_path": "/old/utils",
            }
        ),
        encoding="utf-8",
    )

    runtime_config = build_autoverus_runtime_config(tool_dir=tool_dir, config_file=config_file)

    assert runtime_config["example_path"] == str(tool_dir / "code" / "examples")
    assert runtime_config["lemma_path"] == str(tool_dir / "code" / "lemmas")
    assert runtime_config["util_path"] == str(tool_dir / "utils")
    assert runtime_config["verus_path"] == (
        os.environ.get("VERUS_PATH") or shutil.which("verus") or "/old/verus"
    )


def test_autoverus_cli_run_with_fake_tool(tmp_path):
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "sample.rs").write_text("fn main() {}\n", encoding="utf-8")

    tool_dir = tmp_path / "tool"
    (tool_dir / "code" / "examples").mkdir(parents=True)
    (tool_dir / "code" / "lemmas").mkdir(parents=True)
    (tool_dir / "utils").mkdir(parents=True)
    (tool_dir / "code" / "main.py").write_text(
        "\n".join(
            [
                "import argparse",
                "import json",
                "from pathlib import Path",
                "",
                "parser = argparse.ArgumentParser()",
                "parser.add_argument('--config')",
                "parser.add_argument('--mode')",
                "parser.add_argument('--input')",
                "parser.add_argument('--output')",
                "parser.add_argument('--repair')",
                "parser.add_argument('--temp')",
                "parser.add_argument('--phase1-examples', nargs='+', default=[])",
                "parser.add_argument('--disable-one-refinement')",
                "parser.add_argument('--disable-safe', action='store_true')",
                "parser.add_argument('--repair-uniform', action='store_true')",
                "parser.add_argument('--phase-uniform', action='store_true')",
                "parser.add_argument('--disable-ranking', action='store_true')",
                "parser.add_argument('--direct-repair', action='store_true')",
                "parser.add_argument('--is-baseline', action='store_true')",
                "args = parser.parse_args()",
                "config = json.loads(Path(args.config).read_text(encoding='utf-8'))",
                "Path(args.output).write_text('Score: (1, 0)\\n', encoding='utf-8')",
                "print(",
                "    json.dumps(",
                "        {",
                "            'example_path': config['example_path'],",
                "            'lemma_path': config['lemma_path'],",
                "            'util_path': config['util_path'],",
                "            'verus_path': config['verus_path'],",
                "            'phase1_examples': args.phase1_examples,",
                "        }",
                "    )",
                ")",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    config_file = tmp_path / "config.json"
    config_file.write_text(
        json.dumps(
            {
                "verus_path": "/old/verus",
                "example_path": "/old/examples",
                "lemma_path": "/old/lemmas",
                "util_path": "/old/utils",
            }
        ),
        encoding="utf-8",
    )
    output_root = tmp_path / "runs"

    result = runner.invoke(
        app,
        [
            "autoverus",
            "run",
            "--input-dir",
            str(input_dir),
            "--tool-dir",
            str(tool_dir),
            "--config-file",
            str(config_file),
            "--output-root",
            str(output_root),
            "--name",
            "fake-run",
            "--phase1-examples",
            "8,9",
        ],
        env={"VERUS_PATH": "/tmp/fake-verus"},
    )

    assert result.exit_code == 0
    run_dir = next(output_root.iterdir())
    assert (run_dir / "1-sample.rs").read_text(encoding="utf-8") == "Score: (1, 0)\n"
    log_payload = json.loads((run_dir / "1-sample.log").read_text(encoding="utf-8"))
    assert log_payload["example_path"] == str(tool_dir / "code" / "examples")
    assert log_payload["lemma_path"] == str(tool_dir / "code" / "lemmas")
    assert log_payload["util_path"] == str(tool_dir / "utils")
    assert log_payload["verus_path"] == "/tmp/fake-verus"
    assert log_payload["phase1_examples"] == ["8", "9"]
    assert "Scheduled: 1" in result.stdout
    assert "Verified: 1 (existing 0, new 1)" in result.stdout
