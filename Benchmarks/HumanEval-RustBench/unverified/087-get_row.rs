use std::vec::Vec;
use vstd::prelude::*;

verus! {

fn get_row(lst: Vec<Vec<i32>>, x: i32) -> (coords: Vec<(usize, usize)>)
    ensures
        coords_matches_lst(lst.deep_view(), x, coords@),
        row_sorted_asc(coords@),
        row_col_sorted_desc(coords@),
{
    let mut coords: Vec<(usize, usize)> = Vec::new();
    for i in 0..lst.len()
    {
        let n = lst[i].len();
        for j in 0..n
        {
            if (lst[i][n - 1 - j] == x) {

                coords.push((i, n - 1 - j));

            }
        }
    }
    return coords;
}

} // verus!
fn main() {}
