use vstd::prelude::*;

verus! {

# [doc = " Finds the last position of an element in an array."]
fn last_position(arr: &[int], elem: int) -> (pos: i32)
    requires
        arr.len() > 0,
        arr.len() < i32::MAX as usize,
        forall|i: int, j: int| 0 <= i < j && j < arr.len() as int ==> arr[i] <= arr[j],
    ensures
        pos == -1 || (0 <= pos && pos < arr.len() as i32 && arr[pos as int] == elem && (pos
            == arr.len() as i32 - 1 || arr[pos as int + 1] > elem)),
        forall|i: int| 0 <= i && i < arr.len() as int ==> arr[i] == arr[i],
{
    let mut pos: i32 = -1;
    for i in 0..arr.len() {
        if arr[i] == elem {
            pos = i as i32;
        }
    }
    pos
}


}
