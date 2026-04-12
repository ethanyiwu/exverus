use vstd::prelude::*;

verus! {

# [doc = " Specification function to check if a boolean is true or false"]
spec fn is_bool(b: bool) -> bool {
    b || !b
}

# [doc = " Proof function to check if a boolean is true or false"]
fn m() {
    n();
    n();
}


}
