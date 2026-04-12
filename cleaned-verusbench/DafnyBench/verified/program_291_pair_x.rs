use vstd::prelude::*;

verus! {

// Define a Pair struct
struct Pair {
    x: int,
    y: int,
}

// Define functions for accessing Pair elements
spec fn pair_x(p: Pair) -> int {
    p.x
}

spec fn pair_y(p: Pair) -> int {
    p.y
}

// Define a function for creating a new Pair
spec fn pair(x: int, y: int) -> Pair {
    Pair { x, y }
}

// Define a lemma that uses Pair
proof fn use_pair() {
    assert(pair(1, 2) != pair(2, 1));
    let p = pair(1, 2);
    assert(pair_x(p) + pair_y(p) == 3);

    assert(forall|p1: Pair, p2: Pair|
        pair_x(p1) == pair_x(p2) && pair_y(p1) == pair_y(p2) ==> p1 == p2);
}

// Define axioms for Pair
proof fn x_defn()
    ensures
        forall|x: int, y: int| pair_x(pair(x, y)) == x,
{
    assert(true);
}

proof fn y_defn()
    ensures
        forall|x: int, y: int| pair_y(pair(x, y)) == y,
{
    assert(true);
}

proof fn bijection()
    ensures
        forall|p: Pair| pair(pair_x(p), pair_y(p)) == p,
{
    assert(true);
}

// Define a function that uses the axioms
proof fn use_encoding() {
    x_defn();
    y_defn();
    bijection();

    assert(pair(1, 2) != pair(2, 1)) by {
        x_defn();
    }

    assert(pair_y(pair(1, 2)) == 2) by {
        y_defn();
    }

    assert(forall|p1: Pair, p2: Pair|
        pair_x(p1) == pair_x(p2) && pair_y(p1) == pair_y(p2) ==> p1 == p2) by {
        bijection();
    }
}

fn main() {
}

} // verus!
