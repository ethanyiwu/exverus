use vstd::prelude::*;

verus! {

fn set_to_seq<T: Clone>(s: Vec<T>) -> (xs: Vec<T>)
    requires
        s.len() > 0,
    ensures
        xs.len() == s.len(),
{
    let mut xs: Vec<T> = Vec::new();
    let mut left: Vec<T> = s;
    while left.len() > 0 {
        let x: T = left.remove(0);
        xs.push(x);
    }
    xs
}


}
