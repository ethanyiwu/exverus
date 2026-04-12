use vstd::prelude::*;

verus! {

fn derivative(xs: &Vec<u32>) -> (ret: Vec<u64>)
    requires
        xs.len() <= u32::MAX,
    ensures
        if xs.len() == 0 {
            ret.len() == 0
        } else {
            ret@.map_values(|x| x as int) =~= xs@.map(|i: int, x| i * x).skip(1)
        },
{
fn main () {}
