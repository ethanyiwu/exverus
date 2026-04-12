use vstd::prelude::*;

verus! {

pub closed spec fn concat_helper(strings: Seq<Seq<char>>, i: nat) -> Seq<char>
    recommends
        i <= strings.len(),
    decreases strings.len() - i,
{
    if (i >= strings.len()) {
        seq![]
    } else {
        strings[i as int] + concat_helper(strings, i + 1)
    }
}

pub open spec fn concatenate(strings: Seq<Seq<char>>) -> Seq<char> {
    concat_helper(strings, 0)
}

proof fn sanity_check() {
}

fn concatenate_impl(strings: Vec<Vec<char>>) -> (joined: Vec<char>)
    ensures
        joined@ == concatenate(strings.deep_view()),
{
    let mut i = 0;
    let mut joined = vec![];

    while (i < strings.len())
        invariant
            concatenate(strings.deep_view()) == joined@ + concat_helper(
                strings.deep_view(),
                i as nat,
            ),
        decreases strings.len() - i,
    {

        let mut copy_str = strings[i].clone();
        joined.append(&mut copy_str);
        i = i + 1;
    }
    return joined;
}

} // verus!
fn main() {
    let test1 = vec![vec!['a'], vec!['b'], vec!['c']];
    let test2: Vec<Vec<char>> = Vec::new();
    let test3 = vec![vec!['a', 'z'], vec!['b'], vec!['c', 'y']];

    print!("concatenation of {:?}:\n", test1);
    print!("{:?}\n", concatenate_impl(test1));
    print!("concatenation of {:?}:\n", test2);
    print!("{:?}\n", concatenate_impl(test2));
    print!("concatenation of {:?}:\n", test3);
    print!("{:?}\n", concatenate_impl(test3));
}

/*
### VERUS END
*/

/*
### PROMPT
from typing import List


def concatenate(strings: List[str]) -> str:
    """ Concatenate list of strings into a single string
    >>> concatenate([])
    ''
    >>> concatenate(['a', 'b', 'c'])
    'abc'
    """

*/

/*
### ENTRY POINT
concatenate
*/

/*
### CANONICAL SOLUTION
    return ''.join(strings)

*/


