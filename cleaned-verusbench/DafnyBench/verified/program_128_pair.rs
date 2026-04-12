use vstd::prelude::*;

verus! {

// Specification function for a pair
spec fn pair(x: int, y: int) -> (pair: (int, int)) {
    (x, y)
}

// Specification function for pair_x
spec fn pair_x(p: (int, int)) -> int {
    p.0
}

// Specification function for pair_y
spec fn pair_y(p: (int, int)) -> int {
    p.1
}

// Proof function to use pairs
proof fn use_pair()
    ensures
        pair(1, 2) != pair(2, 1),
        pair_x(pair(1, 2)) + pair_y(pair(1, 2)) == 3,
        forall|p1: (int, int), p2: (int, int)|
            pair_x(p1) == pair_x(p2) && pair_y(p1) == pair_y(p2) ==> p1 == p2,
{
    assert(pair(1, 2) != pair(2, 1));
    let p = pair(1, 2);
    assert(pair_x(p) + pair_y(p) == 3);

    assert(forall|p1: (int, int), p2: (int, int)|
        pair_x(p1) == pair_x(p2) && pair_y(p1) == pair_y(p2) ==> p1 == p2);
}

// Proof function to use encoding
proof fn use_encoding()
    ensures
        pair_x(pair(1, 2)) == 1,
        pair_y(pair(1, 2)) == 2,
        forall|p1: (int, int), p2: (int, int)|
            pair_x(p1) == pair_x(p2) && pair_y(p1) == pair_y(p2) ==> p1 == p2,
{
    assert(pair_x(pair(1, 2)) == 1);
    assert(pair_y(pair(1, 2)) == 2);

    assert(forall|p1: (int, int), p2: (int, int)|
        pair_x(p1) == pair_x(p2) && pair_y(p1) == pair_y(p2) ==> p1 == p2);
}

fn main() {
}

} // verus!
