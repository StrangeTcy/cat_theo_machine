# Pre-flight report — 2026-09-04

Session branch: `arena/01a064d5-cat-theo-machine`. Base: `41e80785d4de090337a9dfc08439f2fcb45915dc`
(tip of `arena/01a00f6b-cat-theo-machine` at fetch time; shallow checkout, widened to
depth 12 for lineage questions during this pre-flight).

## Remote state recorded before work

- origin HEAD: `428ecdc146e38de3481222bed7bddeb3c08e1b2d`
- `arena/01a00f6b-cat-theo-machine`: `41e80785` (equals local base)
- `arena/01a064d5-cat-theo-machine`: absent on origin before this turn; created by this turn's push
- Frozen-line tags visible on origin at start: `experiment-4-frozen`, `experiment-5-frozen`,
  `experiment-5-frozen-r1`, `preflight-shard-cursor-gate`

## Lineage mismatch against the charter's referenced machinery

The charter text references `research.py`, `provenance.py`, `explanation.py`,
`LearnedMemoryCheckpointTest`, a `rule:`/`fact:` teaching path, `research_protocol.md`,
and an FLT goal term with a negative-control decoy. None of these exist in this
checkout (greps recorded during this run). That machinery belongs to a sibling lineage
(`b905bff` / `arena/01a06274-...`), not to this branch's history. Pre-flight items were
executed to the extent this tree admits; the remainder is ledgered below as blocked on
lineage, not silently skipped.

## Pre-flight item 1 — swallowed exception

Target absent: no `LearnedMemoryCheckpointTest` in this tree, so the size-vs-content
discriminating experiment has no subject here. What the full-suite run surfaced instead
is the same failure class (a hidden fault detonating the suite) at a different locus;
see defect ledger D1/D2.

## Pre-flight item 2 — producer/consumer compile and selection

The protocol document that defines the `nosolutions` producer/consumer pair is absent
from this lineage, so the exact A1 rules cannot be reconstructed here. Stand-in rules
were built and driven through the live path (`probes/preflight_item2_multirule.py`):

- producer (two premises) and consumer (two premises) both compile through
  `CompileMultiRuleToLaw` (law != EmptyList): **compile half verified**
- toy goal term `ExprEq(Add(?x, one), ?x)` builds and its head label is `ExprEqLabel`
- selection half: with the two rules as the entire SearchDFS pool over ground instances
  of the `x+1=x` shape, the pool is admitted, compiled into the search job, and the
  start state is expanded (`expanded: 1`); no successor was generated from the states
  tried (`generated: 0`), so the candidate-partial-match witness is **open**, locus
  `search/engine.py` `_SearchStepKernel` premise matching.

## Pre-flight item 3 — decoy shape-match

Not runnable: no FLT goal term and no decoy exist anywhere in this tree (grep for
Fermat/FLT over py/yaml/md returns nothing). Blocked on lineage.

## Pre-flight item 4 — full two-shard suite

Runner: `tools/shard_suite.py <i> 2`, `PYTHONPATH=/home/user`, system Python 3.11.2,
gmpy2 + pyyaml installed (`pip install --break-system-packages`, per the recovery
recipe; not conda).

Before the fix (base `41e80785` as checked out):

- Shard 0: completed, 368s. Failures (3): `converse_default_mode_test`,
  `tree_insert_deep_pair_lookup_avoids_recursion_test`,
  `compare_search_modes_fill_warms_resident_pool_before_root_wave_test`
- Shard 1: **aborted during `install_default_tests`** — AttributeError at
  `testsuite.py:7448` in `ConversePropositionTest.__init__`
  (`'Thingy' object has no attribute 'tail'`); every shard-1 test after it never
  registered. The same crash reproduces at parent commit `227ddf7` (worktree run),
  so both defects below predate this branch's base commit.

After the D1 fix (this turn's commit):

- Shard 0: completed, 363s. Failure set unchanged (3, same names).
- Shard 1: completed, 477s. Failures (4):
  `heuristic_canonical_knowledge_agreement_test`, `converse_proposition_test`,
  `curator_report_test`,
  `compare_search_modes_finds_reusable_worker_snapshot_dir_test`

The recorded suite failure set at the tagged pre-flight state is these 7 tests.

## Defect ledger (found by running, this pre-flight)

1. **D1 — ConversePropositionTest navigates before it guards** (locus
   `testsuite.py`, `ConversePropositionTest.__init__`). The test read
   `Tail^4` off each Converse outcome unconditionally and checked
   `UnderstoodLabel` only afterwards; any NotUnderstood/Ambiguous outcome
   (three-slot term) raised during suite install and took the whole shard down.
   Instrument-level. Fixed this turn: the three UnderstoodLabel guards now run
   before any navigation; a non-Understood outcome fails the test instead of
   aborting the suite. The neighboring `_understood_words` helper in the same
   file already used the correct order; this test was the outlier.
2. **D2 — canonical equality sentence gets no correspondence** (locus
   `graph.py` `Converse` / `ConverseInterpretations` /
   `DefaultCorrespondenceVocabulary`). `Converse` on
   "is two plus two equal to four" returns `NotUnderstood` with
   `ReasonNoCorrespondenceLabel` while `SurfaceUnknownWords` reports every word
   known (probe `probes/preflight_converse_outcome.py`). Machine-level, root
   cause not yet isolated; likely the same family as shard 0's
   `converse_default_mode_test` failure. Open.
3. Five further red tests recorded as the working set, undiagnosed so far:
   `tree_insert_deep_pair_lookup_avoids_recursion_test`,
   `compare_search_modes_fill_warms_resident_pool_before_root_wave_test`,
   `heuristic_canonical_knowledge_agreement_test`, `curator_report_test`,
   `compare_search_modes_finds_reusable_worker_snapshot_dir_test`.

## Instrumentation corrections (this session's own)

- An earlier probe walked `Tail(outcome)` believing it held the unknown-word list;
  it held the surface sentence. Corrected navigation: the reason term is
  `Head(Tail(Tail(outcome)))`. The committed probe uses the corrected path.
- `knowledge_selftest.py` and `probes/tao_dfs_probe.py` import a stale `hyge.*`
  namespace and do not run against the current tree; noted, not fixed this turn.

## Artifacts

- `probes/preflight_converse_outcome.py` — D2 evidence (rerunnable)
- `probes/preflight_item2_multirule.py` — item-2 evidence (rerunnable)
- Raw shard logs: `/tmp/probe/shard0.log`, `/tmp/probe/shard1.log` (before),
  `/tmp/probe/shard0_v2.log`, `/tmp/probe/shard1_v2.log` (after) — ephemeral,
  summarized above
- Tag cut after the code change: `preflight-converse-outcome-guard`
