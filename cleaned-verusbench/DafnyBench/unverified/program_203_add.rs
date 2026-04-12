use vstd::prelude::*;

verus! {

fn add(a: int, b: int) -> (result: int)
    ensures
        result == a + b,
{
    a + b
}


}
