use vstd::prelude::*;
use vstd::arithmetic::div_mod::{lemma_div_is_ordered, lemma_div_is_ordered_by_denominator, lemma_div_multiples_vanish, lemma_fundamental_div_mod, lemma_fundamental_div_mod_converse};
use vstd::arithmetic::mul::{lemma_mul_inequality, lemma_mul_is_distributive_add, lemma_mul_is_distributive_add_other_way, lemma_mul_unary_negation};

verus! {

fn sum_of_fourth_power_of_odd_numbers(n: u64) -> (sum: u64)
    requires
        n > 0,
        n < u64::MAX / u64::MAX,
    ensures
        sum == n * (2 * n + 1) * (24 * n * n * n - 12 * n * n - 14 * n + 7) / 15,
{
    let temp: u128 = n as u128 * (2 * n as u128 + 1) * (24 * n as u128 * n as u128 * n as u128 - 12
        * n as u128 * n as u128 - 14 * n as u128 + 7) / 15;
    let sum: u64 = temp as u64;
    sum
}


}
