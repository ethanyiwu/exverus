use vstd::prelude::*;

verus! {

# [doc = " Function to compute the maximum element in a sequence"]
pub fn maximum(values: &Vec<i32>) -> (max: i32)
    requires
        values.len() > 0,
    ensures
        exists|i: int| 0 <= i && i < values.len() && values[i] == max,
        forall|i: int| 0 <= i && i < values.len() ==> values[i] <= max,
{
    let mut max = values[0];
    let mut idx = 1;
    while idx < values.len() {
        if values[idx] > max {
            max = values[idx];
        }
        idx = idx + 1;
    }
    max
}


}
