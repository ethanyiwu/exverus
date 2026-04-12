use vstd::prelude::*;

verus! {

fn smallest_change(v: Vec<i32>) -> (change: usize)
    requires
        v@.len() < usize::MAX,
    ensures
        change == diff(zip_halves(v@)),
{
    let mut ans: usize = 0;
    let ghost zipped = Seq::<(i32, i32)>::empty();
    for i in 0..v.len() / 2
    {
        if v[i] != v[v.len() - i - 1] {
            ans += 1;
        }
    }
    ans
}

}
fn main() {}
