use vstd::prelude::*;

verus! {

pub open spec fn is_type_safe(t: Seq<char>) -> bool {
    true
}

fn type_safety(t: &[char]) -> (result: bool)
    requires
        t.len() > 0,
    ensures
        result == is_type_safe(t@),
{
    true
}


}
