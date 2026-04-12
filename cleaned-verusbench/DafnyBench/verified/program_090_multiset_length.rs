use vstd::prelude::*;

verus! {

// Define a function to calculate the length of a multiset
fn multiset_length(elems: &Vec<i32>) -> (len: i32)
    requires
        elems.len() > 0,
        elems.len() < i32::MAX,
    ensures
        len == elems.len() as i32,
{
    elems.len() as i32
}

fn main() {
}

} // verus!
