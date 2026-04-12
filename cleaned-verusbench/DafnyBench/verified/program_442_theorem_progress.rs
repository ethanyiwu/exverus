use vstd::prelude::*;

verus! {

fn theorem_progress(t: &str) -> (result: bool)
    requires
        t == "example",
    ensures
        result <==> true,
{
    true
}

fn main() {
}

} // verus!
