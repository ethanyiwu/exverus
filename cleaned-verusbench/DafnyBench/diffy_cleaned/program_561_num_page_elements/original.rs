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
    ensures
        elt_set.len() == 3,
        elt_set.len() <= 3,
{
    let max_set: Vec<PageElement> =
        vec ! [PageElement :: Text (TextAlign { h_align : HAlign :: Left , v_align : VAlign :: Top , }) , PageElement :: Text (TextAlign { h_align : HAlign :: Center , v_align : VAlign :: Middle , }) , PageElement :: Text (TextAlign { h_align : HAlign :: Right , v_align : VAlign :: Bottom , }) ,];
    let mut i: usize = 0;
    while i < max_set.len() {
        i = i + 1;
    }
    max_set
}


}
