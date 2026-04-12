use vstd::prelude::*;

verus! {

/// Specification function to create a pair
spec fn pair(x: int, y: int) -> (pair: (int, int)) {
    (x, y)
}

/// Specification function to get the x-coordinate of a pair
spec fn pair_x(pair: (int, int)) -> int {
    pair.0
}

/// Specification function to get the y-coordinate of a pair
spec fn pair_y(pair: (int, int)) -> int {
    pair.1
}

/// Proof function to use pairs
proof fn use_pair()
    requires
        true,
    ensures
        pair_x(pair(1, 2)) + pair_y(pair(1, 2)) == 3,
        pair(1, 2) != pair(2, 1),
        pair_x(pair(1, 2)) == 1,
        pair_y(pair(1, 2)) == 2,
        forall|p1: (int, int), p2: (int, int)|
            pair_x(p1) == pair_x(p2) && pair_y(p1) == pair_y(p2) ==> p1 == p2,
{
    assert(pair_x(pair(1, 2)) + pair_y(pair(1, 2)) == 3);
    assert(pair(1, 2) != pair(2, 1));
    assert(pair_x(pair(1, 2)) == 1);
    assert(pair_y(pair(1, 2)) == 2);
    assert(forall|p1: (int, int), p2: (int, int)|
        pair_x(p1) == pair_x(p2) && pair_y(p1) == pair_y(p2) ==> p1 == p2);
}

fn main() {
}

} // verus!
