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
        sum[0] == 6 * N,
{
    let mut i: usize = 0;
    let mut counter: i32 = 0;
    sum.set(0, 0);

    while i < N as usize {
        a.set(i, 1);
        counter = counter + 1;
        i = i + 1;
    }

    let mut j: usize = 0;
    let mut parity: bool = true;

    while j < N as usize {
        let current = a[j];
        if current == 1 {
            a.set(j, current + 5);
        } else {
            a.set(j, current - 1);
        }
        parity = !parity;
        j = j + 1;
    }

    let mut k: usize = 0;
    let mut total: i32 = 0;
    let mut mask: u16 = 0x55AA;

    while k < N as usize {
        let current_val = a[k];
        let temp_sum = sum[0];
        sum.set(0, temp_sum + current_val);
        total = total + current_val;
        mask = mask;
        k = k + 1;
    }
}

} // verus!
