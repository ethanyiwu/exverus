use vstd::prelude::*;

verus! {

#[verifier::memoize]
spec fn spec_fibfib(n: nat) -> nat
    decreases n,
{
    if (n == 0) {
        0
    } else if (n == 1) {
        0
    } else if (n == 2) {
        1
    } else {
        spec_fibfib((n - 1) as nat) + spec_fibfib((n - 2) as nat) + spec_fibfib((n - 3) as nat)
    }
}

fn fibfib(x: u32) -> (ret: Option<u32>)
    ensures
        match ret {
            None => spec_fibfib(x as nat) > u32::MAX,
            Some(f) => f == spec_fibfib(x as nat),
        },
    decreases x,
{
    if x > 39 {
        return None;
    }
    match (x) {
        0 => Some(0),
        1 => Some(0),
        2 => Some(1),
        _ => { Some(fibfib(x - 1)? + fibfib(x - 2)? + fibfib(x - 3)?) },
    }
}

} // verus!
fn main() {}
