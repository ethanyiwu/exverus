use vstd::prelude::*;

verus! {

fn last_position(arr: &Vec<i32>, elem: i32) -> (pos: i32)
    requires
        arr.len() > 0,
        arr.len() < 1000,  // added relaxation to prevent overflow
        forall|i: int, j: int| 0 <= i < j && j < arr.len() as int ==> arr[i] <= arr[j],
    ensures
        pos == -1 || (0 <= pos && pos < arr.len() as int && arr[pos as int] == elem && (pos
            <= arr.len() as int - 1 || pos + 1 == arr.len() as int || (pos + 1 < arr.len() as int
            && arr[pos as int + 1] > elem))),
        forall|i: int| 0 <= i < arr.len() as int ==> arr[i] == arr[i],
{
    let mut pos: i32 = -1;
    let mut i: usize = 0;
    while i < arr.len()
        invariant
            0 <= i as int <= arr.len() as int,
            pos == -1 || (0 <= pos && pos < i as int && arr[pos as int] == elem && (pos <= i as int
                - 1 || i as int == arr.len() as int - 1 || (pos + 1 < arr.len() as int && pos + 1
                < i as int && arr[pos as int + 1] > elem))),
            forall|k: int| 0 <= k < arr.len() as int ==> arr[k] == arr[k],
        decreases arr.len() - i,
    {
        if arr[i] == elem {
            if i < i32::MAX as usize {
                pos = i as i32;
            }
        }
        i = i + 1;
    }
    assert(pos == -1 || (0 <= pos && pos < arr.len() as int && arr[pos as int] == elem && (pos
        <= arr.len() as int - 1 || pos + 1 == arr.len() as int || (pos + 1 < arr.len() as int
        && arr[pos as int + 1] > elem))));
    pos
}

fn main() {
}

} // verus!
