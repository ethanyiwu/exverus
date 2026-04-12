use vstd::prelude::*;

verus! {

# [doc = " Specification function for subset"]
pub open spec fn is_subset(a: Seq<int>, b: Seq<int>) -> bool {
    forall|x: int| a.contains(x) ==> b.contains(x)
}

# [doc = " Specification function for subset transitivity"]
pub open spec fn subset_transitivity(a: Seq<int>, b: Seq<int>, c: Seq<int>) -> bool {
    is_subset(a, b) && is_subset(b, c) ==> is_subset(a, c)
}


}
