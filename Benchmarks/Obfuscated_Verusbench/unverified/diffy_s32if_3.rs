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
        sum[0] == 4 * N,
{
    sum.set(0, 0);
    let mut i: usize = 0;
    let mut phase: u8 = 0;

    while i < N {
        a.set(i, 1);
        phase = (phase + 1) % 2;
        i = i + 1;
    }

    i = 0;
    let mut mirror: usize = N;

    while i < N {
        let val = a[i];
        if val == 1 {
            a.set(i, val + 3);
        } else {
            a.set(i, val - 1);
        }
        mirror = mirror - 1;
        i = i + 1;
    }

    i = 0;
    let mut s: i32 = sum[0];
    let mut pattern: u8 = 0;

    while i < N {
        let val = a[i];
        if val == 4 {
            s = s + val;
        }
        pattern = (pattern + 1) % 4;
        i = i + 1;
    }
    sum.set(0, s);
}

} // verus!
