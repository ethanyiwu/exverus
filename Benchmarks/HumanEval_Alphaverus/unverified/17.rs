use vstd::assert_seqs_equal;
use vstd::prelude::*;

verus! {

/// Specification for inserting a number 'delimiter' between every two consecutive elements
/// of input sequence `numbers'
pub open spec fn intersperse_spec(numbers: Seq<u64>, delimiter: u64) -> Seq<u64>
    decreases numbers.len(),
{
    if numbers.len() <= 1 {
        numbers
    } else {
        intersperse_spec(numbers.drop_last(), delimiter) + seq![delimiter, numbers.last()]
    }
}

// We use these two functions to provide valid triggers for the quantifiers in intersperse_quantified
spec fn even(i: int) -> int {
    2 * i
}

spec fn odd(i: int) -> int {
    2 * i + 1
}

// This quantified formulation of intersperse is easier to reason about in the implementation's loop
spec fn intersperse_quantified(numbers: Seq<u64>, delimiter: u64, interspersed: Seq<u64>) -> bool {
    (if numbers.len() == 0 {
        interspersed.len() == 0
    } else {
        interspersed.len() == 2 * numbers.len() - 1
    }) && (forall|i: int| 0 <= i < numbers.len() ==> #[trigger] interspersed[even(i)] == numbers[i])
        && (forall|i: int|
        0 <= i < numbers.len() - 1 ==> #[trigger] interspersed[odd(i)] == delimiter)
}

/// Implementation of intersperse
pub fn intersperse(numbers: Vec<u64>, delimiter: u64) -> (result: Vec<u64>)
    ensures
        result@ == intersperse_spec(numbers@, delimiter),
{
    if numbers.len() <= 1 {
        numbers
    } else {
        let mut result = Vec::new();
        let mut index = 0;
        while index < numbers.len() - 1 {
            result.push(numbers[index]);
            result.push(delimiter);
            index += 1;
        }
        result.push(numbers[numbers.len() - 1]);
        result
    }
}

} // verus!
fn main() {}
