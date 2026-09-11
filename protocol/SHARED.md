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

## INT ruling — REVIVE-LATER (recorded)

```text
ruling: REVIVE-LATER
active process-worker line: workers.py (099586e)
parked subsystem: compare_search_modes (resident pool + snapshot reuse)
authority: this file
```

Grounds: the two reds are a phase gate and a restored-term identity
mismatch. Fill still spawns; reuse still writes and loads; neighboring
compare tests stay green. `workers.py` does not call the resident pool
or the snapshot-dir reuse path; coexistence is authorized.

Standing conditions:

- the two compare reds remain known-red and must stay the same two reds
  at every future cut; a shape change or a third compare red is a
  regression, not inherited baseline
- CONVERGE is the expected eventual path: first `workers.py` need for
  pool warming or snapshot reuse opens that commit; the two reds resolve
  there, not before
- no test deletion this cut

Two-shard suite on 513f883: both shards exit 0. Combined failure set
identical to preflight baseline. The two compare reds are the same two,
same shape. Nothing new, nothing absorbed.
Artifact: verification/2026-09-07-shared-two-shard.txt

## Landed runtime (C2, unchanged)

launcher: subprocess + `python -m cat_theo_machine.workers`
isolation: one immutable snapshot, separate obligations
crash: `ExecutionFailureLabel`, not a false obligation
admission: `SerialAdmitProposal` from proposal-journal heads only

Tests green:
- shared_two_workers_overlap_and_join_test
- shared_or_join_and_crash_execution_failure_test
- shared_serial_admission_and_stale_attempt_test

## Named next tests

- ablation: landed as `shared_serial_admit_proposal_ablation_test` — SerialAdmitProposal journal, existing approval gate, law present after activate, absent on reset to the base GraphVersion, present again after re-mine through the same path. Observation journals still do not admit.
- sibling independence: blocked on mask-coverage finding below
- evidence-class neutrality: landed as `shared_evidence_class_neutrality_test`. AttemptedRuleLabel / CounterfactualEvidenceLabel are observation-class journal terms. Merging traces, residuals, AttemptedRule, and CounterfactualEvidence into the coordinator GraphVersion node store installs no law, activates no policy, and leaves Match/Rewrite results unchanged. SerialAdmitProposal / CheckedAdmitProposal still reject those terms (AdmissionRejectedLabel, empty queue); proposal-class journals still queue through that path only. No FireAny entry. Artifact: verification/2026-09-11-evidence-class-neutrality.txt
- admission logging: queue-level landed as `shared_serial_admit_proposal_cites_baseline_test` — SerialAdmitProposal writes Pair(journal, Pair(baseline, EmptyList)) and preserves the supplied baseline field (Compare against a reconstructed Char). Observation journals still do not admit and write no record. That cut does not check origin vs coordinator and does not activate.
- checked admission: landed as `shared_checked_admit_proposal_logging_test` — CheckedAdmitProposal queues through SerialAdmitProposal, compares worker origin snapshot identity to coordinator SnapshotIdentity(path) via Compare (not IdentityCompare), and on match submits through the existing ProposalStore / Approved / ActivateProposal gate. Success records AdmissionSucceededLabel, queued journal, origin digest, coordinator digest, GraphVersion before/after, and the gate return. Missing origin or coordinator digest → AdmissionRejectedLabel, no activate. Origin≠coordinator → AdmissionStaleLabel, no silent relabel, no activate. Unapproved authority and ObservationJournal write no success record and do not modify laws. Two sequential activations record the intervening GraphVersion change. Artifact: verification/2026-09-08-checked-admit-proposal.txt

## Rule — CheckedAdmitProposal stale-mismatch

Ratified on `8620e2d` (SEMANTIC). Gate binding: `CheckedAdmitProposal` calls the existing `ProposalStore` / `Approved` / `ActivateProposal` path; it does not install.

```text
CheckedAdmitProposal stale-mismatch rule:
  origin identity mismatch against coordinator SnapshotIdentity
  emits AdmissionStaleLabel and refuses install
  no silent relabel — the mismatch is the finding, not a bug to route around
  this closes the class where a worker's proposal, generated against an
  earlier snapshot, would otherwise install against a drifted coordinator
```

Compare is semantic (`M.Compare` on reconstructed Char identities), not `IdentityCompare`. Missing origin or coordinator digest is `AdmissionRejectedLabel`, not stale. Observation journals remain behavioral-null at both `SerialAdmitProposal` and `CheckedAdmitProposal`.

Hold: INT two-shard suite + successor tag to `shared-7cf6394` before measurements count. No CONVERGE this cut.

## INT ruling — RETIRE-IS-ENOUGH (recorded)

```text
ruling: RETIRE-IS-ENOUGH
mechanism: RetireLaw / UnretireLaw (Step 33)
test: shared_sibling_independence_via_retirement_test
authority: this file
```

RetireLaw / UnretireLaw are the covering selective ablation for concurrency-sourced laws. The learned-memory mask remains absent; it was not implemented. Sibling independence is tested by retiring Worker A's law while Worker B stays active, then unretiring A.

## Finding — learned-memory mask does not cover SerialAdmitProposal laws

Inspected 2026-09-07 on `56a5fc6` (base `shared-7cf6394`). No code change for a workaround.

```text
question: does the learned-memory mask disable/enable cover laws
          admitted via SerialAdmitProposal?
answer: no — the mask is not present on this lineage
```

Locus of absence:

- `research.py` absent (already indexed)
- `graph.py`: no `Disable`, `Enable`, `Mask`, `Learned` class
- `workers.py`: no mask, no disable
- `labels.py`: no Learned* constructor
- no named module for learned-memory mask or rent/counterfactual
  (`protocol/research_protocol.md` already records this)

What SerialAdmitProposal-admitted laws can do today:

- install through the existing approval gate (`ActivateProposal`)
- vanish together on restore to the base `GraphVersion` (full reset;
  `shared_serial_admit_proposal_ablation_test`)
- return together on re-mine through the same admit+activate path

What they cannot do:

- per-artifact disable/enable via the learned-memory mask
- therefore sibling independence as stated (ablate worker A's law,
  worker B's law still fires) cannot be tested on this cut

Adjacent machinery that is not the mask:

- `RetireLaw` / `UnretireLaw` (Step 33) append a `Retired` mark on one
  installed law and leave other installed laws active. That is
  retirement, not mask disable/enable/reset.

INT later ruled RETIRE-IS-ENOUGH. Sibling independence is covered by
that mechanism (`shared_sibling_independence_via_retirement_test`).
The mask remains absent; it is not required for this item.

CONVERGE is unrelated and still waits on pool warming / snapshot reuse.

## Deferred

joint-set rent gate; old-subsystem replacement; full snapshot restore
inside the worker; Wave 1.
