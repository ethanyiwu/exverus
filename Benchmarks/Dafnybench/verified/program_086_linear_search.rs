use vstd::prelude::*;

verus! {

/// Searches for an element in an array
fn linear_search(a: &Vec<i32>, key: i32) -> (n: usize)
    requires
        a.len() > 0,
        a.len() < i32::MAX as usize,  // added relaxation to prevent overflow

    ensures
        n <= a.len(),
        n == a.len() || a[n as int] == key,
{
    let mut n = 0;
    while n < a.len()
        invariant

        decreases a.len() - n,
    {
        if a[n] == key {
            return n;
        }
        n = n + 1;
    }
    a.len()
}

fn main() {
}

} // verus!
