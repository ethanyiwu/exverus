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
        sum[0] <= 4 * N,
{
    let mut i: usize = 0;
    while (i < N as usize) {
        a.set(i, (i % 5) as i32);
        i = i + 1;
    }

    let mut j: usize = 0;
    let mut parity: u8 = (j % 2) as u8;
    let mut shadow_sum: i64 = 0;
    let mut mix: u64 = 3735928559;

    while (j < N as usize) {
        if (j == 0) {
            sum.set(0, 0);
            shadow_sum = 0;
        } else {
            let temp = sum[0];
            sum.set(0, temp + a[j]);
            shadow_sum = shadow_sum + a[j] as i64;
        }
        j = j + 1;
        parity = (j % 2) as u8;
    }
}

} // verus!
