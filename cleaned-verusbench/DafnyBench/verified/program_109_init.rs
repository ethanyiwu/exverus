use vstd::prelude::*;

verus! {

struct CodeVariables {
    value: int,
}

struct SpecVariables {
    value: int,
}

struct Event {
    value: int,
}

spec fn init(v: CodeVariables) -> bool {
    v.value == 0
}

spec fn next(v: CodeVariables, v_prime: CodeVariables, ev: Event) -> bool {
    v_prime.value == v.value + ev.value
}

spec fn abstraction(v: CodeVariables) -> SpecVariables {
    SpecVariables { value: v.value }
}

proof fn abstraction_init(v: CodeVariables)
    requires
        init(v),
    ensures
        abstraction(v).value == 0,
{
    assert(abstraction(v).value == v.value);
    assert(v.value == 0);
    assert(abstraction(v).value == 0);
}

proof fn abstraction_inductive(v: CodeVariables, v_prime: CodeVariables, ev: Event)
    requires
        v_prime.value == v.value + ev.value,
    ensures
        abstraction(v_prime).value == abstraction(v).value + ev.value,
{
    assert(abstraction(v_prime).value == v_prime.value);
    assert(abstraction(v).value == v.value);
    assert(abstraction(v_prime).value == abstraction(v).value + ev.value);
}

fn main() {
}

} // verus!
