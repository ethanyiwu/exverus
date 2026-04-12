use vstd::prelude::*;

verus! {

spec fn max(a: int, b: int) -> int {
    if a > b {
        a
    } else {
        b
    }
}

proof fn max_deterministic(a: int, b: int, m: int, m_prime: int)
    requires
        m >= a,
        m >= b,
        m == a || m == b,
        m_prime >= a,
        m_prime >= b,
        m_prime == a || m_prime == b,
    ensures
        m == m_prime,
{
    assert(m == max(a, b));
    assert(m_prime == max(a, b));
    assert(m == m_prime);
}

proof fn max_deterministic_prime(a: int, b: int, m: int, m_prime: int)
    requires
        m != m_prime,
    ensures
        !(m >= a && m >= b && (m == a || m == b)) || !(m_prime >= a && m_prime >= b && (m_prime == a
            || m_prime == b)),
{
    assert(m != m_prime);
    if m >= a && m >= b && (m == a || m == b) {
        assert(m_prime < a || m_prime < b || m_prime != a && m_prime != b);
    } else {
        assert(m < a || m < b || m != a && m != b);
    }
}

proof fn multiset_equality(m1: Seq<int>, m2: Seq<int>, m3: Seq<int>, m4: Seq<int>)
    requires
        m1.len() > m2.len() + m3.len(),
        m1 == m2 + m4,
    ensures
        m3.len() < m4.len(),
{
    assert(m3.len() < m1.len() - m2.len());
}

fn main() {
}

} // verus!
