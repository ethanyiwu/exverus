use vstd::prelude::*;

verus! {

fn non_zero_return(x: i32) -> (y: i32)
    requires
        x != i32::MIN,
    ensures
        y != 0,
{
    if x == 0 {
        return x + 1;
    } else {
        return -x;
    }
}

fn test() {
    let input: i32 = non_zero_return(-1);
    assert(input != 0);
}

fn main() {
}

} // verus!
