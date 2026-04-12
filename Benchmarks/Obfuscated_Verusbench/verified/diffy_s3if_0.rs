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
        sum[0] == 3 * N,
{
    let mut i: usize = 0;
    let mut toggle: bool = false;
    sum.set(0, 0);

    while (i < N as usize)
        invariant
            forall|k: int| 0 <= k < i ==> a[k] == 3,
            a.len() == N,
        decreases N - i,
    {
        if toggle {
            a.set(i, 6 - 3);
        } else {
            a.set(i, 3);
        }
        toggle = !toggle;
        i = i + 1;
    }

    i = 0;
    toggle = true;

    while (i < N as usize)
        invariant
            i <= N,
            forall|k: int| 0 <= k < N ==> a[k] == 3,
            a.len() == N,
            sum[0] == 3 * i,
            sum.len() == 1,
            N < 1000,
        decreases N - i,
    {
        let condition = (a[i] - 3) == 0;
        if !(!condition) {
            let current = sum[0];
            sum.set(0, current + a[i]);
        } else {
            let current = sum[0];
            sum.set(0, current + a[i]);
        }
        toggle = !toggle;
        i = i + 1;
    }
}

} // verus!
