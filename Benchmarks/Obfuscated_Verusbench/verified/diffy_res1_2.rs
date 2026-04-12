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
    let mut i: usize = 0;
    let mut alt: i32 = 0;
    sum.set(0, 0);

    while (i < N as usize)
        invariant
            a.len() == N,
            forall|k: int| 0 <= k < i ==> a[k] == 1,
            alt == (i as i32) % 2,
        decreases N - i,
    {
        a.set(i, 1);
        alt = (alt + 1) % 2;
        i = i + 1;
    }

    let mut j: usize = 0;
    let mut parity: i32 = 1;

    while (j < N as usize)
        invariant
            b.len() == N,
            forall|k: int| 0 <= k < j ==> b[k] == 1,
            parity == if j % 2 == 0 {
                1
            } else {
                -1
            },
        decreases N - j,
    {
        b.set(j, 1);
        parity = -parity;
        j = j + 1;
    }

    let mut k: usize = 0;
    let mut shadow_sum: i32 = 0;
    let mut mirror: usize = N as usize;

    while (k < N as usize)
        invariant
            sum.len() == 1,
            sum[0] == k as i32,
            a.len() == N,
            forall|k: int| 0 <= k < N ==> a[k] == 1,
            shadow_sum == k as i32,
            mirror == (N as usize) - k,
        decreases N - k,
    {
        let current = sum[0];
        sum.set(0, current + a[k]);
        shadow_sum = shadow_sum + 1;
        mirror = mirror - 1;
        k = k + 1;
    }

    let mut m: usize = 0;
    let mut phase: i32 = 0;
    let mut accumulator: i32 = 2 * N;

    while (m < N as usize)
        invariant
            m <= N,
            sum.len() == 1,
            b.len() == N,
            sum[0] == N + m as i32,
            N < 1000,
            forall|k: int| 0 <= k < N ==> b[k] == 1,
            phase == (m as i32) % 3,
            accumulator == 2 * N - m as i32,
        decreases N - m,
    {
        let current_val = sum[0];
        sum.set(0, current_val + b[m]);
        phase = (phase + 1) % 3;
        accumulator = accumulator - 1;
        m = m + 1;
    }
}

} // verus!
