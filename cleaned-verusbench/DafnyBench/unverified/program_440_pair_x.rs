use vstd::prelude::*;

verus! {

# [doc = " A pair of integers"]
struct Pair {
    x: int,
    y: int,
}

# [doc = " Extracts the first element of a pair"]
spec fn pair_x(p: Pair) -> int {
    p.x
}

# [doc = " Extracts the second element of a pair"]
spec fn pair_y(p: Pair) -> int {
    p.y
}

# [doc = " Creates a new pair from two integers"]
spec fn pair(x: int, y: int) -> Pair {
    Pair { x, y }
}


}
