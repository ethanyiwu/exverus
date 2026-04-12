use vstd::prelude::*;

verus! {

// when I make this function generic, there is a panic, I do not know why
pub open spec fn remove_all_occ(s: Seq<i32>, val: i32) -> Seq<i32>
    decreases s,
{
    if s.len() == 0 {
        s
    } else {
        let s1 = remove_all_occ(s.subrange(0, s.len() - 1), val);
        let last = s[s.len() - 1];
        if last != val {
            s1.push(last)
        } else {
            s1
        }
    }
}

// #[verifier::loop_isolation(false)]
pub fn remove_element(nums: &mut Vec<i32>, val: i32) -> (res: usize)
    requires
        0 <= old(nums)@.len() <= 30000,
    ensures
        nums@.subrange(0, res as int) =~= remove_all_occ(old(nums)@, val),
{
    let mut k = 0;
    let len = nums.len();
    let ghost s_old = nums@;

    for i in 0..len {
        let ghost flag = false;
        // let ghost nums_old = nums@;
        let e = nums[i];

        if e != val {
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
