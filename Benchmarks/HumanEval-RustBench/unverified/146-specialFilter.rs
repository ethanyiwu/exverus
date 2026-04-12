use vstd::prelude::*;

verus! {

fn extract_first_digit(n: u32) -> (res: u32)
    ensures
        res == extract_first_digit_spec(n as int),
{
    if n < 10 {
        n
    } else {
        extract_first_digit(n / 10)
    }
}

fn extract_last_digit(n: u32) -> (res: u32)
    ensures
        res == extract_last_digit_spec(n as int),
{
    n % 10
}

fn is_valid_element(n: i32) -> (res: bool)
    ensures
        res == is_valid_element_spec(n as int),
{
    ((n > 10) && (extract_first_digit(n as u32) % 2 != 0) && (extract_last_digit(n as u32) % 2
        != 0))
}

fn special_filter(numbers: &Vec<i32>) -> (count: usize)
    ensures
        count == special_filter_spec(numbers@),
{
    let ghost numbers_length = numbers.len();
    let mut counter: usize = 0;
    let mut index = 0;
    while index < numbers.len()
    {
        if (is_valid_element(numbers[index])) {
            counter += 1;
        }
        index += 1;
    }
    counter
}

} // verus!
fn main() {}
