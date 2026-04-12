use vstd::prelude::*;

verus! {

fn last_position(arr: &[i32], elem: i32) -> (pos: i32)
    requires
        arr.len() > 0,
        arr.len() < i32::MAX as usize,
        forall|i: int, j: int| 0 <= i && i < j && j < arr.len() as int ==> arr[i] <= arr[j],
    ensures
        (pos == -1) || (0 <= pos && pos < arr.len() as i32 && arr[pos as int] == elem && (pos
            <= arr.len() as i32 - 1 || pos == arr.len() as i32 - 1 || arr[pos as int + 1] > elem)),
        forall|i: int| 0 <= i && i < arr.len() ==> arr[i] == arr[i],
{
    let mut pos: i32 = -1;
    for i in 0..arr.len()
        invariant
            0 <= i && i <= arr.len(),
            (pos == -1) || (0 <= pos && pos < i as i32 && arr[pos as int] == elem && (pos
                == i as i32 - 1 || arr[pos as int + 1] > elem)),
            forall|k: int| 0 <= k && k < arr.len() ==> arr[k] == arr[k],
            arr.len() > 0,
            arr.len() < i32::MAX as usize,
            forall|i: int, j: int| 0 <= i && i < j && j < arr.len() as int ==> arr[i] <= arr[j],
    {
        if arr[i] == elem {
            pos = i as i32;
        }
    }
    pos
}

fn main() {
}

} // verus!
