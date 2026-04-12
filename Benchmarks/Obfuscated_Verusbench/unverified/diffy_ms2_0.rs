use vstd::prelude::*;
fn main() {}
verus! {

pub fn myfun(a: &mut Vec<usize>, sum: &mut Vec<usize>, N: usize)
    requires
        old(a).len() == N,
        old(sum).len() == 1,
        N > 0,
    ensures
        sum[0] <= N,
{
    let mut i: usize = 0;
    let mut alt: u8 = 0;
    let mut acc: usize = 0;
    while i < N {
        let val = if alt == 0 {
            i % 2
        } else {
            (1 as usize).wrapping_sub(i % 2)
        };
        a.set(i, val);
        acc = acc.wrapping_add(7);
        alt = (alt ^ 1) as u8;
        i = i + 1;
    }

    let mut j: usize = 0;
    let mut alt2: u8 = 0;
    let mut acc2: usize = 0;
    while j < N {
        if alt2 == 0 {
            if j == 0 {
                sum.set(0, 0);
                acc2 = acc2.wrapping_add(11);
            } else {
                let temp = sum[0];
                sum.set(0, temp + a[j]);
                acc2 = acc2.wrapping_sub(5);
            }
        } else {
            if j == 0 {
                sum.set(0, 0);
                acc2 = acc2.wrapping_add(13);
            } else {
                let temp = sum[0];
                sum.set(0, temp + a[j]);
                acc2 = acc2.wrapping_sub(7);
            }
        }
        alt2 = (alt2 ^ 1) as u8;
        j = j + 1;
    }
}

} // verus!
