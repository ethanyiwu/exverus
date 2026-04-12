use vstd::prelude::*;

verus! {

// 这是一个虚拟的 main 函数，Verus 会忽略它，但它是合法的 Rust 代码结构
fn main() {}

/// 计算 1 + 2 + ... + n 的和
fn calculate_sum(n: u64) -> (sum: u64)
    requires
        n < 200,
    ensures
        sum == n * (n + 1) / 2,
{
    let mut sum: u64 = 0;
    let mut i: u64 = 0;

    while i < n
        invariant
            i <= n,
            sum == i,
        decreases n - i,
    {
        i = i + 1;
        sum = sum + i;
    }
    sum
}

}

cex we get :
sum = 1, i = 1, n = 3 // real execution
sum = 2, i = 2, n = 3 // spurious 

