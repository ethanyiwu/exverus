
use vstd::prelude::*;
fn main()  {}

verus! {

#[verifier::loop_isolation(false)]

pub fn myfun(a: &mut Vec<i32>, sum: &mut Vec<i32>, N: i32) 
    requires 
        old(a).len() == N,
        old(sum).len() == 1,
        N > 0,
        N < 1000,
    ensures
        sum[0] <= 2 * N,
{
    let mut i: usize = 0;
    while (i < N as usize)
    invariant
        N > 0,
        N < 1000,
        a.len() == N,
        sum.len() == 1, // Add this invariant here
    decreases
        N as usize - i,
    {
        if (i % 2 == 0) {
            a.set(i, 2);
        } else {
            a.set(i, 0);
        }
        i = i + 1;
    }

    i = 0;
    
    while (i < N as usize)
    invariant
        N > 0,
        N < 1000,
        a.len() == N,
        sum.len() == 1,
        forall |k: int| 0 <= k < N ==> old(a)[k as int] == a[k as int],
        sum[0] <= 2 * i as i32, // Ensuring invariant based on array setup
    decreases
        N as usize - i,
    {
        if (i == 0) {
            sum.set(0, 0);
        } else {
            let temp = sum[0];
            assert((temp + a[( i ) as int]) <= 2 * N); // Assertion before operation
            sum.set(0, temp + a[i]);
        }
        i = i + 1;
    }
}

pub fn myfun_while1(a: &mut Vec<i32>, sum: &mut Vec<i32>, N: i32) 
    requires 
        old(a).len() == N,
        old(sum).len() == 1,
        N > 0,
        N < 1000,
{

    let mut i: usize = 0;
        // place to add variables assignment. [1]
    let (mut a, mut sum, mut N, mut i) = (vec![1], vec![1], N, i);

    // Loop condition
    assume((i < N as usize));
    // Invariants before the loop
    assume(N > 0);
    assume(N < 1000);
    assume(a.len() == N);
    assume(sum.len() == 1);

    if (i % 2 == 0) {
        a.set(i, 2);
    } else {
        a.set(i, 0);
    }
    i = i + 1;

    // Invariants after the loop
    assert(N > 0);
    assert(N < 1000);
    assert(a.len() == N);
    assert(sum.len() == 1);
}

pub fn myfun_while2(a: &mut Vec<i32>, sum: &mut Vec<i32>, N: i32) 
    requires 
        old(a).len() == N,
        old(sum).len() == 1,
        N > 0,
        N < 1000,
{

    let mut i: usize = 0;
    while (i < N as usize)
    invariant
        N > 0,
        N < 1000,
        a.len() == N,
        sum.len() == 1, // Add this invariant here
    decreases
        N as usize - i,
    {
        if (i % 2 == 0) {
            a.set(i, 2);
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
    assume(N > 0);
    assume(N < 1000);
    assume(a.len() == N);
    assume(sum.len() == 1);
    assume(forall |k: int| 0 <= k < N ==> old(a)[k as int] == a[k as int]);
    assume(sum[0] <= 2 * i as i32);

    if (i == 0) {
        sum.set(0, 0);
    } else {
        let temp = sum[0];
        assert((temp + a[( i ) as int]) <= 2 * N); // Assertion before operation
        sum.set(0, temp + a[i]);
    }
    i = i + 1;

    // Invariants after the loop
    assert(N > 0);
    assert(N < 1000);
    assert(a.len() == N);
    assert(sum.len() == 1);
    assert(forall |k: int| 0 <= k < N ==> old(a)[k as int] == a[k as int]);
    assert(sum[0] <= 2 * i as i32);
}
}

// Score: (0, 2)
// Safe: True