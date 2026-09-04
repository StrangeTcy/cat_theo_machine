# CUR-ORACLE — Sealing request and distribution firewall (single handoff to INT)

**Date:** September 5, 2026
**Author role:** CUR-ORACLE (oracle-contaminated context; eligible for oracle-card, curriculum, inventory, math-verification, and E3/E4/E7 grader work; barred from G-ENG-LINEAR-INVARIANT generation, E3/E4/E7 runtime operators, and clean-room blind evaluation).
**Purpose:** operator-ready content for INT to execute the seal and to mirror the contamination firewall. No production code, no packs, no labels, no training records, no protocol edit in this file. Docs-only.

---

## Part A — Sealing request (INT executes per `SEALED-ORACLES.spec.md`)

The spec is located in the operator's instructions, not committed in the tree (verified: no `sealed-oracles/` and no `SEALED-ORACLES.spec.md` in either branch). Target directory follows the operator's convention:

```text
sealed-oracles/2026-09-04/
```

The three sealed-worthy oracles, with their exact source paths and the branch each currently lives on. The E4 uppercase/lowercase fork is **resolved** (Ruling 1): the canonical card is the lowercase file on `01a066cf`; the uppercase sibling on `01a068c2` is preserved as corroborating cross-verification evidence.

| Oracle | Canonical source (exact path) | Branch | `training-visible` |
|---|---|---|---|
| E3 | `CUR-ENGEL-E3-oracle.md` | `arena/01a068c2` (lands after INT merge step 2) | no |
| E4 | `CUR-ENGEL-E4-oracle.md` | `arena/01a066cf` | no |
| E7 | `CUR-ENGEL-E7-oracle.md` | `arena/01a066cf` | no |

**E3 note:** `CUR-ENGEL-E3-oracle.md` is the persisted eight-part oracle card with recomputed witnesses (created on `01a068c2`; not present on `01a066cf`, which holds only the nine-item inventory `CUR-ENGEL-E3.md`). The seal uses the oracle card. **E4 note:** the uppercase `CUR-ENGEL-E4-ORACLE.md` on `01a068c2` is the sibling variant (notation `V ≡ H`, `d−2s ≡ e_out−e_in`); it is cited in the seal manifest as corroborating evidence with its own content-id, **not** merged as a competing canonical.

**Content-id placeholders** (INT fills these at seal time; they are not fabricated here):

| Oracle | Canonical source | Proposed content-id | corroborating content-id | training-visible |
|---|---|---|---|---|
| E3 | `CUR-ENGEL-E3-oracle.md` | `<CONTENT-ID-E3>` | — | no |
| E4 | `CUR-ENGEL-E4-oracle.md` | `<CONTENT-ID-E4>` | `<CONTENT-ID-E4-VARIANT>` (uppercase sibling) | no |
| E7 | `CUR-ENGEL-E7-oracle.md` | `<CONTENT-ID-E7>` | — | no |

---

## Part B — Distribution firewall (for INT to mirror/apply in `protocol/DISTRIBUTION.md`)

Contamination is per-problem. A context that has seen a problem's oracle answer, weights, or readings is contaminated for that problem and is barred from that problem's generation, runtime operation, and clean-room blind evaluation. It may still serve as an **oracle-side grader** (grade a generated output against the known sealed oracle), and may continue with curriculum / inventory / math-verification work.

### Per-problem contamination records

| Problem | Contaminated by (sees) | Barred roles | Eligible roles |
|---|---|---|---|
| E3 | alternating-sum weights `(1,−1,1,−1,1,−1)`, readings `2`/`0`, grading classifications | G-ENG-LINEAR-INVARIANT generation; E3 runtime operator; E3 clean-room blind evaluator | E3 oracle grader; curriculum; inventory; math verification |
| E4 | descent measure `H` / `e_out − e_in` (same-house enemy-edge count), the degree-4 break and 4-cycle dual-terminal controls | E4 synthesizer; E4 runtime operator; E4 clean-room blind evaluator | E4 oracle grader; curriculum; inventory; math verification |
| E7 | mod-4 width-4 invariant `ResidueMod(S,4)`, the odd-width negative control | E7 synthesizer; E7 runtime operator; E7 clean-room blind evaluator | E7 oracle grader; curriculum; inventory; math verification |

### Key distinction preserved
- **Oracle-side grader** (grade output against a known sealed oracle): **allowed** for a contaminated context.
- **Clean-room blind evaluator** (grade without having seen the oracle, so the evaluation is uncontaminated): **not allowed** for a contaminated context — that role needs a context that has not seen the oracle.
- **Runtime operator / synthesis generation**: **not allowed** for a contaminated context.

### Firewall overrides
The contamination barrier bars **roles, not activity**. Completing a deliverable does not idle an agent; a contaminated context continues with eligible oracle/curriculum/inventory/math-verification work. Agents run until the operator ends the session.

---

## Part C — Merge / seal order (as ratified)

```text
1. INT merges arena/01a066cf (canonical CUR trail: E3 inventory, E4 oracle, E4 refutation, E7 oracle, protocol/CUR.md)
2. then arena/01a068c2 docs batch (uppercase E4 sibling, E3 oracle card, E3/E4/E7 grader contracts, this handoff)
3. then seal: E3 card (once persisted, already done), canonical E4, E7, per Part A
4. firewall mirror per Part B lands in protocol/DISTRIBUTION.md in the same batch
```

After step 2, the merged tree contains both `CUR-ENGEL-E4-oracle.md` (canonical) and `CUR-ENGEL-E4-ORACLE.md` (sibling). The sibling carries the reclassification note marking it as a verification variant of the canonical (Ruling 1) — it is not a competing canonical.

**E3-seal gate (Ruling 2, made explicit):** E3 oracle card sealing is gated on `01a068c2` merge completing first. The seal step for E3 must run **AFTER** merge step 2, because the canonical E3 oracle card (`CUR-ENGEL-E3-oracle.md`) does not exist in the merged tree until `01a068c2` lands. If INT runs the seal batch before merge step 2, the E3 entry will have no source file and its content-id will be computed from nothing. The E4 and E7 seals are not gated this way (their canonical cards are already on `01a066cf`); only the E3 entry carries this gating dependency.

---

```text
result: evidence produced / files changed / tests run / merge request / blocked on
  evidence produced: exact sealed-oracle paths (E3 on 01a068c2, E4/E7 canonical on 01a066cf),
      content-id + corroborating content-id placeholders, per-problem contamination records,
      merge/seal order
  files changed: CUR-ORACLE-SEALING-AND-DISTRIBUTION-HANDOFF.md (rewritten as single handoff)
  tests run: none (content-only design; no runtime machine tests)
  merge request: docs-only; awaits INT merge step 1 then step 2
  blocked on: INT executes merge/seal/firewall mirror; frozen G-ENG blind-output artifacts
      for the three graders (graders armed, not run)
```
