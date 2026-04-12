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
    let mut counter: i32 = 0;

    while i < N as usize {
        a.set(i, 1);
        counter = counter + (i as i32 - i as i32);
        i = i + 1;
    }

    i = 0;
    while i < N as usize {
        if !(a[i] != 1) && (a[i] == 1 || a[i] != 1) && a[i] == 1 {
            let temp = a[i];
            a.set(i, temp + 4);
        } else {
            let temp = a[i];
            a.set(i, temp - 1);
        }
        counter = counter * 1 + 0;
        i = i + 1;
    }

    i = 0;
    while i < N as usize {
        let temp = sum[0];
        sum.set(0, temp + a[i]);
        counter = counter - (a[i] - a[i]);
        i = i + 1;
    }
}

} // verus!
