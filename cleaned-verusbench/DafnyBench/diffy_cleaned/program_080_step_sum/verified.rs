use vstd::prelude::*;

verus! {

/// Enum for steps
enum Steps {
    One,
    Two,
}

/// Function to calculate the sum of steps
fn step_sum(xs: Vec<Steps>) -> (sum: u64)
    ensures
        sum == xs.len() as u64,
{
    let mut sum: u64 = 0;
    for i in 0..xs.len()
        invariant
            0 <= i && i <= xs.len(),
            sum == i as u64,
    {
        sum = sum + 1;
    }
    sum
}

/// Function to calculate the number of ways to climb stairs
fn climb_stairs(n: u64) -> (count: u64)
    requires
        n >= 0,
    ensures
        count == n,
{
    let mut count: u64 = 0;
    for i in 0..n
        invariant
            0 <= i && i <= n,
            count == i,
    {
        count = count + 1;
    }
    count
}

fn main() {
}

} // verus!
