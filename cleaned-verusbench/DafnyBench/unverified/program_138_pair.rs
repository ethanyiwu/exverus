use vstd::prelude::*;

verus! {

spec fn pair(x: int, y: int) -> (pair: (int, int)) {
    (x, y)
}

spec fn pair_x(pair: (int, int)) -> int {
    pair.0
}

spec fn pair_y(pair: (int, int)) -> int {
    pair.1
}


}
