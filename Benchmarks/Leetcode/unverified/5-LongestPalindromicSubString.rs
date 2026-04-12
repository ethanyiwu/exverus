use vstd::prelude::*;

verus! {

/// Check vstd/seq_lib.rs
// pub open spec fn reverse(self) -> Seq<A>
//     decreases self.len(),
// {
//     if self.len() == 0 {
//         Seq::empty()
//     } else {
//         Seq::new(self.len(), |i: int| self[self.len() - 1 - i])
//     }
// }
pub open spec fn is_palindromic<T>(s: Seq<T>) -> bool {
    s.reverse() =~= s
}

// end not included
// [start, end)
pub open spec fn is_sub_palindromic<T>(s: Seq<T>, start: int, end: int) -> bool {
    is_palindromic(s.subrange(start, end)) || s.len() == 0
}

pub open spec fn sub_pal_center_at_smaller<T>(s: Seq<T>, i: int, j: int, upper: int) -> bool {
    &&& 0 <= i <= j <= s.len()
    &&& i == j || i + 1 == j
    &&& if i == j {
        let expand_len = (upper - 1) / 2;
        (i - expand_len < 0) || (j + expand_len >= s.len()) || (s[i - expand_len] != s[j
            + expand_len])
    } else {
        let expand_len = upper / 2 - 1;
        (i - expand_len < 0) || (j + expand_len >= s.len()) || (s[i - expand_len] != s[j
            + expand_len])
    }
}

#[verifier::loop_isolation(false)]
fn expand(s: &Vec<u8>, mut i: isize, mut j: isize, left: &mut usize, right: &mut usize)
    requires
        0 < s@.len() <= 1000000,
        0 <= i <= s@.len(),
        i <= j <= s@.len(),
        s@.len() >= *old(right) >= *old(left) >= 0,
        i == j || j == i + 1,
        is_sub_palindromic(s@, *old(left) as int, *old(right) + 1),
    ensures
        s@.len() >= *right >= *left >= 0,
        is_sub_palindromic(s@, *left as int, *right + 1),
        forall|k: int|
            (&&i == j && i - k >= 0 && j + k < s@.len() && #[trigger] is_sub_palindromic(
                s@,
                i - k,
                j + k + 1,
            )) ==> 2 * k + 1 <= *right - *left + 1,
        forall|k: int|
            (&&i + 1 == j && i - k >= 0 && j + k < s@.len() && #[trigger] is_sub_palindromic(
                s@,
                i - k,
                j + k + 1,
            )) ==> 2 * k + 2 <= *right - *left + 1,
        *right - *left >= *old(right) - *old(left),
{
    let ghost i_old = i;
    let ghost j_old = j;

    let ghost current_len = *right - *left;

    while i >= 0 && j < s.len() as isize && s[i as usize] == s[j as usize] {
        if (j - i) as usize > *right - *left {
            *left = i as usize;
            *right = j as usize;
        }
        i -= 1;
        j += 1;
    }

}

pub fn longest_palindrome_aux(s: Vec<u8>) -> (res: (usize, usize))
    requires
        0 < s@.len() <= 1000_000  // for ease
        ,
    ensures
// return res : (left, right)
// refers to the index of substring, [left, right], right included
// Existence
// the length is : res.1 - res.0 + 1

        is_sub_palindromic(s@, res.0 as int, res.1 + 1),
        // Maximal
        // notice that :
        //       is_sub_palindromatic(s@, p, q)
        //  <==> s@.subrange(p, q).is_palindromatic()
        //  thus, s@.subrange(p, q).len() == q - p <= res.1 - res.0 + 1
        forall|p: int, q: int|
            0 <= p < q <= s@.len() && is_sub_palindromic(s@, p, q) ==> q - p <= res.1 - res.0 + 1,
{
    // Convert string to char vector
    let mut left = 0;
    let mut right = 0;
    let len = s.len();

    for i in 0..len {
        // Odd length palindrome
        expand(&s, i as isize, i as isize, &mut left, &mut right);
        // Even length palindrome
        expand(&s, i as isize, i as isize + 1, &mut left, &mut right);
    }
    // Return the longest palindrome substring
    (left, right)
}

//// We just need to use the same method used in P3; But we do not want to repeat this procedure...
//// To make our life easier, from this problem on, we will regard each String problem as a Vec<u8> Problem
pub fn longest_palindrome(s: String) -> (res: (usize, usize))
    requires
        s.is_ascii(),
        0 < s@.len() <= 1000_000  // for ease
        ,
    ensures
        true,
{
    let s_chars: Vec<u8> = s.as_str().as_bytes_vec();
    longest_palindrome_aux(s_chars)
}

} // verus!
fn main() {}
