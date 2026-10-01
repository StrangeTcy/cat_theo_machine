# cint-integrated-3 corrective slice (2026-09-16)

## Scope ordered per second GPT-6 Astra Max review (#2):
  checker/readiness -> active-attempt fencing -> checked real-worker OR -> recoverable serial activation.

## Changes (relative to base a52094888a30099150e6310b4b171ee2af97fe36 / cint-integrated-2 @2403a1c):

1. main.py (minimal CLI extension)
   - HYGE_SEARCH_WORKER_GATE_PATH / HYGE_SEARCH_WORKER_READY_TIMEOUT env vars
     gate the search-worker entry point: child writes ready-<pid> after the
     durable running-search checkpoint, blocks on release-<pid>, then runs
     the obligation. Default behaviour unchanged when env vars are unset.
   - rc=5 reserved for readiness-timeout.

2. programme_c/worker_dispatch.py
   - Coordinator-side _replay_certificate: boot_from_snapshot(result_path)
     and run proof.BuildDerivation against the child's saved worker_plan to
     accept proofs (not just inspect worker_stage metadata). Producer
     'success-derivation-built' is treated as a claim; the coordinator's
     checker decides acceptance.
   - Per-ticket gate dir: dispatcher waits for ready marker after
     running-search checkpoint, validates declared snapshot/obligation/
     assumptions, then writes the release marker before obligation execution
     (restore -> READY -> validate -> release -> execute).
   - next_attempt_id() and per-task _expected_attempt fencing table; stale
     envelopes are rejected while a retry is still running, not only when
     terminal.
   - spawn() accepts gate_path/manual_release for external control of the
     handshake (used by readiness-handshake test).

3. programme_c/join.py
   - ChildSpec.expected_attempt_id; assign_child_attempt / retry_child.
   - deliver_child_result fences envelopes against expected_attempt_id
     regardless of terminal status. First envelope to arrive for an
     unassigned child claims the slot; once assigned, mismatched attempts
     return F_STALE_RESULT.
   - No accepted_state_version decrement on activation failure (monotonic).
   - States admitted -> activating -> activated (activation-failed kept in
     accepted set with version preserved; blocks new admissions until
     resolved).
   - Durable 'activating' record written BEFORE invoking activation_fn so a
     crash can detect unresolved activation and reconcile; restart refuses
     new admissions while activation is in flight.
   - Invalid-cert reasons list expanded (F_SNAPSHOT_MISMATCH,
     F_SCOPE_VIOLATION, F_INCOMPATIBLE_ASSUMPTIONS, F_UNKNOWN_CHILD); these
     are non-mutating.

## Tests (61 total = 46 Programme C + 15 other Programme C modules pre-existing):
  Ran:  `python3 -m unittest discover -s hyge_int_pkg/programme_c/tests` +
        separate run of test_cb + test_ca (already included in discover).
  Result: 61/61 PASS in ~250s (subprocess-heavy dispatch/e2e tests).

New/updated assertions for this slice:
  * test_readiness_handshake_blocks_obligation_until_release: child is
    observed blocked at READY for 3s with no release marker; once release
    is written the worker proceeds and times out as expected.
  * test_invalid_derivation_fixture_rejected_by_proof_replay: producer
    metadata says success (worker_stage=success-derivation-built) but the
    saved plan's goal is corrupted; coordinator BuildDerivation replay
    rejects it (F_INVALID_CERT / F_SCOPE_VIOLATION).
  * test_checked_or_first_completing_alternative_discharges (e2e): a real
    Zero->Zero worker discharges an OR parent; late-cancelling siblings do
    not regress completion.
  * test_stale_attempt_after_retry_does_not_overwrite (test_cc): covers
    mid-retry stale rejection (before retry terminal).
  * test_gate_order_validity_then_rent_then_human_then_admit_then_activate +
    test_admission_after_join_through_gates_with_crash_safe_activation +
    test_activating_marker_survives_restart_and_prevents_admission:
    activation fails once (version stays 1), then simulated crash mid-
    activation (activating marker persisted), restart refuses new enqueues,
    activate_front runs exactly once and reports already-activated on
    second call.

## Unchanged-file verification against base SHA a52094888a30099150e6310b4b171ee2af97fe36:
  core.py, search/compare_executors.py, search/compare_subprocess.py:
  `git diff --name-only <base> -- <files>` returns empty.

## Still deferred (unchanged standing exclusions):
  T1/T2, Programme L, resident pool (wrapped, not replaced), joint-set
  rent, Experiment 4, live validity/rent/human wiring. Live admission
  remains HOLD until live gates (slice 2) land -- validity currently uses
  structural_only_validity_for_tests / ActivateProposal check-only path
  still needs real proof checking, rent evidence needs binding to
  (proposal, accepted_state, held-out benchmark identity), human approval
  needs binding to same.

