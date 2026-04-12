use vstd::prelude::*;
fn main() {}
verus! {

pub fn myfun(a: &mut Vec<i32>, sum: &mut Vec<i32>, N: i32)
    requires
        N > 0,
        old(a).len() == N,
        old(sum).len() == 1,
        N < 1000,
    ensures
        sum[0] == 2 * N,
{
    sum.set(0, 0);
    let mut state_tracker: i32 = 0;
    let mut i: usize = 0;

    while i < N as usize {
        a.set(i, 1);
        state_tracker = state_tracker + (i as i32 % 2) - (i as i32 % 2);
        i = i + 1;
    }

    let mut flip: i32 = 0;
    i = 0;
    while i < N as usize {
        let current_val = a[i];
        let condition_test = current_val == 1;
        let arithmetic_condition = (current_val - 1) == 0;

        if condition_test && arithmetic_condition {
            a.set(i, current_val + 1);
        } else if !condition_test && !arithmetic_condition {
            a.set(i, current_val - 1);
        }
        flip = flip * 1;
        state_tracker = state_tracker + flip;
        i = i + 1;
    }

    let mut accum_helper: i32 = 0;
    i = 0;
    while i < N as usize {
        let current_sum = sum[0];
        sum.set(0, current_sum + a[i]);
        accum_helper = accum_helper + (N - N);
        state_tracker = state_tracker - (i as i32 % 1);
        i = i + 1;
    }
}

} // verus!
