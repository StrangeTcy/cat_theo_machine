# CUR-ENGEL-E4-GRADER-CONTRACT

**Date:** September 5, 2026
**Role:** oracle-side E4 grader contract. Grades a **frozen blind-output artifact from G-ENG** against the **sealed canonical `CUR-ENGEL-E4-oracle.md`** (canonical on `arena/01a066cf`, `H` / `e_out − e_in` notation).
**Status:** contract built, not yet run. Run only when a frozen G-ENG blind-output artifact arrives.
**Contamination note:** this contract is written by the E4-contaminated context (it has seen the E4 descent measure). It grades **against the known canonical oracle**; it is **not** a clean-room blind evaluation. The clean-room blind-evaluator role is a distinct, disallowed role for this context.

---

## 1. Purpose

When G-ENG produces a frozen blind-output artifact claiming an E4 invariant/descent, this contract decides whether the claim matches the canonical oracle. Output is a verdict in machine terms plus the derivation nodes supporting it.

---

## 2. Inputs

**Required (exactly one frozen artifact):** the G-ENG generated candidate for E4, specifying:
- the claimed potential / monovariant and its classification;
- the derivation nodes / support cited.

**Required reference (fixed, from the canonical sealed oracle):**

- Enemy graph, each member in house 0 or 1 (exactly two houses), symmetric enemy relation.
- **Load-bearing given:** max degree ≤ 3 (each member has at most 3 enemies).
- Move: relocate a member with **≥ 2 enemies in its own house** to the other house.
- Monovariant: `H = # same-house enemy edges`.
- Descent: `ΔH = e_out − e_in ≤ −1` under the bound (`e_in ≥ 2` legal, `e_in + e_out ≤ 3` ⇒ `e_out ≤ 1`).
- Conclusion: termination at a state where no member has ≥ 2 same-house enemies.

---

## 3. Checks (independent; each PASS or FAIL-with-term)

### C1 — Hypothesis discharged (max degree ≤ 3 present)
- **PASS** if the derivation cites the max-degree ≤ 3 bound as load-bearing.
- **FAIL** if the descent is claimed from the general `e_in ≥ 2` condition alone.

### C2 — Exactly two houses discharged
- **PASS** if the derivation states exactly two houses (so relocation target is unique and `ΔH = e_out − e_in`).
- **FAIL** if houses are not bounded to two, or the relocation target is left ambiguous.

### C3 — Descent obligation discharged (ΔH ≤ −1 under legal moves)
- **PASS** if the derivation shows `e_in ≥ 2` + `e_in + e_out ≤ 3` ⇒ `e_out ≤ 1` ⇒ `ΔH = e_out − e_in ≤ −1` for every legal move.
- **FAIL** if an asserted strict descent is not bounded (e.g. deg-4 case `ΔH = 0`).

### C4 — Well-foundedness / termination discharged
- **PASS** if the derivation notes `H` is bounded below by 0 and integer-valued, so strict decrease ⇒ termination in at most `H_0` moves.
- **FAIL** if termination is claimed without a lower bound / well-founded order.

### C5 — Termination ≠ global minimum (no optimality overclaim)
- **PASS** if the derivation states termination yields "no legal move", not a global minimum.
- **FAIL** if it concludes minimality (reject the 4-cycle dual-terminal conflide).

### C6 — No E4 measure in training inputs or implementation constants
- **PASS** if the candidate measure is derived, not supplied as an input or hard-coded constant.
- **FAIL** if the E4 monovariant (or an equivalent) appears as an input constant.

---

## 4. Grading reference (sealed canonical E4 matrix)

| Failure mode | Verdict (sealed) | Witness |
|---|---|---|
| Ignore the degree bound | **REFUTED** | a legal move can have `e_out ≥ e_in`, so `ΔH` not guaranteed `< 0` |
| Measure = # members in house A | **REFUTED** | count is non-monotone (a move can increase or decrease it) |
| Measure = max same-house enemies | **REFUTED** | max need not drop by ≥ 1 on every move |
| Termination ⇒ global minimum | **REFUTED** | 4-cycle dual terminals (ΔH not unique) |
| Descent under max-degree ≤ 3 | **CORRECT** | `ΔH ≤ −1`, bounded below by 0 |

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

No partial verdict: PASS requires all six checks. Classification agreement (section 4) is reported as an additional note, not folded into the six checks.

**Discrepancy taxonomy (for the grading report):** each FAIL is classified as one of `hypothesis-omitted` (C1/C2), `descent-unsupported` (C3/C4), `overclaim` (C5), or `constant-injection` (C6).

---

## 6. Not-run notes

- Built now; run only after a frozen G-ENG blind-output artifact arrives.
- No production labels, packs, planner code, or training records. Sealing is INT-executed.

---

```text
result: evidence produced / files changed / tests run / merge request / blocked on
  evidence produced: E4 grader contract (C1-C6) against canonical E4 oracle (H, e_out-e_in)
  files changed: CUR-ENGEL-E4-GRADER-CONTRACT.md
  tests run: none (contract only; run when a frozen G-ENG artifact arrives)
  merge request: docs-only on arena/01a068c2
  blocked on: frozen G-ENG blind-output artifact for E4
```
