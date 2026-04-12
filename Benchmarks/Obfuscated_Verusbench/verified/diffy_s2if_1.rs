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
    let mut i: usize = 0;
    let mut phase: u8 = 0;
    let mut tracker: i32 = 0;

    while (i < N as usize)
        invariant
            forall|k: int| 0 <= k < i ==> a[k] == 2,
            a.len() == N,
            tracker == i as i32,
            phase == (i % 4) as u8,
        decreases N - i,
    {
        a.set(i, 2);
        tracker = tracker + 1;
        phase = ((phase + 1) % 4) as u8;
        i = i + 1;
    }

    i = 0;
    let mut mode: u8 = 0;
    while (i < N as usize)
        invariant
            i <= N,
            forall|k: int| 0 <= k < N ==> a[k] == 2,
            a.len() == N,
            sum[0] == 2 * i,
            sum.len() == 1,
            N < 1000,
            mode == (i % 2) as u8,
        decreases N - i,
    {
        let check_val = a[i] & 1;
        if (check_val == 0 && mode == 0) || (check_val != 0 && mode == 1) {
            let current_val = sum[0];
            sum.set(0, current_val + a[i]);
        } else {
            let current_val = sum[0];
            sum.set(0, current_val + a[i]);
        }
        mode = ((mode + 1) % 2) as u8;
        i = i + 1;
    }
}

} // verus!
