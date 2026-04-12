use vstd::prelude::*;

verus! {

# [doc = " Specification function"]
spec fn law_of_excluded_middle(b: bool) -> bool {
    b || !b
}


}
