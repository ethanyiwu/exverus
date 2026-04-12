use vstd::prelude::*;

verus! {

// Enumerations are defined using the `enum` keyword.
#[derive(Debug, PartialEq, Eq)]
enum HAlign {
    Left,
    Center,
    Right,
}

#[derive(Debug, PartialEq, Eq)]
enum VAlign {
    Top,
    Middle,
    Bottom,
}

#[derive(Debug, PartialEq, Eq)]
struct TextAlign {
    h_align: HAlign,
    v_align: VAlign,
}

#[derive(Debug, PartialEq, Eq)]
enum GraphicsAlign {
    Square,
    Round,
}

#[derive(Debug, PartialEq, Eq)]
enum PageElement {
    Text(TextAlign),
    Graphics(GraphicsAlign),
}

// Since we are using enums, we do not need to define a function to prove the number of PageElements.
// However, we can define a function to prove the number of HAlign instances.
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

fn main() {
}

} // verus!
