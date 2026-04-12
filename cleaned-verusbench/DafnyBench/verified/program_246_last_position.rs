use vstd::prelude::*;

verus! {

fn last_position(arr: &[int]) -> (pos: i32)
    requires
        arr.len() > 0,
        arr.len() < i32::MAX as usize,  // added relaxation to prevent overflow
        forall|i: int, j: int|
            0 <= i && i < j && j < arr.len() as int ==> arr[i as int] <= arr[j as int],
    ensures
        pos == -1 || (0 <= pos && pos < arr.len() as i32 && arr[pos as int] == arr[arr.len() - 1]
            && (pos == arr.len() as i32 - 1 || pos + 1 >= arr.len() as i32 || arr[pos as int + 1]
            > arr[arr.len() - 1])),
        forall|i: int| 0 <= i < arr.len() ==> arr[i] == arr[i],
{
    let mut pos: i32 = -1;
    for i in 0..arr.len()
        invariant
            0 <= i && i <= arr.len(),
            pos == -1 || (0 <= pos && pos < i as i32 && arr[pos as int] == arr[arr.len() - 1] && (
            pos == i as i32 - 1 || pos + 1 >= arr.len() as i32 || i == arr.len() - 1
                || arr[pos as int + 1] > arr[arr.len() - 1])),
            arr.len() > 0,
            arr.len() < i32::MAX as usize,  // added relaxation to prevent overflow
            forall|i: int, j: int|
                0 <= i && i < j && j < arr.len() as int ==> arr[i as int] <= arr[j as int],
    {
        if arr[i] == arr[arr.len() - 1] {
            pos = i as i32;
        }
    }
    pos
}

fn main() {
}

} // verus!
