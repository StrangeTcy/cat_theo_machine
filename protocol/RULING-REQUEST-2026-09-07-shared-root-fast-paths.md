# RULING REQUEST — shared-root fast paths (INT)

Date: 2026-09-07 · Requested by: Layer-D lane · Branch tip at request time: `120e316` (contains `327a263`)

## Question

`_search_compare_enable_shared_root_fast_paths` is `M.false_value` at every
construction site in the repo (`graph.py:43`, `main.py:835`,
`search/runtime.py:35,561`, `search/compare_subprocess.py:717`). It gates the
whole shared-root-wave lane (`_comparison_states_need_shared_root_wave` →
`_comparison_prepare_shared_root_wave` → `_comparison_cache_shared_root_candidates`),
and it is the exact locus of the still-red parked test
`compare_search_modes_fill_warms_resident_pool_before_root_wave_test`, which
asserts pool-warming the disabled lane cannot produce. One ruling decides the
test's fate.

## Options

**A — keep off-by-default (status quo).**
The red stays a known-red of the parked C1 line (SHARED REVIVE-LATER).
Zero semantics change; Layer-D keeps its milestone-1 land untouched (the
driver rides `_spawn_parallel_executor` + `SearchRootWaveShardPacket`
directly, never through the lane). Cost: one permanently-red test needs a
ledger disposition ("waived while parked" or "rewrite to assert the
independent path") so suite reports keep meaning something.

**B — enable under explicit compare mode only.**
Set the flag from the operator/console entry into `compare_search_modes`
(nothing else), so `fill_warms` goes green where the feature is actually in
force. Semantics change is scoped but REAL: it switches `_compare_all_modes`
from the independent path to the shared path (compare.py:178-180), which
changes measured behaviour → per LAUNCH-PLAN this needs the
semantic-change cycle: suite on the integration candidate, new tag, operator
blank-control rerun. Wall-time and aggregate-work deltas are then measurable
— that is the lane's promised payoff (shared root candidates computed once,
reused by every mode) and also its risk (one poisoned candidate set
contaminates all modes).

**C — converge into the workers line later.**
Fold the shared-root wave into the resident-executor protocol this lane is
already building (the milestone-1 driver's `SearchRootWaveShardPacket` IS the
wave transport), and retire the flag with the parked lane: one path, workers
own root-wave sharding, `fill_warms` gets rewritten against the new locus at
the milestone-2 join/admission commit. No measurement semantics change today;
the red remains open until that land.

## Recommendation

C, with A as the interim ledger posture (red recorded as parked-lane, not a
Layer-D regression — Part 5 of `verification/2026-09-06-layer-d-milestone1.txt`
carries the unchanged-shape probe). B only if INT wants the perf claim
measured before the workers line absorbs the lane.

## Not asked / not implied

No default flip, no test deletion, no phase-gate papering (all three would
be green-by-circumvention and are declined in advance). This request changes
no code; the next Layer-D commit stays milestone-2 (journal split:
OBSERVATIONS vs PROPOSALS) unless INT rules B first.
