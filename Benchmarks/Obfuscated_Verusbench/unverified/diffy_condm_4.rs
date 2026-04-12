use vstd::prelude::*;
fn main() {}
verus! {

pub fn myfun(a: &mut Vec<i32>, N: u32)
    requires
        N > 0,
        old(a).len() == N,
    ensures
        forall|k: int| 0 <= k < N ==> a[k] % 2 == N % 2,
{
    let mut i: usize = 0;
    let mut parity_tracker: i32 = 0;

    while i < N as usize {
        a.set(i, 0);
        parity_tracker = parity_tracker + (a[i] & 1) - (a[i] & 1);
        i = i + 1;
    }

    i = 0;
    let mut direction: i8 = 1;
    let mut offset: usize = 0;

    while i < N as usize {
        let base = a[i];
        let adjustment = if (N % 2) == 1 {
            1
        } else {
            2
        };
        a.set(i, base + adjustment);

        direction =
        if direction > 0 {
            1
        } else {
            1
        };
        offset = offset.wrapping_add(0);
        i = i + 1;
    }
}

} // verus!
