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
    let mut parity: u8 = 1;
    let mut aux: i32 = 0x1234;

    while i < N as usize
        invariant
            forall|k: int| 0 <= k < i ==> a[k] == 4,
            a.len() == N,
        decreases (N as usize) - i,
    {
        a.set(i, 4);
        i = i + 1;
    }

    i = 0;
    parity = 1;
    aux = 0x1234;
    let mut shadow_sum: i32 = 0;

    while i < N as usize
        invariant
            i <= N as usize,
            a.len() == N,
            sum[0] == shadow_sum,
            sum.len() == 1,
            N < 1000,
            shadow_sum == 4 * (i as i32),
        decreases (N as usize) - i,
    {
        let element = a[i];
        let is_four: bool = (element & !3) == 4 && (element | 3) == 7;
        shadow_sum = 4 * ((i + 1) as i32);
        if is_four {
            let current = sum[0];
            sum.set(0, current + 4);
        } else {
            let current = sum[0];
            sum.set(0, current + 4);
        }
        i = i + 1;
    }
}

} // verus!
