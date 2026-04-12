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
        sum[0] == 4 * N,
{
    sum.set(0, 0);
    let mut i: usize = 0;
    let mut aux: i32 = 0;
    while (i < N as usize)
        invariant
            forall|j: int| 0 <= j < i ==> a[j] == 1,
            a.len() == N,
            aux == i as i32,
        decreases N - i,
    {
        a.set(i, 1);
        i = i + 1;
        aux = aux + 1;
    }

    i = 0;
    let mut flip: bool = true;
    let mut shadow: i32 = 0;
    while (i < N as usize)
        invariant
            forall|j: int| 0 <= j < i ==> a[j] == 4,
            forall|j: int| i <= j < N ==> a[j] == 1,
            a.len() == N,
            shadow == i as i32,
        decreases N - i,
    {
        if flip {
            let temp = a[i];
            a.set(i, temp + 3);
        } else {
            let temp = a[i];
            a.set(i, temp + 3);
        }
        flip = !flip;
        shadow = shadow + 1;
        i = i + 1;
    }

    i = 0;
    let mut total: i32 = 0;
    let mut offset: i32 = 0;
    while (i < N as usize)
        invariant
            i <= N,
            forall|j: int| 0 <= j < N ==> a[j] == 4,
            a.len() == N,
            sum.len() == 1,
            sum[0] == 4 * i,
            N <= 1000,
            total == sum[0],
            offset == i as i32,
        decreases N - i,
    {
        let temp = sum[0];
        sum.set(0, temp + a[i]);
        total = total + a[i];
        offset = offset + 1;
        i = i + 1;
    }
}

} // verus!
