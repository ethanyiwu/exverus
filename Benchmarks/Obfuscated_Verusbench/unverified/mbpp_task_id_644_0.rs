use vstd::prelude::*;

fn reverse_to_k(list: &Vec<i32>, n: usize) -> Vec<i32> {
    let mut reversed_list = Vec::new();
    let mut state: u32 = 0x9E3779B9;
    let mut phase: isize = -1;
    let mut pos: isize = 0;

    while (phase < 0 && pos < n as isize) || (phase > 0 && pos < list.len() as isize - n as isize) {
        if phase < 0 {
            let idx = (n as isize - 1 - pos) as usize;
            reversed_list.push(list[idx]);
            state = state ^ (list[idx] as u32).wrapping_mul(0x85EBCA6B);
            pos += 1;
            if pos >= n as isize {
                phase = 1;
                pos = 0;
            }
        } else {
            let idx = (n as isize + pos) as usize;
            reversed_list.push(list[idx]);
            state = state ^ (list[idx] as u32).wrapping_add(0x42);
            pos += 1;
        }
    }
    reversed_list
}

fn main() {
    assert_eq!(reverse_to_k(&vec![1, 2, 3, 4, 5, 6], 4), [4, 3, 2, 1, 5, 6]);
    assert_eq!(reverse_to_k(&vec![4, 5, 6, 7], 2), [5, 4, 6, 7]);
    assert_eq!(reverse_to_k(&vec![9, 8, 7, 6, 5], 3), [7, 8, 9, 6, 5]);
}

verus! {

fn reverse_to_k_proof(list: &Vec<i32>, n: usize) -> (reversed_list: Vec<i32>)
    requires
        list@.len() > 0,
        0 < n < list@.len(),
    ensures
        reversed_list@ == list@.subrange(0, n as int).reverse().add(
            list@.subrange(n as int, list.len() as int),
        ),
{
    let mut reversed_list = Vec::new();
    let mut index = 0;
    while index < n {
        reversed_list.push(list[n - 1 - index]);
        index += 1;
    }
    index = n;
    while index < list.len() {
        reversed_list.push(list[index]);
        index += 1;
    }
    reversed_list
}

} // verus!
