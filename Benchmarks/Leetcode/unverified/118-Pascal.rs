use power2::pow2;
use vstd::arithmetic::power2;
use vstd::prelude::*;

verus! {

// pub open spec fn triangle(num_rows:nat) -> Seq<nat>
//   recommends num_rows > 0,
//   decreases num_rows
// {
//   if num_rows == 1 { seq![1] }
//   else {
//     let prev = triangle((num_rows - 1) as nat);
//     let
//   }
// }
#[verifier::loop_isolation(false)]
pub fn generate(num_rows: i32) -> (res: Vec<Vec<i32>>)
    requires
        1 <= num_rows <= 30,
    ensures
        res.len() == num_rows,
        forall|k: int| 0 <= k < num_rows ==> #[trigger] res[k].len() == k + 1,
        forall|k: int| 0 <= k < num_rows ==> #[trigger] res[k][0] == 1,
        forall|k: int| 0 <= k < num_rows ==> #[trigger] res[k][k] == 1,
        forall|k: int, m: int|
            (1 <= k < num_rows && 1 <= m < k) ==> #[trigger] res[k][m] == res[k - 1][m - 1] + res[k
                - 1][m],
{
    let mut res: Vec<Vec<i32>> = Vec::with_capacity(num_rows as usize);
    let mut vec_0 = Vec::new();
    vec_0.push(1);
    res.push(vec_0);

    for i in 1..num_rows {
        let mut new_v = Vec::with_capacity((i + 1) as usize);
        new_v.push(1i32);

        for j in 1..i {
            new_v.push(res[(i - 1) as usize][j as usize] + res[(i - 1) as usize][(j - 1) as usize]);
        }
        new_v.push(1i32);
        res.push(new_v)
    }

    return res;
}

} // verus!
fn main() {}
