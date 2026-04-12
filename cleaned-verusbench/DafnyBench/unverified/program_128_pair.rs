use vstd::prelude::*;

verus! {

spec fn pair(x: int, y: int) -> (pair: (int, int)) {
    (x, y)
}

spec fn pair_x(p: (int, int)) -> int {
    p.0
}

spec fn pair_y(p: (int, int)) -> int {
    p.1
}


}
