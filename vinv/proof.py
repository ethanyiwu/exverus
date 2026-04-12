import tempfile
from enum import Enum
from pathlib import Path
from typing import Dict, List, Literal, Tuple

from vinv.config import (
    ADDITIONAL_BENCHMARK_ROOT_DIR,
    ADDITIONAL_BENCHMARK_UNVERIFIED_ENTRY_POINTS,
    ADDITIONAL_BENCHMARK_VERIFIED_ENTRY_POINTS,
    CLEANED_BENCHMARK_ROOT_DIR,
    CLEANED_VB_BENCHMARK_UNVERIFIED_ENTRY_POINTS,
    CLEANED_VB_BENCHMARK_VERIFIED_ENTRY_POINTS,
    VB_BENCHMARK_UNVERIFIED_ENTRY_POINTS,
    VB_BENCHMARK_VERIFIED_ENTRY_POINTS,
    VSBHERB_BENCHMARK_UNVERIFIED_ENTRY_POINTS,
    VSBHERB_BENCHMARK_VERIFIED_ENTRY_POINTS,
)
from vinv.invariant import InvariantEntry
from vinv.specification import SpecificationEntry
from vinv.utils import check_status


def _split_code_by_func(code: str) -> tuple[list[int], list[int], list[str]]:
    interval_start: list[int] = []
    interval_end: list[int] = []
    lines = code.split("\n")
    total_line = len(lines)
    prefixes = (
        "fn ",
        "pub fn ",
        "proof fn ",
        "pub proof fn ",
        "spec fn ",
        "pub spec fn ",
    )
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith(prefixes):
            continue
        interval_start.append(i)
        if stripped.endswith("{}"):
            interval_end.append(i)
            continue

        indent = len(line) - len(line.lstrip())
        for j in range(i + 1, total_line):
            next_line = lines[j]
            next_indent = len(next_line) - len(next_line.lstrip())
            if next_indent == indent and next_line.strip().startswith("}"):
                interval_end.append(j)
                break
        else:
            interval_end.append(total_line)
    return interval_start, interval_end, []


class FuncType(Enum):
    NORMAL = "normal"
    MAIN = "main"
    SPEC = "spec"
    PROOF = "proof"


class ProofFile:
    def __init__(self, path: Path):
        self.path = path
        self.code = path.read_text()
        self.code_lines = self.code.splitlines()
        self.name = path.stem
        self.verified = self._is_verified()
        self.benchmark = self.get_benchmark()
        self.task_id = f"{self.benchmark}_{self.name}"
        # Determine dataset prefix based on file location
        p = self.path.resolve()
        try:
            p_str = p.as_posix()
        except Exception:
            p_str = str(p)
        if p_str.startswith(CLEANED_BENCHMARK_ROOT_DIR.as_posix()):
            dataset_prefix = "verusbench"
            self.source = "CLEANED_VB"
        elif self.benchmark in (
            VSBHERB_BENCHMARK_VERIFIED_ENTRY_POINTS
            | VSBHERB_BENCHMARK_UNVERIFIED_ENTRY_POINTS
        ):
            dataset_prefix = "additional"
            self.source = "VSBHERB"
        elif p_str.startswith(ADDITIONAL_BENCHMARK_ROOT_DIR.as_posix()):
            dataset_prefix = "additional"
            self.source = "ADDITIONAL"
        else:
            dataset_prefix = "unknown"
            self.source = "UNKNOWN"
        self.full_id = f"{dataset_prefix}_{self.task_id}"
        self.entry_point = self.get_entry_point()
        self.func_type_dict = self._record_func_types()  # {func_id: FuncType}
        self.func_ids = list(self.func_type_dict.keys())

    def _is_verified(self) -> bool:
        if self.path.parent.name == "verified":
            return True
        if self.path.parent.name == "unverified":
            return False
        raise ValueError(
            f"Cannot determine if {self.path} is verified or not. Please check the parent directory name."
        )

    def get_benchmark(self) -> str:
        return self.path.parent.parent.name.lower()

    def get_entry_point(self) -> Path:
        # Support CLEANED_VB, ADDITIONAL, and original VB entry points.
        if self.verified:
            candidates = [
                CLEANED_VB_BENCHMARK_VERIFIED_ENTRY_POINTS,
                VSBHERB_BENCHMARK_VERIFIED_ENTRY_POINTS,
                ADDITIONAL_BENCHMARK_VERIFIED_ENTRY_POINTS,
                VB_BENCHMARK_VERIFIED_ENTRY_POINTS,
            ]
        else:
            candidates = [
                CLEANED_VB_BENCHMARK_UNVERIFIED_ENTRY_POINTS,
                VSBHERB_BENCHMARK_UNVERIFIED_ENTRY_POINTS,
                ADDITIONAL_BENCHMARK_UNVERIFIED_ENTRY_POINTS,
                VB_BENCHMARK_UNVERIFIED_ENTRY_POINTS,
            ]
        for mapping in candidates:
            ep = mapping.get(self.benchmark)
            if ep is not None:
                return ep
        raise ValueError(
            f"Entry point not found for benchmark '{self.benchmark}' (verified={self.verified})"
        )

    def contains_invariant(self) -> bool:
        if "invariant" in self.code:
            assert (
                "while" in self.code or "for" in self.code or "loop" in self.code
            ), f"loop not found in {self.path}"
        return "invariant" in self.code

    def _split_code_by_func(self):
        return _split_code_by_func(self.code)

    def _get_func_code(self, func_start: int, func_end: int) -> str:
        func_lines = self.code_lines[func_start - 1 : func_end]
        return "".join(func_lines)

    def _record_func_types(self) -> Dict[str, FuncType]:
        """
        Record the types of functions in the proof file.
        Returns:
            A dictionary mapping function IDs to their types.
        """
        func_types = {}
        func_blocks = self._split_code_by_func()
        for i in range(len(func_blocks[0])):
            func_start = func_blocks[0][i] + 1
            func_end = func_blocks[1][i] + 1
            func_id = f"{self.name}_{func_start}_{func_end}"
            func_sig_line = self.code_lines[func_start - 1].strip()
            if "proof fn" in func_sig_line:
                func_types[func_id] = FuncType.PROOF
            elif "spec fn" in func_sig_line:
                func_types[func_id] = FuncType.SPEC
            elif "fn main" in func_sig_line:
                func_types[func_id] = FuncType.MAIN
            else:
                func_types[func_id] = FuncType.NORMAL

        return func_types

    def parse_invariants(self) -> Dict[str, List[InvariantEntry]]:
        invariant_entry_map = {}
        func_blocks = self._split_code_by_func()
        for i in range(len(func_blocks[0])):
            func_start = func_blocks[0][i] + 1  # one-based index, inclusive
            func_end = func_blocks[1][i] + 1  # one-based index, inclusive
            func_id = f"{self.name}_{func_start}_{func_end}"
            if self.func_type_dict.get(func_id) != FuncType.NORMAL:
                # only process normal functions
                continue
            invariant_entry_list = self.parse_invariants_for_func(func_start, func_end)
            if invariant_entry_list:
                invariant_entry_map[func_id] = invariant_entry_list

        return invariant_entry_map

    def parse_invariants_for_func(
        self, func_start: int, func_end: int
    ) -> List[InvariantEntry]:
        """
        Parse the invariants for a function.
        Args:
            func_start: The start line of the function (one-based index).
            func_end: The end line of the function (one-based index).
        Returns:
            A list of InvariantEntry objects containing the invariants.
        """
        invariant_entry_list = []
        loop_start = -1
        func_name = self.code_lines[func_start - 1].strip().split("(")[0].split(" ")[-1]
        for i in range(func_start, func_end + 1):
            line = self.code_lines[i - 1].strip()
            if (
                line.startswith("while")
                or line.startswith("for")
                or line.startswith("loop")
            ):
                loop_start = i  # one-based index, inclusive
            if line.strip() == "invariant":
                assert (
                    loop_start != -1
                ), f"loop not found before invariant at line {i} in {self.path}"
                # find the end of the invariants "{"
                invariants_start = i
                for j in range(i, func_end + 1):
                    if self.code_lines[j - 1].strip() in ["{"]:
                        # note that `ensures` could exist inside invariants
                        invariants_end = j - 1
                        break
                    if j == func_end:
                        raise ValueError(
                            f"End of invariant not found in {self.path} at line {i}"
                        )
                invariants_code = "\n".join(
                    self.code_lines[invariants_start - 1 : invariants_end]
                )
                invariant_entry_list.append(
                    InvariantEntry(
                        self.code_lines,
                        func_name,
                        func_start,
                        loop_start,
                        invariants_start + 1,  # from the line after "invariant"
                        invariants_end,
                        invariants_code,
                    )
                )

        return invariant_entry_list

    def parse_invariants_for_func_id(self, func_id: str) -> List[InvariantEntry]:
        """
        Parse the invariants for a function given its ID.
        Args:
            func_id: The ID of the function in the format "name_start_end".
        Returns:
            A list of InvariantEntry objects containing the invariants.
        """
        func_start, func_end = map(int, func_id.split("_")[-2:])

        return self.parse_invariants_for_func(func_start, func_end)

    def parse_specifications(self) -> Dict[str, SpecificationEntry]:
        """
        Parse the specifications (requires and ensures) in the proof file.
        Returns:
            A dictionary mapping function IDs to SpecificationEntry objects.
        """
        spec_entry_map = {}
        func_blocks = self._split_code_by_func()
        for i in range(len(func_blocks[0])):
            func_start = func_blocks[0][i] + 1  # one-based index, inclusive
            func_end = func_blocks[1][i] + 1  # one-based index, inclusive
            func_id = f"{self.name}_{func_start}_{func_end}"
            if self.func_type_dict.get(func_id) == FuncType.MAIN:
                # skip main function
                continue
            spec_entry = self.parse_spec_entry_for_func(func_start, func_end)
            if spec_entry:
                spec_entry_map[func_id] = spec_entry

        return spec_entry_map

    def parse_spec_entry_for_func(
        self, func_start: int, func_end: int
    ) -> SpecificationEntry:
        """
        Parse the specifications (requires and ensures) for a function.
        Args:
            func_start: The start line of the function (one-based index).
            func_end: The end line of the function (one-based index).
        Returns:
            A SpecificationEntry object containing the specifications.
        """
        func_name = self.code_lines[func_start - 1].strip().split("(")[0].split(" ")[-1]
        spec_entry_start = (
            func_start + 1
        )  # assuming the first line after the function definition is the start of specifications
        spec_entry_end = func_end
        for i in range(spec_entry_start, func_end + 1):
            line = self.code_lines[i - 1].strip()
            if line == "{":
                spec_entry_end = i - 1
                break

        assert (
            spec_entry_end != func_end
        ), f"End of specification not found in {self.path} for function {func_name} at line {func_start}"
        spec_code = "\n".join(self.code_lines[spec_entry_start - 1 : spec_entry_end])

        return SpecificationEntry(
            self.code_lines,
            func_name,
            func_start,
            spec_entry_start + 1,  # one-based index, inclusive
            spec_entry_end,  # one-based index, inclusive
            spec_code,
        )

    def parse_spec_entry_for_func_id(self, func_id: str) -> SpecificationEntry:
        """
        Parse the specifications for a function given its ID.
        Args:
            func_id: The ID of the function in the format "name_start_end".
        Returns:
            A SpecificationEntry object containing the specifications.
        """
        func_start, func_end = map(int, func_id.split("_")[-2:])

        return self.parse_spec_entry_for_func(func_start, func_end)

    def run_verus(self, use_old_verus: bool = False) -> Tuple[bool, str, str]:
        """
        Run Verus on the file.
        Returns a tuple of (success, stdout, stderr).
        """
        if not self.verified:
            raise ValueError(f"Cannot run Verus on unverified file {self.path}")

        from vinv.verus_utils import get_verus_result

        return get_verus_result(self.path, use_old_verus=use_old_verus)

    def deghostify(
        self, deghost_mode: Literal["raw", "unverified"] = "raw", run_fmt: bool = True
    ) -> str:
        """
        Deghostify the proof file.
        Args:
            deghost_mode: "raw" or "unverified". If "raw", the file will be
            deghostified to a raw format that can be directly compiled with
            rustc. If "unverified", the file will be deghostified to an
            unverified format.
            run_fmt: Whether to run `verusfmt` on the deghostified file.
        Returns:
            The deghostified code as a string.
        """
        if not self.verified:
            raise ValueError(f"Cannot deghostify unverified file {self.path}")

        from lynette import lynette

        with tempfile.TemporaryDirectory() as temp_dir:
            Path(temp_dir).mkdir(parents=True, exist_ok=True)
            temp_file = Path(temp_dir) / f"{self.name}_deghosted.rs"
            temp_file.touch()
            print(f"Deghostifying {self.path} to {temp_file}")
            lynette.code_deghost(
                self.path.as_posix(),
                Path(temp_file).as_posix(),
                deghost_mode=deghost_mode,
                run_fmt=run_fmt,
            )
            deghosted_code = temp_file.read_text()

        return deghosted_code

    def __repr__(self):
        return f"ProofFile(name={self.name}, benchmark={self.benchmark}, entry_point={self.entry_point}, path={self.path})"


class IntermediateProofFile(ProofFile):
    def __init__(self, path: Path, parent_proof_file: ProofFile):
        assert (
            parent_proof_file.verified
        ), f"Parent proof file {parent_proof_file.path} must be verified."
        # also assume the file is already formatted
        self.path = path
        self.code = path.read_text()
        self.code_lines = self.code.splitlines()
        self.name = parent_proof_file.name  # use the same of the parent proof file
        self.verified = False  # TODO: it is likely not verified but not guaranteed
        self.benchmark = parent_proof_file.benchmark
        self.task_id = f"{self.benchmark}_{self.name}"

        # added attributes
        # self.obfs_id = path.parent.name  # response_{i}

        self.full_id = f"{self.task_id}_intermediate"
        self.entry_point = parent_proof_file.entry_point

        self.func_type_dict = self._record_func_types()  # {func_id: FuncType}
        self.func_ids = list(self.func_type_dict.keys())


class ObfsProofFile(ProofFile):
    def __init__(self, path: Path, parent_proof_file: ProofFile):
        assert (
            parent_proof_file.verified
        ), f"Parent proof file {parent_proof_file.path} must be verified."
        # also assume the file is already formatted
        self.path = path
        self.code = path.read_text()
        self.code_lines = self.code.splitlines()
        self.name = parent_proof_file.name  # use the same of the parent proof file
        self.verified = True
        self.benchmark = parent_proof_file.benchmark
        self.task_id = f"{self.benchmark}_{self.name}"

        # added attributes
        self.obfs_id = path.parent.name  # response_{i}

        self.full_id = f"{self.task_id}_obfs_{self.obfs_id}"
        self.entry_point = parent_proof_file.entry_point

        self.func_type_dict = self._record_func_types()  # {func_id: FuncType}
        self.func_ids = list(self.func_type_dict.keys())


class InjectedProofFile(ProofFile):
    def __init__(self, path: Path):
        self.path = path
        self.code = path.read_text()
        self.code_lines = self.code.splitlines()
        self.name = path.parent.parent.name
        self.verified = False
        self.benchmark = "inv_inject"
        self.inject_type = path.parent.name
        self.task_id = f"{self.benchmark}_{self.name}"
        self.full_id = f"{self.task_id}_{self.inject_type}"
        self.entry_point = path.parent.parent.parent
        self.func_type_dict = self._record_func_types()  # {func_id: FuncType}
        self.func_ids = list(self.func_type_dict.keys())


class AutoverusProofFile(ProofFile):
    # note that this file is not necessarily formatted
    def __init__(self, path: Path):
        self.path = path
        self.code = path.read_text()
        self.code_lines = self.code.splitlines()
        self.name = path.parent.name  # use the parent directory name
        self.verified = check_status(
            path.parent / "verify_status.txt", "verification_pass"
        )
        self.benchmark = (
            path.parent.parent.name.lower()
        )  # parent directory of the proof file
        self.task_id = f"{self.benchmark}_{self.name}"
        self.full_id = f"autoverus_{self.task_id}"
        self.entry_point = path.parent.parent.parent
        self.func_type_dict = self._record_func_types()  # {func_id: FuncType}
        self.func_ids = list(self.func_type_dict.keys())


class OneStepProofFile(ProofFile):
    def __init__(self, path: Path):
        self.path = path
        self.code = path.read_text()
        self.code_lines = self.code.splitlines()
        self.name = path.stem
        self.verified = False
        self.benchmark = "one-step"
        self.task_id = f"{self.benchmark}_{self.name}"
        self.full_id = f"{self.task_id}"
        self.entry_point = path.parent.parent.parent
        self.func_type_dict = self._record_func_types()  # {func_id: FuncType}
        self.func_ids = list(self.func_type_dict.keys())
