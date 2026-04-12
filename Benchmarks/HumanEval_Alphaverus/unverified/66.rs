use vstd::prelude::*;

verus! {

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
    decreases n,
{
    if n > 47 {
        return None;
    }
    match n {
        0 => Some(0),
        1 => Some(1),
        _ => {
            let n1 = fib(n - 1)?;
            let n2 = fib(n - 2)?;
            Some(n1 + n2)
        },
    }
}

} // verus!
fn main() {}
