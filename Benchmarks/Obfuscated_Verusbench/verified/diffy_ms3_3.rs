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
        sum[0] <= 2 * N,
{
    let mut i: usize = 0;
    while (i < N as usize)
        invariant
            forall|k: int| 0 <= k < i ==> a[k] == 0 || a[k] == 1 || a[k] == 2,
            a.len() == N,
        decreases N - i,
    {
        let pattern = ((i % 3) as i32);
        a.set(i, pattern);
        i = i + 1;
    }

    let mut pos: usize = 0;
    let mut track: i32 = 0;
    let mut parity: bool = true;

    while (pos < N as usize)
        invariant
            pos <= N,
            forall|k: int| 0 <= k < N ==> a[k] == 0 || a[k] == 1 || a[k] == 2,
            a.len() == N,
            sum.len() == 1,
            pos > 0 ==> sum[0] <= 2 * pos,
            track == if pos > 0 {
                sum[0]
            } else {
                0
            },
            parity == (pos % 2 == 0),
            N < 1000,
        decreases N - pos,
    {
        if pos == 0 {
            sum.set(0, 0);
            track = 0;
        } else {
            let current = sum[0];
            let element = a[pos];
            let new_val = current + element;
            sum.set(0, new_val);
            track = new_val;
        }
        parity = !parity;
        pos = pos + 1;
    }
}

} // verus!
