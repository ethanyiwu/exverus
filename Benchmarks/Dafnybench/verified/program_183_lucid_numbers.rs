use vstd::prelude::*;

verus! {

fn lucid_numbers(n: u32) -> (lucid: Vec<u32>)
    requires
        n >= 0,
    ensures
        forall|i: nat| 0 <= i < lucid.len() as nat ==> lucid[i as int] % 3 == 0,
        forall|i: nat| 0 <= i < lucid.len() as nat ==> lucid[i as int] <= n,
        forall|i: nat, j: nat|
            0 <= i < j && j < lucid.len() as nat ==> lucid[i as int] < lucid[j as int],
{
    let mut lucid: Vec<u32> = Vec::new();
    let mut i: u32 = 0;
    while i <= n && i < u32::MAX
        invariant
            0 <= i <= n + 1,
            forall|k: nat| 0 <= k < lucid.len() as nat ==> lucid[k as int] % 3 == 0,
            forall|k: nat| 0 <= k < lucid.len() as nat ==> lucid[k as int] <= i - 1,
            forall|k: nat, l: nat|
                0 <= k < l && l < lucid.len() as nat ==> lucid[k as int] < lucid[l as int],
        decreases n + 1 - i,
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
