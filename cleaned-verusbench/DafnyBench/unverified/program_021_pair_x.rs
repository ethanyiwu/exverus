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
        p.x == x,
        p.y == y,
{
    Pair { x, y }
}

fn pair_equality(p1: Pair, p2: Pair) -> (equal: bool)
    ensures
        equal ==> p1.x == p2.x && p1.y == p2.y,
        !equal ==> p1.x != p2.x || p1.y != p2.y,
{
    let x_equal = p1.x == p2.x;
    let y_equal = p1.y == p2.y;
    if x_equal && y_equal {
        true
    } else {
        false
    }
}


}
