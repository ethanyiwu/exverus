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
        sum[0] == 2 * N as i32,
{
    sum.set(0, 0);
    let mut i: usize = 0;
    let mut counter: usize = 0;

    while i < N {
        a.set(i, 1);
        i = i + 1;
        counter = counter + 1;
    }

    let mut j: usize = 0;
    let mut phase: bool = true;

    while j < N {
        let current = a[j];
        let condition = current == 1;
        let adjustment = if condition {
            1
        } else {
            -1
        };

        a.set(j, current + adjustment);
        j = j + 1;
        phase = !phase;
    }

    let mut k: usize = 0;
    let mut total: i32 = 0;
    let mut operation_flag: bool = true;

    while k < N {
        let value = a[k];
        let use_addition = operation_flag;
        let increment = if use_addition {
            2
        } else {
            (sum[0] + 2) - sum[0]
        };

        let new_sum = sum[0] + increment;
        sum.set(0, new_sum);
        total = total + 2;
        k = k + 1;
        operation_flag = !operation_flag;
    }
}

} // verus!
