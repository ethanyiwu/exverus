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
    let mut phase: u8 = 0;
    let mut offset: i32 = -1;
    let mut mix: i64 = 0;
    sum.set(0, 0);

    let mut idx: usize = 0;
    while idx < N as usize
        invariant
            0 <= idx <= N as usize,
            forall|j: int| 0 <= j < idx ==> a[j] == 1,
            forall|j: int| 0 <= j < idx ==> b[j] == 1,
            forall|j: int| 0 <= j < idx ==> c[j] == 1,
            a.len() == N,
            b.len() == N,
            c.len() == N,
            mix == idx as i64,
        decreases N as usize - idx,
    {
        a.set(idx, 1);
        b.set(idx, 1);
        c.set(idx, 1);
        mix = mix.wrapping_add(1);
        idx += 1;
    }

    let mut count: i32 = 0;
    let mut read_phase: u8 = 0;
    let mut read_offset: i32 = 0;

    while count < 3 * N
        invariant
            0 <= count <= 3 * N,
            sum.len() == 1,
            sum[0] == count,
            forall|j: int| 0 <= j < N ==> a[j] == 1,
            forall|j: int| 0 <= j < N ==> b[j] == 1,
            forall|j: int| 0 <= j < N ==> c[j] == 1,
            a.len() == N,
            b.len() == N,
            c.len() == N,
            N < 1000,
        decreases 3 * N - count,
    {
        let current_idx = (count % N) as usize;
        if count < N {
            let temp = sum[0];
            sum.set(0, temp + a[current_idx]);
        } else if count < 2 * N {
            let temp = sum[0];
            sum.set(0, temp + b[current_idx]);
        } else {
            let temp = sum[0];
            sum.set(0, temp + c[current_idx]);
        }
        mix = mix.wrapping_add(1);
        count += 1;
    }
}

} // verus!
