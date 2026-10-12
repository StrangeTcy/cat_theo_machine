# CL0 drift ledger

## D1 — protocol branches absent from current cut

**Observed:** The current cut contains only `protocol/ODR-FINAL.md`. The authoritative mapping, two-pipeline document, track ledgers, and charter exist on remote Arena branches.

**Impact:** The current cut has the coordination specification but not the full protocol ledger set.

**Disposition:** Keep remote ledger commits as CL0 inputs. Do not merge them automatically into the runtime cut; INT must select the minimum required documents and resolve conflicts.

## D2 — researcher prototype absent from current cut

**Observed:** `researcher_v0/` exists on `origin/arena/01a0eca3-cat-theo-machine` but not on the current cut.

**Impact:** The current branch cannot run the overnight researcher without an adapter or selected prototype merge.

**Disposition:** Reuse the remote prototype as the reference/first candidate route. No duplicate implementation should start before INT decides whether to import it.

## D3 — planner vocabulary exceeds v2 charter

**Observed in current `planner.py`:**

```text
Extremal
Symmetry
Pigeonhole
Divide
Bijection
DoubleCount
```

**Protocol v2:**

```text
Invariance
Extremal
Pigeonhole
Divide
Symmetry
```

**Impact:** G/I measurement cannot claim charter compliance yet. The current file also does not expose an `Invariance` planner method class matching the v2 vocabulary.

**Decision:** Keep `Bijection` and `DoubleCount` as legacy planner constructors for backward compatibility, but reclassify them as non-v2/blocked methods. They are excluded from G/I curriculum and held-out claims. The v2 registry must expose only the five charter methods. The current cut also lacks the v2 `Invariance` planner payload, which is a separate G-eng task.

## D4 — S2 surface is not active on current cut

**Observed:** The current `schemata.py` has derivation-schema classes, but no `RelationSchema`, `RelationContract`, or `FireAny` symbols were found.

**Impact:** S2 contracted relation-schema induction is blocked on the current cut.

**Disposition:** Select G4 as the preliminary autonomy route if CL1 can lift the researcher prototype and its contracts. S2 remains a later route unless INT imports and validates the S2 surface.

## D5 — environment mismatch

**Observed:** The default Python lacks `gmpy2` and `yaml`; the repository environment file requests Python 3.12 and those dependencies.

**Impact:** A plain baseline invocation fails before runtime boot.

**Disposition:** Use a pinned bootstrap environment for probes, but keep the mismatch as a foundation blocker until the environment is reproducible for operators.

## D6 — SearchDFS baseline fixture drift

**Observed:** The initial failure was a stale test/pack rule-ID mismatch. The current geometry pack exposes `tao_angle_from_sides` and `tao_expand_{alpha,beta,gamma}_angle_value`, while the test requested six removed IDs. The test-only mapping was corrected for triage.

**Remaining result:** SearchDFS now boots and runs, but returns `FAILURE` with `expanded=1`, `generated=1`, and all 15 obligations missing.

**Impact:** The full live search baseline is still not green; the remaining issue is semantic/search or fixture behavior, not pack ingress.

**Disposition:** Do not claim GO for the autonomous closed loop. Repair or explicitly re-pin the fixture/search contract. Do not weaken the expected result merely to make the test green.
