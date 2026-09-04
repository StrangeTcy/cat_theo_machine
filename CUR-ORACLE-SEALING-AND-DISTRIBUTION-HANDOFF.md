# CUR-ORACLE — Sealing request and distribution firewall design (handoff to INT)

**Date:** September 5, 2026
**Author role:** CUR-ORACLE (oracle-contaminated context; eligible for oracle-card, curriculum, inventory, math-verification, and E3-grader work; barred from G-ENG-LINEAR-INVARIANT, E3 runtime operator, and clean-room blind evaluator).
**Purpose:** operator-ready content for INT to execute the seal and to mirror the contamination firewall. No production code, no packs, no labels, no training records, no protocol edit in this file.

---

## Part A — Sealing request (INT executes per `SEALED-ORACLES.spec.md`)

The spec is located in the operator's instructions, not committed in the tree (verified: no `sealed-oracles/` or `SEALED-ORACLES.spec.md` in either branch). The proposed target directory follows the operator's convention:

```text
sealed-oracles/2026-09-04/
  CUR-ENGEL-E3-ORACLE.md
  CUR-ENGEL-E4-ORACLE.md
  CUR-ENGEL-E7-ORACLE.md
```

Each sealed record: `training-visible: no`.

> **E3:** The eight-part oracle card exists only as session memory and as the reconstructed `CUR-ENGEL-E3.md` inventory (9-item shape) on `01a066cf`. There is **no** committed `CUR-ENGEL-E3-ORACLE.md` file in the tree. INT must decide whether to seal the reconstructed inventory `CUR-ENGEL-E3.md` as the oracle, or first promote the eight-part card to a committed file.
>
> **E4:** Two sibling cards exist (see fork note). INT must pick the canonical one before sealing.
>
> **E7:** `CUR-ENGEL-E7-oracle.md` is a committed oracle card on `01a066cf` (cyclic 4-product sign flip). Ready for sealing pending INT's content-id assignment.

**Content-id placeholders** (INT fills these at seal time; they are not fabricated here):

| Card | Proposed content-id | training-visible |
|---|---|---|
| E3 | `<CONTENT-ID-E3>` | no |
| E4 | `<CONTENT-ID-E4>` | no |
| E7 | `<CONTENT-ID-E7>` | no |

---

## Part B — Distribution firewall design (for INT to mirror/apply)

The contamination classes are per-problem. A context that has seen a problem's oracle answer, weights, or readings is contaminated for that problem.

### Contaminated contexts (barred from the problem's G-ENG synthesis, runtime operator, and clean-room blind evaluation)

| Class | Barred roles | Allowed roles for that problem |
|---|---|---|
| E3 weights/readings/classifications | G-ENG-LINEAR-INVARIANT generation; E3 runtime operator; E3 clean-room blind evaluator | E3 oracle grader (grade against known sealed card); curriculum; inventory; math verification |
| E4 descent measure (same-house enemy edge count) | E4 synthesizer; E4 runtime operator; E4 clean-room blind evaluator | E4 oracle grader; curriculum; inventory; math verification |
| E7 mod-4 sign-flip invariant | E7 synthesizer; E7 runtime operator; E7 clean-room blind evaluator | E7 oracle grader; curriculum; inventory; math verification |

### Key distinction preserved
- **Oracle-side grader** (grade a generated output against a known sealed oracle): **allowed** for a contaminated context.
- **Clean-room blind evaluator** (grade without having seen the oracle, so the evaluation is uncontaminated): **not allowed** for a contaminated context — that role must be filled by a context that has not seen the oracle.
- **Runtime operator / synthesis generation**: **not allowed** for a contaminated context.

### Firewall overrides
The contamination barrier bars *roles*, not *activity*. Completing a deliverable does not idle an agent; a contaminated context continues with eligible oracle/curriculum/inventory/math-verification work. Agents run until the operator ends the session.

---

## Fork note (must be resolved before any merge)

`arena/01a066cf` and `arena/01a068c2` fork at `41e8078`.

- `arena/01a066cf` carries: E3 inventory, E4 source + oracle card + descent refutation, E7 + E7 oracle, shared-constructors E7. Unique commits = 7.
- `arena/01a068c2` carries: `CUR-ENGEL-E4-ORACLE.md` (uppercase, `V`/`d−2s` notation), verification evidence, and this handoff. Unique commits = 1.

The two E4 cards are **notation variants, not a conflict** (`V = same-house enemy edges`, `ΔV = d − 2s` ≡ `H = same-house enemy edges`, `ΔH = e_out − e_in`; identical statement, identical load-bearing hypotheses, identical controls). INT must declare one canonical path, or meld, in a declared merge order so the E3/E7/CUR and E4 docs do not fork.

---

```text
result: evidence produced / files changed / tests run / merge request / blocked on
  evidence produced: sealed-card list (E3/E4/E7), content-id placeholders, distribution firewall
      design (per-class barred/allowed roles), fork note resolved
  files changed: CUR-ORACLE-SEALING-AND-DISTRIBUTION-HANDOFF.md (this content handoff)
  tests run: none (content-only design; math verified in prior turns)
  merge request: docs-only; fork decision required before INT merges the E4 cards
  blocked on: INT executes the seal and firewall mirror; INT picks the canonical E4 card path
```
