use vstd::prelude::*;

verus! {

fn gen(start: u64) -> (x: u64)
    requires
        true,
    ensures
        x == start,
{
    start
}

fn gen_helper(start: u64, i: u64) -> (x: u64)
    requires
        0 <= i && i < 10,
        start + i < u64::MAX,
    ensures
        x == start + i,
{
    start + i
}

fn main() {
    let mut i = 0;
    while i < 10
        invariant
            0 <= i && i <= 10,
        decreases 10 - i,
    {
        let x = gen_helper(30, i);
        // print x;
        i += 1;
    }
}

} // verus!