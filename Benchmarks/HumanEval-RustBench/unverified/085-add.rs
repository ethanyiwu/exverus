use vstd::prelude::*;

verus! {

fn add(lst: Vec<u32>) -> (sum: u64)
    requires
        0 < lst.len() < u32::MAX,
    ensures
        sum == add_odd_evens(lst@),
{
    let mut sum: u64 = 0;
    let mut i = 1;
    while (i < lst.len())
    {
        if (lst[i] % 2 == 0) {
            sum += lst[i] as u64;
        }
        i += 2;
    }
    return sum;
}

} // verus!
fn main() {}
