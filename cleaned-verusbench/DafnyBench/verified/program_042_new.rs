use vstd::prelude::*;

verus! {

struct Ref {
    val: i32,
}

impl Ref {
    fn new(a: i32) -> (r: Self)
        ensures
            r.val == a,
    {
        Ref { val: a }
    }
}

fn main() {
}

} // verus!
