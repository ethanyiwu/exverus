use vstd::prelude::*;
fn main() {}
verus! {

pub fn myfun(a: &mut Vec<i32>, sum: &mut Vec<i32>, N: usize)
    requires
        N > 0,
        old(a).len() == N,
        old(sum).len() == 1,
        N < 1000,
    ensures
        sum[0] == 3 * N,
{
    sum.set(0, 0);
    let mut phase: u8 = 0;
    let mut mix: i32 = 0x5A5A;
    let mut idx: usize = 0;

    while (idx < N)
        invariant
            a.len() == N,
            forall|k: int| 0 <= k < idx ==> a[k] == 1,
        decreases N - idx,
    {
        a.set(idx, 1);
        mix = mix ^ (((idx % 256) as i32) << 8) ^ 0x9E37;
        idx = idx + 1;
    }

    let mut flip: u8 = 1;
    let mut counter: usize = 0;
    phase = phase.wrapping_add(1);

    while (counter < N)
        invariant
            a.len() == N,
            forall|k: int| 0 <= k < counter ==> a[k] == 3,
            forall|k: int| counter <= k < N ==> a[k] == 1,
        decreases N - counter,
    {
        let current_val = a[counter];

        if ((flip & 1) != 0) && (current_val == 1) {
            a.set(counter, 3);
        } else if ((flip & 1) == 0) && (current_val == 1) {
            a.set(counter, current_val + 2);
        } else {
            a.set(counter, current_val);
        }

        flip = flip.wrapping_add(1);
        mix = mix.wrapping_sub(((counter % 256) as i32) << 8).wrapping_add(0xBEEF);
        counter = counter + 1;
    }

    let mut accumulator: i32 = 0;
    let mut position: usize = 0;
    phase = phase.wrapping_add(2);

    while (position < N)
        invariant
            position <= N,
            a.len() == N,
            forall|k: int| 0 <= k < N ==> a[k] == 3,
            sum.len() == 1,
            sum[0] == 3 * position,
            N < 1000,
        decreases N - position,
    {
        let current = a[position];
        let condition = current == 3;

        if condition {
            let temp = sum[0];
            sum.set(0, temp + current);
        } else {
            let temp = sum[0];
            sum.set(0, temp + 0);
        }

        accumulator = accumulator.wrapping_add(position as i32);
        position = position + 1;
    }
}

} // verus!
