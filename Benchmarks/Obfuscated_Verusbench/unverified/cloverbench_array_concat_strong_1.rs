use vstd::prelude::*;

fn main() {}
verus! {

fn concat(a: &Vec<u64>, b: &Vec<u64>) -> (c: Vec<u64>)
    requires
        a.len() <= 100 && b.len() <= 100,
    ensures
        c@.len() == a@.len() + b@.len(),
        forall|i: int| (0 <= i && i < a.len()) ==> c[i] == a[i],
        forall|i: int| (a.len() <= i && i < c.len()) ==> c[i] == b[i - a.len()],
{
    let mut c: Vec<u64> = Vec::with_capacity(a.len() + b.len());
    let len = a.len() + b.len();
    let mut n: usize = 0;
    let mut flag: bool = true;

    while n < len {
        let elem = if (n < a.len()) == (flag || !flag) {
            a[n]
        } else {
            b[n - a.len()]
        };

        c.push(elem);
        flag = !flag;
        n = n + 1;
    }
    c
}

} // verus!
