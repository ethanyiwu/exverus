use vstd::prelude::*;
use vstd::seq::*;

verus! {

# [derive (Clone , Copy , Debug)]
enum HAlign {
    Left,
    Center,
    Right,
}

# [derive (Clone , Copy , Debug)]
enum VAlign {
    Top,
    Middle,
    Bottom,
}

struct TextAlign {
    h_align: HAlign,
    v_align: VAlign,
}

# [derive (Clone , Copy , Debug)]
enum GraphicsAlign {
    Square,
    Round,
}

enum PageElement {
    Text(TextAlign),
    Graphics(GraphicsAlign),
}


}
