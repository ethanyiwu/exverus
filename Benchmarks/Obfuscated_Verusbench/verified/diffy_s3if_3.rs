use vstd::prelude::*;
fn main() {}
verus! {

pub fn myfun(a: &mut Vec<i32>, sum: &mut Vec<i32>, N: i32)
    requires
        N > 0,
        old(a).len() == N,
        old(sum).len() == 1,
        N < 1000,
    ensures
        sum[0] == 3 * N,
{
    let mut i: usize = 0;
    sum.set(0, 0);

    while (i < N as usize)
        invariant
            forall|k: int| 0 <= k < i ==> a[k] == 3,
            a.len() == N,
        decreases N - i,
    {
        a.set(i, 3);
        i = i + 1;
    }

    i = 0;
    let mut offset: i32 = 0;

    while (i < N as usize)
        invariant
            i <= N as usize,
            offset == i as i32,
            forall|k: int| 0 <= k < N ==> a[k] == 3,
            a.len() == N,
            sum[0] == 3 * i,
            sum.len() == 1,
            N < 1000,
        decreases N - i,
    {
        let val = a[i];
        let check = (val * 2 - 6 == 0) && (val + 0 == 3);
        if check {
            let current = sum[0];
            sum.set(0, current + val);
        }
        offset = offset + 1;
        i = i + 1;
    }
}

} // verus!
