use vstd::prelude::*;
fn main() {
    assert_eq!(reverse_to_k(&vec![1, 2, 3, 4, 5, 6], 4), [4, 3, 2, 1, 5, 6]);
    assert_eq!(reverse_to_k(&vec![4, 5, 6, 7], 2), [5, 4, 6, 7]);
    assert_eq!(reverse_to_k(&vec![9, 8, 7, 6, 5], 3), [7, 8, 9, 6, 5]);
}

verus! {

fn reverse_to_k(list: &Vec<i32>, n: usize) -> (reversed_list: Vec<i32>)
    requires
        list@.len() > 0,
        0 < n < list@.len(),
    ensures
        reversed_list@ == list@.subrange(0, n as int).reverse().add(
            list@.subrange(n as int, list.len() as int),
        ),
{
    let mut reversed_list = Vec::new();
    let mut forward_idx = 0;
    let mut reverse_idx = n;

    while forward_idx < n {
        reverse_idx = reverse_idx - 1;
        reversed_list.push(list[reverse_idx]);
        forward_idx = forward_idx + 1;
    }

    let mut index = n;
    while index < list.len() {
        reversed_list.push(list[index]);
        index = index + 1;
    }
    reversed_list
}

} // verus!
