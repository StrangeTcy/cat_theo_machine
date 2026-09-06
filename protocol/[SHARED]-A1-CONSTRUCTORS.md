# [SHARED] Request — A1 Tier0 domain constructors

Status: **request** (unpartitioned shared append points → [SHARED] to the integrator, per
`protocol/DISTRIBUTION.md` §2 — never a local fork). Routed to INT because the requested items are
**term constructors / domain vocabulary**, not planner methods.

Author: G/I-op (merged operator lane). Branch: `arena/01a068c2-cat-theo-machine`.
Request base: `9fb8870561f0a34f5fd0eb32a06486b8a4e91625`.

## Relation to the existing E7 constructor request

The E7 observable-constructor request (`CyclicWindowProduct`, `SumOfProducts`, `FlipSign`,
`ResidueMod`) is **already filed** in `SHARED-CONSTRUCTORS-E7.md` on `arena/01a066cf` and is **cited,
not re-requested** here. This request is for a **different** set of constructors: the **domain
vocabulary needed to state the A1 Tier0 problem records** (longest-path, pigeonhole, binary-words,
rotation-invariant coloring). Do not merge the two.

## What is being requested

The following term constructors are **absent from the tree** (confirmed by grep across all `.py`
modules and by a built-namespace probe against the real `TrainingRecordLoader`). Signatures are a
proposal; exact arity/shape is INT's to confirm against the surrounding contract system.

| Problem (A1 Tier0) | Method | Missing constructor(s) |
|---|---|---|
| longest-path-gives-cycle | `ExtremalLabel` | `PathLabel`, `CycleLabel`, `GraphLabel`, `VertexLabel` (general graph-theory terms; `HypergraphLabel`/`VerticesLabel`/`EdgesLabel` exist but are not a path/cycle/graph-object vocabulary) |
| n+1 integers, two congruent mod n | `PigeonholeLabel` | `IntegerLabel`, `IntegersLabel`, `RemainderLabel`, `ResidueLabel`, `CongruentLabel` (need an integer-set, a residue/remainder, and a congruence relation; `ModuloLabel`/`CardinalityLabel`/`NatLessLabel` exist but do not state "n+1 integers fall into n residue classes") |
| binary words, no adjacent ones | `DivideLabel` | `WordLabel`, `BinaryWordLabel`, `AdjacentLabel` (need a binary-word term and an adjacency predicate) |
| one rotation-invariant coloring | `SymmetryLabel` | `ColoringLabel`, `RotationLabel`, `RotateLabel` (need a coloring term and a rotation transformation) |

## Why this blocks A1

All five method-head labels (`InvarianceLabel`, `ExtremalLabel`, `PigeonholeLabel`, `DivideLabel`,
`SymmetryLabel`) exist. The four non-E2 records cannot be stated **faithfully** without the domain
constructors: a record that "compiles" using only the method head plus existing tags (e.g.
`PigeonholeLabel` + `ModuloLabel` + `NatLessLabel` bare) is a **vacuous label touchdown** — it does
not express the problem's domain, so it would be the candidate-absence trap, not a real curriculum
record. A1 item 1 (E2) is already satisfied by the existing loadable record.

## Note on statement text

This request covers **constructors only**. Independent of it, the four problems' authoritative Engel
statement text is not in the tree (only nicknames in `CHARTER-v2.md` §3 G2); that is routed to the
operator, not part of this [SHARED] request.

---

```text
result: evidence produced / files changed / tests run / merge request / blocked on
  evidence produced: absent-constructor inventory (measured vs built namespace);
      distinct-from-E7-request note
  files changed: protocol/[SHARED]-A1-CONSTRUCTORS.md (this request)
  tests run: none (load check ran on E2 only)
  merge request: none (docs-only; routed to INT as a [SHARED] request)
  blocked on: INT action on the request; operator statement text
```
