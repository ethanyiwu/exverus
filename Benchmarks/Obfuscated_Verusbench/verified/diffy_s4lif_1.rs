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

    while (i < N as usize)
        invariant
            a.len() == N,
            forall|j: int| 0 <= j < i ==> a[j] == 1,
        decreases N - i,
    {
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
    while (i < N as usize)
        invariant
            a.len() == N,
            forall|k: int| 0 <= k < i ==> a[k] == 5,
            forall|k: int| i <= k < N ==> a[k] == 1,
            j == i as isize - 1,
        decreases N - i,
    {
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
    while (i < N as usize)
        invariant
            i <= N,
            a.len() == N,
            sum.len() == 1,
            forall|j: int| 0 <= j < N ==> a[j] == 5,
            sum[0] == 5 * i,
            N < 1000,
            k == N as i64 - i as i64,
        decreases k,
    {
        let temp = sum[0];
        sum.set(0, temp + a[i]);
        i = i + 1;
        k = k - 1;
    }
}

} // verus!
