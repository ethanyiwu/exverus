use vstd::prelude::*;

verus! {

struct Variables {
    value: int,
}

spec fn init(v: Variables) -> bool {
    v.value == 0
}

spec fn increment_op(v: Variables, v_prime: Variables) -> bool {
    v_prime.value == v.value + 1
}

spec fn decrement_op(v: Variables, v_prime: Variables) -> bool {
    v_prime.value == v.value - 1
}

enum Step {
    Increment,
    Decrement,
}

spec fn next_step(v: Variables, v_prime: Variables, step: Step) -> bool {
    match step {
        Step::Increment => increment_op(v, v_prime),
        Step::Decrement => decrement_op(v, v_prime),
    }
}

spec fn next(v: Variables, v_prime: Variables) -> bool {
    exists|step: Step| next_step(v, v_prime, step)
}

spec fn abstraction(v: Variables) -> Variables {
    Variables { value: v.value }
}


}
