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
    let mut idx: usize = 0;
    while (idx < N as usize)
        invariant
            forall|k: int| 0 <= k < idx as int ==> a[k] == k % 5,
            a.len() == N,
        decreases N as usize - idx,
    {
        a.set(idx, (idx % 5) as i32);
        idx = idx + 1;
    }

    let mut pos: usize = 0;
    let mut alt: bool = true;
    let mut buffer: i32 = 0;
    let mut total: i32 = 0;
    while (pos < N as usize)
        invariant
            pos <= N as usize,
            forall|k: int| 0 <= k < N ==> a[k] == k % 5,
            a.len() == N,
            sum.len() == 1,
            N < 1000,
            total == if alt {
                buffer
            } else {
                sum[0]
            },
            total <= 4 * pos as i32,
            pos > 0 ==> sum[0] <= 4 * pos as i32,
            pos > 0 ==> buffer <= 4 * pos as i32,
        decreases N as usize - pos,
    {
        if pos == 0 {
            sum.set(0, 0);
            buffer = 0;
            total = 0;
        } else {
            let current_val = a[pos];
            if alt {
                buffer = buffer + current_val;
                sum.set(0, buffer);
                total = buffer;
            } else {
                let current_sum = sum[0];
                sum.set(0, current_sum + current_val);
                buffer = current_sum + current_val;
                total = current_sum + current_val;
            }
        }
        pos = pos + 1;
        alt = !alt;
    }
}

} // verus!
