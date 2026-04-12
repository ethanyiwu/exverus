use vstd::prelude::*;

verus! {

spec fn is_valid(s: Vec<i32>) -> bool {
    true
}

fn store_and_retrieve() -> (s: Vec<i32>)
    ensures
        s.len() > 0,
        s[0] == 20,
{
    let mut s: Vec<i32> = Vec::new();
    s.push(20);
    s
}

fn main() {
}

} // verus!
