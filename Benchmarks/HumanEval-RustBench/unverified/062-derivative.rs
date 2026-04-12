use vstd::prelude::*;

verus! {

fn derivative(xs: &Vec<usize>) -> (ret: Option<Vec<usize>>)
    ensures
        ret.is_some() ==> xs@.len() == 0 || xs@.map(|i: int, x| i * x).skip(1)
            =~= ret.unwrap()@.map_values(|x| x as int),
{
    let mut ret = Vec::new();
    if xs.len() == 0 {
        return Some(ret);
    }
    let mut i = 1;
    while i < xs.len()
    {
        ret.push(xs[i].checked_mul(i)?);

        let ghost prods = xs@.map(|i: int, x| i * x);

        i += 1;
    }
    Some(ret)
}

}
fn main() {}
