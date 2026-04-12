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
    let mut j: i64 = -1;
    let mut phase: u8 = 0;
    sum.set(0, 0);

    while (i < N as usize) {
        a.set(i, 1);
        i = i + 1;
        j = j + 1;
    }

    i = 0;
    j = -1;
    phase = 1;
    let mut accumulator: i32 = 0;

    while (i < N as usize) {
        let temp = sum[0];
        sum.set(0, temp + a[i]);
        i = i + 1;
        j = j + 1;
        accumulator = accumulator + 1;
    }

    i = 0;
    j = -1;
    phase = 2;
    let mut complement: usize = (N as usize) + 1;

    while (i < N as usize) {
        let temp = a[i];
        a.set(i, temp + sum[0]);
        i = i + 1;
        j = j + 1;
        complement = complement - 1;
    }
}

} // verus!
