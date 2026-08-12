# 10 August 2026 — Updated Plan by Sol

## Purpose

This plan updates `Q:\20May2026 -- plan from codex.md` against the repository now present in `Q:\hyge`.

The earlier nine-stage direction remains broadly sound, but its status labels are too optimistic for the current evidence. The repository has made real progress in resident packet execution, stale-result handling, persistence coverage, structural arithmetic rules, and planner orchestration. It does not yet have a trustworthy end-to-end runtime baseline, a valid current snapshot, first-class graph task ingestion, a graph curriculum, automatic induction, robustness packs, a surface-language bridge, or distributed self-improvement.

The revised order therefore keeps the nine-stage destination but inserts strict gates between implementation, focused tests, and end-to-end behavioral proof.

## Non-negotiable engineering constraints

All work under this plan must obey these constraints:

- Do not edit `core.py`.
- Do not use `isinstance`, `hasattr`, `type`, `__class__`, or `__new__` in new or revised code.
- Do not introduce Python lists, Python dictionaries, or Python boolean values into the machine/runtime design.
- Do not add helper functions or module globals.
- Do not monkeypatch.
- Use explicit machine-native terms, edges, identities, and constructor paths.
- Keep compatibility code outside the active runtime path.
- Do not replace parallel root-wave search with a serial fallback.
- Do not use repository-status or repository-diff commands as a substitute for reading and testing the code.
- Run runtime verification only from the already-open project Anaconda Prompt. Do not discover interpreters, resolve shortcuts, or run activation-discovery logic.

Existing violations are technical debt to remove from touched active paths, not patterns to copy. Current examples include dynamic class inspection in `prettyprinting.py`, class allocation in `persistence.py`, and host-type parsing in `packs.py`.

## Evidence standard used by this update

A capability receives one of four labels:

- **Behaviorally demonstrated** — a current log or completed validation artifact shows the behavior executing.
- **Implemented with focused coverage** — source and focused tests exist, but no current complete run proves the full path.
- **Partial foundation** — reusable pieces exist, but the stage contract is not satisfied.
- **Not implemented** — the repository does not contain the stage's defining behavior.

Test registration is not treated as a passing test result. Source presence is not treated as runtime completion.

## Current status against the 20 May plan

| Original stage | Updated status | Current evidence | Remaining gate |
|---|---|---|---|
| 1. Reliable runtime | **Implemented with focused coverage; partial behavioral demonstration** | Resident root-wave shards and shared candidates execute in `logs/cold_debug_stage1_runtime_long.log:300-393`. Packet results advance and stale results are requeued in `logs/cold_debug_stage1_runtime.log:471-619`. Focused packet tests are registered in `testsuite.py:4361-4527`. | Produce a clean, bounded comparison run that reaches a terminal outcome; prove pause, resume, selective stop, stale rejection, backlog refill, and completion accounting in one current run set. |
| 2. Persistence | **Partial and blocking** | `nat_value_index` is captured in `persistence.py:1009-1026`; paused search/comparison and generic edge tests exist in `testsuite.py:2006-2219`. | The writer still omits non-singleton character symbols at `persistence.py:967-970`; restore constructs objects through `__new__` at `persistence.py:1067`; concrete edge subclasses are restored as base `Edge`; `snapshots/` contains only a v4 backup and `hyge_snapshot_v9.json.bad`. |
| 3. Mathematical and structural ontology | **Partial** | Direct progression structure and anti-notation-fact tests are registered in `testsuite.py:4530-4541`; order/sign and square-root packs exist. | Active geometry rules still use `EvaluateProblemLabel` and `AlgebraicApproachLabel` in `packs/geometry.pack.yaml:619-646,1130`. Legacy availability labels and rendering branches remain in `labels.py` and `prettyprinting.py`. |
| 4. First-class graph input | **Partial foundation** | `Hypergraph`, `add_node`, and `add_edge` exist in `graph.py:9-135`. `planner.py` adds machine-native problems, obligations, dependencies, and child search jobs. `runtime.py:95-104` exposes planner evaluation. | There is no explicit canonical graph-task ingestion contract, no demonstrated equivalence normalization across alternate graph encodings, and no end-to-end partial graph query suite with returned bindings. Planner variants and transfer records from the earlier specification are absent. |
| 5. Graph curriculum | **Not implemented** | Mathematical packs and planner validation scripts exist. | They are not the requested retrieval/join/binding/two-hop/identity/negation curriculum, and there is no rung-level outcome and trace tracker. |
| 6. Induction, compression, strategy, and policy | **Partial foundation** | Manual derivation-schema storage and lookup exist in `schemata.py` and `graph.py:168-180`. Search modes and heuristics exist. | No automatic motif detector, schema candidate builder, held-out evaluator, or safe search-policy promotion loop is present. |
| 7. Robustness before language | **Not implemented** | General rewrite machinery can support the work. | No controlled missing-edge, duplicate, distractor, alias, or alternate-encoding task suite was found. |
| 8. Surface-language bridge | **Not implemented** | `prettyprinting.py` renders machine terms. | Rendering is not a reversible language/graph mapping. No paired graph/language packs or equivalence tests exist. |
| 9. Promotion, reuse, and distributed improvement | **Partial foundation** | Packet descriptors, resident executors, tokens, generations, and machine-encoded comparison state create a plausible distribution boundary. Proof construction remains separate from scheduling. | No multi-machine transport, durable promotion ledger, proof-promotion policy, search-policy evaluator, rollback path, or closed improvement cycle exists. |

## What is already working and must be preserved

### Resident comparison architecture

- Root candidate work is executed through resident executors.
- Shared root candidates are computed once and reused by fixed modes.
- Root waves are split into theorem branches plus a rewrite handoff.
- Packet results can return further ready work.
- Unavailable or rejected results return work to the queue rather than silently consuming it.
- Packet tokens and generations provide stale-result discipline.
- Success and stop paths have focused coverage for clearing packet state.

The long runtime log demonstrates 68 resident root shards merging into seven shared candidates in 22.42 seconds, followed by four ready branches per fixed mode. This is a large improvement over the earlier repeated multi-minute root applicability scans.

### Search and persistence model coverage

The test suite contains focused cases for:

- grouped comparison jobs, worker baselines, and worker packets;
- worker launch and result serialization;
- paused search snapshot round trips;
- paused comparison snapshot round trips and resume;
- `nat_value_index` round trips;
- machine edge input/result preservation;
- pause backlog preservation and active-packet reclamation;
- stale, missing-token, and missing-payload retries;
- returned packet-count normalization;
- theorem generated-tree progression and rewrite handoff;
- resident baseline refresh;
- batched-wave equivalence with sequential success.

These tests define the intended invariants and should be retained as the minimum regression corpus.

### Planner foundation

`planner.py` is a significant addition not reflected in the 20 May status:

- `PlannerProblem` represents the mathematical state, root goal, rules, and heuristic.
- `PlannerObligation` tracks a single proof obligation and selected rule/bindings.
- `PlannerDependency` links parent and child obligations.
- `PlannerJob` binds an obligation to one ordinary `SearchJob`.
- `PlannerStep` performs backward decomposition, schedules runnable obligations, executes search bursts, records derivations, propagates child failure, and updates the problem state.
- `PlannerRun` advances until the root is proved, failed, or no progress is possible.

Four validation scripts exercise minimal planning, variable conclusions, pack-loaded rules, cycle control, failure propagation, and the supported runtime entry point. Their source assertions are useful evidence, but current run-result artifacts are still required.

## Revised execution plan

## Gate A — Establish a trustworthy runtime baseline

**Priority:** Immediate  
**Blocks:** Every later gate

### Work

1. Run the focused Stage 1 and Stage 2 regression corpus from the project Anaconda Prompt and retain a dated result artifact.
2. Run the planner validation scripts and retain their terminal markers.
3. Run a bounded `cold debug` comparison through a terminal comparison outcome rather than stopping after root-wave creation or early packet integration.
4. Exercise the console control matrix during real packet activity:
   - pause and resume;
   - stop one mode;
   - restrict execution to selected modes;
   - stop the whole comparison;
   - interrupt without losing the pending wave.
5. Re-run a paused comparison from its saved state and confirm the same token generation, pending packet shape, frontier state, and eventual result.
6. Record per-mode terminal status, expanded count, generated count, frontier peak, completed packet count, elapsed time, and selected attempt.
7. Separate expected stale rejection from accidental token equality in log text. A line that prints identical displayed values while claiming staleness is not interpretable evidence.
8. Add a bounded memory observation for resident executors across multiple waves. The acceptance criterion is stabilization, not unlimited growth.

### Acceptance

- Every focused invariant test reports a pass in a current artifact.
- Planner validation reports its expected completion markers.
- At least one nontrivial comparison reaches a terminal result without orphaned workers or queued packets.
- Pause/resume and selective stop are demonstrated during active execution.
- Returned-ready counts equal packet-chain shape throughout the run.
- Stale or missing payloads preserve the original work item exactly once.
- Completion logs are sufficient to reconstruct the final state of every mode.
- Resident memory remains bounded across repeated packet waves.

### Explicit non-goals

- No `main.py` redesign during this gate.
- No broad module split before behavior is captured.
- No serial root-wave fallback.

## Gate B — Repair persistence without forbidden construction paths

**Priority:** Immediate after Gate A's focused baseline  
**Blocks:** Cold resume, planner persistence, curriculum traces, promotion, distribution

### Work

1. Replace the generic snapshot record with explicit machine-native shape records for:
   - atom;
   - character atom with symbol and value;
   - pair;
   - concrete edge construction identity, inputs, results, and referenced children.
2. Remove `__new__` from restore. Restoration must use declared constructors or an explicit constructor registry/factory represented through normal callable paths.
3. Preserve concrete edge meaning rather than restoring every edge as base `Edge`.
4. Add direct round trips for:
   - arbitrary non-singleton character atoms;
   - variables loaded from packs;
   - representative rule, multi-rule, search state, worker packet, planner record, and derivation edges;
   - shared child identity;
   - `nat_value_index`;
   - paused comparison tokens, generations, pending order, and counts.
5. Capture planner state as an explicit root or establish a documented rule that planner state is stored through an existing captured root.
6. Generate a fresh current snapshot only after all focused persistence cases pass.
7. Resume the fresh snapshot through the real cold-resume path and complete useful work.
8. Keep legacy migration isolated from the normal current-format path.

### Acceptance

- Character symbols survive save/load exactly.
- Every selected concrete edge reconstructs with the intended machine identity and behavior.
- No restore path uses `__new__`, dynamic class inspection, monkeypatching, or edits to `core.py`.
- A fresh current snapshot exists and is loadable.
- Paused search, paused comparison, and planner state resume without queue, token, or identity drift.
- The `.bad` snapshot is retained as a diagnostic artifact until its failure is explained.

## Gate C — Finish runtime semantics and observability

**Priority:** High  
**Blocks:** Performance claims and distributed execution

### Work

1. Compare packet expansion directly with sequential `_SearchStepKernel` behavior for theorem progression, rewrite handoff, step budget, visited state, generated tree, and frontier ordering.
2. Audit integration, batching, refill, wave transitions, executor release, terminal cleanup, and stopped-mode rejection as one state machine.
3. Replace misleading progress fields with values derived from machine state.
4. Define terminal invariants for each mode:
   - no active packet;
   - no unexplained pending packet;
   - terminal search status;
   - one stable attempt or explicit failure/stop reason.
5. Reduce inner-loop debug output while retaining packet lifecycle events and invariant violations.
6. Profile the remaining per-packet applicability and rule-ordering costs after correctness is locked.
7. Address recursive hot paths that still cause `RecursionError`, beginning with paths demonstrated by current logs.

### Acceptance

- Batched and sequential execution return equivalent terminal search results across all fixed modes on a small deterministic matrix.
- Progress counters remain monotonic and explainable.
- No active worker survives terminal comparison cleanup.
- Performance work changes elapsed cost without changing proof/search results.

## Gate D — Complete structural ontology and planner contracts

**Priority:** High after persistence  
**Blocks:** First-class graph tasks and curriculum

### Work

1. Remove active Tao dependencies on strategy-facts such as `EvaluateProblem` and `AlgebraicApproach`.
2. Keep arithmetic progression, common difference, side assignment, sign, order, and square-root reality as direct mathematical relations.
3. Remove active availability-fact rules. Compatibility labels may remain loadable only when they are outside current derivations.
4. Remove dynamic class-name dispatch from active pretty-printing. Use explicit machine labels and constructor registration.
5. Add planner records and transitions for problem variants and proof-bearing transfer validation, or formally defer them from the supported planner contract.
6. Define exact aggregate completion goals rather than treating a strategy wrapper as mathematical success.
7. Add planner persistence coverage and planner derivation replay checks.
8. Replace standalone validation scripts with tests integrated into the normal regression entry point while retaining the scripts as focused probes only when useful.

### Acceptance

- Active Tao derivations contain mathematical obligations and conclusions, not strategy availability facts.
- Pretty-printing round trips the supported ontology without class inspection.
- Planner decomposition never creates an obligation cycle.
- Parent completion requires every declared child dependency to be proved and the parent rule to be validated.
- Variant transfer cannot promote a result without a proof-bearing transfer rule.

## Gate E — Make graph tasks first-class

**Priority:** High after Gates B and D  
**Blocks:** Curriculum, robustness, language

### Work

1. Define one canonical task record containing:
   - graph facts;
   - query pattern;
   - expected bindings or expected failure;
   - permitted rule/rewrite bundle;
   - trace and outcome identifiers.
2. Define canonical graph ingestion entirely through machine-native records and edges.
3. Normalize equivalent graph encodings through declared rewrites.
4. Implement query success as partial structural matching with explicit binding output.
5. Keep planner orchestration above ordinary single-goal `SearchJob` execution.
6. Add graph-task persistence, resume, and trace capture.
7. Build a conformance suite showing that equivalent input encodings produce equivalent normalized forms, bindings, and proof traces.

### Acceptance

- A graph task can be loaded, normalized, queried, paused, saved, restored, resumed, and completed.
- Equivalent encodings yield equivalent result bindings.
- Returned bindings are machine terms and remain proof-traceable.
- No graph task is solved by a host-language special case.

## Gate F — Build the graph curriculum and robustness suite

**Priority:** Medium after Gate E

### Curriculum rungs

1. Single-edge retrieval.
2. Two-edge join.
3. Variable binding and repeated-variable constraint.
4. Two-hop derivation.
5. Identity and alias normalization.
6. Explicit negative/failure result.
7. Planner decomposition across dependent queries.

### Robustness variants for every applicable rung

- missing edge;
- duplicate edge;
- irrelevant distractor;
- alternate edge order;
- alias;
- equivalent encoding;
- contradictory input with an interpretable failure.

### Instrumentation

For every task, retain:

- task and rung identity;
- normalized input;
- result bindings or failure class;
- proof/search trace;
- expanded/generated/peak counts;
- selected mode;
- promoted schema or policy involvement.

### Acceptance

- Every rung has deterministic pass/fail reporting.
- Higher rungs declare their lower-rung dependencies.
- Controlled noise does not change valid results except where the corruption removes required information or introduces a declared contradiction.
- Failures identify the missing, conflicting, or unmatched structural requirement.

## Gate G — Add induction and safe promotion

**Priority:** Medium after a stable curriculum corpus  
**Blocks:** Self-improvement claims

### Work

1. Detect repeated successful trace fragments using structural keys.
2. Generalize constants into roles only when repeated traces support the same binding pattern.
3. Store candidates separately from trusted derivation schemata.
4. Validate candidates against:
   - source tasks;
   - held-out structurally similar tasks;
   - adversarial near-miss tasks;
   - proof replay through the independent checker.
5. Promote proof schemata and search-policy hints through separate ledgers and thresholds.
6. Record provenance, supporting tasks, rejected counterexamples, version, and rollback state.
7. Measure both proof correctness and search cost before and after policy promotion.

### Acceptance

- Repeated traces produce a candidate schema automatically.
- A candidate cannot become trusted without independent proof replay.
- Held-out success improves without regression on the established corpus.
- Search-policy promotion cannot alter proof validity.
- Every promotion is reversible and attributable to evidence.

## Gate H — Bridge graph invariants to surface language

**Priority:** Later, after Gates E–G

### Work

1. Create paired surface/graph records for curriculum tasks.
2. Represent parsing and rendering correspondences as explicit machine relations.
3. Normalize paraphrases to shared graph invariants.
4. Solve only in graph space.
5. Render answers and derivation summaries back through declared correspondences.
6. Add round-trip, paraphrase-equivalence, ambiguity, and unsupported-form tests.

### Acceptance

- Supported surface inputs map to the expected graph task record.
- Paraphrases share the same normalized graph interpretation.
- Graph results render faithfully with preserved bindings.
- Ambiguity produces explicit alternatives or failure rather than a hidden guess.
- There is no opaque parallel language solver.

## Gate I — Prepare distribution and close the improvement loop

**Priority:** Last

### Work

1. Freeze the worker protocol around machine-encoded baseline, packet, token, generation, result, and trace records.
2. Make every packet idempotent and independently replayable.
3. Separate transport from scheduler semantics.
4. Add durable lease, retry, timeout, stale-result, and duplicate-result rules.
5. Test state transfer across independent processes before attempting multiple machines.
6. Distribute curriculum and held-out evaluation only after local replay is deterministic.
7. Feed validated traces into the candidate-promotion ledger from Gate G.
8. Retain the proof checker as the final trust boundary.

### Acceptance

- Duplicate delivery does not duplicate semantic work or corrupt counters.
- Stale and late results are rejected without losing live work.
- A packet can move between isolated runtimes and produce an equivalent result.
- Local and transported execution agree on proof result, bindings, counters, and terminal state.
- Distributed evaluation can propose candidates but cannot bypass proof validation or promotion policy.

## Revised priority order

1. **Gate A:** obtain a current behavioral baseline.
2. **Gate B:** repair persistence and create a valid resumable snapshot.
3. **Gate C:** finish runtime state-machine equivalence, cleanup, and observability.
4. **Gate D:** finish ontology cleanup and planner contracts.
5. **Gate E:** define and prove first-class graph task ingestion/query behavior.
6. **Gate F:** build the curriculum and robustness matrix.
7. **Gate G:** implement induction and separated promotion.
8. **Gate H:** add reversible surface language.
9. **Gate I:** distribute deterministic packets and evaluation.

Gates A–D are the active program. Gates E–I should remain design-constrained but should not consume implementation effort until persistence and terminal runtime behavior are trustworthy.

## Immediate work package

The next bounded package should contain only these outcomes:

1. A dated focused-test result artifact for packet, persistence, and planner invariants.
2. A terminal `cold debug` comparison artifact showing final per-mode state.
3. A persistence design that restores characters and concrete edges without `__new__` or class inspection.
4. Focused character, concrete-edge, planner-state, and paused-comparison round trips.
5. A fresh loadable current snapshot and one demonstrated resume.
6. A short discrepancy record for any focused test whose source exists but whose runtime result fails.

Do not begin curriculum, induction, language, or multi-machine work inside this package.

## Definition of program completion

The program reaches the original nine-stage destination only when:

- runtime comparison is terminally reliable under real packet load;
- persistence exactly preserves current machine and planner state;
- active ontology paths are mathematical rather than strategy-fact simulations;
- graph tasks have canonical ingestion, normalization, query bindings, traces, and resume;
- the curriculum and robustness matrix pass deterministically;
- induction produces evidence-backed reusable candidates;
- proof and search-policy promotion remain separate;
- surface language is a reversible view over graph invariants;
- transported packet execution is equivalent to local execution;
- every promoted proof structure remains independently checkable.

Until then, the repository should be described as a substantial symbolic reasoning research prototype with a working resident packet architecture and a functional planner foundation, not as a completed self-improving graph-language system.
