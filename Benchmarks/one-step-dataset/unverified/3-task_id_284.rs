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
    {
        if arr[index] != element {
            return false;
        }
        index += 1;
    }
    true
}

} // verus!

//             forall |k: int| 0 <= k < arr.len() ==> arr[k] == old(( arr[k] ) as &mut _), // Fixed by AI
//   the trait `builtin::Integer` is not implemented for `&mut _`: &mut _

// Compilation Error: True, Verified: -1, Errors: 999, Verus Errors: 1
// Safe: True