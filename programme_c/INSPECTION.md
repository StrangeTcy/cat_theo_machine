Agent A inspection record — 2026-09-16
=====================================

Base: eng-base-0@1374464 (commit a52094888a30099150e6310b4b171ee2af97fe36).

Reproduction:
  compare_search_modes_finds_reusable_worker_snapshot_dir_test
    Result: FAIL
    Firing assertion: testsuite.py line after probe._reusable_search_worker_result_paths
      (the "SearchBFS" key is missing from the returned mapping, or its path
       does not match matching_path).
    Executed path: probe._reusable_search_worker_result_paths walks run-N dirs
      under <package_root>/snapshots/search_compare/ and for each mode calls
      _search_worker_snapshot_matches_current_problem(search/compare_subprocess.py:313),
      which loads the snapshot and compares start/goal/manifest text to the
      current problem. With the test-constructed _CompareSearchModesProbe, the
      manifest written by _write_search_worker_manifest uses start_text/goal_text
      derived from the outer probe's start/goal (Chars "s","g"), while the
      checkpoint inside the fresh worker runtime is written against its own
      heuristic and atoms. _load_search_worker_snapshot returns a failure/
      mismatch pair, so the candidate is skipped, leaving "SearchBFS" absent
      from found (locus search/compare_subprocess.py:364-366 where matched_pair
      Head is false_value the candidate is continue'd).
    Diagnosis does not close the test. No new pool before this inspection lands.

  compare_search_modes_fill_warms_resident_pool_before_root_wave_test
    Result: FAIL
    Firing assertion: invariant 2 (testsuite.py:1755) —
      _comparison_shared_root_candidates_ready remains false_value after
      _fill_parallel_workers returns.
    Executed path: _WarmRootWaveCompareProbe._fill_parallel_workers (in
      search/compare_executors.py, around line 656) walks states and, when the
      desired resident total exceeds current, calls _spawn_parallel_executor
      which constructs a _ResidentExecutorProcessProbe and calls
      _await_parallel_executor_ready. The probe process does not enqueue a
      SearchWorkerReadyLabel onto the result_queue during spawn synchronously;
      the ready-poll loop's zero-timeout path returns false_value before any
      ready message is enqueued, leaving _comparison_shared_root_candidates_ready
      at false_value. The other three invariants (spawned non-zero, workers
      non-empty, need_shared_root_wave false) are satisfied.
    Diagnosis does not close the test.

Required replacement report (per §2) to C-INT:
  Existing resident pool (search/compare_executors.py) is reused:
    - _resident_executor / _total_resident_executor_count /
      _desired_resident_executor_total / _spawn_parallel_executor /
      _await_parallel_executor_ready / _fill_parallel_workers / shard retry /
      generation replacement are intact.
  Additions introduced by programme_c/worker.py BoundedWorkerPool (C-A):
      * hard max_workers=2 cap;
      * explicit mp.get_context("spawn") start method;
      * per-task isolated cwd under scratch_root/workers/<id>;
      * snapshot-identity pre-flight (verify_identity +
        verify_restore_fresh_process) before dispatch, mismatch becomes
        F_SNAPSHOT_MISMATCH machine failure term;
      * readiness-ack handshake before dispatching work; ready ack must
        declare matching snapshot_id and obligation (otherwise F_INVALID_CERT);
      * task_id / attempt_id / declared_snapshot_id / declared_obligation /
        assumption_hash stamped on every envelope (ready, result, failure);
      * explicit budgets, deadlines, SIGTERM→SIGKILL cancellation,
        atexit shutdown, scratch-dir cleanup;
      * crashes and timeouts become F_CRASH / F_TIMEOUT machine terms and
        are never conflated with logical refutation (F_REFRUTATION).
  The existing subprocess search-worker path in compare_subprocess.py is
  untouched (no replacement). BoundedWorkerPool provides an independent
  bounded-execution substrate that C-C can drive from JoinAdmission.
