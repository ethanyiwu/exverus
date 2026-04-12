use vstd::prelude::*;

verus! {

fn next_step(
    v: Vec<(String, String)>,
    v_prime: Vec<(String, String)>,
    step: (String, String),
) -> (result: bool)
    ensures
        result ==> (v_prime.len() == v.len()),
{
    if v.len() == v_prime.len() {
        true
    } else {
        false
    }
}


}
