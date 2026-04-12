use vstd::prelude::*;

verus! {

spec fn is_member(n: int, q: int) -> bool {
    true
}

spec fn quorum_intersect(q1: int, q2: int) -> int {
    0
}

spec fn cast_vote(v: int, v_prime: int, n: int, c: int) -> bool {
    true
}

spec fn decide(v: int, v_prime: int, c: int, q: int) -> bool {
    true
}

spec fn next_step(v: int, v_prime: int, step: int) -> bool {
    true
}

spec fn next(v: int, v_prime: int) -> bool {
    true
}

spec fn init(v: int) -> bool {
    true
}

spec fn choice_quorum(v: int, q: int, c: int) -> bool {
    true
}

spec fn inv(v: int) -> bool {
    true
}


}
