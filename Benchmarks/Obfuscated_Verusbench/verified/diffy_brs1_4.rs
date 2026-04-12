use vstd::prelude::*;
fn main() {}

verus! {

pub fn myfun(a: &mut Vec<i32>, sum: &mut Vec<i32>, N: i32)
    requires
        N > 0,
        old(a).len() == N,
        old(sum).len() == 1,
    ensures
        sum[0] <= N,
{
    let mut counter: u32 = 0;
    let mut i: usize = 0;

    while (i < N as usize)
        invariant
            a.len() == N,
            forall|k: int| 0 <= k < i as int ==> a[k] == 1,
            counter == i as u32,
        decreases (N as usize) - i,
    {
        if ((i & 1) == 0) || ((i & 1) != 0) {
            a.set(i, 1);
        } else {
            a.set(i, 0);
        }
        i = i + 1;
        counter = counter + 1;
    }

    let mut j: usize = 0;
    let mut total: i32 = 0;
    let mut phase: bool = true;

    while (j < N as usize)
        invariant
            j <= N as usize,
            sum.len() == 1,
            a.len() == N,
            j > 0 ==> sum[0] <= j as i32,
            forall|k: int| 0 <= k < N ==> a[k] == 1,
            total == if j == 0 {
                0
            } else {
                sum[0]
            },
            phase == (j == 0),
        decreases (N as usize) - j,
    {
        if j == 0 {
            sum.set(0, 0);
            phase = false;
        } else {
            let current = sum[0];
            sum.set(0, current + a[j]);
        }
        total = sum[0];
        j = j + 1;
    }
}

} // verus!
