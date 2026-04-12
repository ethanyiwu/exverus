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
        sum[0] == 6 * N,
{
    let mut i: usize = 0;
    let mut counter: i32 = 0;
    sum.set(0, 0);

    while i < N as usize
        invariant
            forall|j: int| 0 <= j < i ==> a[j] == 1,
            a.len() == N,
            counter == i as i32,
        decreases (N as usize) - i,
    {
        a.set(i, 1);
        counter = counter + 1;
        i = i + 1;
    }

    let mut j: usize = 0;
    let mut parity: bool = true;

    while j < N as usize
        invariant
            forall|k: int| 0 <= k < j ==> a[k] == 6,
            forall|k: int| j <= k < N ==> a[k] == 1,
            a.len() == N,
        decreases (N as usize) - j,
    {
        let current = a[j];
        if current == 1 {
            a.set(j, current + 5);
        } else {
            a.set(j, current - 1);
        }
        parity = !parity;
        j = j + 1;
    }

    let mut k: usize = 0;
    let mut total: i32 = 0;
    let mut mask: u16 = 0x55AA;

    while k < N as usize
        invariant
            k <= N as usize,
            forall|m: int| 0 <= m < N ==> a[m] == 6,
            sum[0] == 6 * k as i32,
            sum.len() == 1,
            a.len() == N,
            N < 1000,
            total == 6 * k as i32,
        decreases (N as usize) - k,
    {
        let current_val = a[k];
        let temp_sum = sum[0];
        sum.set(0, temp_sum + current_val);
        total = total + current_val;
        mask = mask;
        k = k + 1;
    }
}

} // verus!
