use vstd::prelude::*;

verus! {

spec fn lemma(b: bool) -> bool {
    b || !b
}

fn m() {
    n();
    assert(lemma(true) || 0 != 0);
    n();
    assert(lemma(true) || 3 != 3);
    assert(lemma(true) || 1 != 1);
}

fn n()
    ensures
        lemma(true) || 2 != 2,
{
    assert(lemma(true));
}

fn main() {
}

} // verus!
