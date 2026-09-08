# Tier1 card — T1-EXT-1 (Extremal, no point is a midpoint)

Agent: G/I-op. **Status: blueprint-only, not training input.** Pool A Tier1 practice — UNSOURCED (agent-authored statement; not convertible until operator supplies). Proof-target.

---

## source statement

> A finite set of at least two points in the plane cannot have the property that every point is the
> midpoint of two other points of the set.
> **(UNSOURCED: agent-authored statement, NOT operator-supplied.)**

## target class: proposition

## intended method: Extremal

Method payload signature (verified): `Extremal(family, measure, direction, variation)`.
`ExtremalObligations` generator present.

## exact mathematical target

Contradiction. Take the pair (P, Q) at **maximal distance** (the extremal element). Suppose P is the
midpoint of some pair (A, B) with A, B in the set. Then A, B are collinear on opposite sides of P,
and by the triangle inequality one of |A−Q| or |B−Q| is strictly greater than |P−Q|, contradicting the
maximality of |P−Q|. So the maximal-distance pair's endpoints are never midpoints.

## required domain roles

- finite point set in the plane;
- distance between points;
- the maximal-distance pair (extremal selection);
- midpoint relation.

## constructor mapping found in tree (real, cited)

`ExtremalLabel`, `ExtremalAtLabel`, `ExtremalMaxLabel`, `ExtremalMinLabel`, `RealNumLabel`,
`LengthLabel`, `KnowledgeLabel`, `GoalLabel`.

## missing constructors

`PointLabel`, `PlaneLabel`, `DistanceLabel`, `MidpointLabel`, `ConvexHullLabel`. (A2 vocabulary. No
claim exist.)

## intended obligation sequence

Extremal proof-closing shape:
1. select the element (max-distance pair) of `family` optimising `measure` (distance) in `direction`
   (max);
2. rule out the permitted local `variation` (P as a midpoint gives a longer distance — impossible);
3. discharge the contradiction conclusion.

## negative controls

- A set with a single point (or a symmetric configuration where every point IS a midpoint) would be
  the counter-shape — the finite/≥2 hypothesis is load-bearing;
- the maximal-distance selection must be a genuine extremal element.

## proof-checker evidence required

- maximal-distance pair exists (finite set);
- triangle-inequality contradiction if a midpoint claim holds;
- conclusion replayed.

## TrainingRecord promotion gate

Convert when Ground 1 clears (point/plane/distance/midpoint constructors present) AND record loads +
compiles + genuine partial match. Zero partial matches → stays blueprint-only.

## current status: blueprint-only, not training input
