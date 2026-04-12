use vstd::prelude::*;

verus! {

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

struct TextAlign {
    h_align: HAlign,
    v_align: VAlign,
}

enum GraphicsAlign {
    Square,
    Round,
}

enum PageElement {
    Text(TextAlign),
    Graphics(GraphicsAlign),
}

fn num_page_elements() -> (elt_set: Vec<PageElement>)
    requires
        true,
    ensures
        elt_set.len() == 11,
{
    let mut max_set: Vec<PageElement> = Vec::new();
    max_set.push(PageElement::Text(TextAlign { h_align: HAlign::Left, v_align: VAlign::Top }));
    max_set.push(PageElement::Text(TextAlign { h_align: HAlign::Left, v_align: VAlign::Middle }));
    max_set.push(PageElement::Text(TextAlign { h_align: HAlign::Left, v_align: VAlign::Bottom }));
    max_set.push(PageElement::Text(TextAlign { h_align: HAlign::Center, v_align: VAlign::Top }));
    max_set.push(PageElement::Text(TextAlign { h_align: HAlign::Center, v_align: VAlign::Middle }));
    max_set.push(PageElement::Text(TextAlign { h_align: HAlign::Center, v_align: VAlign::Bottom }));
    max_set.push(PageElement::Text(TextAlign { h_align: HAlign::Right, v_align: VAlign::Top }));
    max_set.push(PageElement::Text(TextAlign { h_align: HAlign::Right, v_align: VAlign::Middle }));
    max_set.push(PageElement::Text(TextAlign { h_align: HAlign::Right, v_align: VAlign::Bottom }));
    max_set.push(PageElement::Graphics(GraphicsAlign::Square));
    max_set.push(PageElement::Graphics(GraphicsAlign::Round));
    max_set
}


}
