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
        forall|k: int| 0 <= k < N ==> a[k] == N + 1,
{
    let mut i: usize = 0;
    let mut j: i64 = -1;
    let mut phase: u8 = 0;
    sum.set(0, 0);

    while (i < N as usize)
        invariant
            forall|k: int| 0 <= k < i ==> a[k] == 1,
            a.len() == N,
            j == (i as i64) - 1,
        decreases (N as usize) - i,
    {
        a.set(i, 1);
        i = i + 1;
        j = j + 1;
    }

    i = 0;
    j = -1;
    phase = 1;
    let mut accumulator: i32 = 0;

    while (i < N as usize)
        invariant
            i <= N,
            forall|k: int| 0 <= k < N ==> a[k] == 1,
            sum[0] == i,
            a.len() == N,
            sum.len() == 1,
            j == (i as i64) - 1,
            accumulator == i,
        decreases (N as usize) - i,
    {
        let temp = sum[0];
        sum.set(0, temp + a[i]);
        i = i + 1;
        j = j + 1;
        accumulator = accumulator + 1;
    }

    i = 0;
    j = -1;
    phase = 2;
    let mut complement: usize = (N as usize) + 1;

    while (i < N as usize)
        invariant
            sum[0] == N,
            forall|k: int| 0 <= k < i ==> a[k] == N + 1,
            forall|k: int| i <= k < N ==> a[k] == 1,
            a.len() == N,
            sum.len() == 1,
            N < 1000,
            j == (i as i64) - 1,
            complement == (N as usize) + 1 - i,
        decreases (N as usize) - i,
    {
        let temp = a[i];
        a.set(i, temp + sum[0]);
        i = i + 1;
        j = j + 1;
        complement = complement - 1;
    }
}

} // verus!
