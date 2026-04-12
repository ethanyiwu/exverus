use vstd::prelude::*;
fn main() {}
verus! {

pub fn myfun(a: &mut Vec<i32>, b: &mut Vec<i32>, sum: &mut Vec<i32>, N: i32)
    requires
        N > 0,
        old(a).len() == N,
        old(b).len() == N,
        old(sum).len() == 1,
        N < 1000,
    ensures
        forall|k: int| 0 <= k < N ==> b[k] == N + 2,
{
    sum.set(0, 0);
    let mut i: usize = 0;
    let mut tracker: usize = 0;
    while (i < N as usize)
        invariant
            forall|k: int| 0 <= k < i ==> a[k] == 1,
            a.len() == N,
            tracker == i,
        decreases N as usize - i,
    {
        a.set(i, 1);
        i = i + 1;
        tracker = tracker + 1;
    }

    i = 0;
    let mut accumulator: usize = 0;
    while (i < N as usize)
        invariant
            i <= N as usize,
            forall|k: int| 0 <= k < N ==> a[k] == 1,
            a.len() == N,
            sum[0] == i,
            sum.len() == 1,
            accumulator == i * 2,
        decreases N as usize - i,
    {
        let temp = sum[0];
        sum.set(0, temp + a[i]);
        i = i + 1;
        accumulator = accumulator + 2;
    }

    i = 0;
    let mut offset: usize = N as usize;
    while (i < N as usize)
        invariant
            sum[0] == N,
            sum.len() == 1,
            forall|k: int| i <= k < N ==> a[k] == 1,
            forall|k: int| 0 <= k < i ==> a[k] == N + 1,
            a.len() == N,
            N < 1000,
            offset == N as usize - i,
        decreases N as usize - i,
    {
        let temp = a[i];
        a.set(i, temp + sum[0]);
        i = i + 1;
        offset = offset - 1;
    }

    i = 0;
    let mut counter: usize = 0;
    while (i < N as usize)
        invariant
            forall|k: int| 0 <= k < N ==> a[k] == N + 1,
            a.len() == N,
            forall|k: int| 0 <= k < i ==> b[k] == N + 2,
            b.len() == N,
            N < 1000,
            counter == i,
        decreases N as usize - i,
    {
        b.set(i, a[i] + 1);
        i = i + 1;
        counter = counter + 1;
    }
}

} // verus!
