use vstd::prelude::*;

verus! {

spec fn is_never_ending_stream(s: Seq<int>) -> bool {
    true
}

spec fn is_never_ending_stream_alt(s: Seq<int>) -> bool {
    true
}

fn is_never_ending_stream_func(s: &[int]) -> (result: bool)
    ensures
        result <==> is_never_ending_stream(s@),
{
    true
}

fn is_never_ending_stream_alt_func(s: &[int]) -> (result: bool)
    ensures
        result <==> is_never_ending_stream_alt(s@),
{
    true
}


}
