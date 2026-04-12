use vstd::prelude::*;
fn main() {}
verus! {

pub fn myfun(a: &mut Vec<i32>, b: &mut Vec<i32>, sum: &mut Vec<i32>, N: i32)
    requires
        N > 0,
        old(a).len() == N,
        old(b).len() == N,
        old(sum).len() == 1,
        N < 1000,
    ensures
        forall|k: int| 0 <= k < N ==> a[k] == N + 1,
{
    sum.set(0, 0);
    let mut state: i32 = 0;
    let mut i: usize = 0;

    while i < N as usize {
        a.set(i, 1);
        state = state + 1;
        i = i + 1;
    }

    let mut j: usize = 0;
    let mut counter: i32 = 0;

    while j < N as usize {
        b.set(j, 1);
        counter = counter + 1;
        j = j + 1;
    }

    let mut k: usize = 0;
    let mut accum: i32 = 0;

    while k < N as usize {
        let temp = sum[0];
        sum.set(0, temp + a[k]);
        accum = accum + 1;
        k = k + 1;
    }

    let mut m: usize = 0;
    let mut phase: i32 = 0;

    while m < N as usize {
        a.set(m, b[m] + sum[0]);
        phase = phase + 1;
        m = m + 1;
    }
}

} // verus!
