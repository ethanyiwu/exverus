from typing import Dict, List, Union

from veval import VerusError, VerusError2m, VerusErrorType, m2VerusError


class CounterExample:
    """Represents a counterexample for a proof's verification error."""

    def __init__(
        self,
        error_type: Union[VerusErrorType, str],
        failing_state: Dict,
        failing_location: str,
        error_message: str,
        cex_index: int,
        suggested_fix: str = None,
    ):
        # Handle both VerusErrorType and string error types
        if isinstance(error_type, str):
            # Try to map string to VerusErrorType
            error_msg_lower = error_type.lower()
            mapped_type = None
            for msg, err_type in m2VerusError.items():
                if msg.lower() in error_msg_lower:
                    mapped_type = err_type
                    break
            self.error_type = mapped_type or VerusErrorType.Other
        else:
            self.error_type = error_type

        self.failing_state = failing_state  # Keep original dict
        # Create hashable version, converting unhashable values like lists to tuples
        hashable_items = []
        for key, value in failing_state.items():
            if isinstance(value, list):
                hashable_items.append((key, tuple(value)))
            elif isinstance(value, dict):
                # Convert nested dicts to frozensets recursively
                hashable_items.append((key, frozenset(value.items())))
            else:
                hashable_items.append((key, value))
        self._failing_state_hashable = frozenset(hashable_items)  # Hashable version
        self.failing_location = failing_location
        self.error_message = error_message
        self.cex_index = cex_index
        self.suggested_fix = suggested_fix
        self.validate_status = {}  # {path -> status}
        self.block_status = {}  # {path -> status}

    def __str__(self) -> str:
        result = [
            f"Error Type: {self.error_type}",
            f"Failing Location: {self.failing_location}",
            f"Error Message: {self.error_message}",
            "Failing State:",
        ]
        for var, value in self.failing_state.items():
            result.append(f"  {var}: {value}")
        if self.suggested_fix:
            result.append(f"Suggested Fix: {self.suggested_fix}")
        return "\n".join(result)

    def to_dict(self) -> dict:
        """Convert the counter example to a dictionary for serialization."""
        return {
            "error_type": VerusError2m.get(self.error_type, "other"),
            "failing_state": self.failing_state,
            "failing_location": self.failing_location,
            "error_message": self.error_message,
            "suggested_fix": self.suggested_fix,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CounterExample":
        """Create a CounterExample instance from a dictionary."""
        error_type = data["error_type"]
        # Convert string error type to VerusErrorType
        if isinstance(error_type, str):
            error_type = m2VerusError.get(error_type, VerusErrorType.Other)

        return cls(
            error_type=error_type,
            failing_state=data["failing_state"],
            failing_location=data["failing_location"],
            error_message=data["error_message"],
            suggested_fix=data.get("suggested_fix"),
        )

    def get_hashable_state(self) -> frozenset:
        """Get the hashable version of the failing state."""
        return self._failing_state_hashable


def is_true_cex_from_validation_result(
    res: Dict[str, object], target_error: VerusError
) -> bool:
    """Decide if a CE is true based on validation result and target error type.

    Rules:
      - If target error is InvFailFront (invariant failed before loop):
          require detected == True and failure_region == "before".
      - If target error is InvFailEnd (invariant failed at end of loop body):
          require detected == True and failure_region == "after".
      - Otherwise (unknown/other errors): consider as true for now.
    """
    detected = bool(res.get("detected"))
    region = res.get("failure_region")
    if target_error.error == VerusErrorType.InvFailFront:
        return bool(detected and region == "before")
    elif target_error.error == VerusErrorType.InvFailEnd:
        return bool(detected and region == "after")
    else:
        # For other errors, treat as true for now
        return True


def add_validate_status(
    counter_examples: List[CounterExample],
    results: List[Dict[str, object]],
    key: str,
    target_error: VerusError,
) -> None:
    """Attach per-CE validation status to each CounterExample under validate_status[key].

    Args:
        counter_examples: the CE objects to annotate (indexed by cex_index order)
        results: list of validation result dicts; each should include 'cex_index'
        key: identifier for this validation run (e.g., extracted harness path)
    """
    # Build index -> result mapping
    idx2res: Dict[int, Dict[str, object]] = {}  # cex_index -> result
    for r in results:
        idx2res[int(r.get("cex_index"))] = r

    for cex in counter_examples:
        res = idx2res.get(int(cex.cex_index), {})
        status = {
            "true_cex": is_true_cex_from_validation_result(res, target_error),
            "detected": bool(res.get("detected")),
            "verification_passed": bool(res.get("verification_passed")),
            "failure_region": res.get("failure_region"),
            "injected_file": res.get("injected_file"),
            "errors": res.get("errors", []),
        }
        cex.validate_status[key] = status
