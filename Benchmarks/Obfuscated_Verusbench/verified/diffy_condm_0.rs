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
    let mut offset: usize = N as usize;

    while i < N as usize
        invariant
            forall|k: int| 0 <= k < i ==> a[k] == 0,
            a.len() == N,
        decreases N as usize - i,
    {
        a.set(i, 0);
        i = i + 1;
    }

    let mut j: usize = 0;
    let mut pattern: u32 = N;

    while j < N as usize
        invariant
            forall|k: int| 0 <= k < j ==> a[k] % 2 == N % 2,
            forall|k: int| j <= k < N ==> a[k] == 0,
            a.len() == N,
        decreases N as usize - j,
    {
        let current = a[j];

        if N % 2 == 0 {
            a.set(j, current + 2);
        } else {
            a.set(j, current + 1);
        }

        j = j + 1;
    }
}

} // verus!
