use vstd::prelude::*;

verus! {

struct Pair {
    x: int,
    y: int,
}

fn pair_x(p: Pair) -> (x: int)
    ensures
        x == p.x,
{
    p.x
}

fn pair_y(p: Pair) -> (y: int)
    ensures
        y == p.y,
{
    p.y
}

fn pair(x: int, y: int) -> (p: Pair)
    ensures
        p.x == x && p.y == y,
{
    Pair { x, y }
}


}
