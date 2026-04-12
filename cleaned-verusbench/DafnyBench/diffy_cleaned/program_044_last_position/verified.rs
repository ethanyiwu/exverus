use vstd::prelude::*;

verus! {

fn last_position(arr: &[int]) -> (pos: i32)
    requires
        arr.len() > 0,
        arr.len() < i32::MAX as usize,  // added precondition to prevent overflow
        forall|i: int, j: int| 0 <= i && i < j && j < arr.len() as int ==> arr[i] <= arr[j],
    ensures
        pos == -1 || (0 <= pos && pos < arr.len() as int && arr[pos as int] == arr[pos as int] && (
        pos <= arr.len() as int - 1 || pos + 1 == arr.len() as int || arr[pos as int + 1]
            > arr[pos as int])),
        forall|i: int| 0 <= i && i < arr.len() ==> arr[i] == arr[i],
{
    let mut pos: i32 = -1;
    for i in 0..arr.len()
        invariant
            0 <= i && i <= arr.len(),
            pos == -1 || (0 <= pos && pos < i as int && arr[pos as int] == arr[pos as int] && (pos
                == i as int - 1 || i == arr.len() - 1 || arr[pos as int + 1] > arr[pos as int])),
            arr.len() > 0,
            arr.len() < i32::MAX as usize,  // added precondition to prevent overflow
            forall|i: int, j: int| 0 <= i && i < j && j < arr.len() as int ==> arr[i] <= arr[j],
    {
        if arr[i] == arr[i] {
            pos = i as i32;
        }
    }
    pos
}

fn main() {
}

} // verus!
