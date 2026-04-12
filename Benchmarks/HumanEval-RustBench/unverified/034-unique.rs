use vstd::calc;
use vstd::prelude::*;
use vstd::seq_lib::lemma_multiset_commutative;
use vstd::seq_lib::lemma_seq_contains_after_push;

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

fn unique_sorted(s: Vec<i32>) -> (result: Vec<i32>)
    requires
        forall|i: int, j: int| 0 <= i < j < s.len() ==> s[i] <= s[j],
    ensures
        forall|i: int, j: int| 0 <= i < j < result.len() ==> result[i] < result[j],
        forall|i: int| #![auto] 0 <= i < result.len() ==> s@.contains(result[i]),
        forall|i: int| #![trigger s[i]] 0 <= i < s.len() ==> result@.contains(s[i]),
{
    let mut result: Vec<i32> = vec![];
    for i in 0..s.len()
    {
        let ghost pre = result;
        if result.len() == 0 || result[result.len() - 1] != s[i] {
            result.push(s[i]);
        }
    }
    result
}

fn unique(s: Vec<i32>) -> (result: Vec<i32>)
    ensures
        forall|i: int, j: int| 0 <= i < j < result.len() ==> result[i] < result[j],
        forall|i: int| #![auto] 0 <= i < result.len() ==> s@.contains(result[i]),
        forall|i: int| #![trigger s[i]] 0 <= i < s.len() ==> result@.contains(s[i]),
{
    let sorted = sort_seq(&s);
    unique_sorted(sorted)
}

}
fn main() {}
