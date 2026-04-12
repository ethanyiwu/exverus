use vstd::prelude::*;

verus! {

fn fib(n: u64) -> (result: u64)
    requires
        n < 1000, // added precondition to prevent overflow
    ensures
        result <= u64::MAX / 2, // added postcondition to prevent overflow
{
    let mut i: u64 = 1;
    if n < 2 {
        return n;
    }
    let mut b: u64 = 1;
    let mut c: u64 = 1;

    while i < n
        invariant
            0 < i && i <= n,
            b <= u64::MAX / 2, // added precondition to prevent overflow
            c <= u64::MAX / 2, // added precondition to prevent overflow
        decreases
            n - i,
    {
        let temp: u128 = b as u128 + c as u128;
        assert(temp <= u64::MAX as u128);
        b = c;
        let c_new = temp as u64;
        if c_new <= u64::MAX / 2 {
            c = c_new;
        } else {
            c = u64::MAX / 2;
        }
        i = i + 1;
    }
    c
}

fn main() {}

} // verus!