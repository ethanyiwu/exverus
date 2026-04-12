use vstd::prelude::*;

verus! {

spec fn law_of_excluded_middle(b: bool) -> bool {
    b || !b
}

fn m() {
    n();
    if true {
        assert(law_of_excluded_middle(true));
    } else {
        assert(law_of_excluded_middle(false) || 0 != 0);
    }
    n();
    assert(law_of_excluded_middle(true) || 3 != 3);
    if true {
        assert(law_of_excluded_middle(true));
    } else {
        assert(law_of_excluded_middle(false) || 1 != 1);
    }
}

fn n()
    ensures
        law_of_excluded_middle(true) || 2 != 2,
{
    assert(law_of_excluded_middle(true) || 2 != 2);
}

fn main() {
}

} // verus!
