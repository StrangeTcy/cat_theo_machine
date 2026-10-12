# Tier0 G4 decoy — Symmetry / labeled square vertices (negative-control decoy)

Agent: G/I-op. **Status: blueprint-only, not training input.** G4 decoy.

---

## source statement

> Color the vertices of a square with m colors; colorings are distinct if any vertex differs (the
> vertices are labeled).
> (supplied verbatim by operator, G4 decoy list)

## target class: count

## surface shape (what a method might latch onto)

Square-coloring language → could trigger **Symmetry** / Burnside.

## intended method (the trap): Symmetry (decoy)

The vertices are **labeled** — there is **no symmetry group at all** (the group is trivial). The
answer is simply `m^4` with **no quotient**. Symmetry/Burnside must NOT fire (a trivial group
quotient by |G|=1 is not a genuine symmetry argument).

## exact mathematical target

Count = `m^4` (each of the 4 labeled vertices independently takes m colors; no two colorings are
identified because there is no rotation/reflection).

## required domain roles

- 4 labeled vertices of a square;
- m-coloring (a function from labeled vertices to colors);
- no identification (trivial symmetry group).

## constructor mapping found in tree (real, cited)

`SymmetryLabel`, `CardinalityLabel`, `KnowledgeLabel`, `GoalLabel`.

## missing constructors

`ColoringLabel`, `RotationLabel`, `ColorLabel`, `VertexLabel`. (A1 vocabulary. No claim exist.)

## negative controls

The Symmetry-vs-trivial distinction is the control. A Symmetry/Burnside policy that fires here and
quotients by a non-existent rotation group (producing `(m^4+...)/4` or another divided count) is
the failure mode.

## expected policy behavior

- **must not fire**, or
- **fire and fail rent** (a Burnside quotient must not close; the trivial `m^4` is the right answer).

## governance (negative-control framing)

This decoy is inert until a `LearnedMethodPolicy` exists for its target method (Symmetry). It grades
the POLICY, not the method payload. A session run against this decoy before S lands policy machinery
measures nothing — there is no policy to fire. Do not record a "the policy did not fire" as evidence
until the policy machinery is landed.

## unsound-derivation risk

A wrong "solve" applies Burnside `(m^4 + m^2 + 2m)/4` to a **labeled** square — quotienting by a
rotation group that the problem does not declare. That is unsound (the vertices are labeled, so no
two colorings are identified). The policy must fail rent on it.

## proof-checker evidence required

- the vertices are labeled — no group action declared;
- hence the group is trivial and the count is `m^4`;
- explicit rejection of any Burnside quotient.

## TrainingRecord promotion gate

G4 decoy. If converted, must load + compile + partial-match AND demonstrate the Symmetry policy does
NOT close it (must not quotient by a rotation group).

## current status: blueprint-only, not training input
