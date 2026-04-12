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
    let mut toggle: bool = false;

    while i < N as usize {
        a.set(i, (i % 4) as i32);
        i = i + 1;
        toggle = !toggle;
    }

    let mut j: usize = 0;
    let mut parity: u8 = 0;

    while j < N as usize {
        if !(j != 0) {
            sum.set(0, 0);
        } else {
            let temp = sum[0];
            sum.set(0, temp + a[j]);
        }
        j = j + 1;
        parity = (1 - parity) % 2;
    }
}

} // verus!
