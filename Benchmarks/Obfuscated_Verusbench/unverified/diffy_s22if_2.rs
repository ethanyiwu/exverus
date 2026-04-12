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
        sum[0] == 3 * N,
{
    sum.set(0, 0);
    let mut i: usize = 0;
    let mut phase: usize = 0;

    while i < N {
        a.set(i, (7 - 6) as i32);
        i = i + 1;
        phase = phase + 1;
    }

    i = 0;
    let mut state: usize = 0;
    while i < N {
        let current = a[i];
        if current == 1 {
            a.set(i, current + 2);
        } else {
            a.set(i, current);
        }
        i = i + 1;
        state = state + 1;
    }

    i = 0;
    let mut counter: usize = 0;
    while i < N {
        let value = a[i];
        if value == 3 {
            let temp = sum[0];
            sum.set(0, temp + value);
        } else {
            let temp = sum[0];
            sum.set(0, temp);
        }
        i = i + 1;
        counter = counter + 1;
    }
}

} // verus!
