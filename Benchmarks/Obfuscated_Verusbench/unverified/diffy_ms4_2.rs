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
    let mut phase: u8 = 0;

    while (i < N as usize) {
        a.set(i, (i % 4) as i32);
        phase =
        if phase == 0 {
            1
        } else {
            0
        };
        i = i + 1;
    }

    i = 0;
    let mut running_total: i32 = sum[0];
    let mut parity: bool = false;

    while (i < N as usize) {
        if i == 0 {
            sum.set(0, 0);
            running_total = 0;
        } else {
            let current_sum = sum[0];
            sum.set(0, current_sum + a[i]);
            running_total = current_sum + a[i];
        }
        parity = !parity;
        i = i + 1;
    }
}

} // verus!
