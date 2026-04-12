use vstd::prelude::*;

verus! {

fn non_zero_return(x: i32) -> (y: i32)
    requires
        x == 0 || x != 0,
    ensures
        y != 0,
{
    if x == 0 {
        let temp: i32 = x + 1;
        assert(temp != 0);
        return temp;
    } else {
        let temp: i32 = if x == i32::MIN {
            i32::MAX
        } else {
            -x
        };
        assert(temp != 0);
        return temp;
    }
}

fn test() {
    let input = non_zero_return(-1);
    assert(input != 0);
}

fn main() {
}

} // verus!
