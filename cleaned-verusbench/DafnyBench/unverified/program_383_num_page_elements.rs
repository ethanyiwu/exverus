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

enum GraphicsAlign {
    Square,
    Round,
}

struct TextAlign {
    hAlign: HAlign,
    vAlign: VAlign,
}

enum PageElement {
    Text(TextAlign),
    Graphics(GraphicsAlign),
}

spec fn num_page_elements() -> bool {
    true
}


}
