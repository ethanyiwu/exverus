use vstd::prelude::*;

verus! {

# [doc = " Tree definition"]
enum Tree {
    Node(Vec<Tree>),
}

# [doc = " Predicate to check if a tree has finite height"]
spec fn has_finite_height(t: Tree) -> bool {
    true
}

# [doc = " Function to check if a tree has finite height"]
fn has_finite_height_func(t: Tree) -> (result: bool)
    ensures
        result == has_finite_height(t),
{
    true
}


}
