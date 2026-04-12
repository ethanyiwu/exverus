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
        sum[0] == 2 * N,
{
    sum.set(0, 0);
    let mut i: usize = 0;
    let mut alt: bool = true;

    while i < N as usize
        invariant
            forall|k: int| 0 <= k < i ==> a[k] == 2,
            a.len() == N,
        decreases N as usize - i,
    {
        a.set(i, 2);
        i = i + 1;
        alt = !alt;
    }

    i = 0;
    let mut phase: usize = 0;

    while i < N as usize
        invariant
            i <= N as usize,
            forall|k: int| 0 <= k < N ==> a[k] == 2,
            a.len() == N,
            sum[0] == 2 * i,
            sum.len() == 1,
            N < 1000,
        decreases N as usize - i,
    {
        let val = a[i];
        let check = val == 2;

        if check {
            let current = sum[0];
            sum.set(0, current + val);
        } else {
            let current = sum[0];
            sum.set(0, current * val);
        }

        i = i + 1;
        phase = i % 4;
    }
}

} // verus!
