use vstd::prelude::*;

verus! {

// Define the HAlign and VAlign datatypes
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

enum TextAlign {
    TextAlign(HAlign, VAlign),
}

enum GraphicsAlign {
    Square,
    Round,
}

enum PageElement {
    Text(TextAlign),
    Graphics(GraphicsAlign),
}

proof fn num_page_elements() -> (result: int)
    ensures
        result == 11,
{
    assert(HAlign::Left != HAlign::Center);
    assert(HAlign::Left != HAlign::Right);
    assert(HAlign::Center != HAlign::Right);

    assert(VAlign::Top != VAlign::Middle);
    assert(VAlign::Top != VAlign::Bottom);
    assert(VAlign::Middle != VAlign::Bottom);

    assert(GraphicsAlign::Square != GraphicsAlign::Round);

    assert(TextAlign::TextAlign(HAlign::Left, VAlign::Top) != TextAlign::TextAlign(
        HAlign::Left,
        VAlign::Middle,
    ));
    assert(TextAlign::TextAlign(HAlign::Left, VAlign::Top) != TextAlign::TextAlign(
        HAlign::Left,
        VAlign::Bottom,
    ));
    assert(TextAlign::TextAlign(HAlign::Left, VAlign::Middle) != TextAlign::TextAlign(
        HAlign::Left,
        VAlign::Bottom,
    ));

    assert(TextAlign::TextAlign(HAlign::Center, VAlign::Top) != TextAlign::TextAlign(
        HAlign::Center,
        VAlign::Middle,
    ));
    assert(TextAlign::TextAlign(HAlign::Center, VAlign::Top) != TextAlign::TextAlign(
        HAlign::Center,
        VAlign::Bottom,
    ));
    assert(TextAlign::TextAlign(HAlign::Center, VAlign::Middle) != TextAlign::TextAlign(
        HAlign::Center,
        VAlign::Bottom,
    ));

    assert(TextAlign::TextAlign(HAlign::Right, VAlign::Top) != TextAlign::TextAlign(
        HAlign::Right,
        VAlign::Middle,
    ));
    assert(TextAlign::TextAlign(HAlign::Right, VAlign::Top) != TextAlign::TextAlign(
        HAlign::Right,
        VAlign::Bottom,
    ));
    assert(TextAlign::TextAlign(HAlign::Right, VAlign::Middle) != TextAlign::TextAlign(
        HAlign::Right,
        VAlign::Bottom,
    ));

    assert(PageElement::Text(TextAlign::TextAlign(HAlign::Left, VAlign::Top))
        != PageElement::Graphics(GraphicsAlign::Square));

    11
}

fn main() {
}

} // verus!
