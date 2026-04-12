use vstd::prelude::*;

verus! {

/// A type for an identifier
struct Id;

/// Function F
spec fn f(s: Seq<Id>) -> int;

proof fn test(x: Id)
    ensures
        f(seq![x]) == f(seq![x]),
{
    let a = seq![x];
    let b = seq![x];
    assert(a.len() == b.len());
    assert(a == b);
}

fn main() {
}

} // verus!
