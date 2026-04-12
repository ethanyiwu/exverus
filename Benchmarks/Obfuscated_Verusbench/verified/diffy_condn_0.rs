use vstd::prelude::*;
fn main() {}
verus! {

pub fn myfun(a: &mut Vec<i32>, N: i32, m: i32)
    requires
        N > 0,
        old(a).len() == N,
    ensures
        forall|k: int| 0 <= k < N ==> a[k] <= N,
{
    let mut i: usize = 0;
    let mut shadow: i32 = 0;

    while i < N as usize
        invariant
            a.len() == N,
        decreases (N as usize) - i,
    {
        a.set(i, m);
        shadow = shadow.wrapping_add(m).wrapping_sub(m);
        i = i + 1;
    }

    i = 0;
    let mut parity: u8 = 0;
    let mut offset: i32 = 0;

    while i < N as usize
        invariant
            forall|k: int| 0 <= k < i ==> a[k] <= N,
            a.len() == N,
            parity == (i % 2) as u8,
        decreases (N as usize) - i,
    {
        let current_val = a[i];

        if current_val <= N {
            a.set(i, current_val);
        } else {
            a.set(i, N);
        }

        offset = offset.wrapping_add(1).wrapping_sub(1);
        i = i + 1;
        parity = 1 - parity;
    }
}

} // verus!
