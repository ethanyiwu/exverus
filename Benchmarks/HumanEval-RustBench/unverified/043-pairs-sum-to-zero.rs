use vstd::prelude::*;

verus! {

#[verifier::loop_isolation(false)]
fn pairs_sum_to_zero(nums: &[i32], target: i32) -> (found: bool)
    requires
        nums.len() >= 2,
        forall|i: int, j: int|
            0 <= i < j < nums.len() ==> nums[i] + nums[j] <= i32::MAX && nums[i] + nums[j]
                >= i32::MIN,
    ensures
        found <==> exists|i: int, j: int| 0 <= i < j < nums.len() && nums[i] + nums[j] == target,
{
    let mut i = 0;

    while i < nums.len()
    {
        let mut j = i + 1;
        while j < nums.len()
        {
            if nums[i] + nums[j] == target {
                return true;
            }
            j = j + 1;
        }
        i = i + 1;
    }
    false
}

}
fn main() {}
