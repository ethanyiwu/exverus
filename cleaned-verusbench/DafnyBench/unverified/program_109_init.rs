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


}
