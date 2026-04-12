# Define error priority order (lower number means higher priority)
ERROR_PRIORITY = {
    "MismatchedType": 1,
    "PreCondFailVecLen": 2,
    "PreCondFail": 3,
    "ArithmeticFlow": 4,
    "InvFailFront": 5,
    "InvFailEnd": 6,
    "AssertFail": 7,
    "PostCondFail": 8,
    "DecFailEnd": 9,
    "DecFailCont": 10,
    "SplitAssertFail": 11,
    "SplitPreFail": 12,
    "SplitPostFail": 13,
    "UnxProofBlock": 14,
    "RustAssert": 15,
    "ExecinGhost": 16,
    "RecommendNotMet": 17,
    "Other": 18,
}


def get_error_priority(error_type: object) -> int:
    """Get the priority for a given error type. Lower number means higher priority."""
    error_name = getattr(error_type, "name", str(error_type).split(".")[-1])
    return ERROR_PRIORITY.get(
        error_name, len(ERROR_PRIORITY) + 1
    )


def sort_errors_by_priority(errors: list) -> list:
    """Sort a list of VerusError objects by their priority."""
    return sorted(errors, key=lambda x: get_error_priority(x.error))
