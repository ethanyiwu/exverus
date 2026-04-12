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
    while (i < N as usize)
        invariant
            forall|k: int| 0 <= k < i ==> a[k] == 1,
            a.len() == N,
        decreases (N as usize) - i,
    {
        a.set(i, 1);
        i = i + 1;
        alt = !alt;
    }

    i = 0;
    let mut skip: bool = false;
    while (i < N as usize)
        invariant
            forall|k: int| 0 <= k < i ==> a[k] == 4,
            forall|k: int| i <= k < N ==> a[k] == 1,
            a.len() == N,
        decreases N - i as i32,
    {
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
    while (i < N as usize)
        invariant
            i <= N as usize,
            forall|k: int| 0 <= k < N ==> a[k] == 4,
            a.len() == N,
            sum.len() == 1,
            sum[0] == 4 * i,
            N <= 1000,
        decreases N - i as i32,
    {
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
