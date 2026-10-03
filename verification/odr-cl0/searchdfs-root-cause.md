# CL1b SearchDFS baseline root cause

**Status:** fixture quarantined; autonomy remains blocked  
**Original cut:** `428ecdc146e38de3481222bed7bddeb3c08e1b2d`  
**Triage commit:** `0785aa3`  
**Current test-only ID mapping:** current branch after `0785aa3`

## Finding

`test_actual_searchdfs.py` tries to prove fifteen independent geometry example goals from one `start` term:

```python
start, goal_1_raw = pack.examples["tao_problem_1_1_triangle"]
```

That start contains only:

```text
SideOf(Segment(v, w), Tao Problem 1.1 triangle)
```

The test then ignores the starts belonging to the other fourteen examples and performs one SearchDFS call with a final goal from `tao_cosine_gamma_identity`.

The other example starts contain the facts needed by the selected rules. For example:

```text
side beta / gamma examples:
    SideOf(Segment(w, u), ...)
    SideOf(Segment(u, v), ...)

angle examples:
    AngleOf(...)
    Opposite(...)
    all three SideOf facts

area example:
    Triangle(...)
    Area(...)
    Perimeter(...)
    ArithmeticProgression(...)

cosine examples:
    Triangle(...)
    all three SideOf facts
    AngleOf(...)
    Opposite(...)
    Distinct(...)
```

The selected rules therefore cannot produce the fifteen obligations from the one-fact start. Direct `JoinPremises` probes show:

```text
rule: tao_side_alpha_from_area_perimeter   bindings: one
all other selected rules                         bindings: zero
```

SearchDFS consequently generates the first side-alpha successor and then reaches a dead end:

```text
status: FAILURE
expanded: 1
generated: 1
frontier_peak: 1
found_depth: 0
15 obligations missing
```

## What this is not

The failing test calls `SearchDFS` directly. It does not call `ReachabilityPrune` or `SearchWithInvariant`. The failure is therefore not currently evidence of an invariant-pruning regression and must not be used to blame G4.

It is also not a pack-loader failure after the test-only rule-ID correction. The current pack loads successfully and exposes the generic/expansion IDs.

## Root cause classification

```text
FOUNDATION_FIXTURE_ERROR

The fixture conflates fifteen separately seeded examples with one shared
SearchDFS initial state. The original uploaded test was already present at
428ecdc; no earlier repository commit is available in this checkout to
attribute a narrower introducing change.
```

## Quarantine policy

The test is not used as a green baseline until its semantics are repaired. Its pinned expected result is:

```text
QUARANTINED_EXPECTED_FAILURE
reason = invalid shared-start construction
```

No autonomous-candidate claim may use this fixture as its baseline.

## Repair choices

A future repair must choose and test one explicit semantics:

1. Run fifteen independent SearchDFS experiments, each with its own example start and goal, then aggregate receipts; or
2. Construct a declared shared initial state by an explicit, deduplicated union of the required premises, and document that it is a synthetic combined fixture.

It must not silently keep the first example's one-fact start while asserting all fifteen goals.
