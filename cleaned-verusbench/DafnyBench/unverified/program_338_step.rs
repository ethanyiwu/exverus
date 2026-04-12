use vstd::prelude::*;

verus! {

struct TMSystem {
    tx_queues: Vec<Vec<u64>>,
    proc_states: Vec<u64>,
    dirty_objs: Vec<u64>,
    locked_objs: Vec<u64>,
    obj_time_stamps: Vec<u64>,
}

fn step(input: &TMSystem, pid: u64) -> (system: TMSystem)
    requires
        pid < input.tx_queues.len() as u64,
        pid < input.proc_states.len() as u64,
    ensures
        system.tx_queues.len() == input.tx_queues.len(),
        system.proc_states.len() == input.proc_states.len(),
        system.dirty_objs.len() == input.dirty_objs.len(),
        system.locked_objs.len() == input.locked_objs.len(),
        system.obj_time_stamps.len() == input.obj_time_stamps.len(),
{
    let mut system = TMSystem {
        tx_queues: input.tx_queues.clone(),
        proc_states: input.proc_states.clone(),
        dirty_objs: input.dirty_objs.clone(),
        locked_objs: input.locked_objs.clone(),
        obj_time_stamps: input.obj_time_stamps.clone(),
    };
    let mut state: u64 = system.proc_states[pid as usize];
    system
}


}
