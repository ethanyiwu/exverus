use vstd::prelude::*;

verus! {

spec fn max(a: int, b: int) -> int {
    if a > b {
        a
    } else {
        b
    }
}


}
