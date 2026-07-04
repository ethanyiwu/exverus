#!/usr/bin/env python3
"""
Script to automatically call convert_assume.py
Creates an 'assume' folder in the same directory as the input file for output
"""

import subprocess
import sys
from pathlib import Path


def create_assume_folder(input_path: Path) -> Path:
    """Create an 'assume' folder in the same directory as the input file"""
    assume_dir = input_path.parent / "assume"
    assume_dir.mkdir(exist_ok=True)
    print(f"Output folder: {assume_dir}")
    return assume_dir


def run_convert_assume(input_path: Path, output_dir: Path, use_assert: bool = False):
    """Run the convert_assume.py script"""
    script_path = Path(__file__).parent / "convert_assume.py"

    if not script_path.exists():
        raise FileNotFoundError(f"convert_assume.py script not found: {script_path}")

    cmd = [sys.executable, str(script_path), str(input_path), str(output_dir)]
    if use_assert:
        cmd.append("--use-assert")
    print(f"Executing command: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("Conversion successful!")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Conversion failed (exit code: {e.returncode}):")
        print(f"Error output: {e.stderr}")
        return False


def convert_rust_file_to_string(input_path: str, use_assert: bool = False) -> str:
    """
    Convert Rust file and return the converted code string

    Args:
        input_path: Path to the input Rust file
        use_assert: If True, use 'assert' instead of 'assume' for loop conditions and invariants

    Returns:
        Converted Rust code string

    Raises:
        FileNotFoundError: If input file doesn't exist
        RuntimeError: If conversion process fails
    """
    input_file = Path(input_path).resolve()

    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if not input_file.is_file():
        raise RuntimeError(f"Input path is not a file: {input_path}")

    # Create output folder
    output_dir = create_assume_folder(input_file)

    # Run conversion script
    success = run_convert_assume(input_file, output_dir, use_assert)

    if not success:
        raise RuntimeError(f"Conversion failed: {output_dir}")

    # Read the converted file content
    output_file = output_dir / input_file.name
    if not output_file.exists():
        raise RuntimeError(f"Output file not generated: {output_file}")

    # Return the converted code string
    return output_file.read_text(encoding="utf-8")


def convert_rust_file_to_file(
    input_path: str, output_dir: str = None, use_assert: bool = False
) -> str:
    """
    Convert Rust file and save to specified directory, return output file path

    Args:
        input_path: Path to the input Rust file
        output_dir: Output directory path, if None creates 'assume' folder in input file's directory
        use_assert: If True, use 'assert' instead of 'assume' for loop conditions and invariants

    Returns:
        Path to the output file

    Raises:
        FileNotFoundError: If input file doesn't exist
        RuntimeError: If conversion process fails
    """
    input_file = Path(input_path).resolve()

    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if not input_file.is_file():
        raise RuntimeError(f"Input path is not a file: {input_path}")

    # Determine output directory
    if output_dir is None:
        output_dir = create_assume_folder(input_file)
    else:
        output_dir = Path(output_dir).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

    # Run conversion script
    success = run_convert_assume(input_file, output_dir, use_assert)

    if not success:
        raise RuntimeError("Conversion failed")

    # Return output file path
    output_file = output_dir / input_file.name
    if not output_file.exists():
        raise RuntimeError(f"Output file not generated: {output_file}")

    return str(output_file)


def main():
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python run_convert_assume.py <input_file_path> [--use-assert]")
        print("Example: python run_convert_assume.py /path/to/input.rs")
        print("Example: python run_convert_assume.py /path/to/input.rs --use-assert")
        print(
            "  --use-assert: Use 'assert' instead of 'assume' for loop conditions and invariants"
        )
        sys.exit(1)

    input_file = sys.argv[1]
    use_assert = len(sys.argv) == 3 and sys.argv[2] == "--use-assert"

    try:
        # Convert code and get string
        converted_code = convert_rust_file_to_string(input_file, use_assert)

        # Output to stdout
        print("\n" + "=" * 50)
        print("Converted code:")
        print("=" * 50)
        print(converted_code)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
