use vstd::prelude::*;

verus! {

struct Ref<A> {
    val: A,
}

impl<A> Ref<A> {
    fn new(a: A) -> (r: Self)
        ensures
            r.val == a,
    {
        Ref { val: a }
    }
}

fn main() {
}

} // verus!
