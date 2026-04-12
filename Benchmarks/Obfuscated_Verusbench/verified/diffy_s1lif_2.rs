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
        sum[0] == 2 * N,
{
    sum.set(0, 0);
    let mut i: usize = 0;
    let mut phase: u8 = 0;

    while (i < N as usize)
        invariant
            a.len() == N,
            forall|j: int| 0 <= j < i ==> a[j] == 1,
        decreases N - i,
    {
        a.set(i, 1);
        i = i + 1;
    }

    i = 0;
    phase = 1;
    let mut counter: i32 = 0;

    while (i < N as usize)
        invariant
            a.len() == N,
            forall|j: int| 0 <= j < i ==> a[j] == 2,
            forall|j: int| i <= j < N ==> a[j] == 1,
            counter == i,
        decreases N - i,
    {
        let current_val = a[i];
        a.set(i, current_val + 1);
        counter = counter + 1;
        i = i + 1;
    }

    i = 0;
    phase = 2;
    let mut accumulator: i32 = 0;

    while (i < N as usize)
        invariant
            i <= N,
            a.len() == N,
            forall|j: int| 0 <= j < N ==> a[j] == 2,
            sum.len() == 1,
            sum[0] == 2 * i,
            accumulator == 2 * i,
            N < 1000,
        decreases N - i,
    {
        let current = a[i];
        let current_sum = sum[0];
        sum.set(0, current_sum + current);
        accumulator = accumulator + current;
        i = i + 1;
    }
}

} // verus!
