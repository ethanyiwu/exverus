use vstd::prelude::*;

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

pub open spec fn reverse_spec(x: nat) -> nat
    decreases x,
{
    if x < 10 {
        x
    } else {
        (x % 10) * pow10(count_digits(x / 10)) + reverse_spec(x / 10)
    }
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
pub fn isPalindrome(mut x: u32) -> (res: bool)
    ensures
        to_seq(x as nat).reverse() =~= to_seq(x as nat)
            <==> res,
// res == true ==> to_seq(x as nat).reverse() =~= to_seq(x as nat),

{
    let ghost x_old = x as nat;

    if (x % 10 == 0 && x != 0) {
        return false;
    }
    if x == 0 {
        return true
    }
    let mut rev = 0;

    let digit = x % 10;
    rev = rev * 10 + digit;
    x = x / 10;

    while x > rev {
        //prove no overflow
        let ghost rev_prev = rev as nat;
        let ghost x_prev = x as nat;

        let digit = x % 10;
        rev = rev * 10 + digit;
        x = x / 10;
    }

    return x == rev || x == (rev / 10)
}

} // verus!
fn main() {}
