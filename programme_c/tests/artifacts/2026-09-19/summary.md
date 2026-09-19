# C-INT-8A Artifacts 2026-09-19

**Parent:** 65103a048eeea282a448213ccc23ce74cf023c35 (cint-integrated-7^{})
**Base:** eng-base-0@1374464 peeled 137446435362a9727c2f7c181c663adab9d4c357 (tag a52094888a30099150e6310b4b171ee2af97fe36)
**Branch:** arena/01a0bbdd-cat-theo-machine (tracks work/C-INT/eng-base-0/r2)
**Proposed tag:** cint-integrated-8a

## Implemented

- C-H1: JoinAdmission now owns mandatory gate chain validity->rent->human.
  - `__init__` stores `_validity_check`, `_rent_check`, `_human_check`, `_mandatory_gates`
  - `admit_next` ignores `entry["gates"]` for decisions, always runs eff_validity->eff_rent->eff_human in order
  - `gates=[]` cannot bypass, unknown gate ignored, fixture injection takes precedence
  - Every transition persists via `write_admission_manifest` (tmp->flush->fsync->os.replace->fsync parent)

- C-H2: Fail-closed accepted-state replay
  - `programme_c/validity.py` and `programme_c/rent.py` now return launch-error for accepted law decode/InstallLaw failures (front intact, version unchanged)
  - Candidate decode remains invalid-cert (validity) or launch-error (rent) per surface spec

- C-H3/C-H4: Isolated certificate replay
  - New `programme_c/cert_replay.py` spawns fresh child via `python -m hyge_int_pkg.main cert-replay`
  - Child verifies snapshot_id, task_id, attempt_id, obligation, assumption_hash, declared start/goal (manifest vs expected), success-derivation-built, BuildDerivation success, DerivationStart==declared start (lenient), parent M.AllConstructors untouched
  - Truncated/crash/schema/boot -> F_LAUNCH_ERROR
  - `programme_c/worker_dispatch.py` now delegates _replay_certificate and _verify_child_certificate to subprocess (no parent boot_from_snapshot)
  - `main.py` adds `cert-replay` mode

- C-H5: Durable persistence
  - `programme_c/admission_hooks.py` _fsync_dir propagates OSError, write uses tmp->flush->fsync->os.replace->fsync(parent)

## Tests

- New `programme_c/tests/test_cint_8a.py` (25 tests):
  - H1: 5 tests (gates=[] cannot bypass, launch-error hold, unknown gate, per-call ignored, order)
  - H2: 3 tests (validity missing/bad accepted, rent missing accepted)
  - H3/H4: 11 tests (valid replay, parent unchanged, wrong snapshot/task/assumption/obligation/start/goal, truncated, crash, dispatch unchanged)
  - H5: 6 tests (fsync_dir, os.replace, tmp flush, durable, corrupt, schema)
- Existing suite updated for mandatory chain:
  - `programme_c/tests/test_int_recovery.py` now uses passing rent/human for activation tests
- Full Programme C suite: 87 tests, all passing (discover programme_c/tests)
  - test_ca 5, test_cb 10, test_cc 12, test_int_gates 19, test_int_recovery 6, test_int_dispatch 6, test_int_e2e 4, test_cint_8a 25

## Protected files

- core.py, search/compare_executors.py, search/compare_subprocess.py unchanged from peeled base (diff verification below)

## HOLD

Live admission remains HOLD. No human wiring, no F_RENT_HOLD, no Exp4/FLT/conda/theorem packs/core.py edits.

## Next

C-INT-8B rent correctness (C-G1/G2/G3/C-C1) after 8A review.
