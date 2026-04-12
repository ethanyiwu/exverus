use vstd::prelude::*;

verus! {

fn checked_total_str_len(lst: &Vec<&str>) -> (ret: Option<usize>)
    ensures
        ret.is_some() <==> total_str_len(lst@) <= usize::MAX,
        ret.is_some() <==> ret.unwrap() == total_str_len(lst@),
{
    let ghost lens = Seq::<nat>::empty();
    let mut sum: usize = 0;
    for i in 0..lst.len()
    {
        let x = lst[i].unicode_len();
        sum = sum.checked_add(x)?;
    }
    return Some(sum);
}

fn total_match<'a>(lst1: Vec<&'a str>, lst2: Vec<&'a str>) -> (ret: Option<Vec<&'a str>>)
    ensures
        ret.is_some() <== total_str_len(lst1@) <= usize::MAX && total_str_len(lst2@) <= usize::MAX,
        inner_expr_total_match(lst1, lst2, ret),
{
    if checked_total_str_len(&lst1)? <= checked_total_str_len(&lst2)? {
        Some(lst1)
    } else {
        Some(lst2)
    }
}

}
fn main() {}
