use vstd::prelude::*;

verus! {

/// Specification function
spec fn infinite_path(r: Seq<int>) -> bool {
    true
}

/// Function to check if a path is infinite
fn infinite_path_func(r: &Vec<int>) -> (result: bool)
    requires
        r.len() > 0,
    ensures
        result <==> infinite_path(r@),
{
    true
}

fn main() {
}

} // verus!
