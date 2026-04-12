use vstd::prelude::*;

verus! {

spec fn knows(a: int, b: int) -> bool {
    true
}

spec fn is_celebrity(n: int, i: int) -> bool
    recommends
        n >= 0 && 0 <= i && i < n,
{
    forall|j: int| 0 <= j && j < n && i != j ==> knows(j, i) && !knows(i, j)
}

spec fn is_celebrity_p(n: int, i: int) -> bool
    recommends
        n >= 0 && 0 <= i && i < n,
{
    is_celebrity(n, i)
}


}
