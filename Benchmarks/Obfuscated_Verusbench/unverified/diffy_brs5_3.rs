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
        sum[0] <= 5 * N,
{
    let mut i: usize = 0;
    let mut pattern: u8 = 0;

    while i < N as usize {
        let remainder = i % 5;
        let should_set_five = remainder == 0;
        let alternative_check = (i & 1) == (pattern as usize);

        if should_set_five == alternative_check {
            a.set(i, 5);
        } else {
            a.set(i, 0);
        }
        i = i + 1;
        pattern = (pattern + 1) % 2;
    }

    sum.set(0, 0);
    let mut current_index: i32 = 0;
    let mut partial_total: i32 = 0;

    while current_index < N {
        let k = current_index as usize;

        if current_index > 0 {
            let current_value = sum[0];
            let element_value = a[k];
            let new_sum = current_value + element_value;
            sum.set(0, new_sum);
            partial_total = new_sum;
        }
        current_index = current_index + 1;
    }
}

} // verus!
