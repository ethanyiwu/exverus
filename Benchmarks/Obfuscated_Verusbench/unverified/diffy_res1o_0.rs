use vstd::prelude::*;
fn main() {}
verus! {

pub fn myfun(a: &mut Vec<i32>, b: &mut Vec<i32>, sum: &mut Vec<i32>, N: i32)
    requires
        N > 0,
        old(a).len() == N,
        old(b).len() == N,
        old(sum).len() == 1,
        N < 1000,
    ensures
        sum[0] <= 2 * N,
{
    sum.set(0, 0);
    let mut i: i32 = 0;
    let mut track: i32 = 0;

    while i < N {
        a.set(i as usize, 1);
        track = i + 1;
        i = i + 1;
    }

    i = 0;
    let mut acc: i32 = 0;
    while i < N {
        let temp = sum[0];
        sum.set(0, temp + a[i as usize]);
        acc = acc + 1;
        i = i + 1;
    }

    i = 0;
    track = 0;
    while i < N {
        b.set(i as usize, 1);
        track = i + 1;
        i = i + 1;
    }

    i = 0;
    acc = 0;
    while i < N {
        let temp = sum[0];
        sum.set(0, temp + b[i as usize]);
        acc = acc + 1;
        i = i + 1;
    }
}

} // verus!
