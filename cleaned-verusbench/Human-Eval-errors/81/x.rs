use vstd::arithmetic::mul::*;
use vstd::prelude::*;

verus! {

// specification
pub closed spec fn factorial(n: nat) -> nat
    decreases n,
{
    if n <= 1 {
        1
    } else {
        n * factorial((n - 1) as nat)
    }
}

pub closed spec fn brazilian_factorial(n: nat) -> nat
    decreases n,
{
    if n <= 1 {
        factorial(1)
    } else {
        factorial(n) * brazilian_factorial((n - 1) as nat)
    }
}

proof fn lemma_factorial_positive(n: nat)
    ensures
        factorial(n) >= 1,
    decreases n,
{
fn main () {}
