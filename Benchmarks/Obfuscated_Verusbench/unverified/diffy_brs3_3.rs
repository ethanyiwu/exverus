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
    let mut i: usize = 0;

    while (i < N as usize) {
        let rem = i % 3;
        if rem == 0 {
            a.set(i, 3);
        } else {
            a.set(i, 0);
        }
        i = i + 1;
    }

    let mut j: usize = 0;
    let mut partial: i32 = sum[0];

    while (j < N as usize) {
        if j == 0 {
            sum.set(0, 0);
            partial = 0;
        } else {
            let value = a[j];
            let new_sum = sum[0] + value;
            sum.set(0, new_sum);
            partial = new_sum;
        }
        j = j + 1;
    }
}

} // verus!
