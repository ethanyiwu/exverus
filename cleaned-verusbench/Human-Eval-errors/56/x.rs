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
    if s.len() == 0 {
        return ;
    }
    if i == 0 {
        assert(s.update(i, v) =~= seq![v] + s.skip(1));
        assert(s.update(i, v).skip(1) =~= s.skip(1));
    } else {
        assert(s.update(i, v) =~= seq![s[0]] + s.skip(1).update(i - 1, v));
        assert(s.update(i, v).skip(1) =~= s.skip(1).update(i - 1, v));
        lemma_update_effect_on_count(s.skip(1), i - 1, v, x);
    }
}

// This lemma proves that if you swap elements `i` and `j` of sequence `s`,
// you get a permutation of `s`.
proof fn lemma_swapping_produces_a_permutation<T>(s: Seq<T>, i: int, j: int)
    requires
        0 <= i < s.len(),
        0 <= j < s.len(),
    ensures
        permutes(s.update(i, s[j]).update(j, s[i]), s),
{
    assert forall|x: T| #[trigger] count(s.update(i, s[j]).update(j, s[i]), x) == count(s, x) by {
        lemma_update_effect_on_count(s, i, s[j], x);
        lemma_update_effect_on_count(s.update(i, s[j]), j, s[i], x);
    }
}

// This is the function we were asked to write.
fn sort_third(l: Vec<i32>) -> (l_prime: Vec<i32>)
    ensures
        l_prime.len() == l.len(),
        forall|i: int| 0 <= i < l.len() && i % 3 != 0 ==> l_prime[i] == l[i],  // unchanged if index not divisible by three
        forall|i: int, j: int|
            0 <= i < j < l.len() && i % 3 == 0 && j % 3 == 0 ==> l_prime[i] <= l_prime[j],
        // indexes divisible by three are ordered
        permutes(l_prime@, l@),  // new vec is a permutation of old vec
{
fn main () {}
