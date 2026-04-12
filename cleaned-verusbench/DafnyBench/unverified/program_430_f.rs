use vstd::prelude::*;

verus! {

spec fn f(x: int, y: int) -> int {
    0
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


}
