use vstd::prelude::*;

verus! {

# [doc = " Specification function to calculate the division of two numbers"]
spec fn div(a: int, b: int) -> int {
    a / b
}

# [doc = " Specification function to calculate the modulo of two numbers"]
spec fn mod_(a: int, b: int) -> int {
    a % b
}

# [doc = " Proof function to calculate the division of two numbers"]
fn div_sub(a: u64, b: u64) -> (q: u64)
    requires
        a >= 0,
        b > 0,
        a < u64::MAX,
        b < u64::MAX,
        a < b * b,
    ensures
        q == a / b,
{
    a / b
}

# [doc = " Proof function to calculate the modulo of two numbers"]
fn mod_sub(a: u64, b: u64) -> (r: u64)
    requires
        a >= 0,
        b > 0,
        a < u64::MAX,
        b < u64::MAX,
        a < b * b,
    ensures
        r == a % b,
{
    a % b
}


}
