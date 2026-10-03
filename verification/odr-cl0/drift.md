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

**Disposition:** G-eng must either add the v2 `Invariance` payload and retire/exclude the two forbidden methods, or document an explicit compatibility boundary before curriculum measurement.

## D4 — S2 surface is not active on current cut

**Observed:** The current `schemata.py` has derivation-schema classes, but no `RelationSchema`, `RelationContract`, or `FireAny` symbols were found.

**Impact:** S2 contracted relation-schema induction is blocked on the current cut.

**Disposition:** Select G4 as the preliminary autonomy route if CL1 can lift the researcher prototype and its contracts. S2 remains a later route unless INT imports and validates the S2 surface.

## D5 — environment mismatch

**Observed:** The default Python lacks `gmpy2` and `yaml`; the repository environment file requests Python 3.12 and those dependencies.

**Impact:** A plain baseline invocation fails before runtime boot.

**Disposition:** Use a pinned bootstrap environment for probes, but keep the mismatch as a foundation blocker until the environment is reproducible for operators.

## D6 — SearchDFS baseline fixture drift

**Observed:** After booting all packs in a dependency-complete disposable environment, `test_actual_searchdfs.py` fails while selecting `tao_angle_alpha_from_sides` from the geometry pack.

**Impact:** The full live search baseline is not green on the current cut.

**Disposition:** Do not claim GO for the autonomous closed loop. Repair or re-pin the fixture/pack contract before CL2 candidate work is admitted.
