# [SHARED] process workers

Base: preflight-412b215@412b2153e99e447764fe17121b82e8f607261e09

## Step 1 inspect — compare_search_modes (dated 2026-09-06)

Both baseline reds reproduced on `make_fresh_runtime` without pack boot.

### compare_search_modes_finds_reusable_worker_snapshot_dir (shard 1)

Locus: `search/compare_subprocess.py` `_search_worker_snapshot_matches_current_problem`
then `_reusable_search_worker_result_paths`.

Executed path: the test writes `bfs.snapshot.json` plus a manifest, then asks
the probe to recover `SearchBFS`. `_load_search_worker_snapshot` returns an
attempt whose status is success and which `_partial_worker_attempt_is_resume_ready`
accepts, but `TermEqual` of loaded `SearchAttemptStart` against the live
`self.start` is false. Reusable-path map stays empty. Snapshot restore does
not preserve term identity for `Pair(Char("s"), EmptyList)`.

### compare_search_modes_fill_warms_resident_pool_before_root_wave_test (shard 0)

Locus: `search/compare_executors.py` `_fill_parallel_workers`.

Executed path: `_comparison_states_need_shared_root_wave` is already false
before fill, so the grow-for-root-wave branch is skipped.
`_comparison_shared_root_candidates_ready` remains `false_value`. Spawn count
is nonzero via later leasing, workers are nonempty, and the post-fill
need-wave flag is false. The test fails on the candidates-ready guard.

Verdict: half-built frontier, not dead. Do not replace it this cut.
Do not close those tests by diagnosis.

## Step 2 ruling

Revive later. First milestone lands beside the subsystem: two OS worker
processes, immutable snapshot identity, checked AND/OR join, serial
proposal admission. No joint-set rent gate.

## Step 3 landed

File: `workers.py`. Labels in `labels.py` and `SNAPSHOT_SYMBOL_NAMES`.
Tests: `shared_two_workers_overlap_and_join_test`,
`shared_or_join_and_crash_execution_failure_test`,
`shared_serial_admission_and_stale_attempt_test`.

Worker writes never touch the parent snapshot. Crash → `ExecutionFailureLabel`,
not a false mathematical obligation. Observation journals do not admit.
Proposal journals admit one at a time.

## Deferred

Full snapshot restore in the worker, joint-set rent, unlimited spawn,
compare_search_modes repair.
