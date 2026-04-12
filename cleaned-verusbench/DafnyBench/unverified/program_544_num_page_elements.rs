use vstd::prelude::*;

verus! {

# [doc = " Specification function"]
spec fn num_page_elements() -> nat {
    11
}

# [doc = " Proof function"]
fn num_page_elements_func() -> (result: bool)
    requires
        true,
    ensures
        result == (num_page_elements() == 11),
{
    let mut result = true;
    result
}

# [doc = " Specification function"]
spec fn num_halign() -> nat {
    3
}

# [doc = " Proof function"]
fn num_halign_func() -> (result: bool)
    requires
        true,
    ensures
        result == (num_halign() == 3),
{
    let mut result = true;
    result
}

# [doc = " Specification function"]
spec fn subset_cardinality<T>(a: Set<T>, b: Set<T>) -> bool
    recommends
        a <= b,
{
    true
}

# [doc = " Proof function"]
fn subset_cardinality_func<T>(a: Set<T>, b: Set<T>) -> (result: bool)
    requires
        a <= b,
    ensures
        result == subset_cardinality(a, b),
{
    let mut result = true;
    result
}


}
