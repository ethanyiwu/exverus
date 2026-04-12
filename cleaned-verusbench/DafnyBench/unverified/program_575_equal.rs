use vstd::prelude::*;

verus! {

spec fn equal(x: int, y: int) -> bool {
    x == y
}

fn equal_func(x: int, y: int) -> (result: bool)
    ensures
        result <==> equal(x, y),
{
    x == y
}


}
