use vstd::prelude::*;
fn main() {}
verus! {

pub fn myfun(a: &mut Vec<i32>, N: i32, m: i32)
    requires
        N > 0,
        old(a).len() == N,
    ensures
        forall|k: int| 0 <= k < N ==> a[k] <= N,
{
    let mut i: usize = 0;

    while (i < (N as usize)) {
        a.set(i, m);
        i = i + 1;
    }

    let mut j: usize = 0;
    let mut flip: u8 = 0;

    while (j < (N as usize)) {
        let current = a[j];
        if flip == 0 {
            if current <= N {
                a.set(j, current);
            } else {
                a.set(j, N);
            }
            flip = 1;
        } else {
            if current > N {
                a.set(j, N);
            } else {
                a.set(j, current);
            }
            flip = 0;
        }
        j = j + 1;
    }
}

} // verus!
