use std::collections::HashMap;
use vstd::prelude::*;

verus! {

broadcast use vstd::std_specs::hash::group_hash_axioms;

pub open spec fn letter_of(n: nat) -> Seq<char>
    recommends
        2 <= n <= 9,
{
    if n == 2 {
        seq!['a', 'b', 'c']
    } else if n == 3 {
        seq!['d', 'e', 'f']
    } else if n == 4 {
        seq!['g', 'h', 'i']
    } else if n == 5 {
        seq!['j', 'k', 'l']
    } else if n == 6 {
        seq!['m', 'n', 'o']
    } else if n == 7 {
        seq!['p', 'q', 'r', 's']
    } else if n == 8 {
        seq!['t', 'u', 'v']
    } else if n == 9 {
        seq!['w', 'x', 'y', 'z']
    } else {
        seq![]
    }
}

pub fn letter_map() -> (res: HashMap::<i32, Vec<char>>)
    ensures
        res@.dom() =~= set![2i32, 3, 4, 5, 6, 7, 8, 9],
        forall|i: i32| 2 <= i <= 9 ==> res@[i]@ =~= #[trigger] letter_of(i as nat),
{
    let mut letter_map = HashMap::<i32, Vec<char>>::new();
    letter_map.insert(2, vec!['a', 'b', 'c']);
    letter_map.insert(3, vec!['d', 'e', 'f']);
    letter_map.insert(4, vec!['g', 'h', 'i']);
    letter_map.insert(5, vec!['j', 'k', 'l']);
    letter_map.insert(6, vec!['m', 'n', 'o']);
    letter_map.insert(7, vec!['p', 'q', 'r', 's']);
    letter_map.insert(8, vec!['t', 'u', 'v']);
    letter_map.insert(9, vec!['w', 'x', 'y', 'z']);
    letter_map
}

pub open spec fn is_comb(str: Vec<char>, index: int, v: Seq<i32>) -> bool {
    &&& str.len() == index
    &&& forall|i: int| 0 <= i < index ==> #[trigger] letter_of(v[i] as nat).contains(str[i])
}

pub open spec fn is_comb_0(str: Vec<char>, v: Seq<i32>) -> bool {
    is_comb(str, v.len() as int, v)
}

pub open spec fn coincide(v1: Vec<char>, v2: Vec<char>, index: int) -> bool {
    &&& index <= v1.len()
    &&& index <= v2.len()
    &&& forall|i: int| 0 <= i < index ==> v1[i] == v2[i]
}

// pub open spec fn myview<T>(v:Vec<Vec<T>>) -> Seq<Seq<T>>{
//   let v = v.view();
//   Seq::new(v.len(), |i: int| v[i]@)
// }
fn testff() {
    let x = vec![vec![1usize], vec![2usize, 3]];
}

//If set loop_isolation, I cannot prove that the fn terminates, it is a bug ?
#[verifier::loop_isolation(false)]
pub fn helper(
    v: &Vec<i32>,
    index: usize,
    len: usize,
    acc: &mut Vec<Vec<char>>,
    map: &HashMap<i32, Vec<char>>,
    tmp: Vec<char>,
)
    requires
        len > 0,
        tmp.len() == index,
        v.len() == len,
        forall|i: int| 0 <= i < v.len() ==> 2 <= #[trigger] v@[i] <= 9,
        0 <= index <= len,
        is_comb(tmp, index as int, v@),
        map@.dom() =~= set![2i32, 3, 4, 5, 6, 7, 8, 9],
        forall|i: i32| 2 <= i <= 9 ==> map@[i]@ =~= #[trigger] letter_of(i as nat),
        forall|i: int|
            0 <= i < old(acc).len() ==> #[trigger] is_comb(
                old(acc)@[i],
                len as int,
                v@,
            ),
// forall |str:Vec<char>| tmp@ =~= str@.subrange(0, index) &&
//   is_comb(str, len as int, v@) ==> old(ans).contains()

    ensures
        forall|i: int| 0 <= i < acc.len() ==> #[trigger] is_comb(acc@[i], len as int, v@),
        forall|str: Vec<char>|
            tmp@ =~= str@.subrange(0, index as int) && is_comb(str, len as int, v@)
                ==> #[trigger] acc.deep_view().contains(str@),
        acc.len() >= old(acc).len(),
        old(acc)@ =~= acc@.subrange(0, old(acc).len() as int),
    decreases len - index,
{
    if index == len {
        acc.push(tmp);
        return ;
    }
    let new_chiffre = v[index];
    let new_letters = map.get(&new_chiffre).unwrap();

    for j in 0..new_letters.len() {
        let mut new_str = tmp.clone();
        new_str.push(new_letters[j]);

        let ghost acc_prev = *acc;
        helper(v, index + 1, len, acc, map, new_str);

    }
}

pub fn letter_combination(digits: Vec<i32>) -> (ans: Vec<Vec<char>>)
    requires
        forall|i: int| 0 <= i < digits.len() ==> 2 <= #[trigger] digits@[i] <= 9,
    ensures
        forall|i: int| 0 <= i < ans.len() ==> #[trigger] is_comb_0(ans@[i], digits@),
        forall|str: Vec<char>| #[trigger]
            is_comb_0(str, digits@) ==> ans.deep_view().contains(str@),
{
    if digits.len() == 0 {
        let ans = vec![vec![]];
        return ans;
    }
    let letter_map = letter_map();
    let mut ans = vec![];
    let tmp = vec![];

    helper(&digits, 0, digits.len(), &mut ans, &letter_map, tmp);

    return ans;
}

} // verus!
//veurs!
fn main() {}
