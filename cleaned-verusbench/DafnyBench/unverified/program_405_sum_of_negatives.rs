use vstd::prelude::*;

verus! {

fn sum_of_negatives(a: &[i32]) -> (result: i32)
    requires
        a.len() > 0,
        a.len() < 1000,
    ensures
        result >= i32::MIN,
{
    let mut result: i32 = 0;
    for i in 0..a.len() {
        if a[i] < 0 {
            let temp: i64 = (result as i64) + (a[i] as i64);
            if temp > i32::MAX as i64 {
                result = i32::MAX;
            } else {
                result = temp as i32;
            }
        }
    }
    result
}


}
