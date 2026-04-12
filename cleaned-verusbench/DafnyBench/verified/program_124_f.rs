use vstd::prelude::*;

verus! {

spec fn f(s: Seq<int>) -> int {
    0
}

proof fn test(x: int)
    ensures
        f(seq![x]) == 0,
{
    assert(true);
}

fn main() {
}

} // verus!
