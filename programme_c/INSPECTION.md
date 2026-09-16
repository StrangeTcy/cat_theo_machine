C-INT inspection record — 2026-09-16
=====================================

Base: eng-base-0@1374464 (commit a52094888a30099150e6310b4b171ee2af97fe36).
Branch: work/C-INT/eng-base-0/r1 @15c449f; tag cint-integrated-1 pushed.

Integrated modules:
  - programme_c/__init__.py, snapshot_id.py, journal.py, evidence.py (C-B interface).
  - programme_c/worker.py (C-A bounded-pool substrate, max_workers=2, explicit
    spawn, isolated cwd, readiness-ack, snapshot pre-flight, deadlines,
    cancellation, cleanup verified by directory-existence assertions).
  - programme_c/join.py (C-C child contract, certificate validation, AND/OR
    join, serial proposal admission; execution failure distinct from logical
    refutation via F_REFRUTATION; on-disk admission manifest persisted on
    every admit/reject/hold transition before returning; re-hydrated at
    construction).
  - programme_c/worker_dispatch.py (integration move 1): wraps the existing
    `python -m hyge_int_pkg.main search-worker <mode> <result> <timeout>`
    subprocess entry under BoundedWorkerPool semantics. Does NOT replace
    search.compare_executors._fill_parallel_workers / _spawn_parallel_executor
    / _await_parallel_executor_ready; those functions remain intact and
    untouched. Every ready/result/failure envelope stamped with
    K_TASK_ID/K_ATTEMPT_ID/K_WORKER_ID/K_DECLARED_SNAPSHOT/K_DECLARED_OBLIGATION/
    K_ASSUMPTION_HASH/K_BUDGET/K_REASON. Exit-code mapping: rc=0/4 → completed,
    rc=2 → F_TIMEOUT, rc<0 → F_CRASH, rc=1 failure → F_CRASH/F_TIMEOUT based
    on the checkpoint stage.
  - programme_c/admission_hooks.py (integration move 2): default validity
    check (structural non-empty, NUL-free), default rent check (pass;
    benchmark dir gated when supplied — joint-set rent deferred), default
    human approval (denies; no private activation path per protocol/F.md);
    write_admission_manifest / load_admission_manifest for durable state.

Tests (all green, dated artifacts under programme_c/tests/artifacts/2026-09-16/):
  test_cb:  10/10 (cb_snap_roundtrip.*, cb_tamper.log, cb_fresh_restore.log,
                   cb_journal_roundtrip.jrnl, cb_dup_import.manifest.json).
  test_ca:   5/5 (ca_two_workers.txt, ca_crash_retry.txt).
  test_cc:  12/12 (cc_serial_admission.log, cc_end_to_end.log).
  test_int_dispatch: 3/3 real search-worker boots (cint_dispatch.log):
    - readiness ack stamps declared snapshot/obligation and every result
      envelope carries K_TASK_ID/K_ATTEMPT_ID/K_DECLARED_OBLIGATION/
      K_ASSUMPTION_HASH/K_BUDGET; isolated cwd cleanup removes directory.
    - tight worker_timeout yields F_TIMEOUT (rc=2) on the envelope.
    - third concurrent spawn is synchronously rejected with F_LAUNCH_ERROR
      (max_workers=2).
  test_int_gates: 3/3 (cint_gates.log):
    - serial validity→rent→human order; second admit with approving human
      callback admits; on-disk manifest reflects every transition.
    - fresh JoinAdmission constructed against an existing manifest
      re-hydrates accepted proposals durably (next candidate sees updated
      accepted set from disk, not just in-memory).
    - validity failure drops front; next candidate is considered.

Baseline T1/T2 remain OPEN (untouched code paths — main.py, core.py,
search/compare_executors.py, search/compare_subprocess.py are unchanged
from eng-base-0@1374464). Inspection record at hyge_ca/programme_c/INSPECTION.md
(C-A) describes the exact failing assertions and executed paths; diagnosis
does not close either test.

Charter conformance:
  - No core.py edits; no banned constructs (@classmethod/@staticmethod/
    @property/dataclass/isinstance/hasattr/getattr/callable/type()/__class__/
    __new__) introduced in new code (legacy isinstance uses from the v2
    modules predate this integration commit and are confined to JSON
    canonicalization / envelope type-dispatch at the Python/process
    boundary).
  - Every execution failure is a machine failure term with K_REASON atom;
    every reported pass cites a dated artifact under artifacts/2026-09-16/.
  - Existing resident pool reused — not replaced.
  - Programme L not restarted. Experiment 4 not run. No conda Python.
    No FLT explanation.
  - protocol/AGENT-SPAWN.md records the base reconciliation (eng-base-0 →
    a520948, not 428ecdc) and the superseding r2 tags.

Deferred (unchanged per opus 4.7):
  - Wiring validity hook to the real ActivateProposal/proof checker.
  - Wiring rent hook to the held-out rent benchmark.
  - Wiring human hook to a UI callback (default is deny-safe).
  - Joint-set rent.
  - Any replacement of compare_executors resident pool — inspection record
    remains the gating artifact for such a proposal.
