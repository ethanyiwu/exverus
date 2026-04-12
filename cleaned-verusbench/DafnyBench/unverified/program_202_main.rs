use vstd::prelude::*;

verus! {

# [doc = " Proof function to calculate the length of a list"]
fn length<T>(xs: &[T]) -> (len: usize)
    requires
        true,
    ensures
        len == xs.len(),
{
    xs.len()
}


}
