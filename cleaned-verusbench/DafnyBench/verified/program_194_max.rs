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
        m >= a && m >= b && (m == a || m == b),
        m_prime >= a && m_prime >= b && (m_prime == a || m_prime == b),
    ensures
        m == m_prime,
{
    if a > b {
        assert(m == a);
        assert(m_prime == a);
    } else if a < b {
        assert(m == b);
        assert(m_prime == b);
    } else {
        assert(m == a);
        assert(m_prime == a);
    }
}

proof fn max_deterministic_prime(a: int, b: int, m: int, m_prime: int)
    requires
        m != m_prime,
    ensures
        !(m >= a && m >= b && (m == a || m == b)) || !(m_prime >= a && m_prime >= b && (m_prime == a
            || m_prime == b)),
{
    assert(m != m_prime);
}

spec fn post_max(a: int, b: int, m: int) -> bool {
    &&& m >= a
    &&& m >= b
    &&& (m == a || m == b)
}

proof fn post_max_vertical_1(a: int, b: int, m: int)
    requires
        m != a && m != b,
    ensures
        !(m >= a && m >= b && (m == a || m == b)),
{
    assert(m != a);
    assert(m != b);
}

proof fn post_max_vertical_1_prime(a: int, b: int, m: int)
    requires
        m >= a && m >= b && (m == a || m == b),
    ensures
        m == a || m == b,
{
    assert(m >= a);
    assert(m >= b);
    assert(m == a || m == b);
}

proof fn post_max_realistic_1(a: int, b: int, m: int)
    requires
        a > b && m == a,
    ensures
        m >= a && m >= b && (m == a || m == b),
{
    assert(a > b);
    assert(m == a);
}

proof fn post_max_realistic_2(a: int, b: int, m: int)
    requires
        a < b && m == b,
    ensures
        m >= a && m >= b && (m == a || m == b),
{
    assert(a < b);
    assert(m == b);
}

proof fn post_max_realistic_3(a: int, b: int, m: int)
    requires
        a == b && m == a,
    ensures
        m >= a && m >= b && (m == a || m == b),
{
    assert(a == b);
    assert(m == a);
}

proof fn post_max_point_1(a: int, b: int, m: int)
    requires
        a > b && m != a,
    ensures
        !(m >= a && m >= b && (m == a || m == b)),
{
    assert(a > b);
    assert(m != a);
}

proof fn post_max_point_1_prime(a: int, b: int, m: int)
    requires
        a > b && m >= a && m >= b && (m == a || m == b),
    ensures
        m == a,
{
    assert(a > b);
    assert(m >= a);
    assert(m >= b);
    assert(m == a || m == b);
}

proof fn post_max_point_2(a: int, b: int, m: int)
    requires
        a == b && m != a && m != b,
    ensures
        !(m >= a && m >= b && (m == a || m == b)),
{
    assert(a == b);
    assert(m != a);
    assert(m != b);
}

proof fn post_max_point_3(a: int, b: int, m: int)
    requires
        a < b && m != b,
    ensures
        !(m >= a && m >= b && (m == a || m == b)),
{
    assert(a < b);
    assert(m != b);
}

proof fn multiset_equality(m1: Seq<int>, m2: Seq<int>, m3: Seq<int>, m4: Seq<int>)
    requires
        m1.len() > m2.len() + m3.len(),
        m1.len() == m2.len() + m4.len(),
    ensures
        m3.len() < m4.len(),
{
    if m1.len() == 0 {
        assert(false);
    }
    assert(m3.len() < m1.len() - m2.len());
}

fn main() {
}

} // verus!
