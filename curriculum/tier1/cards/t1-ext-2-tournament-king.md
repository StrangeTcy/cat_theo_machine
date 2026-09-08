# Tier1 card — T1-EXT-2 (Extremal, tournament king)

Agent: G/I-op. **Status: blueprint-only, not training input.** Pool A Tier1 practice. Proof-target.

---

## source statement

> In a finite tournament, prove there is a vertex from which every other vertex is reachable by a
> path of at most two edges.
> (operator Tier1, verified)

## target class: proposition

## intended method: Extremal

Method payload signature (verified): `Extremal(family, measure, direction, variation)`.
`ExtremalObligations` generator present.

## exact mathematical target

A "king": a vertex of maximum out-degree. For such v, suppose some u is not reachable from v in ≤ 2
edges. Then v does not point to u and neither does any out-neighbor of v point to u. So u points to v
and to every out-neighbor of v — giving outdeg(u) ≥ outdeg(v) + 1, contradicting v's maximal
out-degree. TRUE.

## required domain roles

- finite tournament (complete oriented graph);
- out-degree of a vertex;
- the maximum out-degree vertex (extremal selection);
- reachability by a path of ≤ 2 edges.

## constructor mapping found in tree (real, cited)

`ExtremalLabel`, `ExtremalAtLabel`, `ExtremalMaxLabel`, `ExtremalMinLabel`, `VerticesLabel`,
`EdgesLabel`, `NatLessLabel`, `KnowledgeLabel`, `GoalLabel`.

## missing constructors

`TournamentLabel`, `VertexLabel`, `EdgeLabel`, `OutdegreeLabel`, `ReachableLabel`,
`DirectedEdgeLabel`. (A2 vocabulary. No claim exist.)

## intended obligation sequence

Extremal proof-closing shape:
1. select the element (max out-degree vertex) of `family` optimising `measure` (out-degree) in
   `direction` (max);
2. rule out the permitted local `variation` (a 2-step-unreachable u would have higher out-degree);
3. discharge the ≤2-reachability conclusion.

## negative controls

- In a non-tournament (a general directed graph) a max out-degree vertex need not be a king — the
  completeness of the orientation is load-bearing;
- the reachability is ≤ 2 (not ≤ 1) — a non-neighbor u reached via an out-neighbor is the 2-step case.

## proof-checker evidence required

- max out-degree vertex exists (finite tournament);
- the 2-step-unreachable contradiction (outdeg(u) ≥ outdeg(v)+1);
- conclusion replayed.

## TrainingRecord promotion gate

Convert when Ground 1 clears (tournament/vertex/edge/outdegree constructors present) AND record loads
+ compiles + genuine partial match. Zero partial matches → stays blueprint-only.

## current status: blueprint-only, not training input
