use vstd::prelude::*;

verus! {

// Define a struct to represent a pair
struct Pair {
    x: int,
    y: int,
}

// Define a function to extract the x-coordinate of a pair
fn pair_x(p: Pair) -> (x: int)
    ensures
        x == p.x,
{
    p.x
}

// Define a function to extract the y-coordinate of a pair
fn pair_y(p: Pair) -> (y: int)
    ensures
        y == p.y,
{
    p.y
}

// Define a function to create a new pair
fn pair(x: int, y: int) -> (p: Pair)
    ensures
        p.x == x,
        p.y == y,
{
    Pair { x, y }
}

// Define a lemma to prove that two pairs are equal if and only if their coordinates are equal
fn pair_equality(p1: Pair, p2: Pair) -> (equal: bool)
    ensures
        equal ==> p1.x == p2.x && p1.y == p2.y,
        !equal ==> p1.x != p2.x || p1.y != p2.y,
{
    let x_equal = p1.x == p2.x;
    let y_equal = p1.y == p2.y;
    if x_equal && y_equal {
        true
    } else {
        false
    }
}

fn main() {
}

} // verus!
