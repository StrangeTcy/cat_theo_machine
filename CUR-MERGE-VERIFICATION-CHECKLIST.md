# CUR-MERGE-VERIFICATION-CHECKLIST

**Date:** September 5, 2026
**Purpose:** runnable checklist for INT (or a future CUR context) to confirm the merged tree is correct after the two-branch merge (`arena/01a066cf` then `arena/01a068c2`). Converts the implicit acceptance criteria into explicit checks. Docs-only; no production artefacts validated.

**Pre-merge reference hashes** (recorded before the merge; recompute the same file at the merged tip and compare):

| Oracle | Source (path) | Pre-merge SHA-256 |
|---|---|---|
| E3 | `CUR-ENGEL-E3-oracle.md` | `31a8026d6e59de537d21533d96a0d0050b7bb9a3bbe6c181e138d150fa544b11` |
| E4 (canonical) | `CUR-ENGEL-E4-oracle.md` | `a11ca451e52dbeb7dc3b65854a2ccc500c33dad5647e108510042a3617af9353` |
| E4 (sibling) | `CUR-ENGEL-E4-ORACLE.md` | `0ff055a6f6dc5c81848daa8135cc15efca4ae568c444982ed153e7e75c23c328` |
| E7 | `CUR-ENGEL-E7-oracle.md` | `bd4942a6040b80f825bc25c40dbca4c7db450f5cf1f416643024d9fe9a60ef60` |

---

## Checks

### 1. E3 oracle card present and content-id matches pre-merge hash
- [ ] `CUR-ENGEL-E3-oracle.md` exists in the merged tree.
- [ ] `git show <tip>:CUR-ENGEL-E3-oracle.md | sha256sum` equals `31a8026d...b11` (unchanged by the merge).
- [ ] Its content-id (if assigned at seal post-merge) is computed from this file, not reconstructed.

### 2. E4 canonical present; sibling present with reclassification note
- [ ] `CUR-ENGEL-E4-oracle.md` exists (canonical, from `01a066cf`).
- [ ] `git show <tip>:CUR-ENGEL-E4-oracle.md | sha256sum` equals `a11ca45...9353`.
- [ ] `CUR-ENGEL-E4-ORACLE.md` also exists (sibling, from `01a068c2`).
- [ ] `CUR-ENGEL-E4-ORACLE.md` carries the reclassification note (independent verification variant of the canonical; `V ≡ H`, `d−2s ≡ e_out−e_in`).
- [ ] The two files are not a byte-for-byte duplicate (they are notation variants by design).

### 3. E7 oracle card present
- [ ] `CUR-ENGEL-E7-oracle.md` exists.
- [ ] `git show <tip>:CUR-ENGEL-E7-oracle.md | sha256sum` equals `bd4942a...ef60`.

### 4. No training-visible oracle files
- [ ] Each of `CUR-ENGEL-E3-oracle.md`, `CUR-ENGEL-E4-oracle.md`, `CUR-ENGEL-E4-ORACLE.md`, `CUR-ENGEL-E7-oracle.md` carries a `training-visible: no` line (or a header that states it is not machine training input).
- [ ] No `training_records/` file was added for E3/E4/E7 by this work.

### 5. Firewall entries name all three problems
- [ ] `protocol/DISTRIBUTION.md` exists and lists all three contamination classes: E3 weights/readings, E4 descent measure, E7 mod-4 width-4 invariant.
- [ ] Each entry has a barred-roles vs eligible-roles split (generation / runtime operator / clean-room blind evaluator barred; oracle-side grader, curriculum, inventory, math verification eligible).

### 6. §0 scan across merged CUR-* set shows zero banned tokens
- [ ] Hex-scan every `CUR-ENGEL-*` and `CUR-ORACLE-*` and `CUR-MERGE-*` file (and the commit subjects) against the six-entry banned list. Expect zero matches.

### 7. Grader contracts present and unauthorised
- [ ] `CUR-ENGEL-E3-EVALUATOR-CONTRACT.md`, `CUR-ENGEL-E4-GRADER-CONTRACT.md`, `CUR-ENGEL-E7-GRADER-CONTRACT.md` exist.
- [ ] None of them was run (each states "not run; run only when a frozen G-ENG blind-output artifact arrives").

---

## How to run

```text
for f in CUR-ENGEL-E3-oracle.md CUR-ENGEL-E4-oracle.md CUR-ENGEL-E4-ORACLE.md CUR-ENGEL-E7-oracle.md; do
  echo "$f"; git show <tip>:"$f" | sha256sum
done
```

Compare against the pre-merge table above; any mismatch means the merge altered a sealed-oracle candidate and it must be re-verified before sealing.

---

```text
result: evidence produced / files changed / tests run / merge request / blocked on
  evidence produced: runnable merge-verification checklist with pre-merge SHA-256 hashes for
      the three sealed-oracle candidates + sibling
  files changed: CUR-MERGE-VERIFICATION-CHECKLIST.md
  tests run: none (checklist; hashes recorded, not yet compared at merged tip)
  merge request: docs-only on arena/01a068c2
  blocked on: the merge itself (INT); grader artifacts for E3/E4/E7 (armed, not run)
```
