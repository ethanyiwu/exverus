use vstd::prelude::*;

verus! {

pub open spec fn precondition(v: Vec<u32>) -> bool {
    &&& 1 <= v.len()
    &&& forall|i: int| 0 <= i < v.len() ==> 2 <= #[trigger] v@[i] <= 40
    &&& forall|i: int, j: int|
        0 <= i < j < v.len() ==> v@[i] != v@[j]
    // &&& 1 <= target <= 40

}

pub open spec fn sum(s: Seq<u32>) -> int
    decreases s,
{
    if s.len() == 0 {
        0
    } else {
        sum(s.drop_last()) + s.last()
    }
}

pub fn push_n_times(v: &mut Vec<u32>, x: u32, n: usize)
    ensures
        v@ =~= old(v)@ + seq![x;n as nat],
{
    for i in 0..n {
        v.push(x)
    }
}

#[verifier::loop_isolation(false)]
pub fn helper(
    tmp: Vec<u32>,
    can: &Vec<u32>,
    index: usize,
    target: u32,
    acc: &mut Vec<Vec<u32>>,
    Ghost(total): Ghost<u32>,
)
    requires
        precondition(*can),
        0 <= target <= 40,
        0 <= index <= can.len(),
        // forall |i:int| 0 <= i < tmp.len() ==> #[trigger]can@.contains(tmp@[i]),
        tmp@.to_set().subset_of(can@.to_set()),
        tmp@.to_set().subset_of(can@.subrange(0, index as int).to_set()),
        sum(tmp@) + target == total,
        forall|i: int| 0 <= i < old(acc).len() ==> #[trigger] sum(old(acc)@[i]@) == total,
        forall|i: int|
            0 <= i < old(acc).len() ==> #[trigger] old(acc)@[i]@.to_set().subset_of(can@.to_set()),
    ensures
        old(acc).len() <= acc.len(),
        old(acc)@ =~= acc@.subrange(0, old(acc).len() as int),
        forall|i: int| 0 <= i < acc.len() ==> #[trigger] sum(acc@[i]@) == total,
        forall|i: int| 0 <= i < acc.len() ==> #[trigger] acc@[i]@.to_set().subset_of(can@.to_set()),
        forall|p: Vec<u32>|
            #![all_triggers]
            p.len() >= tmp.len() && tmp@ =~= p@.subrange(0, tmp.len() as int) && p@.subrange(
                tmp.len() as int,
                p.len() as int,
            ).to_set().subset_of(can@.subrange(index as int, can.len() as int).to_set()) && sum(p@)
                == total ==> exists|j: int|
                0 <= j < acc.len() && #[trigger] acc@[j]@.to_multiset()
                    =~= p@.to_multiset()
            // #[trigger] acc.deep_view().contains(p@),
        ,
    decreases can.len() - index,
{
    if target == 0 {
        acc.push(tmp);
        return ;
    }
    if index == can.len() {
        return ;
    }
    let val = can[index];
    let num = target / val;

    helper(tmp.clone(), can, index + 1, target, acc, Ghost(total));

    let mut i = 1;
    let ghost acc_prev = *acc;

    while i <= num {
        let mut v = tmp.clone();
        push_n_times(&mut v, val, i as usize);
        let new_target = target - i * val;

        helper(v, can, index + 1, new_target, acc, Ghost(total));
        i = i + 1;

    }
}

pub fn combination_sum(candidates: Vec<u32>, target: u32) -> (res: Vec<Vec<u32>>)
    requires
        precondition(candidates),
        1 <= target <= 40,
    ensures
        forall|i: int| 0 <= i < res.len() ==> #[trigger] sum(res@[i]@) == target,
        forall|i: int|
            0 <= i < res.len() ==> #[trigger] res@[i]@.to_set().subset_of(candidates@.to_set()),
        forall|p: Vec<u32>|
            #![all_triggers]
            p@.to_set().subset_of(candidates@.to_set()) && sum(p@) == target ==> exists|j: int|
                0 <= j < res.len() && #[trigger] res@[j]@.to_multiset() =~= p@.to_multiset(),
{
    let mut acc = vec![];
    let tmp = vec![];
    helper(tmp, &candidates, 0, target, &mut acc, Ghost(target));

    return acc
}

} // verus!
fn main() {}
