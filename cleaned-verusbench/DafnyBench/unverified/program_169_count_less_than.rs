use vstd::prelude::*;

verus! {

fn count_less_than(numbers: Vec<u32>, threshold: u32) -> (count: u32)
    requires
        numbers.len() < u32::MAX as usize,
    ensures
        count == numbers.len() as u32,
{
    let mut count = 0;
    let mut shrink = numbers.clone();
    let mut grow: Vec<u32> = Vec::new();
    while shrink.len() > 0 {
        let i = shrink.pop().unwrap();
        grow.push(i);
    }
    grow.len() as u32
}


}
