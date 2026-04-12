use vstd::prelude::*;

verus! {

/// Verus version of lemma_vacuous_statement_about_a_sequence
proof fn lemma_vacuous_statement_about_a_sequence(intseq: Seq<int>, j: int)
    requires
        0 <= j && j < intseq.len(),
    ensures
        intseq.take(j) == intseq.take(j),
{
    assert(intseq.take(j) == intseq.take(j));
}

/// Verus version of lemma_painful_statement_about_a_sequence
proof fn lemma_painful_statement_about_a_sequence(intseq: Seq<int>)
    ensures
        intseq == intseq,
{
    assert(intseq == intseq);
}

/// Verus version of lemma_obvious_statement_about_a_sequence
proof fn lemma_obvious_statement_about_a_sequence(boolseq: Seq<bool>, j: int)
    requires
        0 <= j && j < boolseq.len() - 1,
    ensures
        boolseq.skip(1).take(boolseq.len() - 1)[j] == boolseq[j + 1],
{
    assert(boolseq.skip(1).take(boolseq.len() - 1)[j] == boolseq[j + 1]);
}

/// Verus version of lemma_obvious_statement_about_a_sequence_int
proof fn lemma_obvious_statement_about_a_sequence_int(intseq: Seq<int>, j: int)
    requires
        0 <= j && j < intseq.len() - 1,
    ensures
        intseq.skip(1).take(intseq.len() - 1)[j] == intseq[j + 1],
{
    assert(intseq.skip(1).take(intseq.len() - 1)[j] == intseq[j + 1]);
}

/// Verus version of lemma_straightforward_statement_about_a_sequence
proof fn lemma_straightforward_statement_about_a_sequence(intseq: Seq<int>, j: int)
    requires
        0 <= j && j < intseq.len(),
    ensures
        intseq.take(j) + intseq.skip(j) == intseq,
{
    assert(intseq.take(j) + intseq.skip(j) == intseq);
}

/// Verus version of lemma_sequence_reduction
proof fn lemma_sequence_reduction(s: Seq<int>, b: int)
    requires
        0 < b && b < s.len(),
    ensures
        s.take(b).take(b - 1) == s.take(b - 1),
{
    let t = s.take(b);
    assert(s.take(b).take(b - 1) == s.take(b - 1));
}

/// Verus version of lemma_seq_concatenation_associative
proof fn lemma_seq_concatenation_associative(a: Seq<int>, b: Seq<int>, c: Seq<int>)
    ensures
        (a + b) + c == a + (b + c),
{
    assert((a + b) + c == a + (b + c));
}

/// Verus version of lemma_subseq_concatenation
proof fn lemma_subseq_concatenation(s: Seq<int>, left: int, middle: int, right: int)
    requires
        0 <= left && left <= middle && middle <= right && right <= s.len(),
    ensures
        s.skip(left).take(right - left) == s.skip(left).take(middle - left) + s.skip(middle).take(
            right - middle,
        ),
{
    assert(s.skip(left).take(right - left) == s.skip(left).take(middle - left) + s.skip(
        middle,
    ).take(right - middle));
}

/// Verus version of lemma_seq_equality
proof fn lemma_seq_equality(a: Seq<int>, b: Seq<int>, len: int)
    requires
        a.len() == b.len() && a.len() == len,
        forall|i: int| 0 <= i && i < len ==> a[i] == b[i],
    ensures
        a == b,
{
    assert(a == b);
}

/// Verus version of lemma_seq_suffix
proof fn lemma_seq_suffix(s: Seq<int>, prefix_length: int, index: int)
    requires
        0 <= prefix_length && prefix_length <= index && index < s.len(),
    ensures
        s[index] == s.skip(prefix_length)[index - prefix_length],
{
    assert(s[index] == s.skip(prefix_length)[index - prefix_length]);
}

fn main() {
}

} // verus!
