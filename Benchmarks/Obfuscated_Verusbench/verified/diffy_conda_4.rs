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
    let mut shadow: i32 = 0;

    while (i < N as usize)
        invariant
            forall|k: int| 0 <= k < i ==> a[k] == 1,
            a.len() == N,
            shadow == i as i32,
        decreases N - i,
    {
        a.set(i, 1);
        shadow = shadow + 1;
        i = i + 1;
    }

    i = 0;
    let mut toggle: bool = true;
    while (i < N as usize)
        invariant
            forall|k: int| 0 <= k < i ==> a[k] == 2,
            forall|k: int| i <= k < N ==> a[k] == 1,
            a.len() == N,
        decreases N - i,
    {
        let current = a[i];
        a.set(i, current + (2 - current));
        toggle = !toggle;
        i = i + 1;
    }

    i = 0;
    let mut acc: i32 = 0;
    while (i < N as usize)
        invariant
            i <= N,
            forall|k: int| 0 <= k < N ==> a[k] == 2,
            sum[0] == 2 * i,
            sum.len() == 1,
            a.len() == N,
            N < 1000,
            acc == i as i32,
        decreases N - i,
    {
        let temp = sum[0];
        sum.set(0, temp + a[i]);
        acc = acc + 1;
        i = i + 1;
    }
}

} // verus!
