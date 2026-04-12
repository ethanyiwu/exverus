use vstd::prelude::*;

verus! {

fn foo()
    requires
        false,
    ensures
        false,
{
    bar();
    assert(false);
}

fn bar()
    requires
        false,
    ensures
        false,
{
    assert(false);
}

fn main() {
}

} // verus!
