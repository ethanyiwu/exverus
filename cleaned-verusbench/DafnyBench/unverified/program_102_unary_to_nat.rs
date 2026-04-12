use vstd::prelude::*;

verus! {

# [doc = " Specification function for unary numbers"]
spec fn unary_to_nat(x: int) -> int {
    x
}

# [doc = " Specification function for binary numbers"]
spec fn binary_to_nat(x: int) -> int {
    x
}

# [doc = " Function to convert unary to binary"]
fn unary_to_binary(x: int) -> (y: int)
    ensures
        binary_to_nat(y) == unary_to_nat(x),
{
    x
}

# [doc = " Function to convert binary to unary"]
fn binary_to_unary(x: int) -> (y: int)
    ensures
        unary_to_nat(y) == binary_to_nat(x),
{
    x
}

# [doc = " Function to add two unary numbers"]
fn add_unary(x: int, y: int) -> (z: int)
    ensures
        unary_to_nat(z) == unary_to_nat(x) + unary_to_nat(y),
{
    x + y
}

# [doc = " Function to multiply two unary numbers"]
fn mul_unary(x: int, y: int) -> (z: int)
    ensures
        unary_to_nat(z) == unary_to_nat(x) * unary_to_nat(y),
{
    x * y
}

# [doc = " Function to subtract two unary numbers"]
fn sub_unary(x: int, y: int) -> (z: int)
    ensures
        unary_to_nat(z) == unary_to_nat(x) - unary_to_nat(y),
{
    x - y
}

# [doc = " Function to divide two unary numbers"]
fn div_unary(x: int, y: int) -> (z: int)
    ensures
        unary_to_nat(z) == unary_to_nat(x) / unary_to_nat(y),
{
    x / y
}


}
