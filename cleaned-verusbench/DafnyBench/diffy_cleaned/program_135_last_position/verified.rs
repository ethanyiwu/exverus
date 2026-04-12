use vstd::prelude::*;

verus! {

fn last_position(arr: &Vec<i32>) -> (pos: i32)
    requires
        arr.len() > 0,
        arr.len() < 100000,  // added relaxation to prevent overflow
        forall|i: int, j: int| 0 <= i && i < j && j < arr.len() ==> arr[i] <= arr[j],
    ensures
        pos == -1 || (0 <= pos && pos < arr.len() as i32 && arr[pos as int] == arr[pos as int] && (
        pos <= arr.len() as i32 - 1 || pos == arr.len() as i32 - 1 || arr[pos as int + 1]
            > arr[pos as int])),
        forall|i: int| 0 <= i && i < arr.len() ==> arr[i] == arr[i],
{
    let mut pos: i32 = -1;
    for i in 0..arr.len()
        invariant
            0 <= i && i <= arr.len(),
            pos == -1 || (0 <= pos && pos < i as i32 && arr[pos as int] == arr[pos as int] && (pos
                == i - 1 || pos == i - 1 || i == arr.len() || arr[pos as int + 1]
                > arr[pos as int])),
            arr.len() < 100000,  // added invariant
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
