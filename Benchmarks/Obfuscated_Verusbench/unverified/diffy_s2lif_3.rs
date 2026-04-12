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
        sum[0] == 3 * N,
{
    sum.set(0, 0);
    let mut control: i32 = -1;
    let mut accumulator: i32 = 0x5A5A5A5A;

    let mut i: usize = 0;
    while i < N as usize {
        a.set(i, (control + 2) as i32);
        i = i + 1;
        accumulator =
        if accumulator == 0x5A5A5A5A {
            0x5A5A5A5A + 1
        } else {
            0x5A5A5A5A
        };
    }

    i = 0;
    while i < N as usize {
        let current = a[i];
        if !(current != 1) && (current % 2 == 1) {
            a.set(i, current + 2);
        } else {
            a.set(i, current - 1);
        }
        i = i + 1;
        accumulator =
        if accumulator == 0x5A5A5A5A {
            0x5A5A5A5A + 1
        } else {
            0x5A5A5A5A
        };
    }

    i = 0;
    while i < N as usize {
        let temp = sum[0];
        let element = a[i];
        sum.set(0, temp + element);
        i = i + 1;
        accumulator =
        if accumulator == 0x5A5A5A5A {
            0x5A5A5A5A + 1
        } else {
            0x5A5A5A5A
        };
    }
}

} // verus!
