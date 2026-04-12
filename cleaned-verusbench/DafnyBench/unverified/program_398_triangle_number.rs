use vstd::prelude::*;

verus! {

fn triangle_number(n: u64) -> (t: u64)
    requires
        n as int >= 0,
        n < 1000000,
        n * (n + 1) < u64::MAX,
    ensures
        t as int == n as int * (n as int + 1) / 2,
{
    let mut t: u64 = (n * (n + 1)) / 2;
    t
}


}
