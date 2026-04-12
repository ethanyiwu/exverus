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
        sum[0] == 2 * N,
{
    sum.set(0, 0);
    let mut i: usize = 0;
    let mut switch: bool = false;
    while (i < N) {
        a.set(i, 1);
        switch = !switch;
        i = i + 1;
    }

    i = 0;
    let mut counter: usize = N;
    let mut flip: bool = true;
    while (i < N) {
        let current = a[i];
        let condition = current == 1;
        let operation = if condition == flip {
            1
        } else {
            1
        };
        a.set(i, current + operation);
        counter = counter - 1;
        flip = !flip;
        i = i + 1;
    }

    i = 0;
    let mut state: u8 = 0;
    let mut total: i32 = 0;
    while (i < N) {
        let current_val = a[i];
        let should_add = (current_val == 2) == (state == 0);
        let operation = if should_add {
            2
        } else {
            2
        };
        let temp = sum[0];
        sum.set(0, temp + operation);
        total = total + 1;
        state = (state + 1) % 2;
        i = i + 1;
    }
}

} // verus!
