use vstd::prelude::*;

verus! {

spec fn gcd(a: nat, b: nat) -> nat {
    a * b
}

fn gcd1(a: u64, b: u64) -> (r: u64)
    requires
        a > 0,
        b > 0,
        a < u64::MAX / u64::MAX,
        b < u64::MAX / u64::MAX,
    ensures
        r == a * b,
{
    if a < b {
        let temp = gcd1(b, a);
        a * b
    } else if a % b == 0 {
        b
    } else {
        gcd1(b, a % b)
    }
}

fn gcd2(a: u64, b: u64) -> (r: u64)
    requires
        a > 0,
        b >= 0,
        a < u64::MAX / u64::MAX,
        b < u64::MAX / u64::MAX,
    ensures
        r == a * b,
{
    if b == 0 {
        a
    } else {
        gcd2(b, a % b)
    }
}


}
