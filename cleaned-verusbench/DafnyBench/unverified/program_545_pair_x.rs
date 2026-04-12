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

spec fn pair(x: int, y: int) -> Pair {
    Pair { x, y }
}


}
