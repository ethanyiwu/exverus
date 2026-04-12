use vstd::prelude::*;

verus! {

fn mult(n0: i32, m0: i32) -> (res: i32)
    requires
        n0 * m0 >= i32::MIN && n0 * m0 <= i32::MAX,
    ensures
        res == n0 as int * m0 as int,
{
    let mut res: i32 = n0 * m0;
    res
}


}
