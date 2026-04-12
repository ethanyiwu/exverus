use vstd::prelude::*;
fn main() {}
verus! {

pub fn myfun(a: &mut Vec<i32>, b: &mut Vec<i32>, c: &mut Vec<i32>, sum: &mut Vec<i32>, N: i32)
    requires
        N > 0,
        old(a).len() == N,
        old(b).len() == N,
        old(c).len() == N,
        old(sum).len() == 1,
        N < 1000,
    ensures
        sum[0] <= 3 * N,
{
    let mut i: usize = 0;
    let mut track: i32 = 0;
    sum.set(0, 0);

    while i < N as usize
        invariant
            forall|j: int| 0 <= j < i ==> a[j] == 1,
            a.len() == N,
            track == i as i32,
        decreases N as usize - i,
    {
        a.set(i, 1);
        track = track + 1;
        i = i + 1;
    }

    i = 0;
    track = 0;
    while i < N as usize
        invariant
            forall|j: int| 0 <= j < i ==> b[j] == 1,
            b.len() == N,
            track == i as i32,
        decreases N as usize - i,
    {
        b.set(i, 1);
        track = track + 1;
        i = i + 1;
    }

    i = 0;
    track = 0;
    while i < N as usize
        invariant
            forall|j: int| 0 <= j < i ==> c[j] == 1,
            c.len() == N,
            track == i as i32,
        decreases N as usize - i,
    {
        c.set(i, 1);
        track = track + 1;
        i = i + 1;
    }

    i = 0;
    let mut phase: bool = true;
    while i < N as usize
        invariant
            i <= N as usize,
            sum.len() == 1,
            sum[0] == i,
            a.len() == N,
        decreases N as usize - i,
    {
        let temp = sum[0];
        sum.set(0, temp + 1);
        phase = !phase;
        i = i + 1;
    }

    i = 0;
    phase = true;
    while i < N as usize
        invariant
            i <= N as usize,
            sum.len() == 1,
            sum[0] == N + i,
            b.len() == N,
            N < 1000,
        decreases N as usize - i,
    {
        let temp = sum[0];
        sum.set(0, temp + 1);
        phase = !phase;
        i = i + 1;
    }

    i = 0;
    phase = true;
    while i < N as usize
        invariant
            i <= N as usize,
            sum.len() == 1,
            sum[0] == 2 * N + i,
            c.len() == N,
            N < 1000,
        decreases N as usize - i,
    {
        let temp = sum[0];
        sum.set(0, temp + 1);
        phase = !phase;
        i = i + 1;
    }
}

} // verus!
