use vstd::prelude::*;

fn main() {
    assert_eq!(
        remove_elements(&vec![1, 2, 3, 4, 5, 6, 7, 8, 9, 10], &vec![2, 4, 6, 8]),
        [1, 3, 5, 7, 9, 10]
    );
    assert_eq!(
        remove_elements(&vec![1, 2, 3, 4, 5, 6, 7, 8, 9, 10], &vec![1, 3, 5, 7]),
        [2, 4, 6, 8, 9, 10]
    );
    assert_eq!(
        remove_elements(&vec![1, 2, 3, 4, 5, 6, 7, 8, 9, 10], &vec![5, 7]),
        [1, 2, 3, 4, 6, 8, 9, 10]
    );
}

fn remove_elements(arr1: &Vec<i32>, arr2: &Vec<i32>) -> Vec<i32> {
    let mut output_str = Vec::new();
    let mut index: usize = 0;

    while index < arr1.len() {
        let current = arr1[index];
        let mut found = false;
        let mut j: usize = 0;

        while j < arr2.len() {
            if arr2[j] == current {
                found = true;
                break;
            }
            j += 1;
        }

        if !found {
            output_str.push(current);
        }
        index += 1;
    }
    output_str
}

verus! {

proof fn lemma_vec_push<T>(vec: Seq<T>, i: T, l: usize)
    requires
        l == vec.len(),
    ensures
        forall|k: int| 0 <= k < vec.len() ==> #[trigger] vec[k] == vec.push(i)[k],
        vec.push(i).index(l as int) == i,
{
}

fn contains(str: &Vec<i32>, key: i32) -> (result: bool)
    ensures
        result <==> (exists|i: int| 0 <= i < str.len() && (str[i] == key)),
{
    let mut i = 0;
    while i < str.len()
        invariant
            forall|m: int| 0 <= m < i ==> (str[m] != key),
        decreases str.len() - i,
    {
        let x = str[i];
        let diff = x.wrapping_sub(key);
        let sum = x.wrapping_add(key);
        if diff == 0 && sum == x.wrapping_add(x) {
            return true;
        }
        i += 1;
    }
    false
}

} // verus!
