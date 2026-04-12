use vstd::prelude::*;

verus! {

fn f(x: int, y: int) -> (result: int)
    requires
        true,
    ensures
        result == x + y,
{
    x + y
}


}
