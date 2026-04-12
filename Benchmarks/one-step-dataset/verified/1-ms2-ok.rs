use vstd::prelude::*;
fn main() {}
verus!{

#[verifier::loop_isolation(false)]

pub fn myfun(a: &mut Vec<usize>, sum: &mut Vec<usize>, N: usize) 
	requires 
		old(a).len() == N,
		old(sum).len() == 1,
		N > 0,
	ensures
		sum[0] <= N,
{
	let mut i: usize = 0;
	while (i < N as usize)
		invariant
			i <= N,
			a.len() == N,
			sum.len() == 1,
			forall |k: int| 0 <= k < i ==> a[k] == (k % 2) as usize,
		decreases(N - i)
	{
		a.set(i, i % 2 );
		i = i + 1;
	}

	i = 0;
	
	while (i < N as usize)
		invariant
			i <= N,
			a.len() == N,
			sum.len() == 1,
			forall |k: int| 0 <= k < N ==> a[k] == (k % 2) as usize,
			i > 0 ==> sum[0] <= i,
		decreases(N - i)
	{
		if (i == 0) {
			sum.set(0, 0);
		} else {
			let temp = sum[0];
			sum.set(0, temp + a[i]);
		}
		i = i + 1;
	}
}
}