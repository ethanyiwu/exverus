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


}
