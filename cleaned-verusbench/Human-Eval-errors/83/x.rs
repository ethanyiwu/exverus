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
    if (n == 0) {
    } else {
        lemma_factorial_positive((n - 1) as nat);
        assert(factorial(n) >= 1) by {
            broadcast use lemma_mul_strictly_positive;

        };
    }
}

proof fn lemma_brazilian_factorial_positive(n: nat)
    ensures
        brazilian_factorial(n) >= 1,
    decreases n,
{
    if (n == 0) {
    } else {
        lemma_factorial_positive((n) as nat);
        lemma_brazilian_factorial_positive((n - 1) as nat);
        assert(brazilian_factorial(n) >= 1) by {
            lemma_mul_strictly_positive(
                factorial(n) as int,
                brazilian_factorial((n - 1) as nat) as int,
            )
        };
    }
}

proof fn lemma_brazilian_fib_monotonic(i: nat, j: nat)
    requires
        0 <= i <= j,
    ensures
        brazilian_factorial(i) <= brazilian_factorial(j),
    decreases j - i,
{
fn main () {}
