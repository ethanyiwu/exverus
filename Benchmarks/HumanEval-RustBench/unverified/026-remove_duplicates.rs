use vstd::prelude::*;

verus! {

fn count_frequency(elements: &Vec<i64>, key: i64) -> (frequency: usize)
    ensures
        count_frequency_spec(elements@, key) == frequency,
{
    let ghost elements_length = elements.len();
    let mut counter = 0;
    let mut index = 0;
    while index < elements.len()
    {
        if (elements[index] == key) {
            counter += 1;
        }
        index += 1;
    }
    counter
}

fn remove_duplicates(numbers: &Vec<i64>) -> (unique_numbers: Vec<i64>)
    ensures
        unique_numbers@ == numbers@.filter(|x: i64| count_frequency_spec(numbers@, x) == 1),
{
    let ghost numbers_length = numbers.len();
    let mut unique_numbers: Vec<i64> = Vec::new();

    for index in 0..numbers.len()
    {
        if count_frequency(&numbers, numbers[index]) == 1 {
            unique_numbers.push(numbers[index]);
        }
        reveal(Seq::filter);
    }
    unique_numbers
}

} // verus!
fn main() {}
