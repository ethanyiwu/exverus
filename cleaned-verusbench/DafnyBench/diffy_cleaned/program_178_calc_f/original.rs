use vstd::prelude::*;

verus! {

fn calc_f(n: u64) -> (res: u64)
    requires
        n >= 0,
        n < 1000000,
        n < u64::MAX / u64::MAX,
    ensures
        res == n,
{
    let mut a: u64 = 0;
    let mut b: u64 = 1;
    let mut c: u64 = 2;
    let mut i: u64 = 0;
    while i < n {
        let temp_a: u64 = b;
        let temp_b: u64 = c;
        let temp_c: u64 = a + c;
        a = temp_a;
        b = temp_b;
        c = temp_c;
        i = i + 1;
    }
    a
}


}
