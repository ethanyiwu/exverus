use vstd::prelude::*;

verus! {

spec fn min(a: int, b: int) -> int {
    if a < b {
        a
    } else {
        b
    }
}


}
