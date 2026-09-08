# [SHARED] Request — A2 G4/G5/Tier1 domain constructors

Status: **request** (unpartitioned shared append points → [SHARED] to the integrator, per
`protocol/DISTRIBUTION.md` §2 — never a local fork). Routed to INT because the requested items are
**term constructors / domain vocabulary**, not planner methods.

Author: G/I-op (merged operator lane). Branch: `arena/01a068c2-cat-theo-machine`.

## Relation to A1 and E7

- E7 observable-constructor requests (`CyclicWindowProduct`, `SumOfProducts`, `FlipSign`,
  `ResidueMod`) are **already filed** in `SHARED-CONSTRUCTORS-E7.md` on `arena/01a066cf`. Cited, not
  re-requested.
- **A1** (`protocol/[SHARED]-A1-CONSTRUCTORS.md`) is scoped to the **four Tier0** problems and is
  INT's deliverable (15-constructor label-registration patch on the `ef571b6` line).
- **A2** is a **different, separate** vocabulary request for the **new-card** domains introduced by
  the G4 decoys, the G5 held-out examples, and the Tier1 practice pool. Do not merge A1 and A2.

A1's 15 constructors (already in INT's patch): `GraphLabel`, `VertexLabel`, `EdgeLabel`, `PathLabel`,
`CycleLabel`, `DegreeLabel`, `IntegerLabel`, `RemainderLabel`, `ResidueClassLabel`, `CongruentLabel`,
`WordLabel`, `BinaryWordLabel`, `AdjacentLabel`, `ColoringLabel`, `RotationLabel`. **A2 adds the
vocabulary A1 does not cover.**

## What is being requested

The following term constructors are **absent from the tree** (they are un-expressible without them) and
are **not** in the A1 patch. They are needed to state the G4 / G5 / Tier1 problems **faithfully** — a
record that "compiles" using only an existing method head plus existing tags is the vacuous-label
touchdown trap, not a real curriculum record.

Grouped by the operator-named A2 domains (`board`, `domino`, `glass`, `house`, `enemy`,
`tournament`, `necklace`, `cube face`) plus the remaining new-card vocabulary.

| Card (domain) | Method | New constructor(s) | Existing (A1 / in-tree) stays |
|---|---|---|---|
| T1-INV-1 (board) | `InvarianceLabel` | `BoardLabel`, `NumberLabel`, `EraseLabel`, `MoveLabel` | `InvarianceLabel`, `ParityLabel`, `OddLabel`, `EvenLabel`, `AbsDiffLabel`, `ExprAddLabel` |
| pigeonhole-domino-board decoy (board/domino) | `PigeonholeLabel` (trap) | `BoardLabel`, `CellLabel`, `SquareLabel`, `DominoLabel`, `TileLabel`, `CheckerboardLabel`, `CornerLabel`, `ColorLabel` | `InvarianceLabel`, `ParityLabel`, `ColoringLabel`(A1) |
| divide-domino-strip heldout (domino) | `DivideLabel` | `StripLabel`, `DominoLabel`, `TileLabel`, `CellLabel`, `GridLabel`, `TilingLabel` | `DivideLabel`, `DividesLabel` |
| invariance-seven-glasses heldout (glass) | `InvarianceLabel` | `GlassLabel`, `UprightLabel`, `FlipLabel`, `MoveLabel`, `CountUprightLabel` | `InvarianceLabel`, `ParityLabel`, `EvenLabel`, `OddLabel` |
| invariance-parliament decoy (house/enemy) | `InvarianceLabel` (trap) | `PartitionLabel`, `HouseLabel`, `SameHouseLabel`, `EnemyLabel` | `GraphLabel`, `VertexLabel`, `EdgeLabel`, `DegreeLabel` (all A1) |
| divide-decoy-even-ones (word) | `DivideLabel` (trap) | `BitLabel`, `ParityOfOnesLabel` | `WordLabel`, `BinaryWordLabel`, `AdjacentLabel` (all A1) |
| symmetry-labeled-square decoy (color) | `SymmetryLabel` (trap) | `ColorLabel` | `ColoringLabel`, `RotationLabel`, `VertexLabel` (all A1) |
| T1-EXT-2 tournament | `ExtremalLabel` | `TournamentLabel`, `OutdegreeLabel`, `ReachableLabel`, `DirectedEdgeLabel` | `VertexLabel`, `EdgeLabel` (A1) |
| T1-DIV-1 staircase | `DivideLabel` | `StairLabel`, `StaircaseLabel`, `StepLabel`, `SeqLabel`, `MoveLabel` | `PathLabel` (A1) |
| T1-DIV-2 ternary word | `DivideLabel` | `TernaryLabel`, `ZeroLabel`, `OneLabel`, `TwoLabel`, `StringLabel` | `WordLabel` (A1) |
| T1-SYM-1 necklace | `SymmetryLabel` | `NecklaceLabel`, `BeadLabel`, `ColorLabel`, `CycleGroupLabel`, `OrbitLabel` | `RotationLabel` (A1) |
| T1-SYM-2 cube face | `SymmetryLabel` | `CubeLabel`, `FaceLabel`, `ColorLabel`, `CycleGroupLabel`, `OrbitLabel` | `RotationLabel` (A1) |
| T1-INV-2 dragon | `InvarianceLabel` | `HeadCountLabel`, `DragonLabel`, `CutLabel`, `GrowLabel`, `MoveLabel` | `InvarianceLabel`, `ParityLabel`, `ModuloLabel` |
| T1-EXT-1 plane/point | `ExtremalLabel` | `PointLabel`, `PlaneLabel`, `DistanceLabel`, `MidpointLabel`, `ConvexHullLabel` | `ExtremalLabel`, `LengthLabel`, `RealNumLabel` |
| T1-PIG-2 coprime | `PigeonholeLabel` | `CoprimeLabel`, `GCFLabel`, `PairLabel` | `IntegerLabel`, `IntegersLabel` (A1) |
| pigeonhole-subset-sum heldout | `PigeonholeLabel` | `PrefixSumLabel`, `SubsetLabel` | `IntegerLabel`, `RemainderLabel`, `ResidueLabel`, `CongruentLabel` (A1) |

Notes:
- "Existing (A1 / in-tree)" lists what is **already available** so INT can confirm only genuinely-new
  labels are added (A1 patch rule: verify each is ABSENT before adding).
- These are **domain-vocabulary** terms; they do not include any obligation-skeleton terms
  (`PartitionExhaustive`, `GroupDeclared`, etc.) — those are G-eng G1-completion content, not
  vocabulary, and belong to the Ground-3 ruling, not this request.
- Rotation-only and labeled/existence variants stay distinct; the constructors here support the
  *count* statements as supplied (no reflection/existence substitution).

## Why this blocks G4/G5/Tier1

All method-head labels (`InvarianceLabel`, `ExtremalLabel`, `PigeonholeLabel`, `DivideLabel`,
`SymmetryLabel`) exist. The G4/G5/Tier1 cards are blueprint now; they can only be converted to
faithful loadable records once the domain vocabulary exists. The new-card domains (board, domino,
glass, house, enemy, tournament, necklace, cube face) are **not expressible** with A1's set alone.

## Scope ruling (INT implementation boundary — same as A1)

**INT lands:**
- label classes in `labels.py` (inside a marked block or `[SHARED]` region);
- singleton instances;
- registration in `sync_from_namespace`;
- registration in `SNAPSHOT_SYMBOL_NAMES` **if** the label must survive cold restore;
- guard-count bump in the same commit.

**INT does NOT land:**
- pack rules using these constructors (that is G-eng or G/I-op content);
- obligation skeletons referencing them (that is G-eng G1 work);
- training-record meaning structures (that is G/I-op authoring).

Same boundary as A1 and D11's capability-vs-content split. This request is vocabulary only; content
comes from the track owners after the vocabulary exists.

---

```text
result: evidence produced / files changed / tests run / merge request / blocked on
  evidence produced: absent-constructor inventory for G4/G5/Tier1 new-card domains;
      distinct-from-A1 and distinct-from-E7 notes
  files changed: protocol/[SHARED]-A2-CONSTRUCTORS.md (this request);
      curriculum/tier0/* and curriculum/tier1/* cards (mapped, blueprint-only)
  tests run: none (load check ran on E2 only; all new cards blueprint-only)
  merge request: none (docs-only; routed to INT as a [SHARED] request)
  blocked on: INT action on A2; G-eng G1-completion lands before count-target conversion
```
