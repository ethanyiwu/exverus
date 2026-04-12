use vstd::prelude::*;

verus! {

fn correct_bracketing(brackets: &str) -> (ret: bool)
    requires
        brackets@.len() <= i32::MAX,
        -brackets@.len() >= i32::MIN,
    ensures
        ret <==> spec_bracketing(brackets@),
{
    let mut i = 0;
    let mut b = true;
    let mut stack_size: i32 = 0;

    while i < brackets.unicode_len()
    {
        let c = brackets.get_char(i);
        let ghost prev = spec_bracketing_helper(brackets@.subrange(0, i as int));
        if (c == '(') {
            stack_size += 1;
        } else if (c == ')') {
            b = b && stack_size > 0;
            stack_size -= 1;
        }
        i += 1;
    }
    b && stack_size == 0
}

} // verus!
fn main() {}
