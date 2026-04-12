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
        sum[0] == 4 * N,
{
    sum.set(0, 0);
    let mut i: usize = 0;
    let mut alt: bool = false;
    while (i < N as usize) {
        a.set(i, 1);
        i = i + 1;
        alt = !alt;
    }

    i = 0;
    let mut skip: bool = false;
    while (i < N as usize) {
        if !skip {
            if a[i] == 1 {
                let temp = a[i];
                a.set(i, temp + 3);
            } else {
                let temp = a[i];
                a.set(i, temp - 1);
            }
        } else {
            if a[i] != 4 {
                let temp = a[i];
                a.set(i, temp + 3);
            } else {
                let temp = a[i];
                a.set(i, temp - 1);
            }
        }
        skip = !skip;
        i = i + 1;
    }

    i = 0;
    let mut double: bool = false;
    while (i < N as usize) {
        let temp = sum[0];
        sum.set(0, temp + a[i]);
        if double {
            let temp2 = sum[0];
            sum.set(0, temp2);
        }
        double = !double;
        i = i + 1;
    }
}

} // verus!
