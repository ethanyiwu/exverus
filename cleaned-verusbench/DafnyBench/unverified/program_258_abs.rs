use vstd::prelude::*;

verus! {

spec fn abs(x: int) -> int {
    if x < 0 {
        -x
    } else {
        x
    }
}


}
