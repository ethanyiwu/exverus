use vstd::prelude::*;

verus! {

pub open spec fn precondition(nums1: Seq<i32>, nums2: Seq<i32>, m: i32, n: i32) -> bool {
    &&& nums2.len() == n as nat
    &&& nums1.len() == m as nat + n as nat
    &&& 0 <= m
    &&& 0 <= n
    &&& 0 < m + n < 10000
    &&& forall|i: int| m <= i < nums1.len() ==> #[trigger] nums1[i] == 0
    &&& sorted_index(nums1, 0, m as int)
    &&& sorted(nums2)
}

pub open spec fn sorted(s: Seq<i32>) -> bool {
    forall|i: int, j: int| 0 <= i <= j < s.len() ==> s[i] <= s[j]
}

pub open spec fn sorted_index(s: Seq<i32>, start: int, end: int) -> bool {
    &&& 0 <= start <= end <= s.len()
    &&& forall|i: int, j: int| start <= i <= j < end ==> s[i] <= s[j]
}

#[verifier::loop_isolation(false)]
pub fn merge(nums1: &mut Vec<i32>, m: i32, nums2: &Vec<i32>, n: i32)
    requires
        precondition(old(nums1)@, nums2@, m, n),
    ensures
        sorted(nums1@),
        nums1@.to_multiset() =~= old(nums1)@.subrange(0, m as int).to_multiset().add(
            nums2@.to_multiset(),
        ),
{
    broadcast use vstd::seq_lib::group_to_multiset_ensures;
    broadcast use vstd::multiset::group_multiset_properties;

    let ghost m0 = m;
    let ghost n0 = n;
    let ghost nums1_prev = *nums1;

    let mut k = m + n - 1;
    let mut m: i32 = m - 1;
    let mut n = n - 1;
    while m >= 0 && n >= 0 {
        broadcast use vstd::seq_lib::group_to_multiset_ensures;
        broadcast use vstd::multiset::group_multiset_properties;

        let ghost k0 = k as int;
        let ghost nums_prev = *nums1;

        let v1 = nums1[m as usize];
        let v2 = nums2[n as usize];
        if v1 <= v2 {
            let ghost nums10 = nums1@.subrange(k as int + 1, nums1.len() as int);
            nums1.set(k as usize, v2);
            k -= 1;
            n -= 1;
        } else {
            let ghost nums10 = nums1@.subrange(k as int + 1, nums1.len() as int);
            nums1.set(k as usize, v1);
            k -= 1;
            m -= 1;
        }
    }

    let ghost nums_x = *nums1;

    if m < 0 {
        for j in 0..(n + 1) {
            nums1[j as usize] = nums2[j as usize]
        }
        return ;
    }
}

} // verus!
fn main() {}
