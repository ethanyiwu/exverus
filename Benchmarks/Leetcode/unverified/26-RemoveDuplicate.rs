use vstd::prelude::*;

verus! {

// #[verifier::loop_isolation(false)]
pub fn remove_duplicates(nums: &mut Vec<i32>) -> (res: usize)
    requires
        1 <= old(nums)@.len() <= 30000,
        forall|i: int, j: int| 0 <= i <= j < old(nums)@.len() ==> old(nums)@[i] <= old(nums)@[j],
    ensures
        nums@.subrange(0, res as int).to_set() =~= old(nums)@.to_set(),
        forall|p: int, q: int| 0 <= p < q < res ==> nums@[p] < nums@[q],
{
    let mut k = 1;
    let len = nums.len();

    let ghost s_old = nums@;

    for i in 1..len {
        let e = nums[i];

        let ghost flag = false;
        let ghost nums_old = nums@;

        if e != nums[k - 1] {
            nums.set(k, e);  // &mut is limited in Verus
            k += 1;

        }
    }  //end of loop

    k
}

fn test() {
    let mut v = vec![1usize,2];
    v.set(1, 4);

}

} // verus!
fn main() {}
