use vstd::prelude::*;

verus! {

fn sum_product(numbers: Vec<u32>) -> (result: (u64, Option<u32>))
    requires
        numbers.len() < u32::MAX,
    ensures
        result.0 == sum(numbers@),
        result.1 matches Some(v) ==> v == product(numbers@),
{
    let mut sum_value: u64 = 0;
    let mut prod_value: Option<u32> = Some(1);
    for index in 0..numbers.len()
    {
        sum_value += numbers[index] as u64;
        prod_value =
        match prod_value {
            Some(v) => v.checked_mul(numbers[index]),
            None => None,
        };
    }
    (sum_value, prod_value)
}

}
fn main() {}
