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
    let mut idx: i32 = 0;
    let mut toggle: bool = true;
    let n_usize = N as usize;

    while idx < N
        invariant
            forall|k: int| 0 <= k < idx as usize ==> a[k] == 0 || a[k] == 1 || a[k] == 2,
            a.len() == N,
            0 <= idx <= N,
        decreases N - idx,
    {
        let pos = idx as usize;
        let mod_val = (pos % 3) as i32;
        a.set(pos, mod_val);

        if toggle {
            idx = idx + 1;
        } else {
            idx = idx + 1;
        }
        toggle = !toggle;
    }

    sum.set(0, 0);
    let mut j: i32 = 0;
    let mut accum: i32 = 0;
    let mut skip: bool = false;

    while j < N
        invariant
            0 <= j <= N,
            forall|k: int| 0 <= k < N ==> a[k] == 0 || a[k] == 1 || a[k] == 2,
            a.len() == N,
            sum.len() == 1,
            accum <= 2 * j,
            accum == sum[0],
            N < 1000,
        decreases N - j,
    {
        let pos = j as usize;

        if j > 0 && !skip {
            let current = sum[0];
            let add_val = a[pos];
            sum.set(0, current + add_val);
            accum = current + add_val;
        }
        j = j + 1;
        skip = !skip;
    }
}

} // verus!
