# S self-improvement loop — port onto experiment-5-frozen-r1: STATUS

Canonical base decision (orchestrator, 2026-09-06): the program's canonical
integration base is `experiment-5-frozen-r1` = `ef571b688bcfb581bd3e65ec28a18f438ca32595`.
Disposition of this session's five-commit S deliverable: PORT it onto that base.

The port below is built and test-verified this turn, not carried over.

## Ported commit series (base ef571b6)

```
dec1d2b  [S] trace mining
4551636  [S] rent gate for compressions
352eaf6  [S] recursive turn
3a64c58  [S] invariant conjecture from fixed library
2a9513e  [S] learned-memory cycle for self-improvement
6aba1d2  [S] port deltas: register five labels in both completeness tables; bump guard pin
```

The first five are the source commits cherry-picked onto ef571b6 (one
registration-hunk conflict each, resolved to the r1 track-partitioned
`# --- [S] ---` block, class form). The sixth carries the port deltas:

- delta 3 [SHARED hunk]: TraceLabel, MotifLabel, CompressedLawLabel,
  RefusedLabel, CandidateObservableLabel registered in both
  labels.sync_from_namespace and persistence.SNAPSHOT_SYMBOL_NAMES;
  completeness pins unchanged at 40 / 198 / 18.
- delta 4: TestShardCursorPinTest.EXPECTED_GUARD_COUNT 305 -> 310; hard pin
  (cursor 218, shard 0) unchanged.

Source commits, unaltered, still on arena/01a06cca-cat-theo-machine:
548c6f6, 8738bcf, 1e45188, 0e50bc1, 218a40f.

## Verification (this turn, venv gmpy2+pyyaml, PYTHONPATH=/tmp)

```
label_registration_completeness_test  PASS
test_shard_cursor_pin_test            PASS
self_improvement_trace_mining_test    PASS
self_improvement_rent_gate_test       PASS
self_improvement_recursive_turn_test  PASS
invariant_conjecture_test             PASS
self_improvement_memory_cycle_test    PASS
```

Full two-shard suite: not run here (INT's job; engineers run only the track
block plus tests touching changed files).

## How INT applies (on a port branch, not this session's branch)

Option A — bundle (preferred, exact objects):
```
git fetch <this-repo> 'refs/heads/arena/01a06cca-cat-theo-machine:refs/heads/src'
git bundle unbundle verification/self-improve-port/patches/self-improve-r1-port.bundle <branchname>
```
Option B — patches:
```
git checkout -b arena/01a06cca-self-improve-r1-port ef571b688bcfb581bd3e65ec28a18f438ca32595
git am verification/self-improve-port/patches/000*.patch
```
Both reproduce the six commits above on top of ef571b6.

## Shard-1 halt, resolved (world a)

The converse install halt is lineage-dependent: caused by 41e8078's
genus_body_bare template (removed by d528573, which IS in the ef571b6
lineage). Probe this turn: Converse('is two plus two equal to four') ->
Understood, 5 slots; ConversePropositionTest passes. Prediction: port
branch shard 1 installs fully; trace(305)/recursive(307)/memory(309) are
reached and green; comparison 145/5/2 unchanged. One-command pre-check:
`python3 tools/run_named_tests.py converse_proposition_test` on the port
branch.

## Not done here (session-pinned branch)

This session is pinned to arena/01a06cca-cat-theo-machine and cannot create
or push the port branch. INT (or a session pinned to
arena/01a06cca-self-improve-r1-port) applies the bundle/patches, then runs
the full two-shard gate (147/3/2 and 145/5/2 baselines) and the per-entry
OPEN mapping.
