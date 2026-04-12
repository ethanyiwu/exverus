use vstd::prelude::*;

verus! {

// This function counts the number of elements of `s` that are equal to `x`.
spec fn count<T>(s: Seq<T>, x: T) -> int
    decreases s.len(),
{
    if s.len() == 0 {
        0
    } else {
        count(s.skip(1), x) + if s[0] == x {
            1int
        } else {
            0int
        }
    }
}

// This function defines what it means for two sequences to be
// permutations of each other: for every value `x`, each of the two
// sequences has the same number of instances of `x`.
spec fn permutes<T>(s1: Seq<T>, s2: Seq<T>) -> bool {
    forall|x: T| count(s1, x) == count(s2, x)
}

// This lemma establishes the effect of an `update` operation on the
// result of a `count`. That is, it gives a closed-form
// (non-recursive) description of what happens to `count(s, x)` when
// `s` is updated to `s.update(i, v)`.
proof fn lemma_update_effect_on_count<T>(s: Seq<T>, i: int, v: T, x: T)
    requires
        0 <= i < s.len(),
    ensures
        count(s.update(i, v), x) == if v == x && s[i] != x {
            count(s, x) + 1
        } else if v != x && s[i] == x {
            count(s, x) - 1
        } else {
            count(s, x)
        },
    decreases s.len(),
{
fn main () {}
