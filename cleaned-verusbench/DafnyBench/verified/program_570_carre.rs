use vstd::prelude::*;

verus! {

fn carre(a: u64) -> (c: u64)
    requires
        a < 1000,
        a * a < u64::MAX,
    ensures
        c == a * a,
{
    let mut c: u128 = 0;
    c = a as u128 * a as u128;
    assert(c <= u64::MAX as u128);
    c as u64
}

fn main() {
}

} // verus!
