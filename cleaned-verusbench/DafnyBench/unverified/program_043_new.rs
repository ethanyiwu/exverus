use vstd::prelude::*;

verus! {

struct Ref<A> {
    val: A,
}

impl<A> Ref<A> {
    fn new(val: A) -> (r: Ref<A>)
        ensures
            r.val == val,
    {
        Ref { val }
    }
}


}
