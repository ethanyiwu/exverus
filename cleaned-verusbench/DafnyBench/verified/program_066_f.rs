use vstd::prelude::*;

verus! {

spec fn f(s: Seq<int>) -> int {
    0
}

proof fn test(x: int)
    ensures
        f(Seq::<int>::empty()) == f(seq![x]),
{
    assert(f(Seq::<int>::empty()) == 0);
    assert(f(Seq::<int>::empty()) == f(seq![x]));
}

fn main() {
}

} // verus!
