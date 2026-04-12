use vstd::hash_set::HashSetWithView;
use vstd::prelude::*;
use vstd::std_specs::hash::axiom_u8_obeys_hash_table_key_model;

verus! {

broadcast use axiom_u8_obeys_hash_table_key_model;

fn hash_set_from(s: &Vec<u8>) -> (res: HashSetWithView<u8>)
    ensures
        forall|i: int| #![auto] 0 <= i < s.len() ==> res@.contains(s[i]),
        forall|x: int|
            0 <= x < 256 ==> #[trigger] res@.contains(x as u8) ==> #[trigger] s@.contains(x as u8),
{
    let mut res: HashSetWithView<u8> = HashSetWithView::new();
    for i in 0..s.len()
    {
        res.insert(s[i]);
    }
    res
}

#[verifier::loop_isolation(false)]
fn same_chars(s0: &Vec<u8>, s1: &Vec<u8>) -> (same: bool)
    ensures
        same <==> (forall|i: int| #![auto] 0 <= i < s0.len() ==> s1@.contains(s0[i])) && (forall|
            i: int,
        |
            #![auto]
            0 <= i < s1.len() ==> s0@.contains(s1[i])),
{
    let hs0 = hash_set_from(s0);
    let hs1 = hash_set_from(s1);

    let mut contains_s0 = true;
    for i in 0..s0.len()
    {
        if !hs1.contains(&s0[i]) {
            contains_s0 = false;
        }
    }
    let mut contains_s1 = true;
    for i in 0..s1.len()
    {
        if !hs0.contains(&s1[i]) {
            contains_s1 = false;
        }
    }
    contains_s0 && contains_s1
}

}
fn main() {}
