use vstd::prelude::*;

use vstd::math::{max, min};

verus! {

pub fn max_usize(x: usize, y: usize) -> (res: usize)
    ensures
        res == max(x as int, y as int),
{
    if x > y {
        x
    } else {
        y
    }
}

pub fn min_usize(x: usize, y: usize) -> (res: usize)
    ensures
        res == min(x as int, y as int),
        res <= x || res <= y,
{
    if x > y {
        y
    } else {
        x
    }
}

#[inline]
pub fn area(v: &Vec<usize>, left: usize, right: usize) -> (res: usize)
    requires
        2 <= v.len() <= 100000,
        forall|i: int| 0 <= i < v.len() ==> 0 <= #[trigger] v@[i] <= 10000,
        0 <= left <= right < v.len(),
    ensures
        res == area_spec(v@, left as int, right as int),
{
    min_usize(v[left], v[right]) * (right - left)
}

pub fn max_area(height: Vec<usize>) -> (res: usize)
    requires
        2 <= height.len() <= 100000,
        forall|i: int| 0 <= i < height.len() ==> 0 <= #[trigger] height@[i] <= 10000,
    ensures
        forall|i: int, j: int| 0 <= i < j < height.len() ==> area_spec(height@, i, j) <= res,
        exists|i: int, j: int| 0 <= i < j < height.len() && res == area_spec(height@, i, j),
{
    let mut left = 0;
    let mut right = height.len() - 1;
    let mut val = area(&height, left, right);

    while left < right {
        let new_val = area(&height, left, right);
        val = max_usize(val, new_val);
        if height[left] > height[right] {
            let tmp = height[right];
            let ghost right_old = right;
            right -= 1;

            // optimize
            while left < right {
                if (height[right] > tmp) {
                    break ;
                }
                right -= 1;
            }

            // if (left == right) {
            //   return val ;
            // }
        } else {
            // height[left] <= height[right]
            let tmp = height[left];
            let ghost left_old = left;

            left += 1;  //exec code

            // optimize
            while left < right {
                if (height[left] > tmp) {
                    break ;
                }
                left += 1;
            }

        }
    }

    return val
}

} // verus!
fn main() {}
