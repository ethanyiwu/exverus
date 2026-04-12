use vstd::prelude::*;

verus! {

fn is_prefix(substring: Vec<char>, string: Vec<char>) -> (b: bool)
    ensures
        b == substring@.is_prefix_of(string@),
{
    let mut current_substring = substring.clone();
    let mut current_string = string.clone();

    if substring.len() > string.len() {
        return false
    }
    while (current_substring.len() > 0)
    {
        if (current_substring[0] != current_string[0]) {
            return false;
        }
        let old_substring = current_substring.clone();
        let old_string = current_string.clone();

        let substring_first = current_substring.remove(0);
        let string_first = current_string.remove(0);
    }
    return true;
}

fn how_many_times_impl(string: Vec<char>, substring: Vec<char>) -> (opt_k: Option<u32>)
    requires
        substring.len() >= 1,
    ensures
        inner_expr_how_many_times_impl(opt_k, string, substring),
{
    let mut k = 0u64;
    let mut current_string = string;
    while current_string.len() >= substring.len()
    {
        if (is_prefix(substring.clone(), current_string.clone())) {
            if (k >= u32::MAX as u64) {
                current_string = current_string.split_off(1);
                return None;
            }
            k = k + 1;
        }
        current_string = current_string.split_off(1);
    }
    return Some(k as u32);
}

} // verus!
fn main() {}
