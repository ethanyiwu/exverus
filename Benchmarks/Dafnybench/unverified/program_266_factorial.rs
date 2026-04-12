use vstd::prelude::*;

verus! {

fn factorial(n: u64) -> (res: u64)
    requires
        n >= 0,
        n < 1000000,
        n * (n + 1) / 2 < u64::MAX,
    ensures
        res >= 0,
{
    let mut i = 0;
    let mut res = 1;
    while i < n {
        let temp: u128 = (res as u128) + (i as u128);
        if temp <= u64::MAX as u128 {
            res = temp as u64;
        } else {
            res = u64::MAX;
        }
        i = i + 1;
    }
    res
}

fn main() {
}

} // verus!
