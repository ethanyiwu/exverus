use vstd::prelude::*;
use vstd::*;

verus! {

// Specification function for max
spec fn max(a: int, b: int) -> int {
    if a > b {
        a
    } else {
        b
    }
}

// Target function
fn max_func(a: int, b: int) -> (m: int)
    ensures
        m >= a,
        m >= b,
        m == a || m == b,
{
    if a > b {
        a
    } else {
        b
    }
}

// Specification function for checking post_max
spec fn post_max(a: int, b: int, m: int) -> bool {
    &&& m >= a
    &&& m >= b
    &&& (m == a || m == b)
}

// Lemma to check if post_max is not too accommodating
fn post_max_point_1(a: int, b: int, m: int)
    requires
        a > b,
        m != a,
    ensures
        !post_max(a, b, m),
{
    assert(!post_max(a, b, m));
}

// Equivalent way of doing the above
fn post_max_point_1_(a: int, b: int, m: int)
    requires
        a > b,
        post_max(a, b, m),
    ensures
        m == a,
{
    assert(m == a);
}

// Lemma to check if post_max is not too accommodating
fn post_max_point_2(a: int, b: int, m: int)
    requires
        a == b,
        m != a || m != b,
    ensures
        !post_max(a, b, m),
{
    assert(!post_max(a, b, m));
}

// Lemma to check if post_max is not too accommodating
fn post_max_point_3(a: int, b: int, m: int)
    requires
        a < b,
        m != b,
    ensures
        !post_max(a, b, m),
{
    assert(!post_max(a, b, m));
}

// Lemma to check if post_max is not too accommodating
fn post_max_vertical_1(a: int, b: int, m: int)
    requires
        m != a && m != b,
    ensures
        !post_max(a, b, m),
{
    assert(!post_max(a, b, m));
}

// Equivalent way of doing the above
fn post_max_vertical_1_(a: int, b: int, m: int)
    requires
        post_max(a, b, m),
    ensures
        m == a || m == b,
{
    assert(m == a || m == b);
}

// Lemma to check if post_max is realistic
fn post_max_realistic_1(a: int, b: int, m: int)
    requires
        a > b,
        m == a,
    ensures
        post_max(a, b, m),
{
    assert(post_max(a, b, m));
}

// Lemma to check if post_max is realistic
fn post_max_realistic_2(a: int, b: int, m: int)
    requires
        a < b,
        m == b,
    ensures
        post_max(a, b, m),
{
    assert(post_max(a, b, m));
}

// Lemma to check if post_max is realistic
fn post_max_realistic_3(a: int, b: int, m: int)
    requires
        a == b,
        m == a,
    ensures
        post_max(a, b, m),
{
    assert(post_max(a, b, m));
}

// Lemma to check if max is deterministic
fn max_deterministic(a: int, b: int, m: int, m_: int)
    requires
        post_max(a, b, m),
        post_max(a, b, m_),
    ensures
        m == m_,
{
    assert(m == m_);
}

// Lemma to check if max is deterministic
fn max_deterministic_(a: int, b: int, m: int, m_: int)
    requires
        m != m_,
    ensures
        !post_max(a, b, m) || !post_max(a, b, m_),
{
    assert(!post_max(a, b, m) || !post_max(a, b, m_));
}

// Lemma to check if a block is valid in a blockchain
fn lemma_inv_the_proposer_of_any_valid_block_in_an_honest_blockchain_is_in_the_set_of_validators_helper_6_helper<
    T,
>(s: Seq<int>, b: int, i: nat)
    requires
        s.len() > i,
        b == s[i as int],
    ensures
        s.take(i as int) + seq![b] == s.take((i + 1) as int),
{
    assert(s.take(i as int) + seq![b] == s.take((i + 1) as int));
}

// Lemma to check if two multisets are equal
fn multiset_equality(m1: Seq<int>, m2: Seq<int>, m3: Seq<int>, m4: Seq<int>)
    requires
        m1.len() > m2.len() + m3.len(),
        m1.len() == m2.len() + m4.len(),
    ensures
        m3.len() < m4.len(),
{
    assert(m3.len() < m4.len());
}

fn main() {
}

} // verus!
