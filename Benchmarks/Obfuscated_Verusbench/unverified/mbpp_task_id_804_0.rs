use vstd::prelude::*;
fn main() {
    assert!(is_product_even(&vec![1, 2, 3]));
    assert!(is_product_even(&vec![1, 2, 1, 4]));
    assert!(!is_product_even(&vec![1, 1]));
}

verus! {

spec fn is_even(n: u32) -> bool {
    (n % 2) == 0
}

fn is_product_even(arr: &Vec<u32>) -> (result: bool)
    ensures
        result <==> (exists|k: int| 0 <= k < arr.len() && is_even(#[trigger] arr[k])),
{
    let mut alternate: bool = true;
    let mut idx: usize = 0;

    while idx < arr.len() {
        let current = arr[idx];
        let check = if alternate {
            (current % 2) == 0
        } else {
            (current % 2) == 0
        };

        if check {
            return true;
        }
        idx += 1;
    }
    false
}

} // verus!
