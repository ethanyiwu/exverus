from veval import VerusErrorType

# Define error priority order (lower number means higher priority)
ERROR_PRIORITY = {
    VerusErrorType.MismatchedType: 1,  # Type mismatches
    VerusErrorType.PreCondFailVecLen: 2,  # Vector length precondition failures
    VerusErrorType.PreCondFail: 3,  # Precondition failures
    VerusErrorType.ArithmeticFlow: 4,  # Arithmetic overflow/underflow
    VerusErrorType.InvFailFront: 5,  # Loop invariant not satisfied before loop
    VerusErrorType.InvFailEnd: 6,  # Loop invariant not satisfied at end of loop
    VerusErrorType.AssertFail: 7,  # Assertion failures
    VerusErrorType.PostCondFail: 8,  # Postcondition failures
    VerusErrorType.DecFailEnd: 9,  # Decreases not satisfied at end of loop
    VerusErrorType.DecFailCont: 10,  # Decreases not satisfied at continue
    VerusErrorType.SplitAssertFail: 11,  # Split assertion failures
    VerusErrorType.SplitPreFail: 12,  # Split precondition failures
    VerusErrorType.SplitPostFail: 13,  # Split postcondition failures
    VerusErrorType.UnxProofBlock: 14,  # Unexpected proof blocks
    VerusErrorType.RustAssert: 15,  # Rust assert usage
    VerusErrorType.ExecinGhost: 16,  # Exec mode in ghost code
    VerusErrorType.RecommendNotMet: 17,  # Recommendations not met
    VerusErrorType.Other: 18,  # Other unclassified errors
}


def get_error_priority(error_type: VerusErrorType) -> int:
    """Get the priority for a given error type. Lower number means higher priority."""
    return ERROR_PRIORITY.get(
        error_type, len(ERROR_PRIORITY) + 1
    )  # Unknown errors get lowest priority


def sort_errors_by_priority(errors: list) -> list:
    """Sort a list of VerusError objects by their priority."""
    return sorted(errors, key=lambda x: get_error_priority(x.error))
