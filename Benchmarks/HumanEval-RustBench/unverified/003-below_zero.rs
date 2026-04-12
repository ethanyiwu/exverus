use vstd::prelude::*;

verus! {

fn below_zero(operations: Vec<i32>) -> (result: bool)
    requires
        forall|i: int|
            0 <= i <= operations@.len() ==> sum(operations@.take(i).map(|_idx, j: i32| j as int))
                <= i32::MAX,
    ensures
        result <==> exists|i: int|
            0 <= i <= operations@.len() && sum(operations@.take(i).map(|_idx, j: i32| j as int))
                < 0,
{
    let mut s = 0i32;
    for k in 0..operations.len()
    {
        s = s + operations[k];
        if s < 0 {
            return true;
        }
    }
    false
}

}
fn main() {}
