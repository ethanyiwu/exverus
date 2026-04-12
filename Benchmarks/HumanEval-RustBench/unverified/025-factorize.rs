use vstd::arithmetic::div_mod::*;
use vstd::arithmetic::mul::*;
use vstd::assert_by_contradiction;
use vstd::calc;
use vstd::prelude::*;

verus! {

fn factorize(n: u8) -> (factorization: Vec<u8>)
    requires
        1 <= n <= u8::MAX,
    ensures
        is_prime_factorization(n as nat, factorization@.map(|_idx, j: u8| j as nat)),
{
    let mut factorization = vec![];
    let mut k = n;
    let mut m = 2u16;
    let ghost n_nat = n as nat;
    while (m <= n as u16)
    {
        if (k as u16 % m == 0) {
            let ghost old_factors = factorization;
            let l = factorization.len();
            factorization.insert(l, m as u8);

            k = k / m as u8;
        } else {
            m = m + 1;
        }
    }
    return factorization;
}

} // verus!
fn main() {}
