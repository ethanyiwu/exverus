#!/usr/bin/env python3

import sys
from pathlib import Path

from vinv.pipeline.assume.run_convert_assume_syn import (
    convert_rust_file_to_file,
    convert_rust_file_to_string,
    create_assume_folder,
    run_convert_assume_syn,
)


def run_convert_assume(input_path: Path, output_dir: Path, use_assert: bool = False) -> bool:
    return run_convert_assume_syn(input_path, output_dir, use_assert)


def main() -> None:
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        raise SystemExit(
            "Usage: python run_convert_assume.py <input_file_path> [--use-assert]"
        )
    print(convert_rust_file_to_string(sys.argv[1], len(sys.argv) == 3))


if __name__ == "__main__":
    main()
