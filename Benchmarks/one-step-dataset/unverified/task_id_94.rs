
use vstd::prelude::*;

fn main() {}

verus! {

#[verifier::loop_isolation(false)]
fn min_second_value_first(arr: &Vec<Vec<i32>>) -> (first_of_min_second: i32)
    requires
        arr.len() > 0,
        forall|i: int| 0 <= i < arr.len() ==> #[trigger] arr[i].len() >= 2,
    ensures
        exists|i: int|
            0 <= i < arr.len() && first_of_min_second == #[trigger] arr[i][0] && (forall|j: int|
                0 <= j < arr.len() ==> (arr[i][1] <= #[trigger] arr[j][1])),
{
    let mut min_second_index = 0;
    let mut index = 0;

    while index < arr.len()
        invariant
            arr.len() > 0,
            forall|i: int| 0 <= i < arr.len() ==> #[trigger] arr[i].len() >= 2,
            0 <= min_second_index < arr.len(),
            0 <= index <= arr.len(),
            min_second_index >= 0,
            index >= 0,
            forall|i: int| 0 <= i < index ==> #[trigger] arr[i].len() >= 2,
            arr[( min_second_index ) as int].len() >= 2,
            arr[min_second_index as int].len() >= 2,
            index < arr.len() ==> arr[( index ) as int].len() >= 2,
            min_second_index < arr.len() ==> arr[( min_second_index ) as int].len() >= 2,
        decreases
            arr.len() - index,
    {
        if arr[index][1] < arr[min_second_index][1] {
            min_second_index = index;
        }
        index += 1;
        proof {
            assert(forall|i: int| 0 <= i < arr.len() ==> #[trigger] arr[i].len() >= 2);
        } // Added by AI
    }
    arr[min_second_index][0]
}

} // verus!




//         if arr[index][1] < arr[min_second_index][1] {
// failed precondition
//         i < vec.view().len(),
//   failed precondition: i < vec.view().len()
//   None: arr[index][1]

// Compilation Error: False, Verified: 0, Errors: 1, Verus Errors: 1
// Safe: True