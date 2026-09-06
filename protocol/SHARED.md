# [SHARED] process workers

Base: preflight-412b215@412b2153e99e447764fe17121b82e8f607261e09
Landed: 099586e on arena/01a06da9-cat-theo-machine
C1 re-run: 2026-09-06 on `make_fresh_runtime()`, no pack boot.

## C1 — failure mechanism per red test

Both baseline reds reproduced. Results are `false_value` (`core.Diff`).
The two tests were not closed, not deleted, and not greened by this cut.

### 1. compare_search_modes_fill_warms_resident_pool_before_root_wave_test

failure mechanism: `_fill_parallel_workers` never sets
`_comparison_shared_root_candidates_ready` to `truth_value`. The test's
second guard is that identity compare. Spawn and worker-list guards pass.

Measured on `_WarmRootWaveCompareProbe` with `_comparison_machine_parallelism = one`
and `_comparison_states(_mode_chain())` (five modes):

```text
need_wave_before: false
candidates_ready_before: false
spawned_before: 0
pre-state (each of 5): status=SearchRunningLabel
                       phase=SearchRootFastPathPhaseLabel
                       active=0 pending_empty=true fresh_root=true
spawned_after: 5
candidates_ready_after: false   <-- failing term
workers_empty: false
need_wave_after: false
post-state (each of 5): active=1 pending_empty=true fresh_root=false
```

`_comparison_states_need_shared_root_wave` (`search/compare_packets.py`
around the phase/status/active/pending/fresh-root conjunction) requires
`SearchPacketSearchPhaseLabel`. Fresh compare states start in
`SearchRootFastPathPhaseLabel`. The conjunction is false, so
`_fill_parallel_workers` (`search/compare_executors.py`,
`_fill_parallel_workers`) skips `_grow_parallel_executor_pool` and
`_comparison_prepare_shared_root_wave` never reaches
`_comparison_cache_shared_root_candidates` (`search/compare_packets.py`,
the assignment of `_comparison_shared_root_candidates_ready = truth_value`).
Later `_collect_parallel_worker_launches` still leases: five on-demand
spawns, workers nonempty, need-wave stays false because the jobs are no
longer fresh-root.

locus: `search/compare_packets.py` `_comparison_states_need_shared_root_wave`
then `search/compare_executors.py` `_fill_parallel_workers`
then `search/compare_packets.py` `_comparison_cache_shared_root_candidates`
test: `testsuite.py` `CompareSearchModesFillWarmsResidentPoolBeforeRootWaveTest`

### 2. compare_search_modes_finds_reusable_worker_snapshot_dir

failure mechanism: `_reusable_search_worker_result_paths` returns `{}`.
The snapshot file is written. Load succeeds. Resume-ready is true.
Match Head is false, so SearchBFS is never entered in `found`.

Measured after `_search_worker_checkpoint` of `Pair(Char("s"), EmptyList)`
→ `Pair(Char("g"), EmptyList)` with reason `running-derivation`:

```text
snapshot_exists: true   .../run-1/bfs.snapshot.json
manifest_exists: true
status: SearchSuccessLabel
resume_ready: true
final: false
start_pretty_live: [s]     start_pretty_loaded: [s]
goal_pretty_live: [g]      goal_pretty_loaded: [g]
start_equal TermEqual: false
goal_equal TermEqual: false
heuristic_equal TermEqual: false
  live PrettyTerm:  [<?>, <?>, 3, 1, 1, 1]
  loaded PrettyTerm: [<?>, <?>, 0, 1, 1, 1]
matches_head: false
found_keys: []
```

`_search_worker_snapshot_matches_current_problem`
(`search/compare_subprocess.py`) returns Head `false_value` on the first
check: `TermEqual(SearchAttemptStart(attempt)(), self.start)`. PrettyTerm
of live and loaded start is the same `[s]`; snapshot restore does not
preserve `TermEqual` identity for `Pair(Char("s"), EmptyList)`. Goal
fails the same way (`[g]` vs `[g]`). Heuristic also fails: live beam
width 3 vs loaded 0 (`_heuristic_for_mode` vs the checkpointed
`_search_worker_mode_heuristic`). The first failing term is start.

locus: `search/compare_subprocess.py`
`_search_worker_snapshot_matches_current_problem` (TermEqual start/goal/heuristic)
then `_reusable_search_worker_result_paths`
load: `_load_search_worker_snapshot`
resume gate: `_partial_worker_attempt_is_resume_ready`
test: `testsuite.py` `CompareSearchModesFindsReusableWorkerSnapshotDirTest`

### 3. verdict: half-built frontier

grounds: both paths implement real machinery and neighboring
`compare_search_modes_*` tests stay green. Fill still spawns a resident
pool (five leases). Reusable still writes `bfs.snapshot.json`, loads a
success attempt, and accepts resume-ready. The reds fail on phase-gate
and restored-term identity, not on missing files or zero spawn.

`workers.py` does not collide with that subsystem. It launches
`python -m cat_theo_machine.workers` against a SHA-256 of a
`hyge-proof-kernel` snapshot, discharges `M.Compare(M.Char, M.Char)`,
and joins with `AndJoin` / `OrJoin`. It never calls
`_fill_parallel_workers`, `_reusable_search_worker_result_paths`, or the
resident executor pool. Cold read of the parent snapshot; no shared
mutable state.

Active line this cut: `workers.py`.
Parked line: `compare_search_modes` resident-pool / snapshot-dir reuse.

## INT ruling requested (one of three)

This lane does not apply retire or converge. Findings above are the
grounds. Request:

```text
a. RETIRE: compare_search_modes is a dead experiment; remove or
   quarantine the two reds in the same batch. Baseline shrinks by two.

b. REVIVE-LATER: half-built frontier; keep the two reds as known-red.
   Ledger names workers.py as the active process-worker line and
   compare_search_modes as parked. No test deletion.

c. CONVERGE: workers.py later adopts snapshot-dir layout and pool
   warming; ledger the mapping. Not this cut.
```

Recommended: (b) REVIVE-LATER. The measured terms are phase-gate and
TermEqual-after-load, not an empty module. Deleting the reds would hide
a live path. Converge is a later mapping: `workers.py` has no pool
warming and no `snapshots/search_compare` layout.

Holds merge until INT records one of a/b/c.

## Landed runtime (C2, unchanged)

launcher: subprocess + `python -m cat_theo_machine.workers`
isolation: one immutable snapshot, separate obligations
crash: `ExecutionFailureLabel`, not a false obligation
admission: `SerialAdmitProposal` from proposal-journal heads only

Tests green:
- shared_two_workers_overlap_and_join_test
- shared_or_join_and_crash_execution_failure_test
- shared_serial_admission_and_stale_attempt_test

## Named next tests (not this turn)

- ablation: a law admitted via SerialAdmitProposal vanishes on reset, returns on re-mine
- sibling independence: ablating one worker's admitted law does not disturb the other's
- evidence-class neutrality: suite failure set identical with and without merged evidence entries
- admission logging: each admission cites its re-baseline point

## Deferred

joint-set rent gate; old-subsystem replacement; full snapshot restore
inside the worker; Wave 1.
