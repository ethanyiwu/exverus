#!/usr/bin/env python3
"""
Wrapper to run the Rust-based convert_assume_syn tool (verus_syn parser).
Creates an 'assume' folder next to the input file by default.

CLI:
  uv run python run_convert_assume_syn.py /path/to/input.rs [--use-assert] [--out /path/to/dir]

Programmatic API:
  - convert_rust_file_to_string(input_path, use_assert=False)
  - convert_rust_file_to_file(input_path, output_dir=None, use_assert=False)
"""

import argparse
import subprocess
import sys
from pathlib import Path

from vinv.pipeline.parser_utils import find_or_build_rs_convert_bin


def _find_or_build_convert_bin() -> Path:
    return find_or_build_rs_convert_bin("convert_assume_syn")


def create_assume_folder(input_path: Path) -> Path:
    assume_dir = input_path.parent / "assume"
    assume_dir.mkdir(exist_ok=True)
    print(f"Output folder: {assume_dir}")
    return assume_dir


def run_convert_assume_syn(
    input_path: Path, output_dir: Path, use_assert: bool = False
) -> bool:
    bin_path = _find_or_build_convert_bin()
    cmd = [str(bin_path), str(input_path), str(output_dir)]
    if use_assert:
        cmd.append("--use-assert")
    print(f"Executing command: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("Conversion successful!")
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            # verusfmt or warnings may print to stderr; show but don't fail
            print(result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Conversion failed (exit code: {e.returncode}):")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        return False


def convert_rust_file_to_string(input_path: str, use_assert: bool = False) -> str:
    input_file = Path(input_path).resolve()
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    if not input_file.is_file():
        raise RuntimeError(f"Input path is not a file: {input_path}")

    output_dir = create_assume_folder(input_file)
    success = run_convert_assume_syn(input_file, output_dir, use_assert)
    if not success:
        raise RuntimeError(f"Conversion failed: {output_dir}")

    output_file = output_dir / input_file.name
    if not output_file.exists():
        raise RuntimeError(f"Output file not generated: {output_file}")
    return output_file.read_text(encoding="utf-8")


def convert_rust_file_to_file(
    input_path: str, output_dir: str = None, use_assert: bool = False
) -> str:
    input_file = Path(input_path).resolve()
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    if not input_file.is_file():
        raise RuntimeError(f"Input path is not a file: {input_path}")

    if output_dir is None:
        output_path = create_assume_folder(input_file)
    else:
        output_path = Path(output_dir).resolve()
        output_path.mkdir(parents=True, exist_ok=True)

    success = run_convert_assume_syn(input_file, output_path, use_assert)
    if not success:
        raise RuntimeError("Conversion failed")

    output_file = output_path / input_file.name
    if not output_file.exists():
        raise RuntimeError(f"Output file not generated: {output_file}")
    return str(output_file)


def main():
    parser = argparse.ArgumentParser(
        prog="run_convert_assume_syn",
        description="Run the Rust-based convert_assume_syn (verus_syn parser) on a Verus Rust file.",
    )
    parser.add_argument("input", help="Path to the input .rs file")
    parser.add_argument(
        "--use-assert",
        action="store_true",
        help="Use assert for loop-head facts instead of assume",
    )
    parser.add_argument(
        "--out",
        metavar="DIR",
        help="Output directory (default: create 'assume' next to input and print converted code)",
    )
    parser.add_argument(
        "--no-print",
        action="store_true",
        help="Do not print converted code when --out is omitted",
    )

    args = parser.parse_args()

    try:
        if args.out:
            out_path = convert_rust_file_to_file(args.input, args.out, args.use_assert)
            print(f"Converted written to: {out_path}")
        else:
            converted = convert_rust_file_to_string(args.input, args.use_assert)
            if not args.no_print:
                print(converted)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
