use vstd::prelude::*;

verus! {

fn last_position(arr: &[i32], elem: i32) -> (pos: i32)
    requires
        arr.len() > 0,
        arr.len() < i32::MAX as usize,
        forall|i: int, j: int| 0 <= i && i < j && j < arr.len() as int ==> arr[i] <= arr[j],
    ensures
        pos == -1 || (0 <= pos && pos < arr.len() as i32 && arr[pos as int] == elem && (pos
            == arr.len() as i32 - 1 || arr[(pos + 1) as int] > elem)),
        forall|i: int| 0 <= i && i < arr.len() ==> arr[i] == arr[i],
{
    let mut pos = -1;
    for i in 0..arr.len() {
        if arr[i] == elem {
            pos = i as i32;
        }
    }
    pos
}


}
