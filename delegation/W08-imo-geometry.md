# W8 — IMO geometry: auxiliary construction generation

**Dimension 2 · Phase 1 · Suite slot `test21` · Prereq W4 ✅ (done)**

Read `delegation/README.md` first — shared invariants, environment facts and pitfalls are
binding here.

## What already exists (build on it, do not restart)

- `packs/geometry-ontology.pack.yaml` (231 lines) — reusable ontology for polygons,
  triangles and their attached quantities. This is the *legitimate* kind of pack: sorts and
  constructors, no problem conclusions.
- `packs/geometry.pack.yaml` (4059 lines, JSON-in-`.yaml`) — geometry and problem-solving
  knowledge for Tao Problem 1.1 on arithmetic-progression triangles. Requires
  `geometry-ontology` and `trigonometry`.
- `packs/trigonometry.pack.yaml`, `packs/real-closure.pack.yaml`, `packs/order-sign.pack.yaml`.
- `planner.py` — multi-pass backward planner, verified by `test15_multi_pass_planner.py`.
  Your auxiliary constructions must be reachable *through* it, not around it.
- `checker_b.py` — receipt verifier, including knowledge-rewrite steps and `FactsCover`
  goals (verified by `test5`, `test19`).
- `matching.py` / `graph.py` — hypergraph matching over the graph language, specified in
  `HYPERGRAPH_MATCHING_SPECIFICATION.md` and verified by `test17_hypergraph_matching.py`.
  Read the spec: auxiliary-construction generation is pattern instantiation, which is what
  that layer is for.

## Goal

The DAG asks for *auxiliary construction generation* — circumcircles, angle chasing,
projective collineations — and cyclic quadrilaterals. Concretely:

1. A construction generator that, given a goal and the current figure state, proposes
   candidate auxiliary objects (a point on a circumcircle, an angle bisector, a translated
   or reflected point) as **generic schemas** instantiated by `matching.py`, and adds them
   to the figure as new facts.
2. The proposals must be *goal-directed but not problem-specific*: the generator may look at
   the goal's shape (what relation it asks for) but must not contain a table of named IMO
   problems or their known auxiliary points. That is the §5.3 hardcoding line, and W6's
   withdrawal is the precedent for what happens when you cross it.
3. Feed the extended figure into `planner.py`'s multi-pass backward search so constructions
   are tried, discharged, and abandoned on evidence rather than by fixed order.
4. Every accepted construction step must be Checker-B-verifiable, so the final derivation
   earns a receipt.

## Done-definition

- At least one non-trivial olympiad-style configuration is solved end to end **without** the
  solution's auxiliary object being named in the tree: the generator proposes it, the planner
  selects it, Checker B verifies the derivation, and the ledger records it.
- A negative control in the same suite: with construction generation disabled, the search
  does *not* solve it. Without this control you have not shown the generator did anything.
- Ablation evidence via `evaluator.py` (`test7_candidate_evaluator_ablation.py` shows the
  idiom), so the constructions are justified by measurement, not by assertion.
- The suite states which configuration classes work and which do not.

## Files

- New: a construction module (e.g. `constructions.py`) plus `validation/test21_imo_geometry_constructions.py`.
- Extend: `labels.py` (new labels, append-only), `planner.py` (hook constructions into
  backward passes), `graph_task.py` (multi-premise forward derivation already exists there —
  use `MatchQueryConjunction`).
- Packs: extend `geometry-ontology.pack.yaml` with new *sorts/constructors* only. If you must
  add a pack, register it in `main.py:PACK_PATHS`.
- Do not edit `core.py`. Do not weaken `checker_b.py`.

## Verification

`PYTHONPATH=/home/user .venv/bin/python -u validation/test21_imo_geometry_constructions.py`
green, plus all 19 existing suites green. Highest regression risk: `test17` (matching),
`test15` (planner), `test3` (pack load), `test5`/`test19` (Checker B), `test13`/`test16`
(playground, if you sweep figures).

Note that `test13_cartesian_playground.py` takes ~24 s and `test18` ~28 s on this box; budget
accordingly and run suites with `-u`.

## Non-goals

A general-purpose geometry solver, $n=3$/$n=4$ number theory, `core.py` edits, and any
hardcoded problem→construction table.
