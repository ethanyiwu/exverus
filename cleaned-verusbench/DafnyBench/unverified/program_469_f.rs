use vstd::prelude::*;

verus! {

# [doc = " A type for an identifier"]
struct Id;

# [doc = " Function F"]
spec fn f(s: Seq<Id>) -> int;


}
