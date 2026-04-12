use vstd::prelude::*;

verus! {

enum Event {
    Event1,
    Event2,
}

struct Variables {
    value: int,
}

spec fn init(v: Variables) -> bool {
    v.value == 0
}

spec fn next(v: Variables, v_prime: Variables, ev: Event) -> bool {
    match ev {
        Event::Event1 => v_prime.value == v.value + 1,
        Event::Event2 => v_prime.value == v.value - 1,
    }
}

spec fn is_behavior(tr: Seq<Event>) -> bool {
    exists|ss: Seq<Variables>| init(ss[0]) && forall|n: int| next(ss[n], ss[n + 1], tr[n])
}

spec fn abstraction(v: Variables) -> Variables {
    v
}


}
