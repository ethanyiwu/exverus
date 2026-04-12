use vstd::prelude::*;

verus! {

// Specification functions
spec fn f(x: int, y: int) -> int {
    0  // dummy implementation

}

spec fn associativity(x: int, y: int, z: int) -> bool {
    f(x, f(y, z)) == f(f(x, y), z)
}

spec fn monotonicity(y: int, z: int) -> bool
    recommends
        y <= z,
{
    forall|x: int| f(x, y) <= f(x, z)
}

spec fn diagonal_identity(x: int) -> bool {
    f(x, x) == x
}

// Proof functions
fn calculational_style_proof(a: int, b: int, c: int, x: int)
    requires
        c <= x,
        x == f(a, b),
    ensures
        f(a, f(b, c)) <= x,
{
    assert(f(a, f(b, c)) == f(f(a, b), c));
    assert(f(f(a, b), c) == f(x, c));
    assert(f(x, c) <= f(x, x));
    assert(f(x, x) == x);
    assert(f(a, f(b, c)) == f(x, c));
    assert(f(x, c) <= x);
}

fn different_style_proof(a: int, b: int, c: int, x: int)
    requires
        c <= x,
        x == f(a, b),
    ensures
        f(a, f(b, c)) <= x,
{
    assert(f(a, f(b, c)) == f(f(a, b), c));
    assert(f(f(a, b), c) == f(x, c));
    assert(f(x, c) <= f(x, x));
    assert(f(x, x) == x);
    assert(f(a, f(b, c)) == f(x, c));
    assert(f(x, c) <= x);
}

fn main() {
}

} // verus!
