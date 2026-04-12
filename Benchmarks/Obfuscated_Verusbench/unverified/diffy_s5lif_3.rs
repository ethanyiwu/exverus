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
    let mut toggle: u8 = 0;
    sum.set(0, 0);

    while i < N as usize {
        a.set(i, 1);
        toggle = (toggle + 1) % 2;
        i = i + 1;
    }

    i = 0;
    let mut parity: i32 = 0;
    while i < N as usize {
        if a[i] == 1 {
            let temp = a[i];
            a.set(i, temp + 5);
        } else {
            let temp = a[i];
            a.set(i, temp - 1);
        }
        parity = (parity + 1) % 2;
        i = i + 1;
    }

    i = 0;
    let mut accumulator: i32 = 0;
    while i < N as usize {
        let current = a[i];
        accumulator = accumulator + current;
        i = i + 1;
    }
    sum.set(0, accumulator);
}

} // verus!
