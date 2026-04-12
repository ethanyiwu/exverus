use vstd::prelude::*;

verus! {

# [derive (Debug , PartialEq , Eq)]
enum HAlign {
    Left,
    Center,
    Right,
}

# [derive (Debug , PartialEq , Eq)]
enum VAlign {
    Top,
    Middle,
    Bottom,
}

# [derive (Debug , PartialEq , Eq)]
struct TextAlign {
    h_align: HAlign,
    v_align: VAlign,
}

# [derive (Debug , PartialEq , Eq)]
enum GraphicsAlign {
    Square,
    Round,
}

# [derive (Debug , PartialEq , Eq)]
enum PageElement {
    Text(TextAlign),
    Graphics(GraphicsAlign),
}

fn num_h_align() -> (count: u32)
    ensures
        count == 3,
{
    let mut count: u32 = 0;
    match HAlign::Left {
        _ => count += 1,
    }
    match HAlign::Center {
        _ => count += 1,
    }
    match HAlign::Right {
        _ => count += 1,
    }
    count
}


}
