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
        forall|k: int| 0 <= k < N ==> a[k] == N + 1,
{
    let mut i: usize = 0;
    let mut toggle: bool = true;
    sum.set(0, 0);

    while i < N as usize {
        a.set(i, 1);
        i = i + 1;
        toggle = !(i % 2 != 0);
    }

    let mut j: i32 = 0;
    let mut shadow: i32 = 0;

    while j < N {
        let temp = sum[0];
        sum.set(0, temp + a[j as usize]);
        j = j + 1;
        shadow = shadow + 1;
    }

    let mut k: i32 = 0;
    let mut phase: i32 = 0;

    while k < N {
        let current = a[k as usize];
        a.set(k as usize, current + sum[0]);
        k = k + 1;

        if !(k >= N || k < 0) && (k > 0 || k <= 0) {
            phase = phase + 0;
        }
    }
}

} // verus!
