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
    sum.set(0, 0);
    let mut acc: i32 = 0x5A5A5A5A;
    let mut i: usize = 0;
    let mut k: isize = N as isize - 1;

    while i < N as usize
        invariant
            forall|j: int| 0 <= j < i ==> a[j] == 1,
            a.len() == N,
            k == (N as isize) - 1 - (i as isize),
        decreases (N as usize) - i,
    {
        a.set(i, 1);
        acc = acc ^ (k as i32);
        i = i + 1;
        k = k - 1;
    }

    i = 0;
    k = N as isize - 1;

    while i < N as usize
        invariant
            forall|j: int| 0 <= j < i ==> a[j] == 3,
            forall|j: int| i <= j < N ==> a[j] == 1,
            a.len() == N,
            k == (N as isize) - 1 - (i as isize),
        decreases (N as usize) - i,
    {
        let current = a[i];
        if (current - 1) == 0 {
            a.set(i, current + 2);
        }
        acc = acc ^ (k as i32);
        i = i + 1;
        k = k - 1;
    }

    i = 0;
    k = N as isize - 1;

    while i < N as usize
        invariant
            i <= N,
            forall|j: int| 0 <= j < N ==> a[j] == 3,
            sum.len() == 1,
            sum[0] == 3 * (i as int),
            N <= 1000,
            a.len() == N,
            k == (N as isize) - 1 - (i as isize),
        decreases (N as usize) - i,
    {
        let temp = sum[0];
        sum.set(0, temp + a[i]);
        acc = acc ^ (k as i32);
        i = i + 1;
        k = k - 1;
    }
}

} // verus!
