### **Layout Obfuscation**

#### *Meaningless Identifier Names*:

Strategy: Using single letters or generic words that do not reveal the variable's purpose, making it difficult to understand the code's logic.

Examples:
In verified/diffy_sina3_0.rs

### **Data Obfuscation**
This type of obfuscation aims to hide the true value, origin, or purpose of the data.

#### *Dead/Junk Variables*:

Strategy: Declaring and manipulating variables that have no effect on the final output of the program. The computation process for these variables is intended to distract the analyst.

Examples:
verified/diffy_s22if_0.rs
verified/cloverbench_array_sum_strong_0.rs


#### *Instruction Substitution*:

Strategy: Replacing simple, straightforward calculations or assignment operations with functionally equivalent but more complex expressions.

Examples:

In verified/diffy_s22if_2.rs, a.set(i, (7 - 6) as i32); is used instead of the more direct a.set(i, 1);.

### **Control Flow Obfuscation**
This is the most advanced and effective type of obfuscation, designed to disrupt the program's execution logic.

#### *Dead Code Insertion*:

Strategy: Inserting logic blocks or branches into the code that will never be executed, thereby increasing the complexity of static analysis.

Examples:
In verified/cloverbench_linear_search2_3.rs, there is an if false { ... } block; this code will never be executed.
In verified/diffy_brs2_2.rs, the empty if statements if mix > i32::MAX {} and if acc < 0 {} create branches that perform no operations.

#### *Opaque Predicates*:

Strategy: Constructing a conditional expression whose result is known at the time of obfuscation (always true or always false) but is difficult or impossible for a static analysis tool to determine without running the code. This is often used to force the program down a specific branch while compelling the analysis tool to consider all possible paths.

Examples:

In the final loop of verified/diffy_condg_0.rs
In verified/cloverbench_is_prime_2.rs

#### *Redundant or Equivalent Conditional Branches*:

Strategy: Creating an if-else structure where both branches execute identical or equivalent operations, unnecessarily complicating the control flow.

Examples:

In verified/diffy_s5if_1.rs
In verified/diffy_condg_2.rs
In verified/diffy_s4if_4.rs