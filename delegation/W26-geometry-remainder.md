# W26 — IMO geometry remainder

**Dimension 2 · Phase 4b · Suite slot `test38` · Prereq W8 ✅ W4 ✅**

Read `delegation/README.md` first. Read DAG §4 W8, §7.2 and §8 (W26). Do not re-execute
`W08-imo-geometry.md`; that worker landed. This is the remainder it named.

## Where W8 stopped

- Two schemas: bisector completion and circumcircle-at-a-vertex. Goal-directed,
  problem-free, through the planner, negative controls in `test21` (36/36).
- No cyclic-quadrilateral conclusion schema. Circumcircle stops at vertex incidence
  and does not feed chord/angle facts back into goals. Angle chasing beyond the
  bisector, projective collineations: open.
- Checker-B receipts, ledger records, evaluator ablation, figure sweeps: **not met and
  not claimed** on the authoring branch (those modules were absent). They are on this
  tree now; `test21` still does not exercise them.

## Goal

1. At least one new *generic* schema in `constructions.py` / `packs/geometry-constructions.pack.yaml`:
   cyclic quadrilateral (e.g. opposite-angle supplementary, or equal inscribed angles
   on the same arc) **or** chord/angle facts feeding back from a circumcircle into a
   goal. Same discipline as W8: goal shape may be inspected; no table of named IMO
   problems; auxiliary objects are minted, not named.
2. Drive at least one configuration end to end **with** Checker B verifying the
   derivation. Ask the ledger. Ablate via `evaluator.py` or a negative control that
   withholds the new schema (W8 already showed the withhold-the-proposal control;
   reuse it).
3. Leave `test21` passing. Add `test38`; do not grow `test21` into a second owner.

## Done-definition

- `validation/test38_geometry_remainder.py` green.
- `test21` 36/36 still. `test15`, `test17`, `test5`/`test19` still green.
- The suite states which configuration class works and that projective collineations
  (if untouched) are still open.
- Partial is fine: one new schema with a receipt beats a catalogue of un-checked
  schemas.

## Files

- Extend: `constructions.py`, `packs/geometry-constructions.pack.yaml`, `planner.py`
  only if a new method head is required (prefer reusing `Construction`). `labels.py`
  append-only.
- New: `validation/test38_geometry_remainder.py`.
- Do not edit `core.py`. Do not weaken `checker_b.py`. Do not add agenda cases in
  `main.py`.

## Verification

`PYTHONPATH=/home/user .venv/bin/python -u validation/test38_geometry_remainder.py`
green, plus `test21`, `test15`, `test17`, `test5`, `test19`.

## Non-goals

A general geometry solver, FLT, Engel, `core.py` edits, hardcoded problem→construction
tables.
