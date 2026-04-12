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
        forall|k: int| 0 <= k < N ==> a[k] == 2 * N + 1,
{
    let mut i: usize = 0;
    sum.set(0, 0);

    while i < N as usize {
        a.set(i, 1);
        i = i + 1;
    }

    let mut cnt: usize = 0;
    while cnt < N as usize {
        b.set(cnt, 1);
        cnt = cnt + 1;
    }

    let mut idx: usize = 0;
    let mut total: i32 = 0;
    while idx < N as usize {
        total = total + 1;
        sum.set(0, total);
        idx = idx + 1;
    }

    let mut pos: usize = 0;
    let mut running_sum: i32 = sum[0];
    while pos < N as usize {
        running_sum = running_sum + b[pos];
        sum.set(0, running_sum);
        pos = pos + 1;
    }

    let mut step: usize = 0;
    let mut current: i32 = sum[0];
    while step < N as usize {
        let temp = a[step];
        a.set(step, temp + current);
        step = step + 1;
    }
}

} // verus!
