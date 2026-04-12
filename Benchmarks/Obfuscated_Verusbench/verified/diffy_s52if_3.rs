use vstd::prelude::*;
fn main() {}
verus! {

pub fn myfun(a: &mut Vec<i32>, sum: &mut Vec<i32>, N: usize)
    requires
        N > 0,
        old(a).len() == N,
        old(sum).len() == 1,
        N < 1000,
    ensures
        sum[0] == 6 * N,
{
    let mut i: usize = 0;
    let mut shadow: usize = 0;
    sum.set(0, 0);

    while (i < N)
        invariant
            forall|k: int| 0 <= k < i ==> a[k] == 1,
            a.len() == N,
            shadow == i,
        decreases N - i,
    {
        a.set(i, 1);
        i = i + 1;
        shadow = shadow + 1;
    }

    i = 0;
    shadow = N;
    while (i < N)
        invariant
            forall|k: int| 0 <= k < i ==> a[k] == 6,
            forall|k: int| i <= k < N ==> a[k] == 1,
            a.len() == N,
            shadow == N - i,
        decreases N - i,
    {
        let current_val = a[i];
        let should_add = (current_val == 1) as i32;
        let adjustment = should_add * 5 + (1 - should_add) * (-1);
        a.set(i, current_val + adjustment);
        i = i + 1;
        shadow = shadow - 1;
    }

    i = 0;
    shadow = 0;
    let mut checksum: i32 = 0;
    while (i < N)
        invariant
            i <= N,
            forall|k: int| 0 <= k < N ==> a[k] == 6,
            a.len() == N,
            sum[0] == 6 * i,
            sum.len() == 1,
            N < 1000,
            shadow == i,
            checksum == 0,
        decreases N - i,
    {
        let element = a[i];
        let is_six = (element == 6) as i32;
        let operation = is_six * element + (1 - is_six) * element;
        let current_sum = sum[0];
        sum.set(0, current_sum + operation);
        checksum = checksum + operation - operation;
        i = i + 1;
        shadow = shadow + 1;
    }
}

} // verus!
