use vstd::prelude::*;

verus! {

fn foo()
    requires
        false,
    ensures
        false,
{
    bar();
}


}
