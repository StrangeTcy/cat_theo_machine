# Tier1 card — T1-SYM-2 (Symmetry, cube faces)

Agent: G/I-op. **Status: blueprint-only, not training input.** Pool A Tier1 practice. **Count-target.**
Inherits **Ground 3 — RULED-UNSUPPORTED-PENDING-IMPLEMENTATION**.

---

## source statement

> A cube's six faces are to be colored, each face one of m colors. Two colorings are the same if one is
> obtained from the other by a rotation of the cube (the 24-element rotation group). How many distinct
> colorings are there?
> (operator Tier1, verified. Rotation-only group order 24; answer `(m^6+3m^4+12m^3+8m^2)/24`.)

## target class: count

## intended method: Symmetry

Method payload signature (verified): `SymmetryObligations(transformation, domain)`. **The obligation
generator is NOT present at the integration tip — Ground 3 ruling applies.**

## exact mathematical target

Burnside over the 24-element cube rotation group (rotation-only, no reflections). Cycle structure of
the 24 face-permutations:
- identity: 1 element, cycles (1,1,1,1,1,1) → m^6;
- 90°/270° face-axis rotations: 6 elements, cycles (1,1,4) → m^3;
- 180° face-axis rotations: 3 elements, cycles (1,1,2,2) → m^4;
- 180° edge-axis rotations: 6 elements, cycles (2,2,2) → m^3;
- 120°/240° vertex-axis rotations: 8 elements, cycles (3,3) → m^2;

→ `(m^6 + 3m^4 + 12m^3 + 8m^2)/24`. VERIFIED (enumerated the actual 24-element group:
m=2→10, m=3→57, m=4→240).

## required domain roles

- 6 cube faces;
- m colors;
- the rotation group of order 24;
- `GroupDeclared`, `ActionWellDefined`, `FixedPointCount per g`, `OrbitCountByAveraging` obligations.

## constructor mapping found in tree (real, cited)

`SymmetryLabel`, `SymmetryObligationsLabel`? **ABSENT** — note the missing obligation generator.
`IntegerLabel`, `CardinalityLabel`, `NatLessLabel`, `ExprMulLabel`, `KnowledgeLabel`, `GoalLabel`,
`RotationLabel`, `BurnsideLabel`, `CubeLabel`.

## missing constructors

`CubeLabel`, `FaceLabel`, `RotationLabel`, `ColorLabel`, `CycleGroupLabel`, `OrbitLabel`. (A2
vocabulary. No claim exist.)

## Ground 3 ruling (ratifier issued)

`CountTargetUnsupported(Symmetry, missing_obligation_generator)`. This card is **blueprint-only** until
G1-completion lands **`SymmetryObligations(transformation, domain)`**.

## fixed skeleton shape (per the ruling) — to be satisfied by G-eng G1-completion

`SymmetryObligations(transformation, domain)` must emit, **in order**:
1. `GroupDeclared` — declare the 24-element rotation group;
2. `ActionWellDefined` — the rotation action on face-colorings is well-defined;
3. `FixedPointCount` per group element g (the cycle-structure table above);
4. `OrbitCountByAveraging` — Burnside enters as a **`HUMAN_SUPPLIED_TRUSTED_THEOREM`** leaf,
   provenance-tagged, machine does **not** derive it;
5. then `ClosedForm` as a **SEPARATE** obligation.

Classification must be **SEMANTIC**; no automorphism computation; `G`/`transformation` are declared
inputs; no `if goal contains` dispatch; the generator must not write to the Knowledge store.

## intended obligation sequence

1. group declared (order 24);
2. action well-defined;
3. fixed-point counts per g;
4. orbit count via Burnside (human-supplied leaf);
5. closed form (separate).

## negative controls

- Including reflections would change the group (order 48) and the formula — rotation-only is
  load-bearing;
- the existence variant (`SymmetryFixedExists`) is a **distinct** problem, not a substitute for the
  count form.

## proof-checker evidence required

- Burnside `(m^6+3m^4+12m^3+8m^2)/24` replayed (m=2→10, m=3→57, m=4→240);
- `GroupDeclared`/`ActionWellDefined`/`FixedPointCount`/`OrbitCountByAveraging`/`ClosedForm` emitted.

## TrainingRecord promotion gate

**Blocked** — convert only when G-eng G1-completion lands `SymmetryObligations` AND Ground 1 clears AND
record loads + compiles + genuine partial match. Zero partial matches → stays blueprint-only.

## current status: blueprint-only, not training input (Ground 3 pending)
