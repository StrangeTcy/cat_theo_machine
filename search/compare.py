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
from .. import logic as Logicmod
from ..heuristics import *
from ..labels import *
from ..proof import *
from ..proof import _debug, _debug_term
from .chain_utils import *
from .engine import *
from .engine import _SearchStepKernel
from .model import *
from .patricia import *
from .ui import _SearchComparisonPromptGuard, _SearchConsoleInput, _SearchStopConsole








class CompareSearchModes(M.Edge):
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
            host_parallelism = multiprocessing.cpu_count()
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

    def _mode_chain(self):
        return M.Pair(
            DFSLabel,
            M.Pair(
                BFSLabel,
                M.Pair(AStarLabel, M.Pair(BeamLabel, M.Pair(RewriteDFSLabel, M.EmptyList))),
            ),
        )

    def _mode_chain_text(self, modes):
        if M.IdentityCompare(modes, M.EmptyList)() is M.truth_value:
            return ""
        here = SearchModeText(M.Head(modes)())()
        rest = self._mode_chain_text(M.Tail(modes)())
        if rest == "":
            return here
        return here + ", " + rest

    def _selected_modes_text(self, modes):
        return self._mode_chain_text(modes)

    def _comparison_has_usable_best_attempt(self, comparison):
        if M.Compare(comparison, M.EmptyList)() is M.truth_value:
            return M.false_value
        if M.Compare(SearchComparisonBestAttempt(comparison)(), M.EmptyList)() is M.truth_value:
            return M.false_value
        return M.truth_value

    def _comparison_should_rerun(self, comparison):
        if self._comparison_has_usable_best_attempt(comparison) is M.truth_value:
            return M.false_value
        best_attempt = SearchComparisonBestAttempt(comparison)()
        outcome = SearchComparisonOutcome(comparison)()
        if M.Compare(outcome, M.EmptyList)() is M.truth_value:
            if M.Compare(best_attempt, M.EmptyList)() is M.truth_value:
                outcome = SearchFailureLabel
            else:
                outcome = SearchAttemptStatus(best_attempt)()
        if M.OrAtom(
            M.OrAtom(M.IdentityCompare(outcome, SearchPausedLabel)(), M.IdentityCompare(outcome, SearchTimedOutLabel)())(),
            M.IdentityCompare(outcome, SearchAbortedByUserLabel)(),
        )() is M.truth_value:
            return M.truth_value
        return M.false_value

    def _comparison_total_queued_packets(self, states):
        if M.IdentityCompare(states, M.EmptyList)() is M.truth_value:
            return M.Zero
        rest = self._comparison_total_queued_packets(M.Tail(states)())
        return self._nat_add_local(self._comparison_state_pending_packets_count(M.Head(states)()), rest)

    def _comparison_best_finished_attempt_cost(self, states):
        best_attempt = self._best_finished_attempt(states, M.EmptyList)
        if M.Compare(best_attempt, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        return self._attempt_total_value(best_attempt)

    def _comparison_live_process_budget(self, states, workers):
        active_workers = self._worker_entry_count(workers)
        soft_target = self._nat_add_local(self._comparison_machine_parallelism, self._count_states(states))
        if M.NatLess(soft_target, active_workers, self.registry)() is M.truth_value:
            return active_workers
        return soft_target

    def _comparison_live_process_budget_text(self, states, workers):
        active_workers = self._worker_entry_count(workers)
        queued_packets = self._comparison_total_queued_packets(states)
        soft_target = self._nat_add_local(self._comparison_machine_parallelism, self._count_states(states))
        live_budget = self._comparison_live_process_budget(states, workers)
        return (
            "total-active-processes="
            + self._nat_text(active_workers)
            + " total-queued-packets="
            + self._nat_text(queued_packets)
            + " machine-target="
            + self._nat_text(self._comparison_machine_parallelism)
            + " soft-target="
            + self._nat_text(soft_target)
            + " live-budget="
            + self._nat_text(live_budget)
        )

    def _comparison_total_completed_packets(self, states):
        if M.IdentityCompare(states, M.EmptyList)() is M.truth_value:
            return M.Zero
        rest = self._comparison_total_completed_packets(M.Tail(states)())
        return self._nat_add_local(self._comparison_state_completed_packets(M.Head(states)()), rest)

    def _seconds_text(self, total_seconds):
        if total_seconds < 60.0:
            return "{:.0f}s".format(total_seconds)
        if total_seconds < 3600.0:
            minutes = total_seconds / 60.0
            return "{:.1f}m".format(minutes)
        hours = total_seconds / 3600.0
        return "{:.1f}h".format(hours)

    def _comparison_eta_text(self, states, workers):
        if self._comparison_prompt_guard is None:
            return "rough eta unknown"
        elapsed_seconds = time.time() - self._comparison_prompt_guard.started_at
        if elapsed_seconds <= 0.0:
            return "rough eta unknown"
        completed_packets = self._comparison_total_completed_packets(states)
        completed_text = self._nat_text(completed_packets)
        try:
            completed_count = float(completed_text)
        except Exception:
            return "rough eta unknown"
        if completed_count <= 0.0:
            active_workers = self._worker_entry_count(workers)
            queued_packets = self._comparison_total_queued_packets(states)
            live_budget = self._nat_add_local(active_workers, queued_packets)
            oldest_entry = self._oldest_active_worker_entry(workers)
            if M.Compare(oldest_entry, M.EmptyList)() is M.false_value:
                oldest_mode = self._worker_entry_mode(oldest_entry)
                oldest_state = self._comparison_packet_state(oldest_mode, self._worker_entry_packet_job(oldest_entry))
                return (
                    "rough eta unavailable before first completion; oldest live packet "
                    + SearchModeText(oldest_mode)()
                    + " has run "
                    + self._seconds_text(self._worker_entry_elapsed_seconds(oldest_entry))
                    + " stage="
                    + self._state_stage_text(oldest_state)
                    + " "
                    + self._state_next_action_text(oldest_state)
                    + "; overall elapsed "
                    + self._seconds_text(elapsed_seconds)
                    + " with "
                    + self._nat_text(active_workers)
                    + " active processes, "
                    + self._nat_text(queued_packets)
                    + " queued packets, live-budget "
                    + self._nat_text(live_budget)
                )
            return (
                "rough eta unavailable before first completion; elapsed "
                + self._seconds_text(elapsed_seconds)
                + " with "
                + self._nat_text(active_workers)
                + " active processes, "
                + self._nat_text(queued_packets)
                + " queued packets, live-budget "
                + self._nat_text(live_budget)
            )
        outstanding_packets = self._comparison_live_process_budget(states, workers)
        outstanding_text = self._nat_text(outstanding_packets)
        try:
            outstanding_count = float(outstanding_text)
        except Exception:
            return "rough eta unknown"
        packet_rate = completed_count / elapsed_seconds
        if packet_rate <= 0.0:
            return "rough eta unknown"
        eta_seconds = outstanding_count / packet_rate
        rate_per_minute = packet_rate * 60.0
        return (
            "rough eta "
            + self._seconds_text(eta_seconds)
            + " at about "
            + "{:.1f}".format(rate_per_minute)
            + " completed-packets/min if the backlog does not widen much"
        )

    def _comparison_console_input(self):
        console_input = self.graph._search_console_input
        if console_input is None:
            console_input = _SearchConsoleInput()
            self.graph._search_console_input = console_input
        return console_input

    def _start_stop_listener(self):
        if M.IdentityCompare(self.graph._search_disable_console, M.truth_value)() is M.truth_value:
            self._stop_listener = None
            return
        self._stop_listener = _SearchStopConsole(self._comparison_console_input())
        if M.IdentityCompare(self._stop_listener.start(), M.truth_value)() is M.false_value:
            self._stop_listener = None
            _debug("search-compare: console control unavailable in this environment")
            return
        if M.IdentityCompare(self.graph._search_stop_help_shown, M.truth_value)() is M.false_value:
            print("Type 'pause', 'stop', 'stop <mode>', or 'only <modes>' and press Enter in the console to control the current comparison or search.")
            self.graph._search_stop_help_shown = M.truth_value
        _debug("search-compare: console control ready")

    def _stop_stop_listener(self):
        if self._stop_listener is None:
            return
        self._stop_listener.stop()
        self._stop_listener = None

    def _pause_requested(self):
        if self._stop_listener is None:
            return M.false_value
        if M.IdentityCompare(self._stop_listener.requested(), M.truth_value)() is M.truth_value:
            return M.truth_value
        return M.false_value

    def _consume_console_action(self):
        if self._stop_listener is None:
            return "none", M.EmptyList
        command = self._stop_listener.take_command()
        if command == "":
            return "none", M.EmptyList
        action, modes = self._comparison_prompt_action(command)
        if action == "help" or action == "unknown":
            _debug("search-compare: commands are continue | extend | stop | pause | stop <mode> | only <modes>")
            return "none", M.EmptyList
        return action, modes

    def _read_console_line(self, prompt_text):
        return self._comparison_console_input().read_prompt(prompt_text)

    def _mode_from_token(self, token):
        if token in ("dfs", "searchdfs"):
            return DFSLabel
        if token in ("bfs", "searchbfs"):
            return BFSLabel
        if token in ("astar", "a*", "searchastar"):
            return AStarLabel
        if token in ("beam", "searchbeam"):
            return BeamLabel
        if token in ("rewritedfs", "rewrite-dfs", "searchrewritedfs"):
            return RewriteDFSLabel
        return M.EmptyList

    def _mode_selected(self, modes, mode):
        if M.IdentityCompare(modes, M.EmptyList)() is M.truth_value:
            return M.false_value
        if M.IdentityCompare(M.Head(modes)(), mode)() is M.truth_value:
            return M.truth_value
        return self._mode_selected(M.Tail(modes)(), mode)

    def _selected_modes_from_tokens(self, tokens, index):
        if index >= len(tokens):
            return M.EmptyList
        mode = self._mode_from_token(tokens[index])
        rest = self._selected_modes_from_tokens(tokens, index + 1)
        if M.Compare(mode, M.EmptyList)() is M.truth_value:
            return rest
        if self._mode_selected(rest, mode) is M.truth_value:
            return rest
        return M.Pair(mode, rest)

    def _comparison_prompt_action(self, response):
        answer = response.strip().lower()
        if answer in ("", "y", "yes", "continue", "continue all", "proceed"):
            return "continue", M.EmptyList
        if answer in ("extend", "more", "continue longer"):
            return "extend", M.EmptyList
        if answer in ("stop", "abort", "quit", "stop comparison"):
            return "stop", M.EmptyList
        if answer == "pause":
            return "pause", M.EmptyList
        if answer in ("help", "?"):
            return "help", M.EmptyList
        tokens = answer.split()
        if len(tokens) >= 2 and tokens[0] in ("stop", "kill"):
            mode = self._mode_from_token(tokens[1])
            if M.Compare(mode, M.EmptyList)() is M.false_value:
                return "stop_mode", mode
        if len(tokens) >= 2 and tokens[0] == "only":
            modes = self._selected_modes_from_tokens(tokens, 1)
            if M.IdentityCompare(modes, M.EmptyList)() is M.false_value:
                return "only_modes", modes
        return "unknown", M.EmptyList

    def _comparison_read_action(self, summary_text):
        prompt_text = summary_text + "; actions: continue | extend | stop | pause | stop <mode> | only <modes>"
        while M.IdentityCompare(M.truth_value, M.truth_value)() is M.truth_value:
            try:
                response = self._read_console_line(prompt_text)
            except (EOFError, KeyboardInterrupt):
                response = "stop"
            action, modes = self._comparison_prompt_action(response)
            if action == "help" or action == "unknown":
                _debug("search-compare: commands are continue | extend | stop | pause | stop <mode> | only <modes>")
                continue
            return action, modes

    def _beam_width(self, mode):
        width = HeuristicBeamWidth(self.heuristic)()
        if M.IdentityCompare(mode, BeamLabel)() is M.false_value:
            return width
        if M.NatEq(width, M.Zero, self.registry)() is M.truth_value:
            return M.three
        return width

    def _heuristic_for_mode(self, mode):
        return Heuristic(
            mode,
            HeuristicRuleOrder(self.heuristic)(),
            self._beam_width(mode),
            HeuristicAlpha(self.heuristic)(),
            HeuristicBeta(self.heuristic)(),
            HeuristicCanonicalStrength(self.heuristic)(),
        )()

    def _attempt_total_value(self, attempt):
        total_cost = SearchAttemptTotalCost(attempt)()
        return M.TotalCostValue(total_cost)()

    def _attempt_better(self, attempt, best_attempt):
        if M.Compare(best_attempt, M.EmptyList)() is M.truth_value:
            return M.truth_value
        attempt_status = SearchAttemptStatus(attempt)()
        best_status = SearchAttemptStatus(best_attempt)()
        attempt_succeeded = M.IdentityCompare(attempt_status, SearchSuccessLabel)()
        best_succeeded = M.IdentityCompare(best_status, SearchSuccessLabel)()
        if attempt_succeeded is M.truth_value:
            if best_succeeded is M.false_value:
                return M.truth_value
        if attempt_succeeded is M.false_value:
            if best_succeeded is M.truth_value:
                return M.false_value
        return M.NatLess(self._attempt_total_value(attempt), self._attempt_total_value(best_attempt), self.registry)()

    def _comparison_uses_shared_root_fast_paths(self):
        return M.IdentityCompare(self.graph._search_compare_enable_shared_root_fast_paths, M.truth_value)()

    def _fresh_independent_mode_runtime(self):
        from .runtime import _SearchWorkerRuntime

        runtime = _SearchWorkerRuntime(M.FromContextGetConstructors(self.graph)(), M.EmptyList)
        runtime._search_disable_console = M.truth_value
        runtime._search_disable_progress_ticker = M.truth_value
        runtime._search_stop_help_shown = M.truth_value
        runtime._search_compare_enable_shared_root_fast_paths = M.false_value
        runtime._search_compare_ignore_root_fast_paths = M.truth_value
        runtime._search_compare_root_start = self.start
        runtime._search_compare_root_goal = self.goal
        runtime._search_compare_discovery_mode = M.false_value
        runtime._last_search_comparison_outcome = SearchSuccessLabel
        return runtime

    def _zero_proof_cost(self):
        return ProofCost(M.Zero, M.Zero, M.Zero, M.Zero)()

    def _zero_search_cost(self, outcome):
        search_cost_pair = BuildSearchCost(M.EmptyList, M.Zero, M.Zero, M.Zero, outcome, self.registry)()
        search_cost = M.Head(search_cost_pair)()
        self.registry = M.Head(M.Tail(search_cost_pair)())()
        return search_cost

    def _mode_attempt_from_plan(self, heuristic, status, plan, search_cost):
        derivation = M.EmptyList
        proof_cost = self._zero_proof_cost()
        if M.IdentityCompare(status, SearchSuccessLabel)() is M.truth_value:
            derivation_pair = BuildDerivation(self.start, plan, self.registry)()
            derivation = M.Head(derivation_pair)()
            self.registry = M.Head(M.Tail(derivation_pair)())()
            if M.Compare(derivation, M.EmptyList)() is M.false_value:
                proof_cost_pair = DerivationCost(derivation, self.registry)()
                proof_cost = M.Head(proof_cost_pair)()
                self.registry = M.Head(M.Tail(proof_cost_pair)())()
        total_cost_pair = BuildTotalCost(proof_cost, search_cost, heuristic, self.registry)()
        total_cost = M.Head(total_cost_pair)()
        self.registry = M.Head(M.Tail(total_cost_pair)())()
        return SearchAttempt(
            self.start,
            self.goal,
            heuristic,
            status,
            derivation,
            proof_cost,
            search_cost,
            total_cost,
        )()

    def _attempt_better_with_elapsed(self, attempt, elapsed_seconds, best_attempt, best_elapsed_seconds):
        if M.Compare(best_attempt, M.EmptyList)() is M.truth_value:
            return M.truth_value
        attempt_status = SearchAttemptStatus(attempt)()
        best_status = SearchAttemptStatus(best_attempt)()
        attempt_succeeded = M.IdentityCompare(attempt_status, SearchSuccessLabel)()
        best_succeeded = M.IdentityCompare(best_status, SearchSuccessLabel)()
        if attempt_succeeded is M.truth_value:
            if best_succeeded is M.false_value:
                return M.truth_value
        if attempt_succeeded is M.false_value:
            if best_succeeded is M.truth_value:
                return M.false_value
        attempt_total = self._attempt_total_value(attempt)
        best_total = self._attempt_total_value(best_attempt)
        if M.NatLess(attempt_total, best_total, self.registry)() is M.truth_value:
            return M.truth_value
        if M.NatLess(best_total, attempt_total, self.registry)() is M.truth_value:
            return M.false_value
        if best_elapsed_seconds is None:
            return M.truth_value
        if best_elapsed_seconds - elapsed_seconds > 0.0:
            return M.truth_value
        if elapsed_seconds - best_elapsed_seconds > 0.0:
            return M.false_value
        attempt_search_cost = SearchAttemptSearchCost(attempt)()
        best_search_cost = SearchAttemptSearchCost(best_attempt)()
        attempt_expanded = SearchCostExpanded(attempt_search_cost)()
        best_expanded = SearchCostExpanded(best_search_cost)()
        if M.NatLess(attempt_expanded, best_expanded, self.registry)() is M.truth_value:
            return M.truth_value
        if M.NatLess(best_expanded, attempt_expanded, self.registry)() is M.truth_value:
            return M.false_value
        attempt_peak = SearchCostFrontierPeak(attempt_search_cost)()
        best_peak = SearchCostFrontierPeak(best_search_cost)()
        if M.NatLess(attempt_peak, best_peak, self.registry)() is M.truth_value:
            return M.truth_value
        return M.false_value

    def _independent_mode_attempt(self, mode):
        from .api import Search as SearchAPI

        heuristic = self._heuristic_for_mode(mode)
        mode_text = SearchModeText(mode)()
        _debug("SearchComparison: " + mode_text + " started")
        started_at = time.time()
        try:
            mode_runtime = self._fresh_independent_mode_runtime()
            search_pair = SearchAPI(
                mode_runtime,
                self.start,
                self.goal,
                self.rules,
                heuristic,
                mode_runtime.constructor_registry,
            )()
            plan = M.Head(search_pair)()
            search_cost = M.Head(M.Tail(search_pair)())()
            status = SearchCostOutcome(search_cost)()

            derivation = M.EmptyList
            proof_cost = self._zero_proof_cost()
            if M.IdentityCompare(status, SearchSuccessLabel)() is M.truth_value:
                derivation_pair = BuildDerivation(self.start, plan, mode_runtime.constructor_registry)()
                derivation = M.Head(derivation_pair)()
                mode_runtime._replace_context(constructors=M.Head(M.Tail(derivation_pair)())())
                if M.Compare(derivation, M.EmptyList)() is M.false_value:
                    proof_cost_pair = DerivationCost(derivation, mode_runtime.constructor_registry)()
                    proof_cost = M.Head(proof_cost_pair)()
                    mode_runtime._replace_context(constructors=M.Head(M.Tail(proof_cost_pair)())())

            total_cost_pair = BuildTotalCost(proof_cost, search_cost, heuristic, mode_runtime.constructor_registry)()
            total_cost = M.Head(total_cost_pair)()
            mode_runtime._replace_context(constructors=M.Head(M.Tail(total_cost_pair)())())

            attempt = SearchAttempt(self.start, self.goal, heuristic, status, derivation, proof_cost, search_cost, total_cost)()

            elapsed_seconds = time.time() - started_at
            _debug(
                "SearchComparison: "
                + mode_text
                + " finished status="
                + SearchStatusText(status)()
                + " elapsed="
                + "{:.3f}".format(elapsed_seconds)
                + " expanded="
                + self._nat_text(SearchCostExpanded(search_cost)())
                + " generated="
                + self._nat_text(SearchCostGenerated(search_cost)())
                + " frontier_peak="
                + self._nat_text(SearchCostFrontierPeak(search_cost)())
            )
            return attempt, elapsed_seconds
        except Exception as error:
            import traceback

            elapsed_seconds = time.time() - started_at
            _debug(
                "SearchComparison: "
                + mode_text
                + " finished status=error elapsed="
                + "{:.3f}".format(elapsed_seconds)
                + " error="
                + str(error)
            )
            traceback.print_exc()
            failed_attempt = SearchAttempt(
                self.start,
                self.goal,
                heuristic,
                SearchFailureLabel,
                M.EmptyList,
                self._zero_proof_cost(),
                self._zero_search_cost(SearchFailureLabel),
                M.EmptyList,
            )()
            return failed_attempt, elapsed_seconds

    def _comparison_main_script_path(self):
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), "main.py")

    def _search_worker_result_manifest_path(self, result_path):
        return result_path + ".manifest.json"

    def _write_search_worker_manifest(self, result_path):
        manifest = {
            "start_text": _debug_term(self.start, self.registry),
            "goal_text": _debug_term(self.goal, self.registry),
        }
        with open(self._search_worker_result_manifest_path(result_path), "w", encoding="utf-8") as handle:
            json.dump(manifest, handle)

    def _mode_worker_token(self, mode):
        if M.IdentityCompare(mode, DFSLabel)() is M.truth_value:
            return "dfs"
        if M.IdentityCompare(mode, BFSLabel)() is M.truth_value:
            return "bfs"
        if M.IdentityCompare(mode, AStarLabel)() is M.truth_value:
            return "astar"
        if M.IdentityCompare(mode, BeamLabel)() is M.truth_value:
            return "beam"
        if M.IdentityCompare(mode, RewriteDFSLabel)() is M.truth_value:
            return "rewritedfs"
        return "search"

    def _gmp_atom(self, text):
        atom = M.Atom()
        atom.value = Gmpmod.GMPRep(text)
        return atom

    def _reason_atom(self, text):
        atom = M.Atom()
        atom.value = text
        return atom

    def _fabricate_worker_failure_attempt(self, heuristic, status, elapsed_seconds, reason_text):
        search_cost = self._zero_search_cost(status)
        proof_cost = self._zero_proof_cost()
        total_cost_pair = BuildTotalCost(proof_cost, search_cost, heuristic, self.registry)()
        total_cost = M.Head(total_cost_pair)()
        self.registry = M.Head(M.Tail(total_cost_pair)())()
        attempt = SearchAttempt(
            self.start,
            self.goal,
            heuristic,
            status,
            M.EmptyList,
            proof_cost,
            search_cost,
            total_cost,
        )()
        elapsed_milliseconds = int(round(elapsed_seconds * 1000.0))
        if elapsed_milliseconds < 0:
            elapsed_milliseconds = 0
        performance = HeuristicPerformance(
            attempt,
            self._gmp_atom(str(elapsed_milliseconds)),
            self._gmp_atom("0"),
            self._reason_atom(reason_text),
        )()
        return attempt, performance

    def _performance_elapsed_seconds(self, performance):
        elapsed = HeuristicPerformanceElapsedMilliseconds(performance)()
        try:
            return float(Gmpmod.GMPRepText(elapsed())()) / 1000.0
        except Exception:
            return 0.0

    def _performance_reason_text(self, performance):
        reason = HeuristicPerformanceCompletionReason(performance)()
        if M.IsPair(reason)() is M.truth_value:
            status_text = SearchStatusText(reason)()
            if status_text != "unknown":
                return status_text
        try:
            return str(reason())
        except Exception:
            return _debug_term(reason, self.registry)

    def _is_heuristic_performance(self, value):
        if M.IsPair(value)() is M.false_value:
            return M.false_value
        return M.IdentityCompare(M.Head(value)(), HeuristicPerformanceLabel)()

    def _load_search_worker_snapshot(self, mode, heuristic, result_path):
        from ..main import _runtime_namespace
        from ..persistence import SnapshotCodec

        if os.path.exists(result_path) is False:
            return self._fabricate_worker_failure_attempt(heuristic, SearchFailureLabel, 0.0, "launch-error")
        state = SnapshotCodec(_runtime_namespace()).load(result_path)
        child_registry = state.roots.get("constructor_registry", M.EmptyList)
        if M.Compare(child_registry, M.EmptyList)() is M.false_value:
            self.registry = self._merge_tree(self.registry, child_registry)
            self.graph._replace_context(constructors=self.registry)
        attempts = state.roots.get("search_history", M.EmptyList)
        attempt = M.EmptyList
        if M.IdentityCompare(attempts, M.EmptyList)() is M.false_value:
            attempt = M.Head(attempts)()
        performances = state.roots.get("search_comparisons", M.EmptyList)
        performance = M.EmptyList
        if M.IdentityCompare(performances, M.EmptyList)() is M.false_value:
            candidate = M.Head(performances)()
            if self._is_heuristic_performance(candidate) is M.truth_value:
                performance = candidate
        if M.Compare(attempt, M.EmptyList)() is M.truth_value:
            return self._fabricate_worker_failure_attempt(heuristic, SearchFailureLabel, 0.0, "missing-attempt")
        if M.Compare(performance, M.EmptyList)() is M.truth_value:
            return self._fabricate_worker_failure_attempt(
                heuristic,
                SearchAttemptStatus(attempt)(),
                0.0,
                "missing-performance",
            )
        return attempt, performance

    def _relay_search_worker_output(self, mode_text, stdout_pipe):
        if stdout_pipe is None:
            return
        for line in stdout_pipe:
            text = line.rstrip()
            if text == "":
                continue
            if text.startswith("DEBUG: "):
                text = text[7:]
            if "build-derivation:" in text:
                continue
            if text.startswith(mode_text + ":") is False:
                text = mode_text + ": " + text
            _debug(text)
        try:
            stdout_pipe.close()
        except Exception:
            pass

    def _log_independent_mode_finish(self, mode, status, elapsed_seconds, search_cost, reason_text=""):
        mode_text = SearchModeText(mode)()
        _debug(
            "SearchComparison: "
            + mode_text
            + " finished status="
            + SearchStatusText(status)()
            + " elapsed="
            + "{:.3f}".format(elapsed_seconds)
            + " expanded="
            + self._nat_text(SearchCostExpanded(search_cost)())
            + " generated="
            + self._nat_text(SearchCostGenerated(search_cost)())
            + " frontier_peak="
            + self._nat_text(SearchCostFrontierPeak(search_cost)())
            + " total="
            + self._nat_text(SearchCostValue(search_cost)())
            + " reason="
            + reason_text
        )

    def _finalize_independent_mode_attempts(self, attempts, best_attempt, performances):
        comparison_outcome = SearchFailureLabel
        if M.Compare(best_attempt, M.EmptyList)() is M.false_value:
            comparison_outcome = SearchAttemptStatus(best_attempt)()
        self.graph._replace_context(constructors=self.registry)
        attempts_cursor = attempts
        while M.IdentityCompare(attempts_cursor, M.EmptyList)() is M.false_value:
            self.graph.add_search_attempt(M.Head(attempts_cursor)())
            attempts_cursor = M.Tail(attempts_cursor)()
        comparison = SearchComparison(self.signature, attempts, best_attempt, comparison_outcome, performances)()
        self.graph.add_search_comparison(comparison)
        self.graph._last_search_comparison_outcome = comparison_outcome
        best_mode_text = "none"
        if M.Compare(best_attempt, M.EmptyList)() is M.false_value:
            best_mode_text = SearchModeText(HeuristicSearchMode(SearchAttemptHeuristic(best_attempt)())())()
        _debug("SearchComparison: best mode=" + best_mode_text)
        _debug("SearchComparison: provenance recorded")
        return M.Pair(comparison, M.Pair(best_attempt, M.EmptyList))

    def _compare_all_modes_independent_parallel(self, paused_job=M.EmptyList):
        if M.Compare(paused_job, M.EmptyList)() is M.false_value:
            _debug("SearchComparison: paused legacy comparison ignored; restarting independent mode attempts")
        _debug("SearchComparison: starting independent mode attempts")
        self.graph.remove_search_comparison_job(self.signature)
        package_root = os.path.dirname(os.path.dirname(__file__))
        package_name = os.path.basename(package_root)
        import_root = os.path.dirname(package_root)
        result_dir = tempfile.mkdtemp(prefix="hyge_compare_")
        timeout_text = os.environ.get("HYGE_SEARCH_WORKER_TIMEOUT", "600")
        workers = ()
        reader_threads = ()
        modes = self._mode_chain()
        remaining_modes = modes
        while M.IdentityCompare(remaining_modes, M.EmptyList)() is M.false_value:
            mode = M.Head(remaining_modes)()
            mode_token = self._mode_worker_token(mode)
            result_path = os.path.join(result_dir, mode_token + ".snapshot.json")
            self._write_search_worker_manifest(result_path)
            cmd = [sys.executable, "-m", package_name + ".main", "search-worker", mode_token, result_path, timeout_text]
            child_env = os.environ.copy()
            child_env["PYTHONPATH"] = import_root
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=import_root,
                env=child_env,
            )
            _debug("SearchComparison: launched search-worker mode=" + SearchModeText(mode)() + " pid=" + str(process.pid))
            thread = threading.Thread(target=self._relay_search_worker_output, args=(SearchModeText(mode)(), process.stdout), daemon=True)
            thread.start()
            workers = workers + ((mode, self._heuristic_for_mode(mode), process, result_path),)
            reader_threads = reader_threads + (thread,)
            remaining_modes = M.Tail(remaining_modes)()
        worker_index = 0
        attempts_by_mode = {}
        performances_by_mode = {}
        best_attempt = M.EmptyList
        best_elapsed_seconds = None
        while worker_index != len(workers):
            mode, heuristic, process, result_path = workers[worker_index]
            worker_index = worker_index + 1
            exit_code = process.wait()
            attempt, performance = self._load_search_worker_snapshot(mode, heuristic, result_path)
            elapsed_seconds = self._performance_elapsed_seconds(performance)
            reason_text = self._performance_reason_text(performance)
            if exit_code == 2:
                reason_text = "timed_out"
            if exit_code not in (0, 1, 2):
                attempt, performance = self._fabricate_worker_failure_attempt(
                    heuristic,
                    SearchFailureLabel,
                    elapsed_seconds,
                    "launch-error",
                )
                reason_text = "launch-error"
                elapsed_seconds = self._performance_elapsed_seconds(performance)
            attempts_by_mode[SearchModeText(mode)()] = attempt
            performances_by_mode[SearchModeText(mode)()] = performance
            self._log_independent_mode_finish(mode, SearchAttemptStatus(attempt)(), elapsed_seconds, SearchAttemptSearchCost(attempt)(), reason_text)
            if self._attempt_better_with_elapsed(attempt, elapsed_seconds, best_attempt, best_elapsed_seconds) is M.truth_value:
                best_attempt = attempt
                best_elapsed_seconds = elapsed_seconds
        thread_index = 0
        while thread_index != len(reader_threads):
            reader_threads[thread_index].join(timeout=1.0)
            thread_index = thread_index + 1
        attempts_rev = M.EmptyList
        performances_rev = M.EmptyList
        remaining_modes = modes
        while M.IdentityCompare(remaining_modes, M.EmptyList)() is M.false_value:
            mode = M.Head(remaining_modes)()
            mode_text = SearchModeText(mode)()
            attempts_rev = M.Pair(attempts_by_mode[mode_text], attempts_rev)
            performances_rev = M.Pair(performances_by_mode[mode_text], performances_rev)
            remaining_modes = M.Tail(remaining_modes)()
        attempts = self._reverse(attempts_rev, M.EmptyList)
        performances = self._reverse(performances_rev, M.EmptyList)
        perf_cursor = performances
        while M.IdentityCompare(perf_cursor, M.EmptyList)() is M.false_value:
            perf = M.Head(perf_cursor)()
            attempt = HeuristicPerformanceAttempt(perf)()
            _debug(
                "SearchComparison: summary "
                + SearchModeText(HeuristicSearchMode(SearchAttemptHeuristic(attempt)())())()
                + " status="
                + SearchStatusText(SearchAttemptStatus(attempt)())()
                + " elapsed="
                + "{:.3f}".format(self._performance_elapsed_seconds(perf))
                + " expanded="
                + self._nat_text(SearchCostExpanded(SearchAttemptSearchCost(attempt)())())
                + " cost="
                + self._nat_text(self._attempt_total_value(attempt))
            )
            perf_cursor = M.Tail(perf_cursor)()
        return self._finalize_independent_mode_attempts(attempts, best_attempt, performances)

    def _compare_all_modes_independent(self, paused_job=M.EmptyList):
        return self._compare_all_modes_independent_parallel(paused_job)

    def _nat_text(self, value):
        if M.IdentityCompare(value, M.EmptyList)() is M.truth_value:
            return "0"
        try:
            return Gmpmod.GMPRepText(value())()
        except Exception:
            pass
        rep = M.NatRepOf(value, self.registry)()
        if M.IdentityCompare(rep, M.EmptyList)() is M.false_value:
            return Gmpmod.GMPRepText(rep)()
        return M.PrettyTerm(value, self.registry)()

    def _job_focus_text(self, job):
        frontier = SearchJobFrontier(job)()
        if M.IdentityCompare(frontier, M.EmptyList)() is M.truth_value:
            return "empty"
        current = SearchStateCurrent(M.Head(frontier)())()
        return _debug_term(current, self.registry)

    def _job_focus_state(self, job):
        frontier = SearchJobFrontier(job)()
        if M.IdentityCompare(frontier, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        return M.Head(frontier)()

    def _plan_prefix_text(self, plan_rev):
        if M.IdentityCompare(plan_rev, M.EmptyList)() is M.truth_value:
            return "[]"
        return PrettyPlanChain(self._reverse(plan_rev, M.EmptyList), self.registry)()

    def _state_prefix_text(self, state):
        return self._plan_prefix_text(SearchStatePlan(state)())

    def _state_prefix_length(self, state):
        count_pair = M.Count(SearchStatePlan(state)(), self.registry)()
        count = M.Head(count_pair)()
        self.registry = M.Head(M.Tail(count_pair)())()
        return count

    def _job_prefix_text(self, job):
        frontier = SearchJobFrontier(job)()
        if M.IdentityCompare(frontier, M.EmptyList)() is M.truth_value:
            return "[]"
        return self._state_prefix_text(M.Head(frontier)())

    def _job_progress_text(self, job):
        return (
            "frontier="
            + self._nat_text(SearchJobFrontierSize(job)())
            + " expanded="
            + self._nat_text(SearchJobExpanded(job)())
            + " generated="
            + self._nat_text(SearchJobGenerated(job)())
            + " peak="
            + self._nat_text(SearchJobFrontierPeak(job)())
            + " next="
            + self._job_focus_text(job)
            + " prefix="
            + self._job_prefix_text(job)
        )

    def _state_scheduler_text(self, state):
        job = self._comparison_state_job(state)
        return (
            SearchModeText(self._comparison_state_mode(state))()
            + " phase="
            + self._comparison_phase_text(state)
            + " status="
            + SearchStatusText(self._comparison_state_status(state))()
            + " root="
            + self._comparison_root_fast_path_result_text(state)
            + " frontier="
            + self._nat_text(SearchJobFrontierSize(job)())
            + " expanded="
            + self._nat_text(SearchJobExpanded(job)())
            + " generated="
            + self._nat_text(SearchJobGenerated(job)())
            + " peak="
            + self._nat_text(SearchJobFrontierPeak(job)())
            + " mode-active-processes="
            + self._nat_text(self._comparison_state_active_packets(state))
            + " mode-queued-packets="
            + self._nat_text(self._comparison_state_pending_packets_count(state))
            + " mode-completed-packets="
            + self._nat_text(self._comparison_state_completed_packets(state))
        )

    def _comparison_phase_text(self, state):
        phase = self._comparison_state_phase(state)
        if M.IdentityCompare(phase, SearchRootFastPathPhaseLabel)() is M.truth_value:
            return "root_fast_path"
        if M.IdentityCompare(phase, SearchPacketSearchPhaseLabel)() is M.truth_value:
            return "packet_search"
        return "unknown"

    def _comparison_root_fast_path_result_text(self, state):
        result = self._comparison_state_root_fast_path_result(state)
        if M.Compare(result, M.EmptyList)() is M.truth_value:
            return "pending"
        if M.IdentityCompare(result, SearchNoRootFastPathLabel)() is M.truth_value:
            return "miss"
        if M.IdentityCompare(result, SearchRootCacheResultLabel)() is M.truth_value:
            return "cache"
        if M.IdentityCompare(result, SearchRootSchemaResultLabel)() is M.truth_value:
            return "schema"
        if M.IdentityCompare(result, SearchRootGoalResultLabel)() is M.truth_value:
            return "goal"
        if M.IdentityCompare(result, SearchRootImmediateResultLabel)() is M.truth_value:
            return "immediate"
        return "unknown"

    def _active_worker_focus_state(self, workers, mode, best_state=M.EmptyList):
        if M.IdentityCompare(workers, M.EmptyList)() is M.truth_value:
            return best_state
        entry = M.Head(workers)()
        next_best = best_state
        if M.IdentityCompare(self._worker_entry_mode(entry), mode)() is M.truth_value:
            candidate_state = self._comparison_packet_state(mode, self._worker_entry_packet_job(entry))
            if M.IdentityCompare(best_state, M.EmptyList)() is M.truth_value:
                next_best = candidate_state
            elif M.NatLess(self._state_prefix_length(best_state), self._state_prefix_length(candidate_state), self.registry)() is M.truth_value:
                next_best = candidate_state
        return self._active_worker_focus_state(M.Tail(workers)(), mode, next_best)

    def _active_worker_focus_text(self, workers, mode):
        state = self._active_worker_focus_state(workers, mode)
        if M.IdentityCompare(state, M.EmptyList)() is M.truth_value:
            return ""
        return (
            "active-next="
            + _debug_term(SearchStateCurrent(state)(), self.registry)
            + " active-prefix="
            + self._state_prefix_text(state)
            + " active-prefix-steps="
            + self._nat_text(self._state_prefix_length(state))
        )

    def _goal_signal_term(self, term):
        if M.Compare(term, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        if self._comparison_goal_reached(term, self.goal) is M.truth_value:
            return term
        if IsKnowledge(term)() is M.truth_value:
            return self._goal_signal_fact(KnowledgeFacts(term)())
        if M.IsPair(term)() is M.truth_value:
            head = M.Head(term)()
            goal_head = M.EmptyList
            if M.IsPair(self.goal)() is M.truth_value:
                goal_head = M.Head(self.goal)()
            if M.IdentityCompare(head, goal_head)() is M.truth_value:
                return term
            if M.IdentityCompare(head, Lmod.ExprEqLabel)() is M.truth_value:
                return term
            if M.IdentityCompare(head, Lmod.SolvedLabel)() is M.truth_value:
                return term
        return M.EmptyList

    def _goal_signal_fact(self, facts):
        if M.IdentityCompare(facts, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        fact = M.Head(facts)()
        signal = self._goal_signal_term(fact)
        if M.Compare(signal, M.EmptyList)() is M.false_value:
            return signal
        return self._goal_signal_fact(M.Tail(facts)())

    def _goal_signal_text(self, term):
        signal = self._goal_signal_term(term)
        if M.Compare(signal, M.EmptyList)() is M.truth_value:
            return "goal-signal=none"
        if self._comparison_goal_reached(signal, self.goal) is M.truth_value:
            return "goal-signal=goal-reached"
        return "goal-signal=" + _debug_term(signal, self.registry)

    def _append_semantic_item(self, text, item):
        if text == "":
            return item
        return text + "," + item

    def _term_head_matches(self, term, label):
        if M.IsPair(term)() is M.false_value:
            return M.false_value
        if M.IdentityCompare(M.Head(term)(), label)() is M.truth_value:
            return M.truth_value
        return M.false_value

    def _term_first_arg(self, term):
        if M.IsPair(term)() is M.false_value:
            return M.EmptyList
        tail = M.Tail(term)()
        if M.IsPair(tail)() is M.false_value:
            return M.EmptyList
        return M.Head(tail)()

    def _term_contains_label(self, term, label):
        if M.Compare(term, M.EmptyList)() is M.truth_value:
            return M.false_value
        if M.IsPair(term)() is M.false_value:
            return M.false_value
        if M.IdentityCompare(M.Head(term)(), label)() is M.truth_value:
            return M.truth_value
        if self._term_contains_label(M.Head(term)(), label) is M.truth_value:
            return M.truth_value
        return self._term_contains_label(M.Tail(term)(), label)

    def _current_facts(self, term):
        if IsKnowledge(term)() is M.truth_value:
            return KnowledgeFacts(term)()
        return M.EmptyList

    def _fact_is_parameter_of(self, fact, label):
        if self._term_head_matches(fact, Lmod.ParameterLabel) is M.false_value:
            return M.false_value
        if self._term_head_matches(self._term_first_arg(fact), label) is M.truth_value:
            return M.truth_value
        return M.false_value

    def _fact_is_plain_head(self, fact, label):
        return self._term_head_matches(fact, label)

    def _fact_is_solved_target(self, fact, label):
        if self._term_head_matches(fact, Lmod.SolvedLabel) is M.false_value:
            return M.false_value
        if self._term_head_matches(self._term_first_arg(fact), label) is M.truth_value:
            return M.truth_value
        return M.false_value

    def _fact_is_solved_equation(self, fact):
        if self._term_head_matches(fact, Lmod.SolvedLabel) is M.false_value:
            return M.false_value
        if self._term_head_matches(self._term_first_arg(fact), Lmod.ExprEqLabel) is M.truth_value:
            return M.truth_value
        return M.false_value

    def _fact_contains_solved_equation_labels(self, fact, first_label, second_label=M.EmptyList, third_label=M.EmptyList, fourth_label=M.EmptyList):
        if self._fact_is_solved_equation(fact) is M.false_value:
            return M.false_value
        equation = self._term_first_arg(fact)
        if self._term_contains_label(equation, first_label) is M.false_value:
            return M.false_value
        if M.Compare(second_label, M.EmptyList)() is M.false_value:
            if self._term_contains_label(equation, second_label) is M.false_value:
                return M.false_value
        if M.Compare(third_label, M.EmptyList)() is M.false_value:
            if self._term_contains_label(equation, third_label) is M.false_value:
                return M.false_value
        if M.Compare(fourth_label, M.EmptyList)() is M.false_value:
            if self._term_contains_label(equation, fourth_label) is M.false_value:
                return M.false_value
        return M.truth_value

    def _facts_have_plain_head(self, facts, label):
        if M.IdentityCompare(facts, M.EmptyList)() is M.truth_value:
            return M.false_value
        fact = M.Head(facts)()
        if self._fact_is_plain_head(fact, label) is M.truth_value:
            return M.truth_value
        return self._facts_have_plain_head(M.Tail(facts)(), label)

    def _facts_have_parameter(self, facts, label):
        if M.IdentityCompare(facts, M.EmptyList)() is M.truth_value:
            return M.false_value
        fact = M.Head(facts)()
        if self._fact_is_parameter_of(fact, label) is M.truth_value:
            return M.truth_value
        return self._facts_have_parameter(M.Tail(facts)(), label)

    def _facts_have_solved_target(self, facts, label):
        if M.IdentityCompare(facts, M.EmptyList)() is M.truth_value:
            return M.false_value
        fact = M.Head(facts)()
        if self._fact_is_solved_target(fact, label) is M.truth_value:
            return M.truth_value
        return self._facts_have_solved_target(M.Tail(facts)(), label)

    def _facts_have_solved_equation_with_label(self, facts, label):
        if M.IdentityCompare(facts, M.EmptyList)() is M.truth_value:
            return M.false_value
        fact = M.Head(facts)()
        if self._fact_contains_solved_equation_labels(fact, label) is M.truth_value:
            return M.truth_value
        return self._facts_have_solved_equation_with_label(M.Tail(facts)(), label)

    def _facts_have_heron_equation(self, facts):
        if M.IdentityCompare(facts, M.EmptyList)() is M.truth_value:
            return M.false_value
        fact = M.Head(facts)()
        if self._fact_contains_solved_equation_labels(fact, Lmod.AreaLabel, Lmod.LengthLabel) is M.truth_value:
            return M.truth_value
        return self._facts_have_heron_equation(M.Tail(facts)())

    def _facts_have_quadratic_equation(self, facts):
        if M.IdentityCompare(facts, M.EmptyList)() is M.truth_value:
            return M.false_value
        fact = M.Head(facts)()
        if self._fact_contains_solved_equation_labels(
            fact,
            Lmod.ExprPowLabel,
            Lmod.LengthLabel,
            Lmod.CommonDifferenceLabel,
            Lmod.AreaLabel,
        ) is M.truth_value:
            return M.truth_value
        return self._facts_have_quadratic_equation(M.Tail(facts)())

    def _fact_in_facts(self, fact, facts):
        if M.IdentityCompare(facts, M.EmptyList)() is M.truth_value:
            return M.false_value
        if M.TermEqual(fact, M.Head(facts)())() is M.truth_value:
            return M.truth_value
        return self._fact_in_facts(fact, M.Tail(facts)())

    def _introduced_facts(self, term):
        current_facts = self._current_facts(term)
        if M.IdentityCompare(current_facts, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        start_facts = self._current_facts(self.start)
        if M.IdentityCompare(start_facts, M.EmptyList)() is M.truth_value:
            return current_facts
        return self._facts_difference(current_facts, start_facts)

    def _facts_difference(self, facts, base_facts):
        if M.IdentityCompare(facts, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        fact = M.Head(facts)()
        rest = self._facts_difference(M.Tail(facts)(), base_facts)
        if self._fact_in_facts(fact, base_facts) is M.truth_value:
            return rest
        return M.Pair(fact, rest)

    def _first_introduced_equation(self, facts):
        if M.IdentityCompare(facts, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        fact = M.Head(facts)()
        if self._fact_is_solved_equation(fact) is M.truth_value:
            return fact
        return self._first_introduced_equation(M.Tail(facts)())

    def _first_introduced_fact(self, facts):
        if M.IdentityCompare(facts, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        fact = M.Head(facts)()
        if self._fact_is_solved_equation(fact) is M.false_value:
            return fact
        return self._first_introduced_fact(M.Tail(facts)())

    def _term_contains_any_label(self, term, first_label, second_label=M.EmptyList, third_label=M.EmptyList, fourth_label=M.EmptyList):
        if self._term_contains_label(term, first_label) is M.truth_value:
            return M.truth_value
        if M.Compare(second_label, M.EmptyList)() is M.false_value:
            if self._term_contains_label(term, second_label) is M.truth_value:
                return M.truth_value
        if M.Compare(third_label, M.EmptyList)() is M.false_value:
            if self._term_contains_label(term, third_label) is M.truth_value:
                return M.truth_value
        if M.Compare(fourth_label, M.EmptyList)() is M.false_value:
            if self._term_contains_label(term, fourth_label) is M.truth_value:
                return M.truth_value
        return M.false_value

    def _term_contains_all_labels(self, term, first_label, second_label=M.EmptyList, third_label=M.EmptyList, fourth_label=M.EmptyList):
        if self._term_contains_label(term, first_label) is M.false_value:
            return M.false_value
        if M.Compare(second_label, M.EmptyList)() is M.false_value:
            if self._term_contains_label(term, second_label) is M.false_value:
                return M.false_value
        if M.Compare(third_label, M.EmptyList)() is M.false_value:
            if self._term_contains_label(term, third_label) is M.false_value:
                return M.false_value
        if M.Compare(fourth_label, M.EmptyList)() is M.false_value:
            if self._term_contains_label(term, fourth_label) is M.false_value:
                return M.false_value
        return M.truth_value

    def _action_replacement(self, action):
        if Pmod.IsRewriteAction(action)() is M.truth_value:
            return M.EmptyList
        return RuleReplacement(Pmod.ActionRule(action)())()

    def _action_replacement_contains_any_label(self, action, first_label, second_label=M.EmptyList, third_label=M.EmptyList, fourth_label=M.EmptyList):
        replacement = self._action_replacement(action)
        if M.Compare(replacement, M.EmptyList)() is M.truth_value:
            return M.false_value
        return self._term_contains_any_label(replacement, first_label, second_label, third_label, fourth_label)

    def _action_replacement_contains_all_labels(self, action, first_label, second_label=M.EmptyList, third_label=M.EmptyList, fourth_label=M.EmptyList):
        replacement = self._action_replacement(action)
        if M.Compare(replacement, M.EmptyList)() is M.truth_value:
            return M.false_value
        return self._term_contains_all_labels(replacement, first_label, second_label, third_label, fourth_label)

    def _plan_has_rewrite_action(self, plan_rev):
        if M.IdentityCompare(plan_rev, M.EmptyList)() is M.truth_value:
            return M.false_value
        action = M.Head(plan_rev)()
        if Pmod.IsRewriteAction(action)() is M.truth_value:
            return M.truth_value
        return self._plan_has_rewrite_action(M.Tail(plan_rev)())

    def _plan_has_action_replacement_any_label(self, plan_rev, first_label, second_label=M.EmptyList, third_label=M.EmptyList, fourth_label=M.EmptyList):
        if M.IdentityCompare(plan_rev, M.EmptyList)() is M.truth_value:
            return M.false_value
        action = M.Head(plan_rev)()
        if self._action_replacement_contains_any_label(action, first_label, second_label, third_label, fourth_label) is M.truth_value:
            return M.truth_value
        return self._plan_has_action_replacement_any_label(M.Tail(plan_rev)(), first_label, second_label, third_label, fourth_label)

    def _plan_has_action_replacement_all_labels(self, plan_rev, first_label, second_label=M.EmptyList, third_label=M.EmptyList, fourth_label=M.EmptyList):
        if M.IdentityCompare(plan_rev, M.EmptyList)() is M.truth_value:
            return M.false_value
        action = M.Head(plan_rev)()
        if self._action_replacement_contains_all_labels(action, first_label, second_label, third_label, fourth_label) is M.truth_value:
            return M.truth_value
        return self._plan_has_action_replacement_all_labels(M.Tail(plan_rev)(), first_label, second_label, third_label, fourth_label)

    def _state_families_text(self, state):
        plan_rev = SearchStatePlan(state)()
        text = ""
        if self._plan_has_action_replacement_any_label(
            plan_rev,
            Lmod.ArithmeticProgressionLabel,
            Lmod.CommonDifferenceLabel,
            Lmod.MiddleTermAverageLabel,
        ) is M.truth_value:
            text = self._append_semantic_item(text, "arithmetic")
        if self._plan_has_action_replacement_any_label(plan_rev, Lmod.ParameterLabel) is M.truth_value:
            text = self._append_semantic_item(text, "parameters")
        if self._plan_has_action_replacement_all_labels(plan_rev, Lmod.ExprEqLabel, Lmod.LengthLabel) is M.truth_value:
            text = self._append_semantic_item(text, "side-length-equations")
        if self._plan_has_action_replacement_all_labels(plan_rev, Lmod.ExprEqLabel, Lmod.AreaLabel, Lmod.LengthLabel) is M.truth_value:
            text = self._append_semantic_item(text, "heron")
        if self._plan_has_action_replacement_all_labels(
            plan_rev,
            Lmod.ExprEqLabel,
            Lmod.ExprPowLabel,
            Lmod.LengthLabel,
            Lmod.CommonDifferenceLabel,
        ) is M.truth_value:
            text = self._append_semantic_item(text, "quadratic")
        if self._plan_has_action_replacement_any_label(
            plan_rev,
            Lmod.AnglesLabel,
            Lmod.CosineLabel,
            Lmod.FirstAngleLabel,
            Lmod.SecondAngleLabel,
        ) is M.truth_value or self._plan_has_action_replacement_any_label(plan_rev, Lmod.ThirdAngleLabel) is M.truth_value:
            text = self._append_semantic_item(text, "angles")
        if self._plan_has_action_replacement_all_labels(plan_rev, Lmod.SolvedLabel, Lmod.SideLengthsLabel) is M.truth_value:
            text = self._append_semantic_item(text, "side-lengths-solved")
        if self._plan_has_rewrite_action(plan_rev) is M.truth_value:
            text = self._append_semantic_item(text, "rewrite")
        if text == "":
            return "families=none"
        return "families=" + text

    def _state_milestones_text(self, state):
        current = SearchStateCurrent(state)()
        facts = self._current_facts(current)
        text = ""
        if self._facts_have_plain_head(facts, Lmod.ArithmeticProgressionLabel) is M.truth_value:
            text = self._append_semantic_item(text, "ap-recognized")
        area_parameter = self._facts_have_parameter(facts, Lmod.AreaLabel)
        difference_parameter = self._facts_have_parameter(facts, Lmod.CommonDifferenceLabel)
        if area_parameter is M.truth_value and difference_parameter is M.truth_value:
            text = self._append_semantic_item(text, "parameters-extracted(2/2)")
        elif area_parameter is M.truth_value or difference_parameter is M.truth_value:
            text = self._append_semantic_item(text, "parameters-extracted(1/2)")
        if self._facts_have_solved_equation_with_label(facts, Lmod.LengthLabel) is M.truth_value:
            text = self._append_semantic_item(text, "side-length-equations")
        if self._facts_have_heron_equation(facts) is M.truth_value:
            text = self._append_semantic_item(text, "heron-equation")
        elif self._plan_has_action_replacement_all_labels(SearchStatePlan(state)(), Lmod.ExprEqLabel, Lmod.AreaLabel, Lmod.LengthLabel) is M.truth_value:
            text = self._append_semantic_item(text, "heron-equation")
        if self._facts_have_quadratic_equation(facts) is M.truth_value:
            text = self._append_semantic_item(text, "quadratic")
        elif self._plan_has_action_replacement_all_labels(
            SearchStatePlan(state)(),
            Lmod.ExprEqLabel,
            Lmod.ExprPowLabel,
            Lmod.LengthLabel,
            Lmod.CommonDifferenceLabel,
        ) is M.truth_value:
            text = self._append_semantic_item(text, "quadratic")
        if self._facts_have_solved_target(facts, Lmod.SideLengthsLabel) is M.truth_value:
            text = self._append_semantic_item(text, "side-lengths-solved")
        if self._facts_have_solved_target(facts, Lmod.AnglesLabel) is M.truth_value:
            text = self._append_semantic_item(text, "angles-solved")
        if text == "":
            return "milestones=none"
        return "milestones=" + text

    def _state_stage_text(self, state):
        current = SearchStateCurrent(state)()
        current_stage = self._term_stage_text(current)
        if current_stage != "givens-only":
            return current_stage
        if self._plan_has_action_replacement_all_labels(
            SearchStatePlan(state)(),
            Lmod.ExprEqLabel,
            Lmod.ExprPowLabel,
            Lmod.LengthLabel,
            Lmod.CommonDifferenceLabel,
        ) is M.truth_value:
            return "quadratic-introduced"
        if self._plan_has_action_replacement_all_labels(
            SearchStatePlan(state)(),
            Lmod.ExprEqLabel,
            Lmod.AreaLabel,
            Lmod.LengthLabel,
        ) is M.truth_value:
            return "heron-equation-introduced"
        next_term = self._state_cursor_next_term(state)
        if M.Compare(next_term, M.EmptyList)() is M.false_value:
            next_stage = self._term_stage_text(next_term)
            if next_stage != "givens-only":
                return "targeting-" + next_stage
            return "targeting-first-step"
        return "givens-only"

    def _new_fact_text(self, term):
        introduced = self._introduced_facts(term)
        first_fact = self._first_introduced_fact(introduced)
        if M.Compare(first_fact, M.EmptyList)() is M.truth_value:
            return "new-fact=none"
        return "new-fact=" + _debug_term(first_fact, self.registry)

    def _new_equation_text(self, term):
        introduced = self._introduced_facts(term)
        first_equation = self._first_introduced_equation(introduced)
        if M.Compare(first_equation, M.EmptyList)() is M.truth_value:
            return "new-equation=none"
        return "new-equation=" + _debug_term(first_equation, self.registry)

    def _state_cursor_rule(self, state):
        cursor = SearchStateCursor(state)()
        if M.Compare(cursor, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        if M.IsPair(cursor)() is M.false_value:
            return M.EmptyList
        if M.IdentityCompare(M.Head(cursor)(), SearchTheoremCursorLabel)() is M.false_value:
            return M.EmptyList
        rules = SearchTheoremCursorRules(cursor)()
        if M.IdentityCompare(rules, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        return M.Head(rules)()

    def _state_cursor_next_term(self, state):
        rule = self._state_cursor_rule(state)
        if M.Compare(rule, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        current = SearchStateCurrent(state)()
        next_term = self._direct_next_term(rule, current)
        if M.TermEqual(next_term, current)() is M.truth_value:
            return M.EmptyList
        return next_term

    def _state_next_action_text(self, state):
        rule = self._state_cursor_rule(state)
        if M.Compare(rule, M.EmptyList)() is M.truth_value:
            return "next-action=none"
        return "next-action=" + PrettyAction(TheoremAction(rule)(), self.registry)()

    def _term_introduced_facts(self, base_term, next_term):
        current_facts = self._current_facts(next_term)
        if M.IdentityCompare(current_facts, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        base_facts = self._current_facts(base_term)
        if M.IdentityCompare(base_facts, M.EmptyList)() is M.truth_value:
            return current_facts
        return self._facts_difference(current_facts, base_facts)

    def _target_fact_text(self, state):
        next_term = self._state_cursor_next_term(state)
        if M.Compare(next_term, M.EmptyList)() is M.truth_value:
            return "target-fact=none"
        introduced = self._term_introduced_facts(SearchStateCurrent(state)(), next_term)
        first_fact = self._first_introduced_fact(introduced)
        if M.Compare(first_fact, M.EmptyList)() is M.truth_value:
            return "target-fact=none"
        return "target-fact=" + _debug_term(first_fact, self.registry)

    def _target_equation_text(self, state):
        next_term = self._state_cursor_next_term(state)
        if M.Compare(next_term, M.EmptyList)() is M.truth_value:
            return "target-equation=none"
        introduced = self._term_introduced_facts(SearchStateCurrent(state)(), next_term)
        first_equation = self._first_introduced_equation(introduced)
        if M.Compare(first_equation, M.EmptyList)() is M.truth_value:
            return "target-equation=none"
        return "target-equation=" + _debug_term(first_equation, self.registry)

    def _term_stage_text(self, term):
        facts = self._current_facts(term)
        if self._comparison_goal_reached(term, self.goal) is M.truth_value:
            return "goal-reached"
        if self._facts_have_solved_target(facts, Lmod.AnglesLabel) is M.truth_value:
            return "angles-solved"
        if self._facts_have_solved_target(facts, Lmod.SideLengthsLabel) is M.truth_value:
            return "side-lengths-solved"
        if self._facts_have_quadratic_equation(facts) is M.truth_value:
            return "quadratic-introduced"
        if self._facts_have_heron_equation(facts) is M.truth_value:
            return "heron-equation-introduced"
        if self._facts_have_solved_equation_with_label(facts, Lmod.LengthLabel) is M.truth_value:
            return "side-length-equations-introduced"
        if self._facts_have_parameter(facts, Lmod.AreaLabel) is M.truth_value or self._facts_have_parameter(facts, Lmod.CommonDifferenceLabel) is M.truth_value:
            return "parameters-extracted"
        if self._facts_have_plain_head(facts, Lmod.ArithmeticProgressionLabel) is M.truth_value:
            return "ap-recognized"
        return "givens-only"

    def _queued_focus_state(self, state):
        pending_packets = self._comparison_state_pending_packets(state)
        if M.IdentityCompare(pending_packets, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        return self._comparison_packet_state(self._comparison_state_mode(state), M.Head(pending_packets)())

    def _queued_focus_text(self, state):
        queued_state = self._queued_focus_state(state)
        if M.IdentityCompare(queued_state, M.EmptyList)() is M.truth_value:
            return ""
        return (
            "queued-next="
            + _debug_term(SearchStateCurrent(queued_state)(), self.registry)
            + " queued-prefix="
            + self._state_prefix_text(queued_state)
            + " queued-prefix-steps="
            + self._nat_text(self._state_prefix_length(queued_state))
        )

    def _mode_best_live_state(self, state, workers):
        active_state = self._active_worker_focus_state(workers, self._comparison_state_mode(state))
        queued_state = self._queued_focus_state(state)
        if M.IdentityCompare(active_state, M.EmptyList)() is M.truth_value:
            return queued_state
        if M.IdentityCompare(queued_state, M.EmptyList)() is M.truth_value:
            return active_state
        if M.NatLess(self._state_prefix_length(active_state), self._state_prefix_length(queued_state), self.registry)() is M.truth_value:
            return queued_state
        return active_state

    def _state_semantic_text(self, state, workers=M.EmptyList):
        mode = self._comparison_state_mode(state)
        live_state = self._mode_best_live_state(state, workers)
        if M.IdentityCompare(live_state, M.EmptyList)() is M.truth_value:
            return SearchModeText(mode)() + " stage=waiting"
        current = SearchStateCurrent(live_state)()
        text = (
            SearchModeText(mode)()
            + " stage="
            + self._state_stage_text(live_state)
            + " live-prefix-steps="
            + self._nat_text(self._state_prefix_length(live_state))
        )
        next_action_text = self._state_next_action_text(live_state)
        families_text = self._state_families_text(live_state)
        milestones_text = self._state_milestones_text(live_state)
        new_fact_text = self._new_fact_text(current)
        new_equation_text = self._new_equation_text(current)
        target_fact_text = self._target_fact_text(live_state)
        target_equation_text = self._target_equation_text(live_state)
        goal_signal_text = self._goal_signal_text(current)
        if next_action_text != "next-action=none":
            text = text + " " + next_action_text
        if families_text != "families=none":
            text = text + " " + families_text
        if milestones_text != "milestones=none":
            text = text + " " + milestones_text
        if new_fact_text != "new-fact=none":
            text = text + " " + new_fact_text
        if new_equation_text != "new-equation=none":
            text = text + " " + new_equation_text
        if target_fact_text != "target-fact=none":
            text = text + " " + target_fact_text
        if target_equation_text != "target-equation=none":
            text = text + " " + target_equation_text
        if goal_signal_text != "goal-signal=none":
            text = text + " " + goal_signal_text
        return text

    def _running_scheduler_text(self, states):
        if M.IdentityCompare(states, M.EmptyList)() is M.truth_value:
            return ""
        state = M.Head(states)()
        rest = self._running_scheduler_text(M.Tail(states)())
        if M.IdentityCompare(self._comparison_state_status(state), SearchRunningLabel)() is M.false_value:
            return rest
        text = self._state_scheduler_text(state)
        if rest == "":
            return text
        return text + " | " + rest

    def _running_scheduler_summary(self, states):
        text = self._running_scheduler_text(states)
        if text == "":
            return "none"
        return text

    def _finished_scheduler_text(self, states):
        if M.IdentityCompare(states, M.EmptyList)() is M.truth_value:
            return ""
        state = M.Head(states)()
        rest = self._finished_scheduler_text(M.Tail(states)())
        if M.IdentityCompare(self._comparison_state_status(state), SearchRunningLabel)() is M.truth_value:
            return rest
        text = self._state_scheduler_text(state)
        if rest == "":
            return text
        return text + " | " + rest

    def _finished_scheduler_summary(self, states):
        text = self._finished_scheduler_text(states)
        if text == "":
            return "none"
        return text

    def _running_semantic_text(self, states, workers=M.EmptyList):
        if M.IdentityCompare(states, M.EmptyList)() is M.truth_value:
            return ""
        state = M.Head(states)()
        rest = self._running_semantic_text(M.Tail(states)(), workers)
        if M.IdentityCompare(self._comparison_state_status(state), SearchRunningLabel)() is M.false_value:
            return rest
        text = self._state_semantic_text(state, workers)
        if rest == "":
            return text
        return text + " | " + rest

    def _running_semantic_summary(self, states, workers=M.EmptyList):
        text = self._running_semantic_text(states, workers)
        if text == "":
            return "none"
        return text

    def _state_progress_text(self, state, workers=M.EmptyList):
        mode = self._comparison_state_mode(state)
        active_focus = self._active_worker_focus_text(workers, mode)
        queued_focus = self._queued_focus_text(state)
        focus_suffix = ""
        if active_focus != "":
            focus_suffix = focus_suffix + " " + active_focus
        if queued_focus != "":
            focus_suffix = focus_suffix + " " + queued_focus
        return (
            SearchModeText(mode)()
            + " phase="
            + self._comparison_phase_text(state)
            + " status="
            + SearchStatusText(self._comparison_state_status(state))()
            + " root="
            + self._comparison_root_fast_path_result_text(state)
            + " "
            + self._job_progress_text(self._comparison_state_job(state))
            + focus_suffix
            + " mode-active-processes="
            + self._nat_text(self._comparison_state_active_packets(state))
            + " mode-queued-packets="
            + self._nat_text(self._comparison_state_pending_packets_count(state))
            + " mode-completed-packets="
            + self._nat_text(self._comparison_state_completed_packets(state))
        )

    def _running_states_text(self, states, workers=M.EmptyList):
        if M.IdentityCompare(states, M.EmptyList)() is M.truth_value:
            return ""
        state = M.Head(states)()
        rest = self._running_states_text(M.Tail(states)(), workers)
        if M.IdentityCompare(self._comparison_state_status(state), SearchRunningLabel)() is M.false_value:
            return rest
        text = self._state_progress_text(state, workers)
        if rest == "":
            return text
        return text + " | " + rest

    def _running_states_summary(self, states, workers=M.EmptyList):
        text = self._running_states_text(states, workers)
        if text == "":
            return "none"
        return text

    def _finished_states_summary(self, states, workers=M.EmptyList):
        if M.IdentityCompare(states, M.EmptyList)() is M.truth_value:
            return "none"
        state = M.Head(states)()
        rest = self._finished_states_summary(M.Tail(states)(), workers)
        if M.IdentityCompare(self._comparison_state_status(state), SearchRunningLabel)() is M.truth_value:
            return rest
        text = self._state_progress_text(state, workers)
        if rest == "" or rest == "none":
            return text
        return text + " | " + rest

    def _first_goal_signal_in_packets(self, mode, packets):
        if M.IdentityCompare(packets, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        packet_state = self._comparison_packet_state(mode, M.Head(packets)())
        signal = self._goal_signal_term(SearchStateCurrent(packet_state)())
        if M.Compare(signal, M.EmptyList)() is M.false_value:
            return signal
        return self._first_goal_signal_in_packets(mode, M.Tail(packets)())

    def _comparison_state(
        self,
        mode,
        job,
        search_memo,
        active_packets,
        pending_packets=None,
        pending_packets_count=None,
        phase=None,
        completed_packets=None,
        root_fast_path_result=None,
        stop_reason=None,
    ):
        if pending_packets is None:
            pending_packets = M.EmptyList
        if pending_packets_count is None:
            if M.IdentityCompare(pending_packets, M.EmptyList)() is M.truth_value:
                pending_packets_count = M.Zero
            else:
                pending_packets_count = M.Atom()
                pending_packets_count.value = M.CountRep(pending_packets)()
        elif M.IdentityCompare(pending_packets_count, M.EmptyList)() is M.truth_value:
            pending_packets_count = M.Zero
        if phase is None:
            phase = SearchRootFastPathPhaseLabel
        if completed_packets is None:
            completed_packets = M.Zero
        if root_fast_path_result is None:
            root_fast_path_result = M.EmptyList
        if stop_reason is None:
            stop_reason = M.EmptyList
        return M.Pair(
            mode,
            M.Pair(
                job,
                M.Pair(
                    search_memo,
                    M.Pair(
                        active_packets,
                        M.Pair(
                            pending_packets,
                            M.Pair(
                                pending_packets_count,
                                M.Pair(
                                    phase,
                                    M.Pair(
                                        completed_packets,
                                        M.Pair(root_fast_path_result, M.Pair(stop_reason, M.EmptyList)),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        )

    def _comparison_state_mode(self, state):
        return M.Head(state)()

    def _comparison_state_job(self, state):
        return self._comparison_state_unpack(state)[1]

    def _comparison_state_search_memo(self, state):
        return self._comparison_state_unpack(state)[2]

    def _comparison_state_active_packets(self, state):
        return self._comparison_state_unpack(state)[3]

    def _comparison_state_pending_packets(self, state):
        return self._comparison_state_unpack(state)[4]

    def _comparison_state_pending_packets_count(self, state):
        pending_packets_count = self._comparison_state_unpack(state)[5]
        if M.IdentityCompare(pending_packets_count, M.EmptyList)() is M.truth_value:
            return M.Zero
        return pending_packets_count

    def _comparison_state_phase(self, state):
        return self._comparison_state_unpack(state)[6]

    def _comparison_state_completed_packets(self, state):
        return self._comparison_state_unpack(state)[7]

    def _comparison_state_root_fast_path_result(self, state):
        return self._comparison_state_unpack(state)[8]

    def _comparison_state_stop_reason(self, state):
        return self._comparison_state_unpack(state)[9]

    def _comparison_state_unpack(self, state):
        mode = M.Head(state)()
        fields = M.Tail(state)()
        job = M.Head(fields)()
        fields = M.Tail(fields)()
        search_memo = M.Head(fields)()
        fields = M.Tail(fields)()
        active_packets = M.Head(fields)()
        fields = M.Tail(fields)()
        pending_packets = M.Head(fields)()
        fields = M.Tail(fields)()
        pending_packets_count = M.Head(fields)()
        fields = M.Tail(fields)()
        phase = M.Head(fields)()
        fields = M.Tail(fields)()
        completed_packets = M.Head(fields)()
        fields = M.Tail(fields)()
        root_fast_path_result = M.Head(fields)()
        fields = M.Tail(fields)()
        stop_reason = M.Head(fields)()
        return (
            mode,
            job,
            search_memo,
            active_packets,
            pending_packets,
            pending_packets_count,
            phase,
            completed_packets,
            root_fast_path_result,
            stop_reason,
        )

    def _comparison_initial_state_text(self, state):
        (
            mode,
            job,
            search_memo,
            active_packets,
            pending_packets,
            pending_packets_count,
            phase,
            completed_packets,
            root_fast_path_result,
            stop_reason,
        ) = self._comparison_state_unpack(state)
        (
            job_start,
            job_goal,
            job_rules,
            job_heuristic,
            job_status,
            job_frontier,
            job_expanded,
            job_generated,
            job_frontier_size,
            job_frontier_peak,
            job_result_plan,
            job_visited,
            job_theorem_rule_cache,
            job_rewrite_rules,
        ) = self._search_job_unpack_local(job)
        stop_text = "none"
        if M.Compare(stop_reason, M.EmptyList)() is M.false_value:
            stop_text = SearchStatusText(stop_reason)()
        frontier_text = "nonempty"
        if M.IdentityCompare(job_frontier, M.EmptyList)() is M.truth_value:
            frontier_text = "empty"
        return (
            SearchModeText(mode)()
            + "(job="
            + SearchStatusText(job_status)()
            + ", frontier="
            + frontier_text
            + ", active="
            + self._nat_text(active_packets)
            + ", pending="
            + self._nat_text(pending_packets_count)
            + ", stop="
            + stop_text
            + ")"
        )

    def _comparison_initial_states_text(self, states):
        if M.IdentityCompare(states, M.EmptyList)() is M.truth_value:
            return ""
        here = self._comparison_initial_state_text(M.Head(states)())
        rest = self._comparison_initial_states_text(M.Tail(states)())
        if rest == "":
            return here
        return here + " | " + rest

    def _search_job_unpack_local(self, job):
        start = SearchJobStart(job)()
        goal = SearchJobGoal(job)()
        rules = SearchJobRules(job)()
        heuristic = SearchJobHeuristic(job)()
        status = SearchJobStatus(job)()
        frontier = SearchJobFrontier(job)()
        expanded = SearchJobExpanded(job)()
        generated = SearchJobGenerated(job)()
        frontier_size = SearchJobFrontierSize(job)()
        frontier_peak = SearchJobFrontierPeak(job)()
        result_plan = SearchJobResultPlan(job)()
        visited = SearchJobVisited(job)()
        theorem_rule_cache = SearchJobTheoremRuleCache(job)()
        rewrite_rules = SearchJobRewriteRules(job)()
        return (
            start,
            goal,
            rules,
            heuristic,
            status,
            frontier,
            expanded,
            generated,
            frontier_size,
            frontier_peak,
            result_plan,
            visited,
            theorem_rule_cache,
            rewrite_rules,
        )

    def _comparison_state_update(
        self,
        state,
        job=None,
        search_memo=None,
        active_packets=None,
        pending_packets=None,
        pending_packets_count=None,
        phase=None,
        completed_packets=None,
        root_fast_path_result=None,
        stop_reason=None,
    ):
        if job is None:
            job = self._comparison_state_job(state)
        if search_memo is None:
            search_memo = self._comparison_state_search_memo(state)
        if active_packets is None:
            active_packets = self._comparison_state_active_packets(state)
        if pending_packets is None:
            pending_packets = self._comparison_state_pending_packets(state)
            if pending_packets_count is None:
                pending_packets_count = self._comparison_state_pending_packets_count(state)
        if phase is None:
            phase = self._comparison_state_phase(state)
        if completed_packets is None:
            completed_packets = self._comparison_state_completed_packets(state)
        if root_fast_path_result is None:
            root_fast_path_result = self._comparison_state_root_fast_path_result(state)
        if stop_reason is None:
            stop_reason = self._comparison_state_stop_reason(state)
        return self._comparison_state(
            self._comparison_state_mode(state),
            job,
            search_memo,
            active_packets,
            pending_packets,
            pending_packets_count,
            phase,
            completed_packets,
            root_fast_path_result,
            stop_reason,
        )

    def _comparison_state_status(self, state):
        (
            mode,
            job,
            search_memo,
            active_packets,
            pending_packets,
            pending_packets_count,
            phase,
            completed_packets,
            root_fast_path_result,
            state_stop_reason,
        ) = self._comparison_state_unpack(state)
        if M.Compare(state_stop_reason, M.EmptyList)() is M.false_value:
            return state_stop_reason
        (
            job_start,
            job_goal,
            job_rules,
            job_heuristic,
            job_status,
            job_frontier,
            job_expanded,
            job_generated,
            job_frontier_size,
            job_frontier_peak,
            job_result_plan,
            job_visited,
            job_theorem_rule_cache,
            job_rewrite_rules,
        ) = self._search_job_unpack_local(job)
        if M.IdentityCompare(job_status, SearchSuccessLabel)() is M.truth_value:
            return SearchSuccessLabel
        if M.IdentityCompare(job_status, SearchPausedLabel)() is M.truth_value:
            return SearchPausedLabel
        if (
            M.IdentityCompare(job_frontier, M.EmptyList)() is M.truth_value
            and M.IdentityCompare(pending_packets, M.EmptyList)() is M.truth_value
            and M.NatEq(active_packets, M.Zero, self.registry)() is M.truth_value
        ):
            return SearchFailureLabel
        return SearchRunningLabel

    def _comparison_mark_state_outcome(self, state, outcome):
        if M.IdentityCompare(self._comparison_state_status(state), SearchRunningLabel)() is M.false_value:
            return state
        return self._comparison_state_update(
            state,
            active_packets=M.Zero,
            pending_packets=M.EmptyList,
            pending_packets_count=M.Zero,
            stop_reason=outcome,
        )

    def _comparison_mark_mode_outcome(self, states, mode, outcome):
        if M.IdentityCompare(states, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        state = M.Head(states)()
        next_state = state
        if M.IdentityCompare(self._comparison_state_mode(state), mode)() is M.truth_value:
            next_state = self._comparison_mark_state_outcome(state, outcome)
        return M.Pair(next_state, self._comparison_mark_mode_outcome(M.Tail(states)(), mode, outcome))

    def _comparison_mark_unselected_modes(self, states, selected_modes, outcome):
        if M.IdentityCompare(states, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        state = M.Head(states)()
        next_state = state
        if self._mode_selected(selected_modes, self._comparison_state_mode(state)) is M.false_value:
            next_state = self._comparison_mark_state_outcome(state, outcome)
        return M.Pair(next_state, self._comparison_mark_unselected_modes(M.Tail(states)(), selected_modes, outcome))

    def _comparison_mark_unfinished_states(self, states, outcome):
        if M.IdentityCompare(states, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        state = M.Head(states)()
        next_state = self._comparison_mark_state_outcome(state, outcome)
        return M.Pair(next_state, self._comparison_mark_unfinished_states(M.Tail(states)(), outcome))

    def _comparison_pause_state(self, state):
        if M.IdentityCompare(self._comparison_state_status(state), SearchRunningLabel)() is M.false_value:
            return state
        return self._comparison_state_update(
            state,
            active_packets=M.Zero,
            stop_reason=SearchPausedLabel,
        )

    def _comparison_pause_states(self, states):
        if M.IdentityCompare(states, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        state = M.Head(states)()
        next_state = self._comparison_pause_state(state)
        return M.Pair(next_state, self._comparison_pause_states(M.Tail(states)()))

    def _comparison_resume_state(self, state):
        if M.IdentityCompare(self._comparison_state_stop_reason(state), SearchPausedLabel)() is M.false_value:
            return state
        return self._comparison_state_update(
            state,
            active_packets=M.Zero,
            stop_reason=M.EmptyList,
        )

    def _comparison_resume_states(self, states):
        if M.IdentityCompare(states, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        state = M.Head(states)()
        next_state = self._comparison_resume_state(state)
        return M.Pair(next_state, self._comparison_resume_states(M.Tail(states)()))

    def _paused_comparison_job(self, states, outcome):
        return SearchComparisonJob(
            self.signature,
            self.start,
            self.goal,
            self.rules,
            self.heuristic,
            states,
            outcome,
        )()

    def _plan_from_derivation_steps(self, steps):
        if M.IdentityCompare(steps, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        step = M.Head(steps)()
        action = StepAction(step, self.registry)()
        return M.Pair(action, self._plan_from_derivation_steps(M.Tail(steps)()))

    def _comparison_result_plan(self, result_value):
        if M.Compare(result_value, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        if IsDerivation(result_value, self.registry)() is M.truth_value:
            return self._plan_from_derivation_steps(DerivationSteps(result_value, self.registry)())
        return result_value

    def _comparison_result_derivation(self, result_value):
        if M.Compare(result_value, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        if IsDerivation(result_value, self.registry)() is M.truth_value:
            return result_value
        derivation_pair = BuildDerivation(self.start, result_value, self.registry)()
        derivation = M.Head(derivation_pair)()
        self.registry = M.Head(M.Tail(derivation_pair)())()
        return derivation

    def _comparison_state_attempt_or_current(self, state):
        job = self._comparison_state_job(state)
        status = self._comparison_state_status(state)
        mode = self._comparison_state_mode(state)
        heuristic = self._heuristic_for_mode(mode)

        result_value = SearchJobResultPlan(job)()
        plan = result_value
        if M.IdentityCompare(status, SearchSuccessLabel)() is M.false_value:
            plan = M.EmptyList
        else:
            plan = self._comparison_result_plan(result_value)

        search_cost_pair = BuildSearchCost(
            plan,
            SearchJobExpanded(job)(),
            SearchJobGenerated(job)(),
            SearchJobFrontierPeak(job)(),
            status,
            self.registry,
        )()
        search_cost = M.Head(search_cost_pair)()
        self.registry = M.Head(M.Tail(search_cost_pair)())()

        proof_cost = ProofCost(M.Zero, M.Zero, M.Zero, M.Zero)()
        derivation = M.EmptyList
        if M.IdentityCompare(status, SearchSuccessLabel)() is M.truth_value:
            derivation = self._comparison_result_derivation(result_value)
            if M.Compare(derivation, M.EmptyList)() is M.false_value:
                _debug(
                    "search-compare: computing derivation cost for "
                    + SearchModeText(mode)()
                )
                proof_cost_pair = DerivationCost(derivation, self.registry)()
                proof_cost = M.Head(proof_cost_pair)()
                self.registry = M.Head(M.Tail(proof_cost_pair)())()

        total_cost_pair = BuildTotalCost(proof_cost, search_cost, heuristic, self.registry)()
        total_cost = M.Head(total_cost_pair)()
        self.registry = M.Head(M.Tail(total_cost_pair)())()

        return SearchAttempt(
            self.start,
            self.goal,
            heuristic,
            status,
            derivation,
            proof_cost,
            search_cost,
            total_cost,
        )()

    def _finished_attempts(self, states, acc):
        if M.IdentityCompare(states, M.EmptyList)() is M.truth_value:
            return self._reverse(acc, M.EmptyList)
        state = M.Head(states)()
        if M.IdentityCompare(self._comparison_state_status(state), SearchRunningLabel)() is M.truth_value:
            return self._finished_attempts(M.Tail(states)(), acc)
        _debug(
            "search-compare: finalizing attempt for "
            + SearchModeText(self._comparison_state_mode(state))()
            + " status="
            + SearchStatusText(self._comparison_state_status(state))()
        )
        attempt = self._comparison_state_attempt_or_current(state)
        _debug(
            "search-compare: attempt ready root="
            + self._comparison_root_fast_path_result_text(state)
            + " "
            + self._attempt_summary_text(attempt)
        )
        return self._finished_attempts(M.Tail(states)(), M.Pair(attempt, acc))

    def _best_attempt_in_attempts(self, attempts, best_attempt):
        if M.IdentityCompare(attempts, M.EmptyList)() is M.truth_value:
            return best_attempt
        attempt = M.Head(attempts)()
        next_best = best_attempt
        if self._attempt_better(attempt, best_attempt) is M.truth_value:
            next_best = attempt
        return self._best_attempt_in_attempts(M.Tail(attempts)(), next_best)

    def _best_finished_attempt(self, states, best_attempt):
        if M.IdentityCompare(states, M.EmptyList)() is M.truth_value:
            return best_attempt
        state = M.Head(states)()
        next_best = best_attempt
        if M.IdentityCompare(self._comparison_state_status(state), SearchRunningLabel)() is M.false_value:
            attempt = self._comparison_state_attempt_or_current(state)
            if self._attempt_better(attempt, best_attempt) is M.truth_value:
                next_best = attempt
        return self._best_finished_attempt(M.Tail(states)(), next_best)

    def _best_finished_attempt_text(self, states):
        best_attempt = self._best_finished_attempt(states, M.EmptyList)
        if M.Compare(best_attempt, M.EmptyList)() is M.truth_value:
            return "none yet"
        return (
            SearchModeText(HeuristicSearchMode(SearchAttemptHeuristic(best_attempt)())())()
            + " status="
            + SearchStatusText(SearchAttemptStatus(best_attempt)())()
            + " total="
            + self._nat_text(self._attempt_total_value(best_attempt))
        )

    def _attempt_summary_text(self, attempt):
        heuristic = SearchAttemptHeuristic(attempt)()
        mode = HeuristicSearchMode(heuristic)()
        return (
            SearchModeText(mode)()
            + " status="
            + SearchStatusText(SearchAttemptStatus(attempt)())()
            + " total="
            + self._nat_text(TotalCostValue(SearchAttemptTotalCost(attempt)())())
            + " proof="
            + self._nat_text(Pmod.ProofCostValue(SearchAttemptProofCost(attempt)())())
            + " search="
            + self._nat_text(SearchCostValue(SearchAttemptSearchCost(attempt)())())
        )

    def _attempts_summary_text(self, attempts):
        if M.IdentityCompare(attempts, M.EmptyList)() is M.truth_value:
            return "none"
        here = self._attempt_summary_text(M.Head(attempts)())
        rest = self._attempts_summary_text(M.Tail(attempts)())
        if rest == "none":
            return here
        return here + " | " + rest

    def _attempt_ties_best(self, attempt, best_attempt):
        if M.Compare(best_attempt, M.EmptyList)() is M.truth_value:
            return M.false_value
        if M.TermEqual(SearchAttemptStatus(attempt)(), SearchAttemptStatus(best_attempt)())() is M.false_value:
            return M.false_value
        if M.TermEqual(TotalCostValue(SearchAttemptTotalCost(attempt)())(), TotalCostValue(SearchAttemptTotalCost(best_attempt)())())() is M.false_value:
            return M.false_value
        return M.truth_value

    def _best_attempt_modes_text(self, attempts, best_attempt):
        if M.IdentityCompare(attempts, M.EmptyList)() is M.truth_value:
            return ""
        attempt = M.Head(attempts)()
        rest = self._best_attempt_modes_text(M.Tail(attempts)(), best_attempt)
        if self._attempt_ties_best(attempt, best_attempt) is M.false_value:
            return rest
        here = SearchModeText(HeuristicSearchMode(SearchAttemptHeuristic(attempt)())())()
        if rest == "":
            return here
        return here + ", " + rest

    def _best_attempt_mode_count(self, attempts, best_attempt):
        if M.IdentityCompare(attempts, M.EmptyList)() is M.truth_value:
            return M.Zero
        rest = self._best_attempt_mode_count(M.Tail(attempts)(), best_attempt)
        if self._attempt_ties_best(M.Head(attempts)(), best_attempt) is M.false_value:
            return rest
        return self._succ_nat_local(rest)

    def _search_mode_uses_global_visited(self, mode):
        return M.OrAtom(
            M.OrAtom(M.IdentityCompare(mode, BFSLabel)(), M.IdentityCompare(mode, BeamLabel)())(),
            M.IdentityCompare(mode, AStarLabel)(),
        )()

    def _initial_compare_job_visited(self, mode):
        if self._search_mode_uses_global_visited(mode) is M.false_value:
            return M.EmptyList
        return self._tree_insert(M.EmptyList, self.start)

    def _fresh_compare_job(self, mode):
        heuristic = self._heuristic_for_mode(mode)
        start_state = SearchState(self.start, M.EmptyList, M.EmptyList, self._comparison_rule_count)()
        frontier = M.Pair(start_state, M.EmptyList)
        return SearchJob(
            self.start,
            self.goal,
            self.rules,
            heuristic,
            SearchRunningLabel,
            frontier,
            M.Zero,
            M.Zero,
            M.Zero,
            M.EmptyList,
            self._initial_compare_job_visited(mode),
            M.EmptyList,
            M.EmptyList,
            M.one,
        )()

    def _knowledge_has_fact(self, facts, target):
        if M.IdentityCompare(facts, M.EmptyList)() is M.truth_value:
            return M.false_value
        fact = M.Head(facts)()
        if M.TermEqual(fact, target)() is M.truth_value:
            return M.truth_value
        return self._knowledge_has_fact(M.Tail(facts)(), target)

    def _premises_satisfied_by_bindings(self, premises, facts, bindings):
        if M.IdentityCompare(premises, M.EmptyList)() is M.truth_value:
            return M.truth_value
        premise = M.Head(premises)()
        instantiated = M.Instantiate(premise, bindings)()
        concrete_premise = M.Head(instantiated)()
        if self._knowledge_has_fact(facts, concrete_premise) is M.false_value:
            return M.false_value
        return self._premises_satisfied_by_bindings(M.Tail(premises)(), facts, bindings)

    def _match_premises(self, premises, facts, bindings):
        if M.IdentityCompare(premises, M.EmptyList)() is M.truth_value:
            return M.Pair(M.truth_value, bindings)
        premise = M.Head(premises)()
        rest = M.Tail(premises)()
        return self._match_premise_against_facts(premise, rest, facts, facts, bindings)

    def _match_premise_against_facts(self, premise, rest_premises, facts, all_facts, bindings):
        if M.IdentityCompare(facts, M.EmptyList)() is M.truth_value:
            return M.Pair(M.false_value, M.EmptyList)

        fact = M.Head(facts)()
        match = M.Match(premise, fact)()
        flag = M.Head(match)()
        bound = M.Tail(match)()
        if M.IdentityCompare(flag, M.truth_value)() is M.truth_value:
            merged = M.MergeBindings(bindings, bound)()
            merged_flag = M.Head(merged)()
            merged_bindings = M.Tail(merged)()
            if M.IdentityCompare(merged_flag, M.truth_value)() is M.truth_value:
                rest_result = self._match_premises(rest_premises, all_facts, merged_bindings)
                if M.IdentityCompare(M.Head(rest_result)(), M.truth_value)() is M.truth_value:
                    return rest_result

        return self._match_premise_against_facts(premise, rest_premises, M.Tail(facts)(), all_facts, bindings)

    def _direct_next_term(self, rule, current):
        if IsKnowledge(current)() is M.truth_value:
            facts = KnowledgeFacts(current)()
            bindings_pair = self._match_premises(RulePremises(rule)(), facts, M.EmptyList)
            bindings_flag = M.Head(bindings_pair)()
            bindings = M.Tail(bindings_pair)()
            if M.IdentityCompare(bindings_flag, M.truth_value)() is M.false_value:
                return current
            inst = M.Instantiate(RuleReplacement(rule)(), bindings)()
            conclusion = M.Head(inst)()
            if self._knowledge_has_fact(facts, conclusion) is M.truth_value:
                return current
            return HeuristicCanonicalize(Knowledge(M.Pair(conclusion, facts))(), self.heuristic, self.registry)()

        if RuleIsUnary(rule)() is M.false_value:
            return current
        match = M.Match(RulePattern(rule)(), current)()
        flag = M.Head(match)()
        binds = M.Tail(match)()
        if M.IdentityCompare(flag, M.truth_value)() is M.truth_value:
            inst = M.Instantiate(RuleReplacement(rule)(), binds)()
            return HeuristicCanonicalize(M.Head(inst)(), self.heuristic, self.registry)()
        return current

    def _comparison_goal_reached(self, current, goal):
        if IsKnowledge(current)() is M.truth_value:
            return self._knowledge_has_fact(KnowledgeFacts(current)(), goal)
        return M.TermEqual(current, goal)()

    def _comparison_rule_anchor(self, rule):
        premises = RulePremises(rule)()
        if M.IdentityCompare(premises, M.EmptyList)() is M.false_value:
            return M.Head(premises)()
        if RuleIsUnary(rule)() is M.truth_value:
            return RulePattern(rule)()
        return M.EmptyList

    def _comparison_anchor_matches_facts(self, anchor, facts):
        if M.IdentityCompare(anchor, M.EmptyList)() is M.truth_value:
            return M.false_value
        if M.IdentityCompare(facts, M.EmptyList)() is M.truth_value:
            return M.false_value
        fact = M.Head(facts)()
        match = M.Match(anchor, fact)()
        if M.IdentityCompare(M.Head(match)(), M.truth_value)() is M.truth_value:
            return M.truth_value
        return self._comparison_anchor_matches_facts(anchor, M.Tail(facts)())

    def _comparison_candidate_rules_for_knowledge(self, rules, facts):
        if M.IdentityCompare(rules, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        rule = M.Head(rules)()
        rest = self._comparison_candidate_rules_for_knowledge(M.Tail(rules)(), facts)
        anchor = self._comparison_rule_anchor(rule)
        if self._comparison_anchor_matches_facts(anchor, facts) is M.truth_value:
            return M.Pair(rule, rest)
        return rest

    def _find_goal_instantiating_plan(self, rule_list, current):
        if M.IdentityCompare(rule_list, M.EmptyList)() is M.truth_value:
            return M.EmptyList

        rule = M.Head(rule_list)()
        replacement_match = M.Match(RuleReplacement(rule)(), self.goal)()
        replacement_flag = M.Head(replacement_match)()
        replacement_bindings = M.Tail(replacement_match)()

        if M.IdentityCompare(replacement_flag, M.truth_value)() is M.truth_value:
            if IsKnowledge(current)() is M.truth_value:
                facts = KnowledgeFacts(current)()
                if self._premises_satisfied_by_bindings(RulePremises(rule)(), facts, replacement_bindings) is M.truth_value:
                    return M.Pair(TheoremAction(rule)(), M.Pair(replacement_bindings, M.EmptyList))
            elif RuleIsUnary(rule)() is M.truth_value:
                premise_match = M.Match(RulePattern(rule)(), current)()
                premise_flag = M.Head(premise_match)()
                premise_bindings = M.Tail(premise_match)()
                if M.IdentityCompare(premise_flag, M.truth_value)() is M.truth_value:
                    merged = M.MergeBindings(replacement_bindings, premise_bindings)()
                    merged_flag = M.Head(merged)()
                    merged_bindings = M.Tail(merged)()
                    if M.IdentityCompare(merged_flag, M.truth_value)() is M.truth_value:
                        return M.Pair(TheoremAction(rule)(), M.Pair(merged_bindings, M.EmptyList))

        return self._find_goal_instantiating_plan(M.Tail(rule_list)(), current)

    def _find_immediate_rule_plan(self, rule_list, current):
        if M.IdentityCompare(rule_list, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        rule = M.Head(rule_list)()
        next_term = self._direct_next_term(rule, current)
        if M.TermEqual(next_term, current)() is M.false_value:
            if IsKnowledge(next_term)() is M.truth_value:
                if self._knowledge_has_fact(KnowledgeFacts(next_term)(), self.goal) is M.truth_value:
                    return M.Pair(TheoremAction(rule)(), M.EmptyList)
            elif M.TermEqual(next_term, self.goal)() is M.truth_value:
                return M.Pair(TheoremAction(rule)(), M.EmptyList)
        return self._find_immediate_rule_plan(M.Tail(rule_list)(), current)

    def _derivation_reaches_goal(self, derivation):
        end = DerivationEnd(derivation, self.registry)()
        if IsKnowledge(end)() is M.truth_value:
            return self._knowledge_has_fact(KnowledgeFacts(end)(), self.goal)
        return M.TermEqual(end, self.goal)()

    def _comparison_success_job(self, state, result_plan):
        job = self._comparison_state_job(state)
        return SearchJob(
            SearchJobStart(job)(),
            SearchJobGoal(job)(),
            SearchJobRules(job)(),
            SearchJobHeuristic(job)(),
            SearchSuccessLabel,
            M.EmptyList,
            M.Zero,
            M.Zero,
            M.Zero,
            result_plan,
            SearchJobVisited(job)(),
            SearchJobTheoremRuleCache(job)(),
            SearchJobRewriteRules(job)(),
            M.Zero,
        )()

    def _comparison_cached_derivation_plan(self):
        cached = self.graph.lookup_derivation(self.start, self.goal)
        if M.Compare(cached, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        _debug("search-compare: shared root cache hit for " + self._mode_chain_text(self._mode_chain()))
        return cached

    def _comparison_schema_derivation_plan(self):
        schema_hit = self.graph.lookup_derivation_schema(self.start, self.goal)
        if M.Compare(schema_hit, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        plan = M.Head(schema_hit)()
        bindings = M.Head(M.Tail(schema_hit)())()
        derivation_pair = BuildDerivation(self.start, plan, self.registry, bindings)()
        derivation = M.Head(derivation_pair)()
        self.registry = M.Head(M.Tail(derivation_pair)())()
        self.graph._replace_context(constructors=self.registry)
        if M.Compare(derivation, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        if self._derivation_reaches_goal(derivation) is M.false_value:
            return M.EmptyList
        stored = self.graph.add_derivation(self.start, self.goal, derivation)
        _debug("search-compare: shared root schema hit for " + self._mode_chain_text(self._mode_chain()))
        _debug("search-compare: shared root schema plan=" + PrettyPlanChain(plan, self.registry)())
        return stored

    def _comparison_root_fast_path_result(self):
        cached = self._comparison_cached_derivation_plan()
        if M.Compare(cached, M.EmptyList)() is M.false_value:
            return M.Pair(SearchRootCacheResultLabel, M.Pair(cached, M.EmptyList))

        schema = self._comparison_schema_derivation_plan()
        if M.Compare(schema, M.EmptyList)() is M.false_value:
            return M.Pair(SearchRootSchemaResultLabel, M.Pair(schema, M.EmptyList))

        root_job = self._fresh_compare_job(BFSLabel)
        frontier = SearchJobFrontier(root_job)()
        if M.IdentityCompare(frontier, M.EmptyList)() is M.false_value:
            current = SearchStateCurrent(M.Head(frontier)())()
            immediate_plan = self._find_immediate_rule_plan(self._comparison_root_candidate_rules(root_job), current)
            if M.Compare(immediate_plan, M.EmptyList)() is M.false_value:
                _debug("search-compare: shared root immediate theorem hit for " + self._mode_chain_text(self._mode_chain()))
                _debug("search-compare: shared root immediate plan=" + PrettyPlanChain(immediate_plan, self.registry)())
                return M.Pair(SearchRootImmediateResultLabel, M.Pair(immediate_plan, M.EmptyList))

        _debug("search-compare: shared root fast path miss; entering branch-first packet search")
        return M.Pair(SearchNoRootFastPathLabel, M.Pair(M.EmptyList, M.EmptyList))

    def _comparison_root_fast_path_state(self, state, result_label, result_plan):
        if M.IdentityCompare(self._comparison_state_status(state), SearchRunningLabel)() is M.false_value:
            return state
        mode_text = SearchModeText(self._comparison_state_mode(state))()
        if M.Compare(result_plan, M.EmptyList)() is M.truth_value:
            _debug(
                "search-compare: "
                + mode_text
                + " root result="
                + self._comparison_root_result_text(result_label)
                + " so it continues into packet search"
            )
            return self._comparison_state_update(
                state,
                phase=SearchPacketSearchPhaseLabel,
                root_fast_path_result=result_label,
            )
        _debug(
            "search-compare: "
            + mode_text
            + " finished from shared root result="
            + self._comparison_root_result_text(result_label)
            + " before packet search"
        )
        return self._comparison_state_update(
            state,
            job=self._comparison_success_job(state, result_plan),
            root_fast_path_result=result_label,
        )

    def _comparison_states_after_root_fast_paths(self, states):
        result = self._comparison_root_fast_path_result()
        result_label = M.Head(result)()
        result_plan = M.Head(M.Tail(result)())()
        if M.IdentityCompare(result_label, SearchRootSchemaResultLabel)() is M.truth_value:
            _debug(
                "search-compare: shared root schema detail="
                + PrettyPlanChain(self._comparison_result_plan(result_plan), self.registry)()
            )
        _debug(
            "search-compare: applying shared root result="
            + self._comparison_root_result_text(result_label)
            + " to "
            + self._nat_text(self._count_states(states))
            + " mode states"
        )
        if M.Compare(result_plan, M.EmptyList)() is M.false_value:
            _debug("search-compare: shared root result resolves all mode states before packet search")
            return self._comparison_states_with_root_fast_path_result(states, result_label, result_plan)
        _debug("search-compare: shared root miss marks all mode states as packet search")
        return self._comparison_states_with_root_fast_path_result(states, result_label, result_plan)

    def _comparison_states_with_root_fast_path_result(self, states, result_label, result_plan):
        if M.IdentityCompare(states, M.EmptyList)() is M.truth_value:
            _debug("search-compare: shared root result applied to all mode states")
            return M.EmptyList
        state = M.Head(states)()
        _debug(
            "search-compare: marking "
            + SearchModeText(self._comparison_state_mode(state))()
            + " with shared root result="
            + self._comparison_root_result_text(result_label)
        )
        next_state = self._comparison_root_fast_path_state(state, result_label, result_plan)
        return M.Pair(next_state, self._comparison_states_with_root_fast_path_result(M.Tail(states)(), result_label, result_plan))

    def _comparison_root_result_text(self, result_label):
        if M.IdentityCompare(result_label, SearchRootCacheResultLabel)() is M.truth_value:
            return "cache"
        if M.IdentityCompare(result_label, SearchRootSchemaResultLabel)() is M.truth_value:
            return "schema"
        if M.IdentityCompare(result_label, SearchRootGoalResultLabel)() is M.truth_value:
            return "goal"
        if M.IdentityCompare(result_label, SearchRootImmediateResultLabel)() is M.truth_value:
            return "immediate"
        if M.IdentityCompare(result_label, SearchNoRootFastPathLabel)() is M.truth_value:
            return "miss"
        return "unknown"

    def _count_states(self, states):
        count_pair = M.Count(states, self.registry)()
        count = M.Head(count_pair)()
        self.registry = M.Head(M.Tail(count_pair)())()
        return count

    def _comparison_states(self, modes):
        if M.IdentityCompare(modes, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        mode = M.Head(modes)()
        state = self._comparison_state(mode, self._fresh_compare_job(mode), M.EmptyList, M.Zero)
        return M.Pair(state, self._comparison_states(M.Tail(modes)()))

    def _comparison_state_for_mode(self, states, mode):
        if M.IdentityCompare(states, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        state = M.Head(states)()
        if M.IdentityCompare(self._comparison_state_mode(state), mode)() is M.truth_value:
            return state
        return self._comparison_state_for_mode(M.Tail(states)(), mode)

    def _replace_comparison_state(self, states, mode, next_state):
        if M.IdentityCompare(states, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        state = M.Head(states)()
        tail = self._replace_comparison_state(M.Tail(states)(), mode, next_state)
        if M.IdentityCompare(self._comparison_state_mode(state), mode)() is M.truth_value:
            return M.Pair(next_state, tail)
        return M.Pair(state, tail)

    def _comparison_all_finished(self, states):
        if M.IdentityCompare(states, M.EmptyList)() is M.truth_value:
            return M.truth_value
        if M.IdentityCompare(self._comparison_state_status(M.Head(states)()), SearchRunningLabel)() is M.truth_value:
            return M.false_value
        return self._comparison_all_finished(M.Tail(states)())

    def _succ_nat_local(self, value):
        if M.IdentityCompare(value, M.EmptyList)() is M.truth_value:
            value = M.Zero
        try:
            succ_text = Gmpmod.GMPSuccText(Gmpmod.GMPRepText(value())())()
            if Gmpmod.GMPEqualText(succ_text, "0")() is M.truth_value:
                return M.Zero
            if Gmpmod.GMPEqualText(succ_text, "1")() is M.truth_value:
                return M.one
            if Gmpmod.GMPEqualText(succ_text, "2")() is M.truth_value:
                return M.two
            if Gmpmod.GMPEqualText(succ_text, "3")() is M.truth_value:
                return M.three
            if Gmpmod.GMPEqualText(succ_text, "4")() is M.truth_value:
                return M.four
            if Gmpmod.GMPEqualText(succ_text, "5")() is M.truth_value:
                return M.five
            if Gmpmod.GMPEqualText(succ_text, "6")() is M.truth_value:
                return M.six
            if Gmpmod.GMPEqualText(succ_text, "7")() is M.truth_value:
                return M.seven
            if Gmpmod.GMPEqualText(succ_text, "8")() is M.truth_value:
                return M.eight
            if Gmpmod.GMPEqualText(succ_text, "9")() is M.truth_value:
                return M.nine
            succ = M.Atom()
            succ.value = Gmpmod.GMPRep(succ_text)
            return succ
        except Exception:
            pass
        rep = M.NatRepOf(value, self.registry)()
        if M.IdentityCompare(rep, M.EmptyList)() is M.false_value:
            succ_text = Gmpmod.GMPSuccText(Gmpmod.GMPRepText(rep)())()
            if Gmpmod.GMPEqualText(succ_text, "0")() is M.truth_value:
                return M.Zero
            if Gmpmod.GMPEqualText(succ_text, "1")() is M.truth_value:
                return M.one
            if Gmpmod.GMPEqualText(succ_text, "2")() is M.truth_value:
                return M.two
            if Gmpmod.GMPEqualText(succ_text, "3")() is M.truth_value:
                return M.three
            if Gmpmod.GMPEqualText(succ_text, "4")() is M.truth_value:
                return M.four
            if Gmpmod.GMPEqualText(succ_text, "5")() is M.truth_value:
                return M.five
            if Gmpmod.GMPEqualText(succ_text, "6")() is M.truth_value:
                return M.six
            if Gmpmod.GMPEqualText(succ_text, "7")() is M.truth_value:
                return M.seven
            if Gmpmod.GMPEqualText(succ_text, "8")() is M.truth_value:
                return M.eight
            if Gmpmod.GMPEqualText(succ_text, "9")() is M.truth_value:
                return M.nine
            succ = M.Atom()
            succ.value = Gmpmod.GMPRep(succ_text)
            return succ
        pair = M.Succ(value, self.registry)()
        self.registry = M.Head(M.Tail(pair)())()
        return M.Head(pair)()

    def _nat_add_local(self, left, right):
        if M.IdentityCompare(left, M.EmptyList)() is M.truth_value:
            left = M.Zero
        if M.IdentityCompare(right, M.EmptyList)() is M.truth_value:
            right = M.Zero
        try:
            sum_text = Gmpmod.GMPAddText(
                Gmpmod.GMPRepText(left())(),
                Gmpmod.GMPRepText(right())(),
            )()
            if Gmpmod.GMPEqualText(sum_text, "0")() is M.truth_value:
                return M.Zero
            if Gmpmod.GMPEqualText(sum_text, "1")() is M.truth_value:
                return M.one
            if Gmpmod.GMPEqualText(sum_text, "2")() is M.truth_value:
                return M.two
            if Gmpmod.GMPEqualText(sum_text, "3")() is M.truth_value:
                return M.three
            if Gmpmod.GMPEqualText(sum_text, "4")() is M.truth_value:
                return M.four
            if Gmpmod.GMPEqualText(sum_text, "5")() is M.truth_value:
                return M.five
            if Gmpmod.GMPEqualText(sum_text, "6")() is M.truth_value:
                return M.six
            if Gmpmod.GMPEqualText(sum_text, "7")() is M.truth_value:
                return M.seven
            if Gmpmod.GMPEqualText(sum_text, "8")() is M.truth_value:
                return M.eight
            if Gmpmod.GMPEqualText(sum_text, "9")() is M.truth_value:
                return M.nine
            total = M.Atom()
            total.value = Gmpmod.GMPRep(sum_text)
            return total
        except Exception:
            pass
        left_rep = M.NatRepOf(left, self.registry)()
        right_rep = M.NatRepOf(right, self.registry)()
        if M.IdentityCompare(left_rep, M.EmptyList)() is M.false_value:
            if M.IdentityCompare(right_rep, M.EmptyList)() is M.false_value:
                sum_text = Gmpmod.GMPAddText(
                    Gmpmod.GMPRepText(left_rep)(),
                    Gmpmod.GMPRepText(right_rep)(),
                )()
                if Gmpmod.GMPEqualText(sum_text, "0")() is M.truth_value:
                    return M.Zero
                if Gmpmod.GMPEqualText(sum_text, "1")() is M.truth_value:
                    return M.one
                if Gmpmod.GMPEqualText(sum_text, "2")() is M.truth_value:
                    return M.two
                if Gmpmod.GMPEqualText(sum_text, "3")() is M.truth_value:
                    return M.three
                if Gmpmod.GMPEqualText(sum_text, "4")() is M.truth_value:
                    return M.four
                if Gmpmod.GMPEqualText(sum_text, "5")() is M.truth_value:
                    return M.five
                if Gmpmod.GMPEqualText(sum_text, "6")() is M.truth_value:
                    return M.six
                if Gmpmod.GMPEqualText(sum_text, "7")() is M.truth_value:
                    return M.seven
                if Gmpmod.GMPEqualText(sum_text, "8")() is M.truth_value:
                    return M.eight
                if Gmpmod.GMPEqualText(sum_text, "9")() is M.truth_value:
                    return M.nine
                total = M.Atom()
                total.value = Gmpmod.GMPRep(sum_text)
                return total
        pair = M.Add(left, right, self.registry)()
        self.registry = M.Head(M.Tail(pair)())()
        return M.Head(pair)()

    def _nat_max_local(self, left, right):
        if M.NatLess(left, right, self.registry)() is M.truth_value:
            return right
        return left

    def _nat_min_local(self, left, right):
        if M.NatLess(left, right, self.registry)() is M.truth_value:
            return left
        return right

    def _pred_nat_or_zero_local(self, value):
        if M.IdentityCompare(value, M.EmptyList)() is M.truth_value:
            return M.Zero
        try:
            pred_text = Gmpmod.GMPPredText(Gmpmod.GMPRepText(value())())()
            if Gmpmod.GMPEqualText(pred_text, "0")() is M.truth_value:
                return M.Zero
            pred = M.Atom()
            pred.value = Gmpmod.GMPRep(pred_text)
            return pred
        except Exception:
            pass
        rep = M.NatRepOf(value, self.registry)()
        if M.IdentityCompare(rep, M.EmptyList)() is M.false_value:
            pred_text = Gmpmod.GMPPredText(Gmpmod.GMPRepText(rep)())()
            if Gmpmod.GMPEqualText(pred_text, "0")() is M.truth_value:
                return M.Zero
            pred = M.Atom()
            pred.value = Gmpmod.GMPRep(pred_text)
            return pred
        if M.NatEq(value, M.Zero, self.registry)() is M.truth_value:
            return M.Zero
        pred_pair = M.NatPred(value, self.registry)()
        pred = M.Head(pred_pair)()
        self.registry = M.Head(M.Tail(pred_pair)())()
        return pred

    def _nat_sub_or_zero_local(self, left, right):
        if M.NatEq(right, M.Zero, self.registry)() is M.truth_value:
            return left
        if M.NatEq(left, M.Zero, self.registry)() is M.truth_value:
            return M.Zero
        return self._nat_sub_or_zero_local(
            self._pred_nat_or_zero_local(left),
            self._pred_nat_or_zero_local(right),
        )

    def _mode_uses_global_visited(self, mode):
        return M.OrAtom(
            M.OrAtom(M.IdentityCompare(mode, BFSLabel)(), M.IdentityCompare(mode, BeamLabel)())(),
            M.IdentityCompare(mode, AStarLabel)(),
        )()

    def _tree_contains(self, tree, key):
        if M.IdentityCompare(tree, M.EmptyList)() is M.truth_value:
            return M.false_value
        found = self._tree_lookup_fact(tree, key)
        if M.IdentityCompare(found, M.EmptyList)() is M.truth_value:
            return M.false_value
        return M.truth_value

    def _tree_lookup_fact(self, tree, key):
        return SearchPatriciaLookupByKey(tree, key, self.registry)()

    def _tree_insert(self, tree, key):
        return SearchPatriciaInsertByKey(tree, key, M.Pair(key, M.EmptyList), self.registry)()

    def _comparison_filter_new_child(self, child, visited):
        if M.IdentityCompare(child, M.EmptyList)() is M.truth_value:
            return child, visited
        child_current = SearchStateCurrent(child)()
        if self._tree_contains(visited, child_current) is M.truth_value:
            return M.EmptyList, visited
        next_visited = self._tree_insert(visited, child_current)
        return child, next_visited

    def _decode_parallel_worker_payload(self, payload, mode=M.EmptyList, packet_token=M.EmptyList):
        if payload is None:
            return SearchWorkerResult(
                mode,
                SearchFailureLabel,
                M.Zero,
                M.Zero,
                M.Zero,
                M.Zero,
                M.Zero,
                M.Zero,
                M.Zero,
                M.EmptyList,
                M.EmptyList,
                M.EmptyList,
                M.Zero,
                M.EmptyList,
                packet_token,
            )()
        return payload

    def _decoded_mode(self, decoded):
        return SearchWorkerResultMode(decoded)()

    def _decoded_status(self, decoded):
        return SearchWorkerResultStatus(decoded)()

    def _decoded_total_value(self, decoded):
        return SearchWorkerResultTotalValue(decoded)()

    def _decoded_proof_value(self, decoded):
        return SearchWorkerResultProofValue(decoded)()

    def _decoded_search_value(self, decoded):
        return SearchWorkerResultSearchValue(decoded)()

    def _decoded_expanded(self, decoded):
        return SearchWorkerResultExpanded(decoded)()

    def _decoded_generated(self, decoded):
        return SearchWorkerResultGenerated(decoded)()

    def _decoded_frontier_peak(self, decoded):
        return SearchWorkerResultFrontierPeak(decoded)()

    def _decoded_found_depth(self, decoded):
        return SearchWorkerResultFoundDepth(decoded)()

    def _decoded_job(self, decoded):
        return SearchWorkerResultJob(decoded)()

    def _decoded_search_memo(self, decoded):
        return SearchWorkerResultSearchMemo(decoded)()

    def _decoded_ready_packets(self, decoded):
        packets = SearchWorkerResultReadyPackets(decoded)()
        if M.IdentityCompare(packets, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        return packets

    def _decoded_ready_packet_count(self, decoded):
        packet_count = SearchWorkerResultReadyPacketCount(decoded)()
        if M.IdentityCompare(packet_count, M.EmptyList)() is M.truth_value:
            return M.Zero
        return packet_count

    def _decoded_registry(self, decoded):
        registry = SearchWorkerResultRegistry(decoded)()
        if M.IdentityCompare(registry, M.EmptyList)() is M.truth_value:
            return M.Tree(M.EmptyList)
        return registry

    def _decoded_packet_token(self, decoded):
        return SearchWorkerResultPacketToken(decoded)()

    def _decoded_summary_text(self, decoded):
        return (
            "status="
            + SearchStatusText(self._decoded_status(decoded))()
            + " total="
            + self._nat_text(self._decoded_total_value(decoded))
            + " proof="
            + self._nat_text(self._decoded_proof_value(decoded))
            + " search="
            + self._nat_text(self._decoded_search_value(decoded))
            + " expanded="
            + self._nat_text(self._decoded_expanded(decoded))
            + " generated="
            + self._nat_text(self._decoded_generated(decoded))
            + " peak="
            + self._nat_text(self._decoded_frontier_peak(decoded))
            + " ready-packets="
            + self._nat_text(self._decoded_ready_packet_count(decoded))
        )

    def _collect_map_entries(self, tree):
        if M.IdentityCompare(tree, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        if SearchPatriciaIsTree(tree)() is M.truth_value:
            return SearchPatriciaEntries(tree)()
        return self._collect_legacy_map_entries(tree)

    def _collect_legacy_map_entries(self, tree):
        return Tmod.TreeEntries(tree)()

    def _merge_tree_entries_legacy(self, dst_tree, entries):
        if M.IdentityCompare(entries, M.EmptyList)() is M.truth_value:
            return dst_tree
        entry = M.Head(entries)()
        key = M.Head(entry)()
        fact = M.Head(M.Tail(entry)())()
        if M.IdentityCompare(dst_tree, M.EmptyList)() is M.truth_value:
            next_tree = M.TreeInsert(M.Tree(M.EmptyList), key, fact, self.registry)()
        else:
            next_tree = M.TreeInsert(dst_tree, key, fact, self.registry)()
        return self._merge_tree_entries_legacy(next_tree, M.Tail(entries)())

    def _merge_tree_entries_patricia(self, dst_tree, entries):
        if M.IdentityCompare(entries, M.EmptyList)() is M.truth_value:
            return dst_tree
        entry = M.Head(entries)()
        key = M.Head(entry)()
        fact = M.Head(M.Tail(entry)())()
        next_tree = SearchPatriciaInsertByKey(dst_tree, key, fact, self.registry)()
        return self._merge_tree_entries_patricia(next_tree, M.Tail(entries)())

    def _merge_legacy_entries_to_patricia(self, dst_tree, entries):
        if M.IdentityCompare(entries, M.EmptyList)() is M.truth_value:
            return dst_tree
        entry = M.Head(entries)()
        key = M.Head(entry)()
        fact = M.Head(M.Tail(entry)())()
        next_tree = SearchPatriciaInsertByKey(dst_tree, key, fact, self.registry)()
        return self._merge_legacy_entries_to_patricia(next_tree, M.Tail(entries)())

    def _merge_tree(self, left_tree, right_tree):
        if M.IdentityCompare(right_tree, M.EmptyList)() is M.truth_value:
            return left_tree
        if SearchPatriciaIsTree(right_tree)() is M.truth_value:
            base_tree = left_tree
            if M.IdentityCompare(base_tree, M.EmptyList)() is M.truth_value:
                return self._merge_tree_entries_patricia(M.EmptyList, SearchPatriciaEntries(right_tree)())
            if SearchPatriciaIsTree(base_tree)() is M.truth_value:
                return self._merge_tree_entries_patricia(base_tree, SearchPatriciaEntries(right_tree)())
            base_tree = self._merge_legacy_entries_to_patricia(M.EmptyList, self._collect_legacy_map_entries(base_tree))
            return self._merge_tree_entries_patricia(base_tree, SearchPatriciaEntries(right_tree)())
        if M.IdentityCompare(left_tree, M.EmptyList)() is M.truth_value:
            left_tree = M.Tree(M.EmptyList)
        return self._merge_tree_entries_legacy(left_tree, self._collect_legacy_map_entries(right_tree))

    def _astar_goal_distance(self, current, goal):
        if M.TermEqual(current, goal)() is M.truth_value:
            return M.Zero
        if IsKnowledge(current)() is M.truth_value:
            return M.one
        current_is_pair = M.IsPair(current)()
        goal_is_pair = M.IsPair(goal)()
        if M.AndAtom(current_is_pair, goal_is_pair)() is M.truth_value:
            head_distance = self._astar_goal_distance(M.Head(current)(), M.Head(goal)())
            tail_distance = self._astar_goal_distance(M.Tail(current)(), M.Tail(goal)())
            pair = M.Add(head_distance, tail_distance, self.registry)()
            value = M.Head(pair)()
            self.registry = M.Head(M.Tail(pair)())()
            return value
        if M.OrAtom(current_is_pair, goal_is_pair)() is M.truth_value:
            return M.two
        current_head = TermHead(current, self.registry)()
        goal_head = TermHead(goal, self.registry)()
        if M.IdentityCompare(current_head, M.EmptyList)() is M.truth_value:
            return M.two
        if M.IdentityCompare(goal_head, M.EmptyList)() is M.truth_value:
            return M.two
        if M.IdentityCompare(current_head, goal_head)() is M.truth_value:
            return M.one
        return M.two

    def _astar_path_cost(self, state):
        count_pair = M.Count(SearchStatePlan(state)(), self.registry)()
        value = M.Head(count_pair)()
        self.registry = M.Head(M.Tail(count_pair)())()
        return value

    def _astar_frontier_score(self, state):
        path_cost = self._astar_path_cost(state)
        goal_distance = self._astar_goal_distance(SearchStateCurrent(state)(), self.goal)
        pair = M.Add(path_cost, goal_distance, self.registry)()
        value = M.Head(pair)()
        self.registry = M.Head(M.Tail(pair)())()
        return value

    def _astar_insert_state(self, frontier, state):
        if M.IdentityCompare(frontier, M.EmptyList)() is M.truth_value:
            return M.Pair(state, M.EmptyList)
        head_state = M.Head(frontier)()
        if M.NatLess(self._astar_frontier_score(state), self._astar_frontier_score(head_state), self.registry)() is M.truth_value:
            return M.Pair(state, frontier)
        return M.Pair(head_state, self._astar_insert_state(M.Tail(frontier)(), state))

    def _astar_merge_frontiers(self, frontier, incoming):
        if M.IdentityCompare(incoming, M.EmptyList)() is M.truth_value:
            return frontier
        next_frontier = self._astar_insert_state(frontier, M.Head(incoming)())
        return self._astar_merge_frontiers(next_frontier, M.Tail(incoming)())

    def _merge_frontier(self, mode, base_frontier, returned_frontier):
        if M.IdentityCompare(mode, DFSLabel)() is M.truth_value:
            return Append(returned_frontier, base_frontier)()
        if M.IdentityCompare(mode, RewriteDFSLabel)() is M.truth_value:
            return Append(returned_frontier, base_frontier)()
        if M.IdentityCompare(mode, AStarLabel)() is M.truth_value:
            return self._astar_merge_frontiers(base_frontier, returned_frontier)
        return Append(base_frontier, returned_frontier)()

    def _merge_compare_jobs(self, mode, base_job, returned_job):
        merged_frontier = self._merge_frontier(
            mode,
            SearchJobFrontier(base_job)(),
            SearchJobFrontier(returned_job)(),
        )
        if M.IdentityCompare(merged_frontier, M.EmptyList)() is M.truth_value:
            merged_frontier_size = M.Zero
        else:
            merged_frontier_size = M.Atom()
            merged_frontier_size.value = M.CountRep(merged_frontier)()

        expanded_pair = M.Add(
            SearchJobExpanded(base_job)(),
            SearchJobExpanded(returned_job)(),
            self.registry,
        )()
        expanded = M.Head(expanded_pair)()
        self.registry = M.Head(M.Tail(expanded_pair)())()

        generated_pair = M.Add(
            SearchJobGenerated(base_job)(),
            SearchJobGenerated(returned_job)(),
            self.registry,
        )()
        generated = M.Head(generated_pair)()
        self.registry = M.Head(M.Tail(generated_pair)())()

        frontier_peak = SearchJobFrontierPeak(base_job)()
        if M.NatLess(frontier_peak, SearchJobFrontierPeak(returned_job)(), self.registry)() is M.truth_value:
            frontier_peak = SearchJobFrontierPeak(returned_job)()
        if M.NatLess(frontier_peak, merged_frontier_size, self.registry)() is M.truth_value:
            frontier_peak = merged_frontier_size

        merged_visited = self._merge_tree(
            SearchJobVisited(base_job)(),
            SearchJobVisited(returned_job)(),
        )
        merged_theorem_cache = M.EmptyList
        rewrite_rules = SearchJobRewriteRules(base_job)()
        if M.IdentityCompare(rewrite_rules, M.EmptyList)() is M.truth_value:
            rewrite_rules = SearchJobRewriteRules(returned_job)()

        status = SearchRunningLabel
        result_plan = M.EmptyList
        if M.IdentityCompare(SearchJobStatus(returned_job)(), SearchSuccessLabel)() is M.truth_value:
            status = SearchSuccessLabel
            result_plan = SearchJobResultPlan(returned_job)()
            merged_frontier = M.EmptyList
            merged_frontier_size = M.Zero
        elif M.IdentityCompare(merged_frontier, M.EmptyList)() is M.truth_value:
            status = SearchFailureLabel

        return SearchJob(
            SearchJobStart(base_job)(),
            SearchJobGoal(base_job)(),
            SearchJobRules(base_job)(),
            SearchJobHeuristic(base_job)(),
            status,
            merged_frontier,
            expanded,
            generated,
            frontier_peak,
            result_plan,
            merged_visited,
            merged_theorem_cache,
            rewrite_rules,
            merged_frontier_size,
        )()

    def _integrate_parallel_state_result(self, prior_state, mode, decoded, expected_packet_token=M.EmptyList):
        prior_status = self._comparison_state_status(prior_state)
        if M.IdentityCompare(prior_status, SearchRunningLabel)() is M.false_value:
            _debug(
                "search-compare: ignoring stale "
                + SearchModeText(mode)()
                + " packet result because mode status is already "
                + SearchStatusText(prior_status)()
            )
            return prior_state

        returned_packet_token = self._decoded_packet_token(decoded)
        if M.Compare(expected_packet_token, M.EmptyList)() is M.false_value:
            if M.TermEqual(returned_packet_token, expected_packet_token)() is M.false_value:
                _debug(
                    "search-compare: ignoring stale "
                    + SearchModeText(mode)()
                    + " packet result token="
                    + _debug_term(returned_packet_token, self.registry)
                    + " expected="
                    + _debug_term(expected_packet_token, self.registry)
                )
                return prior_state

        returned_status = self._decoded_status(decoded)
        returned_job = self._decoded_job(decoded)
        returned_search_memo = self._decoded_search_memo(decoded)
        returned_ready_packets = self._decoded_ready_packets(decoded)
        returned_ready_packet_count = self._decoded_ready_packet_count(decoded)
        returned_registry = self._decoded_registry(decoded)

        if M.IdentityCompare(returned_registry, M.EmptyList)() is M.false_value:
            self.registry = self._merge_tree(self.registry, returned_registry)
            self.graph._replace_context(constructors=self.registry)

        active_packets = self._pred_nat_or_zero_local(self._comparison_state_active_packets(prior_state))
        if M.IdentityCompare(returned_status, SearchSuccessLabel)() is M.truth_value:
            active_packets = M.Zero
        completed_packets = self._succ_nat_local(self._comparison_state_completed_packets(prior_state))

        merged_search_memo = self._comparison_state_search_memo(prior_state)

        if M.Compare(returned_job, M.EmptyList)() is M.truth_value:
            next_job = self._comparison_state_job(prior_state)
        else:
            next_job = self._merge_compare_jobs(mode, self._comparison_state_job(prior_state), returned_job)
        next_state = self._comparison_state_update(
            prior_state,
            job=next_job,
            search_memo=merged_search_memo,
            active_packets=active_packets,
            completed_packets=completed_packets,
        )
        if M.IdentityCompare(returned_status, SearchSuccessLabel)() is M.truth_value:
            next_state = self._comparison_state_update(
                next_state,
                pending_packets=M.EmptyList,
                pending_packets_count=M.Zero,
            )
        else:
            batched_ready = self._comparison_batch_ready_packets(
                mode,
                self._comparison_state_job(next_state),
                returned_ready_packets,
                returned_ready_packet_count,
            )
            returned_ready_packets = M.Head(batched_ready)()
            returned_ready_packet_count = M.Head(M.Tail(batched_ready)())()
            merged_pending = self._merge_pending_packets(
                mode,
                self._comparison_state_pending_packets(next_state),
                returned_ready_packets,
            )
            merged_pending_count = self._nat_add_local(
                self._comparison_state_pending_packets_count(next_state),
                returned_ready_packet_count,
            )
            next_state = self._comparison_state_update(
                next_state,
                pending_packets=merged_pending,
                pending_packets_count=merged_pending_count,
            )
            if M.IdentityCompare(returned_ready_packets, M.EmptyList)() is M.truth_value:
                next_state = self._comparison_state_enqueue_job_frontier(next_state)
        debug_job = self._comparison_state_job(next_state)
        returned_goal_signal = self._first_goal_signal_in_packets(mode, returned_ready_packets)
        returned_goal_signal_text = "returned-goal-signal=none"
        if M.Compare(returned_goal_signal, M.EmptyList)() is M.false_value:
            if self._comparison_goal_reached(returned_goal_signal, self.goal) is M.truth_value:
                returned_goal_signal_text = "returned-goal-signal=goal-reached"
            else:
                returned_goal_signal_text = "returned-goal-signal=" + _debug_term(returned_goal_signal, self.registry)

        _debug(
            "search-compare: integrated "
            + SearchModeText(mode)()
            + " packet status="
            + SearchStatusText(returned_status)()
            + " total="
            + self._nat_text(self._decoded_total_value(decoded))
            + " frontier="
            + self._nat_text(SearchJobFrontierSize(debug_job)())
            + " expanded="
            + self._nat_text(SearchJobExpanded(debug_job)())
            + " generated="
            + self._nat_text(SearchJobGenerated(debug_job)())
            + " peak="
            + self._nat_text(SearchJobFrontierPeak(debug_job)())
            + " mode-active-processes="
            + self._nat_text(active_packets)
            + " mode-queued-packets="
            + self._nat_text(self._comparison_state_pending_packets_count(next_state))
            + " mode-completed-packets="
            + self._nat_text(completed_packets)
            + " "
            + returned_goal_signal_text
        )

        return next_state

    def _integrate_parallel_result(self, states, mode, decoded, expected_packet_token=M.EmptyList):
        decoded_mode = self._decoded_mode(decoded)
        if M.IdentityCompare(decoded_mode, M.EmptyList)() is M.false_value:
            mode = decoded_mode
        prior_state = self._comparison_state_for_mode(states, mode)
        if M.IdentityCompare(prior_state, M.EmptyList)() is M.truth_value:
            return states
        next_state = self._integrate_parallel_state_result(prior_state, mode, decoded, expected_packet_token)
        if M.Compare(next_state, prior_state)() is M.truth_value:
            return states
        return self._replace_comparison_state(states, mode, next_state)

    def _drained_parallel_result(self, mode, decoded, expected_packet_token):
        return M.Pair(mode, M.Pair(decoded, M.Pair(expected_packet_token, M.EmptyList)))

    def _drained_parallel_result_mode(self, drained_result):
        return M.Head(drained_result)()

    def _drained_parallel_result_decoded(self, drained_result):
        return M.Head(M.Tail(drained_result)())()

    def _drained_parallel_result_expected_packet_token(self, drained_result):
        return M.Head(M.Tail(M.Tail(drained_result)())())()

    def _integrate_parallel_results(self, states, drained_results):
        if M.IdentityCompare(states, M.EmptyList)() is M.truth_value:
            return M.EmptyList

        state = M.Head(states)()
        mode = self._comparison_state_mode(state)
        matching_rev = M.EmptyList
        remaining_results = drained_results
        while M.IdentityCompare(remaining_results, M.EmptyList)() is M.false_value:
            drained_result = M.Head(remaining_results)()
            if M.IdentityCompare(self._drained_parallel_result_mode(drained_result), mode)() is M.truth_value:
                matching_rev = M.Pair(drained_result, matching_rev)
            remaining_results = M.Tail(remaining_results)()

        next_state = state
        matching = self._reverse(matching_rev, M.EmptyList)
        while M.IdentityCompare(matching, M.EmptyList)() is M.false_value:
            drained_result = M.Head(matching)()
            next_state = self._integrate_parallel_state_result(
                next_state,
                mode,
                self._drained_parallel_result_decoded(drained_result),
                self._drained_parallel_result_expected_packet_token(drained_result),
            )
            matching = M.Tail(matching)()

        return M.Pair(next_state, self._integrate_parallel_results(M.Tail(states)(), drained_results))


    def _job_frontier_size_nat(self, job):
        frontier_size = SearchJobFrontierSize(job)()
        if M.IdentityCompare(frontier_size, M.EmptyList)() is M.false_value:
            return frontier_size
        frontier = SearchJobFrontier(job)()
        if M.IdentityCompare(frontier, M.EmptyList)() is M.truth_value:
            frontier_size = M.Zero
        else:
            frontier_size = M.Atom()
            frontier_size.value = M.CountRep(frontier)()
        return frontier_size

    def _comparison_packet_frontier_width(self, mode):
        if M.IdentityCompare(mode, DFSLabel)() is M.truth_value:
            return M.one
        if M.IdentityCompare(mode, RewriteDFSLabel)() is M.truth_value:
            return M.one
        width = HeuristicBeamWidth(self.heuristic)()
        if M.NatEq(width, M.Zero, self.registry)() is M.truth_value:
            width = M.four
        width = self._nat_add_local(width, width)
        return self._nat_min_local(width, self._comparison_machine_parallelism)

    def _take_frontier_packet(self, frontier, width):
        if M.IdentityCompare(frontier, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        if M.NatEq(width, M.Zero, self.registry)() is M.truth_value:
            return M.EmptyList
        next_width_pair = M.NatPred(width, self.registry)()
        next_width = M.Head(next_width_pair)()
        self.registry = M.Head(M.Tail(next_width_pair)())()
        return M.Pair(M.Head(frontier)(), self._take_frontier_packet(M.Tail(frontier)(), next_width))

    def _drop_frontier_packet(self, frontier, width):
        if M.IdentityCompare(frontier, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        if M.NatEq(width, M.Zero, self.registry)() is M.truth_value:
            return frontier
        next_width_pair = M.NatPred(width, self.registry)()
        next_width = M.Head(next_width_pair)()
        self.registry = M.Head(M.Tail(next_width_pair)())()
        return self._drop_frontier_packet(M.Tail(frontier)(), next_width)

    def _split_compare_job_packet(self, state):
        mode = self._comparison_state_mode(state)
        job = self._comparison_state_job(state)

        if M.Compare(job, M.EmptyList)() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(M.EmptyList, M.EmptyList))

        frontier = SearchJobFrontier(job)()
        if M.IdentityCompare(frontier, M.EmptyList)() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(job, M.EmptyList))

        packet_width = self._comparison_packet_frontier_width(mode)
        packet_frontier = self._take_frontier_packet(frontier, packet_width)
        remaining_frontier = self._drop_frontier_packet(frontier, packet_width)

        if M.IdentityCompare(packet_frontier, M.EmptyList)() is M.truth_value:
            packet_frontier_size = M.Zero
        else:
            packet_frontier_size = M.Atom()
            packet_frontier_size.value = M.CountRep(packet_frontier)()

        if M.IdentityCompare(remaining_frontier, M.EmptyList)() is M.truth_value:
            remaining_frontier_size = M.Zero
        else:
            remaining_frontier_size = M.Atom()
            remaining_frontier_size.value = M.CountRep(remaining_frontier)()

        packet_job = SearchJob(
            SearchJobStart(job)(),
            SearchJobGoal(job)(),
            SearchJobRules(job)(),
            SearchJobHeuristic(job)(),
            SearchRunningLabel,
            packet_frontier,
            M.Zero,
            M.Zero,
            M.Zero,
            M.EmptyList,
            SearchJobVisited(job)(),
            SearchJobTheoremRuleCache(job)(),
            SearchJobRewriteRules(job)(),
            packet_frontier_size,
        )()

        remaining_job = SearchJob(
            SearchJobStart(job)(),
            SearchJobGoal(job)(),
            SearchJobRules(job)(),
            SearchJobHeuristic(job)(),
            SearchRunningLabel,
            remaining_frontier,
            SearchJobExpanded(job)(),
            SearchJobGenerated(job)(),
            SearchJobFrontierPeak(job)(),
            M.EmptyList,
            SearchJobVisited(job)(),
            SearchJobTheoremRuleCache(job)(),
            SearchJobRewriteRules(job)(),
            remaining_frontier_size,
        )()

        _debug(
            "search-compare: queued "
            + SearchModeText(mode)()
            + " frontier-state worker packet states="
            + self._nat_text(packet_frontier_size)
            + " remaining-frontier-states="
            + self._nat_text(remaining_frontier_size)
        )

        return M.Pair(packet_job, M.Pair(remaining_job, M.EmptyList))

    def _drain_compare_job_packets(self, state, packet_jobs):
        split = self._split_compare_job_packet(state)
        packet_job = M.Head(split)()
        remaining_job = M.Head(M.Tail(split)())()
        if M.Compare(packet_job, M.EmptyList)() is M.truth_value:
            return M.Pair(state, M.Pair(packet_jobs, M.EmptyList))
        next_state = self._comparison_state_update(state, job=remaining_job)
        return self._drain_compare_job_packets(next_state, M.Pair(packet_job, packet_jobs))

    def _astar_packet_state_score(self, mode, packet):
        packet_state = self._comparison_packet_state(mode, packet)
        if M.IdentityCompare(packet_state, M.EmptyList)() is M.truth_value:
            return M.Zero
        return self._astar_frontier_score(packet_state)

    def _astar_merge_packet_states(self, mode, packet_states, incoming_states):
        if M.IdentityCompare(incoming_states, M.EmptyList)() is M.truth_value:
            return packet_states
        incoming_state = M.Head(incoming_states)()
        return self._astar_merge_packet_states(
            mode,
            self._astar_insert_packet_state(mode, packet_states, incoming_state),
            M.Tail(incoming_states)(),
        )

    def _astar_insert_packet_state(self, mode, packet_states, packet_state):
        if M.IdentityCompare(packet_states, M.EmptyList)() is M.truth_value:
            return M.Pair(packet_state, M.EmptyList)
        head_state = M.Head(packet_states)()
        if M.NatLess(self._astar_packet_state_score(mode, packet_state), self._astar_packet_state_score(mode, head_state), self.registry)() is M.truth_value:
            return M.Pair(packet_state, packet_states)
        return M.Pair(head_state, self._astar_insert_packet_state(mode, M.Tail(packet_states)(), packet_state))

    def _merge_pending_packets(self, mode, pending_packets, new_packets):
        if M.IdentityCompare(new_packets, M.EmptyList)() is M.truth_value:
            return pending_packets
        if M.IdentityCompare(pending_packets, M.EmptyList)() is M.truth_value:
            return new_packets
        if M.IdentityCompare(mode, DFSLabel)() is M.truth_value:
            return Append(new_packets, pending_packets)()
        if M.IdentityCompare(mode, RewriteDFSLabel)() is M.truth_value:
            return Append(new_packets, pending_packets)()
        if M.IdentityCompare(mode, AStarLabel)() is M.truth_value:
            return self._astar_merge_packet_states(mode, pending_packets, new_packets)
        return Append(pending_packets, new_packets)()

    def _comparison_packet_backlog_target_for_job(self, job):
        if M.Compare(job, M.EmptyList)() is M.truth_value:
            return M.Zero
        frontier = SearchJobFrontier(job)()
        if M.IdentityCompare(frontier, M.EmptyList)() is M.truth_value:
            return M.Zero
        return SearchStateStepsRemaining(M.Head(frontier)())()

    def _comparison_packet_backlog_target_for_state(self, packet_state):
        if M.IdentityCompare(packet_state, M.EmptyList)() is M.truth_value:
            return M.Zero
        return SearchStateStepsRemaining(packet_state)()

    def _comparison_frontier_state_packet(self, packet_state):
        return SearchFrontierStatePacket(packet_state)()

    def _comparison_root_rule_packet(self, rule):
        return SearchRootRulePacket(rule)()

    def _comparison_packet_is_root_rule(self, packet):
        if M.IsPair(packet)() is M.false_value:
            return M.false_value
        return M.IdentityCompare(M.Head(packet)(), SearchRootRulePacketLabel)()

    def _comparison_packet_is_frontier_state(self, packet):
        if M.IsPair(packet)() is M.false_value:
            return M.false_value
        return M.IdentityCompare(M.Head(packet)(), SearchFrontierStatePacketLabel)()

    def _comparison_packet_payload(self, packet):
        if M.IsPair(packet)() is M.false_value:
            return packet
        return M.Head(M.Tail(packet)())()

    def _comparison_packet_state(self, mode, packet):
        if self._comparison_packet_is_root_rule(packet) is M.truth_value:
            rule = SearchRootRulePacketRule(packet)()
            root_job = self._fresh_compare_job(mode)
            root_state = M.Head(SearchJobFrontier(root_job)())()
            return self._comparison_rule_cursor_state(root_state, rule)
        if self._comparison_packet_is_frontier_state(packet) is M.truth_value:
            return SearchFrontierStatePacketState(packet)()
        if M.IsPair(packet)() is M.truth_value:
            if M.IdentityCompare(M.Head(packet)(), SearchJobLabel)() is M.truth_value:
                packet_frontier = SearchJobFrontier(packet)()
                if M.IdentityCompare(packet_frontier, M.EmptyList)() is M.truth_value:
                    return M.EmptyList
                return M.Head(packet_frontier)()
        rule = packet
        root_job = self._fresh_compare_job(mode)
        root_state = M.Head(SearchJobFrontier(root_job)())()
        return self._comparison_rule_cursor_state(root_state, rule)

    def _comparison_packet_is_dispatchable(self, mode, packet):
        packet_state = self._comparison_packet_state(mode, packet)
        if M.IdentityCompare(packet_state, M.EmptyList)() is M.truth_value:
            return M.false_value
        if M.NatEq(SearchStateStepsRemaining(packet_state)(), M.Zero, self.registry)() is M.truth_value:
            return M.false_value
        return M.truth_value

    def _comparison_ready_packets_all_frontier_states(self, packets):
        remaining_packets = packets
        while M.IdentityCompare(remaining_packets, M.EmptyList)() is M.false_value:
            if self._comparison_packet_is_frontier_state(M.Head(remaining_packets)()) is M.false_value:
                return M.false_value
            remaining_packets = M.Tail(remaining_packets)()
        return M.truth_value

    def _comparison_ready_packets_frontier(self, packets):
        if M.IdentityCompare(packets, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        return M.Pair(
            SearchFrontierStatePacketState(M.Head(packets)())(),
            self._comparison_ready_packets_frontier(M.Tail(packets)()),
        )

    def _frontier_count_nat(self, frontier):
        if M.IdentityCompare(frontier, M.EmptyList)() is M.truth_value:
            return M.Zero
        count = M.Atom()
        count.value = M.CountRep(frontier)()
        return count

    def _chain_count_nat(self, chain):
        if M.IdentityCompare(chain, M.EmptyList)() is M.truth_value:
            return M.Zero
        count_pair = M.Count(chain, self.registry)()
        count = M.Head(count_pair)()
        self.registry = M.Head(M.Tail(count_pair)())()
        return count

    def _comparison_batch_ready_packets(self, mode, job, ready_packets, ready_packet_count):
        if M.IdentityCompare(ready_packets, M.EmptyList)() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(M.Zero, M.EmptyList))
        actual_ready_packet_count = self._chain_count_nat(ready_packets)
        if M.NatEq(ready_packet_count, actual_ready_packet_count, self.registry)() is M.false_value:
            ready_packet_count = actual_ready_packet_count
        packet_width = self._comparison_packet_frontier_width(mode)
        if M.NatEq(packet_width, M.one, self.registry)() is M.truth_value:
            return M.Pair(ready_packets, M.Pair(ready_packet_count, M.EmptyList))
        if M.NatLess(packet_width, ready_packet_count, self.registry)() is M.false_value:
            return M.Pair(ready_packets, M.Pair(ready_packet_count, M.EmptyList))
        if self._comparison_ready_packets_all_frontier_states(ready_packets) is M.false_value:
            return M.Pair(ready_packets, M.Pair(ready_packet_count, M.EmptyList))

        batched_packets_rev = M.EmptyList
        batched_packet_count = M.Zero
        remaining_frontier = self._comparison_ready_packets_frontier(ready_packets)
        while M.IdentityCompare(remaining_frontier, M.EmptyList)() is M.false_value:
            packet_frontier = self._take_frontier_packet(remaining_frontier, packet_width)
            remaining_frontier = self._drop_frontier_packet(remaining_frontier, packet_width)
            packet_frontier_size = self._frontier_count_nat(packet_frontier)
            packet_job = self._comparison_rebuild_packetized_job(
                job,
                SearchRunningLabel,
                packet_frontier,
                M.Zero,
                M.Zero,
                M.Zero,
                M.EmptyList,
                SearchJobVisited(job)(),
                SearchJobTheoremRuleCache(job)(),
                SearchJobRewriteRules(job)(),
                packet_frontier_size,
            )
            batched_packets_rev = M.Pair(packet_job, batched_packets_rev)
            batched_packet_count = self._succ_nat_local(batched_packet_count)

        batched_packets = self._reverse(batched_packets_rev, M.EmptyList)
        _debug(
            "search-compare: regrouped "
            + SearchModeText(mode)()
            + " returned frontier wave from "
            + self._nat_text(ready_packet_count)
            + " ready frontier states into "
            + self._nat_text(batched_packet_count)
            + " batched packets"
        )
        return M.Pair(batched_packets, M.Pair(batched_packet_count, M.EmptyList))

    def _drop_exhausted_pending_packets(self, mode, pending_packets, pending_packets_count):
        next_pending_packets = pending_packets
        next_pending_packets_count = pending_packets_count
        while M.IdentityCompare(next_pending_packets, M.EmptyList)() is M.false_value:
            head_packet = M.Head(next_pending_packets)()
            if self._comparison_packet_is_dispatchable(mode, head_packet) is M.truth_value:
                break
            _debug(
                "search-compare: dropping exhausted "
                + SearchModeText(mode)()
                + " packet with remaining-budget=0 before lease"
            )
            next_pending_packets = M.Tail(next_pending_packets)()
            next_pending_packets_count = self._pred_nat_or_zero_local(next_pending_packets_count)
        return M.Pair(next_pending_packets, M.Pair(next_pending_packets_count, M.EmptyList))

    def _drop_prunable_pending_packets(self, mode, pending_packets, pending_packets_count, best_cost=M.EmptyList):
        next_pending_packets = pending_packets
        next_pending_packets_count = pending_packets_count
        while M.IdentityCompare(next_pending_packets, M.EmptyList)() is M.false_value:
            head_packet = M.Head(next_pending_packets)()
            if self._comparison_packet_is_dispatchable(mode, head_packet) is M.false_value:
                break
            if self._comparison_packet_prunable(mode, head_packet, best_cost) is M.false_value:
                break
            _debug(
                "search-compare: dropping prunable "
                + SearchModeText(mode)()
                + " packet with optimistic-bound>=best-cost before lease"
            )
            next_pending_packets = M.Tail(next_pending_packets)()
            next_pending_packets_count = self._pred_nat_or_zero_local(next_pending_packets_count)
        return M.Pair(next_pending_packets, M.Pair(next_pending_packets_count, M.EmptyList))

    def _comparison_state_without_exhausted_pending_packets(self, state, best_cost=M.EmptyList):
        mode = self._comparison_state_mode(state)
        pending_packets = self._comparison_state_pending_packets(state)
        pending_packets_count = self._comparison_state_pending_packets_count(state)
        filtered = self._drop_exhausted_pending_packets(mode, pending_packets, pending_packets_count)
        filtered_prunable = self._drop_prunable_pending_packets(
            mode,
            M.Head(filtered)(),
            M.Head(M.Tail(filtered)())(),
            best_cost,
        )
        next_pending_packets = M.Head(filtered_prunable)()
        next_pending_packets_count = M.Head(M.Tail(filtered_prunable)())()
        if M.Compare(next_pending_packets, pending_packets)() is M.truth_value:
            if M.NatEq(next_pending_packets_count, pending_packets_count, self.registry)() is M.truth_value:
                return state
        return self._comparison_state_update(
            state,
            pending_packets=next_pending_packets,
            pending_packets_count=next_pending_packets_count,
        )

    def _comparison_state_packet_backlog_target(self, state):
        job_target = self._comparison_packet_backlog_target_for_job(self._comparison_state_job(state))
        pending_packets = self._comparison_state_pending_packets(state)
        pending_target = M.Zero
        if M.IdentityCompare(pending_packets, M.EmptyList)() is M.false_value:
            pending_target = self._comparison_packet_backlog_target_for_state(
                self._comparison_packet_state(self._comparison_state_mode(state), M.Head(pending_packets)())
            )
        target = self._nat_max_local(job_target, pending_target)
        if M.NatEq(target, M.Zero, self.registry)() is M.truth_value:
            return M.one
        return target

    def _comparison_rule_cursor_state(self, state, rule):
        return SearchState(
            SearchStateCurrent(state)(),
            SearchStatePlan(state)(),
            SearchStateSeen(state)(),
            SearchStateStepsRemaining(state)(),
            SearchTheoremCursor(M.Pair(rule, M.EmptyList), M.Tree(M.EmptyList))(),
        )()

    def _comparison_rule_wave_shards(self, rules):
        per_shard = M.one

        remaining_rules = rules
        shards_rev = M.EmptyList
        while M.IdentityCompare(remaining_rules, M.EmptyList)() is M.false_value:
            shard_rev = M.EmptyList
            k = per_shard
            while M.AndAtom(
                M.IdentityCompare(M.NatEq(k, M.Zero, self.registry)(), M.false_value)(),
                M.IdentityCompare(M.IdentityCompare(remaining_rules, M.EmptyList)(), M.false_value)(),
            )() is M.truth_value:
                shard_rev = M.Pair(M.Head(remaining_rules)(), shard_rev)
                remaining_rules = M.Tail(remaining_rules)()
                pred_pair = M.NatPred(k, self.registry)()
                k = M.Head(pred_pair)()
                self.registry = M.Head(M.Tail(pred_pair)())()
            shards_rev = M.Pair(self._reverse(shard_rev, M.EmptyList), shards_rev)
        return self._reverse(shards_rev, M.EmptyList)

    def _root_wave_shard_worker_entry(self, shard_work, executor):
        return M.Pair(shard_work, M.Pair(executor, M.EmptyList))

    def _root_wave_shard_worker_work(self, entry):
        return M.Head(entry)()

    def _root_wave_shard_worker_slot(self, entry):
        return self._root_wave_shard_work_entry_slot(self._root_wave_shard_worker_work(entry))

    def _root_wave_shard_worker_executor(self, entry):
        return M.Head(M.Tail(entry)())()

    def _root_wave_shard_worker_process(self, entry):
        return self._resident_executor_process(self._root_wave_shard_worker_executor(entry))

    def _root_wave_shard_worker_queue(self, entry):
        return self._resident_executor_result_queue(self._root_wave_shard_worker_executor(entry))

    def _terminate_root_wave_shard_workers(self, workers):
        remaining_workers = workers
        while M.IdentityCompare(remaining_workers, M.EmptyList)() is M.false_value:
            entry = M.Head(remaining_workers)()
            self._retire_parallel_executor(
                self._root_wave_shard_worker_executor(entry),
                "retiring root-wave shard worker ",
            )
            remaining_workers = M.Tail(remaining_workers)()

    def _root_wave_shard_result_entry(self, slot, payload):
        return M.Pair(slot, M.Pair(payload, M.EmptyList))

    def _root_wave_shard_result_entry_slot(self, entry):
        return M.Head(entry)()

    def _root_wave_shard_result_entry_payload(self, entry):
        return M.Head(M.Tail(entry)())()

    def _insert_root_wave_shard_result_entry(self, entries, entry):
        slot = self._root_wave_shard_result_entry_slot(entry)
        remaining_entries = entries
        rebuilt_rev = M.EmptyList
        inserted = M.false_value
        while M.IdentityCompare(remaining_entries, M.EmptyList)() is M.false_value:
            current_entry = M.Head(remaining_entries)()
            if M.IdentityCompare(inserted, M.false_value)() is M.truth_value:
                if M.NatLess(slot, self._root_wave_shard_result_entry_slot(current_entry), self.registry)() is M.truth_value:
                    rebuilt_rev = M.Pair(entry, rebuilt_rev)
                    inserted = M.truth_value
            rebuilt_rev = M.Pair(current_entry, rebuilt_rev)
            remaining_entries = M.Tail(remaining_entries)()
        if M.IdentityCompare(inserted, M.false_value)() is M.truth_value:
            rebuilt_rev = M.Pair(entry, rebuilt_rev)
        return self._reverse(rebuilt_rev, M.EmptyList)

    def _root_wave_shard_result_payloads(self, entries):
        remaining_entries = entries
        payloads_rev = M.EmptyList
        while M.IdentityCompare(remaining_entries, M.EmptyList)() is M.false_value:
            payloads_rev = M.Pair(self._root_wave_shard_result_entry_payload(M.Head(remaining_entries)()), payloads_rev)
            remaining_entries = M.Tail(remaining_entries)()
        return self._reverse(payloads_rev, M.EmptyList)

    def _root_wave_worker_setup(self, job):
        baseline = SearchWorkerBaseline(
            M.FromContextGetConstructors(self.graph)(),
            SearchJobStart(job)(),
            SearchJobGoal(job)(),
            SearchJobRules(job)(),
            SearchJobHeuristic(job)(),
            SearchJobRewriteRules(job)(),
            self._comparison_generation,
        )()
        return SearchWorkerSetup(HeuristicSearchMode(SearchJobHeuristic(job)())(), baseline)()

    def _resident_executor_ready_for_root_wave(self, executor, job):
        mode = HeuristicSearchMode(SearchJobHeuristic(job)())()
        rewrite_rules = SearchJobRewriteRules(job)()
        send_setup = M.false_value
        if M.TermEqual(self._resident_executor_generation(executor), self._comparison_generation)() is M.false_value:
            send_setup = M.truth_value
        elif M.TermEqual(self._resident_executor_mode(executor), mode)() is M.false_value:
            send_setup = M.truth_value
        elif M.TermEqual(self._resident_executor_rewrite_rules(executor), rewrite_rules)() is M.false_value:
            send_setup = M.truth_value
        if M.IdentityCompare(send_setup, M.truth_value)() is M.truth_value:
            self._resident_executor_task_queue(executor).put(self._root_wave_worker_setup(job))
            executor = self._resident_executor_with_baseline(
                executor,
                self._comparison_generation,
                mode,
                rewrite_rules,
            )
        return executor

    def _start_resident_root_wave_shard(self, executor, shard_work, current):
        slot = self._root_wave_shard_work_entry_slot(shard_work)
        shard_rules = self._root_wave_shard_work_entry_rules(shard_work)
        shard_packet = SearchRootWaveShardPacket(
            M.EmptyList,
            shard_rules,
            current,
            Pmod.DEBUG_TRACE_STATE(),
        )()
        launch = SearchRootWaveShardLaunch(shard_packet, slot)()
        self._resident_executor_task_queue(executor).put(launch)
        _debug(
            "search-compare: leased resident executor "
            + self._nat_text(self._resident_executor_slot(executor))
            + " for root-wave shard "
            + self._nat_text(slot)
        )
        return self._root_wave_shard_worker_entry(shard_work, executor)

    def _first_finished_root_wave_shard_worker(self, workers, acc):
        if M.IdentityCompare(workers, M.EmptyList)() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(M.EmptyList, M.Pair(self._reverse(acc, M.EmptyList), M.EmptyList)))
        entry = M.Head(workers)()
        process = self._root_wave_shard_worker_process(entry)
        result_queue = self._root_wave_shard_worker_queue(entry)
        try:
            payload = result_queue.get_nowait()
            return M.Pair(
                entry,
                M.Pair(
                    payload,
                    M.Pair(Append(self._reverse(acc, M.EmptyList), M.Tail(workers)())(), M.EmptyList),
                ),
            )
        except queue.Empty:
            if process.is_alive():
                return self._first_finished_root_wave_shard_worker(M.Tail(workers)(), M.Pair(entry, acc))
            process.join(0.01)
            try:
                payload = result_queue.get_nowait()
            except queue.Empty:
                payload = None
            return M.Pair(
                entry,
                M.Pair(
                    payload,
                    M.Pair(Append(self._reverse(acc, M.EmptyList), M.Tail(workers)())(), M.EmptyList),
                ),
            )

    def _merge_root_wave_shard_results(self, shard_results):
        immediate_rules = M.EmptyList
        goal_rules = M.EmptyList
        other_rules = M.EmptyList
        remaining_results = shard_results
        while M.IdentityCompare(remaining_results, M.EmptyList)() is M.false_value:
            result = M.Head(remaining_results)()
            immediate_rules = Append(immediate_rules, SearchRootWaveShardResultImmediate(result)())()
            goal_rules = Append(goal_rules, SearchRootWaveShardResultGoal(result)())()
            other_rules = Append(other_rules, SearchRootWaveShardResultOther(result)())()
            remaining_results = M.Tail(remaining_results)()
        return Append(immediate_rules, Append(goal_rules, other_rules)())()

    def _comparison_order_rule_wave_candidates(self, mode, job, applicable):
        heuristic = SearchJobHeuristic(job)()
        if M.IdentityCompare(HeuristicRuleOrder(heuristic)(), GoalHeadOrderLabel)() is M.truth_value:
            current = SearchStateCurrent(M.Head(SearchJobFrontier(job)())())()
            buckets = GoalHeadApplicableRuleBuckets(applicable, current, SearchJobGoal(job)(), self.registry)()
            immediate_rules = SearchRootWaveShardResultImmediate(buckets)()
            goal_rules = SearchRootWaveShardResultGoal(buckets)()
            other_rules = SearchRootWaveShardResultOther(buckets)()
            return Append(immediate_rules, Append(goal_rules, other_rules)())()
        return applicable

    def _root_wave_shard_work_entry(self, slot, shard_rules):
        return M.Pair(slot, M.Pair(shard_rules, M.EmptyList))

    def _root_wave_shard_work_entry_slot(self, entry):
        return M.Head(entry)()

    def _root_wave_shard_work_entry_rules(self, entry):
        return M.Head(M.Tail(entry)())()

    def _root_wave_shard_work_entries(self, shard_rules):
        remaining_shards = shard_rules
        entries_rev = M.EmptyList
        slot = M.Zero
        while M.IdentityCompare(remaining_shards, M.EmptyList)() is M.false_value:
            slot = self._succ_nat_local(slot)
            entries_rev = M.Pair(
                self._root_wave_shard_work_entry(slot, M.Head(remaining_shards)()),
                entries_rev,
            )
            remaining_shards = M.Tail(remaining_shards)()
        return self._reverse(entries_rev, M.EmptyList)

    def _spawn_root_wave_replacement_executor(self, shard_count):
        slot = self._succ_nat_local(shard_count)
        try:
            executor = self._spawn_parallel_executor(self._comparison_mp_context, slot)
        except Exception as error:
            _debug(
                "search-compare: resident root-wave replacement unavailable at slot "
                + self._nat_text(slot)
                + " ("
                + str(error)
                + ")"
            )
            return M.EmptyList
        _debug(
            "search-compare: replenished resident root-wave executor "
            + self._nat_text(slot)
            + " for failed shard retry"
        )
        return executor

    def _comparison_root_candidate_rules_parallel(self, job):
        t0 = time.time()
        _debug("search-compare: root prepass: building shards...")
        shard_rules = self._comparison_rule_wave_shards(SearchJobRules(job)())
        _debug("search-compare: root prepass: shards built in {:.2f}s".format(time.time() - t0))
        _debug("search-compare: root prepass: counting shards...")
        if M.IdentityCompare(shard_rules, M.EmptyList)() is M.truth_value:
            shard_count = M.Zero
        else:
            shard_count = M.Atom()
            shard_count.value = M.CountRep(shard_rules)()
        _debug("search-compare: root prepass: shard count computed in {:.2f}s".format(time.time() - t0))
        if M.NatEq(shard_count, M.Zero, self.registry)() is M.truth_value:
            return M.EmptyList

        current = SearchStateCurrent(M.Head(SearchJobFrontier(job)())())()
        workers = M.EmptyList
        idle_executors = self._comparison_root_wave_idle_executors
        completed = M.Zero
        result_entries = M.EmptyList
        remaining_shards = self._root_wave_shard_work_entries(shard_rules)

        _debug(
            "search-compare: routing one shared root rule chain for all fixed modes through "
            + self._nat_text(shard_count)
            + " resident shards"
        )
        _debug(
            "search-compare: shared root shard prepass covers "
            + self._mode_chain_text(self._mode_chain())
        )

        _debug(
            "search-compare: awaiting "
            + self._nat_text(shard_count)
            + " shared-root shard results"
        )
        while M.NatLess(completed, shard_count, self.registry)() is M.truth_value:
            while (
                M.IdentityCompare(remaining_shards, M.EmptyList)() is M.false_value
                and M.IdentityCompare(idle_executors, M.EmptyList)() is M.false_value
            ):
                executor = M.Head(idle_executors)()
                idle_executors = M.Tail(idle_executors)()
                executor = self._resident_executor_ready_for_root_wave(executor, job)
                workers = M.Pair(
                    self._start_resident_root_wave_shard(
                        executor,
                        M.Head(remaining_shards)(),
                        current,
                    ),
                    workers,
                )
                remaining_shards = M.Tail(remaining_shards)()

            if M.IdentityCompare(workers, M.EmptyList)() is M.truth_value:
                replacement_executor = self._spawn_root_wave_replacement_executor(shard_count)
                if M.IdentityCompare(replacement_executor, M.EmptyList)() is M.false_value:
                    idle_executors = M.Pair(replacement_executor, idle_executors)
                    continue
                self._comparison_root_wave_idle_executors = idle_executors
                raise RuntimeError("search-compare: resident root-wave executors unavailable")

            finished = self._first_finished_root_wave_shard_worker(workers, M.EmptyList)
            entry = M.Head(finished)()
            if M.IdentityCompare(entry, M.EmptyList)() is M.truth_value:
                time.sleep(0.01)
                continue
            payload = M.Head(M.Tail(finished)())()
            workers = M.Head(M.Tail(M.Tail(finished)())())()
            if payload is None:
                _debug(
                    "search-compare: a root-wave shard failed; retrying through resident executors"
                )
                self._retire_parallel_executor(
                    self._root_wave_shard_worker_executor(entry),
                    "retiring failed root-wave shard worker ",
                )
                remaining_shards = M.Pair(self._root_wave_shard_worker_work(entry), remaining_shards)
                continue
            result_entries = self._insert_root_wave_shard_result_entry(
                result_entries,
                self._root_wave_shard_result_entry(self._root_wave_shard_worker_slot(entry), payload),
            )
            idle_executors = M.Pair(self._root_wave_shard_worker_executor(entry), idle_executors)
            completed = self._succ_nat_local(completed)

        self._comparison_root_wave_idle_executors = idle_executors
        _debug(
            "search-compare: merged "
            + self._nat_text(shard_count)
            + " shared-root candidate shard results for all fixed modes"
        )
        return self._merge_root_wave_shard_results(self._root_wave_shard_result_payloads(result_entries))

    def _comparison_root_candidate_rules(self, job):
        return self._comparison_root_candidate_rules_parallel(job)

    def _comparison_rule_wave_rules(self, mode, job, candidates=M.EmptyList):
        applicable = candidates
        if M.Compare(applicable, M.EmptyList)() is M.truth_value:
            applicable = self._comparison_root_candidate_rules(job)
        return self._comparison_order_rule_wave_candidates(mode, job, applicable)

    def _comparison_seed_rule_wave(self, mode, job, candidates=M.EmptyList):
        frontier = SearchJobFrontier(job)()
        if M.IdentityCompare(frontier, M.EmptyList)() is M.truth_value:
            return M.Pair(job, M.Pair(M.EmptyList, M.Pair(M.Zero, M.EmptyList)))

        state = M.Head(frontier)()
        if M.IdentityCompare(SearchStateCursor(state)(), M.EmptyList)() is M.false_value:
            return M.Pair(job, M.Pair(M.EmptyList, M.Pair(M.Zero, M.EmptyList)))

        current = SearchStateCurrent(state)()
        remaining_frontier = M.Tail(frontier)()
        rules = self._comparison_rule_wave_rules(mode, job, candidates)
        kernel = _SearchStepKernel(
            self.graph,
            job,
            SearchJobRules(job)(),
            SearchJobHeuristic(job)(),
            SearchJobGoal(job)(),
            self.registry,
            None,
            None,
        )
        expanded_total = self._succ_nat_local(SearchJobExpanded(job)())
        packet_jobs_rev = M.EmptyList
        packet_count = M.Zero
        generated = M.Tree(M.EmptyList)
        remaining_rules = rules
        while M.IdentityCompare(remaining_rules, M.EmptyList)() is M.false_value:
            rule = M.Head(remaining_rules)()
            remaining_rules = M.Tail(remaining_rules)()
            next_term = self._direct_next_term(rule, current)
            if M.TermEqual(next_term, current)() is M.truth_value:
                continue
            if self._tree_contains(generated, next_term) is M.truth_value:
                continue
            packet_jobs_rev = M.Pair(
                self._comparison_frontier_state_packet(
                    SearchState(
                        current,
                        SearchStatePlan(state)(),
                        SearchStateSeen(state)(),
                        SearchStateStepsRemaining(state)(),
                        SearchTheoremCursor(M.Pair(rule, M.EmptyList), generated)(),
                    )()
                ),
                packet_jobs_rev,
            )
            generated = self._tree_insert(generated, next_term)
            packet_count = self._succ_nat_local(packet_count)

        if IsKnowledge(current)() is M.false_value:
            packet_jobs_rev = M.Pair(
                self._comparison_frontier_state_packet(
                    SearchState(
                        current,
                        SearchStatePlan(state)(),
                        SearchStateSeen(state)(),
                        SearchStateStepsRemaining(state)(),
                        SearchRewriteCursor(
                            M.EmptyList,
                            M.EmptyList,
                            M.Pair(kernel._rewrite_frame(current, M.EmptyList), M.EmptyList),
                            generated,
                        )(),
                    )()
                ),
                packet_jobs_rev,
            )
            self.registry = kernel.registry
            self.graph._replace_context(constructors=self.registry)
            packet_count = self._succ_nat_local(packet_count)
        packet_jobs = self._reverse(packet_jobs_rev, M.EmptyList)

        if M.IdentityCompare(remaining_frontier, M.EmptyList)() is M.truth_value:
            remaining_count = M.Zero
        else:
            remaining_count = M.Atom()
            remaining_count.value = M.CountRep(remaining_frontier)()

        combined_frontier = self._nat_add_local(remaining_count, packet_count)
        frontier_peak = self._nat_max_local(SearchJobFrontierPeak(job)(), combined_frontier)

        drained_job = self._comparison_rebuild_packetized_job(
            job,
            SearchRunningLabel,
            remaining_frontier,
            expanded_total,
            SearchJobGenerated(job)(),
            frontier_peak,
            M.EmptyList,
            SearchJobVisited(job)(),
            M.EmptyList,
            kernel._rewrite_rules,
            remaining_count,
        )

        if M.NatEq(packet_count, M.Zero, self.registry)() is M.false_value:
            _debug(
                "search-compare: seeded "
                + SearchModeText(mode)()
                + " root branch wave with "
                + self._nat_text(packet_count)
                + " theorem/rewrite handoff packets"
            )

        return M.Pair(drained_job, M.Pair(packet_jobs, M.Pair(packet_count, M.EmptyList)))

    def _comparison_expand_pending_packets_pass(self, mode, base_job, search_memo, pending_packets, expanded_packets):
        if M.IdentityCompare(pending_packets, M.EmptyList)() is M.truth_value:
            return M.Pair(base_job, M.Pair(expanded_packets, M.EmptyList))

        packet_job = M.Head(pending_packets)()
        rest_packets = M.Tail(pending_packets)()
        queue_pair = self._packet_queue_from_job(mode, packet_job, search_memo)
        drained_packet_job = M.Head(queue_pair)()
        child_packets = M.Head(M.Tail(queue_pair)())()
        merged_job = self._merge_compare_jobs(mode, base_job, drained_packet_job)

        if M.IdentityCompare(SearchJobStatus(merged_job)(), SearchSuccessLabel)() is M.truth_value:
            return M.Pair(merged_job, M.Pair(M.EmptyList, M.EmptyList))

        next_packets = self._merge_pending_packets(mode, expanded_packets, child_packets)
        return self._comparison_expand_pending_packets_pass(
            mode,
            merged_job,
            search_memo,
            rest_packets,
            next_packets,
        )

    def _comparison_widen_pending_packets(self, state):
        if M.IdentityCompare(self._comparison_state_status(state), SearchRunningLabel)() is M.false_value:
            return state
        target = self._comparison_state_packet_backlog_target(state)
        post_return_target = self._comparison_post_return_backlog_target(state)
        if M.NatLess(target, post_return_target, self.registry)() is M.truth_value:
            target = post_return_target
        packet_width = self._comparison_packet_frontier_width(self._comparison_state_mode(state))
        target_limit = self._nat_add_local(packet_width, packet_width)
        active_packets = self._comparison_state_active_packets(state)
        if M.NatEq(active_packets, M.Zero, self.registry)() is M.false_value:
            target_limit = self._nat_add_local(target_limit, active_packets)
        if M.NatLess(target_limit, target, self.registry)() is M.truth_value:
            target = target_limit
        return self._comparison_widen_pending_packets_to_target(state, target)

    def _comparison_is_fresh_root_job(self, job):
        if M.Compare(job, M.EmptyList)() is M.truth_value:
            return M.false_value
        (
            start,
            goal,
            rules,
            heuristic,
            status,
            frontier,
            expanded,
            generated,
            frontier_size,
            frontier_peak,
            result_plan,
            visited,
            theorem_rule_cache,
            rewrite_rules,
        ) = self._search_job_unpack_local(job)
        if M.Compare(result_plan, M.EmptyList)() is M.false_value:
            return M.false_value
        if M.NatEq(expanded, M.Zero, self.registry)() is M.false_value:
            return M.false_value
        if M.NatEq(generated, M.Zero, self.registry)() is M.false_value:
            return M.false_value
        if M.IdentityCompare(frontier, M.EmptyList)() is M.truth_value:
            return M.false_value
        if M.IdentityCompare(M.Tail(frontier)(), M.EmptyList)() is M.false_value:
            return M.false_value
        state = M.Head(frontier)()
        if M.TermEqual(SearchStateCurrent(state)(), self.start)() is M.false_value:
            return M.false_value
        if M.Compare(SearchStateCursor(state)(), M.EmptyList)() is M.false_value:
            return M.false_value
        return M.truth_value

    def _comparison_packets_with_visited(self, mode, visited, packets):
        if self._mode_uses_global_visited(mode) is M.false_value:
            return visited
        if M.IdentityCompare(packets, M.EmptyList)() is M.truth_value:
            return visited
        packet_state = self._comparison_packet_state(mode, M.Head(packets)())
        filtered_child, next_visited = self._comparison_filter_new_child(packet_state, visited)
        return self._comparison_packets_with_visited(mode, next_visited, M.Tail(packets)())

    def _comparison_shared_root_wave_target(self, packet_count):
        return self._nat_add_local(packet_count, self._comparison_rule_count)

    def _comparison_post_return_backlog_target(self, state):
        if M.IdentityCompare(self._comparison_state_status(state), SearchRunningLabel)() is M.false_value:
            return M.Zero
        if M.NatEq(self._comparison_state_active_packets(state), M.Zero, self.registry)() is M.truth_value:
            return M.Zero
        return self._comparison_rule_count

    def _comparison_expand_one_pending_packet(self, state):
        (
            mode,
            job,
            search_memo,
            active_packets,
            pending_packets,
            pending_packets_count,
            phase,
            completed_packets,
            root_fast_path_result,
            stop_reason,
        ) = self._comparison_state_unpack(state)
        if M.IdentityCompare(pending_packets, M.EmptyList)() is M.truth_value:
            return state

        packet_descriptor = M.Head(pending_packets)()
        rest_packets = M.Tail(pending_packets)()
        rest_count = self._pred_nat_or_zero_local(pending_packets_count)
        packet_job = self._comparison_packet_job_for_state(state, packet_descriptor)
        queue_pair = self._packet_queue_from_job(mode, packet_job, search_memo)
        drained_packet_job = M.Head(queue_pair)()
        child_packets = M.Head(M.Tail(queue_pair)())()
        child_packet_count = M.Head(M.Tail(M.Tail(queue_pair)())())()
        merged_job = self._merge_compare_jobs(mode, job, drained_packet_job)

        next_pending = Append(child_packets, rest_packets)()
        next_pending_count = self._nat_add_local(rest_count, child_packet_count)
        if M.IdentityCompare(SearchJobStatus(merged_job)(), SearchSuccessLabel)() is M.truth_value:
            next_pending = M.EmptyList
            next_pending_count = M.Zero

        return self._comparison_state(
            mode,
            merged_job,
            search_memo,
            active_packets,
            next_pending,
            next_pending_count,
            phase,
            completed_packets,
            root_fast_path_result,
            stop_reason,
        )

    def _comparison_widen_pending_packets_to_target(self, state, target):
        if M.IdentityCompare(self._comparison_state_status(state), SearchRunningLabel)() is M.false_value:
            return state
        if M.IdentityCompare(self._comparison_state_pending_packets(state), M.EmptyList)() is M.truth_value:
            return state
        current_count = self._comparison_state_pending_packets_count(state)
        if M.NatLess(current_count, target, self.registry)() is M.false_value:
            return state
        next_state = self._comparison_expand_one_pending_packet(state)
        next_count = self._comparison_state_pending_packets_count(next_state)
        if M.NatLess(current_count, next_count, self.registry)() is M.false_value:
            return next_state
        return self._comparison_widen_pending_packets_to_target(next_state, target)

    def _comparison_cache_shared_root_candidates(self, search_memo):
        if M.IdentityCompare(self._comparison_shared_root_candidates_ready, M.truth_value)() is M.truth_value:
            return
        t0 = time.time()
        root_mode = BFSLabel
        _debug("search-compare: shared root prepass: building root job...")
        root_job = self._fresh_compare_job(root_mode)
        _debug("search-compare: shared root prepass: root job ready in {:.2f}s".format(time.time() - t0))
        _debug("search-compare: shared root prepass: scanning for applicable root rules...")
        candidates = self._comparison_root_candidate_rules(root_job)
        _debug("search-compare: shared root prepass: applicable rule scan done in {:.2f}s".format(time.time() - t0))
        if M.IdentityCompare(candidates, M.EmptyList)() is M.truth_value:
            self._comparison_shared_root_candidate_count = M.Zero
        else:
            self._comparison_shared_root_candidate_count = M.Atom()
            self._comparison_shared_root_candidate_count.value = M.CountRep(candidates)()
        self._comparison_shared_root_candidates = candidates
        self._comparison_shared_root_candidates_ready = M.truth_value
        _debug(
            "search-compare: shared root prepass: cached "
            + self._nat_text(self._comparison_shared_root_candidate_count)
            + " candidates in {:.2f}s".format(time.time() - t0)
        )

    def _comparison_states_need_shared_root_wave(self, states):
        if M.IdentityCompare(states, M.EmptyList)() is M.truth_value:
            return M.false_value
        state = M.Head(states)()
        if M.IdentityCompare(self._comparison_state_status(state), SearchRunningLabel)() is M.truth_value:
            if M.IdentityCompare(self._comparison_state_phase(state), SearchPacketSearchPhaseLabel)() is M.truth_value:
                if M.NatEq(self._comparison_state_active_packets(state), M.Zero, self.registry)() is M.truth_value:
                    if M.IdentityCompare(self._comparison_state_pending_packets(state), M.EmptyList)() is M.truth_value:
                        if self._comparison_is_fresh_root_job(self._comparison_state_job(state)) is M.truth_value:
                            return M.truth_value
        return self._comparison_states_need_shared_root_wave(M.Tail(states)())

    def _comparison_prepare_shared_root_wave(self, states):
        if self._comparison_states_need_shared_root_wave(states) is M.false_value:
            return states
        if M.IdentityCompare(states, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        state = M.Head(states)()
        next_state = state
        if M.IdentityCompare(self._comparison_state_status(state), SearchRunningLabel)() is M.truth_value:
            if M.IdentityCompare(self._comparison_state_phase(state), SearchPacketSearchPhaseLabel)() is M.truth_value:
                if M.NatEq(self._comparison_state_active_packets(state), M.Zero, self.registry)() is M.truth_value:
                    if M.IdentityCompare(self._comparison_state_pending_packets(state), M.EmptyList)() is M.truth_value:
                        if self._comparison_is_fresh_root_job(self._comparison_state_job(state)) is M.truth_value:
                            queued = self._comparison_apply_shared_root_wave(
                                self._comparison_state_mode(state),
                                self._comparison_state_job(state),
                                self._comparison_state_search_memo(state),
                            )
                            next_state = self._comparison_state_update(
                                state,
                                job=M.Head(queued)(),
                                pending_packets=M.Head(M.Tail(queued)())(),
                                pending_packets_count=M.Head(M.Tail(M.Tail(queued)())())(),
                            )
        return M.Pair(next_state, self._comparison_prepare_shared_root_wave(M.Tail(states)()))

    def _comparison_apply_shared_root_wave(self, mode, job, search_memo):
        self._comparison_cache_shared_root_candidates(search_memo)
        candidates = self._comparison_shared_root_candidates
        candidate_count = self._comparison_shared_root_candidate_count
        _debug(
            "search-compare: reusing shared root candidate set for "
            + SearchModeText(mode)()
            + " with "
            + self._nat_text(candidate_count)
            + " candidates"
        )
        seeded = self._comparison_seed_rule_wave(mode, job, candidates)
        packet_count = M.Head(M.Tail(M.Tail(seeded)())())()
        _debug(
            "search-compare: built "
            + SearchModeText(mode)()
            + " root branch wave from shared candidates with "
            + self._nat_text(packet_count)
            + " ready branches"
        )
        return seeded

    def _comparison_branch_packet_job(self, job, child_state, visited, theorem_rule_cache, rewrite_rules):
        return SearchJob(
            SearchJobStart(job)(),
            SearchJobGoal(job)(),
            SearchJobRules(job)(),
            SearchJobHeuristic(job)(),
            SearchRunningLabel,
            M.Pair(child_state, M.EmptyList),
            M.Zero,
            M.Zero,
            M.Zero,
            M.EmptyList,
            visited,
            theorem_rule_cache,
            rewrite_rules,
            M.one,
        )()

    def _comparison_frontier_packets(self, frontier):
        if M.IdentityCompare(frontier, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        return M.Pair(
            self._comparison_frontier_state_packet(M.Head(frontier)()),
            self._comparison_frontier_packets(M.Tail(frontier)()),
        )

    def _comparison_packetize_job_frontier(self, mode, job):
        if M.Compare(job, M.EmptyList)() is M.truth_value:
            return M.Pair(job, M.Pair(M.EmptyList, M.Pair(M.Zero, M.EmptyList)))
        frontier = SearchJobFrontier(job)()
        if M.IdentityCompare(frontier, M.EmptyList)() is M.truth_value:
            return M.Pair(job, M.Pair(M.EmptyList, M.Pair(M.Zero, M.EmptyList)))

        packet_width = self._comparison_packet_frontier_width(mode)
        first_split = self._split_compare_job_packet(self._comparison_state(mode, job, M.EmptyList, M.Zero))
        packet_job = M.Head(first_split)()
        drained_job = M.Head(M.Tail(first_split)())()
        if M.Compare(packet_job, M.EmptyList)() is M.truth_value:
            return M.Pair(job, M.Pair(M.EmptyList, M.Pair(M.Zero, M.EmptyList)))

        packets = M.Pair(packet_job, M.EmptyList)
        packet_count = M.one
        while M.IdentityCompare(SearchJobFrontier(drained_job)(), M.EmptyList)() is M.false_value:
            next_split = self._split_compare_job_packet(self._comparison_state(mode, drained_job, M.EmptyList, M.Zero))
            next_packet = M.Head(next_split)()
            drained_job = M.Head(M.Tail(next_split)())()
            if M.Compare(next_packet, M.EmptyList)() is M.truth_value:
                break
            packets = M.Pair(next_packet, packets)
            packet_count = self._succ_nat_local(packet_count)
            if M.NatEq(packet_width, M.Zero, self.registry)() is M.truth_value:
                break
        packets = self._reverse(packets, M.EmptyList)

        _debug(
            "search-compare: "
            + SearchModeText(mode)()
            + " packetized frontier into "
            + self._nat_text(packet_count)
            + " batches; "
            + self._nat_text(SearchJobFrontierSize(drained_job)())
            + " frontier states remain in the mode job"
        )
        return M.Pair(drained_job, M.Pair(packets, M.Pair(packet_count, M.EmptyList)))

    def _comparison_rebuild_packetized_job(
        self,
        job,
        status,
        frontier,
        expanded,
        generated,
        frontier_peak,
        result_plan,
        visited,
        theorem_rule_cache,
        rewrite_rules,
        frontier_size,
    ):
        return SearchJob(
            SearchJobStart(job)(),
            SearchJobGoal(job)(),
            SearchJobRules(job)(),
            SearchJobHeuristic(job)(),
            status,
            frontier,
            expanded,
            generated,
            frontier_peak,
            result_plan,
            visited,
            theorem_rule_cache,
            rewrite_rules,
            frontier_size,
        )()

    def _comparison_expand_job_packets(self, mode, job, search_memo):
        frontier = SearchJobFrontier(job)()
        if M.IdentityCompare(frontier, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        if M.IdentityCompare(M.Tail(frontier)(), M.EmptyList)() is M.false_value:
            return M.EmptyList

        saved_search_memo = M.FromContextGetSearchMemo(self.graph)()
        prior_guard = self.graph._search_comparison_prompt_guard
        prior_ignore_root_fast_paths = self.graph._search_compare_ignore_root_fast_paths
        self.graph._replace_context(constructors=self.registry, search_memo=search_memo)
        self.graph._search_comparison_prompt_guard = None
        self.graph._search_compare_ignore_root_fast_paths = M.truth_value

        kernel = _SearchStepKernel(
            self.graph,
            job,
            SearchJobRules(job)(),
            SearchJobHeuristic(job)(),
            SearchJobGoal(job)(),
            self.registry,
            None,
            None,
        )

        mode_text = SearchModeText(mode)()

        try:
            state = M.Head(frontier)()
            current = SearchStateCurrent(state)()
            goal = SearchJobGoal(job)()
            cursor = SearchStateCursor(state)()
            expanded_total = SearchJobExpanded(job)()
            active_cursor = cursor
            theorem_rules = M.EmptyList
            theorem_generated = M.EmptyList

            if M.IdentityCompare(cursor, M.EmptyList)() is M.truth_value:
                if M.NatEq(SearchStateStepsRemaining(state)(), M.Zero, self.registry)() is M.truth_value:
                    return M.EmptyList
                if kernel._goal_reached(current, goal) is M.truth_value:
                    return M.EmptyList
                if M.Compare(
                    kernel._cached_solution(current, goal, SearchStatePlan(state)(), SearchStateStepsRemaining(state)()),
                    M.EmptyList,
                )() is M.false_value:
                    return M.EmptyList
                if kernel._seen_term(SearchStateSeen(state)(), current) is M.truth_value:
                    return M.EmptyList
                theorem_rules = kernel._theorem_rules_for(current, goal)
                self.registry = kernel.registry
                self.graph._replace_context(constructors=self.registry)
                theorem_generated = M.Tree(M.EmptyList)
            else:
                if M.IdentityCompare(M.Head(cursor)(), SearchTheoremCursorLabel)() is M.truth_value:
                    theorem_rules = SearchTheoremCursorRules(cursor)()
                    theorem_generated = SearchTheoremCursorGenerated(cursor)()
                elif M.IdentityCompare(M.Head(cursor)(), SearchRewriteCursorLabel)() is M.false_value:
                    return M.EmptyList

            theorem_packet_count = M.Zero
            theorem_packets_rev = M.EmptyList
            theorem_actions_rev = M.EmptyList
            next_theorem_generated = theorem_generated
            if M.IdentityCompare(theorem_rules, M.EmptyList)() is M.false_value:
                remaining_rules = theorem_rules
                while M.IdentityCompare(remaining_rules, M.EmptyList)() is M.false_value:
                    rule = M.Head(remaining_rules)()
                    remaining_rules = M.Tail(remaining_rules)()
                    next_term = kernel._apply_theorem_rule_at_root(rule, current)
                    next_term = kernel._canonical_term(next_term)
                    if M.TermEqual(next_term, current)() is M.truth_value:
                        continue
                    if kernel._tree_contains(next_theorem_generated, next_term) is M.truth_value:
                        continue
                    theorem_packet_count = self._succ_nat_local(theorem_packet_count)
                    theorem_actions_rev = M.Pair(TheoremAction(rule)(), theorem_actions_rev)
                    theorem_packets_rev = M.Pair(
                        self._comparison_frontier_state_packet(
                            SearchState(
                                current,
                                SearchStatePlan(state)(),
                                SearchStateSeen(state)(),
                                SearchStateStepsRemaining(state)(),
                                SearchTheoremCursor(M.Pair(rule, M.EmptyList), next_theorem_generated)(),
                            )()
                        ),
                        theorem_packets_rev,
                    )
                    next_theorem_generated = kernel._tree_insert(next_theorem_generated, next_term)
                packets_rev = theorem_packets_rev
                packet_count = theorem_packet_count
                if IsKnowledge(current)() is M.false_value:
                    packets_rev = M.Pair(
                        self._comparison_frontier_state_packet(
                            SearchState(
                                current,
                                SearchStatePlan(state)(),
                                SearchStateSeen(state)(),
                                SearchStateStepsRemaining(state)(),
                                SearchRewriteCursor(
                                    M.EmptyList,
                                    M.EmptyList,
                                    M.Pair(kernel._rewrite_frame(current, M.EmptyList), M.EmptyList),
                                    next_theorem_generated,
                                )(),
                            )()
                        ),
                        packets_rev,
                    )
                    packet_count = self._succ_nat_local(packet_count)
                if M.NatLess(M.one, packet_count, self.registry)() is M.truth_value:
                    if M.IdentityCompare(cursor, M.EmptyList)() is M.truth_value:
                        expanded_total = self._succ_nat_local(expanded_total)
                    frontier_peak = self._nat_max_local(SearchJobFrontierPeak(job)(), packet_count)
                    drained_job = self._comparison_rebuild_packetized_job(
                        job,
                        SearchRunningLabel,
                        M.EmptyList,
                        expanded_total,
                        SearchJobGenerated(job)(),
                        frontier_peak,
                        M.EmptyList,
                        SearchJobVisited(job)(),
                        M.EmptyList,
                        kernel._rewrite_rules,
                        M.Zero,
                    )
                    self.registry = kernel.registry
                    self.graph._replace_context(constructors=self.registry)
                    _debug(
                        "search-compare: "
                        + mode_text
                        + " split one theorem-ready frontier state into "
                        + self._nat_text(theorem_packet_count)
                        + " one-rule theorem packets plus "
                        + self._nat_text(self._nat_sub_or_zero_local(packet_count, theorem_packet_count))
                        + " rewrite handoff packet"
                    )
                    if M.IdentityCompare(Pmod.DEBUG_TRACE_STATE(), M.truth_value)() is M.truth_value:
                        _debug(
                            "search-compare: "
                            + mode_text
                            + " theorem fanout current="
                            + _debug_term(current, self.registry)
                            + " actions="
                            + PrettyPlanChain(self._reverse(theorem_actions_rev, M.EmptyList), self.registry)()
                        )
                    return M.Pair(
                        drained_job,
                        M.Pair(self._reverse(packets_rev, M.EmptyList), M.Pair(packet_count, M.EmptyList)),
                    )
                return M.EmptyList

            if M.IdentityCompare(cursor, M.EmptyList)() is M.truth_value:
                if IsKnowledge(current)() is M.truth_value:
                    return M.EmptyList
                expanded_total = self._succ_nat_local(expanded_total)
                active_cursor = SearchRewriteCursor(
                    M.EmptyList,
                    M.EmptyList,
                    M.Pair(kernel._rewrite_frame(current, M.EmptyList), M.EmptyList),
                    M.EmptyList,
                )()
            elif M.IdentityCompare(M.Head(cursor)(), SearchTheoremCursorLabel)() is M.truth_value:
                if IsKnowledge(current)() is M.truth_value:
                    return M.EmptyList
                active_cursor = SearchRewriteCursor(
                    M.EmptyList,
                    M.EmptyList,
                    M.Pair(kernel._rewrite_frame(current, M.EmptyList), M.EmptyList),
                    theorem_generated,
                )()
            elif M.IdentityCompare(M.Head(cursor)(), SearchRewriteCursorLabel)() is M.truth_value:
                active_cursor = cursor
            else:
                return M.EmptyList

            rewrite_packets_rev = M.EmptyList
            rewrite_packet_count = M.Zero
            rewrite_actions_rev = M.EmptyList
            working_cursor = active_cursor
            while M.IdentityCompare(working_cursor, M.EmptyList)() is M.false_value:
                frame = SearchRewriteCursorRule(working_cursor)()
                frame_rules = SearchRewriteCursorRestRules(working_cursor)()
                agenda = SearchRewriteCursorAgenda(working_cursor)()
                generated = SearchRewriteCursorGenerated(working_cursor)()

                if M.IdentityCompare(frame, M.EmptyList)() is M.truth_value:
                    if M.IdentityCompare(agenda, M.EmptyList)() is M.truth_value:
                        break
                    next_frame = M.Head(agenda)()
                    next_agenda = M.Tail(agenda)()
                    next_rules = SearchRewritePathFrameRules(next_frame)()
                    if M.IdentityCompare(next_rules, M.EmptyList)() is M.truth_value:
                        working_cursor = SearchRewriteCursor(M.EmptyList, M.EmptyList, next_agenda, generated)()
                    else:
                        working_cursor = SearchRewriteCursor(next_frame, next_rules, next_agenda, generated)()
                    continue

                subterm = SearchRewritePathFrameSubterm(frame)()
                path = SearchRewritePathFramePath(frame)()
                next_agenda = agenda
                next_frame = frame
                if M.IdentityCompare(SearchRewritePathFrameExpanded(frame)(), M.truth_value)() is M.false_value:
                    if M.IsPair(subterm)() is M.truth_value:
                        tail_frame = kernel._rewrite_frame(M.Tail(subterm)(), kernel._append_segment(path, M.one))
                        head_frame = kernel._rewrite_frame(M.Head(subterm)(), kernel._append_segment(path, M.Zero))
                        if M.IdentityCompare(SearchRewritePathFrameRules(tail_frame)(), M.EmptyList)() is M.false_value:
                            next_agenda = M.Pair(tail_frame, next_agenda)
                        if M.IdentityCompare(SearchRewritePathFrameRules(head_frame)(), M.EmptyList)() is M.false_value:
                            next_agenda = M.Pair(head_frame, next_agenda)
                    next_frame = SearchRewritePathFrame(subterm, path, SearchRewritePathFrameRules(frame)(), M.truth_value)()

                if M.IdentityCompare(frame_rules, M.EmptyList)() is M.truth_value:
                    working_cursor = SearchRewriteCursor(M.EmptyList, M.EmptyList, next_agenda, generated)()
                    continue

                remaining_rules = frame_rules
                while M.IdentityCompare(remaining_rules, M.EmptyList)() is M.false_value:
                    active_rule = M.Head(remaining_rules)()
                    remaining_rules = M.Tail(remaining_rules)()
                    rewrite_packet_count = self._succ_nat_local(rewrite_packet_count)
                    rewrite_actions_rev = M.Pair(RewriteAction(active_rule, path)(), rewrite_actions_rev)
                    rewrite_packets_rev = M.Pair(
                        self._comparison_frontier_state_packet(
                            SearchState(
                                current,
                                SearchStatePlan(state)(),
                                SearchStateSeen(state)(),
                                SearchStateStepsRemaining(state)(),
                                SearchRewriteCursor(next_frame, M.Pair(active_rule, M.EmptyList), M.EmptyList, generated)(),
                            )()
                        ),
                        rewrite_packets_rev,
                    )
                working_cursor = SearchRewriteCursor(M.EmptyList, M.EmptyList, next_agenda, generated)()

            if M.NatLess(M.one, rewrite_packet_count, self.registry)() is M.false_value:
                return M.EmptyList

            frontier_peak = self._nat_max_local(SearchJobFrontierPeak(job)(), rewrite_packet_count)
            drained_job = self._comparison_rebuild_packetized_job(
                job,
                SearchRunningLabel,
                M.EmptyList,
                expanded_total,
                SearchJobGenerated(job)(),
                frontier_peak,
                M.EmptyList,
                SearchJobVisited(job)(),
                M.EmptyList,
                kernel._rewrite_rules,
                M.Zero,
            )
            self.registry = kernel.registry
            self.graph._replace_context(constructors=self.registry)
            _debug(
                "search-compare: "
                + mode_text
                + " split one rewrite cursor into "
                + self._nat_text(rewrite_packet_count)
                + " one-rule rewrite packets"
            )
            if M.IdentityCompare(Pmod.DEBUG_TRACE_STATE(), M.truth_value)() is M.truth_value:
                _debug(
                    "search-compare: "
                    + mode_text
                    + " rewrite fanout current="
                    + _debug_term(current, self.registry)
                    + " actions="
                    + PrettyPlanChain(self._reverse(rewrite_actions_rev, M.EmptyList), self.registry)()
                )
            return M.Pair(
                drained_job,
                M.Pair(self._reverse(rewrite_packets_rev, M.EmptyList), M.Pair(rewrite_packet_count, M.EmptyList)),
            )
        finally:
            if kernel is not None:
                self.registry = kernel.registry
            self.graph._replace_context(constructors=self.registry, search_memo=saved_search_memo)
            self.graph._search_comparison_prompt_guard = prior_guard
            self.graph._search_compare_ignore_root_fast_paths = prior_ignore_root_fast_paths

    def _packet_queue_from_job(self, mode, job, search_memo):
        if self._comparison_is_fresh_root_job(job) is M.false_value:
            expanded = self._comparison_expand_job_packets(mode, job, search_memo)
            if M.Compare(expanded, M.EmptyList)() is M.false_value:
                return expanded
        return self._comparison_packetize_job_frontier(mode, job)

    def _comparison_state_enqueue_job_frontier(self, state):
        (
            mode,
            job,
            search_memo,
            active_packets,
            pending_packets,
            pending_packets_count,
            phase,
            completed_packets,
            root_fast_path_result,
            stop_reason,
        ) = self._comparison_state_unpack(state)
        if M.IdentityCompare(self._comparison_state_status(state), SearchRunningLabel)() is M.false_value:
            return state
        if M.Compare(job, M.EmptyList)() is M.truth_value:
            return state
        if M.IdentityCompare(pending_packets, M.EmptyList)() is M.false_value:
            return state
        if M.IdentityCompare(SearchJobFrontier(job)(), M.EmptyList)() is M.truth_value:
            return state
        _debug(
            "search-compare: packetizing frontier for "
            + SearchModeText(mode)()
            + " mode-active-processes="
            + self._nat_text(active_packets)
            + " mode-queued-packets="
            + self._nat_text(pending_packets_count)
            + " mode-completed-packets="
            + self._nat_text(completed_packets)
            + " frontier="
            + self._nat_text(SearchJobFrontierSize(job)())
        )
        queue_pair = self._packet_queue_from_job(
            mode,
            job,
            search_memo,
        )
        drained_job = M.Head(queue_pair)()
        new_packets = M.Head(M.Tail(queue_pair)())()
        new_packet_count = M.Head(M.Tail(M.Tail(queue_pair)())())()
        merged_pending = new_packets
        merged_pending_count = new_packet_count
        if M.IdentityCompare(SearchJobStatus(drained_job)(), SearchSuccessLabel)() is M.truth_value:
            merged_pending = M.EmptyList
            merged_pending_count = M.Zero
        if M.NatEq(new_packet_count, M.Zero, self.registry)() is M.false_value:
            _debug(
                "search-compare: "
                + SearchModeText(mode)()
                + " discovered "
                + self._nat_text(new_packet_count)
                + " branch packets; mode-active-processes="
                + self._nat_text(active_packets)
                + " mode-queued-packets="
                + self._nat_text(merged_pending_count)
                + " mode-completed-packets="
                + self._nat_text(completed_packets)
            )
            _debug(
                "search-compare: examined the frontier for "
                + SearchModeText(mode)()
                + " and formed a branch wave with "
                + self._nat_text(merged_pending_count)
                + " ready branches"
            )
        next_state = self._comparison_state(
            mode,
            drained_job,
            search_memo,
            active_packets,
            merged_pending,
            merged_pending_count,
            phase,
            completed_packets,
            root_fast_path_result,
            stop_reason,
        )
        return next_state

    def _comparison_states_enqueue_all_packets(self, states, best_cost=M.EmptyList, widen_packets=M.false_value):
        if M.IdentityCompare(states, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        trimmed_state = self._comparison_state_without_exhausted_pending_packets(M.Head(states)(), best_cost)
        next_state = self._comparison_state_enqueue_job_frontier(trimmed_state)
        if M.IdentityCompare(widen_packets, M.truth_value)() is M.truth_value:
            next_state = self._comparison_widen_pending_packets(next_state)
        return M.Pair(next_state, self._comparison_states_enqueue_all_packets(M.Tail(states)(), best_cost, widen_packets))


    def _comparison_packet_optimistic_bound(self, mode, packet):
        packet_state = self._comparison_packet_state(mode, packet)
        if M.IdentityCompare(packet_state, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        return SearchStateStepsRemaining(packet_state)()

    def _comparison_packet_prunable(self, mode, packet, best_cost):
        if M.Compare(best_cost, M.EmptyList)() is M.truth_value:
            return M.false_value
        packet_bound = self._comparison_packet_optimistic_bound(mode, packet)
        if M.Compare(packet_bound, M.EmptyList)() is M.truth_value:
            return M.false_value
        if M.NatLess(packet_bound, best_cost, self.registry)() is M.truth_value:
            return M.false_value
        return M.truth_value

    def _comparison_state_has_dispatchable_packet(self, mode, pending_packets, best_cost=M.EmptyList):
        if M.IdentityCompare(pending_packets, M.EmptyList)() is M.truth_value:
            return M.false_value
        packet = M.Head(pending_packets)()
        if self._comparison_packet_is_dispatchable(mode, packet) is M.false_value:
            return self._comparison_state_has_dispatchable_packet(mode, M.Tail(pending_packets)(), best_cost)
        if self._comparison_packet_prunable(mode, packet, best_cost) is M.truth_value:
            return self._comparison_state_has_dispatchable_packet(mode, M.Tail(pending_packets)(), best_cost)
        return M.truth_value

    def _comparison_state_dispatchable_packet_count(self, mode, pending_packets, best_cost=M.EmptyList):
        if M.IdentityCompare(pending_packets, M.EmptyList)() is M.truth_value:
            return M.Zero
        packet = M.Head(pending_packets)()
        if self._comparison_packet_is_dispatchable(mode, packet) is M.false_value:
            return self._comparison_state_dispatchable_packet_count(mode, M.Tail(pending_packets)(), best_cost)
        if self._comparison_packet_prunable(mode, packet, best_cost) is M.truth_value:
            return self._comparison_state_dispatchable_packet_count(mode, M.Tail(pending_packets)(), best_cost)
        return self._succ_nat_local(self._comparison_state_dispatchable_packet_count(mode, M.Tail(pending_packets)(), best_cost))


    def _comparison_state_has_dispatchable_work(self, state, best_cost=M.EmptyList):
        if M.IdentityCompare(self._comparison_state_status(state), SearchRunningLabel)() is M.false_value:
            return M.false_value

        pending_packets = self._comparison_state_pending_packets(state)
        if M.IdentityCompare(pending_packets, M.EmptyList)() is M.truth_value:
            return M.false_value

        return self._comparison_state_has_dispatchable_packet(self._comparison_state_mode(state), pending_packets, best_cost)



    def _dispatchable_backlog(self, state, best_cost=M.EmptyList):
        if self._comparison_state_has_dispatchable_work(state, best_cost) is M.false_value:
            return M.Zero
        return self._comparison_state_dispatchable_packet_count(self._comparison_state_mode(state), self._comparison_state_pending_packets(state), best_cost)

    def _dispatchable_better(self, candidate_state, best_state, best_cost=M.EmptyList):
        if M.IdentityCompare(best_state, M.EmptyList)() is M.truth_value:
            return M.truth_value
        candidate_backlog = self._dispatchable_backlog(candidate_state, best_cost)
        best_backlog = self._dispatchable_backlog(best_state, best_cost)
        if M.NatLess(best_backlog, candidate_backlog, self.registry)() is M.truth_value:
            return M.truth_value
        if M.NatLess(candidate_backlog, best_backlog, self.registry)() is M.truth_value:
            return M.false_value
        candidate_active = self._comparison_state_active_packets(candidate_state)
        best_active = self._comparison_state_active_packets(best_state)
        if M.NatLess(candidate_active, best_active, self.registry)() is M.truth_value:
            return M.truth_value
        return M.false_value

    def _choose_dispatchable_state(self, states, best_state, best_cost=M.EmptyList):
        if M.IdentityCompare(states, M.EmptyList)() is M.truth_value:
            return best_state
        state = M.Head(states)()
        next_best = best_state
        if self._comparison_state_has_dispatchable_work(state, best_cost) is M.truth_value:
            if self._dispatchable_better(state, best_state, best_cost) is M.truth_value:
                next_best = state
        return self._choose_dispatchable_state(M.Tail(states)(), next_best, best_cost)

    def _next_dispatchable_state(self, states, best_cost=M.EmptyList):
        return self._choose_dispatchable_state(states, M.EmptyList, best_cost)

    def _worker_baseline(self, state):
        parent_job = self._comparison_state_job(state)
        return SearchWorkerBaseline(
            M.FromContextGetConstructors(self.graph)(),
            SearchJobStart(parent_job)(),
            SearchJobGoal(parent_job)(),
            SearchJobRules(parent_job)(),
            SearchJobHeuristic(parent_job)(),
            SearchJobRewriteRules(parent_job)(),
            self._comparison_generation,
        )()

    def _worker_setup(self, state):
        return SearchWorkerSetup(self._comparison_state_mode(state), self._worker_baseline(state))()

    def _worker_problem_packet(self, state, packet_descriptor, step_budget, packet_token):
        parent_job = self._comparison_state_job(state)
        return SearchWorkerPacket(
            packet_descriptor,
            M.EmptyList,
            SearchJobVisited(parent_job)(),
            M.EmptyList,
            SearchJobRewriteRules(parent_job)(),
            step_budget,
            Pmod.DEBUG_TRACE_STATE(),
            M.truth_value,
            M.truth_value,
            packet_token,
            self._comparison_generation,
        )()

    def _comparison_packet_budget(self, mode, packet_state):
        packet = packet_state
        packet_state = self._comparison_packet_state(mode, packet)
        if M.IdentityCompare(packet_state, M.EmptyList)() is M.truth_value:
            return M.one
        quantum = HeuristicBeamWidth(self.heuristic)()
        if M.NatEq(quantum, M.Zero, self.registry)() is M.truth_value:
            quantum = self._comparison_packet_frontier_width(mode)
        else:
            quantum = self._succ_nat_local(quantum)
        if M.IsPair(packet)() is M.truth_value:
            if M.IdentityCompare(M.Head(packet)(), SearchJobLabel)() is M.truth_value:
                frontier_size = SearchJobFrontierSize(packet)()
                scaled_pair = M.Multiply(frontier_size, quantum, self.registry)()
                quantum = M.Head(scaled_pair)()
                self.registry = M.Head(M.Tail(scaled_pair)())()
                if M.NatEq(quantum, M.Zero, self.registry)() is M.truth_value:
                    return M.one
                return quantum
        return self._nat_min_local(SearchStateStepsRemaining(packet_state)(), quantum)

    def _comparison_packet_job_for_state(self, state, packet_state):
        if M.IsPair(packet_state)() is M.truth_value:
            if M.IdentityCompare(M.Head(packet_state)(), SearchJobLabel)() is M.truth_value:
                return packet_state
        mode = self._comparison_state_mode(state)
        packet_state = self._comparison_packet_state(mode, packet_state)
        parent_job = self._comparison_state_job(state)
        return SearchJob(
            SearchJobStart(parent_job)(),
            SearchJobGoal(parent_job)(),
            SearchJobRules(parent_job)(),
            SearchJobHeuristic(parent_job)(),
            SearchRunningLabel,
            M.Pair(packet_state, M.EmptyList),
            M.Zero,
            M.Zero,
            M.Zero,
            M.EmptyList,
            SearchJobVisited(parent_job)(),
            M.EmptyList,
            SearchJobRewriteRules(parent_job)(),
            M.one,
        )()

    def _total_resident_executor_count(self, workers, idle_executors):
        return self._nat_add_local(self._worker_entry_count(workers), self._idle_executor_count(idle_executors))

    def _desired_resident_executor_total(self, states, workers, idle_executors):
        resident = self._total_resident_executor_count(workers, idle_executors)
        target_total = self._comparison_live_process_budget(states, workers)
        if M.NatLess(target_total, resident, self.registry)() is M.truth_value:
            return resident
        return target_total

    def _resident_executor(self, slot, process, task_queue, result_queue):
        return M.Pair(
            slot,
            M.Pair(
                process,
                M.Pair(
                    task_queue,
                    M.Pair(
                        result_queue,
                        M.Pair(M.EmptyList, M.Pair(M.EmptyList, M.Pair(M.EmptyList, M.EmptyList))),
                    ),
                ),
            ),
        )

    def _resident_executor_with_baseline(self, executor, generation, mode, rewrite_rules):
        return M.Pair(
            self._resident_executor_slot(executor),
            M.Pair(
                self._resident_executor_process(executor),
                M.Pair(
                    self._resident_executor_task_queue(executor),
                    M.Pair(
                        self._resident_executor_result_queue(executor),
                        M.Pair(generation, M.Pair(mode, M.Pair(rewrite_rules, M.EmptyList))),
                    ),
                ),
            ),
        )

    def _resident_executor_slot(self, executor):
        return M.Head(executor)()

    def _resident_executor_process(self, executor):
        return M.Head(M.Tail(executor)())()

    def _resident_executor_task_queue(self, executor):
        return M.Head(M.Tail(M.Tail(executor)())())()

    def _resident_executor_result_queue(self, executor):
        return M.Head(M.Tail(M.Tail(M.Tail(executor)())())())()

    def _resident_executor_generation(self, executor):
        suffix = M.Tail(M.Tail(M.Tail(M.Tail(executor)())())())()
        if M.IdentityCompare(suffix, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        return M.Head(suffix)()

    def _resident_executor_mode(self, executor):
        suffix = M.Tail(M.Tail(M.Tail(M.Tail(executor)())())())()
        if M.IdentityCompare(suffix, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        tail = M.Tail(suffix)()
        if M.IdentityCompare(tail, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        return M.Head(tail)()

    def _resident_executor_rewrite_rules(self, executor):
        suffix = M.Tail(M.Tail(M.Tail(M.Tail(executor)())())())()
        if M.IdentityCompare(suffix, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        tail = M.Tail(suffix)()
        if M.IdentityCompare(tail, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        rewrite_payload = M.Tail(tail)()
        if M.IdentityCompare(rewrite_payload, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        return M.Head(rewrite_payload)()

    def _worker_entry(self, mode, executor, packet_job, packet_token):
        return M.Pair(mode, M.Pair(executor, M.Pair(packet_job, M.Pair(packet_token, M.Pair(time.time(), M.EmptyList)))))

    def _worker_entry_mode(self, entry):
        return M.Head(entry)()

    def _worker_entry_executor(self, entry):
        return M.Head(M.Tail(entry)())()

    def _worker_entry_process(self, entry):
        return self._resident_executor_process(self._worker_entry_executor(entry))

    def _worker_entry_queue(self, entry):
        return self._resident_executor_result_queue(self._worker_entry_executor(entry))

    def _worker_entry_packet_job(self, entry):
        return M.Head(M.Tail(M.Tail(entry)())())()

    def _worker_entry_packet_token(self, entry):
        payload = M.Tail(M.Tail(entry)())()
        if M.IdentityCompare(payload, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        rest = M.Tail(payload)()
        if M.IdentityCompare(rest, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        return M.Head(rest)()

    def _worker_entry_slot(self, entry):
        return self._resident_executor_slot(self._worker_entry_executor(entry))

    def _worker_entry_started_at(self, entry):
        payload = M.Tail(M.Tail(entry)())()
        if M.IdentityCompare(payload, M.EmptyList)() is M.truth_value:
            return None
        rest = M.Tail(payload)()
        if M.IdentityCompare(rest, M.EmptyList)() is M.truth_value:
            return None
        started_payload = M.Tail(rest)()
        if M.IdentityCompare(started_payload, M.EmptyList)() is M.truth_value:
            return None
        return M.Head(started_payload)()

    def _worker_entry_elapsed_seconds(self, entry):
        started_at = self._worker_entry_started_at(entry)
        if started_at is None:
            return 0.0
        elapsed_seconds = time.time() - started_at
        if elapsed_seconds < 0.0:
            return 0.0
        return elapsed_seconds

    def _oldest_active_worker_entry(self, workers):
        best_entry = M.EmptyList
        remaining_workers = workers
        best_elapsed_seconds = -1.0
        while M.IdentityCompare(remaining_workers, M.EmptyList)() is M.false_value:
            candidate = M.Head(remaining_workers)()
            candidate_elapsed_seconds = self._worker_entry_elapsed_seconds(candidate)
            if candidate_elapsed_seconds > best_elapsed_seconds:
                best_entry = candidate
                best_elapsed_seconds = candidate_elapsed_seconds
            remaining_workers = M.Tail(remaining_workers)()
        return best_entry

    def _sync_graph_live_compare_snapshot(self, states, workers, idle_executors):
        self.graph._search_compare_live_signature = self.signature
        self.graph._search_compare_live_start = self.start
        self.graph._search_compare_live_goal = self.goal
        self.graph._search_compare_live_states = states
        self.graph._search_compare_live_workers = workers
        self.graph._search_compare_live_idle_executors = idle_executors

    def _clear_graph_live_compare_snapshot(self):
        self.graph._search_compare_live_signature = M.EmptyList
        self.graph._search_compare_live_start = M.EmptyList
        self.graph._search_compare_live_goal = M.EmptyList
        self.graph._search_compare_live_states = M.EmptyList
        self.graph._search_compare_live_workers = M.EmptyList
        self.graph._search_compare_live_idle_executors = M.EmptyList

    def _worker_entry_count(self, workers):
        if M.IdentityCompare(workers, M.EmptyList)() is M.truth_value:
            return M.Zero
        count = M.Atom()
        count.value = M.CountRep(workers)()
        return count

    def _idle_executor_count(self, idle_executors):
        if M.IdentityCompare(idle_executors, M.EmptyList)() is M.truth_value:
            return M.Zero
        count = M.Atom()
        count.value = M.CountRep(idle_executors)()
        return count

    def _spawn_parallel_executor(self, mp_context, slot):
        from .runtime import _SearchModeWorkerExecutor

        slot_text = self._nat_text(slot)
        task_queue = mp_context.Queue()
        result_queue = mp_context.Queue()
        process = mp_context.Process(
            target=_SearchModeWorkerExecutor,
            args=(slot_text, task_queue, result_queue),
        )
        process.start()
        executor = self._resident_executor(slot, process, task_queue, result_queue)
        if self._await_parallel_executor_ready(executor) is M.false_value:
            self._retire_parallel_executor(executor, "retiring unready resident executor ")
            raise RuntimeError("search-compare: resident executor did not acknowledge startup")
        _debug(
            "search-compare: resident executor "
            + slot_text
            + " ready pid="
            + str(process.pid)
        )
        return executor

    def _parallel_executor_ready_message(self, payload):
        if M.IsPair(payload)() is M.false_value:
            return M.false_value
        return M.IdentityCompare(M.Head(payload)(), SearchWorkerReadyLabel)()

    def _await_parallel_executor_ready(self, executor):
        process = self._resident_executor_process(executor)
        result_queue = self._resident_executor_result_queue(executor)
        while process.is_alive():
            try:
                payload = result_queue.get_nowait()
            except queue.Empty:
                time.sleep(0.01)
                continue
            if self._parallel_executor_ready_message(payload) is M.truth_value:
                return M.truth_value
            return M.false_value
        return M.false_value

    def _start_parallel_executor_pool(self, mp_context):
        _debug("search-compare: elastic resident executor pool starts empty and grows on demand")
        return M.EmptyList

    def _grow_parallel_executor_pool(self, mp_context, idle_executors, states, workers):
        target_total = self._desired_resident_executor_total(states, workers, idle_executors)
        current_total = self._total_resident_executor_count(workers, idle_executors)
        spawned_now = M.Zero
        spawned_rev = M.EmptyList
        while M.NatLess(current_total, target_total, self.registry)() is M.truth_value:
            slot = self._succ_nat_local(current_total)
            try:
                executor = self._spawn_parallel_executor(mp_context, slot)
            except Exception as error:
                _debug(
                    "search-compare: resident executor spawn unavailable at slot "
                    + self._nat_text(slot)
                    + " ("
                    + str(error)
                    + "); leaving the remaining branch wave queued for retry"
                )
                break
            spawned_rev = M.Pair(executor, spawned_rev)
            current_total = slot
            spawned_now = self._succ_nat_local(spawned_now)
        if M.NatEq(spawned_now, M.Zero, self.registry)() is M.false_value:
            _debug(
                "search-compare: expanded elastic resident executor pool by "
                + self._nat_text(spawned_now)
                + " local workers; local capacity now "
                + self._nat_text(current_total)
            )
        return Append(idle_executors, self._reverse(spawned_rev, M.EmptyList))()

    def _shutdown_idle_parallel_executors(self, idle_executors):
        if M.IdentityCompare(idle_executors, M.EmptyList)() is M.truth_value:
            return
        executor = M.Head(idle_executors)()
        self._retire_parallel_executor(executor, "shutting down idle packet worker ")
        self._shutdown_idle_parallel_executors(M.Tail(idle_executors)())

    def _retire_parallel_executor(self, executor, prefix_text):
        process = self._resident_executor_process(executor)
        task_queue = self._resident_executor_task_queue(executor)
        slot_text = self._nat_text(self._resident_executor_slot(executor))
        if process.is_alive():
            _debug(
                "search-compare: "
                + prefix_text
                + slot_text
                + " pid="
                + str(process.pid)
            )
            task_queue.put(None)
            process.join(0.1)
            if process.is_alive():
                process.terminate()
                process.join()

    def _kill_parallel_worker_entry(self, entry):
        process = self._worker_entry_process(entry)
        if process.is_alive():
            _debug(
                "search-compare: terminating unfinished packet for "
                + SearchModeText(self._worker_entry_mode(entry))()
                + " on resident executor "
                + self._nat_text(self._worker_entry_slot(entry))
                + " pid="
                + str(process.pid)
            )
            process.terminate()
        process.join()

    def _parallel_launch_result_launch(self, result):
        return M.Head(result)()

    def _parallel_launch_result_process(self, result):
        return M.Head(M.Tail(result)())()

    def _parallel_launch_result_queue(self, result):
        return M.Head(M.Tail(M.Tail(result)())())()

    def _dequeue_parallel_worker_launch(self, state, launch_slot, launch_budget):
        (
            mode,
            parent_job,
            search_memo,
            active_before,
            pending_packets,
            pending_packets_count,
            phase,
            completed_packets,
            root_fast_path_result,
            stop_reason,
        ) = self._comparison_state_unpack(state)
        packet_state = M.Head(pending_packets)()
        remaining_packets = M.Tail(pending_packets)()
        step_budget = self._comparison_packet_budget(mode, packet_state)
        branch_serial = self._nat_add_local(
            completed_packets,
            active_before,
        )
        branch_serial = self._succ_nat_local(branch_serial)

        _debug(
            "search-compare: staging resident lease "
            + self._nat_text(launch_slot)
            + "/"
            + self._nat_text(launch_budget)
            + " -> "
            + SearchModeText(mode)()
            + " packet "
            + self._nat_text(branch_serial)
        )

        packet_token = self._succ_nat_local(self._comparison_packet_token)
        self._comparison_packet_token = packet_token
        setup = self._worker_setup(state)
        payload = self._worker_problem_packet(state, packet_state, step_budget, packet_token)

        active_packets = self._succ_nat_local(active_before)
        remaining_count = self._pred_nat_or_zero_local(pending_packets_count)

        next_state = self._comparison_state_update(
            state,
            active_packets=active_packets,
            pending_packets=remaining_packets,
            pending_packets_count=remaining_count,
        )
        launch = SearchWorkerLaunch(
            mode,
            setup,
            payload,
            packet_state,
            launch_slot,
            launch_budget,
            branch_serial,
        )()

        _debug(
            "search-compare: staged "
            + self._nat_text(launch_slot)
            + "/"
            + self._nat_text(launch_budget)
            + " resident leases already; latest="
            + SearchModeText(mode)()
            + " packet "
            + self._nat_text(branch_serial)
        )
        return M.Pair(next_state, M.Pair(launch, M.EmptyList))

    def _collect_parallel_worker_launches(self, mp_context, states, workers, idle_executors):
        worker_budget = self._comparison_live_process_budget(states, workers)
        self._current_worker_process_budget = worker_budget
        current_workers = workers
        current_worker_count = self._worker_entry_count(workers)
        current_states = states
        current_idle_executors = idle_executors
        launched_now = M.Zero
        best_cost = self._comparison_best_finished_attempt_cost(states)

        while M.NatLess(current_worker_count, worker_budget, self.registry)() is M.truth_value:
            state = self._next_dispatchable_state(current_states, best_cost)
            if M.Compare(state, M.EmptyList)() is M.truth_value:
                break
            state = self._comparison_state_without_exhausted_pending_packets(state, best_cost)
            if self._comparison_state_has_dispatchable_work(state, best_cost) is M.false_value:
                break
            launch_slot = self._succ_nat_local(current_worker_count)
            queued = self._dequeue_parallel_worker_launch(state, launch_slot, worker_budget)
            next_state = M.Head(queued)()
            launch = M.Head(M.Tail(queued)())()
            started = self._start_parallel_workers(
                mp_context,
                current_workers,
                current_idle_executors,
                M.Pair(launch, M.EmptyList),
            )
            started_now = M.Head(started)()
            current_idle_executors = M.Head(M.Tail(started)())()
            if M.IdentityCompare(started_now, M.EmptyList)() is M.truth_value:
                mode = SearchWorkerLaunchMode(launch)()
                branch_serial = SearchWorkerLaunchBranchSerial(launch)()
                _debug(
                    "search-compare: resident executor unavailable; leaving "
                    + SearchModeText(mode)()
                    + " packet "
                    + self._nat_text(branch_serial)
                    + " queued for resident retry"
                )
                break
            current_workers = Append(started_now, current_workers)()
            current_worker_count = self._succ_nat_local(current_worker_count)
            launched_now = self._succ_nat_local(launched_now)
            current_states = self._replace_comparison_state(
                current_states,
                self._comparison_state_mode(state),
                next_state,
            )

        return M.Pair(
            current_states,
            M.Pair(
                current_workers,
                M.Pair(current_idle_executors, M.Pair(launched_now, M.EmptyList)),
            ),
        )

    def _start_parallel_workers(self, mp_context, workers, idle_executors, launches):
        if M.IdentityCompare(launches, M.EmptyList)() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(idle_executors, M.EmptyList))

        launched_workers_rev = M.EmptyList
        remaining_launches = launches
        remaining_idle_executors = idle_executors
        resident_total = self._nat_add_local(
            self._worker_entry_count(workers),
            self._idle_executor_count(idle_executors),
        )

        while M.IdentityCompare(remaining_launches, M.EmptyList)() is M.false_value:
            launch = M.Head(remaining_launches)()
            mode = SearchWorkerLaunchMode(launch)()
            branch_serial = SearchWorkerLaunchBranchSerial(launch)()
            if M.IdentityCompare(remaining_idle_executors, M.EmptyList)() is M.truth_value:
                next_slot = self._succ_nat_local(resident_total)
                _debug(
                    "search-compare: spawning resident executor on demand for "
                    + SearchModeText(mode)()
                    + " packet "
                    + self._nat_text(branch_serial)
                )
                try:
                    executor = self._spawn_parallel_executor(mp_context, next_slot)
                except Exception as error:
                    _debug(
                        "search-compare: resident executor spawn unavailable while leasing "
                        + SearchModeText(mode)()
                        + " packet "
                        + self._nat_text(branch_serial)
                        + " ("
                        + str(error)
                        + "); leaving the remaining branch wave queued for retry"
                    )
                    break
                resident_total = next_slot
            else:
                executor = M.Head(remaining_idle_executors)()
                remaining_idle_executors = M.Tail(remaining_idle_executors)()

            packet_state = SearchWorkerLaunchPacketState(launch)()
            launch_slot = SearchWorkerLaunchSlot(launch)()
            launch_budget = SearchWorkerLaunchBudget(launch)()
            launch_setup = SearchWorkerLaunchSetup(launch)()
            launch_payload = SearchWorkerLaunchPayload(launch)()
            launch_baseline = SearchWorkerSetupBaseline(launch_setup)()
            baseline_rewrite_rules = SearchWorkerBaselineRewriteRules(launch_baseline)()
            packet_token = SearchWorkerPacketPacketToken(launch_payload)()
            task_queue = self._resident_executor_task_queue(executor)
            slot_text = self._nat_text(self._resident_executor_slot(executor))
            live_after_lease = self._nat_add_local(
                self._worker_entry_count(workers),
                self._succ_nat_local(self._worker_entry_count(launched_workers_rev)),
            )

            _debug(
                "search-compare: leasing resident executor "
                + slot_text
                + " for "
                + SearchModeText(mode)()
                + " packet "
                + self._nat_text(branch_serial)
                + " ("
                + self._nat_text(launch_slot)
                + "/"
                + self._nat_text(launch_budget)
                + ") live="
                + self._nat_text(live_after_lease)
                + " idle="
                + self._nat_text(self._idle_executor_count(remaining_idle_executors))
            )

            queued_payload = launch_payload
            payload_rewrite_rules = SearchWorkerPacketRewriteRules(launch_payload)()
            send_setup = M.false_value
            if M.TermEqual(self._resident_executor_generation(executor), self._comparison_generation)() is M.false_value:
                send_setup = M.truth_value
            elif M.TermEqual(self._resident_executor_mode(executor), mode)() is M.false_value:
                send_setup = M.truth_value
            elif M.IdentityCompare(payload_rewrite_rules, M.EmptyList)() is M.false_value:
                executor_rewrite_rules = self._resident_executor_rewrite_rules(executor)
                if M.IdentityCompare(executor_rewrite_rules, M.EmptyList)() is M.truth_value:
                    send_setup = M.truth_value
                elif M.TermEqual(executor_rewrite_rules, payload_rewrite_rules)() is M.false_value:
                    send_setup = M.truth_value
            if M.IdentityCompare(send_setup, M.truth_value)() is M.truth_value:
                task_queue.put(launch_setup)
                executor = self._resident_executor_with_baseline(
                    executor,
                    self._comparison_generation,
                    mode,
                    baseline_rewrite_rules,
                )
            if M.IdentityCompare(payload_rewrite_rules, M.EmptyList)() is M.false_value:
                queued_payload = SearchWorkerPacket(
                    SearchWorkerPacketDescriptor(launch_payload)(),
                    SearchWorkerPacketSearchMemo(launch_payload)(),
                    SearchWorkerPacketVisited(launch_payload)(),
                    SearchWorkerPacketTheoremRuleCache(launch_payload)(),
                    M.EmptyList,
                    SearchWorkerPacketStepBudget(launch_payload)(),
                    SearchWorkerPacketDebugTrace(launch_payload)(),
                    SearchWorkerPacketIgnoreRootFastPaths(launch_payload)(),
                    SearchWorkerPacketDiscoveryMode(launch_payload)(),
                    SearchWorkerPacketPacketToken(launch_payload)(),
                    SearchWorkerPacketGeneration(launch_payload)(),
                )()
            launch = SearchWorkerLaunch(
                mode,
                launch_setup,
                queued_payload,
                packet_state,
                launch_slot,
                launch_budget,
                branch_serial,
            )()
            task_queue.put(launch)
            launched_workers_rev = M.Pair(
                self._worker_entry(mode, executor, packet_state, packet_token),
                launched_workers_rev,
            )

            _debug(
                "search-compare: leased "
                + self._nat_text(launch_slot)
                + "/"
                + self._nat_text(launch_budget)
                + " local executors already; latest="
                + SearchModeText(mode)()
                + " packet "
                + self._nat_text(branch_serial)
            )
            remaining_launches = M.Tail(remaining_launches)()

        return M.Pair(
            self._reverse(launched_workers_rev, M.EmptyList),
            M.Pair(remaining_idle_executors, M.EmptyList),
        )

    def _fill_parallel_workers(self, mp_context, idle_executors, states, workers):
        current_states = states
        current_workers = workers
        current_idle_executors = idle_executors
        prior_total_queued = self._comparison_total_queued_packets(current_states)

        if self._comparison_states_need_shared_root_wave(current_states) is M.truth_value:
            current_idle_executors = self._grow_parallel_executor_pool(
                mp_context,
                current_idle_executors,
                current_states,
                current_workers,
            )
        self._comparison_root_wave_idle_executors = current_idle_executors
        current_states = self._comparison_prepare_shared_root_wave(current_states)
        current_idle_executors = self._comparison_root_wave_idle_executors
        best_cost = self._comparison_best_finished_attempt_cost(current_states)

        _debug(
            "search-compare: rechecking fixed mode frontiers for newly packetizable work before refill; "
            + self._comparison_live_process_budget_text(current_states, current_workers)
        )
        current_states = self._comparison_states_enqueue_all_packets(current_states, best_cost, M.truth_value)
        next_total_queued = self._comparison_total_queued_packets(current_states)
        if M.NatLess(prior_total_queued, next_total_queued, self.registry)() is M.truth_value:
            _debug(
                "search-compare: all fixed mode frontiers are packetized; total ready branches="
                + self._nat_text(next_total_queued)
                + "; "
                + self._comparison_live_process_budget_text(current_states, current_workers)
            )

        launchable_budget = self._comparison_live_process_budget(current_states, current_workers)
        launchable_workers = self._worker_entry_count(current_workers)
        if M.NatLess(launchable_workers, launchable_budget, self.registry)() is M.truth_value:
            total_queued = self._comparison_total_queued_packets(current_states)
            launch_now = self._nat_sub_or_zero_local(launchable_budget, launchable_workers)
            remaining_queued = self._nat_sub_or_zero_local(total_queued, launch_now)
            _debug(
                "search-compare: global branch backlog currently has "
                + self._nat_text(total_queued)
                + " ready branches; launching "
                + self._nat_text(launch_now)
                + " resident executors now, "
                + self._nat_text(remaining_queued)
                + " still queued"
            )
            _debug(
                "search-compare: "
                + self._comparison_live_process_budget_text(current_states, current_workers)
                + " for "
                + self._mode_chain_text(self._mode_chain())
            )
            _debug(
                "search-compare: scheduler sees "
                + self._comparison_live_process_budget_text(current_states, current_workers)
                + "; leasing resident workers now"
            )

        queued = self._collect_parallel_worker_launches(mp_context, current_states, current_workers, current_idle_executors)
        current_states = M.Head(queued)()
        current_workers = M.Head(M.Tail(queued)())()
        current_idle_executors = M.Head(M.Tail(M.Tail(queued)())())()
        launched_now = M.Head(M.Tail(M.Tail(M.Tail(queued)())())())()
        if M.NatEq(launched_now, M.Zero, self.registry)() is M.false_value:
            _debug(
                "search-compare: launched "
                + self._nat_text(launched_now)
                + " resident worker leases this cycle; "
                + self._comparison_live_process_budget_text(current_states, current_workers)
            )

        self._current_worker_process_budget = self._comparison_live_process_budget(current_states, current_workers)
        return M.Pair(
            current_states,
            M.Pair(current_workers, M.Pair(current_idle_executors, M.EmptyList)),
        )

    def _first_finished_worker(self, workers, acc):
        if M.IdentityCompare(workers, M.EmptyList)() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(M.EmptyList, M.Pair(self._reverse(acc, M.EmptyList), M.EmptyList)))
        entry = M.Head(workers)()
        process = self._worker_entry_process(entry)
        result_queue = self._worker_entry_queue(entry)

        try:
            payload = result_queue.get_nowait()
            return M.Pair(
                entry,
                M.Pair(
                    payload,
                    M.Pair(Append(self._reverse(acc, M.EmptyList), M.Tail(workers)())(), M.EmptyList),
                ),
            )
        except queue.Empty:
            if process.is_alive():
                return self._first_finished_worker(M.Tail(workers)(), M.Pair(entry, acc))
            process.join(0.01)
            return M.Pair(
                entry,
                M.Pair(
                    None,
                    M.Pair(Append(self._reverse(acc, M.EmptyList), M.Tail(workers)())(), M.EmptyList),
                ),
            )

    def _terminate_parallel_workers(self, workers):
        if M.IdentityCompare(workers, M.EmptyList)() is M.truth_value:
            return
        entry = M.Head(workers)()
        self._kill_parallel_worker_entry(entry)
        self._terminate_parallel_workers(M.Tail(workers)())

    def _terminate_parallel_workers_for_mode(self, mp_context, workers, idle_executors, mode, kept):
        if M.IdentityCompare(workers, M.EmptyList)() is M.truth_value:
            return M.Pair(self._reverse(kept, M.EmptyList), M.Pair(idle_executors, M.EmptyList))
        entry = M.Head(workers)()
        if M.IdentityCompare(self._worker_entry_mode(entry), mode)() is M.truth_value:
            self._kill_parallel_worker_entry(entry)
            return self._terminate_parallel_workers_for_mode(mp_context, M.Tail(workers)(), idle_executors, mode, kept)
        return self._terminate_parallel_workers_for_mode(mp_context, M.Tail(workers)(), idle_executors, mode, M.Pair(entry, kept))

    def _terminate_parallel_workers_not_selected(self, mp_context, workers, idle_executors, selected_modes, kept):
        if M.IdentityCompare(workers, M.EmptyList)() is M.truth_value:
            return M.Pair(self._reverse(kept, M.EmptyList), M.Pair(idle_executors, M.EmptyList))
        entry = M.Head(workers)()
        if self._mode_selected(selected_modes, self._worker_entry_mode(entry)) is M.false_value:
            self._kill_parallel_worker_entry(entry)
            return self._terminate_parallel_workers_not_selected(mp_context, M.Tail(workers)(), idle_executors, selected_modes, kept)
        return self._terminate_parallel_workers_not_selected(mp_context, M.Tail(workers)(), idle_executors, selected_modes, M.Pair(entry, kept))

    def _requeue_worker_entry_for_pause(self, states, entry):
        mode = self._worker_entry_mode(entry)
        packet_state = self._worker_entry_packet_job(entry)
        prior_state = self._comparison_state_for_mode(states, mode)
        next_states = states
        if M.IdentityCompare(prior_state, M.EmptyList)() is M.false_value:
            if M.IdentityCompare(self._comparison_state_status(prior_state), SearchRunningLabel)() is M.truth_value:
                packet_job = self._comparison_packet_job_for_state(prior_state, packet_state)
                requeued_job = self._merge_compare_jobs(mode, self._comparison_state_job(prior_state), packet_job)
                active_packets = self._pred_nat_or_zero_local(self._comparison_state_active_packets(prior_state))
                next_state = self._comparison_state_update(
                    prior_state,
                    job=requeued_job,
                    active_packets=active_packets,
                )
                next_states = self._replace_comparison_state(states, mode, next_state)
                _debug(
                    "search-compare: requeued unfinished packet for "
                    + SearchModeText(mode)()
                    + " pid="
                    + str(self._worker_entry_process(entry).pid)
                )
        return next_states

    def _requeue_worker_entry_for_retry(self, states, entry):
        mode = self._worker_entry_mode(entry)
        packet_descriptor = self._worker_entry_packet_job(entry)
        prior_state = self._comparison_state_for_mode(states, mode)
        if M.IdentityCompare(prior_state, M.EmptyList)() is M.truth_value:
            return states
        if M.IdentityCompare(self._comparison_state_status(prior_state), SearchRunningLabel)() is M.false_value:
            return states

        active_packets = self._pred_nat_or_zero_local(self._comparison_state_active_packets(prior_state))
        pending_packets = M.Pair(packet_descriptor, self._comparison_state_pending_packets(prior_state))
        pending_packets_count = self._succ_nat_local(self._comparison_state_pending_packets_count(prior_state))
        next_state = self._comparison_state_update(
            prior_state,
            active_packets=active_packets,
            pending_packets=pending_packets,
            pending_packets_count=pending_packets_count,
        )
        _debug(
            "search-compare: requeued rejected "
            + SearchModeText(mode)()
            + " packet for resident retry; mode-active-processes="
            + self._nat_text(active_packets)
            + " mode-queued-packets="
            + self._nat_text(pending_packets_count)
        )
        return self._replace_comparison_state(states, mode, next_state)

    def _requeue_parallel_workers_for_pause(self, states, workers):
        if M.IdentityCompare(workers, M.EmptyList)() is M.truth_value:
            return states
        next_states = self._requeue_worker_entry_for_pause(states, M.Head(workers)())
        return self._requeue_parallel_workers_for_pause(next_states, M.Tail(workers)())

    def _signal_parallel_worker_entry(self, entry):
        process = self._worker_entry_process(entry)
        if process.is_alive():
            _debug(
                "search-compare: pause signalling "
                + SearchModeText(self._worker_entry_mode(entry))()
                + " pid="
                + str(process.pid)
            )
            process.terminate()

    def _signal_parallel_workers(self, workers):
        if M.IdentityCompare(workers, M.EmptyList)() is M.truth_value:
            return
        self._signal_parallel_worker_entry(M.Head(workers)())
        self._signal_parallel_workers(M.Tail(workers)())

    def _join_parallel_workers_quick(self, workers, timeout_seconds):
        if M.IdentityCompare(workers, M.EmptyList)() is M.truth_value:
            return
        self._worker_entry_process(M.Head(workers)()).join(timeout_seconds)
        self._join_parallel_workers_quick(M.Tail(workers)(), timeout_seconds)

    def _pause_parallel_workers(self, states, workers):
        worker_count = self._worker_entry_count(workers)
        if M.NatEq(worker_count, M.Zero, self.registry)() is M.truth_value:
            return states
        _debug(
            "search-compare: pause requested; reclaiming "
            + self._nat_text(worker_count)
            + " in-flight branch packets"
        )
        next_states = self._requeue_parallel_workers_for_pause(states, workers)
        _debug(
            "search-compare: pause signalling "
            + self._nat_text(worker_count)
            + " worker processes"
        )
        self._signal_parallel_workers(workers)
        self._join_parallel_workers_quick(workers, 0.0)
        _debug("search-compare: pause requeued packets and signalled worker shutdown")
        return next_states

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
