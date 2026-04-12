use vstd::prelude::*;

verus! {

struct HAlign {
    left: bool,
    center: bool,
    right: bool,
}

struct VAlign {
    top: bool,
    middle: bool,
    bottom: bool,
}

struct TextAlign {
    h_align: HAlign,
    v_align: VAlign,
}

struct GraphicsAlign {
    square: bool,
    round: bool,
}

enum PageElement {
    Text(TextAlign),
    Graphics(GraphicsAlign),
}

spec fn num_page_elements() -> bool {
    true
}

fn num_page_elements_func() -> (result: bool)
    requires
        true,
    ensures
        result,
{
    true
}


}
