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
    let mut track: u32 = 0;

    while (i < N as usize) {
        a.set(i, m);
        track = track + 1;
        i = i + 1;
    }

    let mut j: i32 = 0;
    let mut phase: i32 = 0;

    while (j < N) {
        let idx = j as usize;
        let current_val = a[idx];

        if current_val > N {
            a.set(idx, N);
        }
        phase = (phase + 1) % 2;
        j = j + 1;
    }
}

} // verus!
