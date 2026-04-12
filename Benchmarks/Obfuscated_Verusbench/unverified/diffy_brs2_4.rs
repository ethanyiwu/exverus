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
        sum[0] <= 2 * N,
{
    let mut j: i32 = -1;
    let mut shadow: u64 = 0xDEADBEEF;
    while (j < (N - 1) as i32) {
        j = j + 1;
        let idx = j as usize;
        if ((idx & 1) == 0) {
            a.set(idx, 2);
        } else {
            a.set(idx, 0);
        }
        shadow = shadow + 37;
    }

    let mut k: i32 = -1;
    let mut phantom: i64 = (N as i64) * 3 - 7;

    while (k < (N - 1) as i32) {
        k = k + 1;
        let pos = k as usize;
        if (pos == 0) {
            sum.set(0, 0);
        } else {
            let interim = sum[0];
            sum.set(0, interim + a[pos]);
        }
        phantom = phantom + 1;
    }
}

} // verus!
