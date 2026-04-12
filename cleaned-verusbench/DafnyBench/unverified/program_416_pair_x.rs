use vstd::prelude::*;

verus! {

struct Pair {
    x: i32,
    y: i32,
}

fn pair_x(p: &Pair) -> (x: i32)
    ensures
        x == p.x,
{
    p.x
}

fn pair_y(p: &Pair) -> (y: i32)
    ensures
        y == p.y,
{
    p.y
}

fn use_pair()
    requires
        true,
{
    let p1 = Pair { x: 1, y: 2 };
    let p2 = Pair { x: 2, y: 1 };
    let p = Pair { x: 1, y: 2 };
}


}
