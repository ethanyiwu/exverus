use vstd::prelude::*;

verus! {

pub enum HAlign {
    Left,
    Center,
    Right,
}

pub enum VAlign {
    Top,
    Middle,
    Bottom,
}

pub struct TextAlign {
    h_align: HAlign,
    v_align: VAlign,
}

pub enum GraphicsAlign {
    Square,
    Round,
}

pub enum PageElement {
    Text(TextAlign),
    Graphics(GraphicsAlign),
}


}
