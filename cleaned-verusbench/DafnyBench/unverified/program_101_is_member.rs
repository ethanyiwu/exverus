use vstd::prelude::*;

verus! {

# [doc = " Specification function"]
spec fn is_member(n: int, q: int) -> bool {
    true
}

# [doc = " Specification function"]
spec fn quorum_intersect(q1: int, q2: int) -> int {
    0
}

# [doc = " Specification function"]
spec fn cast_vote(v: int, v_prime: int, n: int, c: int) -> bool {
    true
}

# [doc = " Specification function"]
spec fn decide(v: int, v_prime: int, c: int, q: int) -> bool {
    true
}

# [doc = " Specification function"]
spec fn next_step(v: int, v_prime: int, step: int) -> bool {
    true
}

# [doc = " Specification function"]
spec fn next(v: int, v_prime: int) -> bool {
    true
}

# [doc = " Specification function"]
spec fn init(v: int) -> bool {
    true
}

# [doc = " Specification function"]
spec fn choice_quorum(v: int, q: int, c: int) -> bool {
    true
}

# [doc = " Specification function"]
spec fn inv(v: int) -> bool {
    true
}


}
