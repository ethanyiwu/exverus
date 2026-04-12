use vstd::prelude::*;

verus! {

fn is_prime(num: u32) -> (result: bool)
    requires
        num >= 2,
    ensures
        result <==> spec_prime(num as int),
{
    let mut i = 2;
    let mut result = true;
    while i < num
    {
        if num % i == 0 {
            result = false;
        }
        i += 1;
    }
    result
}

fn largest_prime_factor(n: u32) -> (largest: u32)
    requires
        n >= 2,
    ensures
        1 <= largest <= n,
        spec_prime(largest as int),
{
    let mut largest = 1;
    let mut j = 1;
    while j < n
    {
        j += 1;
        let flag = is_prime(j);
        if n % j == 0 && flag {
            largest =
            if largest > j {
                largest
            } else {
                j
            };
        }
    }
    largest
}

}
fn main() {}
