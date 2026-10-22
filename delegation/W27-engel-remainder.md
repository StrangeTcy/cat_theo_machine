# W27 — Engel remainder: instances, discovery, search firing

**Dimension 3 · Phase 4b · Suite slot `test39` · Prereq W10 ✅**

Read `delegation/README.md` first. Read DAG §4 W10, §7.3 and §8 (W27). Do not re-execute
`W10-engel-strategies.md`; the strategy pack landed. This is the remainder it named.

## Where W10 stopped

- Generic schemas for invariance, monovariant, semi-invariant, extremal; box as
  obligation; colouring as invariance. `test23` 80/80. Planner methods exist.
- No domain pack drives these rules from a *real Engel problem* not named in code.
- Nothing verifies a `StrictlyDecreases` / `NonIncreases` / `Preserves` claim
  independently of the strategy pack.
- Discovery of a measure or observable (miner, not a handed-in $\phi$) is open.
- Strategy rules do not fire during ordinary search — nothing proposes them the way
  the planner methods do.
- `main.py` still hardcodes `"Engel E1"`, `"Engel E2"`, `"Engel coin problem"`.
  **Do not add more cases in that style.** Do not silently delete the existing ones.

## Goal

1. **Two unnamed instances** as *evaluation data* (packs or graph facts), not as
   answers. The strategy machinery must close them. Prefer curriculum cards if W25
   has landed; if not, construct instances in the suite the way `test23` constructs
   symbolic problems, but they must not be the three named Engel packs.
2. **Search firing:** ordinary search (`search/` or `PlannerRun` without a pre-built
   method term) proposes a `Monovariant` / `Invariance` / `SemiInvariant` method on
   at least one instance. Pin that with the generator disabled the instance does not
   close that way.
3. **One discovery attempt:** ask `invariant_miner.py` to propose an observable on
   one instance. If it finds one, ablate; if it does not, that is a precise negative
   — record it, do not fake a measure in Python.
4. Coordinate with W25 on `curriculum.py` / `labels.py`. Coordinate with W9/W24 on
   `invariant_miner.py` — keep additions additive.

## Done-definition

- `validation/test39_engel_remainder.py` green.
- `test23` 80/80, `test8`, `test7`, `test10` still green.
- The suite states which of {instances, search firing, discovery} landed and which
  did not. Partial is fine; claiming discovery you did not get from the miner is not.

## Files

- Extend: `packs/engel-strategies.pack.yaml` (ontology only), `invariant_miner.py`,
  `search/` or `planner.py` (proposal hook). `labels.py` append-only.
- New: `validation/test39_engel_remainder.py`. Maybe a small evaluation pack with
  *no* conclusion rules.
- Do not edit `core.py`. Do not add `main.py` agenda cases. Do not weaken Checker B.

## Verification

`PYTHONPATH=/home/user .venv/bin/python -u validation/test39_engel_remainder.py`
green, plus `test23`, `test8`, `test7`, `test10`.

## Non-goals

IMO geometry (W26), FLT, new hardcoded agenda cases, `core.py` edits.
