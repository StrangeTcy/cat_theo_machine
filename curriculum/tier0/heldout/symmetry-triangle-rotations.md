# Tier0 G5 held-out — Symmetry / triangle colorings up to rotation (second example)

Agent: G/I-op. **Status: blueprint-only, not training input.** G5 held-out. Count-target → inherits
Ground 3 + the pre-finding (no Symmetry obligation generator registered).

---

## source statement

> Color the vertices of an equilateral triangle with m colors; colorings are distinct only if they
> cannot be transformed into one another by rotation.
> (supplied verbatim by operator, G5 held-out list)

## target class: count

## intended method: Symmetry

Method payload signature (verified in tree): `Symmetry(transformation, domain)` — no automorphism
group is computed. **NOTE: `Symmetry` has a payload term but NO obligation generator** (pre-finding
on the symmetry-square-rotations card; only Pigeonhole and Extremal are expanded). Whether a
count/Burnside skeleton is expressible is **Ground 3** (G-COUNT-AUDIT decides). This card does NOT
assert expressibility.

## exact mathematical target

Count of distinct 3-vertex colorings of an equilateral triangle under C3 (rotation only, no
reflections). Burnside over C3: `(m^3 + 2m) / 3`.

## required domain roles

- 3 vertices of the triangle (the domain);
- a coloring (map vertices → m colors);
- the rotation group C3 (identity; rotations by 120 and 240 degrees); NO reflections;
- fixed points of each group element;
- orbit equivalence (colorings equivalent iff related by a rotation);
- the orbit count (averaged fixed-point counts).

## constructor mapping found in tree (real, cited)

`SymmetryLabel`, `CardinalityLabel`, `KnowledgeLabel`, `GoalLabel`.

## missing constructors

`ColoringLabel`, `RotationLabel`, `RotateLabel`, `VertexLabel`. (A1 vocabulary. No claim exist.)

## group locked to C3

```text
identity:     every coloring fixed                -> m^3
rotation 120: colorings fixed by 120 = m          (3-cycle on vertices)
rotation 240: colorings fixed by 240 = m          (3-cycle on vertices)
total:        (m^3 + m + m) / 3 = (m^3 + 2m) / 3
NO reflections (rotations only, not the dihedral D3/S3).
```

## intended obligation sequence (count-target)

Same count/Burnside shape as the symmetry-square card:
1. declare the finite group action (C3 on colorings);
2. count fixed points of each group element (identity m^3, 120/240 m);
3. establish orbit equivalence;
4. average fixed-point counts over |C3| = 3 ⇒ `(m^3 + 2m)/3`.

## negative controls

- The dihedral D3 (with reflections) gives `(m^3 + 3m^2 + 2m)/6` — a DIFFERENT result. Using D3
  would be a silent substitution; the supplied statement is C3 only.
- The "one rotation-fixed coloring" (existence) version is a different task from "count colorings up
  to rotation" (count) — do not substitute one for the other.

## proof-checker evidence required

- fixed-point counts for each of the 3 rotations;
- C3 (not D3) referenced explicitly;
- the Burnside average `(m^3 + 2m)/3`.

## TrainingRecord promotion gate

Convert only when ALL: Ground 1 clears (coloring/rotation constructors present) AND Ground 3 clears
(count-skeleton expressible) AND the record loads + compiles + genuine partial match. Zero partial
matches → stays blueprint-only.

## current status: blueprint-only, not training input
