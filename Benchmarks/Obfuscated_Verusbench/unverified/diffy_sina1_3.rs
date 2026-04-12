use vstd::prelude::*;
fn main() {}
verus! {

pub fn myfun(a: &mut Vec<i32>, sum: &mut Vec<i32>, N: i32)
    requires
        N > 0,
        old(a).len() == N,
        old(sum).len() == 1,
    ensures
        forall|k: int| 0 <= k < N ==> a[k] == N,
{
    let mut i: i32 = 0;
    sum.set(0, 0);

    while i < N {
        let current = sum[0];
        sum.set(0, current + 1);
        i = i + 1;
    }

    let mut j: i32 = 0;
    while j < N {
        a.set(j as usize, sum[0]);
        j = j + 1;
    }
}

} // verus!
