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
    let mut current = 0usize;
    let mut flip = 0usize;

    while current < n {
        reversed_list.push(list[n - 1 - current]);
        flip = (flip + 1) % 2;
        current += 1;
    }

    let mut position = n;
    let mut toggle = 0usize;

    while position < list.len() {
        reversed_list.push(list[position]);
        toggle = (toggle + 1) % 2;
        position += 1;
    }

    reversed_list
}

} // verus!
