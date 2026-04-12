from enum import Enum
from typing import List


class SpecificationType(Enum):
    """
    Enum representing the type of specification.
    """

    REQUIRES = "requires"
    ENSURES = "ensures"


class SpecificationEntry:
    """
    Represents a specification entry in a function, containing multiple
    specification entries (requires and ensures).
    """

    def __init__(
        self,
        file_code_lines: List[str],
        func_name: str,
        func_start: int,
        spec_entry_start: int,
        spec_entry_end: int,
        spec_code: str,
    ):
        self.file_code_lines = file_code_lines
        self.func_name = func_name
        self.func_start = func_start
        self.spec_entry_start = spec_entry_start  # one-based index, inclusive
        self.spec_entry_end = spec_entry_end  # one-based index, inclusive
        self.spec_code = spec_code.strip()  # requires ... ensures ...


class SpecificationItem:
    """
    Represents a single specification item (requires or ensures) in a specification entry.
    """

    def __init__(
        self,
        spec_entry: SpecificationEntry,
        spec_item_start: int,
        spec_item_end: int,
        spec_item_type_str: str,
    ):
        self.spec_entry = spec_entry
        self.spec_item_start = spec_item_start  # one-based index, inclusive
        self.spec_item_end = spec_item_end  # one-based index, inclusive
        self.spec_item_file_code_lines = spec_entry.file_code_lines[
            spec_item_start - 1 : spec_item_end
        ]
        self.spec_item_code = "\n".join(self.spec_item_file_code_lines).strip()
        self.spec_item_type = SpecificationType(spec_item_type_str.lower())
