use vstd::calc;
use vstd::prelude::*;
use vstd::seq_lib::lemma_multiset_commutative;

verus! {

fn sort_seq(s: &Vec<i32>) -> (ret: Vec<i32>)
    ensures
        forall|i: int, j: int| 0 <= i < j < ret@.len() ==> ret@.index(i) <= ret@.index(j),
        ret@.len() == s@.len(),
        s@.to_multiset() == ret@.to_multiset(),
{
    let mut sorted = s.clone();
    let mut i: usize = 0;
    while i < sorted.len()
    {
        let mut min_index: usize = i;
        let mut j: usize = i + 1;
        while j < sorted.len()
        {
            if sorted[j] < sorted[min_index] {
                min_index = j;
            }
            j += 1;
        }
        if min_index != i {
            let ghost old_sorted = sorted@;
            let curr_val = sorted[i];
            let min_val = sorted[min_index];
            sorted.set(i, min_val);

            sorted.set(min_index, curr_val);

        }
        i += 1;
    }
    sorted
}

fn strange_sort_list_helper(s: &Vec<i32>) -> (ret: (Vec<i32>, Vec<i32>))
    ensures
        s@.to_multiset() == (ret.0)@.to_multiset(),
        s@.len() == (ret.0)@.len() == (ret.1)@.len(),
        forall|i: int|
            0 <= i < s@.len() && i % 2 == 0 ==> (ret.1)@.index(i) == (ret.0)@.index(i / 2),
        forall|i: int|
            0 <= i < s@.len() && i % 2 == 1 ==> (ret.1)@.index(i) == (ret.0)@.index(
                s@.len() - (i - 1) / 2 - 1,
            ),
{
    let sorted = sort_seq(s);
    let mut strange = Vec::new();
    let mut i: usize = 0;
    while i < sorted.len()
    {
        if i % 2 == 0 {
            strange.push(sorted[i / 2]);
        } else {
            let r = (i - 1) / 2;
            strange.push(sorted[s.len() - r - 1]);
        }
        i += 1;
    }
    (sorted, strange)
}

fn strange_sort_list(s: &Vec<i32>) -> (ret: Vec<i32>)
    ensures
        s@.len() == ret@.len(),
{
    let (_, strange) = strange_sort_list_helper(s);
    strange
}

}
fn main() {}
