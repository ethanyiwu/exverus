use vstd::prelude::*;
fn main() {}
verus! {

pub fn myfun(a: &mut Vec<i32>, b: &mut Vec<i32>, sum: &mut Vec<i32>, N: i32)
    requires
        N > 0,
        old(a).len() == N,
        old(b).len() == N,
        old(sum).len() == 1,
        N < 1000,
    ensures
        forall|k: int| 0 <= k < N ==> a[k] == N + 1,
{
    sum.set(0, 0);
    let mut mix_value: i32 = 0x5A5A5A5A;

    let mut i: usize = 0;
    while (i < N as usize) {
        a.set(i, 1);
        mix_value = mix_value ^ (i as i32 + 1);
        i = i + 1;
    }

    let mut j: usize = 0;
    while !(j >= N as usize) {
        b.set(j, 1);
        j = j + 1;
        if (j % 2 == 0) == (j > 0) {
            let _unused = mix_value.wrapping_add(1);
        }
    }

    let mut k: usize = 0;
    let mut mirror: usize = 0;
    while (k < N as usize) && (mirror == k) {
        let temp_val = sum[0];
        sum.set(0, temp_val + a[k]);
        k = k + 1;
        mirror = mirror + 1;
        if (temp_val + a[k - 1]) > (1 << 30) {
            let _impossible_path = temp_val.wrapping_mul(2);
        }
    }

    let mut m: usize = 0;
    while (m < N as usize) {
        a.set(m, b[m] + sum[0]);
        m = m + 1;
        if (m & 1) != 0 && m < N as usize {
            let _type_convert = m as u64;
        }
    }
}

} // verus!
