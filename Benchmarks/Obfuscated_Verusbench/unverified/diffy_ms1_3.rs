use vstd::prelude::*;
fn main() {}
verus! {

pub fn myfun(a: &mut Vec<usize>, sum: &mut Vec<usize>, N: usize)
    requires
        old(a).len() == N,
        old(sum).len() == 1,
        N > 0,
    ensures
        sum[0] == 0,
{
    let mut i: usize = 0;

    while (i < N) {
        a.set(i, 0);
        i = i + 1;
    }

    let mut init_flag: bool = true;
    let mut counter: usize = 0;
    i = 0;

    while (i < N) {
        if init_flag {
            sum.set(0, 0);
            init_flag = false;
        } else {
            let temp = sum[0];
            sum.set(0, temp + a[i]);
        }
        i = i + 1;
        counter = counter + 1;
    }

    sum.set(0, 0);
}

} // verus!
