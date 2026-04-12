use vstd::prelude::*;

verus! {

struct Pair {
    x: int,
    y: int,
}

spec fn pair_x(p: Pair) -> int {
    p.x
}

spec fn pair_y(p: Pair) -> int {
    p.y
}

// Dafny encodes pairs to SMT by emitting the SMT equivalent of the following.
// Then we define _uninterpreted functions_ for all the operations on the
// type. These are all the implicit operations on a DafnyVersion.Pair:
spec fn pair(x: int, y: int) -> Pair {
    Pair { x, y }
}

proof fn x_defn()
    ensures
        forall|x: int, y: int| pair_x(pair(x, y)) == x,
{
    assert(forall|x: int, y: int| pair_x(pair(x, y)) == x);
}

proof fn y_defn()
    ensures
        forall|x: int, y: int| pair_y(pair(x, y)) == y,
{
    assert(forall|x: int, y: int| pair_y(pair(x, y)) == y);
}

proof fn bijection()
    ensures
        forall|p: Pair| pair(pair_x(p), pair_y(p)) == p,
{
    assert(forall|p: Pair| pair(pair_x(p), pair_y(p)) == p);
}

proof fn use_encoding() {
    assert(pair(1, 2) != pair(2, 1));
    assert(pair_y(pair(1, 2)) == 2);
    assert(forall|p1: Pair, p2: Pair|
        pair_x(p1) == pair_x(p2) && pair_y(p1) == pair_y(p2) ==> p1 == p2);
}

fn main() {
}

} // verus!
