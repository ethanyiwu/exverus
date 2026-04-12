use vstd::math::min;
use vstd::prelude::*;

verus! {

#[inline]
pub fn min_usize(x: usize, y: usize) -> (res: usize)
    ensures
        res == min(x as int, y as int),
{
    if x < y {
        x
    } else {
        y
    }
}

// pub open spec fn leq_i(s1:Seq<i32>, s2:Seq<i32>, index:int) -> bool
//   decreases s2.len() - index,
// {
//   if index >= s1.len() {true}
//   else if index >= s2.len() {false}
//   else if s1[index] < s2[index] {true}
//   else if s1[index] > s2[index] {false}
//   else {leq_i(s1, s2, index + 1)}
// }
pub open spec fn leq(s1: Seq<i32>, s2: Seq<i32>) -> bool
    decreases s1,
{
    if s1.len() == 0 {
        true
    } else if s2.len() == 0 {
        false
    } else {
        if s1[0] < s2[0] {
            true
        } else if s1[0] > s2[0] {
            false
        } else {
            leq(s1.subrange(1, s1.len() as int), s2.subrange(1, s2.len() as int))
        }
    }
}

pub open spec fn min_len(v: Seq<Vec<i32>>, len: int) -> bool {
    &&& forall|i: int| 0 <= i < v.len() ==> #[trigger] v[i].len() >= len
    &&& exists|i: int| 0 <= i < v.len() && #[trigger] v[i].len() == len
}

// if we assume v is sorted
pub fn longest_common_prefix(v: &Vec<Vec<i32>>) -> (res: Vec<i32>)
    requires
        v.len() >= 1,
        forall|i: int, j: int| 0 <= i <= j < v.len() ==> leq(v@[i]@, v@[j]@),
    ensures
        forall|j: int|
            #![all_triggers]
            0 <= j < v.len() ==> res@ =~= v@[j]@.subrange(0, res@.len() as int) && v@[j]@.len()
                >= res@.len(),
        min_len(
            v@,
            res.len() as int,
        )
        // || v@[0]@[res.len() as int] != v@[v.len() - 1]@[res.len() as int]
         || exists|k1: int, k2: int|
            #![all_triggers]
            0 <= k1 < k2 < v.len() && v@[k1]@[res.len() as int] != v@[k2]@[res.len() as int],
{
    if v.len() == 1 {
        return v[0].clone()
    }
    let v1 = &v[0];
    let v2 = &v[v.len() - 1];

    let len = min_usize(v1.len(), v2.len());
    let mut res = Vec::<i32>::new();

    let i = 0;

    for i in 0..len {
        if v1[i] == v2[i] {
            res.push(v1[i])
        } else {
            return res;
        }
    }
    return res;
}

///////////////////////////////////////////////////
#[verifier::external_body]
pub fn sort(v: &mut Vec<Vec<i32>>)
    ensures
        old(v)@.to_multiset() =~= v@.to_multiset(),
        forall|i: int, j: int| 0 <= i <= j < v.len() ==> leq(v@[i]@, v@[j]@),
        //corr
        old(v).len() == v.len(),
        forall|val: Vec<i32>| old(v)@.contains(val) <==> v@.contains(val),
{
    unimplemented!()
}

pub fn longest_common_prefix_2(v: &mut Vec<Vec<i32>>) -> (res: Vec<i32>)
    requires
        old(v).len() >= 1,
    ensures
        forall|j: int|
            #![all_triggers]
            0 <= j < v.len() ==> res@ =~= v@[j]@.subrange(0, res@.len() as int) && v@[j]@.len()
                >= res@.len(),
        min_len(v@, res.len() as int) || exists|k1: int, k2: int|
            #![all_triggers]
            0 <= k1 < k2 < v.len() && v@[k1]@[res.len() as int] != v@[k2]@[res.len() as int],
{
    sort(v);

    let res = longest_common_prefix(v);
    return res;
}

} // verus!
fn main() {}
