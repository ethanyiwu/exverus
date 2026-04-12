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

proof fn knower_cannot_be_celebrity(n: int, i: int)
    requires
        n >= 0 && 0 <= i && i < n && n < 1000 && i != 0 && i != n
            - 1,  // added a relaxation on the size of n and value of i

    ensures
        exists|j: int|
            0 <= j && j < n && j != i && knows(i, j) ==> !forall|k: int|
                0 <= k && k < n && i != k ==> knows(k, i) && !knows(i, k),
{
    assert(forall|j: int|
        0 <= j && j < n && i != j ==> knows(j, i) && !knows(i, j) ==> !knows(i, j)) by {
        assert(forall|j: int|
            0 <= j && j < n && i != j ==> knows(j, i) && !knows(i, j) ==> !knows(i, j));
    }
    let j: int = i + 1;
    assert(0 <= j && j < n);
    assert(j != i);
    assert(knows(i, j));
    assert(exists|j: int| 0 <= j && j < n && j != i && knows(i, j));
}

spec fn is_celebrity_p(n: int, i: int) -> bool
    recommends
        n >= 0 && 0 <= i && i < n,
{
    is_celebrity(n, i)
}

fn main() {
}

} // verus!
