use vstd::prelude::*;

verus! {

struct Ref<A> {
    val: A,
}

impl<A> Ref<A> {
    fn new(a: A) -> (ref_a: Ref<A>)
        ensures
            ref_a.val == a,
    {
        Ref { val: a }
    }
}

fn main() {
}

} // verus!
