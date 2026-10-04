# CL1c independent SearchDFS probe

**Status:** per-example manifests introduced; geometry baseline still blocked
**Runner:** `verification/odr-cl0/searchdfs_independent.py`
**Results:** `verification/odr-cl0/searchdfs-independent-results.json`
**Per-example timeout:** 60 seconds, including pack boot

## Purpose

The original aggregate test used one example's start and one mixed rule list for fifteen goals. This runner gives each example its own start, goal, and explicit rule manifest. Examples that have no sound current manifest are reported as `BLOCKED` instead of receiving synthetic premises.

## Current manifest results

```text
SUCCESS: 9
    tao_problem_1_1_triangle
    tao_side_beta
    tao_side_gamma
    tao_perimeter_identity
    tao_area_identity
    tao_positive_alpha_side
    tao_positive_beta_side
    tao_positive_gamma_side
    tao_strict_triangle_inequality

BLOCKED: 3
    tao_angle_alpha
    tao_angle_beta
    tao_angle_gamma

TIMEOUT: 3
    tao_cosine_alpha_identity
    tao_cosine_beta_identity
    tao_cosine_gamma_identity
```

The nine successful runs use small, explicit manifests. Examples:

```text
side goals:
    one corresponding side rule

perimeter:
    three side rules → tao_verify_perimeter

positive side:
    tao_perimeter_third_positive → corresponding positive-side rule

strict inequality:
    tao_verify_strict_triangle_inequality
```

## Remaining manifest problems

### Angle examples

The three angle starts lack `Triangle` and `Distinct` premises required by the only available generic `tao_angle_from_sides` route. They are therefore explicitly blocked rather than repaired by adding facts that were not in the example.

### Cosine examples

The cosine starts contain the required geometric facts, and the manifest is:

```text
three side rules
→ tao_angle_from_sides
→ trigonometry.triangle_yields_generic_cosine_relation
```

The manifest is semantically aligned with the `CosineRuleRelates` goal, but all three runs exceed the 60-second per-example wall clock bound. This is now a bounded search/performance or unification problem, not a shared-start problem.

## Cosine timeout isolation

A staged alpha-cosine probe isolated the first blocking operation:

```text
three side rules                         bounded SearchFailure
angle rule only                          bounded SearchFailure
trigonometry rule only                   bounded SearchFailure
three side rules + tao_angle_from_sides  enters generic premise join and does not return
full five-rule manifest                  still exceeds the wall-clock bound
```

A direct `proof.JoinPremises` probe over the same twelve source/derived facts returns one valid angle binding in about 1.7 seconds. The Search-specific matcher was materially different: its partial `M.Instantiate` call rebuilt unresolved variable pairs, creating fresh variable identities. The next premise therefore failed to recognize an already-bound variable and accumulated duplicate bindings. The trace showed repeated `opposite_side` bindings and branch growth across the `SideOf`, `Length`, and `Distinct` premises.

A local experiment that makes `machine.Instantiate` preserve unresolved variable nodes removes the duplicate-binding defect: the prepared Search matcher then returns one binding in about 12.5 seconds. Enabling that experiment globally did not make the fixture green; a targeted full-manifest run still exceeded 120 seconds, and a broader probe also exposed permutation cost in previously successful multi-rule examples. The experiment is therefore not accepted as a baseline repair yet. The remaining issue is a sound matcher/search optimization that preserves the existing SearchDFS contract while avoiding redundant independent-rule permutations.

This is a code-path diagnosis, not a silent fixture repair. No synthetic premises, invariant pruning, or G4 machinery were added, and the experimental core patch is not part of the baseline.

## Decision

```text
aggregate fixture: quarantined
per-example manifests: partially repaired
runnable manifest successes: 9/12
blocked examples: 3, with explicit missing-premise reasons
timeouts: 3, with explicit manifests and receipts
invariant pruning involved: no
SearchDFS baseline: not release-ready
```

The next repair is to make the remaining side-rule permutation search terminate through a checked SearchDFS path or record it as a separate performance blocker. The angle examples require either corrected source fixtures or a new explicitly sourced premise contract; no synthetic facts should be added silently.
