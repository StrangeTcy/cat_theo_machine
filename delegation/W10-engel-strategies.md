# W10 — Engel's heuristic strategies as machine-derivable machinery

**Dimension 3 · Phase 1 · Suite slot `test23` · Prereqs W3 ✅ W4 ✅ (done)**

Read `delegation/README.md` first — shared invariants, environment facts and pitfalls are
binding here.

## What already exists

Three Engel instances are already working, and they are the pattern to generalize from:

- `packs/engel-coins.pack.yaml` (104 lines) — adjacent-flip coin row; heads-count parity as
  the Phi pattern.
- `packs/engel-means.pack.yaml` (85 lines) — Engel E1, arithmetic-mean invariant.
- `packs/engel-blackboard.pack.yaml` (414 lines) — Engel E2: erase $a,b$, write
  $\lvert a-b\rvert$; observable `BoardSum`, invariant the parity of that sum, move changes
  the sum by $-2\min(a,b)$. Its own description is explicit: *"Nothing here simulates a board
  or enumerates a move order."* That is the discipline to keep.
- `invariance.py` — a `Phi` class: the invariant-pattern abstraction these packs use.
- `invariant_miner.py` + `evaluator.py` — invariant discovery with ablation and holdout
  regression gates (`test8`, `test7`).
- `curriculum.py` + `curriculum/tier0`, `tier1` — cards, decoys and heldouts across the
  pigeonhole, extremal, invariance, symmetry and divide-and-conquer families (`test10`).
- `promotion_ledger.py` — refuses promotion without a Checker B receipt (`test9`).

Optional reading, **not on this branch**: the `CUR-ENGEL-E3/E4/E7` task documents live on
`arena/01a066cf-cat-theo-machine` and `arena/01a068c2-cat-theo-machine`
(`git show <branch>:CUR-ENGEL-E3.md`). Useful context on how those Engel tasks were framed;
do not import their code.

## A trap that is already in the tree

`main.py`'s theorem agenda hardcodes named Engel instances — `"Engel E1"`, `"Engel E2"`,
`"Engel coin problem"`, and literal configurations like `"Engel coins HHHHH to HHTTT"`.
That is a standing tension with invariant §5.3 (no domain-specific hardcoding). **Do not add
more cases in that style.** Your contribution should make the strategy classes discoverable,
so instances stop needing to be named in `main.py`. If you can generalize the agenda itself
to derive its cases, that is a bonus worth reporting — but do not silently delete the
existing cases, since `test` mode and the DAG's status claims depend on them.

## Goal

Turn the five Engel principles from *three hand-crafted instances* into *machinery*:

1. **Invariance** — already partly there (`Phi`, `engel-blackboard`). Generalize: given a
   move relation and a candidate observable, let `invariant_miner.py` propose observables and
   confirm invariance over the reachable state space via sweeps (`playground.py`).
2. **Monovariant / semi-invariant** — a termination measure that strictly decreases (or
   increases) under the move relation, discovered rather than declared, yielding a
   well-founded termination argument the machine can state.
3. **Extremal principle** — pick an extremal element of a discovered order and derive
   consequences from its extremality. Generic over the order; no per-problem choice.
4. **Box principle (pigeonhole)** — a generic counting argument from a cardinality mismatch
   between a domain and a codomain the machine has represented, using Peano arithmetic and
   `GMPRep`.
5. **Checkerboard colouring** — a generic 2-colouring parity argument, i.e. a colouring as a
   map plus a parity observable; the curriculum's colouring cards are evaluation data for it.

Priority: **2, 3, 4** are the ones with the least existing coverage. Deliver those well
rather than all five shallowly.

## Done-definition

- Each principle you claim is demonstrated on **at least two** distinct instances that are
  *not* named anywhere in your code or packs, plus the existing three packs still working.
- **Held-out and decoy evidence**: `curriculum/heldout/` solved, `curriculum/decoys/`
  rejected. This is the operational form of §5.3 and the only thing that distinguishes a
  discovered strategy from a memorized one.
- Ablation via `evaluator.py` showing each strategy measurably helps on its instances.
- Checker B verifies the derivations; the ledger either promotes (with receipt) or refuses
  for a stated reason. Both are acceptable outcomes; silence is not.
- The suite states which principles work, on which families, and which do not.

## Files

- New: `validation/test23_engel_strategies.py`, plus a strategies module if the work needs
  one (e.g. `strategies.py`).
- Extend: `invariance.py`, `invariant_miner.py`, `playground.py`, `curriculum.py`,
  `labels.py` (append-only).
- Packs: a new Engel pack may carry ontology and *generic* move/observable schemas — not a
  problem's answer. Register it in `main.py:PACK_PATHS`.
- Coordinate with W9 (`delegation/W09-imo-combinatorics-funceq.md`): both briefs extend
  `invariant_miner.py`. If you both land changes there, expect a merge and keep your
  additions additive and independently testable.
- Do not edit `core.py`. Do not weaken `checker_b.py` or the ledger's receipt requirement.

## Verification

`PYTHONPATH=/home/user .venv/bin/python -u validation/test23_engel_strategies.py` green, plus
all 19 existing suites green. Highest regression risk: `test8` (invariant miner), `test7`
(evaluator/ablation), `test10` (curriculum), `test13`/`test16` (playground — `test13` takes
~24 s), `test9` (promotion loop).

## Non-goals

IMO geometry (W8), functional equations (W9), FLT (W6/W7), `core.py` edits, and any new
hardcoded agenda case in `main.py`.
