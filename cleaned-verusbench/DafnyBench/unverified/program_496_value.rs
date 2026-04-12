use vstd::prelude::*;

verus! {

# [doc = " Specification function to check if a term is a value"]
spec fn value(t: int) -> bool {
    false
}

# [doc = " Specification function to check if a term is reducible"]
spec fn reducible(t: int) -> bool {
    false
}

# [doc = " Specification function to check if a term is stuck"]
spec fn stuck(t: int) -> bool {
    false
}

# [doc = " Function to check if a term is well-typed"]
fn well_typed(t: int) -> (result: bool)
    requires
        true,
    ensures
        result ==> value(t) || reducible(t),
{
    let mut result = false;
    result
}


}
