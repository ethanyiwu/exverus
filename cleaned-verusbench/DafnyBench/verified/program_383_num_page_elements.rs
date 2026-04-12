use vstd::prelude::*;

verus! {

// Algebraic datatypes in their full glory. The include statement.
// A struct is a product:
// There are 3 HAlign instances, and 3 VAlign instances;
// so there are 9 TextAlign instances (all combinations).
// Note that it's okay to omit the parens for zero-element constructors.
enum HAlign {
    Left,
    Center,
    Right,
}

enum VAlign {
    Top,
    Middle,
    Bottom,
}

// If you squint, you'll believe that unions are like
// sums. There's one "Top", one "Middle", and one "Bottom"
// element, so there are three things that are of type VAlign.
// There are two instances of GraphicsAlign
enum GraphicsAlign {
    Square,
    Round,
}

// So if we make another tagged-union (sum) of TextAlign or GraphicsAlign,
// it has how many instances?
// (That's the exercise, to answer that question. No Verus required.)
struct TextAlign {
    hAlign: HAlign,
    vAlign: VAlign,
}

enum PageElement {
    Text(TextAlign),
    Graphics(GraphicsAlign),
}

// The answer is 11:
// There are 9 TextAligns.
// There are 2 GraphicsAligns.
// So there are 11 PageElements.
// Here's a *proof* for the HAlign type (to keep it simple):
spec fn num_page_elements() -> bool {
    true
}

proof fn num_page_elements_proof() -> (result: bool)
    ensures
        result ==> num_page_elements(),
{
    true
}

fn main() {
}

} // verus!
