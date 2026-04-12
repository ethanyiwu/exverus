use vstd::prelude::*;

verus! {

# [doc = " Specification function for reverse"]
spec fn reverse(xs: Seq<u64>) -> Seq<u64> {
    if xs.len() == 0 {
        Seq::empty()
    } else {
        Seq::new(xs.len(), |i| xs[xs.len() - 1 - i])
    }
}


}
