use vstd::prelude::*;

use vstd::multiset::Multiset;

verus! {

broadcast use {vstd::multiset::group_multiset_properties, vstd::seq_lib::group_seq_properties};

pub open spec fn precondition(s: Multiset<u32>) -> bool {
    exists|single: u32| pre_aux(s, single)
}

pub open spec fn pre_aux(s: Multiset<u32>, single: u32) -> bool {
    &&& s.count(single) == 1
    &&& forall|val: u32| s.count(val) > 0 && val != single ==> s.count(val) == 2
}

pub open spec fn xor_all(s: Seq<u32>) -> u32
    decreases s,
{
    if s.len() == 0 {
        0
    } else {
        s[0] ^ xor_all(s.subrange(1, s.len() as int))
    }
}

pub open spec fn double(s: Multiset<u32>) -> bool {
    forall|val: u32| s.count(val) > 0 ==> s.count(val) == 2
}

pub fn helper(v: &Vec<u32>, i: usize, acc: u32) -> (res: u32)
    requires
        0 <= i <= v.len(),
    ensures
        res == v@.subrange(i as int, v.len() as int).reverse().fold_right(
            |x: u32, y: u32| x ^ y,
            acc,
        ),
    decreases v.len() - i,
{
    if i >= v.len() {
        acc
    } else {
        helper(v, i + 1, v[i] ^ acc)  // tail recursive

    }
}

pub fn single_number(v: Vec<u32>) -> (res: u32)
    requires
        precondition(v@.to_multiset()),
    ensures
        v@.to_multiset().count(res) == 1,
        forall|val: u32|
            v@.to_multiset().count(val) > 0 && val != res ==> v@.to_multiset().count(val) == 2,
{
    let ghost f_xor = |x: u32, y: u32| x ^ y;
    let res = helper(&v, 0, 0);

    return res;
}

} // verus!
fn main() {}
