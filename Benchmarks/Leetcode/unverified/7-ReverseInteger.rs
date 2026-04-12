use vstd::prelude::*;
// use vstd::math::abs;

//todo

verus! {

pub open spec fn to_seq(i: nat) -> Seq<nat>
    decreases i,
{
    if 0 <= i < 10 {
        seq![i]
    } else {
        to_seq(i / 10).push(i % 10)
    }
}

pub open spec fn to_nat_2(s: Seq<nat>) -> nat
    recommends
        forall|i: int| 0 <= i < s.len() ==> s[i] < 10,
    decreases s,
{
    if s.len() == 0 {
        0
    } else {
        to_nat_2(s.drop_last()) * 10 + s.last()
    }
}

pub open spec fn to_nat(s: Seq<nat>) -> nat
    decreases s,
{
    if s.len() == 0 {
        0
    } else {
        s[0] * pow10((s.len() - 1) as nat) + to_nat(s.subrange(1, s.len() as int))
    }
}

#[verifier::spinoff_prover]
pub open spec fn reverse_nat(n: nat) -> nat {
    to_nat(to_seq(n).reverse())
}

pub open spec fn reverse_int(i: int) -> int {
    if i >= 0 {
        reverse_nat(i as nat) as int
    } else {
        -(reverse_nat((-i) as nat) as int)
    }
}

pub open spec fn reverse_truncate(i: i32) -> i32 {
    let x = reverse_int(i as int);
    if x > i32::MAX || x < i32::MIN {
        0
    } else {
        x as i32
    }
}

pub open spec fn reverse_spec(x: nat) -> nat
    decreases x,
{
    if x < 10 {
        x
    } else {
        (x % 10) * pow10(count_digits(x / 10)) + reverse_spec(x / 10)
    }
}

pub open spec fn no_overflow(x: nat) -> bool {
    reverse_spec(x) <= i32::MAX
}

pub open spec fn count_digits(x: nat) -> nat
    decreases x,
{
    if x == 0 {
        0
    } else {
        1 + count_digits(x / 10)
    }
}

pub open spec fn pow10(n: nat) -> nat
    decreases n,
{
    if n == 0 {
        1
    } else {
        10 * pow10((n - 1) as nat)
    }
}

#[verifier::spinoff_prover]
pub fn reverse(x: u32) -> (res: u32)
    requires
        x >= 0,
    ensures
        no_overflow(x as nat) ==> res == reverse_spec(x as nat),
        !no_overflow(x as nat) ==> res == 0,
{
    let mut num = x;
    let mut reversed = 0;

    while num != 0 {
        let ghost num_old = num as nat;
        let ghost reversed_old = reversed as nat;

        let digit = num % 10;
        num = num / 10;

        if reversed > i32::MAX as u32 / 10 || (reversed == i32::MAX as u32 / 10 && digit > 7) {
            return 0;
        }
        reversed = reversed * 10 + digit;
        let ghost num_val = num;

    }

    reversed
}

} // verus!
fn main() {}
