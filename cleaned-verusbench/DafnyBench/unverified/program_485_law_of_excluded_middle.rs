use vstd::prelude::*;

verus! {

spec fn law_of_excluded_middle(b: bool) -> bool {
    b || !b
}

fn m() {
    n();
    n();
}


}
