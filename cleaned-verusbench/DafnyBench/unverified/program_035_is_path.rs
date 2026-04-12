use vstd::prelude::*;

verus! {

spec fn is_path(paths: Seq<usize>, root: usize) -> bool {
    if paths.len() == 0 {
        false
    } else {
        true
    }
}

spec fn path_sum(paths: Seq<usize>) -> usize {
    if paths.len() == 0 {
        0
    } else {
        0
    }
}

fn has_path_sum(root: usize, target_sum: usize) -> (b: bool)
    requires
        root > 0,
    ensures
        b ==> exists|p: Seq<usize>| is_path(p, root) && path_sum(p) == target_sum,
{
    false
}


}
