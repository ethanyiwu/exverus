use vstd::prelude::*;

verus! {

// Implement a set in terms of a sequence
spec fn set_to_seq<T>(s: Seq<T>) -> Set<T> {
    s.to_set()
}

// Implement a set in terms of a sequence
fn set_to_seq_exec<T>(s: Vec<T>) -> (result: Vec<T>)
    requires
        true,
    ensures
        set_to_seq(s@) == set_to_seq(result@),
{
    s
}

// Implement a set in terms of a sequence
fn set_to_seq_exec_wrapper<T>(s: Vec<T>) -> (result: Vec<T>)
    requires
        true,
    ensures
        set_to_seq(s@) == set_to_seq(result@),
{
    set_to_seq_exec(s)
}

fn main() {
}

} // verus!
