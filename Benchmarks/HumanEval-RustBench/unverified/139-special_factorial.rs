use vstd::arithmetic::mul::*;
use vstd::prelude::*;

verus! {

fn brazilian_factorial_impl(n: u64) -> (ret: Option<u64>)
    ensures
        match ret {
            None => brazilian_factorial(n as nat) > u64::MAX,
            Some(bf) => bf == brazilian_factorial(n as nat),
        },
{
    if n >= 9 {
        return None;
    }
    let mut start = 1u64;
    let mut end = n + 1u64;
    let mut fact_i = 1u64;
    let mut special_fact = 1u64;

    while start < end
    {

        fact_i = start * fact_i;

        special_fact = fact_i * special_fact;

        start = start + 1;
    }
    return Some(special_fact);

}

} // verus!
fn main() {}
