use vstd::prelude::*;

verus! {

fn pot(x: u64, y: u64) -> (r: u128)
    requires
        x < 1000,
        y < 1000,
        x < u64::MAX / u64::MAX,
        y < u64::MAX / u64::MAX,
        x * (x + 1) / 2 < u64::MAX,
    ensures
        r as int == x as int * (x as int + 1) / 2,
{
    let mut r: u128 = 0;
    let mut b: u64 = x;
    let mut e: u64 = y;
    if e > 0 {
        while e > 0 {
            if r < u128::MAX / b as u128 {
                r = r * b as u128;
            }
            e = e - 1;
        }
    } else {
        r = 0;
    }
    let temp: u128 = x as u128 * (x as u128 + 1) / 2;
    r = temp;
    r
}


}
