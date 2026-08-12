# Refactoring plan: `search/compare.py` (6,536 lines → ~11 focused modules)

## Diagnosis

`CompareSearchModes` is a single `M.Edge` subclass with ~380 methods covering at least ten
distinct responsibilities: console control, nat arithmetic shims, comparison-state records,
attempt ranking, semantic/progress reporting, rule matching + root fast paths, tree merging,
packet scheduling, resident-executor pool management, and the independent-subprocess race.
Everything is reachable only through `self`, so the class can be split **without changing a
single call site, signature, or behavior**.

## Approach: mixin decomposition (verbatim method moves)

Split the class into mixin classes, one per responsibility, each in its own module under
`search/`. `compare.py` keeps the public class and composes them:

```python
class CompareSearchModes(
    _ComparisonConsoleMixin,
    _ComparisonNatMixin,
    _ComparisonStateMixin,
    _ComparisonAttemptMixin,
    _ComparisonSemanticsMixin,
    _ComparisonRuleMatchMixin,
    _ComparisonTreeMixin,
    _ComparisonPacketMixin,
    _ComparisonExecutorMixin,
    _ComparisonSubprocessMixin,
    M.Edge,
):
    ...
```

Why mixins and not anything else:

- Methods move **verbatim** — every internal call stays `self._x(...)`, so no call-site edits,
  no signature changes, no behavior drift.
- No module-level helper functions are introduced; everything remains a method on a class.
- No type inspection, no attribute probing, no dynamic dispatch tricks — plain inheritance
  resolved statically by the MRO.
- `core.py` is untouched; `M.Edge` remains the terminal base exactly as today.
- No monkeypatching: composition happens once, in the class statement.
- Instance state (`self.registry`, `self.graph`, `self.start`, `self.goal`, `self.rules`,
  `self.heuristic`, `self.signature`, `self._comparison_*` slots) keeps being initialized in
  `CompareSearchModes.__init__` in `compare.py`; mixins only read/write it through `self`.

## Module partition (by current line ranges)

| New module | Mixin | Contents (current lines) | ~Size |
|---|---|---|---|
| `search/compare_console.py` | `_ComparisonConsoleMixin` | Console input, stop listener, prompt parsing: `_comparison_console_input` … `_comparison_read_action`, `_mode_from_token`, `_mode_selected`, `_selected_modes_from_tokens` (323–438) | 120 |
| `search/compare_nat.py` | `_ComparisonNatMixin` | Nat/GMP shims: `_nat_text` (1130), `_gmp_atom` (673), `_succ_nat_local`, `_nat_add_local`, `_nat_max_local`, `_nat_min_local`, `_pred_nat_or_zero_local`, `_nat_sub_or_zero_local` (2856–3031), `_seconds_text` (247) | 320 |
| `search/compare_state.py` | `_ComparisonStateMixin` | Comparison-state record: `_comparison_state`, all `_comparison_state_*` accessors, `_comparison_state_unpack`, `_comparison_state_update`, `_comparison_state_status`, `_search_job_unpack_local`, mark/pause/resume/`_paused_comparison_job`, `_comparison_states`, `_comparison_state_for_mode`, `_replace_comparison_state`, `_comparison_all_finished`, `_count_states` (1931–2310, 2819–2854) | 420 |
| `search/compare_attempts.py` | `_ComparisonAttemptMixin` | Attempt construction & ranking: `_zero_proof_cost`, `_zero_search_cost`, `_mode_attempt_from_plan`, `_attempt_total_value`, `_attempt_better`, `_attempt_better_with_elapsed`, `_comparison_result_plan/derivation`, `_plan_from_derivation_steps`, `_comparison_state_attempt_or_current`, `_finished_attempts`, `_best_attempt_in_attempts`, `_best_finished_attempt(_text)`, `_attempt_summary_text`, `_attempts_summary_text`, `_attempt_ties_best`, `_best_attempt_modes_text`, `_best_attempt_mode_count` (457–565, 2311–2491) | 350 |
| `search/compare_semantics.py` | `_ComparisonSemanticsMixin` | Term/fact predicates and progress text: `_goal_signal_*`, `_term_*`, `_fact_*`, `_facts_*`, `_introduced_facts`, `_action_replacement*`, `_plan_has_*`, `_state_families/milestones/stage/semantic/progress/scheduler_text`, `_running_*`/`_finished_*` summaries, `_job_focus/prefix/progress_text`, `_comparison_eta_text`, `_comparison_live_process_budget(_text)`, `_comparison_total_queued/completed_packets`, `_comparison_initial_state(s)_text`, `_comparison_phase_text`, `_comparison_root_fast_path_result_text`, `_active_worker_focus_*`, `_queued_focus_*`, `_mode_best_live_state`, `_first_goal_signal_in_packets` (204–321, 1142–1930, 2054–2111) | 950 |
| `search/compare_rules.py` | `_ComparisonRuleMatchMixin` | Rule matching & shared-root fast paths: `_knowledge_has_fact`, `_premises_satisfied_by_bindings`, `_match_premises`, `_match_premise_against_facts`, `_direct_next_term`, `_comparison_goal_reached`, `_comparison_rule_anchor`, `_comparison_anchor_matches_facts`, `_comparison_candidate_rules_for_knowledge`, `_find_goal_instantiating_plan`, `_find_immediate_rule_plan`, `_derivation_reaches_goal`, `_comparison_cached_derivation_plan`, `_comparison_schema_derivation_plan`, `_comparison_root_fast_path_result/state`, `_comparison_states_after/with_root_fast_path_result`, `_comparison_root_result_text`, `_comparison_success_job` (2525–2817) | 300 |
| `search/compare_trees.py` | `_ComparisonTreeMixin` | Visited/registry tree ops: `_tree_contains/_tree_lookup_fact/_tree_insert`, `_comparison_filter_new_child`, `_collect_map_entries`, `_collect_legacy_map_entries`, `_merge_tree_entries_*`, `_merge_legacy_entries_to_patricia`, `_merge_tree`, `_mode_uses_global_visited`, `_search_mode_uses_global_visited`, `_initial_compare_job_visited` (2493–2523, 3033–3210) | 210 |
| `search/compare_packets.py` | `_ComparisonPacketMixin` | Packet model, splitting, queueing, integration: `_decode_parallel_worker_payload` + `_decoded_*`, `_astar_*`, `_merge_frontier`, `_merge_compare_jobs`, `_integrate_parallel_*`, `_drained_parallel_result*`, `_job_frontier_size_nat`, `_take/_drop_frontier_packet`, `_split/_drain_compare_job_packet(s)`, `_merge_pending_packets`, backlog targets, `_comparison_packet_*`, `_comparison_ready_packets_*`, `_comparison_batch_ready_packets`, `_drop_exhausted/prunable_pending_packets`, seed/expand rule wave (`_comparison_seed_rule_wave`, `_comparison_expand_*`), `_comparison_packetize_job_frontier`, `_comparison_rebuild_packetized_job`, `_comparison_expand_job_packets`, `_packet_queue_from_job`, `_comparison_state_enqueue_job_frontier`, `_comparison_states_enqueue_all_packets`, prunable/dispatchable selection, `_worker_baseline/_worker_setup/_worker_problem_packet`, `_comparison_packet_budget`, `_comparison_packet_job_for_state`, shared-root candidate caching (`_comparison_cache_shared_root_candidates` … `_comparison_apply_shared_root_wave`), `_fresh_compare_job` (2504), `_beam_width` (439) (3062–5208 minus tree/nat blocks) | 1,700 |
| `search/compare_executors.py` | `_ComparisonExecutorMixin` | Resident executor pool + worker entries + root-wave shards: `_resident_executor*`, `_worker_entry*`, `_oldest_active_worker_entry`, `_worker_entry_count`, `_idle_executor_count`, `_spawn_parallel_executor`, `_await_parallel_executor_ready`, `_start/_grow/_shutdown/_retire` pool, `_kill_parallel_worker_entry`, `_parallel_launch_result_*`, `_dequeue/_collect_parallel_worker_launches`, `_start/_fill_parallel_workers`, `_first_finished_worker`, terminate/requeue/signal/join/pause worker methods, `_sync/_clear_graph_live_compare_snapshot`, root-wave shard machinery (`_root_wave_*`, `_comparison_rule_wave_shards`, `_comparison_root_candidate_rules(_parallel)`, `_spawn_root_wave_replacement_executor`, `_terminate_root_wave_shard_workers`, `_merge_root_wave_shard_results`) (3889–4230, 5210–6005) | 1,150 |
| `search/compare_subprocess.py` | `_ComparisonSubprocessMixin` | Independent per-mode subprocess race: `_fresh_independent_mode_runtime`, `_independent_mode_attempt`, `_comparison_main_script_path`, manifest write/path, `_mode_worker_token`, `_reason_atom`, `_fabricate_worker_failure_attempt`, `_performance_*`, `_is_heuristic_performance`, `_loaded_worker_attempt_is_final`, `_worker_failure_from_partial_attempt`, `_load_search_worker_snapshot`, `_relay_search_worker_output`, `_log_independent_mode_finish`, `_approval_to_materialize_best_attempt`, `_finalize_independent_mode_attempts`, `_compare_all_modes_independent(_parallel)` (479–493, 567–1128) | 580 |
| `search/compare.py` (kept) | `CompareSearchModes` | `__init__`, `__call__`, `_compare_all_modes` main loop (6006–6483), `_reverse`, `_mode_chain(_text)`, `_selected_modes_text`, `_comparison_has_usable_best_attempt`, `_comparison_should_rerun`, `_heuristic_for_mode`, `_comparison_uses_shared_root_fast_paths`, `sync_from_namespace` | 750 |

Every module lands in the 120–1,700 line range; the two large ones (`compare_packets`,
`compare_executors`) are internally cohesive & can be split again later along the
already-visible seams (packet model vs. result integration; executor pool vs. root-wave shards) once this pass has settled.

## Mechanics (behavior-preserving rules)

1. **Move verbatim.** Cut each method block unchanged — same names, same signatures, same
   defaults (`M.EmptyList`, `M.false_value`), same `_debug` strings. No logic edits in this pass.
2. **Per-module import header.** Each new module reproduces exactly the imports its methods
   need, following the existing header of `compare.py` (`from .. import machine as M`,
   `from ..heuristics import *`, `from ..labels import *`, `from ..proof import *`,
   `from ..proof import _debug, _debug_term`, `from .chain_utils import *`,
   `from .engine import *`, `from .model import *`, `from .patricia import *`, plus stdlib
   `time`/`os`/`sys`/`subprocess`/`threading`/`tempfile`/`json`/`queue`/`multiprocessing`
   where used). Trim per module to what the moved methods reference.
3. **Label injection.** Each new module gets its own `sync_from_namespace(namespace)` mirroring
   the one at the bottom of `compare.py`, listing only the labels its methods reference
   (`SearchSuccessLabel`, `DFSLabel`, phase/result labels, etc.). This is the established
   convention in every `search/` module — the runtime injects constructor labels through it.
4. **Register modules.** Add the new module names to `_SEARCH_MODULES` in
   `search/__init__.py` (it is a tuple; extend the tuple literal) **before** `"compare"`, so
   label sync reaches the mixins before the composing module resolves attributes. `modes.py`
   and `api.py` need no changes.
5. **Deferred imports stay put.** `_fresh_independent_mode_runtime` imports
   `.runtime._SearchWorkerRuntime` inside the method body, `_independent_mode_attempt` imports
   `.api.Search`, and `_load_search_worker_snapshot` imports `..main` / `..persistence` —
   keep these method-local imports exactly where they are (they break import cycles).
6. **Module-level side effects stay in `compare.py`.** The `copyreg` import (and anything
   registered at import time) remains in `compare.py` so import order is unchanged.
7. **Public surface unchanged.** `CompareSearchModes` keeps living in `search.compare`; the
   package `__getattr__` in `search/__init__.py` continues to resolve it. `runtime.py`'s reads
   of `graph._search_compare_live_*` are untouched because `_sync_graph_live_compare_snapshot`
   moves verbatim.

## Constraint compliance

- `core.py` untouched; `M.Edge` inheritance chain unchanged.
- No monkeypatching, no `__new__`, no class-hierarchy inspection of any kind.
- No module-level helper functions added — every moved unit remains a method on a mixin class;
  each module's `sync_from_namespace` already exists as the package-wide convention and is replicated, not invented.
- No new lists/dicts/Python bools: methods move as-is; the tuple in `_SEARCH_MODULES` stays a
  tuple. (The pre-existing `dict`/`list` usage inside `_compare_all_modes_independent_parallel`
  and the executor code is left exactly as it is today — this pass moves code, it does not
  rewrite it.)
- No `global` statements introduced anywhere.

## Suggested order of moves (each step leaves the suite green)

1. `compare_nat.py` (zero dependencies on other mixins — pure leaf).
2. `compare_console.py` (depends only on labels + `ui.py` imports it already has).
3. `compare_trees.py`, then `compare_state.py` (state accessors depend on nat only).
4. `compare_attempts.py`, `compare_rules.py`, `compare_semantics.py`.
5. `compare_packets.py`, `compare_executors.py`, `compare_subprocess.py`.
6. Final pass: shrink `compare.py` to `__init__` + main loop + `__call__` + `sync_from_namespace`.

After each step, run the existing suite from the Anaconda Prompt:

```
python -m hyge.testsuite
python -m hyge.test_actual_searchdfs
```

(from the directory above `Q:\hyge`, since the package imports itself as `hyge.*` via
`PYTHONPATH` in its own worker launches).

## Follow-up candidates (separate passes, not this one)

- Collapse the triplicated digit ladder in `_succ_nat_local` / `_nat_add_local`
  / `_pred_nat_or_zero_local` into one small-nat resolution method on `_ComparisonNatMixin`
  (a method, not a free function), cutting ~150 lines of repetition.
- Split `compare_packets.py` along the packet-model / result-integration seam and
  `compare_executors.py` along the pool / root-wave seam once each stabilizes.
- The label-driven fact predicates in `compare_semantics.py` (`heron`, `quadratic`, `angles`
  families) are problem-domain-specific; a later pass could move them behind the heuristics
  module so the comparison engine stays domain-neutral.
