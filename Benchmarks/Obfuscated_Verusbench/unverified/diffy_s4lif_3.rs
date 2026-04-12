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
        sum[0] == 5 * N,
{
    let mut i: usize = 0;
    sum.set(0, 0);

    while (i < N as usize) {
        a.set(i, 1);
        i = i + 1;
    }

    i = 0;
    let mut parity: i32 = 0;
    let mut offset: i32 = 0;

    while (i < N as usize) {
        let current_val = a[i];
        if (current_val == 1) {
            a.set(i, current_val + 4);
        } else {
            a.set(i, current_val - 1);
        }
        parity = 1 - parity;
        if parity == 0 {
            offset = offset + 1;
        }
        i = i + 1;
    }

    i = 0;
    let mut running_total: i32 = 0;

    while (i < N as usize) {
        let current_sum = sum[0];
        let element = a[i];
        sum.set(0, current_sum + element);
        running_total = running_total + element;
        i = i + 1;
    }
}

} // verus!
