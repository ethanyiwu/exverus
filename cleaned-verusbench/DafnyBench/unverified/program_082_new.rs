use vstd::prelude::*;

verus! {

struct TicketSystem {
    ticket: u64,
    serving: u64,
    p: Vec<u64>,
    cs: Vec<u64>,
    t: Vec<u64>,
}

impl TicketSystem {
    # [doc = " Constructor"]
    fn new() -> (ts: Self)
        ensures
            ts.ticket == 0,
            ts.serving == 0,
    {
        Self { ticket: 0, serving: 0, p: Vec::new(), cs: Vec::new(), t: Vec::new() }
    }
}


}
