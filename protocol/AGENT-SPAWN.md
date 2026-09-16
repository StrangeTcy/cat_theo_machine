# Arena spawn pack

Two programmes. Do not mix them in one agent.

```text
PROGRAMME L  — five-track launch (INT, S/E/G/F-tools, operators)
PROGRAMME C  — [SHARED] process-based hypergraph workers (A, B, C, INT)
```

L is the charter tracks. C is one runtime feature: parallel exploration,
checked results, serial promotion. C does not restart L.

Standing constraints (every agent, every line):

```text
No core.py edits. No isinstance, hasattr, type, __class__, __new__,
getattr, callable as machine-type tests. No Python lists, dicts, or
booleans as machine values. No helper functions, module globals,
monkeypatching, dataclass, typing checks, .results[0], is_var fields,
named Var fields. No LLM, embeddings, statistical parsing, or host
string templates for machine utterances. Every failure is a machine
term. Every “passed” cites a dated artifact. Record remote tip before
work. Never force-push. Push every green step. Do not run Python in
conda without asking. Do not run Experiment 4. Do not explain FLT.
Banned phrases: “If you want”, “matters”, “but wait”, “actually”,
“honest”, “Let me”.
```

Current engineering base (this tip): `eng-base-0` / `1374464`.
F-op still gated by `protocol/F.md`. Measurement tag: none.

---

# PROGRAMME L — launch (summary)

Full texts: `protocol/CHARTER-v1.md`, `CHARTER-v2.md`, `TWO-PIPELINE.md`.

```text
Wave 0  INT only. Wait for preflight complete + base tag.
Wave 1  S-eng E-eng G-eng F-tools-eng at once from that tag.
Wave 1b operators on the frozen tag, one cut behind.
Batch   Text #8 into INT. Never merge engineer with operator.
F-op    human only.
```

Engineers: `work/<T>/<tag>/r1`, marked blocks only, one phase per turn.
INT: exact SHAs, SHARED→S→E→G→F, suite vs baseline, tag or return.

---

# PROGRAMME C — process workers (this is the implementation pack)

## Ground truth

```text
EXISTS:  PlannerAlternative — fork as data
EXISTS:  content-addressed checkpoints — read isolation
EXISTS:  rent gate + provenance + mask on adoptions only
PARTIAL: compare_search_modes (resident pool, root wave, worker snapshot
         dirs) — inspect before replacing
MISSING: per-worker write journal (write isolation)
SAFE:    spawn + cold checkpoint + discard writes
GAP:     spawn + KEEP writes
DEFER:   joint-set rent; unlimited spawn; shared mutable hypergraphs
```

## Three rules

```text
WORKER     = OS process + immutable snapshot + one obligation + budget
             + local journal. Never writes parent knowledge/adoption.
JOURNAL    = OBSERVATIONS (append, inert archive) vs PROPOSALS (queue).
COORDINATOR= validate certificates, AND/OR join, serial admission through
             existing gates. Success report is not a proof.
```

## Proposed terms (agree if missing; reuse if present)

```text
WorkItem(id, parent, snapshot_id, obligation, context, budget)
Claim(task_id, attempt_id, worker_id)
WorkerResult(task_id, attempt_id, snapshot_id,
             outcome, certificate, journal, counters)
```

Control terms stay out of the theorem fact store.

## Common block — paste into A, B, C

```text
You implement PROGRAMME C, not track S/E/G/F features.
Follow charter §0 (standing constraints above).
Record exact base SHA. Own checkout. Push only your authorized branch.
Never force-push. Do not cut tags.

Inspect before replacing:
  compare_search_modes, PlannerAlternative, snapshot codec,
  learned-memory masks, proof checker, adoption/rent gate.

Names in this brief are proposed interfaces, not claims of existing code.
No theorem packs, no new mathematics, no LLM scheduling, no Experiment 4.

Deliver code + focused tests + dated artifacts.
End every turn:
  agent / branch / base / pushed commit
  implemented interfaces
  tests + dated artifacts
  failures with loci
  ready for integration
  next bounded item
```

---

## Text C-A — Worker runtime

```text
You are Agent A (worker runtime). Programme C. Base: <PASTE TAG@SHA>.
Branch work/C-A/<tag>/r1.

[paste common block]

1. Reproduce and inspect:
     compare_search_modes_finds_reusable_worker_snapshot_dir
     compare_search_modes_fill_warms_resident_pool_before_root_wave_test
   Record failing assertion and executed path. Diagnosis does not close
   a test. Do not infer cause from names.

2. Reuse the existing pool where compatible. Report required replacement
   to INT before replacing it.

3. Bounded execution:
   max_workers=2; explicit start method; isolated worker directories;
   snapshot identity checked before work; readiness ack before dispatch;
   task/attempt ids on every message; budgets, timeouts, cancellation,
   cleanup.

4. Crashes and timeouts become machine execution-failure terms.
   Neither means the obligation is false.

Deliver: two concurrent workers returning serialized results; crash/retry
and cleanup tests.
```

## Text C-B — Snapshot and journal

```text
You are Agent B (snapshot + journal). Programme C. Base: <PASTE TAG@SHA>.
Branch work/C-B/<tag>/r1.

[paste common block]

Publish the small interface first so A and C can build against fixtures.

1. Verify snapshot coverage and fresh-process restore equivalence.
   A hash alone does not prove restore or isolation.

2. Private journal per worker bound to snapshot, task, attempt,
   assumptions, enabled-memory profile, budget.

3. OBSERVATIONS: traces, attempts, residuals, counterfactuals.
   PROPOSALS: candidate laws and policies.

4. Validate and deduplicate observations into an inert evidence archive.
   Do not merge them into stores consumed by search or learning.
   Later mining is explicit and provenance-recorded.

5. Proposals remain inactive. No journal import installs a rule or
   policy. Reject malformed, truncated, or misattributed journals.

Deliver: round-trip, tamper, scope-isolation, duplicate-import tests.
```

## Text C-C — Join and serial admission

```text
You are Agent C (join + admission). Programme C. Base: <PASTE TAG@SHA>.
Branch work/C-C/<tag>/r1.

[paste common block]

1. claim → running → completed/failed/cancelled.
   Retry uses a new attempt id. Duplicate delivery has no duplicate
   effect. Late results from superseded attempts cannot overwrite
   accepted state.

2. Replay each certificate against its declared snapshot and obligation
   before accepting it.

3. AND: every required child discharged. OR: one complete alternative
   discharged. Never combine incompatible sibling assumptions.

4. Proposal admission only after checked fork/join works:
   recorded stable queue; revalidate against current accepted state;
   existing validity, held-out rent, human approval;
   publish updated state before the next candidate.
   Rent is a performance test, not a soundness proof.
   No private activation path. No joint-set rent in this version.

Deliver: checked joins, stale-result rejection, serial-admission tests.
```

## Text C-INT — integrate Programme C

```text
You are INT for Programme C only this batch. Pin base and file ownership.
A/B/C concurrent; each shared file has one named owner.

On the composed candidate require:
- two worker processes overlap in wall time
- parent snapshot unchanged by worker execution
- results replay; AND/OR joins respect assumptions
- crash, retry, cancel, duplicate delivery preserve accounting
- evidence import leaves active rules, policies, search inputs unchanged
- worker proposals cannot bypass approval
- admitted laws keep provenance and disable/reset/restore
- ablation preserves independent siblings; dependents tracked
- wall time AND aggregate work recorded
- both suite shards complete; failures vs pinned baseline

Then cut an immutable tag under existing admission. Classify SEMANTIC
or NON-SEMANTIC.

Deferred: unlimited spawn, distributed hosts, shared mutable graphs,
automatic policy activation, joint-batch admission.
```

## Working order

```text
inspect and reuse → isolated workers → checked fork/join → serial promotion
```

## Kill conditions

```text
Adoption-class entry reaches the store without the gate → defect, void.
Suite failure set grows at merge → no tag.
E1 fail (Programme L) → E stops; no patch-to-pass.
Decoy residuals identical (F-op) → reading withdrawn.
```
