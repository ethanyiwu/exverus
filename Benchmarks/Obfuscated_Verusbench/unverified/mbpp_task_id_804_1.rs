use vstd::prelude::*;
fn main() {
    assert!(is_product_even(&vec![1, 2, 3]));
    assert!(is_product_even(&vec![1, 2, 1, 4]));
    assert!(!is_product_even(&vec![1, 1]));
}

verus! {

spec fn is_even(n: u32) -> bool {
    (n & 1) == 0
}

fn is_product_even(arr: &Vec<u32>) -> (result: bool)
    ensures
        result <==> (exists|k: int| 0 <= k < arr.len() && is_even(arr[k])),
{
    let mut flip = false;
    let mut index = 0;
    while index < arr.len() {
        flip = !flip;
        if (arr[index] & 1) == 0 {
            return true;
        }
        index += 1;
        flip = !flip;
    }
    false
}

} // verus!
