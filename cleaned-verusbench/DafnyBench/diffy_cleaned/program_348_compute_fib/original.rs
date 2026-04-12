use vstd::prelude::*;

verus! {

fn compute_fib(n: u64) -> (x: u64)
    requires
        n < 100,
        n <= u64::MAX,
    ensures
        x <= u64::MAX,
{
    let mut i = 0;
    let mut x = 0;
    let mut y = 1;
    while i < n {
        if y < u64::MAX - x {
            let temp = x + y;
            x = y;
            y = temp;
        } else {
            x = u64::MAX;
            y = u64::MAX;
        }
        i = i + 1;
    }
    x
}


}
