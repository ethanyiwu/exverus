use vstd::prelude::*;

verus! {

fn calc_f(n: u64) -> (res: u64)
    requires
        n > 0,
        n <= 1000,
        n < u64::MAX / u64::MAX,
    ensures
        res == n,
{
    let mut a: u64 = 0;
    let mut b: u64 = 1;
    let mut c: u64 = 2;
    let mut i: u64 = 0;
    while i < n {
        let temp: u64 = a + c;
        a = b;
        b = c;
        c = temp;
        i = i + 1;
    }
    a
}


}
