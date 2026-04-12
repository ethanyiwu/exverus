use vstd::prelude::*;

verus! {

spec fn sum_vector(v: Seq<u32>, n: int) -> int
    recommends
        0 <= n && n <= v.len(),
    decreases v.len() - n,
{
    if n as int >= 0 && n as int <= v.len() {
        if n as int == v.len() {
            0
        } else {
            v[n] + sum_vector(v, n + 1)
        }
    } else {
        0
    }
}

fn sum_it(v: &[u32]) -> (x: u32)
    requires
        v.len() > 0,
        v.len() < 1000,
        forall|i: nat| i < v.len() ==> v[i as int] < u32::MAX / 2,
    ensures
        x as int == sum_vector(v@, 0) || x == u32::MAX,
{
    let mut x: u32 = 0;
    let mut n: usize = v.len();
    while n > 0
        invariant
            0 <= n && n <= v.len(),
            (x == u32::MAX) || (x as int == sum_vector(v@, n as int)),
        decreases n,
    {
        if let Some(new_x) = x.checked_add(v[n - 1]) {
            x = new_x;
        } else {
            // handle overflow
            x = u32::MAX;
        }
        n = n - 1;
    }
    x
}

fn main() {
}

} // verus!