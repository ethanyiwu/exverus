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

// NOTE: We use i32 rather than float because of lack of support for float in Verus.
/// Trusted specification functions
// Specification for what it means to sum a sequence of numbers
pub open spec fn sum(numbers: Seq<int>) -> int {
    numbers.fold_left(0, |acc: int, x| acc + x)
}

// Specification for what it means to compute the mean of a sequence of numbers
pub open spec fn mean(values: Seq<int>) -> int
    recommends
        values.len() > 0,
{
    sum(values) / (values.len() as int)
}

// Specification for what it means to compute the absolute value of a number
pub open spec fn abs(n: int) -> int {
    if n >= 0 {
        n
    } else {
        -n
    }
}

// Specification for what it means to compute the mean absolute deviation of a sequence of numbers
pub open spec fn spec_mean_absolute_deviation(numbers: Seq<int>) -> int
    recommends
        numbers.len() > 0,
{
    let avg = mean(numbers);
    sum(numbers.map(|_index, n: int| abs(n - avg))) / (numbers.len() as int)
}

/// Lemmas used in proving correctness
// This lemma establishes that if every element of a sequence of
// numbers `numbers` is between `min` and `max` inclusive, then their
// sum is between `numbers.len() * min` and `numbers.len() * max`
fn divide_i32_by_u32(x: i32, d: u32) -> (qr: (i32, u32))
    requires
        d > 0,
    ensures
        ({
            let (q, r) = qr;
            q == x as int / d as int && r == x as int % d as int
        }),
{
    // The easy case is when `x` is non-negative.
    if x >= 0 {
        return ((x as u32 / d) as i32, x as u32 % d);
    }
    // When `x` is negative, compute `-x` as a `u32`. This is a bit
    // tricky because of the special case `i32::MIN`.

    let neg_x: u32;
    if x == i32::MIN {
        if d == 1 {
            // If `x == i32::MIN` and `d == 1`, the algorithm below
            // won't work, so we special-case it here.
            return (x, 0);
        } else {
            // For the special case `x == i32::MIN`, we can't negate
            // it (because `-i32::MIN` isn't a valid `i32`). But we
            // can just directly assign the constant value of
            // `-i32::MIN` to a `u32`.
            neg_x = 0x80000000u32;
        }
    } else {
        neg_x = (-x) as u32;
    }

    // Compute `(-x) / d` and `(-x) % d`. We can do this because `-x`
    // is non-negative and Verus supports dividing non-negative
    // numbers.

    let neg_x_div_d = neg_x / d;
    let neg_x_mod_d = neg_x % d;

    // Prove some useful things about `(-x) / d` and `(-x) % d`.

    // There are two cases to consider. Case 1 is when `(-x) % d ==
    // 0`. Case 2 is when it's positive.

    if neg_x_mod_d == 0 {
        (-(neg_x_div_d as i32), 0u32)
    } else {
        (-(neg_x_div_d as i32) - 1, d - neg_x_mod_d)
    }
}

// This function divides an `i32` by a `usize` and returns the
// quotient and remainder. You need this because Verus doesn't support
// using the `/` and `%` operator on negative numbers. And even if it
// did, the Rust versions of `/` of `%` produce "wrong" results for
// negative numbers. That is, Rust rounds towards zero rather than
// computing mathematical quotient and remainder.
fn divide_i32_by_usize(x: i32, d: usize) -> (qr: (i32, usize))
    requires
        d > 0,
    ensures
        ({
            let (q, r) = qr;
            q == x as int / d as int && r == x as int % d as int
        }),
{
    // There are three cases to consider:
    //
    // (1) `d <= u32::MAX`, so we can compute it by calling
    // `divide_i32_by_u32`.
    //
    // (2) `d > u32::MAX` and `x >= 0`, so we know that the
    // quotient and remainder are just `0` and `x`.
    //
    // (3) `d > u32::MAX` and `x < 0`, so we know that the
    // quotient and remainder are `-1` and `d + x`.
    if d <= u32::MAX as usize {
        let (q, r) = divide_i32_by_u32(x, d as u32);
        (q, r as usize)
    } else if x >= 0 {
        (0, x as usize)
    } else {
        // The remainder is `d + x`, but we can't directly add those
        // two values because we can't cast them to the same type. So instead
        // we compute `-x` then use subtraction to compute `d - (-x)`.
        let neg_x: usize = if x == i32::MIN {
            0x80000000usize
        } else {
            (-x) as usize
        };
        (-1, d - neg_x)
    }
}

// This function computes the mean of a slice of `i32`s.
fn compute_mean_of_i32s(numbers: &[i32]) -> (result: i32)
    requires
        numbers.len() > 0,
    ensures
        result == mean(numbers@.map(|_index, n: i32| n as int)),
{
    // The natural way to compute the mean is to first compute the sum
    // and then divide by the length. But this won't be verifiable
    // because we can't prove the absence of overflow when summing the
    // array. So instead we use the following algorithm.
    //
    // We iterate through the elements of the slice, keeping track of
    // the running sum of the first elements indirectly. That is, we
    // don't store that running sum `s` in a variable but rather we
    // keep track of `s / numbers.len()` and `s % numbers.len()`. The
    // former is guaranteed to fit in an `i32` and the latter is
    // guaranteed to fit in a `usize`. We store these in the variables
    // `quotient` and `remainder`. At the end of the loop, we return
    // `quotient` since it's the overall sum divided by the length of
    // the slice.
    let ghost nums = numbers@.map(|_index, n: i32| n as int);
    let mut quotient: i32 = 0;
    let mut remainder: usize = 0;
    let numbers_len: usize = numbers.len();
    for i in 0..numbers_len {
        let n = numbers[i];

        // Prove that:
        //
        // (1) We can go from the running sum of the first `i`
        // elements to the sum of the first `i + 1` elements by adding
        // the `i`the element.
        //
        // (2) The running sum divided by `numbers.len()` is bounded
        // between `i32::MIN` and `i32::MAX`, so the running quotient
        // can be stored in an `i32`.
        //
        // (3) We can update the running quotient and remainder using
        // an algorithm that doesn't need the running sum as input.
        // It just needs the old running quotient and remainder.

        let (q, r) = divide_i32_by_usize(n, numbers_len);

        if r >= numbers_len - remainder {
            // Prove that we won't overflow by adding one to `q`. This
            // follows from the facts that `q == n / numbers_len`,
            // `numbers_len >= 2`, and `q <= i32::MAX`.
            remainder -= (numbers_len - r);
            quotient += (q + 1);
        } else {
            remainder += r;
            quotient += q;
        }
    }
    quotient
}

// This function computes the absolute difference between two `i32`s as a `u32`.
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

/// Target function
pub fn mean_absolute_deviation(numbers: &[i32]) -> (result: u32)
    requires
        numbers.len() > 0,
    ensures
        result == spec_mean_absolute_deviation(numbers@.map(|_index, n: i32| n as int)),
{
    let numbers_mean: i32 = compute_mean_of_i32s(numbers);
    let ghost deviations = numbers@.map(|_index, n: i32| n as int).map(
        |_index, n: int| abs(n - numbers_mean),
    );

    // The natural way to compute the mean absolute deviation is to
    // first compute the sum and then divide by the length. But this
    // won't be verifiable because we can't prove the absence of
    // overflow when summing the deviations. So instead we use the
    // following algorithm.
    //
    // We iterate through the elements of the slice, keeping track of
    // the running sum of the first deviations indirectly. That is, we
    // don't store that running sum `s` in a variable but rather we
    // keep track of `s / numbers.len()` and `s % numbers.len()`. The
    // former is guaranteed to fit in an `u32` and the latter is
    // guaranteed to fit in a `usize`. We store these in the variables
    // `quotient` and `remainder`. At the end of the loop, we return
    // `quotient` since it's the overall sum divided by the length of
    // the slice.

    let mut quotient: u32 = 0;
    let mut remainder: usize = 0;
    let numbers_len: usize = numbers.len();
    for i in 0..numbers_len {
        let n: u32 = compute_absolute_difference(numbers[i], numbers_mean);

        // Prove that:
        //
        // (1) We can go from the running sum of the first `i`
        // elements to the sum of the first `i + 1` elements by adding
        // the `i`the element.
        //
        // (2) The running sum divided by `numbers.len()` is bounded
        // between `u32::MIN` and `u32::MAX`, so the running quotient
        // can be stored in an `u32`.
        //
        // (3) We can update the running quotient and remainder using
        // an algorithm that doesn't need the running sum as input.
        // It just needs the old running quotient and remainder.

        let q: u32 = (n as usize / numbers_len) as u32;
        let r: usize = n as usize % numbers_len;

        if r >= numbers_len - remainder {
            // Prove that we won't overflow by adding one to `q`. This
            // follows from the facts that `q == n / numbers_len`,
            // `numbers_len >= 2`, and `q <= u32::MAX`.
            remainder -= (numbers_len - r);
            quotient += (q + 1);
        } else {
            remainder += r;
            quotient += q;
        }
    }
    quotient
}

} // verus!
fn main() {}
