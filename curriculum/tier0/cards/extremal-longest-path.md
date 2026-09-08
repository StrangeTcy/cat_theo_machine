# Tier0 card — Extremal / longest-path-gives-cycle (blueprint)

Agent: G/I-op (Agent 3, parallel-unblock lane). **Status: blueprint-only, not training input.**
Ground 2 (statement) state: CLEARED. Ground 1 (constructors) state: OPEN. Ground 3 (count-target) n/a for this card (proof-target).

---

## source statement

> In a finite graph G = (V, E), every vertex has degree at least 2. Prove that there exists a cycle.
> (supplied verbatim, recorded in protocol/I.md Turn 3)

## target class: proposition

## intended method: Extremal

Method payload signature (verified in tree, `planner.py`: `class Extremal`):
`Extremal(family, measure, direction, variation)` — pick the element of `family` that optimises
`measure` in `direction`, then rule out the permitted local `variation`.
There IS an obligation generator (`ExtremalObligations`) for this method (verified).

## exact mathematical target

There exists a cycle in G. Equivalent (finite graph, min degree ≥ 2): take a maximal simple path
`v_1 ... v_k`; its endpoint `v_k` has degree ≥ 2, so it has at least two neighbors, all lying on the
path (else the path could be extended); one of those neighbors is `v_i` with `i < k-1`, so the edge
`v_k v_i` closes a cycle. Target proposition: `Exists(cycle)`.

## required domain roles

- `graph` — the finite graph G = (V, E);
- `vertex` / `edge` — the constituents of V and E;
- `degree` — a natural-valued map on vertices;
- `path` — a simple vertex sequence with adjacent-vertex edges;
- `cycle` — a closed path (the existence target);
- `maximality` of the chosen path (the Extre-mal selection).

## constructor mapping found in tree (real, cited)

Existing, usable in tree: `ExtremalLabel`, `ExtremalAtLabel`, `ExtremalMaxLabel`,
`ExtremalMinLabel`, `HypergraphLabel`, `VerticesLabel`, `EdgesLabel`, `VertexOfLabel`, `NatLessLabel`,
`KnowledgeLabel`, `GoalLabel`, `PigeonholeLabel`, `ModuloLabel`, `CardinalityLabel`.

## missing constructors

`PathLabel`, `CycleLabel`, `GraphLabel`, `VertexLabel`, `EdgeLabel` (a graph-object/path-object
vocabulary; `HypergraphLabel`/`VerticesLabel`/`EdgesLabel` exist but do not denote a path or cycle).
Filing: `protocol/[SHARED]-A1-CONSTRUCTORS.md` (longest-path row). No claim these exist.

## intended obligation sequence

The `ExtremalObligations` shape applies to a **proposition-closing** target. Intended obligations
(semantic roles; exact machine terms require the path/cycle/graph constructors):

1. select the element (a maximal-length path) of `family` that optimises `measure` (path length) in
   `direction` (max);
2. rule out the permitted local `variation` (extending the path, which is impossible at the endpoint
   of a maximal path);
3. discharge the resulting cycle-existence conclusion.

## required theorem leaves

- maximality of the chosen path (no extension exists);
- a degree-2 endpoint has two distinct neighbors, both on the path;
- a back-edge from the endpoint to an interior vertex closes a cycle.
(These are leaves the proof checker must accept; none asserted as present in tree.)

## negative controls

- A graph with a vertex of degree 1 (min degree NOT ≥ 2) may be a tree — the CycleExists claim must
  FAIL there.
- A non-finite (infinite) graph with min degree ≥ 2 need not contain a cycle as a closed finite path
  in the same way — the target is specifically the finite case.

## proof-checker evidence required

- a replayable derivation whose final step is the cycle-existence conclusion;
- every leaf discharged by existing laws, with no inferred-rule applied;
- maximality of the chosen path recorded explicitly (not assumed).

## TrainingRecord promotion gate

Convert card → TrainingRecord only when BOTH:
- Ground 1 clears (INT-SHARED-A1 lands `PathLabel`, `CycleLabel`, `GraphLabel`, `VertexLabel`,
  `EdgeLabel` in the tree) — constructors present; AND
- the record loads through the real `TrainingRecordLoader`, its goal compiles, and it obtains a
  genuine partial match (not a vacuous label touchdown).
If Ground 1 or the partial-match check fails, the record stays blueprint-only; it is not rewritten
into a vacuous shape.

## current status: blueprint-only, not training input
