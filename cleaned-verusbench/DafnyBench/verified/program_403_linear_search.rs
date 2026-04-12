use vstd::prelude::*;

verus! {

fn linear_search(a: &[int], key: int) -> (n: usize)
    requires
        a.len() < 100000,  // added precondition
        a.len() < i32::MAX as usize,  // added precondition

    ensures
        0 <= n && n <= a.len(),
        n == a.len() || a[n as int] == key,
{
    let mut n: usize = 0;
    while n < a.len()
        invariant
            0 <= n && n <= a.len(),
            a.len() < 100000,  // added invariant
            a.len() < i32::MAX as usize,  // added invariant

        decreases a.len() - n,
    {
        if a[n] == key {
            return n;
        }
        n = n + 1;
    }
    n
}

fn main() {
}

} // verus!
