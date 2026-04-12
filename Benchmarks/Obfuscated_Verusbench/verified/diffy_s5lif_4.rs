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
        sum[0] == 6 * N,
{
    let mut counter: i32 = 0;
    let mut offset: i32 = -1;
    sum.set(0, 0);

    while (counter < N)
        invariant
            forall|j: int| 0 <= j < counter ==> a[j] == 1,
            a.len() == N,
            counter >= 0,
        decreases (N - counter) as nat,
    {
        a.set(counter as usize, 1);
        counter = counter + 1;
        offset = counter - 1;
    }

    counter = 0;
    offset = -1;
    while (counter < N)
        invariant
            forall|j: int| 0 <= j < counter ==> a[j] == 6,
            forall|j: int| counter <= j < N ==> a[j] == 1,
            a.len() == N,
            counter >= 0,
        decreases (N - counter) as nat,
    {
        let idx = counter as usize;
        if a[idx] == 1 {
            let temp = a[idx];
            a.set(idx, temp + 5);
        } else {
            let temp = a[idx];
            a.set(idx, temp - 1);
        }
        counter = counter + 1;
        offset = counter - 1;
    }

    let mut i: usize = 0;
    while (i < N as usize)
        invariant
            i <= N as usize,
            forall|j: int| 0 <= j < N ==> a[j] == 6,
            sum[0] == 6 * (i as int),
            sum.len() == 1,
            a.len() == N,
            N < 1000,
        decreases (N as usize - i),
    {
        let temp = sum[0];
        sum.set(0, temp + a[i]);
        i = i + 1;
    }
}

} // verus!
