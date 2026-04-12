use vstd::prelude::*;

verus! {

/// Function to assert false
fn bar() -> ()
    requires
        false,  // equivalent to ensures false in Dafny
{
    assert(false);
}

/// Function to call bar and assert false
fn foo() -> ()
    requires
        false,  // equivalent to ensures false in Dafny
{
    bar();
    assert(false);
}

fn main() {
}

} // verus!
