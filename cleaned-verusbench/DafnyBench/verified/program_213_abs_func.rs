use vstd::prelude::*;

verus! {

fn abs_func(x: i32) -> (y: i32)
    requires
        x >= 0,
    ensures
        y >= 0,
{
    if x < 0 {
        -x
    } else {
        x
    }
}

fn foo(x: i32)
    requires
        x >= 0,
{
    let y: i32 = abs_func(x);
}

fn main() {
}

} // verus!
