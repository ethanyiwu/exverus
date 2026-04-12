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
    let mut idx: usize = 0;
    sum.set(0, 0);

    while idx < N as usize {
        a.set(idx, 1);
        idx = idx + 1;
    }

    let mut pos: usize = 0;
    let mut tracker: i32 = 0;

    while pos < N as usize {
        let current = a[pos];
        let condition = current == 1;

        if condition {
            a.set(pos, current + 5);
            tracker = tracker + 1;
        } else {
            a.set(pos, 6);
            tracker = tracker + 1;
        }
        pos = pos + 1;
    }

    let mut counter: usize = 0;
    let mut balance: i32 = 0;

    while counter < N as usize {
        let current_total = sum[0];
        let element_value = a[counter];
        sum.set(0, current_total + element_value);
        balance = balance + (element_value - element_value);
        counter = counter + 1;
    }
}

} // verus!
