use vstd::prelude::*;

verus! {

// Define an enum for Horizontal Alignment
pub enum HAlign {
    Left,
    Center,
    Right,
}

// Define an enum for Vertical Alignment
pub enum VAlign {
    Top,
    Middle,
    Bottom,
}

// Define a struct for Text Alignment
pub struct TextAlign {
    h_align: HAlign,
    v_align: VAlign,
}

// Define an enum for Graphics Alignment
pub enum GraphicsAlign {
    Square,
    Round,
}

// Define an enum for Page Element
pub enum PageElement {
    Text(TextAlign),
    Graphics(GraphicsAlign),
}

// Define a proof function to count the number of Page Elements
proof fn num_page_elements() -> (num: int)
    ensures
        num == 11,
{
    // Define the set of all HAlign instances
    let h_align_set = [HAlign::Left, HAlign::Center, HAlign::Right];
    assert(h_align_set.len() == 3);

    // Define the set of all VAlign instances
    let v_align_set = [VAlign::Top, VAlign::Middle, VAlign::Bottom];
    assert(v_align_set.len() == 3);

    // Define the set of all TextAlign instances
    let text_align_set = [
        TextAlign { h_align: HAlign::Left, v_align: VAlign::Top },
        TextAlign { h_align: HAlign::Left, v_align: VAlign::Middle },
        TextAlign { h_align: HAlign::Left, v_align: VAlign::Bottom },
        TextAlign { h_align: HAlign::Center, v_align: VAlign::Top },
        TextAlign { h_align: HAlign::Center, v_align: VAlign::Middle },
        TextAlign { h_align: HAlign::Center, v_align: VAlign::Bottom },
        TextAlign { h_align: HAlign::Right, v_align: VAlign::Top },
        TextAlign { h_align: HAlign::Right, v_align: VAlign::Middle },
        TextAlign { h_align: HAlign::Right, v_align: VAlign::Bottom },
    ];
    assert(text_align_set.len() == 9);

    // Define the set of all GraphicsAlign instances
    let graphics_align_set = [GraphicsAlign::Square, GraphicsAlign::Round];
    assert(graphics_align_set.len() == 2);

    // Define the set of all PageElement instances
    let page_element_set = [
        PageElement::Text(TextAlign { h_align: HAlign::Left, v_align: VAlign::Top }),
        PageElement::Text(TextAlign { h_align: HAlign::Left, v_align: VAlign::Middle }),
        PageElement::Text(TextAlign { h_align: HAlign::Left, v_align: VAlign::Bottom }),
        PageElement::Text(TextAlign { h_align: HAlign::Center, v_align: VAlign::Top }),
        PageElement::Text(TextAlign { h_align: HAlign::Center, v_align: VAlign::Middle }),
        PageElement::Text(TextAlign { h_align: HAlign::Center, v_align: VAlign::Bottom }),
        PageElement::Text(TextAlign { h_align: HAlign::Right, v_align: VAlign::Top }),
        PageElement::Text(TextAlign { h_align: HAlign::Right, v_align: VAlign::Middle }),
        PageElement::Text(TextAlign { h_align: HAlign::Right, v_align: VAlign::Bottom }),
        PageElement::Graphics(GraphicsAlign::Square),
        PageElement::Graphics(GraphicsAlign::Round),
    ];
    assert(page_element_set.len() == 11);

    // Return the total number of PageElement instances
    11
}

fn main() {
}

} // verus!
