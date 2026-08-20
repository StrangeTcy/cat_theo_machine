from __future__ import annotations

import copyreg
import json
import multiprocessing
import os
import queue
import subprocess
import sys
import tempfile
import threading
import time

from .. import machine as M
from .. import heuristics as Hmod
from .. import labels as Lmod
from .. import proof as Pmod
from .. import context as Ctxmod
from .. import schemata as Smod
from .. import gmprep as Gmpmod
from .. import trees as Tmod
from .. import wire as Wmod
from .. import logic as Logicmod
from ..heuristics import *
from ..labels import *
from ..proof import *
from ..proof import _debug, _debug_term
from .chain_utils import *
from .engine import *
from .compare_console import _ComparisonConsoleMixin
from .compare_nat import _ComparisonNatMixin
from .compare_trees import _ComparisonTreeMixin
from .compare_state import _ComparisonStateMixin
from .compare_attempts import _ComparisonAttemptMixin
from .compare_rules import _ComparisonRuleMatchMixin
from .compare_semantics import _ComparisonSemanticMixin
from .compare_subprocess import _ComparisonSubprocessMixin
from .compare_packets import _ComparisonPacketMixin
from .compare_executors import _ComparisonExecutorMixin
from .engine import _SearchStepKernel
from .model import *

# A live daemon fans out at the same time as a foreground comparison, so the
# comparison layer takes a share of the one host budget instead of claiming
# every core for itself.
COMPARISON_BUDGET_CLAIMANTS = 2
from .patricia import *
from .ui import _SearchComparisonPromptGuard, _SearchConsoleInput, _SearchStopConsole








class CompareSearchModes(_ComparisonConsoleMixin, _ComparisonNatMixin, _ComparisonTreeMixin, _ComparisonStateMixin, _ComparisonAttemptMixin, _ComparisonRuleMatchMixin, _ComparisonSemanticMixin, _ComparisonSubprocessMixin, _ComparisonPacketMixin, _ComparisonExecutorMixin, M.Edge):
    def __init__(self, graph, start, goal, rules, heuristic, registry):
        t0 = time.time()
        self.graph = graph
        self.start = HeuristicCanonicalize(start, heuristic, registry)()
        self.goal = HeuristicCanonicalize(goal, heuristic, registry)()
        self.rules = rules
        self.heuristic = heuristic
        self.registry = registry
        self._stop_listener = None
        self._current_worker_process_budget = M.Zero
        self._comparison_mp_context = None
        self._comparison_shared_root_candidates_ready = M.false_value
        self._comparison_shared_root_candidates = M.EmptyList
        self._comparison_shared_root_candidate_count = M.Zero
        self._comparison_root_wave_idle_executors = M.EmptyList
        self._comparison_machine_parallelism = M.four
        try:
            host_parallelism = Wmod.share_process_budget(COMPARISON_BUDGET_CLAIMANTS)
            if host_parallelism <= 1:
                self._comparison_machine_parallelism = M.one
            elif host_parallelism == 2:
                self._comparison_machine_parallelism = M.two
            elif host_parallelism == 3:
                self._comparison_machine_parallelism = M.three
            elif host_parallelism == 4:
                self._comparison_machine_parallelism = M.four
            elif host_parallelism == 5:
                self._comparison_machine_parallelism = M.five
            elif host_parallelism == 6:
                self._comparison_machine_parallelism = M.six
            elif host_parallelism == 7:
                self._comparison_machine_parallelism = M.seven
            elif host_parallelism == 8:
                self._comparison_machine_parallelism = M.eight
            elif host_parallelism == 9:
                self._comparison_machine_parallelism = M.nine
            else:
                self._comparison_machine_parallelism = M.Atom()
                self._comparison_machine_parallelism.value = Gmpmod.GMPRep(str(host_parallelism))
        except Exception:
            self._comparison_machine_parallelism = M.four
        _debug("search-compare: init starting")
        # Prefer the graph-maintained next_rule_index as an O(1) rule count.
        # This avoids an expensive TreeLookup on the context tree.
        try:
            context_rule_count = graph.next_rule_index
        except AttributeError:
            context_rule_count = M.EmptyList
        _debug("search-compare: init fetched next_rule_index in {:.2f}s".format(time.time() - t0))
        if M.IdentityCompare(context_rule_count, M.EmptyList)() is M.false_value:
            # Some snapshots/pack-load paths may leave next_rule_index at Zero even
            # when rules are present. Never treat that as a real budget.
            _debug("search-compare: init checking next_rule_index != Zero in {:.2f}s".format(time.time() - t0))
            if M.NatEq(context_rule_count, M.Zero, self.registry)() is M.false_value:
                self._comparison_rule_count = context_rule_count
            else:
                _debug("search-compare: init counting rules (fallback) in {:.2f}s".format(time.time() - t0))
                rule_count_rep = M.CountRep(self.rules)()
                self._comparison_rule_count = M.Atom()
                self._comparison_rule_count.value = rule_count_rep
        else:
            _debug("search-compare: init counting rules (no next_rule_index) in {:.2f}s".format(time.time() - t0))
            rule_count_rep = M.CountRep(self.rules)()
            self._comparison_rule_count = M.Atom()
            self._comparison_rule_count.value = rule_count_rep
        _debug("search-compare: init got rule count in {:.2f}s".format(time.time() - t0))
        self.graph._last_search_comparison_outcome = SearchSuccessLabel
        self.saved_derivations = M.FromContextGetDerivations(graph)()
        self.saved_schemata = M.FromContextGetDerivationSchemata(graph)()
        self._comparison_packet_token = M.Zero
        self.signature = SearchSignatureForProblem(self.start, self.goal, registry)()
        self._comparison_generation = self.signature

        _debug("search-compare: init computing signature in {:.2f}s".format(time.time() - t0))
        existing = LookupSearchComparison(self.signature, M.FromContextGetSearchComparisons(graph)())()
        _debug("search-compare: init looked up existing comparison in {:.2f}s".format(time.time() - t0))
        paused_job = LookupSearchComparisonJob(self.signature, M.FromContextGetSearchComparisonJobs(graph)())()
        _debug("search-compare: init looked up paused job in {:.2f}s".format(time.time() - t0))
        if (
            M.Compare(paused_job, M.EmptyList)() is M.false_value
            or M.Compare(existing, M.EmptyList)() is M.truth_value
            or self._comparison_should_rerun(existing) is M.truth_value
        ):
            _debug("search-compare: init entering compare_all_modes after {:.2f}s".format(time.time() - t0))
            compared = self._compare_all_modes(paused_job)
            comparison = M.Head(compared)()
            best_attempt = M.Head(M.Tail(compared)())()
            if M.Compare(comparison, M.EmptyList)() is M.truth_value or M.Compare(best_attempt, M.EmptyList)() is M.truth_value:
                self.result = M.Pair(M.EmptyList, M.Pair(M.EmptyList, M.EmptyList))
            else:
                self.result = M.Pair(comparison, M.Pair(best_attempt, M.EmptyList))
        else:
            best_attempt = SearchComparisonBestAttempt(existing)()
            if M.Compare(best_attempt, M.EmptyList)() is M.truth_value:
                self.result = M.Pair(M.EmptyList, M.Pair(M.EmptyList, M.EmptyList))
            else:
                self.result = M.Pair(existing, M.Pair(best_attempt, M.EmptyList))

        super().__init__(
            inputs=M.Pair(
                graph,
                M.Pair(
                    start,
                    M.Pair(goal, M.Pair(rules, M.Pair(heuristic, M.Pair(registry, M.EmptyList)))),
                ),
            ),
            results=self.result,
        )

    def _reverse(self, chain, acc):
        remaining = chain
        reversed_chain = acc
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            reversed_chain = M.Pair(M.Head(remaining)(), reversed_chain)
            remaining = M.Tail(remaining)()
        return reversed_chain

    def _comparison_uses_shared_root_fast_paths(self):
        return M.IdentityCompare(self.graph._search_compare_enable_shared_root_fast_paths, M.truth_value)()

    def _compare_all_modes(self, paused_job=M.EmptyList):
        if self._comparison_uses_shared_root_fast_paths() is M.false_value:
            return self._compare_all_modes_independent(paused_job)
        _debug("search-compare: benchmarking all current search modes for this problem family")
        compare_started_at = time.time()
        prior_guard = self.graph._search_comparison_prompt_guard
        prior_ignore_root_fast_paths = self.graph._search_compare_ignore_root_fast_paths
        prior_root_start = self.graph._search_compare_root_start
        prior_root_goal = self.graph._search_compare_root_goal
        self._comparison_prompt_guard = _SearchComparisonPromptGuard()
        self.graph._search_comparison_prompt_guard = self._comparison_prompt_guard
        self.graph._search_compare_ignore_root_fast_paths = M.false_value
        self.graph._search_compare_root_start = self.start
        self.graph._search_compare_root_goal = self.goal

        workers = M.EmptyList
        idle_executors = M.EmptyList
        mp_context = None
        states = M.EmptyList
        comparison_outcome = SearchSuccessLabel
        try:
            modes = self._mode_chain()
            if M.Compare(paused_job, M.EmptyList)() is M.truth_value:
                _debug("search-compare: initializing mode states...")
                states = self._comparison_states(modes)
                _debug("search-compare: initialized mode states in {:.2f}s".format(time.time() - compare_started_at))
                # Start multiprocessing immediately so parallel executors exist
                # during benchmarking (even if fast paths later resolve early).
                _debug("search-compare: initializing multiprocessing context...")
                mp_context = multiprocessing.get_context("spawn")
                self._comparison_mp_context = mp_context
                idle_executors = self._start_parallel_executor_pool(mp_context)
                _debug("search-compare: growing resident executor pool (pre-fast-path)...")
                idle_executors = self._grow_parallel_executor_pool(mp_context, idle_executors, states, workers)
                _debug(
                    "search-compare: resident executor pool ready (idle="
                    + self._nat_text(self._idle_executor_count(idle_executors))
                    + ") after {:.2f}s".format(time.time() - compare_started_at)
                )

                _debug("search-compare: applying shared-root fast-paths...")
                self._comparison_root_wave_idle_executors = idle_executors
                states = self._comparison_states_after_root_fast_paths(states)
                idle_executors = self._comparison_root_wave_idle_executors
                _debug("search-compare: shared-root fast-paths done after {:.2f}s".format(time.time() - compare_started_at))
            else:
                _debug("search-compare: resuming paused comparison")
                states = self._comparison_resume_states(SearchComparisonJobStates(paused_job)())
            _debug("search-compare: removing stale paused comparison job if present")
            self.graph.remove_search_comparison_job(self.signature)
            _debug("search-compare: comparison job cleanup done")
            prompt_window_seconds = float(self._comparison_prompt_guard.time_prompt_step_seconds)
            _debug("search-compare: checking whether all mode states are already finished")
            _debug(
                "search-compare: all modes are searching for a derivation from "
                + _debug_term(self.start, self.registry)
                + " to "
                + _debug_term(self.goal, self.registry)
            )
            _debug("search-compare: initial raw states " + self._comparison_initial_states_text(states))
            self._sync_graph_live_compare_snapshot(states, workers, idle_executors)
            all_finished = self._comparison_all_finished(states)
            _debug("search-compare: initial all-finished check returned " + SearchStatusText(all_finished)())
            if M.IdentityCompare(all_finished, M.truth_value)() is M.truth_value:
                _debug("search-compare: all-finished predicate says yes")
            else:
                _debug("search-compare: all-finished predicate says no")
            if M.IdentityCompare(all_finished, M.truth_value)() is M.truth_value:
                _debug(
                    "search-compare: initial state summary before packet search says finished="
                    + self._finished_states_summary(states)
                    + "; running="
                    + self._running_states_summary(states)
                )
                _debug("search-compare: shared root fast path resolved all modes before packet search")
            else:
                # mp_context + idle_executors are already initialized above for
                # the new-comparison (non-resume) path.
                if mp_context is None:
                    mp_context = multiprocessing.get_context("spawn")
                    self._comparison_mp_context = mp_context
                    idle_executors = self._start_parallel_executor_pool(mp_context)
                _debug("search-compare: starting console pause listener setup")
                self._start_stop_listener()
                _debug("search-compare: console pause listener setup finished")
                _debug("search-compare: starting parallel mode race")

                filled = self._fill_parallel_workers(mp_context, idle_executors, states, M.EmptyList)
                states = M.Head(filled)()
                workers = M.Head(M.Tail(filled)())()
                idle_executors = M.Head(M.Tail(M.Tail(filled)())())()
                self._sync_graph_live_compare_snapshot(states, workers, idle_executors)

                _debug(
                    "search-compare: leasing "
                    + self._nat_text(self._current_worker_process_budget)
                    + " resident executors for the current branch backlog"
                )
                _debug(
                    "search-compare: "
                    + self._comparison_live_process_budget_text(states, workers)
                    + " for "
                    + self._mode_chain_text(modes)
                )

            phase_deadline = time.time() + prompt_window_seconds
            next_progress_report = time.time() + 1.0

            while M.IdentityCompare(self._comparison_all_finished(states), M.truth_value)() is M.false_value:
                self._sync_graph_live_compare_snapshot(states, workers, idle_executors)
                action, selected_modes = self._consume_console_action()
                if action == "stop":
                    _debug("search-compare: operator stopped comparison")
                    comparison_outcome = SearchAbortedByUserLabel
                    states = self._comparison_mark_unfinished_states(states, SearchAbortedByUserLabel)
                    self._terminate_parallel_workers(workers)
                    workers = M.EmptyList
                    self._sync_graph_live_compare_snapshot(states, workers, idle_executors)
                    break

                if action == "pause":
                    _debug("search-compare: operator paused comparison")
                    comparison_outcome = SearchPausedLabel
                    states = self._pause_parallel_workers(states, workers)
                    workers = M.EmptyList
                    states = self._comparison_pause_states(states)
                    self.graph.store_search_comparison_job(self._paused_comparison_job(states, comparison_outcome))
                    self._sync_graph_live_compare_snapshot(states, workers, idle_executors)
                    break

                if action == "stop_mode":
                    _debug("search-compare: operator stopped " + SearchModeText(selected_modes)())
                    comparison_outcome = SearchAbortedByUserLabel
                    states = self._comparison_mark_mode_outcome(states, selected_modes, SearchAbortedByUserLabel)
                    terminated = self._terminate_parallel_workers_for_mode(
                        mp_context,
                        workers,
                        idle_executors,
                        selected_modes,
                        M.EmptyList,
                    )
                    workers = M.Head(terminated)()
                    idle_executors = M.Head(M.Tail(terminated)())()
                    self._sync_graph_live_compare_snapshot(states, workers, idle_executors)
                    phase_deadline = time.time() + prompt_window_seconds
                    next_progress_report = time.time() + 1.0
                    continue

                if action == "only_modes":
                    _debug("search-compare: operator kept only " + self._selected_modes_text(selected_modes))
                    comparison_outcome = SearchAbortedByUserLabel
                    states = self._comparison_mark_unselected_modes(states, selected_modes, SearchAbortedByUserLabel)
                    terminated = self._terminate_parallel_workers_not_selected(
                        mp_context,
                        workers,
                        idle_executors,
                        selected_modes,
                        M.EmptyList,
                    )
                    workers = M.Head(terminated)()
                    idle_executors = M.Head(M.Tail(terminated)())()
                    self._sync_graph_live_compare_snapshot(states, workers, idle_executors)
                    phase_deadline = time.time() + prompt_window_seconds
                    next_progress_report = time.time() + 1.0
                    continue

                if M.IdentityCompare(self._pause_requested(), M.truth_value)() is M.truth_value:
                    _debug("search-compare: console pause requested")
                    comparison_outcome = SearchPausedLabel
                    states = self._pause_parallel_workers(states, workers)
                    workers = M.EmptyList
                    states = self._comparison_pause_states(states)
                    self.graph.store_search_comparison_job(self._paused_comparison_job(states, comparison_outcome))
                    self._sync_graph_live_compare_snapshot(states, workers, idle_executors)
                    break

                if M.IdentityCompare(workers, M.EmptyList)() is M.truth_value:
                    filled = self._fill_parallel_workers(mp_context, idle_executors, states, workers)
                    states = M.Head(filled)()
                    workers = M.Head(M.Tail(filled)())()
                    idle_executors = M.Head(M.Tail(M.Tail(filled)())())()
                    self._sync_graph_live_compare_snapshot(states, workers, idle_executors)
                    if M.IdentityCompare(workers, M.EmptyList)() is M.truth_value:
                        if M.NatEq(self._comparison_total_queued_packets(states), M.Zero, self.registry)() is M.truth_value:
                            break
                        _debug(
                            "search-compare: branch wave still has "
                            + self._nat_text(self._comparison_total_queued_packets(states))
                            + " queued packets but no resident executors are available yet; waiting to retry"
                        )
                        time.sleep(0.05)
                        continue

                remaining_workers = workers
                finished = self._first_finished_worker(remaining_workers, M.EmptyList)
                entry = M.Head(finished)()

                if M.IdentityCompare(entry, M.EmptyList)() is M.truth_value:
                    now = time.time()

                    if now >= next_progress_report:
                        _debug(
                            "search-compare: scheduler progress "
                            + self._comparison_live_process_budget_text(states, workers)
                            + "; running "
                            + self._running_scheduler_summary(states)
                            + "; finished "
                            + self._finished_scheduler_summary(states)
                        )
                        _debug(
                            "search-compare: semantic progress goal="
                            + _debug_term(self.goal, self.registry)
                            + "; running "
                            + self._running_semantic_summary(states, workers)
                            + "; best finished so far "
                            + self._best_finished_attempt_text(states)
                            + "; "
                            + self._comparison_eta_text(states, workers)
                        )
                        next_progress_report = now + 1.0

                    if now >= phase_deadline:
                        elapsed_seconds = int(now - self._comparison_prompt_guard.started_at)
                        if elapsed_seconds < 0:
                            elapsed_seconds = 0
                        summary_text = (
                            "search-compare: "
                            + str(elapsed_seconds)
                            + "s elapsed; scheduler "
                            + self._comparison_live_process_budget_text(states, workers)
                            + "; semantic goal="
                            + _debug_term(self.goal, self.registry)
                            + "; best finished so far "
                            + self._best_finished_attempt_text(states)
                            + "; "
                            + self._comparison_eta_text(states, workers)
                        )
                        _debug(summary_text)
                        _debug(
                            "search-compare: scheduler detail running "
                            + self._running_scheduler_summary(states)
                            + "; finished "
                            + self._finished_scheduler_summary(states)
                        )
                        _debug(
                            "search-compare: semantic detail running "
                            + self._running_semantic_summary(states, workers)
                        )

                        _debug(
                            "search-compare: still running; enter pause | stop | stop <mode> | only <modes> in the console at any time"
                        )
                        phase_deadline = time.time() + prompt_window_seconds
                        next_progress_report = time.time() + 1.0
                        continue

                    time.sleep(0.01)
                    continue

                drained_any = M.false_value
                drained_results_rev = M.EmptyList
                while M.IdentityCompare(entry, M.EmptyList)() is M.false_value:
                    drained_any = M.truth_value
                    payload = M.Head(M.Tail(finished)())()
                    remaining_workers = M.Head(M.Tail(M.Tail(finished)())())()
                    mode = self._worker_entry_mode(entry)
                    slot_text = self._nat_text(self._worker_entry_slot(entry))
                    pid_text = str(self._worker_entry_process(entry).pid)
                    expected_packet_token = self._worker_entry_packet_token(entry)
                    decoded = self._decode_parallel_worker_payload(payload, mode, expected_packet_token)
                    returned_packet_token = self._decoded_packet_token(decoded)
                    if payload is not None and M.Compare(expected_packet_token, M.EmptyList)() is M.false_value:
                        if M.TermEqual(returned_packet_token, expected_packet_token)() is M.false_value:
                            _debug(
                                "search-compare: ignoring stale "
                                + SearchModeText(mode)()
                                + " packet result token="
                                + _debug_term(returned_packet_token, self.registry)
                                + " expected="
                                + _debug_term(expected_packet_token, self.registry)
                            )
                            states = self._requeue_worker_entry_for_retry(states, entry)
                            if self._worker_entry_process(entry).is_alive():
                                idle_executors = M.Pair(
                                    self._worker_entry_executor(entry),
                                    idle_executors,
                                )
                            self._sync_graph_live_compare_snapshot(states, remaining_workers, idle_executors)
                            next_progress_report = time.time() + 1.0
                            finished = self._first_finished_worker(remaining_workers, M.EmptyList)
                            entry = M.Head(finished)()
                            continue
                    if payload is None:
                        _debug(
                            "search-compare: resident executor "
                            + slot_text
                            + " pid="
                            + pid_text
                            + " finished "
                            + SearchModeText(mode)()
                            + " packet with no payload; requeueing original packet for resident retry"
                        )
                        states = self._requeue_worker_entry_for_retry(states, entry)
                        if self._worker_entry_process(entry).is_alive():
                            self._retire_parallel_executor(
                                self._worker_entry_executor(entry),
                                "retiring failed packet worker ",
                            )
                            _debug(
                                "search-compare: resident executor "
                                + slot_text
                                + " pid="
                                + pid_text
                                + " retired after failed "
                                + SearchModeText(mode)()
                                + " packet; live="
                                + self._nat_text(self._worker_entry_count(remaining_workers))
                                + " idle="
                                + self._nat_text(self._idle_executor_count(idle_executors))
                            )
                        else:
                            _debug(
                                "search-compare: packet worker "
                                + slot_text
                                + " pid="
                                + pid_text
                                + " exited after failed "
                                + SearchModeText(mode)()
                                + " packet"
                            )
                        self._sync_graph_live_compare_snapshot(states, remaining_workers, idle_executors)
                        next_progress_report = time.time() + 1.0
                        finished = self._first_finished_worker(remaining_workers, M.EmptyList)
                        entry = M.Head(finished)()
                        continue
                    else:
                        _debug(
                            "search-compare: resident executor "
                            + slot_text
                            + " pid="
                            + pid_text
                            + " finished "
                            + SearchModeText(mode)()
                            + " packet and returned "
                            + self._decoded_summary_text(decoded)
                        )
                    if self._worker_entry_process(entry).is_alive():
                        idle_executors = M.Pair(
                            self._worker_entry_executor(entry),
                            idle_executors,
                        )
                        _debug(
                            "search-compare: resident executor "
                            + slot_text
                            + " pid="
                            + pid_text
                            + " returned to the idle pool after completed "
                            + SearchModeText(mode)()
                            + " packet; live="
                            + self._nat_text(self._worker_entry_count(remaining_workers))
                            + " idle="
                            + self._nat_text(self._idle_executor_count(idle_executors))
                        )
                    else:
                        _debug(
                            "search-compare: packet worker "
                            + slot_text
                            + " pid="
                            + pid_text
                            + " already exited after completed "
                            + SearchModeText(mode)()
                            + " packet"
                        )
                    drained_results_rev = M.Pair(
                        self._drained_parallel_result(mode, decoded, expected_packet_token),
                        drained_results_rev,
                    )
                    finished = self._first_finished_worker(remaining_workers, M.EmptyList)
                    entry = M.Head(finished)()

                workers = remaining_workers
                if M.IdentityCompare(drained_any, M.truth_value)() is M.truth_value:
                    if M.IdentityCompare(drained_results_rev, M.EmptyList)() is M.false_value:
                        states = self._integrate_parallel_results(states, self._reverse(drained_results_rev, M.EmptyList))
                    filled = self._fill_parallel_workers(mp_context, idle_executors, states, remaining_workers)
                    states = M.Head(filled)()
                    workers = M.Head(M.Tail(filled)())()
                    idle_executors = M.Head(M.Tail(M.Tail(filled)())())()
                    self._sync_graph_live_compare_snapshot(states, workers, idle_executors)
                    next_progress_report = time.time() + 1.0
                    continue

            self._terminate_parallel_workers(workers)
            workers = M.EmptyList
            self._shutdown_idle_parallel_executors(idle_executors)
            idle_executors = M.EmptyList
            self._sync_graph_live_compare_snapshot(states, workers, idle_executors)

            if M.IdentityCompare(self._comparison_all_finished(states), M.false_value)() is M.truth_value:
                _debug(
                    "search-compare: comparison ended with unfinished modes; scheduler running "
                    + self._running_scheduler_summary(states)
                    + "; finished "
                    + self._finished_scheduler_summary(states)
                )
                _debug(
                    "search-compare: unfinished semantic progress goal="
                    + _debug_term(self.goal, self.registry)
                    + "; running "
                    + self._running_semantic_summary(states, workers)
                    + "; best finished so far "
                    + self._best_finished_attempt_text(states)
                )
                if M.IdentityCompare(comparison_outcome, SearchSuccessLabel)() is M.truth_value:
                    comparison_outcome = SearchFailureLabel
                    states = self._comparison_mark_unfinished_states(states, SearchFailureLabel)

            _debug("search-compare: building finished comparison attempts")
            _debug("search-compare: finished states " + self._finished_states_summary(states))
            attempts = self._finished_attempts(states, M.EmptyList)
            _debug("search-compare: attempts " + self._attempts_summary_text(attempts))
            _debug("search-compare: selecting best finished attempt")
            best_attempt = self._best_attempt_in_attempts(attempts, M.EmptyList)
            if M.Compare(best_attempt, M.EmptyList)() is M.false_value:
                tied_modes = self._best_attempt_modes_text(attempts, best_attempt)
                tied_mode_count = self._best_attempt_mode_count(attempts, best_attempt)
                if M.NatLess(M.one, tied_mode_count, self.registry)() is M.truth_value:
                    _debug(
                        "search-compare: best result is a tie between "
                        + tied_modes
                        + " at total="
                        + self._nat_text(TotalCostValue(SearchAttemptTotalCost(best_attempt)())())
                    )
                else:
                    _debug(
                        "search-compare: unique best mode "
                        + tied_modes
                        + " total="
                        + self._nat_text(TotalCostValue(SearchAttemptTotalCost(best_attempt)())())
                    )

            self.graph._replace_context(
                constructors=self.registry,
                derivations=self.saved_derivations,
                derivation_schemata=self.saved_schemata,
            )

            if M.Compare(best_attempt, M.EmptyList)() is M.truth_value and M.IdentityCompare(comparison_outcome, SearchSuccessLabel)() is M.truth_value:
                comparison_outcome = SearchFailureLabel

            comparison = SearchComparison(self.signature, attempts, best_attempt, comparison_outcome)()
            _debug("search-compare: storing completed comparison")
            self.graph.add_search_comparison(comparison)
            self.graph._last_search_comparison_outcome = comparison_outcome
            return M.Pair(comparison, M.Pair(best_attempt, M.EmptyList))
        except KeyboardInterrupt:
            if M.Compare(states, M.EmptyList)() is M.truth_value:
                raise
            _debug("search-compare: keyboard interrupt; pausing comparison")
            comparison_outcome = SearchPausedLabel
            states = self._pause_parallel_workers(states, workers)
            workers = M.EmptyList
            states = self._comparison_pause_states(states)
            self.graph.store_search_comparison_job(self._paused_comparison_job(states, comparison_outcome))
            self.graph._last_search_comparison_outcome = comparison_outcome
            self._sync_graph_live_compare_snapshot(states, workers, idle_executors)
            return M.Pair(M.EmptyList, M.Pair(M.EmptyList, M.EmptyList))
        finally:
            self._terminate_parallel_workers(workers)
            self._shutdown_idle_parallel_executors(idle_executors)
            self._stop_stop_listener()
            self._comparison_mp_context = None
            self.graph._search_compare_ignore_root_fast_paths = prior_ignore_root_fast_paths
            self.graph._search_compare_root_start = prior_root_start
            self.graph._search_compare_root_goal = prior_root_goal
            self.graph._search_comparison_prompt_guard = prior_guard
            self._clear_graph_live_compare_snapshot()

    def __call__(self):
        return self.result




def sync_from_namespace(namespace):
    for name in (
        "DFSLabel",
        "BFSLabel",
        "BeamLabel",
        "AStarLabel",
        "RewriteDFSLabel",
        "GoalHeadOrderLabel",
        "KnowledgeLabel",
        "ContextSearchComparisonJobsLabel",
        "ContextSearchJobsLabel",
        "SearchSignatureLabel",
        "SearchComparisonLabel",
        "SearchComparisonJobLabel",
        "SearchCostLabel",
        "SearchJobLabel",
        "SearchStateLabel",
        "SearchTheoremCursorLabel",
        "SearchRewriteCursorLabel",
        "SearchRewritePathFrameLabel",
        "SearchRewriteRuleBundleLabel",
        "SearchPairKeyLabel",
        "SearchCtorKeyLabel",
        "SearchPatriciaTokenLabel",
        "SearchPatriciaPairTokenLabel",
        "SearchPatriciaStopTokenLabel",
        "SearchPatriciaLeafLabel",
        "SearchPatriciaBranchLabel",
        "SearchPatriciaChoiceLabel",
        "SearchSuccessLabel",
        "SearchFailureLabel",
        "SearchRunningLabel",
        "SearchPausedLabel",
        "SearchTimedOutLabel",
        "SearchAbortedByUserLabel",
        "SearchRootFastPathPhaseLabel",
        "SearchPacketSearchPhaseLabel",
        "SearchNoRootFastPathLabel",
        "SearchRootCacheResultLabel",
        "SearchRootSchemaResultLabel",
        "SearchRootGoalResultLabel",
        "SearchRootImmediateResultLabel",
        "SearchRootWaveShardLaunchLabel",
    ):
        if name in namespace:
            globals()[name] = namespace[name]
