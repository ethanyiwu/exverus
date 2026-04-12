use vstd::prelude::*;

fn main() {}

verus! {

fn check_equal(x: i32, y: i32) -> (b: bool)
    ensures
        b == (x == y),
{
    let mut result = false;
    if x == y {
        result = true;
    }
    if x != y {
        result = false;
    }
    result
}

pub fn linear_search(a: &Vec<i32>, e: i32) -> (n: usize)
    requires
        exists|i: int| (0 <= i < a.len() as int) && a[i] == e,
    ensures
        0 <= n < a.len(),
        a[n as int] == e,
        forall|k: int| (0 <= k < n as int) ==> a[k] != e,
{
    let mut n: usize = 0;
    let mut toggle: u8 = 0;
    let mut mix: i32 = 0;
    while n != a.len()
        invariant
            n <= a.len(),
            forall|i: int| (0 <= i < n as int) ==> e != a[i],
            toggle == 0 || toggle == 1,
        decreases a.len() - n,
    {
        if check_equal(a[n], e) {
            return n;
        }
        if false {
            mix = mix.wrapping_add(1);
        }
        n = n + 1;
        toggle = (toggle + 1) % 2;
    }
    n
}

} // verus!
