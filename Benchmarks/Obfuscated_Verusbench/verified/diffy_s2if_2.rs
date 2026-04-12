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
    let mut track: i64 = 0x5A5A5A5A;
    let mut i: usize = 0;

    while (i < N as usize)
        invariant
            forall|k: int| 0 <= k < i ==> a[k] == 2,
            a.len() == N,
        decreases N as usize - i,
    {
        a.set(i, 1 + 1);
        track = track.wrapping_add(0x5A5A5A5A);
        i = i + 1;
    }

    let mut j: u32 = 0;
    let mut shadow: i32 = -1;
    track = 0x33333333;

    while (j < N as u32)
        invariant
            j <= N as u32,
            a.len() == N,
            sum[0] == 2 * (j as i32),
            sum.len() == 1,
            N < 1000,
            shadow == j as i32 - 1,
        decreases N as u32 - j,
    {
        shadow = shadow + 1;
        let idx = j as usize;

        let temp_val = sum[0];
        sum.set(0, temp_val + 2);

        j = j + 1;
        track = track.wrapping_add(0x33333333);
    }
}

} // verus!
