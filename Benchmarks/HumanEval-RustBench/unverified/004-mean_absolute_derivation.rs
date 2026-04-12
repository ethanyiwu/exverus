use vstd::arithmetic::div_mod::{
    lemma_div_is_ordered, lemma_div_is_ordered_by_denominator, lemma_div_multiples_vanish,
    lemma_fundamental_div_mod, lemma_fundamental_div_mod_converse,
};
use vstd::arithmetic::mul::{
    lemma_mul_inequality, lemma_mul_is_distributive_add, lemma_mul_is_distributive_add_other_way,
    lemma_mul_unary_negation,
};
use vstd::prelude::*;

verus! {

fn divide_i32_by_u32(x: i32, d: u32) -> (qr: (i32, u32))
    requires
        d > 0,
    ensures
        expr_inner_divide_i32_by_u32(qr, x, d),
{
    if x >= 0 {
        return ((x as u32 / d) as i32, x as u32 % d);
    }
    let neg_x: u32;
    if x == i32::MIN {
        if d == 1 {
            return (x, 0);
        } else {
            neg_x = 0x80000000u32;
        }
    } else {
        neg_x = (-x) as u32;
    }
    let neg_x_div_d = neg_x / d;
    let neg_x_mod_d = neg_x % d;
    if neg_x_mod_d == 0 {
        (-(neg_x_div_d as i32), 0u32)
    } else {
        (-(neg_x_div_d as i32) - 1, d - neg_x_mod_d)
    }
}

fn divide_i32_by_usize(x: i32, d: usize) -> (qr: (i32, usize))
    requires
        d > 0,
    ensures
        expr_inner_divide_i32_by_usize(qr, x, d),
{
    if d <= u32::MAX as usize {
        let (q, r) = divide_i32_by_u32(x, d as u32);
        (q, r as usize)
    } else if x >= 0 {
        (0, x as usize)
    } else {
        let neg_x: usize = if x == i32::MIN {
            0x80000000usize
        } else {
            (-x) as usize
        };
        (-1, d - neg_x)
    }
}

fn compute_mean_of_i32s(numbers: &[i32]) -> (result: i32)
    requires
        numbers.len() > 0,
    ensures
        result == mean(numbers@.map(|_index, n: i32| n as int)),
{
    let ghost nums = numbers@.map(|_index, n: i32| n as int);
    let mut quotient: i32 = 0;
    let mut remainder: usize = 0;
    let numbers_len: usize = numbers.len();
    for i in 0..numbers_len
    {
        let n = numbers[i];

        let (q, r) = divide_i32_by_usize(n, numbers_len);

        if r >= numbers_len - remainder {
            remainder -= (numbers_len - r);
            quotient += (q + 1);
        } else {
            remainder += r;
            quotient += q;
        }
    }
    quotient
}

fn compute_absolute_difference(x: i32, y: i32) -> (z: u32)
    ensures
        z == abs(x - y),
{
    if x >= y {
        if y >= 0 || x < 0 {
            (x - y) as u32
        } else {
            let neg_y: u32 = if y == i32::MIN {
                0x80000000u32
            } else {
                (-y) as u32
            };
            x as u32 + neg_y
        }
    } else {
        if x >= 0 || y < 0 {
            (y - x) as u32
        } else {
            let neg_x: u32 = if x == i32::MIN {
                0x80000000u32
            } else {
                (-x) as u32
            };
            y as u32 + neg_x
        }
    }
}

fn mean_absolute_deviation(numbers: &[i32]) -> (result: u32)
    requires
        numbers.len() > 0,
    ensures
        result == spec_mean_absolute_deviation(numbers@.map(|_index, n: i32| n as int)),
{
    let numbers_mean: i32 = compute_mean_of_i32s(numbers);
    let ghost deviations = numbers@.map(|_index, n: i32| n as int).map(
        |_index, n: int| abs(n - numbers_mean),
    );
    let mut quotient: u32 = 0;
    let mut remainder: usize = 0;
    let numbers_len: usize = numbers.len();
    for i in 0..numbers_len
    {
        let n: u32 = compute_absolute_difference(numbers[i], numbers_mean);

        let q: u32 = (n as usize / numbers_len) as u32;
        let r: usize = n as usize % numbers_len;

        if r >= numbers_len - remainder {
            remainder -= (numbers_len - r);
            quotient += (q + 1);
        } else {
            remainder += r;
            quotient += q;
        }
    }
    quotient
}

}
fn main() {}
