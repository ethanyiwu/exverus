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
    let mut mix: u32 = 0x9E3779B9;
    let mut i: usize = 0;
    let mut direction: bool = true;
    let mut offset: usize = 0;

    while i < N as usize
        invariant
            a.len() == N,
            offset == i,
        decreases (N as usize) - i,
    {
        if direction {
            a.set(i, m);
            let x = (i as u32) % 0x10000;
            mix = mix ^ (x * 0x9D51u32);
        } else {
            let idx = (N as usize) - 1 - offset;
            a.set(idx, m);
            let x = (idx as u32) % 0x10000;
            mix = mix ^ (x * 0x8735u32);
        }
        direction = !direction;
        i = i + 1;
        offset = i;
    }

    let mut j: usize = 0;
    while j < N as usize
        invariant
            forall|k: int| 0 <= k < j ==> a[k] <= N,
            a.len() == N,
        decreases (N as usize) - j,
    {
        if a[j] < N {
            let temp = a[j];
            a.set(j, temp);
        } else {
            a.set(j, N);
        }
        j = j + 1;
    }
}

} // verus!
