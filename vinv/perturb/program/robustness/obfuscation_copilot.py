from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

DEFAULT_MODEL = "gpt-5"
DEFAULT_CASE_ROOT = Path("VeruSAGE_sampled")
DEFAULT_PROMPT_FILE = Path("vinv") / "prompt" / "obfuscate_pro_plus.txt"
DEFAULT_TIMEOUT = 3600
DEFAULT_COPILOT_CONFIG = Path.home() / ".copilot" / "config.json"

BASE_INSTRUCTIONS = """\
We now want to obfuscate the verified program in VeruSAGE_sampled.

Specifically, you need to read the verified code of a case, and then perform
obfuscation according to the instructions below:

### Detailed instructions begin

<prompt_file_contents>

### Detailed instructions end.

You are required to perform a multi-stage obfuscation, using 5 stages to
obfuscate the code. Each stage uses the output of the previous stage as input,
and the input for the first stage is the original verified program. 

Across the 5 stages, apply changes from easy to hard, keep them non-redundant,
and make each stage use different techniques (try to avoid repeating the same kind of
transformation across stages). Use the detailed instructions and the change.txt
record to plan stage-specific modifications, so that each stage is a distinct
step toward higher obfuscation difficulty. The goal is to maximize obfuscation
within the requirements: increase unreadability and logical complexity while
still meeting all verification and change constraints.

You should not use any comments or use any variable names to indicate you are doing obfuscation.

Also, don't
make any changes that change the semantics of the program. 

If the file is very long, you may focus on obfuscating on a certain part of the code,
and inject the modifications into the original code, and then save it as a new file as the output.
This is to save the token usage. 


# Requirements:

The generated output file should satisfy the following requirements:

1. After completing the obfuscation for each stage, you must run:
  verus {output_file_name}.rs

and the output is considered success if you see "0 errors" in the "verification results" line,
otherwise it is considered failure.

2. Also, you must run:
  lynette additions {original_file_name}.rs {output_file_name}.rs

and the output is considered success is there is no output, otherwise it is considered failure.

3. Besides that, you should also check that the number of occurrences of 
"admit()"、"assume("、"#[verifier::external_body]"、"#[verifier::admit]"
in {original_file_name}.rs and {output_file_name}.rs
are the same, to ensure that no new admits or external bodies are introduced.

4. Create a change log at {case_dir}/change.txt summarizing what each stage
   changes. The file must list Stage 1..5 and briefly describe the technique
   added at each stage. Keep it as plain text (no code blocks).


You may attempt up to 5 times per stage. Do not proceed to the next
stage until both checks pass.

If verus has errors, try to fix the error with the feedback of the error messages and analyze the code.

If you cannot fix the issues on verus after 10 attempts on this stage, 
abort the obfuscation for this case, and write in the log on the verus error messages.

Naming convention:
  verified_stage1.rs ... verified_stage5.rs
  
You can ONLY exit after completing all 5 stages successfully, or you have used up all attempts for a stage.

If you see there are partial results in the directory, you must continue from the last incomplete stage.

Preserve runtime semantics and public signatures, and
prioritize spec/proof obfuscation over executable changes.

And again, do not change the semantics of the program, and make sure verus pass
after each stage of obfuscation to proceed to next stage.
"""


def find_copilot_bin(explicit_path: str | None) -> str:
    if explicit_path:
        return explicit_path
    resolved = os.environ.get("COPILOT_CMD") or shutil.which("copilot")
    if not resolved:
        raise FileNotFoundError(
            "copilot CLI not found. Set COPILOT_CMD or pass --copilot-bin."
        )
    return resolved


def load_token_from_config(config_path: Path) -> str | None:
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except Exception:
        return None
    tokens = data.get("copilot_tokens")
    if not isinstance(tokens, dict) or not tokens:
        return None
    token = None
    last_user = data.get("last_logged_in_user")
    if isinstance(last_user, dict):
        host = last_user.get("host")
        login = last_user.get("login")
        if isinstance(host, str) and isinstance(login, str):
            token = tokens.get(f"{host}:{login}")
    if not token and len(tokens) == 1:
        token = next(iter(tokens.values()))
    if isinstance(token, str):
        token = token.strip()
    return token if token else None


def build_env(args: argparse.Namespace) -> dict[str, str]:
    env = os.environ.copy()
    if args.xdg_config_home:
        config_home = Path(args.xdg_config_home).expanduser().resolve()
        config_home.mkdir(parents=True, exist_ok=True)
        env["XDG_CONFIG_HOME"] = str(config_home)
    if args.xdg_state_home:
        state_home = Path(args.xdg_state_home).expanduser().resolve()
        state_home.mkdir(parents=True, exist_ok=True)
        env["XDG_STATE_HOME"] = str(state_home)
    if args.github_token_env and args.github_token_file:
        raise ValueError("Use only one of --github-token-env or --github-token-file.")
    if args.github_token_env:
        token = env.get(args.github_token_env)
        if not token:
            raise ValueError(f"Env var {args.github_token_env} is not set.")
        env["COPILOT_GITHUB_TOKEN"] = token
    if args.github_token_file:
        token_path = Path(args.github_token_file).expanduser().resolve()
        token = token_path.read_text(encoding="utf-8").strip()
        if not token:
            raise ValueError(f"Token file {token_path} is empty.")
        env["COPILOT_GITHUB_TOKEN"] = token
    if not args.github_token_env and not args.github_token_file:
        if not (
            env.get("COPILOT_GITHUB_TOKEN")
            or env.get("GH_TOKEN")
            or env.get("GITHUB_TOKEN")
        ):
            token = load_token_from_config(DEFAULT_COPILOT_CONFIG)
            if token:
                env["COPILOT_GITHUB_TOKEN"] = token
    return env


def build_prompt(case_dir: Path, obfuscate_rules: str) -> str:
    base_instructions = BASE_INSTRUCTIONS.replace(
        "<prompt_file_contents>", obfuscate_rules.strip()
    )
    return (
        base_instructions
        + "\nCase directory:\n"
        + f"{case_dir}\n\n"
        + "You must read verified.rs from the case directory and write stage outputs\n"
        + "into the same directory.\n"
    )


def build_command(
    copilot_bin: str,
    prompt: str,
    model: str,
    allow_all_tools: bool,
    add_dirs: list[Path],
) -> list[str]:
    cmd = [copilot_bin, "--prompt", prompt, "--model", model, "--no-color"]
    if allow_all_tools:
        cmd.append("--allow-all-tools")
    for add_dir in add_dirs:
        cmd.extend(["--add-dir", str(add_dir)])
    return cmd


def _case_dirs_from_list(root: Path, list_path: Path) -> list[Path]:
    case_dirs: list[Path] = []
    for line in list_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        case_dirs.append(root / line)
    return case_dirs


def run_case(
    case_dir: Path,
    prompt_text: str,
    copilot_bin: str,
    model: str,
    allow_all_tools: bool,
    add_dirs: list[Path],
    timeout: int,
    env: dict[str, str],
) -> None:
    cmd = build_command(
        copilot_bin=copilot_bin,
        prompt=prompt_text,
        model=model,
        allow_all_tools=allow_all_tools,
        add_dirs=add_dirs,
    )
    start_time = time.time()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(case_dir),
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"copilot timed out after {timeout}s for {case_dir}.") from exc

    duration = time.time() - start_time
    log_path = case_dir / "obfuscation_copilot.log"
    with log_path.open("w", encoding="utf-8") as log_file:
        log_file.write(f"--- CMD: {' '.join(cmd)} ---\n")
        log_file.write(f"--- TIME: {duration:.2f}s ---\n")
        log_file.write("--- STDOUT ---\n")
        log_file.write(result.stdout)
        log_file.write("\n--- STDERR ---\n")
        log_file.write(result.stderr)

    if result.returncode != 0:
        raise RuntimeError(
            f"copilot failed ({result.returncode}) for {case_dir}. See {log_path}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run Copilot to obfuscate verified.rs using a multi-stage prompt."
    )
    parser.add_argument(
        "--case-dir",
        type=Path,
        help="Case directory containing verified.rs (e.g. VeruSAGE_sampled/<case_id>).",
    )
    parser.add_argument(
        "--case-list",
        type=Path,
        help="Path to sampled_task_ids.txt to process in order.",
    )
    parser.add_argument(
        "--case-root",
        type=Path,
        default=DEFAULT_CASE_ROOT,
        help="Root directory for case IDs listed in --case-list.",
    )
    parser.add_argument(
        "--prompt-file",
        type=Path,
        default=DEFAULT_PROMPT_FILE,
        help="Path to obfuscation prompt template (obfuscate_pro.txt).",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="Copilot model name to use.",
    )
    parser.add_argument(
        "--copilot-bin",
        default=None,
        help="Path to the copilot CLI binary (default: resolve from PATH).",
    )
    parser.add_argument(
        "--allow-all-tools",
        action="store_true",
        help="Pass --allow-all-tools to copilot (non-interactive runs).",
    )
    parser.add_argument(
        "--add-dir",
        action="append",
        default=[],
        help="Extra directory to allow copilot access to (can be repeated).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help="Timeout in seconds for the copilot process (default: 3600).",
    )
    parser.add_argument(
        "--xdg-config-home",
        default=None,
        help="Set XDG_CONFIG_HOME for copilot (must be writable).",
    )
    parser.add_argument(
        "--xdg-state-home",
        default=None,
        help="Set XDG_STATE_HOME for copilot (must be writable).",
    )
    parser.add_argument(
        "--github-token-env",
        default=None,
        help="Name of an env var holding a Copilot token (sets COPILOT_GITHUB_TOKEN).",
    )
    parser.add_argument(
        "--github-token-file",
        default=None,
        help="Path to a file containing a Copilot token (sets COPILOT_GITHUB_TOKEN).",
    )

    args = parser.parse_args()

    if not args.case_dir and not args.case_list:
        parser.error("Provide --case-dir or --case-list.")

    repo_root = Path(__file__).resolve().parents[4]
    prompt_path = (repo_root / args.prompt_file).resolve()
    obfuscate_rules = prompt_path.read_text(encoding="utf-8")

    if args.case_dir:
        case_dirs = [args.case_dir]
    else:
        case_dirs = _case_dirs_from_list(args.case_root, args.case_list)

    copilot_bin = find_copilot_bin(args.copilot_bin)
    env = build_env(args)

    for case_dir in case_dirs:
        case_dir = case_dir.resolve()
        prompt_text = build_prompt(case_dir, obfuscate_rules)
        add_dirs = [case_dir]
        for extra in args.add_dir:
            add_dirs.append(Path(extra).resolve())
        run_case(
            case_dir=case_dir,
            prompt_text=prompt_text,
            copilot_bin=copilot_bin,
            model=args.model,
            allow_all_tools=args.allow_all_tools,
            add_dirs=add_dirs,
            timeout=args.timeout,
            env=env,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
