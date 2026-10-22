# CUR-ENGEL-E3 — Oracle card (six-sector alternating sum)

**Date:** September 5, 2026
**Status:** source-pinned oracle text; not sealed, not machine training input.
**Canonical convention:** lowercase filename matching `CUR-ENGEL-E4-oracle.md` / `CUR-ENGEL-E7-oracle.md` on `arena/01a066cf`.
**Recompute discipline:** every weight, reading, and classification below was **recomputed this session from the move constraints** (measured, not recalled). Nothing asserted from memory. Any item not recomputable would be marked `unverified-recall`; no item required that mark.

---

## 1. Reference observable

For a six-sector state `a = (a_1,...,a_6)`, the reference observable is the exact-integer alternating sum

\[
R(a) = \sum_{i=1}^{6} w_i a_i,\qquad w = (1,-1,1,-1,1,-1).
\]

Computed from the move condition: a move increases two neighboring entries by 1, so for the observable to be preserved under every move we need

\[
w_i + w_{i+1} = 0 \quad(1 \le i \le 6,\ \text{indices cyclic}).
\]

Solving the six cyclic constraints gives exactly the alternating family `w = (c, −c, c, −c, c, −c)`. Over integer weights, the nonzero solutions are `c ∈ {−3,−2,−1,1,2,3}` (verified by brute-force over `c ∈ [−3,3]`). The reference takes the primitive generator `c = 1`, i.e. `(1,−1,1,−1,1,−1)`.

---

## 2. Start and target readings

\[
R(\text{start}) = R(1,0,1,0,0,0) = 1 - 0 + 1 - 0 + 0 - 0 = 2.
\]

For the target class (all six equal to any value `v`):

\[
R(v,v,v,v,v,v) = v - v + v - v + v - v = 0.
\]

So the start reading is `2` and the all-equal reading is `0` for every `v`. A move preserves `R` (see item 3), the start reading is nonzero, and the target reading is zero — hence the all-equal state is **unreachable**, which answers the problem in the negative.

---

## 3. Preservation of the observable

Under the move at pair `(i, i+1)` (adds `+1` to positions `i` and `i+1`):

\[
\Delta R = w_i + w_{i+1} = 1 + (-1) = 0.
\]

So every legal move leaves `R` unchanged. The observable is preserved (an invariant), verified directly from the alternating weights.

---

## 4. Preservation / separation matrix

| Candidate observable | Verdict | Evidence (computed) |
|---|---|---|
| Raw total sum `Σ a_i` | **REFUTED** | a move adds `+2` to the sum (`w_i=w_{i+1}=1`), so the sum is not preserved |
| Parity of total sum | **PRESERVED_NOT_SEPARATING** | start sum `2` is even; all-equal sum `6v` is even for every integer `v`; parity never distinguishes start from target |
| Alternating sum `(1,−1,1,−1,1,−1)` | **PRESERVED_AND_SEPARATING** | `R(start)=2`, `R(all-equal)=0`; preserved because `w_i+w_{i+1}=0` |
| Max entry | **REFUTED** | witness move_12: `(1,0,1,0,0,0) → (2,1,1,0,0,0)`, max `1 → 2` |
| Odd cycle (n=5) | **NoNonzeroExactLinearObservable(move_family)** | the cyclic constraints force `w_0 = −w_1 = w_2 = ... = −w_{n−1} = −w_0`, so `w_0 = 0`; only the zero weighting solves it |

---

## 5. Concrete witnesses for the rejected candidates

- **Raw sum:** apply move_12 once to `(1,0,1,0,0,0)` → `(2,1,1,0,0,0)`. Sum `2 → 4`, so the sum is not preserved.
- **Max entry:** same move `(1,0,1,0,0,0) → (2,1,1,0,0,0)`, with max `1 → 2`; the max changes, so it is not an invariant.
- **Parity of sum:** start sum `2` (even) and all-equal `(1,1,1,1,1,1)` sum `6` (even) — parity is even on both sides, so it cannot separate the reachable start from the target.

---

## 6. Negative control — odd cycle width

The reference cycle has `n = 6` (even), where `(1,−1,1,−1,1,−1)` is a nonzero exact-integer alternating weighting. For an **odd** cycle `n = 5`, solve the same cyclic constraints `w_i + w_{i+1} = 0`:

\[
w_0 = -w_1 = w_2 = -w_3 = w_4 = -w_0 \implies w_0 = -w_0 \implies w_0 = 0,
\]

so every `w_i = 0`. There is **no nonzero** exact-integer alternating weighting over `{−1,0,1}` (or any integer set) on the odd cycle. This is a genuine negative control on the width/parity of the cycle, distinguishing `n=6` (soluble) from `n=5` (not soluble) for the same move family. (Computed: over `c ∈ [−3,3]`, the only solution for `n=5` is the all-zero one.)

---

## 7. Conclusion for the oracle

The exact-linear invariant is the alternating sum `(1,−1,1,−1,1,−1)`. It is **preserved and separating**: start reading `2`, all-equal reading `0`, preserved under every move. Therefore **no** sequence of moves can make all six sectors equal; the answer to the problem is no.

The odd-cycle (`n=5`) control is genuine: the same move family admits **no** nonzero exact-integer alternating weighting over the odd cycle, confirming the mechanism depends on `n` even.

---

## 8. Source provenance

- Statement: Engel, Chapter 1, Problem E3 (a circle divided into six sectors containing `1,0,1,0,0,0`; a move increases two neighboring entries by 1; can all entries become equal?).
- Reconstruction note: the earlier nine-item `CUR-ENGEL-E3.md` inventory is a **read-only content inventory**. This file is the oracle card in canonical lowercase convention.
- All numbers recomputed this session; no item marked `unverified-recall`.

---

```text
result: evidence produced / files changed / tests run / merge request / blocked on
  evidence produced: E3 alternating-sum observable (1,-1,1,-1,1,-1) recomputed from move
      constraints w_i+w_{i+1}=0; start reading 2, all-equal reading 0 (all v); preservation
      delta 0; matrix (raw sum REFUTED, parity PNS, alternating PSA, max REFUTED); odd n=5
      NoNonzeroExactLinearObservable
  files changed: CUR-ENGEL-E3-oracle.md (this persistence)
  tests run: source-only recomputation (brute-force over c in [-3,3], both n=6 and n=5)
  merge request: docs-only on arena/01a068c2
  blocked on: sealing is INT-executed per Part A
```
