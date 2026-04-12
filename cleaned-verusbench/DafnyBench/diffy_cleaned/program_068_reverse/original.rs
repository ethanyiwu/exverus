use vstd::prelude::*;

verus! {

# [doc = " Function to reverse a sequence"]
fn reverse(xs: Vec<i32>) -> (r: Vec<i32>)
    requires
        xs.len() < 1000,
    ensures
        r.len() == xs.len(),
        forall|i: int| 0 <= i < xs.len() ==> r[i] == xs[xs.len() - 1 - i],
{
    let mut r: Vec<i32> = Vec::new();
    for i in 0..xs.len() {
        r.push(xs[xs.len() - 1 - i]);
    }
    r
}

# [doc = " Function to check if reversing a sequence twice results in the original sequence"]
fn reverse_involution(xs: Vec<i32>) -> (r: Vec<i32>)
    requires
        xs.len() < 1000,
    ensures
        r.len() == xs.len(),
        forall|i: int| 0 <= i < xs.len() ==> r[i] == xs[i],
{
    let r = reverse(reverse(xs));
    r
}


}
