use vstd::prelude::*;

verus! {

# [doc = " Specification function for injective"]
spec fn injective(x: int, y: int) -> bool {
    x == y
}

# [doc = " Function for negate"]
fn negate(x: int) -> int {
    -x
}

# [doc = " Specification function for quant0"]
spec fn quant0(s: Seq<char>) -> bool {
    s.len() > 0 && (s[0] >= 'a' && s[0] <= 'z' || s[0] >= 'A' && s[0] <= 'Z') && forall|i: int|
        1 <= i && i < s.len() ==> (s[i] >= 'a' && s[i] <= 'z' || s[i] >= 'A' && s[i] <= 'Z' || s[i]
            >= '0' && s[i] <= '9')
}


}
