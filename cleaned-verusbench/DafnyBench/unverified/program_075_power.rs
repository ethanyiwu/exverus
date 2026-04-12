use vstd::prelude::*;

verus! {

# [doc = " Specification function to calculate power of 2"]
spec fn power(n: nat) -> nat {
    if n == 0 {
        1
    } else {
        n * 2
    }
}

# [doc = " Function to calculate power of 2 using iteration"]
fn power_func(n: u64) -> (result: u64)
    requires
        n > 0,
        n < u64::MAX / u64::MAX,
    ensures
        result == power(n as nat),
{
    let mut result: u64 = 1;
    for i in 1..n {
        result = result * 2;
    }
    result
}


}
