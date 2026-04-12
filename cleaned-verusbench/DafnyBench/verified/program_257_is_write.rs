use vstd::prelude::*;

verus! {

type ProcessId = nat;

type MemoryObject = nat;

type TimeStamp = nat;

spec fn is_write(op: nat) -> bool {
    // assuming 0 is write and 1 is read
    op == 0
}

spec fn mem_object(op: nat) -> MemoryObject {
    // assuming memory object is always 0
    0
}

spec fn process_state_valid(pid: ProcessId, state: nat) -> bool {
    pid == 0 && state == 0
}

spec fn tm_system_valid(system: nat) -> bool {
    system == 0
}

spec fn step(input: nat, pid: ProcessId) -> nat {
    input
}

fn step_func(input: nat, pid: ProcessId) -> (system: nat)
    requires
        pid >= 0,
        input >= 0,
        process_state_valid(pid, 0),
        tm_system_valid(input),
    ensures
        system >= 0,
        tm_system_valid(system),
{
    input
}

fn main() {
}

} // verus!
