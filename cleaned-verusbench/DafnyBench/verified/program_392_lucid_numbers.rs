use vstd::prelude::*;

verus! {

fn lucid_numbers(n: u64) -> (lucid: Vec<u64>)
    requires
        n >= 0,
        n < u64::MAX / 3,
    ensures
        forall|i: int| 0 <= i && i < lucid.len() ==> lucid[i as int] % 3 == 0,
        forall|i: int| 0 <= i && i < lucid.len() ==> lucid[i as int] <= n,
        forall|i: int, j: int|
            0 <= i && i < j && j < lucid.len() ==> lucid[i as int] < lucid[j as int],
{
    let mut lucid: Vec<u64> = Vec::new();
    let mut i: u64 = 0;
    while i <= n && i < u64::MAX - 1
        invariant
            0 <= i && i <= n + 1,
            lucid.len() <= i,
            forall|k: int| 0 <= k && k < lucid.len() ==> lucid[k as int] % 3 == 0,
            forall|k: int| 0 <= k && k < lucid.len() ==> lucid[k as int] <= i - 1,
            forall|k: int, l: int|
                0 <= k && k < l && l < lucid.len() ==> lucid[k as int] < lucid[l as int],
        decreases n - i + 1,
    {
        if i % 3 == 0 {
            lucid.push(i);
        }
        i = i + 1;
    }
    lucid
}

fn main() {
}

} // verus!
