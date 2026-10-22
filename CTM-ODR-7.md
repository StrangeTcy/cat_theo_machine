# CTM-ODR-7 — Programme integration

**Spec ID:** `CTM-ODR-7`
**Date:** 2026-10-01
**Companion to:** `CTM-ODR-6.md` (the one-day build)
**Question answered:** how does the ODR-6 requirement merge with the five tracks (G/I/S/E/F), the pyground (INV-0), and the overnight researcher (Researcher-v0)?

---

## §0 The correction that has to land first

**ODR-6 is built on a stale base.** My session was branched from `428ecdc`, and everything in ODR-6 was measured there. But `428ecdc` is not the machine — it is a snapshot of it. Measured on the carrier branches:

| Path | on `428ecdc` (my base) | on `origin/arena/01a0eca3` |
|---|---|---|
| `session.py` | absent | **present** |
| `wire.py` | absent | **present** (562 lines) |
| `vocabulary.py` | absent | **present** (3,015 lines) |
| `verbalizer.py` | absent | **present** |
| `language.py`, `nl_parser.py` | absent | **present** |
| `protocol/` | absent | **present** |
| `researcher_v0/` | absent | **present** |
| `training_records/` | absent | **present** |
| `invariant_experiment.py` | absent | absent |

Carrier divergence from my base: **211 files changed, +162,274 / −1,240,013**. The deletions are almost entirely `snapshots/hyge_snapshot_v8.json` (1,233,703 lines) plus a 5,540-line `testsuite.py` restructure — housekeeping, not code loss.

Two consequences I got wrong and am correcting here:

1. **ODR-1 was not hallucinating `session.py` and `wire.py`.** I marked them "Do not exist" in `CTM-ODR-6.md` Appendix H. They exist; they are simply not on the commit this session inherited. The correct statement is "absent from the base I was given," which is a fact about my branch, not about the repository.
2. **ODR-6's §0 table is measured on the right tree for what it claims** (every probe ran against `428ecdc` and is reproducible there), **but the plan is aimed at the wrong target.** The `input()` seam, the missing step checker, and the absent residual/dependency/teaching vocabulary were all verified against a tree that lacks `wire.py`, the vocabulary layer, and the programme. Those findings must be **re-verified on the carrier** before dispatch, and some will change: a teaching ingress may already exist.

**Phase 0 is therefore not optional: re-base, then re-measure, then dispatch.** A one-day plan aimed at `428ecdc` builds against a machine that is months behind the one being developed.

---

## §1 The answer in one line

They do not merge as peers.

> **The five dimensions are the org chart and the invariants. INV-0 and Researcher-v0 are two inert demonstrations at a lower trust level. ODR-6 is a one-day build that produces the next frozen cut. The merge is a dependency relation with four named interfaces — not a union of task lists.**

Concretely: **ODR-6 produces the cut; the programme consumes it.** The programme contributes *constraints* (things the day must not violate) and *consumers* (things that must be able to read the day's output). It contributes **zero tasks**. That rule is the whole discipline of this document, and §7 defends it.

---

## §2 What each artifact is, in the programme's own terms

| Artifact | Kind | Trust level | Lives on | Relation to ODR-6 |
|---|---|---|---|---|
| **Five tracks G/I/S/E/F** | months-scale programme: organisation, invariants, measurement protocol | live path, tagged, human-gated | `protocol/*.md` on `01a05cb0`, `01a05d5d`, `01a0eca3` | ODR-6 is a one-day instance of one of its gates |
| **Pyground / INV-0** | checked invariant-discovery laboratory | **inert** — no activation, no live knowledge; own restricted codec | `01a0bb91` **only** | design model for CL2; supplies a checker discipline ODR-6 lacked |
| **Researcher-v0** | inert overnight research worker, G0–G6 complete | **inert** — no admission, rent, or live writes | `01a0eca3` (+ 4 siblings) | CL0's inventory method; and the clearest statement of why CL6 matters |
| **ODR-6** | one-day build + pre-tag acceptance | produces a cut | `01a0f845` | the day |

**The trust ladder is the key structure:** programme (live, tagged, human-gated) ▸ ODR-6 (produces the cut that the live path will rest on) ▸ Researcher-v0 and INV-0 (inert, can consume nothing, can promote nothing). Work flows **up** the ladder one rung at a time, and only through a gate.

---

## §3 Four resonances that are not coincidences

These four are why the merge is coherent rather than bolted-on.

**R1 — ODR-6's four legs *are* the programme's third invariant.**
`protocol/LAUNCH-PLAN.md` §1: *"Nothing counts until it appears and disappears with the structure claimed to produce it (enable/disable/reset/re-mine, ablation, provenance)."* ODR-6's control / treatment / replay / ablation is exactly that sentence, applied to a one-day object. The four legs are not an ODR-6 invention and should not be presented as one — they are the programme's own standard, and ODR-6 simply makes them executable by script rather than by an operator's session.

**R2 — ODR-6 Track II (CL8) is S-track S2/S3 compressed.**
S2 mines `RelationSchema` from two-or-more adopted laws with distinct relation heads and matching contracts; S3 instantiates it into `ProposedMacroLaw`, which then passes held-out validation, the rent gate, human approval, and the learned-memory lifecycle. CL8's shape is identical: traces → generalised schema → sealed holdout → checked use. CL8 is narrower and must **say so**: no rent gate, no human promotion, no far transfer. It is the mechanism tested at one-day scale, not the mechanism certified.

**R3 — ODR-6's holdout seal is I-track's retirement discipline.**
`protocol/CHARTER-v2.md`: *"Once an exam derivation is released to S or E for training, retire it from future held-out claims for the affected component."* Seal-before-holdout and retirement-after-release are the same rule seen from opposite ends of a day. CL8's seal is that rule made cryptographic.

**R4 — ODR-6's R2 and G's five-method list are the same prohibition.**
G: *exactly five methods, no sixth, no `if goal contains …` dispatch.* ODR-6 R2: *no test-visible fixture constants.* Both forbid shape-based special-casing — recognising the answer instead of deriving it. One is a constraint on planner content, the other on application code; they are one rule.

---

## §4 The four collisions, and how each resolves

**C1 — The measurement invariant vs. a day of continuous semantic change.**
The programme's rule: measurements count only on a frozen tag, and a semantic change forces full suite → new tag → rerun blank controls. ODR-6 is a day of unbroken semantic change. Under the programme's rules, **nothing measured during the day counts**.

*Resolution:* ODR-6 is not a measurement, and must stop being described as one. It produces a **cut**. The four legs, the bounded suite, and the blank controls are **pre-tag acceptance** — precisely what INT requires before publishing the next immutable measurement tag. Operators then run *on* that cut. This is the single most important reframing in the merge: it turns an apparent conflict into the programme's own next step.

**C2 — The inert demonstrations vs. closing the loop.**
INV-0 and Researcher-v0 are forbidden from activation, admission, rent, and live-knowledge writes. ODR-6's entire point is to admit a candidate and use it.

*Resolution:* the inert constraint is not principled opposition to activation — it is a consequence of there being **no gate to activate through**. Researcher-v0's brief forbids admission because admission does not exist. ODR-6's CL6 *builds* that gate. So:

> **CL6 is the unlock for researcher-v1.** Until a candidate can be admitted for a scoped session and independently checked, an overnight researcher must remain inert, because it has no safe way to affect anything.

That also sets the direction of travel: INV-0 → Researcher-v0 (inert, safe) → *ODR-6 CL6* → Researcher-v1 (bounded, admitted, checked, still revocable). The programme's S-track rent gate and human promotion remain the rung above that.

**C3 — Persistence: F1 is a shared blocker, and both demonstrations routed around it.**
INV-0's report explicitly rejected the main snapshot path: *"Its shared-singleton field writes at `persistence.py:1125-1164` make it unsuitable for the stricter replay boundary."* It then wrote its own restricted JSON codec — no object activation, no pickle, no import instructions. Researcher-v0, per its G0 inspection, built a v0-local journal for the same class of reason.

Both demonstrations are carrying **private persistence** because the shared one is broken. So:

> **F1 is not an ODR-6 task that happens to be on the critical path. It is the one change that lets three otherwise-separate artifacts share a replay substrate.**

Until F1 lands, every artifact that needs cold replay pays for its own codec. After F1, INV-0's and Researcher-v0's replay boundary can be re-expressed against the shared path — or, if they prefer isolation, the *reason* for isolation must be restated, because "shared-singleton writes" will no longer be it.

**C4 — Two residual vocabularies.**
F-track audit requires that *every teach was preceded by a concrete residual*, and that `computable-request` count be zero. ODR-6's CL3 builds residual as `PlannerObligation` + `PlannerDependency`.

*Resolution:* these are not competitors; CL3 is the machine-term substrate for F's requirement. F's audit is the *consumer*. The merge is: CL3 must emit residuals in a form F's grading script can classify, and F's `must be zero` bar (a computable request is a defect) becomes a CL3 acceptance criterion. See §6.

---

## §5 The merge is mechanical on one side and real on the other

Measured, not assumed:

**INV-0 merges mechanically.** `git diff 428ecdc origin/arena/01a0bb91` = **29 files, 1,872 insertions, zero shared-file edits** — all new files (`invariant_experiment.py`, `validation/test_inv0_invariant_discovery.py`, `verification/inv0_*`). A cherry-pick onto a carrier cannot conflict by construction.

**The carrier does not merge mechanically with anything.** Five branches carry programme + researcher (`01a0352a`, `01a0d2fb`, `01a0d325`, `01a0d40c`, `01a0eca3`); **none** carries `invariant_experiment.py`. All are descendants of the same base but 211 files diverge from it. The natural carrier is **`01a0eca3`** — newest (2026-09-29) and G6-complete.

So the shape is: one clean cherry-pick, onto one chosen carrier, plus a re-measurement of every ODR-6 probe.

---

## §6 What ODR-6 owes back to each track

The merge, stated as obligations. Each row is a *consumer relationship*, and none of them adds a task to the day.

| To | What the day must yield | Why that track needs it |
|---|---|---|
| **G** | residuals expressed in the planner ontology (`PlannerProblem`, `PlannerObligation`, `PlannerDependency`, `PlannerAlternative*`) — the machine-term form of "a concrete residual" | G supplies method payloads and obligation skeletons; it needs obligations that are already first-class |
| **I** | the sealed-holdout mechanism, reusable: candidate hashed before release, holdout released after, retirement recorded | I's exam discipline needs a mechanism, not a convention |
| **S** | CL8's induction harness plus the **sealed-budget ablation conjunct** (holdout positives must fail without the candidate) — reported as `bounded_search_gain`, never as speedup | S must distinguish "the macro is used" from "the macro is necessary"; that *is* the rent gate's question |
| **E** | derivations carrying step-level provenance sufficient for every sentence to trace to a node | E1's acceptance is traceability; it cannot be retrofitted onto derivations that never carried it |
| **F** | the approval-policy seam (`interactive` / `auto-proceed` / `deny`) with a machine-term approval event carrying provenance, plus `intervention_events: 0` as a graded field | F's audit header lists every loaded class and every teach must follow a concrete residual; the day must be able to prove it made no undeclared human decisions |

**The two additions CL3 inherits from F** (adopt verbatim, they are free and they are strict):
- `computable-request count` on residuals must be **zero** — a residual that names something the machine could simply compute is a defect in characterisation, not a request for teaching.
- residual classification must support **role coverage (recall vs discovery)**, so F's grader can read the day's output without a human interpreting transcripts.

**The one addition CL2 inherits from INV-0** — a real improvement to ODR-6:

> INV-0's reachability obstruction **returns `Unknown` rather than a verdict when the two observations are equal.** ODR-6's checker (§3, CL2) has a forced binary verdict vocabulary with no `inconclusive` member. Add one. A checker that cannot say "I cannot decide this" will eventually decide it wrongly, and the mutation matrix will not catch that, because every mutation has a correct answer.

---

## §7 What does **not** merge — and the rule that keeps it that way

**Does not merge:**

| Excluded | Reason |
|---|---|
| `hyge.py` / `session.txt` | struck by operator ruling |
| **E track** | consumes solved proofs and adopted laws; the day produces neither at scale. E contributes one constraint (traceability, §6) and no task |
| **F's session tooling** | built for human-run operator sessions; the day has none. F contributes the approval-policy requirement and the grading fields, not its harness |
| **S's rent gate, human promotion, far-transfer, cross-domain schemas** | explicitly outside the day's claim. CL8 must report `bounded_search_gain` and `AUTO_SCHEMA_INDUCTION` separately and never imply rent |
| **S5 near-transfer rerun, E1 held-out transfer, G1 method alignment, Experiment 4** | programme-scale sessions. Adding any of them converts a 16-hour build into a fortnight |

**The rule:**

> **The programme may impose a *constraint* (a thing the day must not violate) or a *consumer* (a thing that must be able to read the day's output). It may never impose a *task*.**

This is not tidiness. The original question was how to compress months into a day; a merge that imports the months is the exact failure mode the whole chain was built to avoid. Ten tasks at T+0 is the point. Eleven would be a symptom.

---

## §8 Operational sequencing — three phases

**Phase 0 — before the day (not part of the 16 h).**
- **H0 (human decision):** designate the carrier. Recommendation: `01a0eca3`, newest and G6-complete. Alternatives: `01a0d40c` (G3-complete, simpler), or `01a05cb0` (programme docs, no researcher).
- Cherry-pick INV-0's 29 additive files onto the carrier. Verify no shared-file conflict (expected: none).
- **Re-run every ODR-6 probe on the carrier** and re-issue the §0 table. Findings expected to change: whether a teaching ingress already exists (`wire.py`), whether the `input()` seam still sits at `search/compare_subprocess.py:248`, and whether the snapshot round trip still fails.
- Freeze: carrier SHA becomes `BASE_SHA` for the day, and the first measurement tag after it.

**Phase 1 — the day.**
ODR-6 on the carrier → **cut N+1 plus its pre-tag acceptance**. The four legs are the acceptance, not a research result. Deliverable: the release report (one page, machine-filled) plus the frozen tag.

**Phase 2 — after the day.**
- Operators run sessions on cut N+1 (the two-pipeline model: operators one cut behind engineers).
- S-track consumes CL8's induction harness and the sealed-budget ablation conjunct.
- I-track consumes the seal mechanism for the next exam.
- **Researcher-v1** becomes possible behind CL6: admitted, session-scoped, independently checked, revocable. Still inert with respect to durable promotion, which stays human-gated.

---

## §9 The one-line answer, restated

> **ODR-6 does not sit beside the five dimensions. It becomes the mechanism that produces the next frozen cut the dimensions run on. The pyground supplies the checker discipline and merges as 29 additive files. The overnight researcher supplies the inventory method and is the reason CL6 matters — it is inert today because there is no gate, and CL6 builds the gate. And none of them adds a task to the day; they add constraints and consumers only.**

The precondition is §0: this plan is currently aimed at a base that lacks `wire.py`, the vocabulary layer, and the programme. Re-base first, re-measure second, dispatch third. Everything else in this document is worthless until that happens.
