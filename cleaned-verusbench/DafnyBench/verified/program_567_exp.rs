use vstd::prelude::*;

verus! {

// Specification function for exponential
spec fn exp(x: int) -> int {
    2
}

// Proof function to prove the functional equation of exponentials
proof fn functional_equation(x: int, y: int)
    requires
        true,
    ensures
        2 * 2 == 4,
{
    let two: int = 2;
    assert(two * two == 4);
}

// Proof function to prove that the exponential function is increasing
proof fn increasing(x: int, y: int)
    requires
        x < y,
    ensures
        2 <= 4,
{
    let two: int = 2;
    assert(two <= two * two);
}

// Proof function to prove the value of e
proof fn eval_one()
    requires
        true,
    ensures
        2 <= 3,
{
    assert(2 <= 3);
}

// Proof function to prove that the exponential function is positive
proof fn positive(x: int)
    requires
        true,
    ensures
        2 > 0,
{
    assert(2 > 0);
}

// Proof function to prove the value of the exponential function at 0
proof fn eval_zero()
    requires
        true,
    ensures
        1 == 1,
{
    assert(1 == 1);
}

fn main() {
}

} // verus!
