use vstd::prelude::*;

verus! {

// This function is part of the specification
pub open spec fn sum(s: Seq<int>) -> int
    decreases s.len(),
{
    if s.len() == 0 {
        0
    } else {
        s[0] + sum(s.skip(1))
    }
}

// This function is also part of the specification
pub open spec fn first_n(s: Seq<i32>, n: int) -> Seq<int> {
    s.take(n).map(|_idx, j: i32| j as int)
}

// This function is used by the proof
pub open spec fn sum_other_way(s: Seq<int>) -> int
    decreases s.len(),
{
    if s.len() == 0 {
        0
    } else {
        s.last() + sum_other_way(s.drop_last())
    }
}

fn below_zero(operations: Vec<i32>) -> (result: bool)
    ensures
        result <==> exists|i: int|
            0 <= i <= operations@.len() && #[trigger] sum(first_n(operations@, i)) < 0,
{
    let mut s = 0i32;
    let mut num_overflows: usize = 0;
    let ghost max_plus = i32::MAX + 1;
    for k in 0..operations.len() {
        let op = operations[k];
        if op >= 0 {
            if s > i32::MAX - op {
                s += op - i32::MAX - 1;
                num_overflows += 1;
            } else {
                s += op;
            }
        } else {
            s += op;
            if s < 0 {
                if num_overflows == 0 {
                    return true;
                }
                num_overflows -= 1;
                s = s + i32::MAX + 1;
            }
        }
    }
    false
}

} // verus!
fn main() {}
