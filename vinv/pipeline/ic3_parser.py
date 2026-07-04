"""
Parser functions for IC3-style responses from LLM.
"""
from typing import Dict, List, Tuple

from veval import VerusError

from vinv.pipeline.counter_example import CounterExample


def parse_state_dict(state_lines: List[str]) -> Dict:
    """Parse state lines into a dictionary."""
    state = {}
    for line in state_lines:
        if "=" in line:
            var, value = map(str.strip, line.split("=", 1))
            state[var] = value
    return state


def parse_ic3_generation_response(
    response: str, verus_error: VerusError, console_error_msg: str
) -> CounterExample:
    """
    Parse LLM response for counter example generation.

    Expected format:
    ```
    Error Type: <error_type>
    Failing Location: <location>

    Minimal Failing State:
    <var1> = <value1>
    <var2> = <value2>
    ...

    State Evolution:
    1. Initial: <state1>
    2. After <event>: <state2>
    ...

    Key Predicates:
    1. <predicate1>
    2. <predicate2>
    ...

    Suggested Invariant Clauses:
    1. <clause1>
    2. <clause2>
    ...
    ```
    """
    lines = response.strip().split("\n")
    error_type = None
    failing_location = None
    state_lines = []
    suggested_fix = None

    current_section = None
    predicates = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith("Error Type:"):
            error_type = line.split(":", 1)[1].strip()
        elif line.startswith("Failing Location:"):
            failing_location = line.split(":", 1)[1].strip()
        elif line == "Minimal Failing State:":
            current_section = "state"
            state_lines = []  # Reset state lines
        elif line.startswith("State Evolution:"):
            current_section = "evolution"
        elif line.startswith("Key Predicates:"):
            current_section = "predicates"
        elif line.startswith("Suggested Invariant Clauses:"):
            current_section = "invariants"
            suggested_fix = ""
        elif current_section == "state":
            if "=" in line:
                state_lines.append(line)
        elif current_section == "predicates" and line.startswith("1."):
            predicates.append(line[2:].strip())
        elif current_section == "invariants":
            if suggested_fix:
                suggested_fix += "\n"
            suggested_fix += line.strip()

    # If we don't get an error type from response, use the one from verus_error
    if not error_type:
        error_type = verus_error.error

    # Parse state lines into a dictionary
    failing_state = parse_state_dict(state_lines)

    # Create and return counter example
    return CounterExample(
        error_type=error_type,
        failing_state=failing_state,
        failing_location=failing_location or "Unknown",
        error_message=console_error_msg,
        suggested_fix=suggested_fix,
    )


def parse_ic3_generalization_response(response: str) -> Tuple[str, List[str]]:
    """
    Parse LLM response for invariant generalization.

    Expected format:
    ```rust
    // New invariant clauses
    <code with new invariants>

    /*
    Justification:
    1. Why each clause is needed
    2. How it blocks the counter example
    3. Proof of inductiveness
    4. Progress toward property
    */
    ```

    Returns:
        Tuple[str, List[str]]: (fixed proof code, list of new invariant clauses)
    """
    # Extract code block
    code_start = response.find("```rust")
    if code_start == -1:
        code_start = response.find("```")
    code_end = response.find("```", code_start + 3)

    if code_start == -1 or code_end == -1:
        raise ValueError("Could not find code block in response")

    code = response[code_start:code_end].strip()
    if code.startswith("```rust"):
        code = code[7:]
    elif code.startswith("```"):
        code = code[3:]

    # Extract invariant clauses
    invariants = []
    in_invariant = False
    for line in code.split("\n"):
        line = line.strip()
        if line.startswith("invariant"):
            invariants.append(line)
            in_invariant = True
        elif in_invariant and line.endswith(","):
            invariants.append(line)
        else:
            in_invariant = False

    return code, invariants
