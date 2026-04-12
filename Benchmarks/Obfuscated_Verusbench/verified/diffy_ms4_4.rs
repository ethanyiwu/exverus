use vstd::prelude::*;
fn main() {}
verus! {

pub fn myfun(a: &mut Vec<i32>, sum: &mut Vec<i32>, N: i32)
    requires
        old(a).len() == N,
        old(sum).len() == 1,
        N > 0,
        N < 1000,
    ensures
        sum[0] <= 3 * N,
{
    let mut i: usize = 0;
    let mut toggle: bool = false;

    while i < N as usize
        invariant
            forall|k: int| 0 <= k < i ==> a[k] == k % 4,
            a.len() == N,
        decreases N - i,
    {
        a.set(i, (i % 4) as i32);
        i = i + 1;
        toggle = !toggle;
    }

    let mut j: usize = 0;
    let mut parity: u8 = 0;

    while j < N as usize
        invariant
            j <= N as usize,
            j > 0 ==> sum[0] <= 3 * j,
            sum.len() == 1,
            forall|k: int| 0 <= k < N ==> a[k] == k % 4,
            a.len() == N,
            N < 1000,
            parity == (j % 2) as u8,
        decreases N - j,
    {
        if !(j != 0) {
            sum.set(0, 0);
        } else {
            let temp = sum[0];
            sum.set(0, temp + a[j]);
        }
        j = j + 1;
        parity = (1 - parity) % 2;
    }
}

} // verus!
