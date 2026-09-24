# cint-integrated-3 follow-up — GPT-5.6 corrective closures (2026-09-16)

Closes the three qualifications raised against cint-integrated-3:

1. Activation idempotency keyed by activation_id.
   - admit_next assigns a stable activation_id ("act-<uuid16>") to every
     admitted proposal BEFORE persisting 'admitted'.
   - activate_front accepts an optional reconcile_fn(entry) used on the
     'activating' recovery path: True=committed (mark 'activated' without
     calling activation_fn); False=not committed (invoke activation_fn
     with the same activation_id); None=ambiguous (HOLD, leave state
     'activating').
   - activation_fn receives entry dict with activation_id so external
     adapters can dedup/reconcile against it.
   - Test: test_post_side_effect_pre_persist_crash_reconciles writes an
     external journal keyed by activation_id and raises to simulate a
     post-effect/pre-persist crash; restart + reconcile_fn flips state to
     'reconciled-activated' with no duplicate side effect (journal count
     == 1, fn called 0 times).
   - Test: test_reconcile_unknown_stays_hold verifies ambiguous verdict
     keeps state 'activating' and returns "activation ambiguous".
   - Test: test_activation_id_stable_and_passed_to_fn verifies id is
     passed to fn and second activate_front is already-activated.

2. Durable expected-attempt fencing across dispatcher restart.
   - SearchWorkerDispatch accepts state_path; expected_attempt is
     persisted via atomic tmp+fsync+replace on every spawn/retry and
     reloaded on construction.
   - Test: test_expected_attempt_fence_survives_dispatcher_restart
     spawns a-1, advances fence to a-2 via next_attempt_id, destroys
     the dispatcher, reconstructs with the same state_path, and
     confirms a late a-1 envelope returns F_STALE_RESULT before the
     cert-replay step.
   - Note: join-side ChildSpec.expected_attempt_id remains process-local
     (caller is the coordinator which rebuilds child state from its own
     durable records); the dispatcher's expected_attempt covers the
     poll/cert-replay path.

3. main.py env-unset regression + rc=5 mapping.
   - Spawn gained a gate_enabled=True parameter; when False, no gate env
     vars are passed to the child (HYGE_SEARCH_WORKER_GATE_PATH and
     HYGE_SEARCH_WORKER_READY_TIMEOUT are explicitly stripped from the
     inherited env), no _gate directory is created in the work dir, and
     the worker runs the legacy path (search starts immediately after
     checkpoint restore).
   - rc=5 (ready-timeout) is mapped to F_TIMEOUT via the existing
     RC_READY_TIMEOUT branch in _wait_ready; pool.cleanup removes the
     worker directory.
   - Test: test_gate_disabled_runs_without_gate_dir_and_succeeds boots a
     Zero->Zero worker with gate_enabled=False and confirms no _gate
     dir exists, search completes, and cleanup removes the worker dir.
   - Test: test_rc5_ready_timeout_maps_to_f_timeout holds release,
     drives the coordinator past its budget, and asserts F_TIMEOUT with
     clean cleanup.

main.py is now listed as intentionally modified (readiness-gate
extension); core.py, search/compare_executors.py,
search/compare_subprocess.py remain unchanged (empty diff against
a5209488…).

Test suite: 52/52 pass in ~292s via
  python3 -m unittest discover -s hyge_int_pkg/programme_c/tests
