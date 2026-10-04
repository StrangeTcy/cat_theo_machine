# CL1c independent SearchDFS probe

**Status:** cosine alpha route now terminates; beta/gamma remain explicit Search failures; geometry baseline still blocked
**Runner:** `verification/odr-cl0/searchdfs_independent.py`
**Results:** `verification/odr-cl0/searchdfs-independent-results.json`
**Per-example timeout:** 60 seconds, including pack boot

## Purpose

The original aggregate test used one example's start and one mixed rule list for fifteen goals. This runner gives each example its own start, goal, and explicit rule manifest. Examples that have no sound current manifest are reported as `BLOCKED` instead of receiving synthetic premises.

## Current manifest results

```text
SUCCESS: 10
    tao_problem_1_1_triangle
    tao_side_beta
    tao_side_gamma
    tao_perimeter_identity
    tao_area_identity
    tao_positive_alpha_side
    tao_positive_beta_side
    tao_positive_gamma_side
    tao_strict_triangle_inequality
    tao_cosine_alpha_identity

BLOCKED: 3
    tao_angle_alpha
    tao_angle_beta
    tao_angle_gamma

FAILURE: 2
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

The manifest is semantically aligned with the `CosineRuleRelates` goal. After the matcher and premise-order repair, the direct per-example receipts are:

```text
SUCCESS: tao_cosine_alpha_identity  (55.523s)
FAILURE: tao_cosine_beta_identity   (21.350s)
FAILURE: tao_cosine_gamma_identity  (20.347s)
TIMEOUT: none
```

### Isolation and repair

A direct `proof.JoinPremises` probe over the same twelve source/derived facts returned one valid angle binding in about 1.7 seconds. The Search-specific matcher was materially different: its partial `M.Instantiate` call rebuilt unresolved variable pairs, creating fresh variable identities. The next premise therefore failed to recognize an already-bound variable and accumulated duplicate bindings. The trace showed repeated `opposite_side` bindings and branch growth across the `SideOf`, `Length`, and `Distinct` premises.

The repair now preserves unresolved variable nodes during partial instantiation and adds `instantiate_preserves_unbound_variable_identity_test`. The generic trigonometry rule keeps the same premises and replacement but orders them from selective to expansive: `Triangle`, `AngleOf`, `Opposite`, side facts, lengths, `AngleMeasure`, then `Distinct`. This avoids exploring the independent side combinations before the angle and opposite-side bindings are known. The alpha cosine route now succeeds within the 60-second bound.

Beta and gamma now terminate as `SearchFailureLabel`, rather than timing out. Their starts do not contain the reverse `Distinct` orientations used by the generic cosine rule; the existing `geometry-ontology.distinct_is_symmetric` source rule supplies that relation in the replay tests, but adding the unary rewrite directly to this SearchDFS theorem manifest is not yet a terminating checked route. No synthetic premises were added.

No invariant pruning or G4 machinery was used.

## Decision

```text
aggregate fixture: quarantined
per-example manifests: repaired for termination, not all goals
runnable manifest successes: 10/12
runnable manifest failures: 2, with explicit premise-orientation reasons
blocked examples: 3, with explicit missing-premise reasons
timeouts: 0 in the direct per-example rerun
invariant pruning involved: no
SearchDFS baseline: not release-ready
```

The next repair is to provide a terminating, explicitly manifested route for the reverse `Distinct` premises in the beta and gamma cosine cases, or retain those two failures with precise source-premise blockers. The angle examples require either corrected source fixtures or a new explicitly sourced premise contract; no synthetic facts should be added silently.
