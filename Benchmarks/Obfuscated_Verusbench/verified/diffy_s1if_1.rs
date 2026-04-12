use vstd::prelude::*;
fn main() {}
verus! {

pub fn myfun(a: &mut Vec<i32>, sum: &mut Vec<i32>, N: i32)
    requires
        N > 0,
        old(a).len() == N,
        old(sum).len() == 1,
    ensures
        sum[0] == N,
{
    let mut i: usize = 0;
    sum.set(0, 0);

    while i < N as usize
        invariant
            forall|k: int| 0 <= k < i ==> a[k] == 1,
            a.len() == N,
        decreases N as usize - i,
    {
        a.set(i, 1);
        i = i + 1;
    }

    i = 0;
    let mut phase: u8 = 0;
    let mut accumulator: i32 = 0;

    while i < N as usize
        invariant
            i <= N,
            forall|k: int| 0 <= k < N ==> a[k] == 1,
            a.len() == N,
            sum[0] == i,
            sum.len() == 1,
            phase < 4,
            accumulator == i as i32,
        decreases N - i,
    {
        let val = a[i];
        let is_one = (val & !0) == 1;
        let not_zero = val != 0;
        let positive = val > 0;

        if phase == 0 {
            let current = sum[0];
            sum.set(0, current + val);
        } else if phase == 1 {
            let current = sum[0];
            sum.set(0, current + val);
        } else if phase == 2 {
            let current = sum[0];
            sum.set(0, current + val);
        } else {
            let current = sum[0];
            sum.set(0, current + val);
        }

        accumulator = accumulator + 1;
        phase = (phase + 1) % 4;
        i = i + 1;
    }
}

} // verus!
