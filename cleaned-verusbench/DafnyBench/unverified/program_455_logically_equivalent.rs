use vstd::prelude::*;

verus! {

# [doc = " Function to check if two predicates are logically equivalent"]
fn logically_equivalent(a: bool, b: bool) -> (equivalent: bool)
    requires
        true,
    ensures
        equivalent ==> (a ==> b && b ==> a),
{
    let equivalent = a == b;
    equivalent
}

# [doc = " Function to check if a predicate is always true"]
fn always_true(a: bool) -> (always_true: bool)
    requires
        true,
    ensures
        always_true ==> a,
{
    let always_true = a;
    always_true
}

# [doc = " Function to check if two predicates are logically equivalent"]
fn logically_equivalent_old(a: bool, b: bool) -> (equivalent: bool)
    requires
        true,
    ensures
        equivalent ==> (a ==> b && b ==> a),
{
    let equivalent = a == b;
    equivalent
}

# [doc = " Function to check if a predicate is always true"]
fn always_true_old(a: bool) -> (always_true: bool)
    requires
        true,
    ensures
        always_true ==> a,
{
    let always_true = a;
    always_true
}


}
