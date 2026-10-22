# W25 — Curriculum card loader

**Dimensions 2, 3, 4 · Phase 4b · Suite slot `test37` · Prereq none**

Read `delegation/README.md` first. Read DAG §7.2–7.5 and §8 (W25). Read
`MATHEMATICAL_APPRENTICESHIP_LADDER.md` for the rung language, and `test10` for the
*executable* curriculum (rung builders in `curriculum.py`) which this worker must not
break.

## Why this worker exists

`curriculum/tier0` and `tier1` hold cards, decoys and held-outs for pigeonhole, extremal,
invariance, symmetry, divide-and-conquer. W9's done-definition asked for those held-outs
as evaluation data. `test22` section [31] checked, rather than assumed: every corpus file
declares `blueprint-only`, constructors named in the cards (`IntegerLabel`,
`IntegersLabel`, `RemainderLabel`, `ResidueLabel`, `CongruentLabel`, plus path/cycle/
colouring constructors) are **absent** from `labels.py`, and no loader exists. Curriculum
held-out evidence is currently impossible. W10's held-out/decoy clause is blocked on the
same hole.

`test10` builds synthetic graph tasks with `BuildRung1RetrievalTask` … `BuildRung7PlannerTask`.
That is a different curriculum. Keep it. This worker loads the *markdown corpus*.

## Goal

1. Add the missing labels (append-only, snapshot-registered). Names should match what
   the cards already cite so Ground 1 can clear; do not rename the corpus to dodge this.
2. A loader that turns a card into a graph task / fact hypergraph the existing engines
   (`ExecuteGraphQuery`, `ForwardDeriveFacts`, planner) can run. Blueprint-only is a
   *property of the old files*, not a law — once a card is loadable it is evaluation
   data, still not training input (do not copy answers into packs).
3. At least one card from `heldout/` runs and is *not* solved by anything you authored
   for that card; at least one `decoys/` card is rejected.
4. Honest scope: if a family still lacks constructors (graph colouring, Burnside), the
   suite lists them as still-OPEN Ground 1 rather than skipping silently.

## Done-definition

- `validation/test37_curriculum_loader.py` green.
- `test10` still green (rung builders untouched in behaviour).
- At least one held-out solved, one decoy rejected, machine-side. Partial family
  coverage is fine; claiming a family whose constructors you did not add is not.
- Cards remain without encoded solutions. The suite greps, or structurally pins, that
  your new pack/module does not contain the held-out's conclusion as a constant.

## Files

- Extend: `curriculum.py` (loader), `labels.py` (the missing constructors), maybe a
  `curriculum/load.py`. Register new labels in `SNAPSHOT_SYMBOL_NAMES`.
- New: `validation/test37_curriculum_loader.py`.
- Do not rewrite the markdown into answers. Do not edit `core.py`.
- Coordinate with W24/W27 on `labels.py` (append-only union).

## Verification

`PYTHONPATH=/home/user .venv/bin/python -u validation/test37_curriculum_loader.py`
green, plus `test10`, `test3`, `test12` (new labels round-trip).

## Non-goals

Solving all tier1 cards, Engel strategy discovery (W27), geometry constructions (W26),
`core.py` edits.
