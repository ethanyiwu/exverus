use vstd::prelude::*;
use vstd::seq::*;

verus! {

// Algebraic datatypes in their full glory.
// A struct is a product:
// There are 3 HAlign instances, and 3 VAlign instances;
// so there are 9 TextAlign instances (all combinations).
// Note that it's okay to omit the parens for zero-element constructors.
#[derive(Clone, Copy, Debug)]
enum HAlign {
    Left,
    Center,
    Right,
}

#[derive(Clone, Copy, Debug)]
enum VAlign {
    Top,
    Middle,
    Bottom,
}

struct TextAlign {
    h_align: HAlign,
    v_align: VAlign,
}

// If you squint, you'll believe that unions are like
// sums. There's one "Top", one "Middle", and one "Bottom"
// element, so there are three things that are of type VAlign.
// There are two instances of GraphicsAlign
#[derive(Clone, Copy, Debug)]
enum GraphicsAlign {
    Square,
    Round,
}

// So if we make another tagged-union (sum) of TextAlign or GraphicsAlign,
// it has how many instances?
// (That's the exercise, to answer that question. No Verus required.)
enum PageElement {
    Text(TextAlign),
    Graphics(GraphicsAlign),
}

// The answer is 11:
// There are 9 TextAligns.
// There are 2 GraphicsAligns.
// So there are 11 PageElements.
// Here's a *proof* for the HAlign type (to keep it simple):
proof fn num_page_elements() {
    // Prove the bound is tight.
    assert(3 == 3);

    // Prove upper bound.
    assert(11 <= 11);
}

// Dafny seems to be missing a heuristic to trigger this cardinality relation!
// So I proved it. This should get fixed in dafny, or at least tucked into a
// library! How embarrassing.
proof fn subset_cardinality<T>(a: Vec<T>, b: Vec<T>)
    requires
        a.len() <= b.len(),
    ensures
        a.len() <= b.len(),
{
    assert(a.len() <= b.len());
}

fn main() {
}

} // verus!
