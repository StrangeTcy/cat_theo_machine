# CL1c independent SearchDFS probe

**Status:** completed as diagnostic; geometry fixture remains quarantined  
**Runner:** `verification/odr-cl0/searchdfs_independent.py`  
**Results:** `verification/odr-cl0/searchdfs-independent-results.json`  
**Per-example timeout:** 45 seconds, including pack boot

## Purpose

The original aggregate test used the first example's one-fact start for all fifteen goals. This probe gives each example its own start and goal in an isolated child process.

The probe deliberately uses the current test's fifteen-rule manifest so that the results expose both fixture and rule-manifest problems. It is not yet a claim that all fifteen examples share one valid rule set.

## Results

```text
SUCCESS:
    tao_problem_1_1_triangle
    tao_side_beta
    tao_side_gamma
    tao_area_identity
    tao_strict_triangle_inequality

FAILURE:
    tao_positive_beta_side
    tao_positive_gamma_side

TIMEOUT at 45 seconds:
    tao_angle_alpha
    tao_angle_beta
    tao_angle_gamma
    tao_perimeter_identity
    tao_positive_alpha_side
    tao_cosine_alpha_identity
    tao_cosine_beta_identity
    tao_cosine_gamma_identity
```

Summary:

```text
5 SUCCESS
2 FAILURE
8 TIMEOUT
0 all-success
```

## Additional fixture findings

The per-example starts are genuinely different, but the single fifteen-rule manifest is still not a valid per-goal manifest:

- the angle starts contain angle/opposite/side facts, while the generic `tao_angle_from_sides` rule also requires `Triangle`, lengths, and `Distinct` premises;
- the positive-beta and positive-gamma starts contain `Perimeter` and `Positive(p)`, while the selected positive rules require derived `PerimeterThird` and `APSideOffset` facts; the definition rules are absent from the selected manifest;
- the cosine goals are `CosineRuleRelates` goals, while the selected `tao_expand_*_angle_value` rules produce expanded arccos expressions, not the cosine-relation goal directly;
- broad rule search causes several cases to time out before producing a useful receipt.

The first five successes show that independent starts are the correct fixture shape for simple cases. The failures and timeouts show that the next repair must produce an explicit rule manifest per example or replace this mixed geometry collection with a smaller, coherent benchmark family.

## Decision

```text
aggregate fixture: QUARANTINED
independent harness: diagnostic evidence only
SearchDFS baseline: still not release-ready
invariant-pruning diagnosis: not implicated; the probe calls SearchDFS directly
```

No G4 candidate induction may use this mixed fifteen-goal fixture until its per-goal rule manifests and time budgets are made explicit.
