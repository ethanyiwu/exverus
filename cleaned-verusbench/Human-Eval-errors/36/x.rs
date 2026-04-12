use vstd::arithmetic::div_mod::*;
use vstd::arithmetic::mul::*;
use vstd::assert_by_contradiction;
use vstd::calc;
use vstd::prelude::*;

verus! {

pub closed spec fn is_prime(n: nat) -> bool {
    forall|i: nat| 1 < i < n ==> #[trigger] (n % i) != 0
}

// canonical definition of prime factoriztion
pub closed spec fn is_prime_factorization(n: nat, factorization: Seq<nat>) -> bool {
    // all factors are prime
    &&& forall|i: int|
        0 <= i < factorization.len() ==> #[trigger] is_prime(
            factorization[i] as nat,
        )
    // product of factors is n
    &&& factorization.fold_right(|x: nat, acc: nat| (acc * x as nat), 1nat)
        == n
    // factors are listed in ascending order
    &&& forall|i: nat, j: nat|
        (1 < i <= j < factorization.len()) ==> (#[trigger] factorization[i as int]
            <= #[trigger] factorization[j as int])
}

// these two pull out lemmas are the same except for types
// would prefer to have one polymorphic function, but won't go through
// See https://github.com/verus-lang/verus/issues/1287
proof fn lemma_fold_right_pull_out_nat(seq: Seq<nat>, k: nat)
    ensures
        seq.fold_right(|x, acc: nat| (acc * x) as nat, k) == (seq.fold_right(
            |x, acc: nat| (acc * x) as nat,
            1,
        ) * k) as nat,
    decreases seq.len(),
{
fn main () {}
