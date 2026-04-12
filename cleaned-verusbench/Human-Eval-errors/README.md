Here are 17 examples that can not be easily repaired in alphaverus'results.

x.rs is the input of alphaverus. y.rs is their output which should be the verified program.

I have mentioned in our group chat that 11 out of 17 is decrease issues, here is the specific numbers:

group 1 
36/y.rs: fail
37/y.rs: fail
38/y.rs: fail
39/y.rs: fail
40/y.rs: fail
41/y.rs: fail
42/y.rs: fail
43/y.rs: fail

group 2
54/y.rs: fail
55/y.rs: fail
56/y.rs: fail

6 out of 17 programs reported 
" error: invariant not satisfied at end of loop body
  --> /Users/sun/Downloads/alphaverus-main/datasets/errors/75/y.rs:22:13
   |
22 |             xs@.map(|i: int, x| i * x).subrange(1, i as int) =~= ret@.map_values(|x| x as int),
   |             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

error: possible arithmetic underflow/overflow
  --> /Users/sun/Downloads/alphaverus-main/datasets/errors/75/y.rs:37:18
   |
37 |         ret.push((i as u64) * (xs[i] as u64));
   |                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^

verification results:: 1 verified, 1 errors
error: aborting due to 2 previous errors "

75/y.rs: fail
81/y.rs: fail
82/y.rs: fail
83/y.rs: fail
84/y.rs: fail
85/y.rs: fail