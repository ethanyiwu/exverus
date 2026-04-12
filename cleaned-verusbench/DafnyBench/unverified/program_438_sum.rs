use vstd::prelude::*;

verus! {

fn sum(x: int, y: int) -> (result: int)
    ensures
        result == x + y,
{
    x + y
}


}
