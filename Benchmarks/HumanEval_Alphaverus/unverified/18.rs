use vstd::prelude::*;

verus! {

/// Specification for what it means to sum a sequence of numbers
pub open spec fn sum(numbers: Seq<u32>) -> int {
    numbers.fold_left(0, |acc: int, x| acc + x)
}

/// Specification for taking the product of a sequence of numbers
pub open spec fn product(numbers: Seq<u32>) -> int {
    numbers.fold_left(1, |acc: int, x| acc * x)
}

/// Implementation.  We leave the consequences of an intermediate
/// overflow during the product calculation underspecified.
fn sum_product(numbers: Vec<u32>) -> (result: (u64, Option<u32>))
    requires
        numbers.len() < u32::MAX,
    ensures
        result.0 == sum(numbers@),
        match result.1 {
            None =>   // Computing the product overflowed at some point
            exists|i|
                #![auto]
                0 <= i < numbers.len() && product(numbers@.subrange(0, i)) * numbers[i] as int
                    > u32::MAX,
            Some(v) => v == product(numbers@),
        },
{
    let mut sum_value: u64 = 0;
    let mut prod_value: Option<u32> = Some(1);
    for index in 0..numbers.len() {
        sum_value += numbers[index] as u64;
        prod_value =
        match prod_value {
            Some(v) => v.checked_mul(numbers[index]),
            None => None,
        };
    }
    (sum_value, prod_value)
}

} // verus!
fn main() {}
