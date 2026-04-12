use vstd::prelude::*;

verus! {

fn bar()
    requires
        false,
    ensures
        false,
{
    assert(false);
}

fn foo()
    requires
        false,
    ensures
        false,
{
    bar();
    assert(false);
}

fn main() {
}

} // verus!
