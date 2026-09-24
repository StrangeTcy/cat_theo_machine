# C-INT-8A — admission correctness boundary

**Date:** 2026-09-19
**Programme:** C
**Parent:** cint-integrated-7^{} = 65103a048eeea282a448213ccc23ce74cf023c35
**Base provenance:**
- base tag name: eng-base-0@1374464
- annotated tag object: a52094888a30099150e6310b4b171ee2af97fe36
- peeled base commit: 137446435362a9727c2f7c181c663adab9d4c357
**Branch:** work/C-INT/eng-base-0/r2 (authorized); this checkout is arena/01a0bbdd-cat-theo-machine tracking the same parent (grafted) — content identical to r2.
**Tag after review:** cint-integrated-8a

Own checkout. Push only authorized branch. Never force-push. Do not move or delete existing tags. Programme C only. Programme L and INV-0 remain untouched. Live admission remains HOLD. Do not wire production human approval in this cut. Do not change rent miss semantics in this cut. Do not introduce F_RENT_HOLD. No Experiment 4, FLT, conda Python, theorem packs, LLM scheduling, or core.py edits.

## Lineage correction

`protocol/AGENT-SPAWN.md` previously identified `a52094888a30099150e6310b4b171ee2af97fe36` as a commit. It is an **annotated tag object** for `eng-base-0@1374464`. The peeled commit is `137446435362a9727c2f7c181c663adab9d4c357`. This document records the correction; the `eng-base-0` tag was not moved. No INV-0 cherry-pick is authorized.

## Authorized scope — C-H1 .. C-H5

### C-H1 — mandatory coordinator-owned gate chain
1. A proposal or enqueue caller may not omit validity, rent, or human gates.
2. The mandatory order is validity → rent → human.
3. Remove caller authority over the live mandatory chain, or ignore/reject caller-supplied omissions.
4. Test injection belongs on the JoinAdmission/coordinator fixture, not in the proposal entry.
5. Empty gates supplied to enqueue must not produce admission.
6. Persist every gate transition before returning.

### C-H2 — fail-closed accepted-state validity replay
1. Remove catch-and-continue behavior when decoding/installing accepted laws.
2. Any accepted-state replay failure becomes F_LAUNCH_ERROR (or the existing equivalent infrastructure/state-replay reason).
3. Leave the queue front intact and accepted_state_version unchanged.
4. Do not classify incomplete-state replay as F_INVALID_CERT for the candidate.

### C-H3/C-H4 — isolated certificate replay with exact endpoint checking
1. Coordinator certificate replay must run in a fresh spawned subprocess.
2. Parent must not call boot_from_snapshot or mutate M.AllConstructors for replay.
3. Replay and verify: snapshot_id, task_id, attempt_id, obligation, assumption_hash, declared start, declared goal, success-derivation-built stage, BuildDerivation success, derivation start == declared start, derivation conclusion == declared goal.
4. A valid derivation for a different terminal goal is F_INVALID_CERT and cannot complete a child.
5. Parent runtime singleton identities/content must remain unchanged before/after.
6. Truncated response, child crash, schema mismatch, or boot failure becomes F_LAUNCH_ERROR / execution failure, not mathematical refutation.

### C-H5 — durable persistence errors propagate
1. _fsync_dir must not suppress OSError under the stated Linux durability contract.
2. tmp write → flush → fsync(tmp) → os.replace → fsync(parent dir).
3. If any stage fails, enqueue/admit/activate must not report durable success.
4. Add injected directory-fsync failure and replace-failure tests.

## Required tests (8A)
- enqueue with gates=[] still runs validity → rent → human and cannot admit.
- unknown/unsupported gate configuration fails closed.
- accepted-law decode failure holds front intact and does not run candidate check.
- accepted-law install failure holds front intact.
- wrong derivation terminal goal rejected.
- wrong start rejected.
- valid certificate replay succeeds in fresh child.
- parent constructor/runtime state unchanged by replay.
- child crash/truncated replay response becomes execution failure.
- directory fsync failure propagates; no admitted success is returned.
- os.replace failure propagates; manifest is not silently reset.

## Protected files
core.py, search/compare_executors.py, search/compare_subprocess.py must remain byte-for-byte unchanged from the peeled base unless the final report explicitly identifies an already-carried intentional difference.

## Deliverables
- protocol/C-INT-8A.md (this file)
- corrected protocol/AGENT-SPAWN.md
- implementation and tests
- dated artifacts under programme_c/tests/artifacts/2026-09-19/
- full Programme C suite result
- diff verification for protected files
- pushed commit and proposed immutable tag

## End-report fields
agent / branch / base tag object / peeled base commit / parent / pushed commit;
interfaces changed;
tests and artifacts;
open failures with loci;
ready for 8B: yes/no;
live admission HOLD;
next bounded item: C-INT-8B rent correctness.

## Held next cut: C-INT-8B — rent correctness
Do not begin until 8A is reviewed. Must close rent findings and formal review identifiers C-G1/G2/G3/C-C1.
