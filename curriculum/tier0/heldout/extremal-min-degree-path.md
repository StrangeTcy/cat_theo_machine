# Tier0 G5 held-out — Extremal / min-degree path (second example)

Agent: G/I-op. **Status: blueprint-only, not training input.** G5 held-out (method taught, problem not seen).

---

## source statement

> A finite simple graph in which every vertex has degree ≥ k contains a path with k edges.
> (supplied verbatim by operator, G5 held-out list)

## target class: proposition

## intended method: Extremal

Method payload signature (verified in tree): `Extremal(family, measure, direction, variation)`.
`ExtremalObligations` generator present. Same method as the longest-path Tier0 card, applied to a
**held-out** problem (not in Pool A).

## exact mathematical target

A path with k edges exists. Longest-path argument: take a maximal simple path; its endpoint has
degree ≥ k, so it has ≥ k neighbors, all on the path (else extend), giving a path with ≥ k edges.

## required domain roles

- finite simple graph, min degree ≥ k;
- vertex / edge / path / degree;
- maximal path (Extremal selection);
- adjacency.

## constructor mapping found in tree (real, cited)

`ExtremalLabel`, `ExtremalAtLabel`, `ExtremalMaxLabel`, `ExtremalMinLabel`, `VerticesLabel`,
`EdgesLabel`, `NatLessLabel`, `KnowledgeLabel`, `GoalLabel`.

## missing constructors

`PathLabel`, `CycleLabel`, `GraphLabel`, `VertexLabel`, `EdgeLabel`, `DegreeLabel`. (A1 vocabulary.
No claim exist.)

## intended obligation sequence

Same proposition-closing shape as the Extremal Tier0 card:
1. select a maximal-length path (the element of `family` optimising `measure`=path length);
2. rule out the permitted local `variation` (extending the path);
3. discharge the ≥ k-edges path conclusion (endpoint has ≥ k neighbors, all on the path).

## negative controls

- min degree < k → the path-with-k-edges claim must fail;
- a tree (degree-1 leaf) is not ≥ k for k ≥ 2 — the claim must be min-degree-gated.

## proof-checker evidence required

- maximality of the chosen path recorded explicitly;
- endpoint has ≥ k distinct neighbors all on the path;
- the ≥ k-edges path conclusion replayed.

## TrainingRecord promotion gate

Convert when Ground 1 clears (path/graph/vertex/edge/degree constructors present) AND the record
loads + compiles + obtains a genuine partial match. Zero partial matches → stays blueprint-only.

## current status: blueprint-only, not training input
