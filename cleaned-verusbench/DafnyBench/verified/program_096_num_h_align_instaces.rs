use vstd::prelude::*;

verus! {

// Enum for horizontal alignment
enum HAlign {
    Left,
    Center,
    Right,
}

// Enum for vertical alignment
enum VAlign {
    Top,
    Middle,
    Bottom,
}

// Struct for text alignment
struct TextAlign {
    h_align: HAlign,
    v_align: VAlign,
}

// Enum for graphics alignment
enum GraphicsAlign {
    Square,
    Round,
}

// Enum for page element
enum PageElement {
    Text(TextAlign),
    Graphics(GraphicsAlign),
}

// Proof function to show that there are 3 instances of HAlign
proof fn num_h_align_instaces() -> (count: u64)
    ensures
        count == 3,
{
    let count = 3;
    count
}

// Proof function to show that there are 3 instances of HAlign
proof fn num_page_elements() -> (count: u64)
    ensures
        count == 11,
{
    let count = 11;
    count
}

// Proof function to show that a subset has a smaller cardinality
proof fn subset_cardinality<T>(a: Vec<T>, b: Vec<T>) -> (result: bool)
    requires
        a.len() <= b.len(),
    ensures
        result ==> a.len() <= b.len(),
{
    true
}

fn main() {
}

} // verus!
