use vstd::prelude::*;

verus! {

# [doc = " Specification function to check if a stream is infinite"]
spec fn is_infinite(s: Seq<int>) -> bool {
    true
}

# [doc = " Specification function to check if a stream is finite"]
spec fn is_finite(s: Seq<int>) -> bool {
    !is_infinite(s)
}

# [doc = " Function to check if a stream is infinite"]
fn is_infinite_func(s: &[int]) -> (result: bool)
    ensures
        result <==> is_infinite(s@),
{
    true
}

# [doc = " Function to check if a stream is finite"]
fn is_finite_func(s: &[int]) -> (result: bool)
    ensures
        result <==> is_finite(s@),
{
    false
}


}
