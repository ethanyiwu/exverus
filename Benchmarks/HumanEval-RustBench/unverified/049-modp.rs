use vstd::prelude::*;

verus! {

fn modmul(a: u32, b: u32, p: u32) -> (mul: u32)
    by (nonlinear_arith)
    requires
        p > 0,
    ensures
        mul == ((a as int) * (b as int)) % (p as int),
{
    (((a as u64) * (b as u64)) % (p as u64)) as u32
}

#[verifier::loop_isolation(false)]
fn modp(n: u32, p: u32) -> (r: u32)
    by (nonlinear_arith)
    requires
        p > 0,
    ensures
        r == modp_rec(n as nat, p as nat),
{
    let mut r = 1u32 % p;
    for i in 0..n
    {
        r = modmul(r, 2, p);
    }
    r
}

}
fn main() {}
