use vstd::prelude::*;

verus! {

struct OddList {
    s: Vec<i32>,
    capacity: usize,
}

impl OddList {
    fn new(capacity: usize) -> (l: OddList)
        ensures
            l.capacity == capacity,
            l.s.len() == 0,
    {
        OddList { s: Vec::with_capacity(capacity), capacity }
    }
}


}
