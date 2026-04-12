use vstd::prelude::*;

verus! {

fn sum_to_n(n: u32) -> (sum: Option<u32>)
    ensures
        sum.is_some() ==> sum.unwrap() == spec_sum_to_n(n as nat),
{
    let mut res: u32 = 0;
    let mut sum: u32 = 0;
    let mut i: u32 = 0;
    while i < n
    {
        i += 1;
        res = i.checked_add(res)?;
    }
    Some(res)
}

}
fn main() {}
