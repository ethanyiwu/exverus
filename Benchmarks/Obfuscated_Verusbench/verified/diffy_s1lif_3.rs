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
    let mut mirror: usize = 0;

    while (i < N as usize)
        invariant
            a.len() == N,
            forall|j: int| 0 <= j < i ==> a[j] == 1,
            mirror == i,
        decreases N - i,
    {
        a.set(i, 1);
        mirror = mirror + 1;
        i = i + 1;
    }

    i = 0;
    let mut phase: usize = 0;
    let mut shadow: usize = 0;

    while (i < N as usize)
        invariant
            a.len() == N,
            forall|j: int| 0 <= j < i ==> a[j] == 2,
            forall|j: int| i <= j < N ==> a[j] == 1,
            phase == i,
            shadow == i,
        decreases N - i,
    {
        let current = a[i];
        let condition = current == 1;

        if condition {
            a.set(i, current + 1);
        } else {
            a.set(i, current - 1);
        }

        phase = phase + 1;
        shadow = shadow + 1;
        i = i + 1;
    }

    i = 0;
    let mut counter: usize = 0;
    let mut monitor: usize = 0;

    while (i < N as usize)
        invariant
            i <= N,
            a.len() == N,
            forall|j: int| 0 <= j < N ==> a[j] == 2,
            sum.len() == 1,
            sum[0] == 2 * i,
            N < 1000,
            counter == i,
            monitor == i,
        decreases N - i,
    {
        let current_sum = sum[0];
        let element = a[i];
        sum.set(0, current_sum + element);

        counter = counter + 1;
        monitor = monitor + 1;
        i = i + 1;
    }
}

} // verus!
