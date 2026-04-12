use vstd::arithmetic::mul::*;
use vstd::prelude::*;

verus! {

fn prime(p: u32) -> (ret: bool)
    ensures
        ret <==> spec_prime(p as int),
{
    if p <= 1 {
        return false;
    }
    for k in 2..p
    {
        if p % k == 0 {
            return false;
        }
    }
    true
}

fn checked_mul_thrice(x: u32, y: u32, z: u32) -> (ret: Option<u32>)
    ensures
        ret.is_some() ==> ret.unwrap() == x * y * z,
        ret.is_none() ==> x * y * z > u32::MAX,
{
    if (x == 0 || y == 0 || z == 0) {
        return Some(0);
    }
    let prod2 = x.checked_mul(y);
    if prod2.is_some() {
        let prod3 = prod2.unwrap().checked_mul(z);
        if prod3.is_some() {
            let ans = prod3.unwrap();
            Some(ans)
        } else {
            None
        }
    } else {
        None
    }
}

fn is_multiply_prime(x: u32) -> (ans: bool)
    requires
        x > 1,
    ensures
        ans <==> exists|a: int, b: int, c: int|
            spec_prime(a) && spec_prime(b) && spec_prime(c) && x == a * b * c,
{
    let mut a = 1;
    while a < x
    {
        a += 1;
        if prime(a) {
            let mut b = 1;
            while b < x
            {
                b += 1;
                if prime(b) {
                    let mut c = 1;
                    while c < x
                    {
                        c += 1;
                        let prod = checked_mul_thrice(a, b, c);
                        if prime(c) && prod.is_some() && x == prod.unwrap() {
                            return true;
                        }
                    }
                }
            }
        }
    }
    false
}

}
fn main() {}
