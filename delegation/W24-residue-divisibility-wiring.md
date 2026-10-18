# W24 — Residue and divisibility schema wiring (W9 remainder)

**Dimension 2 · Phase 4b · Suite slot `test36` · Prereq W9 ✅ (edges already exist)**

Read `delegation/README.md` first. Read DAG §7.2 and §8 (W24). This is the item the
2026-10-15 scoreboard called **W9(c)**.

## Why this worker exists

`math/arithmetic.py` already has `Divides`, `Gcd`, `Modulo`, `IsCoprime` (from `91dd5f7`)
and W7's signed `Whole*`/`Ring*` edges. W9(b) (`test29`) said "the machine has no modulo,
subtraction or division" — true on the authoring branch, **false on this tree** (DAG §6.3).
Residues beyond parity and divisibility chains are a *wiring* task: the pack schemas
do not fire those edges. Family 3 in `test29` stops at even/odd.

Do not add new host arithmetic unless an edge is genuinely missing. Prefer pack schemas
over Python.

## Goal

Give `packs/funceq-nt.pack.yaml` (and/or `math/funceq.py`) generic schemas whose
premises/replacements are residue and divisibility facts, so `ForwardDeriveFacts` closes
them the way it already closes parity.

1. At least two of: transitivity of divisibility, residue addition/multiplication,
   gcd-coprimality consequences. Each is a schema, not a Python loop.
2. Instances come from the machine's own `Add` / `Multiply` / `Modulo` edges, recorded
   as facts (`NatSum` / `NatProduct` already exist; add a residue fact label if needed).
3. Negative controls: wrong residue, non-divisor, the decoy that would hold if gcd were
   ignored. The suite pins unreachability.
4. No FLT constants, no named lemma about cubes or fourth powers.

## Done-definition

- `validation/test36_residue_divisibility_wiring.py` green.
- At least one derivation is Checker-B-verified; the ledger is asked and either promotes
  or refuses for a stated reason (a refusal with a reason is a pass).
- `test22` and `test29` still green. Do not renumber them. Do not claim family 1
  combinatorics coverage you did not add.
- The suite states which residue moduli work (if only mod $k$ for small $k$, say so)
  and that d'Alembert is still out (needs W22's minus).

## Files

- Extend: `packs/funceq-nt.pack.yaml`, `math/funceq.py` if the compiler must admit a
  new equation shape. `labels.py` append-only. `graph_task.py` only if a fact-list
  path is missing — say so, and expect a merge with W21.
- New: `validation/test36_residue_divisibility_wiring.py`.
- Do not edit `core.py`, `math/arithmetic.py` (W23), `constructions.py` (W26).

## Verification

`PYTHONPATH=/home/user .venv/bin/python -u validation/test36_residue_divisibility_wiring.py`
green, plus `test22`, `test29`, `test3` (pack load), `test19`.

## Non-goals

d'Alembert, Eisenstein, curriculum card loading (W25), new host `Modulo` (it exists).
