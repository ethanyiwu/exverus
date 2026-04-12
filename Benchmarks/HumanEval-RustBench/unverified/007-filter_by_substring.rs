use vstd::prelude::*;

verus! {

fn string_eq(s1: &str, s2: &str) -> (result: bool)
    ensures
        result <==> s1@ == s2@,
{
    let s1_len = s1.unicode_len();
    let s2_len = s2.unicode_len();
    if s1_len != s2_len {
        return false;
    }
    for i in 0..s1_len
    {
        let c = s1.get_char(i);
        if c != s2.get_char(i) {
            return false;
        }
    }
    true
}

fn check_substring(s: &str, sub: &str) -> (result: bool)
    ensures
        result <==> exists|i: int|
            0 <= i <= s@.len() - sub@.len() && s@.subrange(i, #[trigger] (i + sub@.len())) == sub@,
{
    let s_len = s.unicode_len();
    let sub_len = sub.unicode_len();
    if (s_len < sub_len) {
        return false;
    }
    if sub_len == 0 {
        return true;
    }
    for i in 0..s_len - sub_len + 1
    {
        if string_eq(sub, s.substring_char(i, i + sub_len)) {
            return true;
        }
    }
    false
}

fn filter_by_substring<'a>(strings: &Vec<&'a str>, substring: &str) -> (res: Vec<&'a str>)
    ensures
        forall|i: int|
            0 <= i < strings@.len() && (exists|j: int|
                0 <= j <= strings@[i]@.len() - substring@.len() && strings[i]@.subrange(
                    j,
                    #[trigger] (j + substring@.len()),
                ) == substring@) ==> res@.contains(#[trigger] (strings[i])),
{
    let mut res = Vec::new();
    for n in 0..strings.len()
    {
        if check_substring(strings[n], substring) {
            let ghost res_old = res;
            res.push(strings[n]);
        }
    }
    res
}

}
fn main() {}
