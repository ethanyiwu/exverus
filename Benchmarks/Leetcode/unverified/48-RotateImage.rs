use vstd::prelude::*;

verus! {

#[verifier::external_body]
pub fn matrix_update(matrix: &mut Vec<Vec<i32>>, i: usize, j: usize, val: i32)
    requires
        0 <= i < old(matrix)@.len(),
        0 <= j < old(matrix)@[j as int]@.len(),
    ensures
        matrix@.len() == old(matrix)@.len(),
        forall|k: int|
            0 <= k < matrix@.len() && k != i ==> #[trigger] matrix@[k]@ =~= old(matrix)@[k]@,
        matrix@[i as int]@ =~= old(matrix)@[i as int]@.update(j as int, val),
{
    matrix[i][j] = val;
}

pub open spec fn precondition(matrix: Vec<Vec<i32>>) -> bool {
    &&& 1 <= matrix@.len() <= 20
    &&& forall|i: int| 0 <= i < matrix@.len() ==> #[trigger] matrix@[i]@.len() == matrix@.len()
    &&& forall|i: int, j: int|
        0 <= i < matrix@.len() && 0 <= j < matrix@.len() ==> -1000 <= #[trigger] matrix@[i]@[j]
            <= 1000
}

pub open spec fn is_rotate(m1: Vec<Vec<i32>>, m2: Vec<Vec<i32>>) -> bool {
    &&& precondition(m1)  //for ease
    &&& precondition(m2)  //for ease
    &&& m1@.len() == m2@.len()
    &&& forall|i: int, j: int|
        0 <= i < m1@.len() && 0 <= j < m1@.len() ==> m2@[i]@[j] == m1@[m1@.len() - j - 1]@[i]
}

#[verifier::spinoff_prover]
pub fn rotate(matrix: &mut Vec<Vec<i32>>)
    requires
        precondition(*old(matrix)),
    ensures
        is_rotate(*old(matrix), *matrix),
{
    let ghost matrix_old = *matrix;
    let size = matrix.len();

    for a in 0..size / 2 {
        for i in a..size - a - 1 {
            let tmp = matrix[a][i];

            let v1 = matrix[size - 1 - i][a];
            matrix_update(matrix, a, i, v1);
            // matrix[a][i] = matrix[size - 1 - i][a];
            let v2 = matrix[size - 1 - a][size - 1 - i];
            matrix_update(matrix, size - 1 - i, a, v2);
            // matrix[size-1-i][a] = matrix[size - 1 - a][size-1-i];
            let v3 = matrix[i][size - 1 - a];
            matrix_update(matrix, size - 1 - a, size - 1 - i, v3);
            // matrix[size-1-a][size-1-i] = matrix[i][size-1-a];
            matrix_update(matrix, i, size - 1 - a, tmp);
            // matrix[i][size-1-a] = tmp;

        }
    }

}

} // verus!
fn main() {}
