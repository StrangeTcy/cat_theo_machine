# Process-Based Agent Behaviour in the Hypergraph — Verified Build Plan

Base commit: `428ecdc` ("Add files via upload"), branch `arena/01a0a820-cat-theo-machine`.
Every fact below was produced by a command run against this checkout. Loci are `file:line`.

---

## 0. Corrections to the prior plans

Six claims in the preceding launch charters do not survive contact with this tree. They are
listed first because three of them would have sent agents to work that does not exist.

| # | Claim in prior plans | Verified status |
|---|---|---|
| 1 | `protocol/CHARTER-v1.md`, `protocol/CHARTER-v2.md`, `protocol/TWO-PIPELINE.md` exist; commit `d3de45a` | **False.** No `protocol/` directory. `git log` has one commit: `428ecdc`. |
| 2 | "Two-shard suite, ~25 min per shard" | **False.** `run_test_mode` (`main.py:1117-1132`) runs the whole suite in one process. Full suite measured **twice**: 90.65 s and 89.03 s. There is no shard split and no per-test filter. |
| 3 | Baseline failure set is the two `compare_search_modes` tests | **False.** Baseline is **four** tests (§1). |
| 4 | "S owns learned-policy induction", "learned-memory mask", "rent gate", `adopt_compressed_law`, provenance classes, `TrainingRecord`, `research.py`, `provenance.py`, `explanation.py`, `mining.py` | **Absent — 0 hits** for every one of these across `*.py` and `*.yaml`. `mining.py` exists only as `mining.py.txt`. The five-track charter (S/E/F/G/I) has no substrate here. |
| 5 | `save checkpoint <name>` / `load checkpoint <name>` are the checkpoint primitives | **False names.** The real primitives are `save_runtime(runtime, snapshot_path, namespace)` (`runtime.py:1790`), `boot_from_snapshot(snapshot_path, namespace, debug)` (`runtime.py:1708`), `SnapshotCodec` (`persistence.py:420`), and `_search_worker_checkpoint(...)` (`main.py:703`). |
| 6 | `PlannerAlternative(parent, method, children, status, evidence)` is a proposed interface to be checked | **Exists, with a longer signature** (`planner.py:413`). See §2. |

Consequence: **the five-track programme is not runnable at this commit.** Only the
process-concurrency work has real machinery under it. That is what this plan assigns.

---

## 1. Verified baseline (run it yourself before touching anything)

Reproduce, from `/home/user`:

```bash
python -m venv .venv
.venv/bin/pip install gmpy2 pyyaml          # the only two third-party deps
.venv/bin/python -m cat_theo_machine.main test
```

Without `gmpy2` the import chain dies at `gmprep.py:3`. Without `pyyaml` it dies at
`packs.py:334`. `environment.yml` targets conda `python=3.12` on a Windows prefix; this
sandbox is Python 3.11 on Linux.

Cold boot loads 12 packs: `rule_count: 159`, `schema_count: 4`, `example_count: 27`.
194 `_register_test(` call sites in `testsuite.py`.

**Baseline failure set — four tests, identical across two consecutive full runs:**

```text
heuristic_canonical_knowledge_agreement_test
compare_search_modes_finds_reusable_worker_snapshot_dir_test
tree_insert_deep_pair_lookup_avoids_recursion_test
compare_search_modes_fill_warms_resident_pool_before_root_wave_test
```

All four return `false_value`. None raise. Confirmed by instantiating the real test classes
directly against a packed runtime — no exception, `result: FALSE` for each.

**Platform divergence — measured, not assumed.** `environment.yml` records a Windows conda
prefix (`prefix: C:\Users\hatgu\anaconda3\envs\hyge`, `python=3.12.13`); this sandbox is Python
3.11 / Linux and `multiprocessing.get_start_method()` returns `fork`, `cpu_count()` returns 2.

The grep the plan would otherwise have assigned to an agent is already done. Every process-
creation site in the tree, and the context each one uses:

```text
search/compare_executors.py:271   mp_context.Process(...)   context from compare.py:201/251 = "spawn"
search/engine.py:702              mp_context.Process(...)   context from engine.py:654/656
persistence.py:565                ctx.Process(...)          ctx = get_context("spawn")  persistence.py:562
persistence.py:658                ctx.Process(...)          ctx = get_context("spawn")  persistence.py:647
search/compare_subprocess.py:268  subprocess.Popen(...)     per-mode search-worker child
search/compare_subprocess.py:462  subprocess.Popen(...)     per-mode search-worker child
main.py:24                        subprocess.run(...)       module re-exec wrapper
main.py:1308                      multiprocessing.freeze_support()
search/ui.py:131                  queue.Queue               threading queue, not mp
```

**No un-contexted `Process()` or `Pool()` call exists.** There are no `multiprocessing.Pool`
uses at all, and no `set_start_method` anywhere. So the divergence risk is not un-pinned
spawns. It is one pinned site that behaves differently per platform — see §2.1.

---

## 2. What concurrency machinery exists (this is more than the prior plans assumed)

The machine already runs real OS worker processes end to end.

```text
spawn          search/compare_executors.py:265-287
                 mp_context.Process(target=_SearchModeWorkerExecutor,
                                    args=(slot_text, task_queue, result_queue))
                 process.start()
ready handshake  _await_parallel_executor_ready, compare_executors.py:293
                 raises "resident executor did not acknowledge startup" on failure
worker entry   main.py:1290  mode "search-worker"
                 run_search_worker_mode(worker_mode, result_path, timeout_seconds)  main.py:749
term vocabulary  ~80 SearchWorker* classes in search/model.py:
                 SearchWorkerSetup, SearchWorkerPacket, SearchWorkerLaunch,
                 SearchWorkerPayload, SearchWorkerResult, SearchWorkerMetrics, ...
worker pickling  search/serialization.py:328 _install_search_worker_pickle_support()
snapshot I/O   runtime.py:1790 save_runtime / runtime.py:1708 boot_from_snapshot
                 persistence.py:420 SnapshotCodec
                 main.py:703 _search_worker_checkpoint (per-worker checkpoint)
                 _reusable_search_worker_result_paths (snapshot-dir reuse)
```

`SearchWorkerLaunch` real signature (`search/model.py:606`):

```python
SearchWorkerLaunch(mode, setup, payload, packet_state, launch_slot, launch_budget, branch_serial)
```

`PlannerAlternative` real signature (`planner.py:413`):

```python
class PlannerAlternative(M.Edge):
    def __init__(self, parent_obligation_id, method, child_obligation_ids, status, evidence)
```

It is an `M.Edge`, not a dataclass, and it is documented in-tree as "planner data … never
inserted into mathematical Knowledge" (`planner.py:414-420`). Accessors exist as separate
edges: `PlannerAlternativeParent/Method/Children/Status/Evidence` (`planner.py:449-494`).

**Do not invent `WorkItem` / `Claim` / `WorkerResult` terms.** `SearchWorkerPacket`,
`SearchWorkerLaunch`, and `SearchWorkerResult` already fill those roles. Extending the
existing vocabulary is the task; adding a parallel one is the defect.

### 2.1 Three worker mechanisms, and one platform-dependent code path

There are **three** distinct ways this tree spawns work, not one:

```text
(a) resident executors   multiprocessing, context "spawn"
                         compare_executors.py:265-287, ready handshake at :293
(b) applicability shards multiprocessing, context "fork" (or serial — see below)
                         engine.py:702, target _SearchApplicableRulesShardWorker
(c) per-mode workers     subprocess.Popen of `python -m <pkg>.main search-worker ...`
                         compare_subprocess.py:268 and :462, each with a
                         threading.Thread output relay at :278 and :472
```

Mechanism (c) was missing from the earlier inventory. It launches one child process per
search mode with `HYGE_SEARCH_WORKER_DEFER_DERIVATION=1` (`:461`) or
`HYGE_SEARCH_WORKER_RESUME_DERIVATION=1` (`:267`), collects `exit_code` at `:280`, and
reloads the snapshot via `_load_search_worker_snapshot` at `:283`. Any concurrency work that
claims to cover "the worker path" must say which of the three it means.

**The one pinned site whose behaviour differs by platform** is
`_theorem_applicable_rules_sharded` (`search/engine.py:646`):

```python
if multiprocessing.get_start_method() == "spawn":          # engine.py:649
    return FilterApplicableRulesWithIndex(...)              # engine.py:651  serial
try:
    mp_context = multiprocessing.get_context("fork")        # engine.py:654
except ValueError:
    mp_context = multiprocessing.get_context("spawn")       # engine.py:656
if mp_context.get_start_method() == "spawn":                # engine.py:657
    return FilterApplicableRulesWithIndex(...)              # engine.py:659  serial
```

Measured here: default start method `fork`; `get_start_method() == "spawn"` is `False`;
`get_context("fork")` succeeds and reports `fork`, so the `:657` guard does **not** trip.
`cpu_count()` is 2 and cold boot gives `rule_count: 159`, so `worker_capacity` computes to 2
and the parallel shard path at `:702` is the one taken.

On a Windows default (`spawn`) the function returns at `:651` and runs
`FilterApplicableRulesWithIndex` in-process instead. Two platforms, two different
implementations of rule-applicability filtering. A behavioural difference between them
presents as a nondeterministic test flake rather than as a platform difference, which is
exactly the failure mode to pre-empt. Any finding about mechanism (b) must state which branch
produced it.

---

## 3. Diagnosis of `compare_search_modes_fill_warms_resident_pool_before_root_wave_test`

Traced by instrumenting the real code path, not by reading names.

The flag the test asserts, `_comparison_shared_root_candidates_ready`, is written in exactly
one place: `search/compare_packets.py:1410`, inside `_comparison_cache_shared_root_candidates`
(`compare_packets.py:1393`). That function has exactly one caller:
`_comparison_apply_shared_root_wave` (`compare_packets.py:1455`), which is reached only from
`_comparison_prepare_shared_root_wave` (`compare_packets.py:1429`), whose five nested guards
(`compare_packets.py:1436-1440`) require, per state:

```text
status          == SearchRunningLabel
phase           == SearchPacketSearchPhaseLabel
active_packets  == 0
pending_packets == EmptyList
is_fresh_root_job == true
```

Measured against the test's own constructed states (5 states, from
`_WarmRootWaveCompareProbe`, `testsuite.py:1626`):

```text
state 0..4  status=SearchRunningLabel  is_fresh_root_job: T  needs_shared_root_wave: F
```

`_comparison_states_need_shared_root_wave` returns `false_value` for **every** state, so
`_comparison_prepare_shared_root_wave` returns early at `compare_packets.py:1430-1431`,
`_comparison_apply_shared_root_wave` never runs, and the flag stays `false_value`.

Two of the test's four assertions pass for the wrong reason, which is why this red is
informative rather than merely broken:

```text
A) spawned != 0             PASS   (but probe.spawned is M.Atom, testsuite.py:1636,
                                    so NatEq(spawned, Zero) is false even at count 0)
B) shared_root_cands ready  FAIL   <- the real failure
C) workers non-empty        PASS   (workers came from the budget-launch path at
                                    compare_executors.py:687-696, not from
                                    _grow_parallel_executor_pool, which only runs when
                                    need_shared_root_wave is true — compare_executors.py:662)
D) needs_shared_root_wave   PASS   (passes because nothing was consumed)
```

**Named defect:** the shared-root candidate prepass is only reachable once a state is already
in packet-search phase, but entering that phase is what the root wave produces. The test name
asserts "fill warms resident pool **before** root wave"; the code caches candidates **during**
the wave. That is an ordering gap in the warm-pool path, not a test bug.

The second red, `compare_search_modes_finds_reusable_worker_snapshot_dir_test`
(`testsuite.py:1331`), exercises `_search_worker_checkpoint` and
`_reusable_search_worker_result_paths` and fails on the `"SearchBFS" in found` /
path-equality check (`testsuite.py:1375-1378`). Its mechanism is **not yet traced** — that is
Agent A's first deliverable, and it must not be inferred from this one.

---

## 4. Agent briefs

Four agents. A, B, C run concurrently; INT serialises. One worktree each.

### Shared prelude — paste verbatim into every agent

```text
Environment, verified:
  python -m venv .venv && .venv/bin/pip install gmpy2 pyyaml
  .venv/bin/python -m cat_theo_machine.main test      # whole suite, ~90 s, from /home/user
There is no per-test filter: run_test_mode (main.py:1117) ignores its filter argument and
runs all 194 registered tests. Budget ~90 s per suite run. Do not write a private test
runner that reimplements test logic; instantiate the real test classes from
cat_theo_machine.testsuite against a runtime from boot_from_packs(main.PACK_PATHS,
main._runtime_namespace()).

Verified baseline, deterministic across two full runs — four failures:
  heuristic_canonical_knowledge_agreement_test
  compare_search_modes_finds_reusable_worker_snapshot_dir_test
  tree_insert_deep_pair_lookup_avoids_recursion_test
  compare_search_modes_fill_warms_resident_pool_before_root_wave_test

Standing constraints:
  No core.py edits. No isinstance/hasattr/type/__class__/__new__/getattr/callable in
  machine-facing code. No Python lists, dicts, or booleans as MACHINE values (host-side
  test scaffolding already uses them; match the surrounding style). No monkeypatching,
  dataclass, or typing checks in machine code. Every failure is a machine term. Every
  claim of "passed" cites a dated artifact.
  Never force-push. Push every green step. Engineers do not cut tags.
  Do not run the "search-worker" mode against a live problem without stating the timeout.
  Report the platform: this sandbox is Python 3.11 / Linux / start method "fork";
  environment.yml targets conda Python 3.12 / Windows. Say which one a finding came from.
  Do not claim a test is fixed unless the full suite failure set shrank by exactly that test.
  Housekeeping: a full suite run writes new untracked snapshots/search_compare/run-<epoch-ms>/
  directories. Remove only directories you created this turn. The 20 files committed under
  run-1786543184669 and run-1786548752373 are tracked fixtures — check `git status` before
  removing anything under snapshots/.

VOCABULARY SCOPE — the one hard line in this plan.
No agent may introduce rent, provenance, adoption, promotion, learned-memory, mask, or
schema vocabulary. Verified: none of it exists at this commit (§0, row 4 — 0 hits for
INVENTED_LEMMA, HUMAN_SUPPLIED_TRUSTED_THEOREM, adopt_compressed_law, LearnedMemoryCheckpoint,
RelationSchema, TrainingRecord). The absence is not an invitation. Building a rent-gate-shaped
or provenance-shaped thing under a new name, inside a concurrency fix, and calling it
infrastructure is the specific failure this plan exists to prevent. It requires its own
charter, its own review, and its own measurements, and it is out of scope for every brief
below. If your task seems to require it, stop and write the requirement down instead.
What you may add: worker execution-failure terms, journal terms, replay/claim/replay-state
terms, and tests. All of them are observations about work already done; none of them decide
what the machine is allowed to believe.
```

### Agent A — worker runtime diagnosis

```text
You are A-RUNTIME. Worktree of your own. Base: 428ecdc.

EVIDENCE STANDARD for every mechanism you name. A locus is three things, not one: the single
write site of the value in question, the full guard chain that reaches it, and the measured
state of that chain on the failing input. §3 of this document is the worked example for the
fill test. A plausible narrative without all three is not a diagnosis and will be returned.
This applies to Task 1 especially: do not inherit or invent a story about the second red.

Task 1 — trace the second red. compare_search_modes_finds_reusable_worker_snapshot_dir_test
(testsuite.py:1331) fails at testsuite.py:1375-1378. Determine whether
_reusable_search_worker_result_paths returns no "SearchBFS" key or a different path, then
produce the three-part locus for it. Note the test writes a deliberately mismatching manifest
at testsuite.py:1371-1372 and expects run-1 to be chosen over run-2; find out which half of
that expectation breaks. Do not fix it yet.

Task 2 — confirm the §3 diagnosis of the fill test independently, then state a minimal fix
proposal. The locus is the ordering between _grow_parallel_executor_pool
(compare_executors.py:662-668) and _comparison_cache_shared_root_candidates
(compare_packets.py:1393-1411). Do not widen any of the five guards at
compare_packets.py:1436-1440 without stating what else reaches that code.

WARNING — the green half of this test is also lying, and fixing only the failing assertion
is not a fix. Two of its four assertions pass for the wrong reason:
  A) "spawned != 0" passes because probe.spawned is an M.Atom (testsuite.py:1636), so
     NatEq(spawned, Zero) is false even when the count is zero. It proves nothing.
  C) "workers non-empty" passes because workers arrived via the budget-launch path
     (compare_executors.py:687-696), not via the pool-warming the test name claims.
     _grow_parallel_executor_pool only runs when need_shared_root_wave is true
     (compare_executors.py:662), which is false for all five states.
  D) "needs_shared_root_wave is false" passes because nothing was consumed, not because the
     wave completed.
Your fix must make the test's green assertions true for the reason the test name states.
Restate A, C and D as assertions that can fail, and say what each one now proves. If your
change leaves any of them vacuous, say so rather than reporting the test as fixed.

Task 3 — bounded execution hardening, and the platform check.
The un-pinned-spawn grep is already done; the inventory is in §1 and it is clean, so do not
redo it. There are three worker mechanisms (§2.1) — say which one each finding applies to.
  (a) resident executors, compare_executors.py:265-287: verify timeout, cancellation and
      cleanup of _retire_parallel_executor and _terminate_active_children (defined
      main.py:1232, called from the KeyboardInterrupt path at main.py:1303).
  (b) applicability shards, engine.py:702: this path is platform-dependent. State which
      branch produced your result — the parallel shard path past engine.py:657, or the serial
      FilterApplicableRulesWithIndex return at engine.py:651/659. On Linux with fork and
      cpu_count 2 the parallel branch is taken here; on a Windows spawn default it is not.
      If you cannot run both, say which one you ran.
  (c) per-mode subprocess workers, compare_subprocess.py:268 and :462: check exit-code
      handling at :280 and the relay-thread join at :281 for orphaned children on timeout.
      Note :281 joins with timeout=1.0 and does not act on a join that expires.
Convert any crash or timeout you find into a machine execution-failure term. A worker crash
is not evidence that the mathematical obligation is false.

Deliver: two traced mechanisms with three-part loci, a minimal fix for the fill test with A,
C and D restated, and a suite run whose failure set is the baseline minus the tests you fixed.
State the platform and, for mechanism (b), the branch.
```

### Agent B — snapshot and worker-state isolation

```text
You are B-SNAPSHOT. Worktree of your own. Base: 428ecdc.

Publish the real interfaces first, from the code, before writing anything:
  save_runtime / boot_from_snapshot (runtime.py:1790, 1708), SnapshotCodec
  (persistence.py:420, ROOT_NAMES at :421), _search_worker_checkpoint (main.py:703),
  _install_search_worker_pickle_support (search/serialization.py:328),
  sync_from_namespace (search/serialization.py:340).

Task 1 — restore equivalence. A snapshot path and a content hash do not prove complete
restoration. Write a test that boots from packs, saves, boots the snapshot in a fresh
runtime, and compares the roots listed in SnapshotCodec.ROOT_NAMES. Report any root that
does not round-trip.

Note: the repo already commits 20 fixture files under snapshots/search_compare/
(run-1786543184669, run-1786548752373; per-mode *.snapshot.json plus *.manifest.json for
astar/beam/bfs/dfs/rewritedfs). Read them before writing fixtures of your own. They are
tracked content, not debris: do not delete them. Fresh suite runs write new
snapshots/search_compare/run-<epoch-ms>/ directories; leave tracked ones alone.

Task 2 — fresh-process restore. The worker path re-boots inside a child process
(main.py:749-788). Verify that a child booted from a saved snapshot reaches the same state
as the parent, under start method "spawn" as pinned at search/compare.py:201. Record the
start method used; fork and spawn are not interchangeable here.

Task 3 — worker journal. Each worker already produces an attempt plus performance record via
_search_worker_checkpoint. Give each worker run a private, append-only journal bound to
(snapshot identity, worker mode, attempt, budget). Journal entries are observations, not
rules: nothing imported from a journal may install a rule or change search behaviour. Add a
test proving that importing a journal leaves the active rule set and search inputs
byte-identical.

Deliver: the interface list as found, round-trip results per ROOT_NAME, and the journal test.
```

### Agent C — join semantics and result checking

```text
You are C-JOIN. Worktree of your own. Base: 428ecdc.

Task 1 — result replay. SearchWorkerResult (search/model.py:1169) carries metrics and a job.
Before a worker result is accepted, replay its certificate against the snapshot and problem
it claims. A worker reporting success is not a proof; the derivation must replay.

Task 2 — join semantics. Preserve the planner's existing semantics exactly. Read
PlannerAlternative (planner.py:413) and its accessors (planner.py:449-494) and the consumer
loop at planner.py:852-920 before proposing any change. AND requires every child discharged;
OR requires one complete alternative. Never combine incompatible sibling assumptions.

Task 3 — stale and duplicate results. The tree already ignores stale packets — see
"ignoring stale SearchBFS packet result because mode status is already success" in the
search-compare debug output. Extend that discipline: a late result from a superseded attempt
must not overwrite accepted state, and duplicate delivery must have no duplicate effect.
Add tests for both.

Do not build a scheduler. Do not add a promotion or adoption path. Report a defect if you
find a result accepted without replay.

Deliver: replay test, join-semantics test, stale/duplicate tests, all green.
```

### INT — integrate, verify, tag

```text
You are INT. You do not write track features and you do not run sessions.

Pin the base: 428ecdc. Record the four-test baseline from a full suite run yourself; do not
inherit it.

Merge order: A, then B, then C, onto a candidate branch. A conflict inside a marked region
you resolve and report. A conflict where two branches touch one behaviour — the spawn path,
the snapshot codec, the result-acceptance path, or the ROOT_NAMES list — is semantic:
exclude both branches and name both owners.

Admission requires, on the composed candidate:
  two worker processes demonstrably overlap in wall time;
  the parent snapshot is unchanged by worker execution;
  worker results replay;
  crash, retry, cancellation and duplicate delivery preserve accounting;
  journal import leaves active rules and search inputs unchanged;
  wall time AND aggregate work recorded — parallelism is not assumed faster;
  every mechanism (b) finding names its branch — parallel shard past engine.py:657, or the
  serial return at engine.py:651/659. A finding that does not say is not admitted;
  no rent, provenance, adoption, promotion, learned-memory, mask, or schema vocabulary
  entered the diff. Grep the composed diff for these before merging. A branch that adds them
  is excluded from the batch regardless of test results, and the requirement goes in the
  index as a separate charter proposal;
  the full suite failure set is a subset of the four-test baseline.

A test that newly passes is only credited if its assertions can now fail. If an engineer
reports a fixed test whose assertions are vacuous — the A/C/D pattern in Agent A's brief —
return it. A green suite reached by making assertions unfalsifiable is worse than the red.

Only then cut an immutable tag. Record the platform and the suite duration with it.

Deferred, do not build: unlimited spawning, distributed machines, shared mutable hypergraphs,
automatic policy activation, and any learned-law adoption path. The five-track charter's
learned-memory, rent-gate, and provenance machinery does not exist at this commit; proposing
work against it is out of scope until that substrate is built.
```

---

## 5. Report format (every agent, every turn)

```text
agent: <A-RUNTIME | B-SNAPSHOT | C-JOIN | INT>
branch @ <hash>   base: 428ecdc
platform: <python, os, multiprocessing start method>
suite: <duration>s   failure set: <list>   delta vs baseline: <added/removed>
touched: <files, with line ranges>
traced mechanisms: <name — file:line>
ready to merge: <yes|no>   blocked on: <none | semantic conflict with agent X>
not built (deliberate): <list>
```

## 6. Stop conditions

```text
- A test "passes" only under a private runner -> void; the suite is the only arbiter.
- A fix that widens the guards at compare_packets.py:1436-1440 without naming every other
  caller of _comparison_prepare_shared_root_wave -> reject.
- Any journal or worker-result import that changes active rules or search inputs -> defect.
- A worker result accepted without derivation replay -> defect.
- A claim of speedup with no aggregate-work number alongside it -> not a measurement.
- A test reported fixed whose new assertions cannot fail -> returned, not credited.
- A mechanism named without write site + guard chain + measured state -> not a diagnosis.
- Rent/provenance/adoption/mask/schema vocabulary in any diff -> branch excluded, requirement
  re-filed as a separate charter proposal.
- A mechanism (b) finding that does not name its branch (engine.py:657 parallel vs :651/:659
  serial) -> not admitted.
```
