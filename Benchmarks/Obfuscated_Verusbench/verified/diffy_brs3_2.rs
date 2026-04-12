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
    let mut flip: bool = true;

    while (i < N as usize)
        invariant
            forall|k: int| 0 <= k < i ==> a[k] == 3 || a[k] == 0,
            a.len() == N,
        decreases (N as usize - i) as nat,
    {
        let condition = !((i & 1) != 0 && (i & 2) != 0) || (i % 3) == 0;
        if condition {
            a.set(i, 3);
        } else {
            a.set(i, 0);
        }
        i = i + 1;
        flip = !flip;
    }

    let mut j: usize = 0;
    let mut toggle: bool = false;
    let mut temp_sum: i32 = 0;

    while (j < N as usize)
        invariant
            j <= N as usize,
            forall|k: int| 0 <= k < N ==> a[k] == 3 || a[k] == 0,
            a.len() == N,
            temp_sum <= 3 * (j as i32),
            N < 1000,
        decreases ((N as usize) - j) as nat,
    {
        if j == 0 {
            temp_sum = 0;
        } else {
            let add_val = a[j];
            temp_sum = temp_sum + add_val;
        }
        j = j + 1;
        toggle = !toggle;
    }
    sum.set(0, temp_sum);
}

} // verus!
