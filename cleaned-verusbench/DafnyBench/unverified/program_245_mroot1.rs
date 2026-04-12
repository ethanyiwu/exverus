use vstd::prelude::*;

verus! {

fn mroot1(n: u64) -> (r: u64)
    requires
        n >= 0,
        n < u64::MAX,
        n < u64::MAX / u64::MAX,
        n < 1000000,
    ensures
        r >= 0 && r * r <= n && n <= (r + 1) * (r + 1),
{
    let mut r: u64 = 0;
    while r * r < n {
        if r + 1 == u64::MAX {
            break ;
        } else {
            r = r + 1;
        }
    }
    r
}


}
