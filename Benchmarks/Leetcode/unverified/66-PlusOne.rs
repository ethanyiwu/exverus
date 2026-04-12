use vstd::prelude::*;

verus! {

pub open spec fn to_nat(s: Seq<u32>) -> nat
    recommends
        forall|i: int| 0 <= i < s.len() ==> s[i] < 10,
    decreases s,
{
    if s.len() == 0 {
        0
    } else {
        (to_nat(s.drop_last()) * 10 + s.last()) as nat
    }
}

pub open spec fn precondition(s: Seq<u32>) -> bool {
    &&& 1 <= s.len() <= 100
    &&& forall|i: int| 0 <= i < s.len() ==> 0 <= #[trigger] s[i] <= 9
    &&& s.len() != 0 ==> s[0] != 0
}

pub fn plus_one(digits_0: Vec<u32>) -> (res: Vec<u32>)
    requires
        precondition(digits_0@),
    ensures
        to_nat(res@) == to_nat(digits_0@) + 1,
{
    let ghost digits_old = digits_0;

    let mut digits = digits_0;
    let len = digits.len();

    for i in 0..len {
        let tmp = digits[(len - i - 1) as usize];
        if tmp == 9 {
            digits.set((len - i - 1) as usize, 0);
        } else {
            let ghost head = digits@.subrange(0, len - i);

            digits.set((len - i - 1) as usize, tmp + 1);

            return digits;
        }
    }

    digits.push(0);
    digits.set(0, 1);
    return digits;
}

} // verus!
fn main() {}
