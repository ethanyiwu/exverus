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
        n >= 2 && i != n - 1 && n < 1000 && 0 <= i && i < n,
    ensures
        exists|j: int|
            0 <= j && j < n && j != i && knows(i, j) ==> !forall|k: int|
                0 <= k && k < n && i != k ==> knows(k, i) && !knows(i, k),
{
    let j: int = if i == 0 {
        1
    } else {
        i - 1
    };
    assert(0 <= j && j < n && j != i) by {
        assert(i >= 0);
        assert(i < n);
        assert(j >= 0);
        assert(j < n);
        assert(j != i);
    }
    assert(knows(i, j)) by {
        assert(i != j);
    }
    assert(exists|j: int| 0 <= j && j < n && j != i && knows(i, j)) by {
        assert(0 <= j && j < n && j != i);
        assert(knows(i, j));
    }
    assert(exists|j: int|
        0 <= j && j < n && j != i && knows(i, j) ==> !forall|k: int|
            0 <= k && k < n && i != k ==> knows(k, i) && !knows(i, k)) by {
        assert(exists|j: int| 0 <= j && j < n && j != i && knows(i, j));
    }
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
