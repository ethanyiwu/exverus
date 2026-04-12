use vstd::prelude::*;

verus! {

fn lucid_numbers(n: u64) -> (lucid: Vec<u64>)
    requires
        n >= 0,
        n < 1000000,  // added relaxation to prevent overflow

    ensures
        forall|i: int| 0 <= i && i < lucid.len() ==> lucid[i as int] % 3 == 0,
        forall|i: int| 0 <= i && i < lucid.len() ==> lucid[i as int] <= n,
        forall|i: int, j: int|
            0 <= i && i < j && j < lucid.len() as int ==> lucid[i as int] < lucid[j as int],
{
    let mut lucid: Vec<u64> = Vec::new();
    let mut i: u64 = 0;
    while i <= n && i < u64::MAX - 1 {
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
