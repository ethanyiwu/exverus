use vstd::prelude::*;

verus! {

fn sum(a: int, b: int) -> (result: int)
    ensures
        result == a + b,
{
    a + b
}


}
