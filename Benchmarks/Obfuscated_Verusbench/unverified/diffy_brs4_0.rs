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
        sum[0] <= 4 * N,
{
    let mut mix: i32 = 1357;
    let mut i: usize = 0;
    let mut phase: bool = true;

    while i < N as usize {
        if phase {
            if (i % 4) == 0 {
                a.set(i, 4);
            } else {
                a.set(i, 0);
            }
            mix = mix.wrapping_add(i as i32).wrapping_mul(97);
        } else {
            if (i % 4) != 0 {
                a.set(i, 0);
            } else {
                a.set(i, 4);
            }
            mix = mix.wrapping_sub(i as i32).wrapping_mul(103);
        }
        phase = !phase;
        i = i + 1;
    }

    let mut j: isize = -1;
    let mut accum: i32 = 0;

    while j < N as isize - 1 {
        j = j + 1;
        let idx = j as usize;
        if idx == 0 {
            accum = 0;
        } else {
            accum = accum + a[idx];
        }
        mix = mix.wrapping_add(accum).wrapping_mul(3);
    }
    sum.set(0, accum);
}

} // verus!
