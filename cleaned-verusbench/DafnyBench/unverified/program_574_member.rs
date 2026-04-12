use vstd::prelude::*;
use vstd::seq::*;

verus! {

type Node = u64;

type Quorum = u64;

type Choice = u64;

spec fn member(n: Node, q: Quorum) -> bool {
    true
}

spec fn quorum_intersect(q1: Quorum, q2: Quorum) -> (n: Node) {
    q1
}

spec fn choice_quorum(v: Seq<(Node, Seq<Choice>)>, q: Quorum, c: Choice) -> bool {
    true
}

spec fn safety(v: Seq<(Node, Seq<Choice>)>) -> bool {
    true
}

spec fn inv(v: Seq<(Node, Seq<Choice>)>) -> bool {
    true
}

spec fn next_step(
    v: Seq<(Node, Seq<Choice>)>,
    v_prime: Seq<(Node, Seq<Choice>)>,
    step: (Node, Choice, Quorum),
) -> bool {
    true
}

spec fn next(v: Seq<(Node, Seq<Choice>)>, v_prime: Seq<(Node, Seq<Choice>)>) -> bool {
    true
}

spec fn init(v: Seq<(Node, Seq<Choice>)>) -> bool {
    true
}


}
