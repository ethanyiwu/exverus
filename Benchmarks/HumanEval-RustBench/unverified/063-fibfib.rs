use vstd::prelude::*;

verus! {

fn fibfib(x: u32) -> (ret: Option<u32>)
    ensures
        ret.is_some() ==> spec_fibfib(x as nat) == ret.unwrap(),
{
    match (x) {
        0 => Some(0),
        1 => Some(0),
        2 => Some(1),
        _ => fibfib(x - 1)?.checked_add(fibfib(x - 2)?)?.checked_add(fibfib(x - 3)?),
    }
}

}
fn main() {}
