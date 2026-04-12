use vstd::prelude::*;

verus! {

# [doc = " Specification function for even numbers"]
spec fn even(n: nat) -> bool {
    n % 2 == 0
}

# [doc = " Function to check if a number is even"]
fn is_even(n: u64) -> (r: bool)
    requires
        n < 1000000,
    ensures
        r <==> even(n as nat),
{
    if n % 2 == 0 {
        true
    } else {
        false
    }
}


}
