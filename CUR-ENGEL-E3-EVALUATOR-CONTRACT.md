# CUR-ENGEL-E3-EVALUATOR-CONTRACT

**Date:** September 5, 2026
**Role:** oracle-side E3 evaluator contract (grades a **frozen blind-output artifact from G-ENG** against the **sealed CUR-ENGEL-E3 oracle**).
**Status:** contract built, not yet run. It is run only once a frozen blind-output artifact arrives.
**Contamination note:** this contract is written by the oracle-contaminated context that has seen the E3 answer/weights/readings/classifications. It therefore grades *against the known sealed oracle*. It is **not** a clean-room blind evaluation. The clean-room blind-evaluator role (a context that has not seen the oracle) is a distinct, disallowed role for this context and is not what this document does.

---

## 1. Purpose

When G-ENG-LINEAR-INVARIANT produces a frozen blind-output artifact claiming an E3 invariant (the weight vector and its classification), this contract decides whether that claim matches the sealed oracle. The output is a verdict in machine terms plus the derivation nodes supporting it.

The E3 problem and oracle are fixed. The frozen artifact under evaluation is the thing graded; this contract is not a template for regenerating the answer.

---

## 2. Inputs

**Required (exactly one frozen artifact):**

- `frozen blind-output artifact`: the G-ENG generated candidate for E3. It must specify, at minimum:
  - the candidate weight vector (a machine term family on the six-sector state space);
  - the claimed classification (one of the grading-matrix verdict labels);
  - the derivation nodes / support it cites.

**Required reference (fixed, from the sealed CUR-ENGEL-E3 oracle):**

- Statement: a circle divided into six sectors containing `(1,0,1,0,0,0)`. A move increases two neighboring entries by 1. Question: can all entries become equal?
- Move set: six neighboring-pair increments — `12, 23, 34, 45, 56, 61` (each adds +1 to both positions).
- Goal class: all-six-equal.
- Reference observable (sealed, preserved-and-separating): alternating weight `(1,-1,1,-1,1,-1)`.
- Reference readings: initial `2`; all-equal `0`.

---

## 3. Checks (the obligations the frozen artifact must discharge)

Each check is independent. A check is either **PASS** or **FAIL-with-term**; the evaluator does not interpolate.

### C1 — Candidate derived from the move constraints
The candidate must be generated from the move constraints (the move-failure directions), not from the goal alone. Grading:
- **PASS** if the candidate's derivation cites the move family and the candidate is orthogonal (zero net change) to every move's direction.
- **FAIL** if the candidate is stated without reference to the move constraints (e.g. invented from the goal), or if it is not in the kernel of the move matrix.

### C2 — Preservation obligation discharged
The candidate must be preserved by every move (its reading is unchanged after applying any single move).
- **PASS** if, for the candidate weight vector \(w\), the change under a move at pair \((i,i{+}1)\) is \(w_i + w_{i+1} = 0\) for all six moves (this is the reference alternating condition).
- **FAIL** if any single move changes the reading.

### C3 — Start/target separation discharged
The candidate must separate a reachable start reading from the goal-class reading (different readings on the start state and the all-equal target class), so unreachability follows.
- **PASS** if the candidate's reading at the start differs from its reading at every state in the all-equal class. For the reference candidate that is initial `2` vs target `0`.
- **FAIL** if the start and target readings coincide (then the candidate cannot prove unreachability).

### C4 — Odd-cycle control emits the No-nonzero-exact-linear-observable term
The seam must correctly report that the odd-cycle (5-sector) control has **no** nonzero exact-integer alternating weighting over `{−1,0,1}`.
- **PASS** if the five-cycle control emits the machine failure term `NoNonzeroExactLinearObservable(move_family)`.
- **FAIL** if the odd-cycle control instead yields a nonzero candidate (a false invariant on an odd cycle) or silently omits the control.

### C5 — Removing the weighted generation removes the candidate
Disabling the weighted-invariant generator must remove the candidate from the output. This proves the candidate is genuinely produced by the weighted solver, not injected as a constant.
- **PASS** if, with weighted generation disabled, the candidate is absent from the output.
- **FAIL** if the candidate survives (indicating a hard-coded constant or a second, unexamined path).

### C6 — No E3 weights in training inputs or implementation constants
The frozen artifact must not supply the E3 oracle weights as training input or as a hard-coded implementation constant. This check verifies the weight is *derived*, not fed.
- **PASS** if the E3 reference weights (or an equivalent constant) do **not** appear among the training inputs nor as a hard-coded constant in the implementation.
- **FAIL** if the E3 weights (or an equivalent) are present as an input or constant.

---

## 4. Grading reference (sealed CUR-ENGEL-E3 matrix)

Against this the candidate's claimed classification is compared:

| Candidate observable | Verdict (sealed) | Sealed evidence |
|---|---|---|
| Raw total sum | **REFUTED** | each move adds `+2` to the sum, so the sum is not preserved |
| Parity of total sum | **PRESERVED_NOT_SEPARATING** | start sum `2` even; all-equal sum `6v` even; parity never separates start from target |
| Alternating sum `(1,-1,1,-1,1,-1)` | **PRESERVED_AND_SEPARATING** | initial reading `2`; all-equal reading `0` |
| Max entry | **REFUTED** | witness move_12: `(1,0,1,0,0,0) → (2,1,1,0,0,0)`, max `1 → 2` |
| Five-cycle (odd) | **NoNonzeroExactLinearObservable(move_family)** | no nonzero exact-integer alternating weighting over `{−1,0,1}` on the odd cycle |

---

## 5. Output format

On completion the evaluator emits one of:

```text
PASS:
  terms: <machine term(s) matching the sealed classification>
  derivation nodes: <the nodes in the frozen artifact that support the passes>
  checks: C1 PASS, C2 PASS, C3 PASS, C4 PASS, C5 PASS, C6 PASS

FAIL:
  unmet: <comma-separated Ck labels that did not pass>
  terms: <machine failure term per unmet check>
  derivation nodes: <the nodes that were absent or unsupported>
```

The evaluator does **not** produce a "partial" verdict: either all six checks pass (PASS) or at least one is enumerated as unmet (FAIL). Classification agreement (section 4) is reported as an additional note but is not folded into the six checks.

---

## 6. Not-run notes

- This contract is built now but **run only after a frozen G-ENG blind-output artifact arrives**.
- No production labels, packs, planner code, or training records are involved in this contract (it is a grading contract, not a training record).
- Sealing of the E3 oracle is INT-executed per `SEALED-ORACLES.spec.md`; the evaluator does not seal.

---

```text
result: evidence produced / files changed / tests run / merge request / blocked on
  evidence produced: E3 evaluator contract (6 checks C1-C6), graded against sealed E3 matrix
  files changed: CUR-ENGEL-E3-EVALUATOR-CONTRACT.md (this artifact)
  tests run: none (contract only; run when a frozen G-ENG blind-output artifact arrives)
  merge request: none (content-only; no code, no protocol edit, no seal)
  blocked on: frozen blind-output artifact from G-ENG (contract is run only when it arrives)
```
