use vstd::prelude::*;

verus! {

// Specification
// if s is a solution to climb the stairs from start to end,
pub open spec fn valid(s: Seq<nat>, start: nat, end: nat) -> bool {
    &&& s.len() > 0
    &&& s[0] == start
    &&& s.last() == end
    &&& forall|i: int| 0 < i < s.len() ==> 1 <= #[trigger] s[i] - s[i - 1] <= 2
    &&& forall|i: int, j: int| 0 <= i < j < s.len() ==> s[i] < s[j]
}

// all possible ways to climb the stairs
pub open spec fn climb(i: nat, n: nat) -> Set<Seq<nat>> {
    Set::new(|s: Seq<nat>| valid(s, i, n))
}

//////
// see def of climb
pub open spec fn res_spec(n: nat) -> nat {
    climb(0, n).len()
}

pub fn climb_stairs(n: i32) -> (res: i32)
    requires
        1 <= n <= 45,
        // in fact n <= 45 implies this condition, we can prove it by the lemma commented above
        res_spec(n as nat) < i32::MAX,
    ensures
        res == res_spec(n as nat),
{
    if n == 1 {
        return 1;
    }
    let mut v = Vec::with_capacity((n + 1) as usize);
    v.push(1);
    v.push(1);
    for i in 2..n + 1 {
        let val = v[(i - 1) as usize] + v[(i - 2) as usize];
        v.push(val)
    }

    return v[n as usize]
}

} // verus!
fn main() {}
