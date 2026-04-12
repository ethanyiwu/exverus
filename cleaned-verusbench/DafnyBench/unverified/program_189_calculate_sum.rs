use vstd::prelude::*;

verus! {

fn calculate_sum(a: int, b: int) -> (result: int)
    ensures
        result == a + b,
{
    a + b
}


}
