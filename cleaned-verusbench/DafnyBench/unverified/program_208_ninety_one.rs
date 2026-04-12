use vstd::prelude::*;

verus! {

fn ninety_one(x: i32, prove_functional_postcondition: bool) -> (z: i32)
    requires
        prove_functional_postcondition ==> x > 101 ==> x - 10 == 91,
    ensures
        prove_functional_postcondition ==> z == if x > 101 {
            x - 10
        } else {
            91
        },
{
    if x > 101 {
        x - 10
    } else {
        91
    }
}

fn gcd(x1: u64, x2: u64) -> (result: u64)
    requires
        x1 >= 1,
        x2 >= 1,
        x1 < 1000000,
        x2 < 1000000,
    ensures
        result >= 1,
{
    let mut y1 = x1;
    let mut y2 = x2;
    loop
        invariant
            y1 >= 1,
            y2 >= 1,
        decreases y1 + y2,
    {
        if y1 == y2 {
            break ;
        } else if y1 > y2 {
            y1 = y1 - y2;
        } else {
            y2 = y2 - y1;
        }
    }
    y1
}


}
