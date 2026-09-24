C-INT corrective integration record — 2026-09-16
================================================

Base: eng-base-0@1374464 (commit a52094888a30099150e6310b4b171ee2af97fe36).
Branch: work/C-INT/eng-base-0/r1 @f87c063 (push this commit; tag below).
Prior integration checkpoint: cint-integrated-1 @349a92f (superseded, not deleted).

## What changed relative to cint-integrated-1 (349a92f)

Per C-INT review (gpt-6-astra-max):

1. Fail-closed live gates (`programme_c/admission_hooks.py`):
   * `make_validity_check(None)` denies (fail-closed). Structural-only
     validity is retained as `structural_only_validity_for_tests()` for
     unit tests; it is NOT wired for live admission. The real isolated-runtime
     ActivateProposal check is the intended validity hook signature:
     `fn(entry, accepted, accepted_state_version) -> bool`; it must perform
     its checks without mutating parent state (caller uses an isolated
     runtime). Scaffolding for that wiring is in place but a fully wired
     validity-prover hook is a future item (a stub that always denies is
     used here so that nothing activates through a fake pass).
   * `make_rent_check(benchmark_dir=None)` with no benchmark_dir denies;
     presence of a readable JSON benchmark file in benchmark_dir is
     required to pass (performance-only gate, as before). Joint-set rent
     deferred.
   * `make_human_check(None)` denies (no private activation per protocol/F.md);
     callback exceptions deny.
   * Gate evidence is bound to `accepted_state_version`; after admission the
     version increments so stale evidence is re-validated.

2. Real-worker verification boundary (`programme_c/worker_dispatch.py`):
   * `_verify_child_certificate` uses the real `persistence.SnapshotCodec`
     (loaded via `main._runtime_namespace()`) to inspect the child snapshot
     rather than parsing raw JSON indices. It validates the manifest
     sidecar against declared snapshot_id, obligation, assumption_hash,
     task_id, attempt_id, then reads `worker_stage` via the codec.
   * Readiness ack (`_ready_from_checkpoint`) is accepted only after the
     snapshot is loadable via the codec AND the manifest sidecar matches
     the declared snapshot/obligation AND worker_stage is non-empty. The
     process must have completed restore and written its first checkpoint.
   * `rc=0/4` alone NEVER discharges a child; the certificate is replayed.
   * Stages `running-search`, `running-derivation`, `success-plan-found`
     are classified as incomplete (F_INVALID_CERT). `success-derivation-built`
     → S_COMPLETED; `timed_out` → F_TIMEOUT; failure-*/error → F_CRASH.
   * `_spawn_search_worker_process` gained a `defer_derivation` flag so
     tests can drive a complete (non-deferred) derivation end-to-end.
   * `_terminate` / `_proc_is_alive` are duck-typed for both
     multiprocessing.Process and subprocess.Popen (no isinstance/hasattr).

3. Durable manifest persistence (`programme_c/admission_hooks.py`, join.py):
   * Same-directory tmp → write+flush+fsync(tmp) → os.replace → fsync(dir)
     for Linux crash durability.
   * Persistence errors propagate — admit_next/enqueue do NOT report
     success if fsync or replace fails.
   * `enqueue_proposal` persists (queue entry durable even before any gate
     runs).
   * `load_admission_manifest`: missing file → new run; corrupt/truncated/
     schema-mismatch → raise `ManifestError` (fail-closed; silent reset
     removed). Schema version bumped to MANIFEST_SCHEMA_VERSION=2.
   * `JoinAdmission(..., strict_manifest=True)` raises ManifestError on a
     bad manifest; constructors take strict_manifest=False opt-in for tests.
   * `activate_front(activation_fn)` runs after a successful admit_next;
     failure rolls the entry back to the queue front with state
     'activation-failed', decrements the version, so restart/retry does
     not double-activate. Success marks the entry 'activated' and
     persists. One admission at a time through validity→rent→human→
     admit→persist→activate→persist.

4. Certificate delivery in `deliver_child_result`:
   * Invalid reason terms (F_INVALID_CERT, F_SNAPSHOT_MISMATCH, F_SCOPE_VIOLATION,
     F_INCOMPATIBLE_ASSUMPTIONS, F_UNKNOWN_CHILD, F_STALE_RESULT) return
     False without mutating child status, so the child stays 'running' and
     is retryable. Only accepted attempts mark the child terminal.
   * Stale-result check only fires when the child is already terminal.

## Tests (45/45 pass)

| Suite | Count | What it covers |
|---|---|---|
| test_cb  | 10 | snapshot round-trip+verify, tamper, fresh-process restore, journal round-trip, truncated/malformed/misattributed rejection, assumption-hash mismatch, duplicate import, scope isolation |
| test_ca  |  5 | max_workers=2, crash→F_CRASH + retry, timeout→F_TIMEOUT, snapshot tamper→F_SNAPSHOT_MISMATCH, cleanup |
| test_cc  | 12 | AND/OR join, stale/unknown child rejection, snapshot/obligation/assumption mismatch, execution-failure vs F_REFRUTATION, serial gate order (with new signature), e2e two-mp-workers |
| test_int_dispatch | 5 | real search-worker: readiness ack with cert, completed cert stamps all K_* fields, rc=2→F_TIMEOUT, deferred-derivation (rc=4) → F_INVALID_CERT (does not discharge), max_workers cap → F_LAUNCH_ERROR, wrong-obligation caught by cert replay |
| test_int_gates | 9 | fail-closed: missing validity/rent/human each block; gate order; human deny→approve→admit→activate→fail-rollback→admit→activate with no double-activation; enqueue persisted; restart rehydrates queue+accepted+version and prevents duplicate activation; corrupt manifest raises; wrong schema raises; persistence failure raises |
| test_int_e2e | 4 | two real search-worker subprocesses → certificate replay → checked AND join completes; deferred-derivation cert does NOT complete the parent; wrong snapshot/obligation rejected by F_SNAPSHOT_MISMATCH/F_SCOPE_VIOLATION; full validity→rent→human→admit→persist→crash→recover→approve→activate path with durable on-disk manifest, no double activation |

Dated artifacts under programme_c/tests/artifacts/2026-09-16/:
cb_snap_roundtrip.{identity.json,snapshot.json}, cb_tamper.log,
cb_fresh_restore.log, cb_journal_roundtrip.jrnl, cb_dup_import.manifest.json,
ca_two_workers.txt, ca_crash_retry.txt, cc_serial_admission.log,
cc_end_to_end.log, cint_dispatch.log, cint_gates.log, cint_e2e.log.

Interpreter: /usr/bin/python3  (system Python; gmpy2 2.3.1, pyyaml 6.0.3).
Command pattern: `PYTHONPATH=/home/user timeout <sec> python3 -m hyge_int_pkg.programme_c.tests.test_<name>`.
Full SHA at tip: f87c063 (tag cint-integrated-2 recommended for this slice).

## Charter conformance

* core.py md5 unchanged: 52226f209956fa1f62c484021855b0e9.
* search/compare_executors.py and search/compare_subprocess.py unchanged
  (verified via `git diff 1374464 -- search/ core.py main.py` is empty).
* No new pool replaces the existing resident pool; wrapper is additive.
* Programme L untouched; Experiment 4 not run; no conda Python; no FLT
  explanation; joint-set rent deferred.
* Every execution failure is a machine failure term with K_REASON atom.
* Every reported pass cites a dated artifact.
* T1 (compare_search_modes_finds_reusable_worker_snapshot_dir_test) and T2
  (compare_search_modes_fill_warms_resident_pool_before_root_wave_test)
  remain OPEN; the failing code paths are unchanged from eng-base-0 and
  diagnosis does not close them.

## Remaining bounded work for the next slice

* Wire the isolated-runtime validity hook to a real check-only
  ActivateProposal (boot isolated runtime, attach proposal with Approved
  annotation, call ActivateProposal; treat non-EmptyList installed_version
  as pass; discard runtime afterwards so parent knowledge is not mutated).
* Wire rent hook to the real held-out rent benchmark once a benchmark_dir
  convention is established (fail-closed in the meantime).
* Wire human approval to an explicit console/UI callback (default-deny
  already enforced).
* Keep single-admission-at-a-time through activation.
