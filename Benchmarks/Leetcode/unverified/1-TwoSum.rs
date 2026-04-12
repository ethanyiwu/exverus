use vstd::prelude::*;

verus! {

spec fn aux(p: int, q: int, k: int, len: int) -> bool {
    0 <= p < k <= q < len
}

// brute force
fn find_sum_2(l: Vec<i32>, sum: i32) -> (res: Option<(usize, usize)>)
    requires
        -10_0000_0000 <= sum <= 10_0000_0000,
        forall|i: int| 0 <= i < l.len() ==> -10_0000_0000 <= #[trigger] l[i] <= 10_0000_0000,
    ensures
        (forall|i: int, j: int| 0 <= i < j < l.len() ==> l[i] + l[j] != sum) <==> res == None::<
            (usize, usize),
        >,
        !(forall|i: int, j: int| 0 <= i < j < l.len() ==> l[i] + l[j] != sum) <==> res.is_Some()
            && l[res.unwrap().0 as int] + l[res.unwrap().1 as int] == sum,
{
    let len = l.len();
    let mut i = 0;

    while i < len {
        let mut j = i + 1;

        while j < len {
            if (l[i] + l[j] == sum) {
                return Some((i, j))
            }
            j = j + 1;
        }

        i = i + 1;
    }
    None
}

// method 2
use std::collections::HashMap;

fn find_sum_3(l: Vec<i32>, sum: i32) -> (res: Option<(usize, usize)>)
    requires
        -10_0000_0000 <= sum <= 10_0000_0000,
        forall|i: int| 0 <= i < l.len() ==> -10_0000_0000 <= #[trigger] l[i] <= 10_0000_0000,
    ensures
        (forall|i: int, j: int| 0 <= i < j < l.len() ==> l[i] + l[j] != sum) <==> res == None::<
            (usize, usize),
        >,
        !(forall|i: int, j: int| 0 <= i < j < l.len() ==> l[i] + l[j] != sum) <==> res.is_Some()
            && l[res.unwrap().0 as int] + l[res.unwrap().1 as int] == sum,
{
    broadcast use vstd::std_specs::hash::group_hash_axioms;

    let mut map: HashMap<i32, usize> = HashMap::new();
    let mut i = 0;
    let len = l.len();
    while i < len {
        broadcast use vstd::std_specs::hash::group_hash_axioms;

        let v = l[i];
        let value = map.get(&v);
        match value {
            Some(k) => { return Some((i, *k)) },
            None => {
                map.insert(sum - v, i);
                i = i + 1;
            },
        }
    }

    None
}

fn main() {
}

} // verus!
//veurs!
