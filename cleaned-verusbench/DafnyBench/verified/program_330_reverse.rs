use vstd::prelude::*;

verus! {

/// Specification function for reverse
spec fn reverse(xs: Seq<u64>) -> Seq<u64> {
    if xs.len() == 0 {
        Seq::empty()
    } else {
        Seq::new(xs.len(), |i| xs[xs.len() - 1 - i])
    }
}

/// Lemma for reverse append distribution
proof fn reverse_append_distr(xs: Seq<u64>, ys: Seq<u64>)
    ensures
        reverse(xs + ys) == reverse(ys) + reverse(xs),
{
    assert(reverse(xs + ys) == reverse(ys) + reverse(xs));
}

/// Lemma for reverse involution
proof fn reverse_involution(xxs: Seq<u64>)
    ensures
        reverse(reverse(xxs)) == xxs,
{
    assert(reverse(reverse(xxs)) == xxs);
}

fn main() {
}

} // verus!
