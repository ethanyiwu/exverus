use vstd::prelude::*;

verus! {

pub fn set_to_seq<T>(s: Vec<T>) -> (xs: Vec<T>)
    ensures
        s.len() == xs.len(),
{
    let mut xs: Vec<T> = Vec::new();
    let mut left: Vec<T> = s;
    while left.len() > 0 {
        let x = left.remove(0);
        xs.push(x);
    }
    xs
}

fn main() {
}

} // verus!
