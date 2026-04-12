use vstd::prelude::*;

verus! {

struct Pair {
    x: int,
    y: int,
}

fn pair_x(p: &Pair) -> (x: int)
    requires
        true,
    ensures
        x == p.x,
{
    p.x
}

fn pair_y(p: &Pair) -> (y: int)
    requires
        true,
    ensures
        y == p.y,
{
    p.y
}

fn main() {
}

} // verus!
