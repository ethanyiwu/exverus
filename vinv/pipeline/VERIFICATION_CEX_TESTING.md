## Verification CEX Testing Guide

This guide explains how to run the verification-oriented counterexample (CEX) generation strategy on single files and in batch over the dataset in `vinv/pipeline/assume/example_input/`.

### 1) Environment setup

- Export API keys as needed (DeepSeek and/or OpenAI):

```bash
export DEEPSEEK_API_KEY=sk-...            # if using deepseek-* models
export OPENAI_API_KEY=sk-proj-...         # if using gpt-* models
```

- Sync the project and ensure Python can import the project modules and Vercode tools:

```bash
uv sync
export PYTHONPATH=verus-proof-synthesis/code:$(pwd)
```

- Optional (if your local setup needs them):

```bash
export LYNETTE_PATH=$(pwd)/verus-proof-synthesis/utils/lynette/source/target/debug/lynette
# export OLD_VERUS_PATH=...  # only if your local Verus setup expects it
```

### 1.5) Common helper CLI

Use the unified CLI for the common assume/assert utilities:

```bash
uv run vinv assume convert vinv/pipeline/assume/example_input/example-2.rs --output-dir /tmp/assume_out
uv run vinv assume validate-cex /tmp/assume_out/example-2.rs --assign i=0 --assign j=1
```

### 2) What the verification strategy does

Given an input Rust/Verus file, the strategy:

- Converts `while` loops into `assume`/`assert` form via `convert_assume.py` (string-only transform).
- Builds a prompt (including converted code and optional Verus analysis text) to ask an LLM to produce a Python Z3 script.
- Runs the Z3 script with a timeout. The script must set:
  - `__z3_cex_status__` in {"sat","unsat","unknown"}
  - `__z3_cex_result__` as a JSON-serializable dict of variable assignments (original Rust names)
- Injects the resulting `let (mut ... ) = (...)` line into the converted program at the marker `// place to add variables assignment. [1]`.
- Optionally verifies the injected program with Verus (best effort).

Artifacts per attempt are written under a per-file `try_1/` directory (see section 5).

### 3) Single-file run (deepseek-chat example)

The following runs verification CEX on `example-2.rs` using `deepseek-chat` and writes artifacts under `results/pipeline/verification_ds_focus/example-2_deepseekchat/try_1/`.

```bash
DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY} OPENAI_API_KEY=${OPENAI_API_KEY} uv run python - <<'PY'
import json, os, sys, shutil
from pathlib import Path

repo_root = Path('/Users/sun/Desktop/code/GithubLink/verusinv_backup/verusinv')
sys.path.insert(0, str(repo_root / 'verus-proof-synthesis' / 'code'))
sys.path.insert(0, str(repo_root))

from vinv.pipeline.verification_cex import verification_cex_generation

path = repo_root / 'vinv' / 'pipeline' / 'assume' / 'example_input' / 'example-2.rs'
work_dir = repo_root / 'results' / 'pipeline' / 'verification_ds_focus' / 'example-2_deepseekchat'
try_dir = work_dir / 'try_1'
shutil.rmtree(try_dir, ignore_errors=True)
try_dir.mkdir(parents=True, exist_ok=True)

class _DummyErr:
    class _ET: name = 'AssertFail'
    error = _ET()
    def get_text(self):
        return 'Dummy error for verification CEX'
    spans = []
verus_error = _DummyErr()

cex = verification_cex_generation(
    failing_proof_file=path,
    verus_error=verus_error,  # type: ignore[arg-type]
    try_dir=try_dir,
    console_error_msg='',
    model='deepseek-chat',
    z3_exec_timeout_seconds=25,
)

out = {
  'input': str(path),
  'work_dir': str(work_dir),
  'prompt': str(try_dir / 'verification_z3_prompt.txt'),
  'responses': sorted([str(p) for p in try_dir.glob('verification_z3_response_attempt_*.txt')]),
  'scripts': sorted([str(p) for p in try_dir.glob('verification_z3_script_attempt_*.py')]),
  'status': sorted([str(p) for p in try_dir.glob('verification_z3_status_attempt_*.txt')]),
  'result_json': sorted([str(p) for p in try_dir.glob('verification_z3_result_attempt_*.json')]),
  'let_line': str(try_dir / 'verification_let_line.txt'),
  'injected': str(try_dir / 'verification_injected.rs'),
  'counter_example': (cex.to_dict() if cex else None),
}
print(json.dumps(out, indent=2))
PY
```

Notes:
- Supported models include: `deepseek-chat`, `deepseek-reasoner`, `gpt-4o`, `gpt-5`.
- If you see authentication errors, verify your API key exports.

### 4) Batch run over the dataset

This runs the verification CEX on all `.rs` files in `vinv/pipeline/assume/example_input/` with `deepseek-chat`, writing per-file artifacts and a summary JSON.

```bash
DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY} OPENAI_API_KEY=${OPENAI_API_KEY} uv run python - <<'PY'
import os, sys, json, time
from pathlib import Path
import shutil

repo_root = Path('/Users/sun/Desktop/code/GithubLink/verusinv_backup/verusinv')
sys.path.insert(0, str(repo_root / 'verus-proof-synthesis' / 'code'))
sys.path.insert(0, str(repo_root))

from vinv.pipeline.verification_cex import verification_cex_generation

in_dir = repo_root / 'vinv' / 'pipeline' / 'assume' / 'example_input'
out_root = repo_root / 'results' / 'pipeline' / 'verification_ds_batch_deepseekchat'

files = sorted([p for p in in_dir.glob('*.rs')])
summary = {}
for path in files:
    tag = path.stem
    work_dir = out_root / tag
    try_dir = work_dir / 'try_1'
    shutil.rmtree(try_dir, ignore_errors=True)
    try_dir.mkdir(parents=True, exist_ok=True)

    class _DummyErr:
        class _ET: name = 'AssertFail'
        error = _ET()
        def get_text(self):
            return 'Dummy error for verification CEX'
        spans = []
    verus_error = _DummyErr()

    t0 = time.time()
    ce = None
    err = None
    try:
        ce = verification_cex_generation(
            failing_proof_file=path,
            verus_error=verus_error,  # type: ignore[arg-type]
            try_dir=try_dir,
            console_error_msg='',
            model='deepseek-chat',
            z3_exec_timeout_seconds=25,
        )
    except Exception as e:
        err = str(e)
    dt = time.time() - t0

    item = {
        'file': str(path),
        'work_dir': str(work_dir),
        'prompt': str(try_dir / 'verification_z3_prompt.txt'),
        'responses': sorted([str(p) for p in try_dir.glob('verification_z3_response_attempt_*.txt')]),
        'scripts': sorted([str(p) for p in try_dir.glob('verification_z3_script_attempt_*.py')]),
        'status': sorted([str(p) for p in try_dir.glob('verification_z3_status_attempt_*.txt')]),
        'result_json': sorted([str(p) for p in try_dir.glob('verification_z3_result_attempt_*.json')]),
        'let_line': str(try_dir / 'verification_let_line.txt'),
        'injected': str(try_dir / 'verification_injected.rs'),
        'counter_example': (ce.to_dict() if ce else None),
        'exception': err,
        'elapsed_sec': round(dt, 2),
    }
    summary[tag] = item

out_root.mkdir(parents=True, exist_ok=True)
(out_root / 'summary.json').write_text(json.dumps(summary, indent=2))
print('Summary written to', out_root / 'summary.json')
PY
```

- The summary is written to: `results/pipeline/verification_ds_batch_deepseekchat/summary.json`.
- Each file has its own `try_1/` artifacts directory under that root.

### 5) Artifacts produced per run (per-file `try_1/`)

- `converted_assume.rs`: assume/assert-converted source code
- `converted_analysis.txt`: optional Verus analysis text
- `verification_z3_prompt.txt`: the full prompt given to the LLM
- `verification_z3_response_attempt_*.txt`: raw LLM responses
- `verification_z3_script_attempt_*.py`: the extracted Python Z3 script(s)
- `verification_z3_status_attempt_*.txt`: reported status (sat/unsat/unknown)
- `verification_z3_result_attempt_*.json`: JSON of variable assignments
- `verification_let_line.txt`: the constructed Rust `let` tuple assignment
- `verification_injected.rs`: converted program with the `let` assignment injected

### 6) Tips and troubleshooting

- If you see `Authentication Fails (governor)` or 401, re-check your `DEEPSEEK_API_KEY` or `OPENAI_API_KEY`.
- If you see `Symbolic expressions cannot be cast to concrete Boolean values.`, make sure you are using the updated prompt (we enforce Z3 BoolRef usage via z3.And/Or/Not/Implies and s.add(...) only).
- Models: if a model is consistently returning UNSAT or malformed scripts, try switching between `deepseek-chat`, `deepseek-reasoner`, or `gpt-4o`/`gpt-5` and compare.
