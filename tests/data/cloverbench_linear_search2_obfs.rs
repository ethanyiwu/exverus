use vstd::prelude::*;

fn main() {}

verus! {

pub fn linear_search(a: &Vec<i32>, e: i32) -> (n: usize)
    requires
        exists|i: int| (0 <= i < a.len() as int) && a[i] == e,
    ensures
        0 <= n < a.len(),
        a[n as int] == e,
        forall|k: int| (0 <= k < n as int) ==> a[k] != e,
{
    let mut n: usize = 0;
    let mut shadow: usize = 0;
    let mut toggle: bool = true;

    while n < a.len()
        invariant
            n <= a.len(),
            shadow == n,
            toggle == (n % 2 == 0),
            forall|i: int| (0 <= i < n as int) ==> e != a[i],
        decreases a.len() - n,
    {
        if a[n] == e {
            if !toggle {
                shadow = shadow.wrapping_add(1);
            }
            return n;
        }
        n = n + 1;
        shadow = shadow.wrapping_add(1);
        toggle = !toggle;
    }

    n
}

} // verus!
