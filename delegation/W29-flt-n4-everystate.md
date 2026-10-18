# W29 — FLT $n=4$: discharge `EveryStateMoves` (gated)

**Dimension 1 · Phase 5 · Suite slot `test41` · Prereqs W21, W22, W23, W6 `[~]`**

> **Do not start until W21–W23 have reported.** Do not re-execute
> `delegation/W06-flt-n4-descent.md`; it is closed as partial. This brief retries
> *only* the missing list in DAG §4 W6 / `test26` against the new substrate.

Read `delegation/README.md` first. Read DAG §4 W6, §6.5, §7.1 and §8 (W29).

## Goal

`test26` reduced the theorem to `EveryStateMoves(descent)`. Retry each missing item
with the new machinery:

- Witness introduction for $(m,n)$ / $(u,v,w)$ (W21).
- Ring normalisation of the grid identities (W22).
- Factorisation / `NatLess` (W23).

Do not author a quartic rule, a parametrisation, a constant or a lemma about squares.
The parametrisation remains a human-stated candidate until the machine discovers or
derives it; `test26` already said so.

## Done-definition

First reachable of {full, partial, precise negative}, as in W6. New suite
`validation/test41_flt_n4_everystate.py`. **Do not modify `test26`'s claims** — it is
the historical negative account. If you discharge `EveryStateMoves`, this suite
asserts that, and DAG §4 W6 is updated to point here.

## Files

New `test41`. Consume `playground.py`, `graph_task.py`, `math/arithmetic.py` as they
stand after W21–W23. No `core.py`. No revival of `flt-quartic`.

## Non-goals

$n=3$ (W28), the full FLT, weakening the ledger, rewriting history in `test26`.
