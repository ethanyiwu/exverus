#!/usr/bin/env python3

import sys

from vinv.pipeline.assume.run_convert_assume_syn import convert_rust_file_to_file


def convert_file(input_path: str, output_dir: str, use_assert: bool = False) -> str:
    return convert_rust_file_to_file(input_path, output_dir, use_assert)


def main() -> None:
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        raise SystemExit(
            "Usage: python convert_assume.py path/to/input.rs path/to/save/folder [--use-assert]"
        )
    out_path = convert_file(
        sys.argv[1],
        sys.argv[2],
        len(sys.argv) == 4 and sys.argv[3] == "--use-assert",
    )
    print(f"Converted written to: {out_path}")


if __name__ == "__main__":
    main()
