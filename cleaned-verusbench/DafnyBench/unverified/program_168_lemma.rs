use vstd::prelude::*;

verus! {

spec fn lemma(b: bool) -> bool {
    b || !b
}

fn m() {
    n();
    n();
}


}
