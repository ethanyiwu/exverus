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
    let mut phase: u8 = 0;
    let mut shadow: i32 = 0;

    while n < a.len()
        invariant
            forall|i: int| (0 <= i < n as int) ==> e != a[i],
        decreases a.len() - n,
    {
        if phase == 0 {
            if !(a[n] != e) {
                return n;
            }
            shadow = shadow ^ a[n];
            n = n + 1;
            phase = 1;
        } else {
            if !(a[n] != e) {
                return n;
            }
            shadow = shadow ^ a[n];
            n = n + 1;
            phase = 0;
        }
        shadow = 0;
    }
    n
}

} // verus!
