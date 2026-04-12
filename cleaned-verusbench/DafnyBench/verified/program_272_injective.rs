use vstd::prelude::*;

verus! {

/// Specification function for injective
spec fn injective(x: int, y: int) -> bool {
    x == y
}

/// Proof function for injective
proof fn injective_proof(x: int, y: int)
    requires
        x == y,
    ensures
        injective(x, y),
{
    assert(x == y);
}

/// Function for negate
fn negate(x: int) -> int {
    -x
}

/// Specification function for quant0
spec fn quant0(s: Seq<char>) -> bool {
    s.len() > 0 && (s[0] >= 'a' && s[0] <= 'z' || s[0] >= 'A' && s[0] <= 'Z') && forall|i: int|
        1 <= i && i < s.len() ==> (s[i] >= 'a' && s[i] <= 'z' || s[i] >= 'A' && s[i] <= 'Z' || s[i]
            >= '0' && s[i] <= '9')
}

/// Proof function for quant0
proof fn quant0_proof(s: Seq<char>)
    requires
        quant0(s),
    ensures
        quant0(s),
{
    assert(s.len() > 0);
    assert(s[0] >= 'a' && s[0] <= 'z' || s[0] >= 'A' && s[0] <= 'Z');
    assert(forall|i: int|
        1 <= i && i < s.len() ==> (s[i] >= 'a' && s[i] <= 'z' || s[i] >= 'A' && s[i] <= 'Z' || s[i]
            >= '0' && s[i] <= '9'));
}

fn main() {
}

} // verus!
