use vstd::prelude::*;

verus! {

struct Odd {
    n: int,
}

impl Odd {
    fn new(n: int) -> (o: Odd)
        ensures
            o.n == n,
    {
        Odd { n }
    }
}

fn main() {
}

} // verus!
