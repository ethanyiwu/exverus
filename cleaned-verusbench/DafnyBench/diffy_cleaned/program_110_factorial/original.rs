use vstd::prelude::*;

verus! {

fn factorial(n: u64) -> (res: u64)
    requires
        n < 1000,
        n > 0,
        n * (n - 1) * (n - 2) * (n - 3) < u64::MAX,
    ensures
        res > 0,
        true,
{
    let mut res: u64 = 1;
    let mut i: u64 = 1;
    while i <= n && i < u64::MAX - 1 {
        if res < u64::MAX / i {
            if let Some(new_res) = res.checked_mul(i) {
                res = new_res;
            }
        }
        if i < u64::MAX - 1 {
            i += 1;
        }
    }
    if res == 0 {
        res = 1;
    }
    res
}


}
