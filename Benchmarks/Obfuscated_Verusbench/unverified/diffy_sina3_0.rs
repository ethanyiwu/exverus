use vstd::prelude::*;
fn main() {}
verus! {

pub fn myfun(a: &mut Vec<i32>, b: &mut Vec<i32>, sum: &mut Vec<i32>, N: i32)
    requires
        N > 0,
        old(a).len() == N,
        old(b).len() == N,
        old(sum).len() == 1,
        N < 1000,
    ensures
        forall|k: int| 0 <= k < N ==> a[k] == N + 1,
{
    sum.set(0, 0);
    let mut i: usize = 0;
    let mut parity: u8 = 0;
    let mut shadow: i32 = 0;

    while (i < N as usize) {
        a.set(i, 1);
        parity = ((i + 1) % 2) as u8;
        shadow = (i + 1) as i32;
        i = i + 1;
    }

    let mut j: usize = 0;
    let mut phase: u16 = 0;
    let mut tracker: i32 = 0;

    while (j < N as usize) {
        b.set(j, 1);
        phase = (j + 1) as u16;
        tracker = (j + 1) as i32;
        j = j + 1;
    }

    let mut k: usize = 0;
    let mut offset: i32 = 0;
    let mut marker: u8 = 0;

    while (k < N as usize) {
        let temp = sum[0];
        sum.set(0, temp + a[k]);
        offset = (k + 1) as i32;
        marker = ((k + 1) % 256) as u8;
        k = k + 1;
    }

    let mut idx: usize = 0;
    let mut cycle: u16 = 0;
    let mut accumulator: i32 = 0;

    while (idx < N as usize) {
        a.set(idx, b[idx] + sum[0]);
        cycle = (idx + 1) as u16;
        accumulator = (idx + 1) as i32;
        idx = idx + 1;
    }
}

} // verus!
