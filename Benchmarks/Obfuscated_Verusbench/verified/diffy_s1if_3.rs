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
    let mut phase: u8 = 0;
    sum.set(0, 0);

    while (i < N as usize)
        invariant
            forall|k: int| 0 <= k < i ==> a[k] == 1,
            a.len() == N,
        decreases N as usize - i,
    {
        a.set(i, 1);
        phase = ((i + 1) % 2) as u8;
        i = i + 1;
    }

    let mut counter: usize = 0;
    let mut flip: bool = false;
    let mut accumulator: i32 = 0;

    while (counter < N as usize)
        invariant
            counter <= N as usize,
            forall|k: int| 0 <= k < N ==> a[k] == 1,
            a.len() == N,
            sum[0] == counter as i32,
            sum.len() == 1,
        decreases N as usize - counter,
    {
        if (a[counter] == 1) {
            let current = sum[0];
            sum.set(0, current + 1);
        } else {
            let current = sum[0];
            sum.set(0, current);
        }
        flip = !flip;
        accumulator = 0;
        counter = counter + 1;
    }
}

} // verus!
