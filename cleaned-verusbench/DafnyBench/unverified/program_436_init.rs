use vstd::prelude::*;

verus! {

struct Variables {
    value: int,
}

spec fn init(v: Variables) -> bool {
    v.value == 0
}

spec fn increment_op(v: Variables, v_prime: Variables) -> bool {
    v_prime.value == v.value + 1
}

spec fn decrement_op(v: Variables, v_prime: Variables) -> bool {
    v_prime.value == v.value - 1
}

enum Step {
    Increment,
    Decrement,
}

spec fn next_step(v: Variables, v_prime: Variables, step: Step) -> bool {
    match step {
        Step::Increment => increment_op(v, v_prime),
        Step::Decrement => decrement_op(v, v_prime),
    }
}

spec fn next(v: Variables, v_prime: Variables) -> bool {
    exists|step: Step| next_step(v, v_prime, step)
}

struct VariablesProtocol {
    value: int,
}

spec fn init_protocol(v: VariablesProtocol) -> bool {
    v.value == 0
}

spec fn increment_op_protocol(v: VariablesProtocol, v_prime: VariablesProtocol) -> bool {
    v_prime.value == v.value - 1
}

spec fn decrement_op_protocol(v: VariablesProtocol, v_prime: VariablesProtocol) -> bool {
    v_prime.value == v.value + 1
}

enum StepProtocol {
    Increment,
    Decrement,
}

spec fn next_step_protocol(
    v: VariablesProtocol,
    v_prime: VariablesProtocol,
    step: StepProtocol,
) -> bool {
    match step {
        StepProtocol::Increment => increment_op_protocol(v, v_prime),
        StepProtocol::Decrement => decrement_op_protocol(v, v_prime),
    }
}

spec fn next_protocol(v: VariablesProtocol, v_prime: VariablesProtocol) -> bool {
    exists|step: StepProtocol| next_step_protocol(v, v_prime, step)
}

spec fn abstraction(v: VariablesProtocol) -> Variables {
    Variables { value: v.value }
}

struct PositiveSet {
    store: Vec<int>,
    nelems: int,
}

spec fn init_positive_set(v: PositiveSet) -> bool {
    v.nelems == 0
}

spec fn increment_op_positive_set(v: PositiveSet, v_prime: PositiveSet) -> bool {
    v_prime.nelems == v.nelems + 1
}

spec fn decrement_op_positive_set(v: PositiveSet, v_prime: PositiveSet) -> bool {
    v_prime.nelems == v.nelems - 1
}

enum StepPositiveSet {
    Increment,
    Decrement,
}

spec fn next_step_positive_set(
    v: PositiveSet,
    v_prime: PositiveSet,
    step: StepPositiveSet,
) -> bool {
    match step {
        StepPositiveSet::Increment => increment_op_positive_set(v, v_prime),
        StepPositiveSet::Decrement => decrement_op_positive_set(v, v_prime),
    }
}

spec fn next_positive_set(v: PositiveSet, v_prime: PositiveSet) -> bool {
    exists|step: StepPositiveSet| next_step_positive_set(v, v_prime, step)
}

struct SavingsAccount {
    store: Vec<int>,
    nelems: int,
}

spec fn init_savings_account(v: SavingsAccount) -> bool {
    v.nelems == 0
}

spec fn increment_op_savings_account(v: SavingsAccount, v_prime: SavingsAccount) -> bool {
    v_prime.nelems == v.nelems + 1
}

spec fn decrement_op_savings_account(v: SavingsAccount, v_prime: SavingsAccount) -> bool {
    v_prime.nelems == v.nelems - 1
}

enum StepSavingsAccount {
    Increment,
    Decrement,
}

spec fn next_step_savings_account(
    v: SavingsAccount,
    v_prime: SavingsAccount,
    step: StepSavingsAccount,
) -> bool {
    match step {
        StepSavingsAccount::Increment => increment_op_savings_account(v, v_prime),
        StepSavingsAccount::Decrement => decrement_op_savings_account(v, v_prime),
    }
}

spec fn next_savings_account(v: SavingsAccount, v_prime: SavingsAccount) -> bool {
    exists|step: StepSavingsAccount| next_step_savings_account(v, v_prime, step)
}


}
