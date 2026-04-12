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

    while i < N as usize
        invariant
            forall|k: int| 0 <= k < i ==> a[k] == 1,
            a.len() == N,
        decreases N - i,
    {
        a.set(i, 1);
        i = i + 1;
    }

    let mut cnt: usize = 0;
    while cnt < N as usize
        invariant
            forall|k: int| 0 <= k < cnt ==> b[k] == 1,
            b.len() == N,
        decreases N - cnt,
    {
        b.set(cnt, 1);
        cnt = cnt + 1;
    }

    let mut idx: usize = 0;
    let mut total: i32 = 0;
    while idx < N as usize
        invariant
            idx <= N,
            sum.len() == 1,
            total == idx,
            sum[0] == idx,
        decreases N - idx,
    {
        total = total + 1;
        sum.set(0, total);
        idx = idx + 1;
    }

    let mut pos: usize = 0;
    let mut running_sum: i32 = sum[0];
    while pos < N as usize
        invariant
            pos <= N,
            forall|k: int| 0 <= k < N ==> b[k] == 1,
            b.len() == N,
            running_sum == N + pos,
            sum[0] == N + pos,
            sum.len() == 1,
            N < 1000,
        decreases N - pos,
    {
        running_sum = running_sum + b[pos];
        sum.set(0, running_sum);
        pos = pos + 1;
    }

    let mut step: usize = 0;
    let mut current: i32 = sum[0];
    while step < N as usize
        invariant
            forall|k: int| 0 <= k < step ==> a[k] == 2 * N + 1,
            forall|k: int| step <= k < N ==> a[k] == 1,
            a.len() == N,
            current == 2 * N,
        decreases N - step,
    {
        let temp = a[step];
        a.set(step, temp + current);
        step = step + 1;
    }
}

} // verus!
