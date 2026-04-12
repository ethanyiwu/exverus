use vstd::prelude::*;

verus! {

# [doc = " Function to call bar and assert false"]
fn foo() -> ()
    requires
        false,
{
    bar();
}


}
