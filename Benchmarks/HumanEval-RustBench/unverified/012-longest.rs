use vstd::prelude::*;

verus! {

fn longest(strings: &Vec<Vec<u8>>) -> (result: Option<&Vec<u8>>)
    ensures
        expr_inner_longest(strings, result),
{
    if strings.len() == 0 {
        return None;
    }
    let mut result: &Vec<u8> = &strings[0];
    let mut pos = 0;

    for i in 1..strings.len()
    {
        if result.len() < strings[i].len() {
            result = &strings[i];
            pos = i;
        }
    }
    Some(result)
}

}
fn main() {}
