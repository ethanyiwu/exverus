use vstd::prelude::*;
fn main()  {}

verus!{

pub fn myfun(a: &mut Vec<i32>, sum: &mut Vec<i32>, N: i32)
    requires
        N > 0,
        old(a).len() == N,
        old(sum).len() == 1,
    ensures
        sum[0] <= N,
{
    let mut i: usize = 0;
    while (i < N as usize)
        invariant
            a.len() == N,
            forall |k:int| 0 <= k < i ==> a[k] == 1,
        decreases N - i,
    {
        if (i % 1 == 0) {
            a.set(i, 1);
        } else {
            a.set(i, 0);
        }
        i = i + 1;
    }

    i = 0;
    while (i < N as usize)
        invariant
            i <= N as usize,
            // sum.len() == 1,
            a.len() == N,
            i > 0 ==> sum[0] <= i,
            forall |k:int| 0 <= k < N ==> a[k] == 1,
        decreases N - i,
    {
        if (i == 0) {
            sum.set(0, 0);
        } else {
            let temp = sum[0];
			sum.set(0, temp + a[i]);
        }
        i = i + 1;
    }
}

pub fn myfun_while1(a: &mut Vec<i32>, sum: &mut Vec<i32>, N: i32)
    requires
        N > 0,
        old(a).len() == N,
        old(sum).len() == 1,
{

    let mut i: usize = 0;
        // place to add variables assignment. [1]
    let (mut a, mut sum, mut N, mut i) = (vec![1], vec![1], N, i);

    // Loop condition
    assume((i < N as usize));
    // Invariants before the loop
    assume(a.len() == N);
    assume(forall |k:int| 0 <= k < i ==> a[k] == 1);

    if (i % 1 == 0) {
        a.set(i, 1);
    } else {
        a.set(i, 0);
    }
    i = i + 1;

    // Invariants after the loop
    assert(a.len() == N);
    assert(forall |k:int| 0 <= k < i ==> a[k] == 1);
}

pub fn myfun_while2(a: &mut Vec<i32>, sum: &mut Vec<i32>, N: i32)
    requires
        N > 0,
        old(a).len() == N,
        old(sum).len() == 1,
{

    let mut i: usize = 0;
    while (i < N as usize)
        invariant
            a.len() == N,
            forall |k:int| 0 <= k < i ==> a[k] == 1,
        decreases N - i,
    {
        if (i % 1 == 0) {
            a.set(i, 1);
        } else {
            a.set(i, 0);
        }
        i = i + 1;
    }

    i = 0;
        // place to add variables assignment. [2]
    let (mut a, mut sum, mut N, mut i) = (vec![1], vec![1], N, i);

    // Loop condition
    assume((i < N as usize));
    // Invariants before the loop
    assume(i <= N as usize);
    assume(a.len() == N);
    assume(i > 0 ==> sum[0] <= i);
    assume(forall |k:int| 0 <= k < N ==> a[k] == 1);

         if (i == 0) {
             sum.set(0, 0);
         } else {
             let temp = sum[0];
    sum.set(0, temp + a[i]);
         }
         i = i + 1;

    // Invariants after the loop
    assert(i <= N as usize);
    assert(a.len() == N);
    assert(i > 0 ==> sum[0] <= i);
    assert(forall |k:int| 0 <= k < N ==> a[k] == 1);
}
}
