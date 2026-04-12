use vstd::prelude::*;

verus! {

use std::collections::HashMap;
use vstd::math::max;

broadcast use vstd::std_specs::hash::group_hash_axioms;

pub fn max_i32(a: i32, b: i32) -> (res: i32)
    ensures
        res == max(a as int, b as int),
{
    if a >= b {
        a
    } else {
        b
    }
}

pub open spec fn no_repeat<T>(l: Seq<T>, start: int, end: int) -> bool {
    forall|i: int, j: int| start <= i < j < end ==> l[i] != l[j]
}

pub open spec fn max_no_repeat<T>(l: Seq<T>, end: int, n: int) -> bool {
    forall|i: int, j: int| 0 <= i < j <= end && no_repeat(l, i, j) ==> j - i <= n
}

// defined for using trigger
pub open spec fn is_le_3(x: int, y: int, z: int) -> bool {
    x <= y <= z
}

#[verifier::loop_isolation(false)]
pub fn help(s: Vec<u8>) -> (res: i32)
    requires
        0 <= s@.len() < 5000000,
    ensures
        max_no_repeat(s@, s@.len() as int, res as int),
        exists|p: int, q: int| 0 <= p <= q <= s@.len() && q - p == res && no_repeat(s@, p, q),
{
    let mut hash: HashMap<u8, i32> = HashMap::new();
    let mut ans = 0;
    let mut start = 0;
    let str_len = s.len();

    for end in 0..str_len {
        let ch = s[end as usize];

        let ghost start_old = start;

        match hash.insert(ch, end as i32) {
            None => {},
            Some(i) => {
                start = max_i32(start, i + 1);
            },
        }
        let ghost ans_old = ans;
        ans = max_i32(ans, end as i32 - start + 1);

    }
    ans
}

pub fn length_of_longest_substring(s: String) -> (res: i32)
    requires
        s@.len() < 5000000,
        s.is_ascii(),
    ensures
        max_no_repeat(s@, s@.len() as int, res as int),
        exists|p: int, q: int| 0 <= p <= q <= s@.len() && q - p == res && no_repeat(s@, p, q),
{
    let str = s.as_str();
    // this function allocate a vec;
    // anyhow, currently, I find no better way to iterate the String
    let v = str.as_bytes_vec();
    let res = help(v);
    res
}

} // verus!
fn main() {}
