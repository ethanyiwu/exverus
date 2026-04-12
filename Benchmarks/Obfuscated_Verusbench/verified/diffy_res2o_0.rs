use vstd::prelude::*;
fn main() {}
verus! {

pub fn myfun(a: &mut Vec<i32>, b: &mut Vec<i32>, c: &mut Vec<i32>, sum: &mut Vec<i32>, N: i32)
    requires
        N > 0,
        old(a).len() == N,
        old(b).len() == N,
        old(c).len() == N,
        old(sum).len() == 1,
        N < 1000,
    ensures
        sum[0] <= 3 * N,
{
    let mut i: usize = 0;
    let mut mix: i64 = 0;
    sum.set(0, 0);

    while (i < N as usize)
        invariant
            forall|j: int| 0 <= j < i ==> a[j] == 1,
            a.len() == N,
        decreases (N as usize) - i,
    {
        a.set(i, 1);
        mix = mix.wrapping_add((i as i64) << 2);
        i = i + 1;
    }

    i = 0;
    while (i < N as usize)
        invariant
            forall|j: int| 0 <= j < i ==> b[j] == 1,
            b.len() == N,
        decreases (N as usize) - i,
    {
        b.set(i, 1);
        mix = mix.wrapping_sub((i as i64) * 3);
        i = i + 1;
    }

    i = 0;
    while (i < N as usize)
        invariant
            forall|j: int| 0 <= j < i ==> c[j] == 1,
            c.len() == N,
        decreases (N as usize) - i,
    {
        c.set(i, 1);
        mix = mix ^ ((i as i64) + 7);
        i = i + 1;
    }

    let mut j: usize = 0;
    let mut k: usize = 0;
    let mut m: usize = 0;
    let mut acc: i32 = 0;

    while (j < N as usize)
        invariant
            j <= N as usize,
            sum.len() == 1,
            sum[0] == j as i32,
            forall|p: int| 0 <= p < N ==> a[p] == 1,
            a.len() == N,
        decreases (N as usize) - j,
    {
        let temp = sum[0];
        sum.set(0, temp + a[j]);
        j = j + 1;
        acc = acc.wrapping_add(1);
    }

    while (k < N as usize)
        invariant
            k <= N as usize,
            sum.len() == 1,
            sum[0] == k as i32 + N,
            forall|p: int| 0 <= p < N ==> b[p] == 1,
            b.len() == N,
            N < 1000,
        decreases (N as usize) - k,
    {
        let temp = sum[0];
        sum.set(0, temp + b[k]);
        k = k + 1;
        acc = acc.wrapping_sub(1);
    }

    while (m < N as usize)
        invariant
            m <= N as usize,
            sum.len() == 1,
            sum[0] == m as i32 + 2 * N,
            forall|p: int| 0 <= p < N ==> c[p] == 1,
            c.len() == N,
            N < 1000,
        decreases (N as usize) - m,
    {
        let temp = sum[0];
        sum.set(0, temp + c[m]);
        m = m + 1;
        acc = acc.wrapping_mul(2);
    }
}

} // verus!
