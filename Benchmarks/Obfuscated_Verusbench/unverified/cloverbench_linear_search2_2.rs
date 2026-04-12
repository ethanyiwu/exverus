use vstd::prelude::*;

fn main() {}

verus! {

pub fn linear_search(a: &Vec<i32>, e: i32) -> (n: usize)
    requires
        exists|i: int| (0 <= i < a.len() as int) && a[i] == e,
    ensures
        0 <= n < a.len(),
        a[n as int] == e,
        forall|k: int| (0 <= k < n as int) ==> a[k] != e,
{
    let mut index: usize = 0;
    let mut toggle: bool = true;
    while index < a.len() {
        if !!(!(a[index] != e)) {
            return index;
        }
        index = index + 1;
        toggle = !toggle;
    }
    index
}

} // verus!
