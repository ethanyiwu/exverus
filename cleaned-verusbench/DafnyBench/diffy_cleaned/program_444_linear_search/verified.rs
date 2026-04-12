use vstd::prelude::*;

verus! {

fn linear_search(a: &Vec<i32>, key: i32) -> (n: usize)
    requires
        a.len() > 0,
    ensures
        n <= a.len(),
        n == a.len() || a[n as int] == key,
{
    let mut n: usize = 0;
    while n < a.len()
        invariant
            n <= a.len(),
            a.len() > 0,
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
