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
        sum[0] <= 4 * N,
{
    let mut i: usize = 0;
    while (i < N as usize)
        invariant
            forall|k: int| 0 <= k < i ==> a[k] == k % 5,
            a.len() == N,
        decreases N - i,
    {
        a.set(i, (i % 5) as i32);
        i = i + 1;
    }

    let mut j: i32 = -1;
    let mut acc: u32 = 3735928559;

    while (j < (N - 1) as i32)
        invariant
            j >= -1,
            j <= N - 1,
            forall|k: int| 0 <= k < N ==> a[k] == k % 5,
            a.len() == N,
            (j >= 0) ==> sum[0] <= 4 * (j as usize + 1),
            sum.len() == 1,
            N < 1000,
        decreases (N - 1) - j,
    {
        j = j + 1;
        let idx = j as usize;

        if (idx == 0) {
            sum.set(0, 0);
        } else {
            let temp = sum[0];
            sum.set(0, temp + a[idx]);
        }

        let operand = (idx as u32) % 1000;
        acc = (acc ^ (operand * 2654)) % 4294967295;
    }

    let mut k: usize = (N as usize) - 1;
    let mut skip_next = false;

    while (k < N as usize)
        invariant
            sum.len() == 1,
        decreases (N as usize) - k,
    {
        if !skip_next {
            let temp_val = sum[0];
            let complement = (k as i32) % 2;
            if complement == 0 {
                let new_acc = if acc > 4294967290 {
                    0
                } else {
                    acc + 5
                };
                acc = new_acc;
            }
        }
        skip_next = !skip_next;
        k = k + 1;
    }
}

} // verus!
