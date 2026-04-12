use vstd::prelude::*;

verus! {

/// A pair of integers
struct Pair {
    x: int,
    y: int,
}

/// Extracts the first element of a pair
spec fn pair_x(p: Pair) -> int {
    p.x
}

/// Extracts the second element of a pair
spec fn pair_y(p: Pair) -> int {
    p.y
}

/// Creates a new pair from two integers
spec fn pair(x: int, y: int) -> Pair {
    Pair { x, y }
}

/// Axiom: pair_x(pair(x, y)) == x
proof fn x_defn(x: int, y: int) -> (ensures: bool)
    ensures
        pair_x(pair(x, y)) == x,
{
    true
}

/// Axiom: pair_y(pair(x, y)) == y
proof fn y_defn(x: int, y: int) -> (ensures: bool)
    ensures
        pair_y(pair(x, y)) == y,
{
    true
}

/// Axiom: pair(pair_x(p), pair_y(p)) == p
proof fn bijection(p: Pair) -> (ensures: bool)
    ensures
        pair(pair_x(p), pair_y(p)) == p,
{
    true
}

proof fn use_encoding() -> (ensures: bool) {
    x_defn(1, 2);
    y_defn(1, 2);
    bijection(Pair { x: 1, y: 2 });

    assert(pair(1, 2) != pair(2, 1)) by {
        x_defn(1, 2);
    }

    assert(pair_y(pair(1, 2)) == 2) by {
        y_defn(1, 2);
    }

    assert(forall|p1: Pair, p2: Pair|
        pair_x(p1) == pair_x(p2) && pair_y(p1) == pair_y(p2) ==> p1 == p2) by {
        bijection(Pair { x: 1, y: 2 });
    }

    true
}

fn main() {
}

} // verus!
