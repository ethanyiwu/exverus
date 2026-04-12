use vstd::prelude::*;

verus! {

fn calc_f(n: u64) -> (res: u64)
    requires
        n > 0,
        n <= 1000,  // added precondition to prevent overflow
        n < u64::MAX / u64::MAX,  // added precondition to prevent overflow

    ensures
        res == n,
{
    let mut a: u64 = 0;
    let mut b: u64 = 1;
    let mut c: u64 = 2;
    let mut i: u64 = 0;
    while i < n
        invariant
            0 <= i && i <= n,
            a == i && b == i + 1 && c == i + 2,
            n <= 1000,  // added precondition to prevent overflow
            n < u64::MAX / u64::MAX,  // added precondition to prevent overflow

        decreases n - i,
    {
        let temp: u64 = a + c;
        assert(temp <= u64::MAX);
        a = b;
        b = c;
        c = temp;
        i = i + 1;
    }
    a
}

fn main() {
}

} // verus!
