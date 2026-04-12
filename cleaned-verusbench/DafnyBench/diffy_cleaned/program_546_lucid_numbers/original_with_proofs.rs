use vstd::prelude::*;

verus! {

/// Function to generate lucid numbers
fn lucid_numbers(n: u64) -> (lucid: Vec<u64>)
    requires
        n >= 0,
        n < u64::MAX - 1,
    ensures
        forall|i: int| 0 <= i < lucid.len() ==> lucid[i as int] % 3 == 0,
        forall|i: int| 0 <= i < lucid.len() ==> lucid[i as int] <= n,
        forall|i: int, j: int| 0 <= i < j && j < lucid.len() ==> lucid[i as int] < lucid[j as int],
{
    let mut lucid: Vec<u64> = Vec::new();
    let mut i: u64 = 0;
    while i <= n && i < u64::MAX - 1
        invariant
            0 <= i <= n + 1,
            lucid.len() <= i,
            forall|k: int| 0 <= k < lucid.len() ==> lucid[k as int] % 3 == 0,
            forall|k: int| 0 <= k < lucid.len() ==> lucid[k as int] <= i - 1,
            forall|k: int, l: int| 0 <= k < l && l < lucid.len() ==> lucid[k as int] < lucid[l as int],
        decreases n + 1 - i,
    {
        if i % 3 == 0 {
            lucid.push(i);
        }
        i = i + 1;
    }
    lucid
}

fn main() {}
} // verus!