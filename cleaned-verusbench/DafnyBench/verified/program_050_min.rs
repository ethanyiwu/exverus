use vstd::prelude::*;

verus! {

spec fn min(a: int, b: int) -> int {
    if a < b {
        a
    } else {
        b
    }
}

proof fn min_proof(a: int, b: int)
    requires
        a <= b || b <= a,
    ensures
        min(a, b) <= a && min(a, b) <= b,
        min(a, b) == a || min(a, b) == b,
{
    if a < b {
        assert(min(a, b) == a);
    } else {
        assert(min(a, b) == b);
    }
}

fn main() {
}

} // verus!
