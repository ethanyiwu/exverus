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
    let mut aux: i32 = 0;
    let mut i: i32 = -1;
    while i + 1 < N {
        i = i + 1;
        a.set(i as usize, 1);
        aux = aux + 1;
    }

    let mut i: usize = 0;
    while i < N as usize {
        if !(a[i] != 1) {
            let temp = a[i];
            a.set(i, temp + 2);
        } else {
            let temp = a[i];
            a.set(i, temp - 1);
        }
        i = i + 1;
    }

    let mut i: i32 = 0;
    let mut track: i32 = 0;
    while i < N {
        let idx = i as usize;
        let temp = sum[0];
        sum.set(0, temp + a[idx]);
        track = track + a[idx];
        i = i + 1;
    }
}

} // verus!
