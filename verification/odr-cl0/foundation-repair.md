# Foundation-repair task after CL0

**Status:** active follow-up to CL0  
**Owner:** INT  
**Autonomy dispatch:** blocked until the acceptance gates below pass

## FR1 — reproducible operator environment

Use `verification/odr-cl0/requirements-cl0.txt` for the minimal Python probe dependencies and record the interpreter version. The supported repository environment remains `environment.yml`; the requirements file is not a replacement for the full Conda environment.

Acceptance:

```text
python -m cat_theo_machine.testsuite → exit 0
runtime imports do not depend on an undeclared package
operator command and environment digest are recorded
```

## FR2 — SearchDFS fixture triage

The initial failure was a stale test/pack rule-ID mismatch:

```text
old test IDs:
    tao_angle_alpha_from_sides
    tao_angle_beta_from_sides
    tao_angle_gamma_from_sides
    tao_verify_cosine_alpha
    tao_verify_cosine_beta
    tao_verify_cosine_gamma

current pack IDs:
    tao_angle_from_sides
    tao_expand_alpha_angle_value
    tao_expand_beta_angle_value
    tao_expand_gamma_angle_value
```

The test was updated only to use the currently shipped IDs. This removes the ingress `KeyError` but does not make the proof pass.

The remaining baseline failure is substantive:

```text
SearchDFS status: FAILURE
expanded: 1
generated: 1
15 obligations remain missing
```

Acceptance for FR2 is not merely “the test gets past pack loading.” It requires either:

1. a reproducible, checked repair of the SearchDFS/fixture contract; or
2. an explicit re-pinned baseline fixture whose expected failure is documented and independently replayable.

Do not add target-specific proof rules or change the expected result only to turn the test green. The root cause and pinned quarantine are recorded in `verification/odr-cl0/searchdfs-root-cause.md` and `searchdfs-expected-failure.json`; this is a triage completion, not a green baseline.

## FR3 — G method-vocabulary decision

Decision for the current cut:

```text
Bijection and DoubleCount remain legacy planner constructors for
backward compatibility, but are reclassified as non-v2 / blocked methods.
They are not eligible for G/I curriculum or held-out claims.
```

The v2 method registry must expose only:

```text
Invariance
Extremal
Pigeonhole
Divide
Symmetry
```

The current cut also lacks an `Invariance` planner payload. Adding that payload and its non-vacuous obligation test is a separate G-eng task. Legacy methods must not be silently relabeled as v2 methods.

## FR4 — rerun CL0

Rerun the full CL0 probes after FR1–FR3. The autonomy route may become `G4`, but the decision cannot become `GO` until the SearchDFS baseline and operator environment are reproducible.
