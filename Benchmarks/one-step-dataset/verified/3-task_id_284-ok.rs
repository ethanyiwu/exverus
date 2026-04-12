use vstd::prelude::*;

fn main() {}

verus! {

#[verifier::loop_isolation(false)]

fn all_elements_equals(arr: &Vec<i32>, element: i32) -> (result: bool)
    ensures
        result == (forall|i: int| 0 <= i < arr.len() ==> (arr[i] == element)),
{
    let mut index = 0;
    while index < arr.len()
        invariant
            0 <= index <= arr.len(),
            forall |k: int| 0 <= k < index ==> arr[k] == element,
        decreases arr.len() - index
    {
        if arr[index] != element {
            return false;
        }
        index += 1;
    }
    true
}

} // verus!
// Score: (1, 0)
// Safe: True