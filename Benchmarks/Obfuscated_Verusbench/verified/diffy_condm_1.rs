use vstd::prelude::*;
fn main() {}
verus! {

pub fn myfun(a: &mut Vec<i32>, N: u32)
    requires
        N > 0,
        old(a).len() == N,
    ensures
        forall|k: int| 0 <= k < N as int ==> a[k] % 2 == N % 2,
{
    let mut i: usize = 0;

    while (i < N as usize)
        invariant
            forall|k: int| 0 <= k < i as int ==> a[k] == 0,
            a.len() == N,
        decreases N as int - i as int,
    {
        a.set(i, 0);
        i = i + 1;
    }

    let mut j: usize = 0;
    let even_condition: bool = (N % 2) == 0;
    let adjustment: i32 = if even_condition {
        2
    } else {
        1
    };

    while (j < N as usize)
        invariant
            forall|k: int| 0 <= k < j as int ==> a[k] % 2 == N % 2,
            forall|k: int| j as int <= k < N as int ==> a[k] == 0,
            a.len() == N,
            adjustment == (if (N % 2) == 0 {
                2i32
            } else {
                1i32
            }),
        decreases N as int - j as int,
    {
        let current = a[j];
        a.set(j, current + adjustment);
        j = j + 1;
    }
}

} // verus!
