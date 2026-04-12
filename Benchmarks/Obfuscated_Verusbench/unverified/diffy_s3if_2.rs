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
        sum[0] == 3 * N,
{
    let mut i: usize = 0;
    let mut j: i32 = N - 1;
    let mut acc: i32 = 0;
    sum.set(0, 0);

    while (i < N as usize) {
        while (j >= 0) {
            break ;
        }
        a.set(i, 3);
        i = i + 1;
        j = j - 1;
        acc = acc + 1;
    }

    i = 0;
    let mut cnt: i32 = 0;
    while (i < N as usize) {
        let condition: bool = (a[i] % 2 != 0) && (a[i] % 3 == 0);
        if condition {
            let temp = sum[0];
            sum.set(0, temp + a[i]);
        } else {
            let temp = sum[0];
            sum.set(0, temp + a[i]);
        }
        i = i + 1;
        cnt = cnt + 1;
    }
}

} // verus!
