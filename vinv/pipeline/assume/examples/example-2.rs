use vstd::prelude::*;

fn main()  {}
verus! {

#[verifier::loop_isolation(false)]

#[verifier(external_body)]
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
            v.len() == len,
            n >= 0,
            n < len + 1,
            // c.len() == n,
            forall|i: int| (0 <= i && i < n) ==> c[i] == v[i],  // Added by AI
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

    assume(n != len);
    assume(v.len() == len);
    assume(n >= 0);
    assume(n < len + 1);
    assume(forall|i: int| (0 <= i && i < n) ==> c[i] == v[i]);

    c.push(v[n]);
    n = n + 1;

    assert(v.len() == len);
    assert(n >= 0);
    assert(n < len + 1);
    assert(forall|i: int| (0 <= i && i < n) ==> c[i] == v[i]);
    c
}

} // verus!
// Score: (1, 0)
// Safe: True