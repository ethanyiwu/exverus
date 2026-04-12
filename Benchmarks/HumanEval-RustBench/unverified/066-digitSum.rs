use vstd::prelude::*;

verus! {

fn digit_sum(text: &[char]) -> (sum: u128)
    ensures
        count_uppercase_sum(text@) == sum,
{
    let mut index = 0;
    let mut sum = 0u128;

    while index < text.len()
    {
        if (text[index] >= 'A' && text[index] <= 'Z') {
            sum = sum + text[index] as u128;
        }
        index += 1;
    }
    sum
}

} // verus!
fn main() {}
