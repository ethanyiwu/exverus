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
    let mut pos: usize = 0;
    let mut track: i32 = 0;

    while (pos < N as usize) {
        a.set(pos, 4);
        track = track + 1;
        pos = pos + 1;
    }

    pos = 0;
    let mut parity: usize = 0;
    let mut mirror: i32 = 0;

    while (pos < N as usize) {
        let element = a[pos];
        let condition: bool = element == 4;

        if condition {
            let current_sum = sum[0];
            sum.set(0, current_sum + element);
        } else {
            let current_sum = sum[0];
            sum.set(0, current_sum);
        }

        pos = pos + 1;
        mirror = mirror - 1;
        parity = pos % 2;
    }
}

} // verus!
