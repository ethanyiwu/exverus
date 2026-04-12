use vstd::prelude::*;

verus! {

fn bar() -> (result: bool)
    requires
        false,
    ensures
        !result,
{
    false
}

fn foo() -> (result: bool)
    requires
        false,
    ensures
        !result,
{
    bar();
    false
}


}
