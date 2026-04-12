use vstd::prelude::*;

verus! {

// Specification function for pair
spec fn pair(x: int, y: int) -> (pair: (int, int)) {
    (x, y)
}

// Specification function for pair_x
spec fn pair_x(pair: (int, int)) -> int {
    pair.0
}

// Specification function for pair_y
spec fn pair_y(pair: (int, int)) -> int {
    pair.1
}

// Proof function for pair_x
proof fn pair_x_proof(pair: (int, int)) -> (x: int)
    ensures
        x == pair.0,
{
    pair.0
}

// Proof function for pair_y
proof fn pair_y_proof(pair: (int, int)) -> (y: int)
    ensures
        y == pair.1,
{
    pair.1
}

// Proof function for bijection
proof fn bijection_proof(pair: (int, int)) -> (p: (int, int))
    ensures
        p == pair,
{
    pair
}

fn main() {
}

} // verus!
