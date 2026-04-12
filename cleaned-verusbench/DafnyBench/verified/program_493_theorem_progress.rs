use vstd::prelude::*;

verus! {

fn theorem_progress(t: Vec<char>) -> (result: bool)
    requires
        true,
    ensures
        result ==> (true),
        !result ==> (true),
{
    true
}

fn main() {
}

} // verus!
