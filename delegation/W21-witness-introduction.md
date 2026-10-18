# W21 — Existential witness introduction

**Substrate / Dim 1 · Phase 4 · Suite slot `test33` · Prereq none**

Read `delegation/README.md` first — shared invariants, environment facts and pitfalls are
binding here. Read DAG §7.1 and §8 (W21) before writing anything.

## Why this worker exists

W6 (`test26`) reduced FLT $n=4$ to `EveryStateMoves(descent)` and named the blockage:
no loaded schema has a replacement variable unbound by its premises, so no rule can
introduce the witnesses a descent step constructs (the $m,n$, the $u,v,w$). Existential
witness introduction is absent from the knowledge-rewrite format. That is a *generic*
hole, not an FLT hole. W7's cubic descent and W8's auxiliary points (which currently
mint a `Thingy` in host code) want the same ability as a machine step Checker B can
audit.

Do not re-execute W6 or W7. Build the ability; let those remainders consume it later
(W28, W29).

## Goal

When a knowledge-rewrite rule's replacement mentions a variable that the premises did
not bind, instantiation *mints a fresh witness* and records the introduction, instead
of leaving a `Var` pattern in the fact list or silently dropping the fact.

1. Implement minting in `graph_task.py` (host of `ForwardDeriveFacts` /
   `InstantiateFactList` use), **after** `machine.Instantiate` / `proof.InstantiateFactList`,
   not by editing them. `core.py`, `machine.py`, `proof.py` are kernel. If you believe
   the kernel must change, stop and report — do not edit it.
2. The witness is a machine term (`Thingy` or a fresh `Atom`), not a Python object and
   not a hardcoded name. Two firings mint two distinct witnesses (`Compare` unequal).
3. Checker B (`checker_b.py`) accepts a step that introduces a witness only when the
   introduction is in the derivation record, and rejects a step that smuggles an
   unbound `Var` into the fact list. Do not weaken existing `test5` / `test19` behaviour.
4. A negative control: a rule whose replacement is fully bound by its premises still
   introduces nothing.

## Done-definition

- `validation/test33_witness_introduction.py` green. At least: (a) a generic two-premise
  rule whose replacement mentions a third variable produces a fact containing a fresh
  witness; (b) Checker B verifies that derivation and refuses the same steps against a
  different goal; (c) a fully-bound rule is unchanged; (d) the ledger is asked to promote
  a candidate that uses an introduced witness and either accepts (receipt present) or
  refuses for a stated reason.
- Existing suites `test5`, `test19`, `test15`, `test22`, `test26` still green. `test26`
  must keep its negative account — you have not discharged `EveryStateMoves`.
- The suite states what is *not* claimed (no FLT, no geometry construction catalogue).

## Files

- Extend: `graph_task.py`, `checker_b.py` (consume; preserve `_knowledge_reproduces` /
  `FactsCover`). `labels.py` append-only if a new label is needed (`Witness` /
  `Introduced` or similar), registered in `SNAPSHOT_SYMBOL_NAMES`.
- New: `validation/test33_witness_introduction.py`.
- Do not edit `core.py`, `machine.py`, `proof.py`, `trees.py`, `matching.py`.
- Do not author an FLT or geometry pack.

## Verification

`PYTHONPATH=/home/user .venv/bin/python -u validation/test33_witness_introduction.py`
green, plus `test5`, `test19`, `test15`, `test22`, `test26`. Full gate before reporting.

## Non-goals

Discharging FLT (W28/W29), cyclic quadrilaterals (W26), `core.py` edits, and any
named witness (`m`, `n`, `foot`, …) in a pack.
