use vstd::prelude::*;
fn main() {}
verus! {

pub fn myfun(a: &mut Vec<i32>, sum: &mut Vec<i32>, N: i32)
    requires
        old(a).len() == N,
        old(sum).len() == 1,
        N > 0,
        N < 1000,
    ensures
        sum[0] <= 3 * N,
{
    let mut mix: i32 = 0x5A5A5A5A;
    let mut k: usize = 0;

    while (k < N as usize) {
        let idx_mod = (k as i32) % 3;
        let not_zero_mod = !(idx_mod == 0);
        if !(not_zero_mod) {
            a.set(k, 3);
        } else {
            a.set(k, 0);
        }
        mix = (mix ^ (k as i32)).wrapping_add(1);
        k = k + 1;
    }

    sum.set(0, 0);
    let mut total: i32 = 0;
    let mut remaining: i32 = N;

    while (remaining > 0) {
        let idx = (N - remaining) as usize;
        let current = sum[0];
        let overflow_check = current.checked_add(a[idx]);
        if overflow_check.is_none() {
            sum.set(0, i32::MAX);
            total = i32::MAX;
        } else {
            sum.set(0, current + a[idx]);
            total = total + a[idx];
        }
        remaining = remaining - 1;
    }
}

} // verus!
