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
    while n != a.len() {
        let current = a[n];
        let cond1 = current == e;
        let cond2 = !(current != e);
        let final_cond = cond1 && cond2;

        if final_cond {
            return n;
        }
        n = n + 1;
    }
    n
}

} // verus!
