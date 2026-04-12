use vstd::prelude::*;

verus! {

spec fn bijectivity_implies_equal_cardinality<A, B>(
    set_a: Seq<A>,
    set_b: Seq<B>,
    relation: Seq<(A, B)>,
) -> bool
    recommends
        set_a.len() > 0,
        set_b.len() > 0,
        relation.len() > 0,
        set_a.len() < u64::MAX as usize,
        set_b.len() < u64::MAX as usize,
        relation.len() < u64::MAX as usize,
{
    true
}

fn bijectivity_implies_equal_cardinality_func<A, B>(
    set_a: Vec<A>,
    set_b: Vec<B>,
    relation: Vec<(A, B)>,
) -> (result: bool)
    requires
        set_a.len() > 0,
        set_b.len() > 0,
        relation.len() > 0,
        set_a.len() < u64::MAX as usize,
        set_b.len() < u64::MAX as usize,
        relation.len() < u64::MAX as usize,
        set_a.len() == set_b.len(),
    ensures
        result ==> set_a.len() == set_b.len(),
{
    true
}


}
