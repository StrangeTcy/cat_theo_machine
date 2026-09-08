# Tier1 card — T1-SYM-1 (Symmetry, 5-bead necklace)

Agent: G/I-op. **Status: blueprint-only, not training input.** Pool A Tier1 practice — UNSOURCED (agent-authored statement; not convertible until operator supplies). **Count-target.**
Inherits **Ground 3 — RULED-UNSUPPORTED-PENDING-IMPLEMENTATION**.

---

## source statement

> A necklace has 5 beads, each to be colored one of m colors. Two colorings are the same if one is a
> rotation of the other (rotations of the 5-bead necklace are considered equivalent). How many
> distinct necklaces are there?
> **(UNSOURCED: agent-authored statement, NOT operator-supplied.)** Math: Rotation-only C5; answer `(m^5 + 4m)/5`.

## target class: count

## intended method: Symmetry

Method payload signature (verified): `SymmetryObligations(transformation, domain)`. **The obligation
generator is NOT present at the integration tip — Ground 3 ruling applies.**

## exact mathematical target

Burnside over the cyclic group C5 of order 5 (rotation group of the necklace, rotation-only, no
reflections): the identity fixes m^5 colorings; each of the four nontrivial 5-cycles fixes m colorings
(all beads the same). → `(m^5 + 4m)/5`. VERIFIED.

## required domain roles

- 5 bead positions;
- m colors;
- the C5 rotation group (order 5);
- the `GroupDeclared`, `ActionWellDefined`, `FixedPointCount`, `OrbitCountByAveraging` obligations.

## constructor mapping found in tree (real, cited)

`SymmetryLabel`, `SymmetryObligationsLabel`? **ABSENT** — note the missing obligation generator.
`IntegerLabel`, `CardinalityLabel`, `NatLessLabel`, `ExprMulLabel`, `KnowledgeLabel`, `GoalLabel`,
`RotationLabel`, `BurnsideLabel`.

## missing constructors

`NecklaceLabel`, `BeadLabel`, `RotationLabel`, `ColorLabel`, `CycleGroupLabel`,
`GroupDeclaredLabel`, `OrbitLabel`. (A2 vocabulary. No claim exist.)

## Ground 3 ruling (ratifier issued)

`CountTargetUnsupported(Symmetry, missing_obligation_generator)`. This card is **blueprint-only** until
G1-completion lands **`SymmetryObligations(transformation, domain)`**.

## fixed skeleton shape (per the ruling) — to be satisfied by G-eng G1-completion

`SymmetryObligations(transformation, domain)` must emit, **in order**:
1. `GroupDeclared` — declare C5 as the acting group;
2. `ActionWellDefined` — the rotation action on colorings is well-defined;
3. `FixedPointCount` per group element g (identity m^5, four 5-cycles each m);
4. `OrbitCountByAveraging` — Burnside enters as a **`HUMAN_SUPPLIED_TRUSTED_THEOREM`** leaf,
   provenance-tagged, machine does **not** derive it;
5. then `ClosedForm` as a **SEPARATE** obligation.

Classification must be **SEMANTIC**; no automorphism computation; `G`/`transformation` are declared
inputs; no `if goal contains` dispatch; the generator must not write to the Knowledge store.

## intended obligation sequence

1. group declared (C5);
2. action well-defined;
3. fixed-point counts per g;
4. orbit count via Burnside (human-supplied leaf);
5. closed form (separate).

## negative controls

- Including reflections (dihedral D5) would change the formula to `(m^5 + 4m)/...` differently — the
  rotation-only constraint is load-bearing;
- the existence variant (`SymmetryFixedExists`) is a **distinct** problem, not a substitute for the
  count form.

## proof-checker evidence required

- Burnside `(m^5 + 4m)/5` replayed (identity m^5 + 4 × 5-cycle m)/5;
- `GroupDeclared`/`ActionWellDefined`/`FixedPointCount`/`OrbitCountByAveraging`/`ClosedForm` emitted.

## TrainingRecord promotion gate

**Blocked** — convert only when G-eng G1-completion lands `SymmetryObligations` AND Ground 1 clears AND
record loads + compiles + genuine partial match. Zero partial matches → stays blueprint-only.

## current status: blueprint-only, not training input (Ground 3 pending)
