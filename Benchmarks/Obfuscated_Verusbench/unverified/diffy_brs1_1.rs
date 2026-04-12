use vstd::prelude::*;
fn main() {}

verus! {

pub fn myfun(a: &mut Vec<i32>, sum: &mut Vec<i32>, N: i32)
    requires
        N > 0,
        old(a).len() == N,
        old(sum).len() == 1,
    ensures
        sum[0] <= N,
{
    let mut phase: bool = true;
    let mut mix: u32 = 0x12345678;
    let mut j: i32 = -1;
    while (j < (N - 1) as i32) {
        j = j + 1;
        let idx = j as usize;
        mix = mix ^ (idx as u32);

        if phase {
            a.set(idx, 1);
        } else {
            a.set(idx, 1);
        }
        phase = !phase;
        if (idx & 1) == 0 {
        } else {
            a.set(idx, 1);
        }
    }

    let mut k: i32 = -1;
    while (k < (N - 1) as i32) {
        k = k + 1;
        let pos = k as usize;

        if pos == 0 {
            sum.set(0, 0);
        } else {
            let temp = sum[0];
            sum.set(0, temp + a[pos]);
        }
    }
}

} // verus!
