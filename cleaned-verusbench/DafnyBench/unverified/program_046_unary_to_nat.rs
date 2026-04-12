use vstd::prelude::*;

verus! {

struct Unary {
    val: int,
}

fn unary_to_nat(x: &Unary) -> (n: int)
    requires
        true,
    ensures
        n == x.val,
{
    x.val
}

fn nat_to_unary(n: int) -> (x: Unary)
    requires
        true,
    ensures
        x.val == n,
{
    Unary { val: n }
}


}
