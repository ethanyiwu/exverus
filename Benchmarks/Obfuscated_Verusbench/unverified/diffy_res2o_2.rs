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
    while idx < N as usize {
        a.set(idx, 1);
        b.set(idx, 1);
        c.set(idx, 1);
        mix = mix.wrapping_add(1);
        idx += 1;
    }

    let mut count: i32 = 0;
    let mut read_phase: u8 = 0;
    let mut read_offset: i32 = 0;

    while count < 3 * N {
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
