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
    assert(p1.x != p2.x || p1.y != p2.y);
    let p = Pair { x: 1, y: 2 };
    assert(p.x + p.y == 3);

    assert(forall|p1: Pair, p2: Pair|
        p1.x == p2.x && p1.y == p2.y ==> p1.x == p2.x && p1.y == p2.y);
}

fn main() {
}

} // verus!
