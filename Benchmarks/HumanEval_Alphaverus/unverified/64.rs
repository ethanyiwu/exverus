use vstd::prelude::*;

verus! {

// O(n) non-recursive solution using same spec as 55a
#[verifier::memoize]
spec fn spec_fib(n: nat) -> nat
    decreases n,
{
    if (n == 0) {
        0
    } else if (n == 1) {
        1
    } else {
        spec_fib((n - 1) as nat) + spec_fib((n - 2) as nat)
    }
}

fn fib(n: u32) -> (ret: Option<u32>)
    ensures
        match ret {
            None => spec_fib(n as nat) > u32::MAX,
            Some(f) => f == spec_fib(n as nat),
        },
{
    if n == 0 {
        return Some(0);
    }
    if n == 1 {
        return Some(1);
    }
    if n > 47 {
        return None;
    }
    let mut a: u32 = 0;
    let mut b: u32 = 1;
    let mut i: u32 = 2;

    for i in 1..n {
        let sum = a + b;
        a = b;
        b = sum;
    }
    Some(b)
}

} // verus!
fn main() {}
