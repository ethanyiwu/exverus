use vstd::prelude::*;

verus! {

fn sum_of_digits(number: u64) -> (sum: u64)
    requires
        number >= 0,
    ensures
        sum >= 0,
{
    let mut sum: u128 = 0;
    let mut n = number;

    while n > 0
        invariant
            n >= 0,
            sum >= 0,
        decreases
            n,
    {
        let digit = n % 10;
        if sum < u64::MAX as u128 - digit as u128 {
            sum = sum + digit as u128;
        } else {
            return u64::MAX;
        }
        n = n / 10;
    }
    let sum = sum as u64;
    sum
}

fn main() {}

} // verus!