# CHARTER-v1 (transcribed)

Provenance: supplied verbatim by the operator in the session opening
(2026-09-04, "fable 5.1: Unified Arena-Agent Charter: Three Tracks, One
Instrument"). Transcribed unchanged; the operating program on this branch
has run under it since. CHARTER-v2 and TWO-PIPELINE.md are NOT committed:
v2 was never supplied; TWO-PIPELINE arrived truncated (mid Text #3) on
2026-09-05 and an incomplete charter text will not be committed. Both are
blocked on the operator (see protocol/research_protocol.md).

---

## 0. Standing constraints (apply to every track)

- No `core.py` edits. No `isinstance`, `hasattr`, `type`, `__class__`,
  `__new__`, `getattr`, `callable`. No Python lists, dicts, or booleans as
  machine values. No helper functions, module globals, monkeypatching,
  `dataclass`, typing checks, `.results[0]`, `is_var` fields, named `Var`
  fields.
- No LLM, embeddings, statistical parsing, or host string templates for
  machine utterances.
- Every failure is a machine term. Every claim of "passed" cites a dated
  artifact.
- Record remote tip before work; never force-push; new tag per code change
  on the frozen line.
- Do not run Python in conda without asking. Do not run Experiment 4. Do
  not explain FLT.
- Banned phrases in prose and commits: "If you want", "matters", "but
  wait", "actually", "honest", "Let me".

## 1. Pre-flight
1. Surface the swallowed exception in LearnedMemoryCheckpointTest; ledger
   the true mechanism as a named defect; fix real defects in a separate
   commit and re-cut the tag.
2. Verify the A1 producer/consumer pair compiles and is selectable on the
   toy goal (x + 1 = x). Parsing is not evidence; selection is.
3. Verify the negative-control decoy is shape-matched to the FLT goal.
4. Full two-shard suite; record the failure set; commit `preflight`.

## 2. Track isolation
| Track | Touches | Must not touch |
|---|---|---|
| S | research.py mining/schema, provenance.py, testsuite.py | main.py dispatch, packs, explanation |
| E | explanation.py, render laws, testsuite.py | mining, residual compiler, packs |
| F | checkpoint tooling, grading script, protocol doc | generators, theorem packs, parser branches |

One commit per track per turn, labeled [S]/[E]/[F]. Induced laws are
INVENTED_LEMMA, never LIBRARY_THEOREM. E never touches an FLT-shaped goal.

## 3-5. Track definitions (S1-S5 contracts/schemas/instantiation/tests/
transfer; E1-E5 held-out/dependency/audience/second idea/feed; F1-F4
checkpoints/grading/decoy/audit) — full text as supplied; see operator
transcript or verification/strack_translation_2026-09-05.md for the
lineage translation actually in force.

## 6. Interleaving: F audit -> S phase -> E phase -> F tooling -> full
suite; commit per track; re-cut tag on code change.

## 7. Report format: remote tip before/after, tag, preflight status,
phase/test/suite per track, defects found by running, not built
(deliberate), blocked on operator.

## 8. Freeze: any code commit re-cuts the tag; sessions log their tag; a
session spanning two tags is inadmissible; rent/ablation/reset/re-mine/
provenance/human gating shared by all tracks; no private promotion path.
