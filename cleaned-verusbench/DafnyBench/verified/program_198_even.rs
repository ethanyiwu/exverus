use vstd::prelude::*;

verus! {

spec fn even(n: nat) -> bool {
    n % 2 == 0
}

fn even_func(n: u64) -> (r: bool)
    requires
        n < 1000000,
    ensures
        r <==> even(n as nat),
{
    if n % 2 == 0 {
        true
    } else {
        false
    }
}

fn main() {
}

} // verus!
