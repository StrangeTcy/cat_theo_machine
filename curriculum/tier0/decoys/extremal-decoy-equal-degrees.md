# Tier0 G4 decoy — Extremal / two equal degrees (negative-control decoy)

Agent: G/I-op. **Status: blueprint-only, not training input.** G4 decoy.

---

## source statement

> In any finite simple graph with ≥ 2 vertices, two vertices have the same degree.
> (supplied verbatim by operator, G4 decoy list)

## target class: proposition

## surface shape (what a method might latch onto)

Finite graph, "maximize/something" language → could trigger **Extremal** (pick an extremal element).

## intended method (the trap): Extremal (decoy)

The correct method is **Pigeonhole**, not Extremal. A finite simple graph on n vertices has degrees
in `{0, 1, ..., n-1}`, but degree 0 and degree n-1 cannot both occur (an isolated vertex and a
vertex adjacent to every other) — so the degrees occupy at most n-1 distinct values, while there
are n vertices. Two vertices share a degree by pigeonhole. Extremal must NOT fire.

## exact mathematical target

Two vertices with the same degree. Proof: n vertices, at most n-1 possible degrees (0 and n-1 are
mutually exclusive) → pigeonhole.

## required domain roles

- finite simple graph on n ≥ 2 vertices;
- degree map (vertex → natural);
- the degree-value box set `{0, ..., n-1}` with the 0/n-1 exclusion;
- pigeonhole (n vertices into n-1 degree boxes).

## constructor mapping found in tree (real, cited)

`PigeonholeLabel`, `CardinalityLabel`, `NatLessLabel`, `ModuloLabel`, `VerticesLabel`, `EdgesLabel`,
`KnowledgeLabel`, `GoalLabel`, `ExtremalLabel`, `ExtremalAtLabel`.

## missing constructors

`GraphLabel`, `VertexLabel`, `EdgeLabel`, `DegreeLabel`. (A1 graph vocabulary. No claim exist.)

## negative controls

The Extremal-vs-Pigeonhole distinction is the control. An Extremal policy that fires here and picks
an "extremal degree" vertex without a pigeonhole argument is the failure mode.

## expected policy behavior

- **must not fire**, or
- **fire and fail rent** (an extremal "solution" must not close; the pigeonhole route is the right
  method).

## governance (negative-control framing)

This decoy is inert until a `LearnedMethodPolicy` exists for its target method (Extremal). It grades
the POLICY, not the method payload. A session run against this decoy before S lands policy machinery
measures nothing — there is no policy to fire. Do not record a "the policy did not fire" as evidence
until the policy machinery is landed.

## unsound-derivation risk

A wrong "solve" picks the vertex of maximum degree and asserts the result follows "by extremality"
— but extremality gives no collision guarantee. Two vertices must share a degree only by the
pigeonhole box argument (n vertices, ≤ n-1 degree values). Such a derivation is a defect; the
policy must fail rent on it.

## proof-checker evidence required

- the ≤ n-1 degree values claim (0 and n-1 mutually exclusive);
- the pigeonhole step (n vertices into n-1 boxes);
- an explicit rejection of the extremal route.

## TrainingRecord promotion gate

G4 decoy. If converted, must load + compile + partial-match AND demonstrate the Extremal policy does
NOT close it.

## current status: blueprint-only, not training input
