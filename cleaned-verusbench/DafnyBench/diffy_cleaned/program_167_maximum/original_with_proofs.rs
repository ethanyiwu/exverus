use vstd::prelude::*;

verus! {

/// Function to compute the maximum element in a sequence
pub fn maximum(values: &Vec<i32>) -> (max: i32)
    requires
        values.len() > 0,
    ensures
        exists|i: int| 0 <= i && i < values.len() && values[i] == max,
        forall|i: int| 0 <= i && i < values.len() ==> values[i] <= max,
{
    let mut max = values[0];
    let mut idx = 1;
    while idx < values.len()
        invariant
            exists|i: int| 0 <= i && i < values.len() && values[i] == max,
            idx <= values.len(),
            forall|j: int| 0 <= j && j < idx ==> values[j] <= max,
        decreases values.len() - idx,
    {
        if values[idx] > max {
            max = values[idx];
        }
        idx = idx + 1;
    }
    max
}

/// Lemma to prove the uniqueness of the maximum element
proof fn maximum_is_unique(values: &Vec<i32>, m1: i32, m2: i32)
    requires
        exists|i: int| 0 <= i && i < values.len() && values[i] == m1,
        forall|i: int| 0 <= i && i < values.len() ==> values[i] <= m1,
        exists|i: int| 0 <= i && i < values.len() && values[i] == m2,
        forall|i: int| 0 <= i && i < values.len() ==> values[i] <= m2,
    ensures
        m1 == m2,
{
    assert(m1 == m2);
}

fn main() {}

} // verus!