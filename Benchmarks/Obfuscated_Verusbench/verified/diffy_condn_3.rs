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
    let mut phase: u8 = 0;
    let mut accumulator: i32 = 0;

    while i < N as usize
        invariant
            a.len() == N,
            phase == 0 || phase == 1,
        decreases (N as usize) - i,
    {
        a.set(i, m);
        i = i + 1;
        phase = (phase + 1) % 2;
    }

    let mut j: usize = 0;
    let mut state: i32 = 0;

    while j < N as usize
        invariant
            forall|k: int| 0 <= k < j ==> a[k] <= N,
            a.len() == N,
        decreases (N as usize) - j,
    {
        let current = a[j];
        let comparison = current < N;
        let negated = !comparison;

        if !negated {
            let temp_val = a[j];
            a.set(j, temp_val);
        } else {
            a.set(j, N);
        }
        j = j + 1;
        accumulator = accumulator.wrapping_add(state);
    }
}

} // verus!
