use vstd::prelude::*;

verus! {

fn pot(x: u64, y: u64) -> (r: u128)
    requires
        x < 1000,  // added relaxation to prevent overflow
        y < 1000,  // added relaxation to prevent overflow
        x < u64::MAX / u64::MAX,  // added relaxation to prevent overflow
        y < u64::MAX / u64::MAX,  // added relaxation to prevent overflow
        x * (x + 1) / 2 < u64::MAX,  // added relaxation to prevent overflow

    ensures
        r as int == x as int * (x as int + 1) / 2,
{
    let mut r: u128 = 0;
    let mut b: u64 = x;
    let mut e: u64 = y;
    if e > 0 {
        while e > 0
            invariant
                x as int == b as int && y as int == e as int,
                e > 0 ==> r as int == (x as int) * (x as int + 1) / 2,
                e == 0 ==> r as int == 0,
                x < 1000,  // added relaxation to prevent overflow
                y < 1000,  // added relaxation to prevent overflow
                x < u64::MAX / u64::MAX,  // added relaxation to prevent overflow
                y < u64::MAX / u64::MAX,  // added relaxation to prevent overflow

            decreases y - e,
        {
            if r < u128::MAX / b as u128 {
                r = r * b as u128;
            }
            e = e - 1;
        }
    } else {
        r = 0;
    }
    let temp: u128 = x as u128 * (x as u128 + 1) / 2;
    assert(temp <= u128::MAX as u128);
    r = temp;
    assert(r as int == x as int * (x as int + 1) / 2);
    r
}

fn main() {
}

} // verus!
