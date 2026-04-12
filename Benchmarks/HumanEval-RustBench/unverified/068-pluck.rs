use vstd::prelude::*;

verus! {

fn pluck_smallest_even(nodes: &Vec<u32>) -> (result: Vec<u32>)
    requires
        nodes@.len() <= u32::MAX,
    ensures
        result@.len() == 0 || result@.len() == 2,
        result@.len() == 0 ==> forall|i: int| 0 <= i < nodes@.len() ==> nodes@[i] % 2 != 0,
        result@.len() == 2 ==> {
            let node = result@[0];
            let index = result@[1];
            &&& 0 <= index < nodes@.len()
            &&& nodes@[index as int] == node
            &&& node % 2 == 0
            &&& forall|i: int|
                0 <= i < nodes@.len() && nodes@[i] % 2 == 0 ==> node <= nodes@[i] && forall|i: int|
                    0 <= i < result@[1] ==> nodes@[i] % 2 != 0 || nodes@[i] > node
        },
{
    let mut smallest_even: Option<u32> = None;
    let mut smallest_index: Option<u32> = None;

    for i in 0..nodes.len()
    {
        if nodes[i] % 2 == 0 && (smallest_even.is_none() || nodes[i] < smallest_even.unwrap()) {
            smallest_even = Some(nodes[i]);
            smallest_index = Some((i as u32));
        }
    }
    if smallest_index.is_none() {
        Vec::new()
    } else {
        vec![smallest_even.unwrap(), smallest_index.unwrap()]
    }
}

}
fn main() {}
