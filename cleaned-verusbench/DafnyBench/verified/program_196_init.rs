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

struct VariablesProtocol {
    value: int,
}

spec fn init_protocol(v: VariablesProtocol) -> bool {
    v.value == 0
}

spec fn increment_op_protocol(v: VariablesProtocol, v_prime: VariablesProtocol) -> bool {
    v_prime.value == v.value - 1
}

spec fn decrement_op_protocol(v: VariablesProtocol, v_prime: VariablesProtocol) -> bool {
    v_prime.value == v.value + 1
}

enum StepProtocol {
    Increment,
    Decrement,
}

spec fn next_step_protocol(
    v: VariablesProtocol,
    v_prime: VariablesProtocol,
    step: StepProtocol,
) -> bool {
    match step {
        StepProtocol::Increment => increment_op_protocol(v, v_prime),
        StepProtocol::Decrement => decrement_op_protocol(v, v_prime),
    }
}

spec fn next_protocol(v: VariablesProtocol, v_prime: VariablesProtocol) -> bool {
    exists|step: StepProtocol| next_step_protocol(v, v_prime, step)
}

spec fn abstraction(v: VariablesProtocol) -> Variables {
    Variables { value: v.value }
}

proof fn refinement_init(v: VariablesProtocol)
    requires
        init_protocol(v),
    ensures
        init(abstraction(v)),
{
    assert(true);
}

proof fn refinement_next(v: VariablesProtocol, v_prime: VariablesProtocol)
    requires
        next_protocol(v, v_prime),
    ensures
        next(abstraction(v), abstraction(v_prime)),
{
    assert(abstraction(v_prime).value == abstraction(v).value + 1 || abstraction(v_prime).value
        == abstraction(v).value - 1);
    assert(exists|step: Step| next_step(abstraction(v), abstraction(v_prime), step)) by {
        if abstraction(v_prime).value == abstraction(v).value + 1 {
            assert(next_step(abstraction(v), abstraction(v_prime), Step::Increment));
        } else {
            assert(next_step(abstraction(v), abstraction(v_prime), Step::Decrement));
        }
    }
    assert(next(abstraction(v), abstraction(v_prime)));
}

fn main() {
}

} // verus!
