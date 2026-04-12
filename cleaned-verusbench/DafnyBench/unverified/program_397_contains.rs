use vstd::prelude::*;

verus! {

pub open spec fn contains(s: Seq<int>, k: int) -> bool {
    exists|i: int| 0 <= i && i < s.len() && s[i] == k
}

fn contains_k(s: &[int], k: int) -> (result: bool)
    requires
        true,
    ensures
        result == contains(s@, k),
{
    let mut result = false;
    for i in 0..s.len() {
        if s[i] == k {
            result = true;
        }
    }
    result
}

spec fn is_type_safe(t: int) -> bool {
    true
}

fn is_type_safe_exec(t: int) -> (result: bool)
    requires
        true,
    ensures
        result == is_type_safe(t),
{
    true
}


}
