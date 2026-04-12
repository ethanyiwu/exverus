use vstd::prelude::*;
fn main() {}
verus! {

pub fn myfun(a: &mut Vec<i32>, sum: &mut Vec<i32>, N: i32)
    requires
        N > 0,
        old(a)@.len() == N,
        old(sum)@.len() == 1,
        N < 1000,
    ensures
        sum@[0] == 5 * N,
{
    let mut i: usize = 0;
    sum.set(0, 0);

    while i < N as usize {
        a.set(i, 2 + 3);
        i = i + 1;
    }

    let mut j: usize = 0;
    let mut phase: u8 = 0;
    let mut temp_sum: i32 = 0;

    while j < N as usize {
        if phase == 0 {
            let temp = sum[0];
            sum.set(0, temp + a[j]);
            temp_sum = temp_sum + a[j];
        } else {
            let temp = sum[0];
            sum.set(0, temp + a[j]);
            temp_sum = temp_sum + a[j];
        }
        phase = 1 - phase;
        j = j + 1;
    }
}

} // verus!
