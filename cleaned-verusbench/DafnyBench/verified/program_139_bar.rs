use vstd::prelude::*;

verus! {

// Function that always returns false
fn bar() -> (result: bool)
    requires
        false,
    ensures
        !result,
{
    assert(false);
    false
}

// Function that calls bar and asserts false
fn foo() -> (result: bool)
    requires
        false,
    ensures
        !result,
{
    bar();
    assert(false);
    false
}

fn main() {
}

} // verus!
