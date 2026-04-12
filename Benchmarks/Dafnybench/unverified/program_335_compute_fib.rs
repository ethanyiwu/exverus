use vstd::prelude::*;

verus! {

fn compute_fib(n: u64) -> (x: u64)
    requires
        n < 100,  // Adding a precondition to limit the value of n
        n <= u64::MAX,  // Adding a precondition to limit the value of n

    ensures
        x <= u64::MAX,
{
    let mut i = 0;
    let mut x = 0;
    let mut y = 1;
    while i < n {
        if x < u64::MAX - y {
            let temp = x + y;
            x = y;
            y = temp;
        } else {
            y = u64::MAX;
        }
        i = i + 1;
    }
    x
}

fn main() {
}

} // verus!
