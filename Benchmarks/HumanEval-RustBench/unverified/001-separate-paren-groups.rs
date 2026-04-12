use vstd::prelude::*;

verus! {

fn separate_paren_groups(input: &Vec<char>) -> (groups: Vec<Vec<char>>)
    requires
        is_sequence_of_balanced_groups(input@),
    ensures
        forall|i: int|
            #![trigger groups[i]]
            0 <= i < groups.len() ==> is_balanced_group(groups[i]@),
        vecs_to_seqs(groups@).flatten() == remove_nonparens(input@),
{
    let mut groups: Vec<Vec<char>> = Vec::new();
    let mut current_group: Vec<char> = Vec::new();
    let input_len = input.len();
    let ghost mut ghost_groups: Seq<Seq<char>> = Seq::empty();
    let mut current_nesting_level: usize = 0;
    for pos in 0..input_len
    {
        let ghost prev_group = current_group@;
        let ghost prev_groups = ghost_groups;
        let c = input[pos];
        if c == '(' {
            current_nesting_level = current_nesting_level + 1;
            current_group.push('(');
        } else if c == ')' {
            current_nesting_level = current_nesting_level - 1;
            current_group.push(')');
            if current_nesting_level == 0 {
                proof {
                    ghost_groups = ghost_groups.push(current_group@);
                }
                groups.push(current_group);
                current_group = Vec::<char>::new();
            }
        }
    }
    groups
}

}
fn main() {}
