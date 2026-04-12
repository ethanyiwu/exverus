use vstd::prelude::*;

verus! {

// pub open spec fn last_space(s:Seq<char>) -> int
//   decreases s
// {
//   if s.len() == 0 { -1 }
//   else {
//     if s[s.len() - 1] == ' ' {s.len() - 1}
//     else {
//       last_space(s.drop_last())
//     }
//   }
// }
// pub open spec fn last_word_before_space(s:Seq<char>) -> Seq<char>
//   decreases s
// {
//   if last_space(s) == -1 {s}
//   else {
//     s.subrange(,)
//   }
// }
// pub open spec fn last_word(s:Seq<char>) -> Seq<char>
// {
//   if s.len() == 0 {seq![]}
//   else {
//   }
// }
//   length, index
pub fn length_of_last_word(s: Vec<char>) -> (res: (i32, Ghost<int>))
    requires
        0 < s.len() < 1000000,
        exists|j: int| 0 <= j < s.len() && s[j] != ' ',
    ensures
        0 <= res.1@ < s.len(),
        forall|j: int| res.1@ < j < s.len() ==> s[j] == ' ',
        forall|j: int| res.1@ - res.0 < j <= res.1@ ==> s[j] != ' ',
        res.1@ - res.0 >= 0 ==> s[res.1@ - res.0]
            == ' ',  // last word not begins at s[0]
{
    let mut res = 0;
    let len = s.len();
    let mut i = (len - 1) as i32;

    let ghost index = -1;  //helper

    while i >= 0 {
        if s[i as usize] != ' ' {
            res += 1;
        } else if res != 0 {
            return (res, Ghost(index));
        }
        i -= 1;
    }

    return (res, Ghost(index));
}

} // verus!
fn main() {}
