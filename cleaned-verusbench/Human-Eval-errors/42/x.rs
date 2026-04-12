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
    if seq.len() == 0 {
    } else {
        calc! {
            (==)
            seq.fold_right(|x, acc: nat| (acc * x) as nat, k); {
                lemma_fold_right_pull_out_nat(seq.drop_last(), (k * seq.last()) as nat)
            }
            (seq.drop_last().fold_right(|x, acc: nat| (acc * x) as nat, 1) * (k
                * seq.last()) as nat) as nat; {
                lemma_mul_is_commutative(k as int, seq.last() as int)
            }
            (seq.drop_last().fold_right(|x, acc: nat| (acc * x) as nat, 1) * (seq.last()
                * k) as nat) as nat; {
                lemma_mul_is_associative(
                    seq.drop_last().fold_right(|x: nat, acc: nat| (acc * x) as nat, 1nat) as int,
                    seq.last() as int,
                    k as int,
                );
            }  // {lemma_mul_is_associative(seq.drop_last().fold_right(|x, acc : nat| (acc * x) as nat, 1) as int, seq.last() as int, k as int)}
            (((seq.drop_last().fold_right(|x, acc: nat| (acc * x) as nat, 1) * seq.last()) as nat)
                * k) as nat; { lemma_fold_right_pull_out_nat(seq.drop_last(), seq.last() as nat) }
            (seq.fold_right(|x, acc: nat| (acc * x) as nat, 1) * k) as nat;
        }
    }
}

proof fn lemma_fold_right_pull_out_hybrid(seq: Seq<u8>, k: nat)
    ensures
        seq.fold_right(|x, acc: nat| (acc * x) as nat, k) == (seq.fold_right(
            |x, acc: nat| (acc * x) as nat,
            1,
        ) * k) as nat,
    decreases seq.len(),
{
    if seq.len() == 0 {
    } else {
        calc! {
            (==)
            seq.fold_right(|x, acc: nat| (acc * x) as nat, k); {
                lemma_fold_right_pull_out_hybrid(seq.drop_last(), (k * seq.last()) as nat)
            }
            (seq.drop_last().fold_right(|x, acc: nat| (acc * x) as nat, 1) * (k
                * seq.last()) as nat) as nat; {
                lemma_mul_is_commutative(k as int, seq.last() as int)
            }
            (seq.drop_last().fold_right(|x, acc: nat| (acc * x) as nat, 1) * (seq.last()
                * k) as nat) as nat; {
                lemma_mul_is_associative(
                    seq.drop_last().fold_right(|x: u8, acc: nat| (acc * x) as nat, 1nat) as int,
                    seq.last() as int,
                    k as int,
                );
            }
            (((seq.drop_last().fold_right(|x, acc: nat| (acc * x) as nat, 1) * seq.last()) as nat)
                * k) as nat; { lemma_fold_right_pull_out_hybrid(seq.drop_last(), seq.last() as nat)
            }
            (seq.fold_right(|x, acc: nat| (acc * x) as nat, 1) * k) as nat;
        }
    }
}

proof fn lemma_unfold_right_fold(factors: Seq<u8>, old_factors: Seq<u8>, k: u8, m: u8)
    requires
        old_factors.push(m) == factors,
        k % m == 0,
        m != 0,
    ensures
        factors.fold_right(|x, acc: nat| (acc * x) as nat, ((k / m) as nat))
            == old_factors.fold_right(|x, acc: nat| (acc * x) as nat, ((k as nat))),
{
    assert((old_factors.push(m)).drop_last() == old_factors);
    assert(((k as int) / (m as int)) * (m as int) + (k as int) % (m as int) == (k as int)) by {
        lemma_fundamental_div_mod(k as int, m as int)
    };
}

proof fn lemma_unfold_right_fold_new(factors: Seq<u8>, old_factors: Seq<u8>, m: u8)
    requires
        old_factors.push(m as u8) == factors,
        m != 0,
    ensures
        factors.fold_right(|x, acc: nat| (acc * x) as nat, 1nat) == old_factors.fold_right(
            |x, acc: nat| (acc * x) as nat,
            1nat,
        ) * (m as nat),
{
    assert((old_factors.push(m as u8)).drop_last() == old_factors);
    assert(factors.fold_right(|x, acc: nat| (acc * x) as nat, 1nat) == old_factors.fold_right(
        |x, acc: nat| (acc * x) as nat,
        1,
    ) * (m as nat)) by { lemma_fold_right_pull_out_hybrid(old_factors, m as nat) }
}

proof fn lemma_multiple_mod_is_zero(m: int, n: int, k: int)
    requires
        n % k == 0,
        k % m == 0,
        k > 0,
        m > 0,
    ensures
        n % (k / m) == 0,
{
    assert(k == (k / m) * m) by { lemma_fundamental_div_mod(k, m) };
    assert(n == (n / k) * k) by { lemma_fundamental_div_mod(n, k) };

    assert(n == ((n / k) * m) * (k / m)) by {
        broadcast use group_mul_properties;

    };
    assert(n % (k / m) == 0) by { lemma_mod_multiples_basic((n / k) * m, k / m) };
}

proof fn lemma_multiple_mod_is_zero_new(m: int, n: int, k: int)
    requires
        n % k == 0,
        k % m == 0,
        k > 0,
        m > 0,
        n > 0,
    ensures
        m * (n / k) == n / (k / m),
{
    assert(k == (k / m) * m) by { lemma_fundamental_div_mod(k, m) };
    let a = choose|a: int| (#[trigger] (a * m) == k && (a == k / m));

    assert(n == (n / k) * k) by { lemma_fundamental_div_mod(n, k) };
    let b = choose|b: int| (#[trigger] (b * k) == n && b == n / k);

    assert((a * m) * b == n) by { lemma_mul_is_commutative(b, a * m) }
    assert(a * (m * b) == n) by { lemma_mul_is_associative(a, m, b) };
    assert((m * b) == n / a) by { lemma_div_multiples_vanish(m * b, a) };
}

proof fn lemma_factor_mod_is_zero(k: int, m: int, j: int)
    requires
        k % j != 0,
        k % m == 0,
        1 <= j < m,
    ensures
        (k / m) % j != 0,
{
fn main () {}
