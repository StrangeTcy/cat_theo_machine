# Tier0 card — Symmetry / square colorings up to rotation (blueprint)

Agent: G/I-op (Agent 3, parallel-unblock lane). **Status: blueprint-only, not training input.**
Ground 2 (statement) state: CLEARED. Ground 1 (constructors) state: OPEN. Ground 3 (count-target) state: PENDING G-COUNT-AUDIT — this card's count target is gated on Ground 3.

---

## source statement

> Find the number of distinct colorings of the vertices of a square using m colors, where colorings
> are considered distinct only if they cannot be transformed into one another by rotation.
> (supplied verbatim, recorded in protocol/I.md Turn 3)

## target class: count

## intended method: Symmetry

Method payload signature (verified in tree, `planner.py`: `class Symmetry`):
`Symmetry(transformation, domain)` — "Declared transformation on a domain. No automorphism group is
computed." **NOTE: `Symmetry` has a payload term but NO obligation generator** (verified: no
`SymmetryObligations`/`SymmetryConclusion`; only Pigeonhole and Extremal are expanded). Whether the
`Symmetry` skeleton can carry a **count** target (Burnside: average fixed-point counts over the group)
is exactly **Ground 3** (G-COUNT-AUDIT decides). This card records the design; it does NOT assert
expressibility.

## exact mathematical target

Count of distinct colorings of a square's 4 vertices with m colors, under the cyclic group C4
(rotation only). Burnside over C4: `(m^4 + m^2 + 2m) / 4`. Verified m=2→6, m=3→24, m=4→70, m=5→165.
Target: closed-form count `(m^4 + m^2 + 2m) / 4`.

## required domain roles

- vertices of the square (the domain, 4 elements);
- a coloring (a map from vertices to m colors);
- the rotation group C4 (identity; rotations by 90, 180, 270 degrees; NO reflections);
- fixed points of each group element (colorings unchanged by that rotation);
- orbit equivalence (two colorings equivalent iff a group element transforms one into the other);
- the orbit count (averaged fixed-point counts).

## constructor mapping found in tree (real, cited)

Existing, usable in tree: `SymmetryLabel`, `KnowledgeLabel`, `GoalLabel`, `CardinalityLabel`.

## missing constructors

`ColoringLabel`, `RotationLabel`, `RotateLabel` (a coloring term and a rotation transformation).
Filing: `protocol/[SHARED]-A1-CONSTRUCTORS.md` (coloring row). No claim these exist.

## group locked to C4

```text
identity:      every coloring fixed                -> m^4
rotation 90:   colorings fixed by 90 = m           (4-cycle on vertices)
rotation 180:  colorings fixed by 180 = m^2        (2 transpositions)
rotation 270:  colorings fixed by 270 = m          (4-cycle on vertices)
total:         (m^4 + m^2 + m + m) / 4 = (m^4 + m^2 + 2m) / 4
NO reflections (the statement says rotation, not rotation and reflection).
```

## intended obligation sequence

**This is a count target.** Obligations (semantic roles; exact machine terms require the
coloring/rotation constructors AND a count/Burnside skeleton, which Ground 3 decides):

1. declare the finite group action (C4 acting on colorings);
2. count fixed points of each group element (identity m^4, 90/270 m, 180 m^2);
3. establish orbit equivalence (colorings equivalent iff related by a rotation);
4. average the fixed-point counts over |C4| = 4 ⇒ `(m^4 + m^2 + 2m)/4`.

## required theorem leaves

- the fixed-point count for each of the 4 rotations;
- the group is C4 (no reflections) — this controls the count;
- Burnside's averaging lemma (orbit count = average of fixed-point counts).

## negative controls

- The dihedral group D4 (with reflections) gives `(m^4 + 2m^3 + 3m^2 + 2m)/8` — a DIFFERENT result.
  Using D4 would be a silent substitution; the supplied statement is C4 only.
- The "one rotation-fixed coloring" (charter warm-up) is a different task from "count colorings up to
  rotation" — do not substitute one for the other.

## statement divergence (recorded, preserved)

```text
charter warm-up (CHARTER-v2.md §3 G2):  "one coloring fixed by a declared rotation"   (existence)
supplied source (protocol/I.md Turn 3):  "count square colorings up to the rotation group C4"
                                         (count / Burnside)
```

This card uses the **supplied C4 counting statement**. Any switch to the existence warm-up requires
an operator ruling and a new source statement. The divergence is preserved, not resolved implicitly.

## proof-checker evidence required

- a replayable derivation producing each fixed-point count;
- an explicit reference to the C4 group (not D4);
- the Burnside average step `(m^4 + m^2 + 2m)/4`.

## TrainingRecord promotion gate

Convert card → TrainingRecord only when ALL of:
- Ground 1 clears (INT-SHARED-A1 lands `ColoringLabel`, `RotationLabel`);
- Ground 3 clears (G-COUNT-AUDIT confirms the Symmetry skeleton can carry a Burnside/count target); AND
- the record loads through the real `TrainingRecordLoader`, its count goal compiles, and it obtains a
  genuine partial match (not a vacuous label touchdown).
If any gate fails, the record stays blueprint-only.

## current status: blueprint-only, not training input
