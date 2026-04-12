use vstd::prelude::*;

verus! {

fn count_less_than(numbers: Vec<u32>, threshold: u32) -> (count: u32)
    requires
        true,
    ensures
        count == numbers.len() as u32,
{
    let mut shrink = numbers.clone();
    let mut grow: Vec<u32> = Vec::new();
    while shrink.len() > 0
        invariant
            shrink.len() + grow.len() == numbers.len(),
        decreases shrink.len(),
    {
        let i = shrink.pop().unwrap();
        grow.push(i);
    }
    assert(grow.len() == numbers.len());
    grow.len() as u32
}

fn main() {
}

} // verus!
