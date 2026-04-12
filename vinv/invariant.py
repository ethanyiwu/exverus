from typing import List


class InvariantEntry:
    # assume the verus code has been formatted before parsing
    def __init__(
        self,
        file_code_lines: List[str],
        func_name: str,
        func_start: int,
        loop_start: int,
        invariant_entry_start: int,
        invariant_entry_end: int,
        invariants_code: str,
    ):
        self.file_code_lines = file_code_lines
        self.func_name = func_name
        self.func_start = func_start
        self.loop_start = loop_start
        self.invariant_entry_start = invariant_entry_start
        self.invariant_entry_end = invariant_entry_end
        self.invariants_code = invariants_code.replace("invariant", "").strip()
        self.invariants_code = self.invariants_code.split("decreases")[0].strip()
        # self.invariant_list = [line.replace(",", "").strip() for line in self.invariants_code.splitlines()]
        self.decreases = (
            self.invariants_code.split("decreases")[-1].strip()
            if "decreases" in self.invariants_code
            else None
        )


class InvariantItem:
    def __init__(
        self,
        invariant_entry: InvariantEntry,
        invariant_item_start: int,
        invariant_item_end: int,
    ):
        self.invariant_entry = invariant_entry
        self.invariant_item_start = invariant_item_start  # one-based index, inclusive
        self.invariant_item_end = invariant_item_end  # one-based index, inclusive
        self.invariant_item_file_code_lines = invariant_entry.file_code_lines[
            invariant_item_start - 1 : invariant_item_end
        ]
        self.invariant_item_code = "\n".join(
            self.invariant_item_file_code_lines
        ).strip()


def parse_invariant_items(invariant_entry: InvariantEntry) -> List[InvariantItem]:
    """
    Parse the invariant items from the invariant entry. The invariant items are splitted by commas.
    """

    invariant_items = []
    invariant_item_start = (
        invariant_entry.invariant_entry_start
    )  # one-based index, inclusive
    for line_no in range(
        invariant_entry.invariant_entry_start, invariant_entry.invariant_entry_end + 1
    ):
        line = invariant_entry.file_code_lines[line_no - 1].strip()
        if line.endswith(",") or line_no == invariant_entry.invariant_entry_end:
            invariant_item_end = line_no
            invariant_items.append(
                InvariantItem(
                    invariant_entry,
                    invariant_item_start,
                    invariant_item_end,
                )
            )
            invariant_item_start = line_no + 1

    return invariant_items
