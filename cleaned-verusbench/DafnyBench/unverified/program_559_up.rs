use vstd::prelude::*;

verus! {

# [doc = " Takes an integer and returns a stream of integers starting from that number."]
fn up(n: int) -> (stream: Vec<int>)
    requires
        true,
    ensures
        stream.len() == 1,
        stream[0] == n,
{
    let stream: Vec<int> = vec ! [n];
    stream
}


}
