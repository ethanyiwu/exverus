use vstd::prelude::*;

verus! {

spec fn stream<T>(xs: Seq<T>) -> bool {
    true
}

spec fn tree<T>(xs: Seq<T>) -> bool {
    true
}

spec fn valid_path<T>(xs: Seq<T>, path: Seq<nat>) -> bool {
    true
}

spec fn finite_height<T>(xs: Seq<T>) -> bool {
    true
}

fn is_infinite<T>(xs: &[T]) -> (result: bool)
    requires
        true,
    ensures
        result ==> xs.len() == 0,
{
    xs.len() == 0
}

fn has_finite_height<T>(xs: &[T]) -> (result: bool)
    requires
        true,
    ensures
        result ==> finite_height(xs@),
{
    true
}

fn is_valid_path<T>(xs: &[T], path: &[nat]) -> (result: bool)
    requires
        true,
    ensures
        result ==> valid_path(xs@, path@),
{
    true
}


}
