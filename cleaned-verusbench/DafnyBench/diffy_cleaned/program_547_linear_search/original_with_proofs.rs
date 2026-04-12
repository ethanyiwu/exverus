use vstd::prelude::*;

verus! {

/// Searches for an element in an array using a loop.
fn linear_search(a: &[int], key: int) -> (n: usize)
    requires
        a.len() > 0,
        a.len() < usize::MAX,
    ensures
        0 <= n && n <= a.len(),
        n == a.len() || a[n as int] == key,
{
    let mut n: usize = 0;
    while n < a.len()
        invariant
            0 <= n && n <= a.len(),
            a.len() > 0,
            a.len() < usize::MAX,
        decreases a.len() - n,
    {
        if a[n] == key {
            return n;
        }
        n = n + 1;
    }
    a.len()
}

fn main() {}

} // verus!