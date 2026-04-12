use vstd::prelude::*;

verus! {

spec fn precondition(s: Seq<u32>) -> bool {
    &&& 0 <= s.len() <= 300
    &&& forall|i: int| 0 <= i < s.len() ==> 0 <= #[trigger] s[i] <= 2
}

spec fn count(s: Seq<u32>, val: u32) -> nat
    decreases s.len(),
{
    if s.len() == 0 {
        0
    } else if s.last() == val {
        1 + count(s.drop_last(), val)
    } else {
        count(s.drop_last(), val)
    }
}

#[verifier::spinoff_prover]
fn sortColors(nums: &mut Vec<u32>)
    requires
        precondition(old(nums)@),
    ensures
        vstd::relations::sorted_by(nums@, |x: u32, y: u32| x <= y),
        nums@.to_multiset() =~= old(nums)@.to_multiset(),
{
    let mut a = 0;
    let mut b = 0;
    let mut c = 0;
    for i in 0..nums.len() {
        broadcast use lemma_count;

        if (nums[i] == 0) {
            a += 1;
        } else if (nums[i] == 1) {
            b += 1;
        } else {
            c += 1;
        }
    }

    for i in 0..a {
        nums.set(i, 0);

    }

    for i in 0..b {
        nums.set(i + a, 1);
    }

    for i in 0..c {
        nums.set(i + a + b, 2);
    }
}

} // verus!
fn main() {}
