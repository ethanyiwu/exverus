use vstd::prelude::*;

verus! {

# [doc = " Specification function to create a pair"]
spec fn pair(x: int, y: int) -> (pair: (int, int)) {
    (x, y)
}

# [doc = " Specification function to get the x-coordinate of a pair"]
spec fn pair_x(pair: (int, int)) -> int {
    pair.0
}

# [doc = " Specification function to get the y-coordinate of a pair"]
spec fn pair_y(pair: (int, int)) -> int {
    pair.1
}


}
