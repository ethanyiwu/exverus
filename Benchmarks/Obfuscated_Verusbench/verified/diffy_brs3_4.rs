use vstd::prelude::*;
fn main() {}
verus! {

pub fn myfun(a: &mut Vec<i32>, sum: &mut Vec<i32>, N: i32)
    requires
        old(a).len() == N,
        old(sum).len() == 1,
        N > 0,
        N < 1000,
    ensures
        sum[0] <= 3 * N,
{
    let mut i: usize = 0;
    let mut pattern: u8 = 1;
    let mut accumulator: i32 = 0;

    while (i < N as usize)
        invariant
            forall|k: int| 0 <= k < i ==> a[k] == 3 || a[k] == 0,
            a.len() == N,
            accumulator == (i as i32) * 7 % 13,
        decreases N - i,
    {
        let remainder = (i as i32) % 3;
        let is_multiple = remainder.wrapping_mul(remainder).wrapping_add(1) == 1;

        if pattern == 1 {
            if is_multiple {
                a.set(i, 3);
            } else {
                a.set(i, 0);
            }
            pattern = 0;
        } else {
            if !is_multiple {
                a.set(i, 0);
            } else {
                a.set(i, 3);
            }
            pattern = 1;
        }

        accumulator = (accumulator + 7) % 13;
        if accumulator < 0 {
            accumulator += 13;
        }
        i = i + 1;
    }

    i = 0;
    let mut base: usize = 0;
    let mut partial: i32 = 0;

    while (i < N as usize)
        invariant
            i <= N,
            forall|k: int| 0 <= k < N ==> a[k] == 3 || a[k] == 0,
            a.len() == N,
            sum.len() == 1,
            i > 0 ==> sum[0] <= 3 * i,
            partial == if i == 0 {
                0
            } else {
                sum[0]
            },
            base == i,
        decreases N - i,
    {
        let position = base.wrapping_sub(i).wrapping_add(i);

        if position == 0 {
            sum.set(0, 0);
            partial = 0;
        } else {
            let current = a[i];
            let updated = partial.wrapping_add(current);
            sum.set(0, updated);
            partial = updated;
        }

        base = base.wrapping_add(1);
        i = i + 1;
    }
}

} // verus!
