use vstd::prelude::*;

verus! {

spec fn spec_sum_to_n(n: nat) -> nat
    decreases n,
{
    if (n == 0) {
        0
    } else {
        n + spec_sum_to_n((n - 1) as nat)
    }
}

fn sum_to_n(n: u32) -> (sum: Option<u32>)
    ensures
        match sum {
            None => spec_sum_to_n(n as nat) > u32::MAX,
            Some(f) => f == spec_sum_to_n(n as nat),
        },
{
    if n >= 92682 {
        return None;
    }
    let mut res: u32 = 0;
    let mut sum: u32 = 0;
    let mut i: u32 = 0;
    while i < n {
        i += 1;
        res = i + res;
    }
    Some(res)
}

} // verus!
fn main() {}
