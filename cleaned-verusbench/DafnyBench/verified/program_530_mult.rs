use vstd::prelude::*;

verus! {

fn mult(x: usize, y: usize) -> (r: usize)
    requires
        x >= 0 && y >= 0 && x * y <= usize::MAX,
    ensures
        r == x * y,
{
    if x == 0 {
        return 0;
    } else if y == 0 {
        return 0;
    } else {
        let temp: u128 = x as u128 * y as u128;
        assert(temp <= usize::MAX as u128);
        let temp: usize = temp as usize;
        assert(temp == x * y);
        temp
    }
}

fn main() {
}

} // verus!
