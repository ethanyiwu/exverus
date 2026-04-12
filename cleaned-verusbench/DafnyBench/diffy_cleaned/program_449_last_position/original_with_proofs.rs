use vstd::prelude::*;

verus! {

fn last_position(arr: &[int], elem: int) -> (pos: i32)
    requires
        arr.len() > 0,
        arr.len() < i32::MAX as usize,
        forall|i: int, j: int| 0 <= i < j && j < arr.len() as int ==> arr[i as int] <= arr[j as int],
    ensures
        pos == -1 || (0 <= pos && pos < arr.len() as i32 && arr[pos as int] == elem && (pos <= arr.len() as i32 - 1 || pos == arr.len() as i32 - 1 || arr[pos as int + 1] > elem)),
        forall|i: int| 0 <= i && i < arr.len() ==> arr[i as int] == arr[i as int],
{
    let mut pos: i32 = -1;
    for i in 0..arr.len()
        invariant
            0 <= i && i <= arr.len(),
            pos == -1 || (0 <= pos && pos < i && arr[pos as int] == elem && (pos == i - 1 || pos == i || pos == arr.len() as i32 - 1 || arr[pos as int + 1] > elem)),
            arr.len() > 0,
            arr.len() < i32::MAX as usize,
            forall|i: int, j: int| 0 <= i < j && j < arr.len() as int ==> arr[i as int] <= arr[j as int],
    {
        if arr[i] == elem {
            pos = i as i32;
        }
    }
    pos
}

fn main() {}

} // verus!