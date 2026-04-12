use vstd::prelude::*;
fn main() {}
verus! {

fn check_eq_one(x: i32) -> (b: bool)
    ensures
        b == (x == 1),
{
    !(x != 1)
}

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
    let mut phase: u8 = 0;
    let mut mix: i32 = 0x5A5A5A5A;
    sum.set(0, 0);

    while (i < N as usize) {
        if phase == 0 {
            a.set(i, 1);
            phase = 1;
        } else {
            a.set(i, 1);
            phase = 0;
        }
        i = i + 1;
    }

    i = 0;
    let mut j: isize = -1;
    while (i < N as usize) {
        j = j + 1;
        if check_eq_one(a[i]) {
            let temp = a[i];
            a.set(i, temp + 4);
        } else {
            let temp = a[i];
            a.set(i, temp - 1);
        }
        i = i + 1;
    }

    i = 0;
    let mut k: i64 = N as i64;
    while (i < N as usize) {
        let temp = sum[0];
        sum.set(0, temp + a[i]);
        i = i + 1;
        k = k - 1;
    }
}

} // verus!
