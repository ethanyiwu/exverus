use vstd::prelude::*;
// use vstd::math::min;

verus! {

//correct ?
pub open spec fn valid_index(s: Seq<char>, len: int, acc: int) -> bool
    recommends
        len <= s.len(),
        len >= 0,
    decreases len,
{
    if len < 0 || acc < 0 {
        false
    } else if len == 0 {
        acc == 0
    } else {
        let c = s[len - 1];
        if c == '(' {
            &&& valid_index(s, len - 1, acc - 1)
        } else if c == ')' {
            &&& valid_index(s, len - 1, acc + 1)
        } else {
            false
        }
    }
}

pub open spec fn count_lpar(s: Seq<char>) -> nat
    decreases s,
{
    if s.len() == 0 {
        0
    } else {
        if s.last() == '(' {
            1 + count_lpar(s.drop_last())
        } else {
            count_lpar(s.drop_last())
        }
    }
}

// the main specification of valide parentheses
pub open spec fn valid_par(s: Seq<char>) -> bool {
    valid_index(s, s.len() as int, 0)
}

pub fn helper(tmp: Vec<char>, ans: &mut Vec<Vec<char>>, lp: usize, rp: usize, len: usize)
    requires
        len >= 1,
        0 <= rp <= lp <= len,
        tmp.len() == lp + rp,
        count_lpar(tmp@) == lp,
        valid_index(tmp@, lp + rp, lp - rp),
        forall|i: int| 0 <= i < old(ans).len() ==> #[trigger] valid_par(old(ans)@[i]@),
        forall|i: int| 0 <= i < old(ans).len() ==> #[trigger] old(ans)@[i].len() == 2 * len,
    ensures
        forall|i: int| 0 <= i < ans.len() ==> #[trigger] valid_par(ans@[i]@),
        forall|i: int| 0 <= i < ans.len() ==> #[trigger] ans@[i].len() == 2 * len,
        ans.len() >= old(ans).len(),
        old(ans)@ =~= ans@.subrange(0, old(ans).len() as int),
        forall|p: Vec<char>|
            tmp@ =~= p@.subrange(0, lp + rp) && valid_par(p@) && p.len() == 2 * len
                ==> #[trigger] ans.deep_view().contains(p@),
    decreases len - lp, len - rp,
{
    // broadcast use lemma_count_lpar_push;
    if rp == len {
        ans.push(tmp);
        return ;
    } else if lp == rp {
        let mut str = tmp.clone();
        str.push('(');
        helper(str, ans, lp + 1, rp, len);
        return ;
    } else {
        let mut str2 = tmp.clone();
        str2.push(')');

        helper(str2, ans, lp, rp + 1, len);

        if lp == len {
            return ;
        } else {
            let mut str = tmp.clone();
            str.push('(');
            let ghost ans_prev = *ans;

            helper(str, ans, lp + 1, rp, len);
            return ;
        }

        // let ghost str = tmp@.push(')');
    }
}

pub fn generate(n: usize) -> (ans: Vec<Vec<char>>)
    requires
        n >= 1,
    ensures
        forall|i: int| 0 <= i < ans.len() ==> #[trigger] valid_par(ans@[i]@),
        forall|i: int| 0 <= i < ans.len() ==> #[trigger] ans@[i].len() == 2 * n,
        forall|p: Vec<char>|
            valid_par(p@) && p.len() == 2 * n ==> #[trigger] ans.deep_view().contains(p@),
{
    let mut ans = vec![];
    let tmp = vec![];
    helper(tmp, &mut ans, 0, 0, n);
    return ans;
}

} // verus!
fn main() {}
