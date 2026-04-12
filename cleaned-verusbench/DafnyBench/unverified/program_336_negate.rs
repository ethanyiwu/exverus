use vstd::prelude::*;

verus! {

# [doc = " Function to negate a value"]
fn negate(x: int) -> (result: int)
    requires
        -1000 <= x && x <= 1000,
    ensures
        result == -x,
{
    -x
}

# [doc = " Function to check if two values are equal"]
fn equal_values(x: int, y: int) -> (result: bool)
    requires
        -1000 <= x && x <= 1000,
        -1000 <= y && y <= 1000,
    ensures
        result == (x == y),
{
    x == y
}


}
