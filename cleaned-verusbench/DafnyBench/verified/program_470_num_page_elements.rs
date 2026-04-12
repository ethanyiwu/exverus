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

fn num_page_elements() -> (elt_set: Vec<HAlign>)
    requires
        true,
    ensures
        elt_set.len() == 3,
{
    let mut max_set: Vec<HAlign> = Vec::new();
    max_set.push(HAlign::Left);
    max_set.push(HAlign::Center);
    max_set.push(HAlign::Right);
    max_set
}

fn subset_cardinality<T>(a: Vec<T>, b: Vec<T>) -> (result: bool)
    requires
        a.len() <= b.len(),
    ensures
        result == (a.len() <= b.len()),
{
    assert(a.len() <= b.len());
    true
}

fn main() {
}

} // verus!
