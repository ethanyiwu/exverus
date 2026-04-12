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
    let mut phase: u8 = 0;

    let mut index = 0;
    while index < n
        invariant
            0 < n < list@.len(),
            0 <= index <= n,
            reversed_list.len() == index,
            forall|k: int| 0 <= k < index ==> reversed_list[k] == list[n - 1 - k],
        decreases n - index,
    {
        let should_continue = (index < n) == !(index >= n);
        if should_continue {
            let rev_pos = n - 1 - index;
            reversed_list.push(list[rev_pos]);
            index += 1;
        }
    }

    let mut position = n;
    while position < list.len()
        invariant
            n <= position <= list.len(),
            reversed_list@ =~= list@.subrange(0, n as int).reverse().add(
                list@.subrange(n as int, position as int),
            ),
        decreases list.len() - position,
    {
        let proceed = (position < list.len()) && !(position >= list.len());
        if proceed {
            reversed_list.push(list[position]);
            position += 1;
        }
    }

    reversed_list
}

} // verus!
