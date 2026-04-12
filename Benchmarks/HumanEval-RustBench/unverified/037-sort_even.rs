use vstd::prelude::*;

verus! {

#[verifier::loop_isolation(false)]
fn sort_pred(l: Vec<i32>, p: Vec<bool>) -> (l_prime: Vec<i32>)
    requires
        l.len() == p.len(),
    ensures
        l_prime.len() == l.len(),
        forall|i: int| 0 <= i < l.len() && !p[i] ==> l_prime[i] == l[i],
        forall|i: int, j: int|
            #![auto]
            0 <= i < j < l.len() && p[i] && p[j] ==> l_prime[i] <= l_prime[j],
        permutes(l_prime@, l@),
{
    let ghost old_l = l@;
    let l_len = l.len();
    let mut pos_replace: usize = 0;
    let mut l_prime: Vec<i32> = l;
    while pos_replace < l_len
    {
        if p[pos_replace] {
            let mut pos_cur: usize = pos_replace;
            let mut pos: usize = pos_replace;
            while pos < l_len
            {
                if p[pos] && l_prime[pos] < l_prime[pos_cur] {
                    pos_cur = pos;
                }
                pos = pos + 1;
            }
            let v1 = l_prime[pos_replace];
            let v2 = l_prime[pos_cur];
            l_prime.set(pos_replace, v2);
            l_prime.set(pos_cur, v1);
        }
        pos_replace = pos_replace + 1;
    }
    l_prime
}

#[verifier::loop_isolation(false)]
fn sort_even(l: Vec<i32>) -> (result: Vec<i32>)
    ensures
        l.len() == result.len(),
        permutes(result@, l@),
        forall|i: int| 0 <= i < l.len() && i % 2 == 1 ==> result[i] == l[i],
        forall|i: int, j: int|
            #![auto]
            0 <= i < j < l.len() && i % 2 == 0 && j % 2 == 0 ==> result[i] <= result[j],
{
    let mut p: Vec<bool> = vec![];
    for i in 0..l.len()
    {
        p.push(i % 2 == 0);
    }
    sort_pred(l, p)
}

}
fn main() {}
