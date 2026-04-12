# Pipeline for proof generation/repair
## Input and output
input: an unverified proof

output: a fixed proof

## Key idea
Using IC3 to incrementally find counter example to induction and refine the proof with the guidance of counter examples.

## Overview
1. Given a verification error, especially when the error is about invariants, ask the LLM to reason about counter example to induction (not inductive) or counter example (wrong fact), either using z3 solver or direct LLM prompting.

2. Given the counter example, generalize the counter example to fix or strengthen the invariants.

3. Possibility 1, the invariant is fixed, so we move forward; possibility 2, the invariant is not fixed (still wrong or not inductive), then generating counter example again; possibility 3, compilation error, then iteratively refine.

## Modules
### Counter example generation
input:

a buggy proof (with verification errors, saying which invariant does not hold at loop start/end, we focus on one invariant at a time)

output:

1. a verdict on whether the invariant is a wrong fact or a correct but weak and not inductive invariant

2. a concrete counter example (not necessarily concrete value assignments) that may or may not be achievable
### Counter example generalization
input:

1. the verdict from the last step

2. the concrete counter example from the last step

output:

refined invariants (fixed or strengthend)

### Iteratively refinement
input:

updated but still wrong invariants

output:

iteratively fixed invariants
