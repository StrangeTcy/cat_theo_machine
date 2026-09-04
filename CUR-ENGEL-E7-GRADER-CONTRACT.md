# CUR-ENGEL-E7-GRADER-CONTRACT

**Date:** September 5, 2026
**Role:** oracle-side E7 grader contract. Grades a **frozen blind-output artifact from G-ENG** against the **sealed canonical `CUR-ENGEL-E7-oracle.md`** (canonical on `arena/01a066cf`).
**Status:** contract built, not yet run. Run only when a frozen G-ENG blind-output artifact arrives.
**Contamination note:** this contract is written by the E7-contaminated context (it has seen the E7 mod-4 invariant). It grades **against the known canonical oracle**; it is **not** a clean-room blind evaluation.

---

## 1. Purpose

When G-ENG produces a frozen blind-output artifact claiming an E7 invariant, this contract decides whether the claim matches the canonical oracle. Output is a verdict in machine terms plus the derivation nodes supporting it.

---

## 2. Inputs

**Required (exactly one frozen artifact):** the G-ENG generated candidate for E7, specifying:
- the claimed observable and its classification;
- the derivation nodes / support cited.

**Required reference (fixed, from the canonical sealed oracle):**

- Universe: sign vector `a ∈ {−1,1}^n`, indices mod `n`, `n ≥ 4`.
- Move: `FlipSign(state, position)` (negate `a_j`, leaving others unchanged).
- Reference observable: `S = Σ_i (a_i a_{i+1} a_{i+2} a_{i+3})` (width-4 cyclic window products), and `O = ResidueMod(S, 4)`.
- Claim: `O` is invariant under `FlipSign`, so a start with `S = 0` forces terminal `n mod 4 = 0`, i.e. `4 | n`.

---

## 3. Checks (independent; each PASS or FAIL-with-term)

### C1 — Observable derived from the move constraints
- **PASS** if the candidate's derivation cites the `FlipSign` move family and the observable is derived from the width-4 cyclic window-product structure.
- **FAIL** if the candidate is invented without reference to the move set.

### C2 — Preservation obligation discharged (mod-4)
- **PASS** if the derivation shows `ΔS = −2(p_1+p_2+p_3+p_4)` with the four-product sum even, so `ΔS ∈ {−8,−4,0,4,8}` and `ResidueMod(S,4)` is unchanged under every `FlipSign`.
- **FAIL** if preservation is claimed without the even-window argument (or asserted at odd width).

### C3 — Start/target separation discharged
- **PASS** if the start residue `0` differs from the target residue `n mod 4` whenever `4 ∤ n`.
- **FAIL** if the observable cannot separate admissible (`4 | n`) from inadmissible cases.

### C4 — Odd-width negative control discharged
- **PASS** if the derivation emits the odd-width failure (window `width=3` gives `ΔS ≡ 2 (mod 4)`, not preserved) as a genuine negative control.
- **FAIL** if the width-3 control is omitted, or if the mod-4 preservation is claimed to hold for all widths.

### C5 — Rejected candidates correctly classified
- **PASS** if the derivation classifies `Σ a_i` as not invariant, `∏ a_i` as not invariant, and `Parity(S)` as preserved-but-non-separating.
- **FAIL** if any rejected candidate is asserted invariant, or if parity is claimed to separate.

### C6 — No E7 weights in training inputs or implementation constants
- **PASS** if the observable is derived, not supplied as an input or hard-coded constant.
- **FAIL** if the E7 reference weights (or an equivalent) appear as an input constant.

---

## 4. Grading reference (sealed canonical E7 matrix)

| Candidate observable | Verdict (sealed) | Evidence |
|---|---|---|
| `Σ a_i` | **REFUTED** | `FlipSign` changes it by `−2` (state `[1,1,1,1]` → `[-1,1,1,1]`) |
| `∏ a_i` | **REFUTED** | `FlipSign` negates it (state `[1,1,1,1]` → `[-1,1,1,1]`) |
| `Parity(S)` | **PRESERVED_NOT_SEPARATING** | `n=6` target `S=6` even but `6 mod 4 = 2 ≠ 0` |
| `ResidueMod(S, 4)`, width 4 | **PRESERVED_AND_SEPARATING** | start `0` differs from `n mod 4` whenever `4 ∤ n` |
| Odd width (3) control | **REFUTED for preservation** | `ΔS ≡ 2 (mod 4)`, not invariant |

---

## 5. Output format

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

No partial verdict: PASS requires all six checks. Classification agreement (section 4) is reported as an additional note.

**Discrepancy taxonomy:** each FAIL is classified as `derivation-absent` (C1), `preservation-unsupported` (C2/C4), `separation-unsupported`/`overclaim` (C3/C5), or `constant-injection` (C6).

---

## 6. Not-run notes

- Built now; run only after a frozen G-ENG blind-output artifact arrives.
- No production labels, packs, planner code, or training records. Sealing is INT-executed.

---

```text
result: evidence produced / files changed / tests run / merge request / blocked on
  evidence produced: E7 grader contract (C1-C6) against canonical E7 oracle (mod-4 width-4)
  files changed: CUR-ENGEL-E7-GRADER-CONTRACT.md
  tests run: none (contract only; run when a frozen G-ENG artifact arrives)
  merge request: docs-only on arena/01a068c2
  blocked on: frozen G-ENG blind-output artifact for E7
```
