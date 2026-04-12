use vstd::prelude::*;

fn main()   {}
verus! {

#[verifier::loop_isolation(false)]
fn append(v: &Vec<u64>, elem: u64) -> (c: Vec<u64>)
    requires
        v.len() <= 100,
    ensures
        c@.len() == v@.len() + 1,
        forall|i: int| (0 <= i && i < v.len()) ==> c[i] == v[i],
        c@.last() == elem,
{
    let mut c = Vec::with_capacity(v.len() + 1);
    let mut n: usize = 0;
    let len: usize = v.len();
    while n != len
        invariant
            n <= len,
            // n == c@.len(),
            len == v@.len(),
            forall|i: int| 0 <= i < n ==> c[i] == v[i],
        decreases len - n,
    {
        c.push(v[n]);
        n = n + 1;
    }
    c.push(elem);
    c
}

fn append_while1(v: &Vec<u64>, elem: u64) -> (c: Vec<u64>)
    requires
        v.len() <= 100,
{

    let mut c = Vec::with_capacity(v.len() + 1);
    let mut n: usize = 0;
    let len: usize = v.len();
        // place to add variables assignment. [1]
    let (mut v, mut elem, mut c, mut n, mut len) = (v, elem, c, n, len);

    // Loop condition
    assume(n != len);
    // Invariants before the loop
    assume(n <= len);
    assume(len == v@.len());
    assume(forall|i: int| 0 <= i < n ==> c[i] == v[i]);

    c.push(v[n]);
    n = n + 1;

    // Invariants after the loop
    assert(n <= len);
    assert(len == v@.len());
    assert(forall|i: int| 0 <= i < n ==> c[i] == v[i]);
    c
}
}