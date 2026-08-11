from __future__ import annotations

import multiprocessing
import queue
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
from .. import rewrite_strategies as RewriteStrategymod
from ..heuristics import *
from ..labels import *
from ..proof import *
from ..proof import _debug, _debug_term
from .chain_utils import *
from .model import *
from .patricia import *
from .ui import _SearchComparisonPromptGuard, _SearchConsoleInput, _SearchProgressTicker, _SearchStopConsole






class Search(M.Edge):
    def __init__(self, graph, start, goal, ordered_rules, heuristic, registry):
        self.graph = graph
        self.registry = registry
        self.rules = ordered_rules
        self.heuristic = heuristic
        self.start = HeuristicCanonicalize(start, heuristic, registry)()
        self.goal = HeuristicCanonicalize(goal, heuristic, registry)()
        self.search_aborted = M.false_value
        self.search_outcome_on_abort = SearchFailureLabel
        self._active_search_job = None
        self._premise_bindings_cache = M.EmptyList
        self._console_input = self.graph._search_console_input
        if self._console_input is None:
            self._console_input = _SearchConsoleInput()
            self.graph._search_console_input = self._console_input
        self._stop_listener = None
        self._dfs_timeout_seconds = None
        self._dfs_timeout_triggered = M.false_value
        self._init_search_prompt_state()
        self._final_status_text = "stopped"
        self._start_progress_ticker()
        self._start_stop_listener()
        job = M.EmptyList
        try:
            _debug(self.mode_text + ": start received")
            _debug(self.mode_text + ": goal received")
            job = self._resume_or_start_search_job()
            try:
                while M.IdentityCompare(SearchJobStatus(job)(), SearchRunningLabel)() is M.truth_value:
                    job = self._maybe_abort_slow_dfs(job)
                    if M.IdentityCompare(SearchJobStatus(job)(), SearchRunningLabel)() is M.false_value:
                        break
                    job = self._maybe_pause_search_job(job)
                    if M.IdentityCompare(SearchJobStatus(job)(), SearchPausedLabel)() is M.truth_value:
                        self.graph.store_search_job(job)
                        break
                    burst_pair = SearchBurst(self.graph, job, self._burst_budget(), self.registry, self._stop_listener, self)()
                    job = M.Head(burst_pair)()
                    self.registry = M.Head(M.Tail(burst_pair)())()
                    self.graph._replace_context(constructors=self.registry)
                    job = self._maybe_abort_slow_dfs(job)
                    if M.IdentityCompare(SearchJobStatus(job)(), SearchPausedLabel)() is M.truth_value:
                        self.graph.store_search_job(job)
                        break
                    if M.IdentityCompare(SearchJobStatus(job)(), SearchFailureLabel)() is M.truth_value:
                        comparison_guard = self._comparison_prompt_guard()
                        if comparison_guard is not None and comparison_guard.comparison_aborted is M.truth_value:
                            self.search_aborted = M.truth_value
                            self.search_outcome_on_abort = SearchFailureLabel
                    if M.IdentityCompare(SearchJobStatus(job)(), SearchRunningLabel)() is M.truth_value:
                        self._active_search_job = job
                        self._maybe_prompt_to_continue()
                        if self.search_aborted is M.truth_value:
                            if M.IdentityCompare(self.search_outcome_on_abort, SearchPausedLabel)() is M.truth_value:
                                _debug(self.mode_text + ": stop requested; pausing current mode")
                                job = self._search_job_with_status(job, SearchPausedLabel)
                                self.graph.store_search_job(job)
                            else:
                                _debug(self.mode_text + ": comparison guard aborted current mode")
                                job = self._search_job_with_status(job, SearchFailureLabel)
                            break
                        job = self._maybe_pause_search_job(job)
                        if M.IdentityCompare(SearchJobStatus(job)(), SearchPausedLabel)() is M.truth_value:
                            self.graph.store_search_job(job)
                            break
            except KeyboardInterrupt:
                if M.Compare(job, M.EmptyList)() is M.truth_value:
                    raise
                _debug(self.mode_text + ": keyboard interrupt; pausing current search")
                job = self._search_job_with_status(job, SearchPausedLabel)
                self.graph.store_search_job(job)

            outcome = SearchJobStatus(job)()
            self._active_search_job = job
            self._final_status_text = self._completion_status_text(outcome)
            if M.IdentityCompare(outcome, SearchPausedLabel)() is M.false_value:
                self.graph.remove_search_job(self.start, self.goal, self.heuristic)
                self._commit_completed_search_cost()
            plan = SearchJobResultPlan(job)()
            if M.IdentityCompare(outcome, SearchSuccessLabel)() is M.false_value:
                plan = M.EmptyList
            cost_pair = BuildSearchCost(
                plan,
                SearchJobExpanded(job)(),
                SearchJobGenerated(job)(),
                SearchJobFrontierPeak(job)(),
                outcome,
                self.registry,
            )()
            search_cost = M.Head(cost_pair)()
            self.registry = M.Head(M.Tail(cost_pair)())()
            self.graph._replace_context(constructors=self.registry)
            self.result = M.Pair(plan, M.Pair(search_cost, M.EmptyList))
            _debug(self.mode_text + ": " + self._final_status_text)
            super().__init__(inputs=M.Pair(graph, M.Pair(start, M.Pair(goal, M.Pair(ordered_rules, M.Pair(heuristic, M.Pair(registry, M.EmptyList)))))), results=self.result)
        finally:
            self._active_search_job = None
            self._stop_stop_listener()
            self._stop_progress_ticker()

    def _start_progress_ticker(self):
        self.mode_text = SearchModeText(HeuristicSearchMode(self.heuristic)())()
        if M.IdentityCompare(self.graph._search_disable_progress_ticker, M.truth_value)() is M.truth_value:
            self._progress_ticker = None
            return
        self._progress_ticker = _SearchProgressTicker(self.mode_text, self)
        self._progress_ticker.start()

    def _stop_progress_ticker(self):
        if self._progress_ticker is None:
            return
        elapsed = self._progress_ticker.stop()
        if self._final_status_text == "done":
            _debug(self.mode_text + ": done in " + str(elapsed) + " seconds")
            return
        _debug(self.mode_text + ": " + self._final_status_text + " after " + str(elapsed) + " seconds")

    def _start_stop_listener(self):
        if M.IdentityCompare(self.graph._search_disable_console, M.truth_value)() is M.truth_value:
            self._stop_listener = None
            return
        self._stop_listener = _SearchStopConsole(self._console_input)
        if M.IdentityCompare(self._stop_listener.start(), M.truth_value)() is M.false_value:
            self._stop_listener = None
            _debug("search: console stop control unavailable in this environment")
            return
        if M.IdentityCompare(self.graph._search_stop_help_shown, M.truth_value)() is M.false_value:
            print("Type 'pause' (or 'stop') and press Enter in the console to pause and save the current search.")
            self.graph._search_stop_help_shown = M.truth_value
        _debug("search: console stop control ready")

    def _stop_stop_listener(self):
        if self._stop_listener is None:
            return
        self._stop_listener.stop()
        self._stop_listener = None

    def _pause_progress_ticker(self):
        if self._progress_ticker is None:
            return
        self._progress_ticker.pause()

    def _resume_progress_ticker(self):
        if self._progress_ticker is None:
            return
        self._progress_ticker.resume()

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

    def _reverse(self, chain, acc):
        remaining = chain
        reversed_chain = acc
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            reversed_chain = M.Pair(M.Head(remaining)(), reversed_chain)
            remaining = M.Tail(remaining)()
        return reversed_chain

    def _frontier_focus_text(self, job):
        frontier = SearchJobFrontier(job)()
        if M.IdentityCompare(frontier, M.EmptyList)() is M.truth_value:
            return "empty"
        current = SearchStateCurrent(M.Head(frontier)())()
        return _debug_term(current, self.registry)

    def _plan_prefix_text(self, plan_rev):
        if M.IdentityCompare(plan_rev, M.EmptyList)() is M.truth_value:
            return "[]"
        return PrettyPlanChain(self._reverse(plan_rev, M.EmptyList), self.registry)()

    def _state_prefix_text(self, state):
        return self._plan_prefix_text(SearchStatePlan(state)())

    def _frontier_prefix_text(self, job):
        frontier = SearchJobFrontier(job)()
        if M.IdentityCompare(frontier, M.EmptyList)() is M.truth_value:
            return "[]"
        return self._state_prefix_text(M.Head(frontier)())

    def _state_progress_text(self, state):
        return (
            "current="
            + _debug_term(SearchStateCurrent(state)(), self.registry)
            + " prefix="
            + self._state_prefix_text(state)
        )

    def _state_transition_text(self, state, action, next_term):
        next_plan_rev = M.Pair(action, SearchStatePlan(state)())
        return (
            "current="
            + _debug_term(SearchStateCurrent(state)(), self.registry)
            + " prefix="
            + self._state_prefix_text(state)
            + " action="
            + PrettyAction(action, self.registry)()
            + " next="
            + _debug_term(next_term, self.registry)
            + " next-prefix="
            + self._plan_prefix_text(next_plan_rev)
        )

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
        )

    def _ticker_progress_text(self):
        if self._progress_ticker is None:
            return self.mode_text
        job = self._active_search_job
        if job is None:
            return self.mode_text + ": " + str(self._progress_ticker._elapsed_seconds()) + "s elapsed"
        return (
            self.mode_text
            + ": "
            + str(self._progress_ticker._elapsed_seconds())
            + "s elapsed; "
            + self._job_progress_text(job)
        )

    def _pause_stop_listener(self):
        if self._stop_listener is None:
            return
        self._stop_listener.pause()

    def _resume_stop_listener(self):
        if self._stop_listener is None:
            return
        self._stop_listener.resume()

    def _comparison_prompt_guard(self):
        return self.graph._search_comparison_prompt_guard

    def _read_console_line(self, prompt_text):
        return self._console_input.read_prompt(prompt_text)

    def _timeout_requested(self):
        if self._progress_ticker is None:
            return M.false_value
        timeout_seconds = self.graph._search_worker_timeout_seconds
        if timeout_seconds is None:
            if self._mode_is_plain_dfs() is M.false_value:
                return M.false_value
            timeout_seconds = self._dfs_timeout_seconds
        if timeout_seconds is None:
            return M.false_value
        if self._progress_ticker._elapsed_seconds() <= timeout_seconds:
            return M.false_value
        if self._dfs_timeout_triggered is M.false_value:
            _debug(self.mode_text + ": timeout requested")
            self._pause_progress_ticker()
            self._pause_stop_listener()
            self._dfs_timeout_triggered = M.truth_value
        return M.truth_value

    def _mode_is_plain_dfs(self):
        mode = HeuristicSearchMode(self.heuristic)()
        return M.IdentityCompare(mode, DFSLabel)()

    def _burst_budget(self):
        mode = HeuristicSearchMode(self.heuristic)()
        budget = M.five
        if M.OrAtom(M.IdentityCompare(mode, DFSLabel)(), M.IdentityCompare(mode, RewriteDFSLabel)())() is M.truth_value:
            budget = M.nine
        return budget

    def _maybe_abort_slow_dfs(self, job):
        if self._timeout_requested() is M.false_value:
            return job
        self.search_aborted = M.truth_value
        self.search_outcome_on_abort = SearchTimedOutLabel
        return self._search_job_with_status(job, SearchTimedOutLabel)

    def _completion_status_text(self, outcome):
        if self.search_aborted is M.truth_value:
            if M.IdentityCompare(self.search_outcome_on_abort, SearchPausedLabel)() is M.truth_value:
                return "paused"
            if M.IdentityCompare(self.search_outcome_on_abort, SearchTimedOutLabel)() is M.truth_value:
                return "timed_out"
            return "aborted"
        if M.IdentityCompare(outcome, SearchPausedLabel)() is M.truth_value:
            return "paused"
        if M.IdentityCompare(outcome, SearchTimedOutLabel)() is M.truth_value:
            return "timed_out"
        if M.IdentityCompare(outcome, SearchFailureLabel)() is M.truth_value:
            return "failed"
        return "done"

    def _search_job_with_status(self, job, status):
        return SearchJob(
            SearchJobStart(job)(),
            SearchJobGoal(job)(),
            SearchJobRules(job)(),
            SearchJobHeuristic(job)(),
            status,
            SearchJobFrontier(job)(),
            SearchJobExpanded(job)(),
            SearchJobGenerated(job)(),
            SearchJobFrontierPeak(job)(),
            SearchJobResultPlan(job)(),
            SearchJobVisited(job)(),
            SearchJobTheoremRuleCache(job)(),
            SearchJobRewriteRules(job)(),
            SearchJobFrontierSize(job)(),
        )()

    def _search_mode_uses_global_visited(self):
        mode = HeuristicSearchMode(self.heuristic)()
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

    def _tree_insert_fact(self, tree, key, fact):
        return SearchPatriciaInsertByKey(tree, key, fact, self.registry)()

    def _tree_insert(self, tree, key):
        return self._tree_insert_fact(tree, key, M.Pair(key, M.EmptyList))

    def _tree_insert_term(self, tree, term):
        return self._tree_insert(tree, term)

    def _initial_search_job_visited(self):
        if self._search_mode_uses_global_visited() is M.false_value:
            return M.EmptyList
        return self._tree_insert_term(M.EmptyList, self.start)

    def _fresh_search_job(self):
        steps_remaining = M.EmptyList
        start_state = SearchState(self.start, M.EmptyList, M.EmptyList, steps_remaining)()
        frontier = M.Pair(start_state, M.EmptyList)
        visited = self._initial_search_job_visited()
        return SearchJob(
            self.start,
            self.goal,
            self.rules,
            self.heuristic,
            SearchRunningLabel,
            frontier,
            M.Zero,
            M.Zero,
            M.Zero,
            M.EmptyList,
            visited,
            M.EmptyList,
            M.EmptyList,
            M.one,
        )()

    def _resume_or_start_search_job(self):
        existing = self.graph.lookup_search_job(self.start, self.goal, self.heuristic)
        if M.Compare(existing, M.EmptyList)() is M.truth_value:
            return self._fresh_search_job()
        _debug(self.mode_text + ": resuming paused search job")
        return self._search_job_with_status(existing, SearchRunningLabel)

    def _maybe_pause_search_job(self, job):
        if self._stop_listener is None:
            return job
        if M.IdentityCompare(self._stop_listener.requested(), M.truth_value)() is M.false_value:
            return job
        self.search_aborted = M.truth_value
        self.search_outcome_on_abort = SearchPausedLabel
        _debug(self.mode_text + ": pausing search job")
        return self._search_job_with_status(job, SearchPausedLabel)

    def _reverse(self, L, acc):
        if M.IdentityCompare(L, M.EmptyList)() is M.truth_value:
            return acc
        return self._reverse(M.Tail(L)(), M.Pair(M.Head(L)(), acc))

    def _nat_units(self, value):
        try:
            return int(M.PrettyTerm(value, self.registry)())
        except Exception:
            return 0

    def _search_job_total_cost_units(self, job):
        expanded_units = self._nat_units(SearchJobExpanded(job)())
        generated_units = self._nat_units(SearchJobGenerated(job)())
        frontier_peak_units = self._nat_units(SearchJobFrontierPeak(job)())
        return expanded_units + generated_units + frontier_peak_units

    def _init_search_prompt_state(self):
        self.search_started_at = time.time()
        self.cost_prompt_step = M.Atom()
        self.cost_prompt_step.value = Gmpmod.GMPRep("100")
        self.next_cost_prompt = self.cost_prompt_step
        self.prompt_expanded = M.Zero
        self.prompt_generated = M.Zero
        self.prompt_total_cost = M.Zero
        self.prompt_frontier_peak = M.Zero
        self.prompt_expanded_units = 0
        self.prompt_generated_units = 0
        self.prompt_total_cost_units = 0
        self.search_aborted = M.false_value
        self.search_outcome_on_abort = SearchFailureLabel

    def _init_search_order_state(self, goal, theorem_rule_cache=None, rewrite_rules=None):
        self.rule_order_mode = HeuristicRuleOrder(self.heuristic)()
        self._theorem_rule_cache = theorem_rule_cache
        self._theorem_applicable_rule_cache = M.EmptyList
        # Premise-join cache, plus the knowledge state it was computed
        # against. Shared by every construction path, including kernels
        # that bypass the Search constructor.
        self._premise_bindings_cache = M.EmptyList
        self._premise_bindings_cache_state_key = M.EmptyList
        self._premise_bindings_cache_delta = M.EmptyList
        self._rewrite_rules = rewrite_rules
        self._rewrite_rules_goal = goal
        self._rewrite_strategy = RewriteStrategymod.GoalDemandRewriteStrategy()()
        self._goal_head_index = M.EmptyList
        self._goal_head_index_ready = M.false_value

    def _canonical_term(self, term):
        # Keep canonicalization inside the hypergraph kernel.
        return HeuristicCanonicalize(term, self.heuristic, self.registry)()

    def _goal_head_allows(self, subterm):
        if self._goal_head_index_ready is M.false_value:
            self._goal_head_index = HeuristicGoalHeadNeighborhood(self._rewrite_rules_goal, self.rules, self.registry)()
            self._goal_head_index_ready = M.truth_value
        return RewriteStrategymod.RewriteStrategyAllowsSubterm(
            self._rewrite_strategy,
            self._goal_head_index,
            subterm,
            self.registry,
        )()

    def _rewrite_rule_bundle(self, rules, index_tree, wildcards):
        return SearchRewriteRuleBundle(rules, index_tree, wildcards)()

    def _rewrite_rule_bundle_rules(self, bundle):
        return SearchRewriteRuleBundleRules(bundle)()

    def _rewrite_rule_bundle_index(self, bundle):
        return SearchRewriteRuleBundleIndex(bundle)()

    def _rewrite_rule_bundle_wildcards(self, bundle):
        return SearchRewriteRuleBundleWildcards(bundle)()

    def _is_rewrite_rule_bundle(self, value):
        if M.IsPair(value)() is M.false_value:
            return M.false_value
        return M.IdentityCompare(M.Head(value)(), SearchRewriteRuleBundleLabel)()

    def _build_rewrite_rule_bundle_walk(self, rules, index_tree, wildcards):
        if M.IdentityCompare(rules, M.EmptyList)() is M.truth_value:
            return self._rewrite_rule_bundle(M.EmptyList, index_tree, wildcards)
        rule = M.Head(rules)()
        rest = M.Tail(rules)()
        tail_bundle = self._build_rewrite_rule_bundle_walk(rest, index_tree, wildcards)
        tail_rules = self._rewrite_rule_bundle_rules(tail_bundle)
        tail_index = self._rewrite_rule_bundle_index(tail_bundle)
        tail_wildcards = self._rewrite_rule_bundle_wildcards(tail_bundle)
        pattern = RulePattern(rule)()
        if IsVarPattern(pattern)() is M.truth_value:
            return self._rewrite_rule_bundle(M.Pair(rule, tail_rules), tail_index, M.Pair(rule, tail_wildcards))
        rule_head = TermHead(pattern, self.registry)()
        if M.IdentityCompare(rule_head, M.EmptyList)() is M.truth_value:
            return self._rewrite_rule_bundle(M.Pair(rule, tail_rules), tail_index, M.Pair(rule, tail_wildcards))
        existing = M.TreeLookup(tail_index, rule_head, self.registry)()
        if M.IdentityCompare(existing, M.EmptyList)() is M.truth_value:
            existing = M.EmptyList
        next_index = self._tree_insert_fact(tail_index, rule_head, M.Pair(rule, existing))
        return self._rewrite_rule_bundle(M.Pair(rule, tail_rules), next_index, tail_wildcards)

    def _build_rewrite_rule_bundle(self, rules):
        return self._build_rewrite_rule_bundle_walk(rules, M.Tree(M.EmptyList), M.EmptyList)

    def _ensure_rewrite_rule_bundle(self, goal):
        if M.IdentityCompare(self._rewrite_rules, M.EmptyList)() is M.truth_value:
            if M.IdentityCompare(self.rule_order_mode, GoalHeadOrderLabel)() is M.truth_value:
                self._rewrite_rules = self._build_rewrite_rule_bundle(GoalHeadRewriteOrderer(self.rules, goal, self.registry)())
            else:
                self._rewrite_rules = self._build_rewrite_rule_bundle(self.rules)
            return self._rewrite_rules
        if self._is_rewrite_rule_bundle(self._rewrite_rules) is M.truth_value:
            return self._rewrite_rules
        self._rewrite_rules = self._build_rewrite_rule_bundle(self._rewrite_rules)
        return self._rewrite_rules

    def _ensure_rewrite_rules(self, goal):
        return self._rewrite_rule_bundle_rules(self._ensure_rewrite_rule_bundle(goal))

    def _rewrite_candidate_rules(self, subterm):
        bundle = self._ensure_rewrite_rule_bundle(self._rewrite_rules_goal)
        specific = M.EmptyList
        subterm_head = TermHead(subterm, self.registry)()
        if M.IdentityCompare(subterm_head, M.EmptyList)() is M.false_value:
            looked_up = M.TreeLookup(self._rewrite_rule_bundle_index(bundle), subterm_head, self.registry)()
            if M.IdentityCompare(looked_up, M.EmptyList)() is M.false_value:
                specific = looked_up
        # Goal-directed rewrite candidate selection:
        # - Skip non-goal heads entirely (fast pruning).
        # - Do not attach wildcard rules here; they are throttled to root only.
        if self._goal_head_allows(subterm) is M.false_value:
            return M.EmptyList
        return self._reverse(specific, M.EmptyList)

    def _rewrite_root_wildcards(self):
        bundle = self._ensure_rewrite_rule_bundle(self._rewrite_rules_goal)
        return self._reverse(self._rewrite_rule_bundle_wildcards(bundle), M.EmptyList)

    def _rewrite_frame(self, subterm, path):
        rules = self._rewrite_candidate_rules(subterm)
        # Wildcards are only allowed at the root, and only when specific-head rules
        # are absent there.
        at_root = M.IdentityCompare(path, M.EmptyList)()
        no_rules = M.IdentityCompare(rules, M.EmptyList)()
        if M.AndAtom(at_root, no_rules)() is M.truth_value:
            rules = self._rewrite_root_wildcards()
        return SearchRewritePathFrame(subterm, path, rules, M.false_value)()

    def _stage_debug_label(self):
        mode = HeuristicSearchMode(self.heuristic)()
        if M.IdentityCompare(mode, DFSLabel)() is M.truth_value:
            return "search-dfs-stage"
        if M.IdentityCompare(mode, BFSLabel)() is M.truth_value:
            return "search-bfs-stage"
        if M.IdentityCompare(mode, BeamLabel)() is M.truth_value:
            return "search-beam-stage"
        if M.IdentityCompare(mode, AStarLabel)() is M.truth_value:
            return "search-astar-stage"
        if M.IdentityCompare(mode, RewriteDFSLabel)() is M.truth_value:
            return "search-rewrite-dfs-stage"
        return "search-stage"

    def _stage_debug(self, text):
        _debug(self._stage_debug_label() + ": " + text)

    def _state_key(self, term):
        return SearchStructuralKey(self._canonical_term(term), self.registry)()

    def _goal_key(self):
        return self._state_key(self.goal)

    def _memo_key(self, current, goal, steps_remaining):
        steps_rep = M.NatRepOf(steps_remaining, self.registry)()
        steps_key = steps_remaining
        if M.IdentityCompare(steps_rep, M.EmptyList)() is M.false_value:
            steps_key = Gmpmod.GMPRepDigitList(steps_rep)()
        return SearchMemoKey(self._state_key(current), self._state_key(goal), steps_key)()

    def _lookup_search_memo(self, current, goal, steps_remaining):
        return self.graph.lookup_search_memo(self._memo_key(current, goal, steps_remaining))

    def _store_search_memo(self, current, goal, steps_remaining, status, plan):
        if M.OrAtom(ContainsVar(current)(), ContainsVar(goal)())() is M.truth_value:
            return M.EmptyList
        entry = SearchMemoEntry(status, plan)()
        self.graph.store_search_memo(self._memo_key(current, goal, steps_remaining), entry)
        return entry

    def _rule_head_key(self, rule):
        pattern = RulePattern(rule)()
        if IsVarPattern(pattern)() is M.truth_value:
            return M.EmptyList
        return TermHead(pattern, self.registry)()

    def _rewrite_rule_may_match_subterm(self, rule, subterm):
        pattern = RulePattern(rule)()
        if IsVarPattern(pattern)() is M.truth_value:
            return M.truth_value
        rule_head = self._rule_head_key(rule)
        subterm_head = TermHead(subterm, self.registry)()
        if M.IdentityCompare(rule_head, M.EmptyList)() is M.truth_value:
            if M.IdentityCompare(subterm_head, M.EmptyList)() is M.truth_value:
                return M.truth_value
            return M.false_value
        if M.IdentityCompare(subterm_head, M.EmptyList)() is M.truth_value:
            return M.false_value
        return M.IdentityCompare(rule_head, subterm_head)()

    def _theorem_rule_cache_key(self, current, goal):
        return self._state_key(current)

    def _theorem_applicable_rule_cache_key(self, current):
        if IsKnowledge(current)() is M.truth_value:
            return self._state_key(current)
        if M.IsPair(current)() is M.truth_value:
            return M.Head(current)()
        return current

    def _theorem_applicable_rules_sharded(self, current, knowledge_head_index, knowledge_exact_trie):
        from .runtime import _SearchApplicableRulesShardWorker

        if multiprocessing.get_start_method() == "spawn":
            self._stage_debug("applicability multiprocessing disabled on spawn")
            return FilterApplicableRulesWithIndex(self.rules, current, knowledge_head_index, self.registry, knowledge_exact_trie)()

        try:
            mp_context = multiprocessing.get_context("fork")
        except ValueError:
            mp_context = multiprocessing.get_context("spawn")
        if mp_context.get_start_method() == "spawn":
            self._stage_debug("applicability multiprocessing disabled on spawn")
            return FilterApplicableRulesWithIndex(self.rules, current, knowledge_head_index, self.registry, knowledge_exact_trie)()

        rule_count = 0
        remaining_rules = self.rules
        while M.IdentityCompare(remaining_rules, M.EmptyList)() is M.false_value:
            rule_count = rule_count + 1
            remaining_rules = M.Tail(remaining_rules)()
        worker_capacity = multiprocessing.cpu_count()
        if worker_capacity < 1:
            worker_capacity = 1
        if rule_count < worker_capacity:
            worker_capacity = rule_count
        if worker_capacity < 2:
            return FilterApplicableRulesWithIndex(self.rules, current, knowledge_head_index, self.registry, knowledge_exact_trie)()

        shard_width_count = rule_count // worker_capacity
        wide_shard_count = rule_count % worker_capacity
        self._stage_debug(
            "applicability multiprocessing start-method="
            + mp_context.get_start_method()
            + " workers="
            + str(worker_capacity)
            + " rules="
            + str(rule_count)
            + " rules-per-worker="
            + str(shard_width_count)
            + "-"
            + str(shard_width_count + 1)
        )

        remaining_rules = self.rules
        slot = 0
        workers = ()
        try:
            while M.IdentityCompare(remaining_rules, M.EmptyList)() is M.false_value:
                active_shard_width_count = shard_width_count
                if slot < wide_shard_count:
                    active_shard_width_count = active_shard_width_count + 1
                active_shard_width = M.Atom()
                active_shard_width.value = Gmpmod.GMPRep(str(active_shard_width_count))
                shard_rules = SearchChainTake(remaining_rules, active_shard_width)()
                remaining_rules = SearchChainDrop(remaining_rules, active_shard_width)()
                result_queue = mp_context.Queue()
                process = mp_context.Process(
                    target=_SearchApplicableRulesShardWorker,
                    args=(slot, shard_rules, current, knowledge_head_index, knowledge_exact_trie, self.registry, result_queue),
                )
                process.start()
                self._stage_debug(
                    "applicability worker start slot="
                    + str(slot)
                    + " pid="
                    + str(process.pid)
                    + " rules="
                    + str(active_shard_width_count)
                )
                workers = workers + ((slot, shard_rules, process, result_queue),)
                slot = slot + 1

            shard_results = M.EmptyList
            worker_index = len(workers)
            while worker_index != 0:
                worker_index = worker_index - 1
                worker = workers[worker_index]
                shard_rules = worker[1]
                process = worker[2]
                result_queue = worker[3]
                process.join()
                if process.exitcode != 0:
                    raise RuntimeError("search theorem applicability worker exited with code " + str(process.exitcode))
                try:
                        shard_payload = result_queue.get(timeout=1.0)
                except queue.Empty:
                    raise RuntimeError("search theorem applicability worker produced no result")
                result_queue.close()
                result_queue.join_thread()
                shard_positions = shard_payload[1]
                worker_pid = shard_payload[2]
                worker_elapsed = shard_payload[3]
                self._stage_debug(
                    "applicability worker done slot="
                    + str(worker[0])
                    + " pid="
                    + str(worker_pid)
                    + " elapsed="
                    + "{:.3f}".format(worker_elapsed)
                    + "s exit="
                    + str(process.exitcode)
                )
                if shard_positions is None:
                    raise RuntimeError("search theorem applicability shard failed")
                shard_results = M.Pair(self._select_shard_rules(shard_rules, shard_positions), shard_results)
            self._stage_debug("applicability multiprocessing done workers=" + str(len(workers)))
            return SearchChainAppendMany(shard_results)()
        except Exception:
            worker_index = len(workers)
            while worker_index != 0:
                worker_index = worker_index - 1
                worker = workers[worker_index]
                process = worker[2]
                result_queue = worker[3]
                if process.exitcode is None:
                    process.terminate()
                process.join()
                try:
                    result_queue.close()
                    result_queue.join_thread()
                except Exception:
                    pass
            raise

    def _select_shard_rules(self, shard_rules, shard_positions):
        selected_rev = M.EmptyList
        shard_cursor = shard_rules
        position_index = 0
        shard_index = 0
        while M.IdentityCompare(shard_cursor, M.EmptyList)() is M.false_value:
            if position_index != len(shard_positions):
                if shard_index == shard_positions[position_index]:
                    selected_rev = M.Pair(M.Head(shard_cursor)(), selected_rev)
                    position_index = position_index + 1
            shard_cursor = M.Tail(shard_cursor)()
            shard_index = shard_index + 1
        return self._reverse(selected_rev, M.EmptyList)

    def _theorem_indexes_for(self, current):
        knowledge_head_index = M.EmptyList
        knowledge_exact_trie = M.EmptyList
        if IsKnowledge(current)() is M.truth_value:
            facts = KnowledgeFacts(current)()
            knowledge_head_index = K.KnowledgeHeadIndexInsertChain(M.EmptyTree, facts, self.registry)()
            knowledge_exact_trie = K.KnowledgeTrieInsertChain(M.EmptyTree, facts, self.registry)()
        return M.Pair(knowledge_head_index, M.Pair(knowledge_exact_trie, M.EmptyList))

    def _theorem_applicable_rules_for(self, current, knowledge_head_index=None, knowledge_exact_trie=None):
        started_at = time.time()
        self._stage_debug("applicable theorem rules start")
        cache_key = self._theorem_applicable_rule_cache_key(current)
        cache_disabled = M.IdentityCompare(self.graph._search_probe_disable_applicable_cache, M.truth_value)()
        if cache_disabled is M.false_value:
            if M.IdentityCompare(self._theorem_applicable_rule_cache, M.EmptyList)() is M.false_value:
                if M.TermEqual(M.Head(self._theorem_applicable_rule_cache)(), cache_key)() is M.truth_value:
                    self._stage_debug("applicable theorem rules served from cache")
                    return M.Head(M.Tail(self._theorem_applicable_rule_cache)())()
        if knowledge_head_index is None or knowledge_exact_trie is None:
            indexes = self._theorem_indexes_for(current)
            knowledge_head_index = M.Head(indexes)()
            knowledge_exact_trie = M.Head(M.Tail(indexes)())()
        after_indexes = time.time()
        self._stage_debug(
            "applicable theorem rules after indexes in "
            + "{:.3f}".format(after_indexes - started_at)
            + "s"
        )
        shard_disabled = M.IdentityCompare(self.graph._search_probe_disable_applicable_shards, M.truth_value)()
        if shard_disabled is M.truth_value:
            applicable = FilterApplicableRulesWithIndex(
                self.rules,
                current,
                knowledge_head_index,
                self.registry,
                knowledge_exact_trie,
            )()
        else:
            applicable = self._theorem_applicable_rules_sharded(current, knowledge_head_index, knowledge_exact_trie)
        after_filter = time.time()
        self._stage_debug(
            "applicable theorem rules after filtering in "
            + "{:.3f}".format(after_filter - after_indexes)
            + "s"
        )
        if cache_disabled is M.false_value:
            self._theorem_applicable_rule_cache = M.Pair(cache_key, M.Pair(applicable, M.EmptyList))
        self._stage_debug("applicable theorem rules ready")
        return applicable

    def _theorem_rules_for(self, current, goal):
        started_at = time.time()
        indexes = self._theorem_indexes_for(current)
        knowledge_head_index = M.Head(indexes)()
        knowledge_exact_trie = M.Head(M.Tail(indexes)())()
        after_indexes = time.time()
        self._stage_debug(
            "theorem rule order after indexes in "
            + "{:.3f}".format(after_indexes - started_at)
            + "s"
        )
        applicable_rules = self._theorem_applicable_rules_for(current, knowledge_head_index, knowledge_exact_trie)
        after_applicable = time.time()
        self._stage_debug(
            "theorem rule order after applicable in "
            + "{:.3f}".format(after_applicable - after_indexes)
            + "s"
        )
        if M.IdentityCompare(self.rule_order_mode, GoalHeadOrderLabel)() is M.truth_value:
            self._stage_debug("ordering theorem rules")
            ordered = GoalHeadRuleOrdererWithIndex(applicable_rules, current, goal, knowledge_head_index, knowledge_exact_trie, self.registry)()
        else:
            ordered = applicable_rules
        after_orderer = time.time()
        self._stage_debug(
            "theorem rule order after orderer in "
            + "{:.3f}".format(after_orderer - after_applicable)
            + "s total="
            + "{:.3f}".format(after_orderer - started_at)
            + "s"
        )
        return ordered

    def _theorem_cursor_for(self, current, goal, knowledge_head_index=None, knowledge_exact_trie=None, delta=None, actions_rev=None):
        started_at = time.time()
        facts = M.EmptyList
        if IsKnowledge(current)() is M.truth_value:
            facts = KnowledgeFacts(current)()
        fact_count_text = M.GMPRepText(M.CountRep(facts)())()
        rule_count_text = M.GMPRepText(M.CountRep(self.rules)())()
        self._stage_debug(
            "cursor build: root facts ready; facts="
            + fact_count_text
            + " rules="
            + rule_count_text
        )
        if knowledge_head_index is None or knowledge_exact_trie is None:
            head_started_at = time.time()
            self._stage_debug("cursor build: head index build start; facts=" + fact_count_text)
            knowledge_head_index = K.KnowledgeHeadIndexInsertChain(M.EmptyTree, facts, self.registry)()
            after_head_index = time.time()
            self._stage_debug(
                "cursor build: head index build complete; elapsed="
                + "{:.3f}".format(after_head_index - head_started_at)
                + "s facts="
                + fact_count_text
            )
            knowledge_exact_trie = K.KnowledgeTrieInsertChain(M.EmptyTree, facts, self.registry)()
            after_exact_trie = time.time()
            self._stage_debug(
                "cursor build: exact trie built; elapsed="
                + "{:.3f}".format(after_exact_trie - head_started_at)
                + "s facts=" + fact_count_text
            )
        else:
            after_exact_trie = time.time()
            self._stage_debug("cursor build: reusing supplied knowledge indexes; facts=" + fact_count_text)
        if delta is None:
            delta = facts
            self._stage_debug(
                "cursor build: initial delta reuses root facts; trie reconstruction=no facts="
                + fact_count_text
            )
        else:
            self._stage_debug(
                "cursor build: supplied delta retained; trie reconstruction=no facts="
                + M.GMPRepText(M.CountRep(delta)())()
            )
        if actions_rev is None:
            actions_rev = M.EmptyList
        after_indexes = time.time()
        self._stage_debug(
            "cursor build: knowledge indexes complete; elapsed="
            + "{:.3f}".format(after_indexes - started_at)
            + "s facts="
            + fact_count_text
            + " rules="
            + rule_count_text
        )
        shard_disabled = M.IdentityCompare(self.graph._search_probe_disable_applicable_shards, M.truth_value)()
        if shard_disabled is M.truth_value:
            applicable_rules = FilterApplicableRulesWithIndex(
                self.rules,
                current,
                knowledge_head_index,
                self.registry,
                knowledge_exact_trie,
            )()
        else:
            applicable_rules = self._theorem_applicable_rules_sharded(current, knowledge_head_index, knowledge_exact_trie)
        after_applicable = time.time()
        self._stage_debug(
            "cursor build: applicability scan complete; elapsed="
            + "{:.3f}".format(after_applicable - after_indexes)
            + "s applicable-rules="
            + M.GMPRepText(M.CountRep(applicable_rules)())()
        )
        if M.IdentityCompare(self.rule_order_mode, GoalHeadOrderLabel)() is M.truth_value:
            ordered_rules = GoalHeadRuleOrdererWithIndex(applicable_rules, current, goal, knowledge_head_index, knowledge_exact_trie, self.registry)()
        else:
            ordered_rules = applicable_rules
        after_order = time.time()
        self._stage_debug(
            "cursor build: rule ordering complete; elapsed="
            + "{:.3f}".format(after_order - after_applicable)
            + "s queued-rules="
            + M.GMPRepText(M.CountRep(ordered_rules)())()
        )
        cursor = SearchTheoremCursor(
            ordered_rules,
            M.EmptyList,
            knowledge_head_index,
            knowledge_exact_trie,
            delta,
            M.EmptyList,
            actions_rev,
            current,
        )()
        after_cursor = time.time()
        self._stage_debug(
            "cursor build: ready; assembly-elapsed="
            + "{:.3f}".format(after_cursor - after_order)
            + "s total-elapsed="
            + "{:.3f}".format(after_cursor - started_at)
            + "s"
        )
        return cursor

    def _rewrite_rules_for(self, goal):
        return self._ensure_rewrite_rules(goal)

    def _nat_add(self, left, right):
        pair = M.Add(left, right, self.registry)()
        self.registry = M.Head(M.Tail(pair)())()
        return M.Head(pair)()

    def _nat_max(self, left, right):
        if M.NatLess(left, right, self.registry)() is M.truth_value:
            return right
        return left

    def _current_peak(self, depth):
        pair = M.Succ(depth, self.registry)()
        self.registry = M.Head(M.Tail(pair)())()
        return M.Head(pair)()

    def _succ_nat(self, value):
        pair = M.Succ(value, self.registry)()
        self.registry = M.Head(M.Tail(pair)())()
        return M.Head(pair)()

    def _nat_add_increment(self, total, increment):
        pair = M.Add(increment, total, self.registry)()
        self.registry = M.Head(M.Tail(pair)())()
        return M.Head(pair)()

    def _record_prompt_expansion(self):
        if M.IdentityCompare(self.graph._search_disable_progress_ticker, M.truth_value)() is M.truth_value:
            return
        self.prompt_expanded = self._succ_nat(self.prompt_expanded)
        self.prompt_total_cost = self._succ_nat(self.prompt_total_cost)
        self.prompt_expanded_units += 1
        self.prompt_total_cost_units += 1

    def _record_prompt_generated_one(self):
        if M.IdentityCompare(self.graph._search_disable_progress_ticker, M.truth_value)() is M.truth_value:
            return
        self.prompt_generated = self._succ_nat(self.prompt_generated)
        self.prompt_total_cost = self._succ_nat(self.prompt_total_cost)
        self.prompt_generated_units += 1
        self.prompt_total_cost_units += 1

    def _record_prompt_generated_count(self, count):
        if M.IdentityCompare(self.graph._search_disable_progress_ticker, M.truth_value)() is M.truth_value:
            return
        self.prompt_generated = self._nat_add_increment(self.prompt_generated, count)
        self.prompt_total_cost = self._nat_add_increment(self.prompt_total_cost, count)
        count_units = int(M.PrettyTerm(count, self.registry)())
        self.prompt_generated_units += count_units
        self.prompt_total_cost_units += count_units

    def _search_result(self, plan, expanded, generated, frontier_peak):
        return M.Pair(plan, M.Pair(expanded, M.Pair(generated, M.Pair(frontier_peak, M.EmptyList))))

    def _search_result_plan(self, result):
        return M.Head(result)()

    def _search_result_expanded(self, result):
        return M.Head(M.Tail(result)())()

    def _search_result_generated(self, result):
        return M.Head(M.Tail(M.Tail(result)())())()

    def _search_result_frontier_peak(self, result):
        return M.Head(M.Tail(M.Tail(M.Tail(result)())())())()

    def _rewrite_attempt(self, result, generated):
        return M.Pair(result, M.Pair(generated, M.EmptyList))

    def _rewrite_attempt_result(self, attempt):
        return M.Head(attempt)()

    def _rewrite_attempt_generated(self, attempt):
        return M.Head(M.Tail(attempt)())()

    def _empty_search_result(self):
        return self._search_result(M.EmptyList, M.Zero, M.Zero, M.Zero)

    def _current_total_cost(self):
        return self.prompt_total_cost

    def _current_total_cost_units(self):
        job_units = 0
        prompt_units = self.prompt_total_cost_units
        if self._active_search_job is not None:
            job_units = self._search_job_total_cost_units(self._active_search_job)
        return job_units + prompt_units

    def _maybe_prompt_to_continue(self):
        if self._timeout_requested() is M.truth_value:
            self.search_aborted = M.truth_value
            self.search_outcome_on_abort = SearchFailureLabel
            return
        if self._stop_listener is not None and M.IdentityCompare(self._stop_listener.requested(), M.truth_value)() is M.truth_value:
            self.search_aborted = M.truth_value
            self.search_outcome_on_abort = SearchPausedLabel
            return
        comparison_guard = self._comparison_prompt_guard()
        if comparison_guard is not None:
            comparison_guard.maybe_prompt(self)

    def _commit_completed_search_cost(self):
        comparison_guard = self._comparison_prompt_guard()
        if comparison_guard is not None:
            comparison_guard.record_completed_cost(self._current_total_cost_units())

    def _seen_term(self, seen, x):
        if M.IdentityCompare(seen, M.EmptyList)() is M.truth_value:
            return M.false_value
        h = M.Head(seen)()
        if M.TermEqual(h, x)() is M.truth_value:
            return M.truth_value
        return self._seen_term(M.Tail(seen)(), x)

    def _knowledge_has_fact(self, facts, target):
        if M.IdentityCompare(facts, M.EmptyList)() is M.truth_value:
            return M.false_value
        fact = M.Head(facts)()
        if M.TermEqual(fact, target)() is M.truth_value:
            return M.truth_value
        return self._knowledge_has_fact(M.Tail(facts)(), target)

    def _goal_reached(self, current, goal, knowledge_exact_trie=None):
        if IsKnowledge(current)() is M.truth_value:
            if knowledge_exact_trie is None:
                return self._knowledge_has_fact(KnowledgeFacts(current)(), goal)
            if M.IdentityCompare(knowledge_exact_trie, M.EmptyList)() is M.truth_value:
                return self._knowledge_has_fact(KnowledgeFacts(current)(), goal)
            return K.KnowledgeTrieHasFact(knowledge_exact_trie, goal, self.registry)()
        return M.TermEqual(current, goal)()

    def _derivation_reaches_goal(self, derivation, goal):
        end = DerivationEnd(derivation, self.registry)()
        return self._goal_reached(end, goal)

    def _match_premises(self, premises, facts, bindings, knowledge_head_index, knowledge_exact_trie, delta=None, used_delta=None, premise_index=0):
        if delta is None:
            delta = K.KnowledgeTrieFacts(knowledge_exact_trie, self.registry)()
        if used_delta is None:
            used_delta = M.false_value
        if M.IdentityCompare(premises, M.EmptyList)() is M.truth_value:
            if M.IdentityCompare(used_delta, M.truth_value)() is M.truth_value:
                return M.Pair(bindings, M.EmptyList)
            return M.EmptyList
        premise = M.Head(premises)()
        rest = M.Tail(premises)()
        premise_head_text = ""
        if M.IdentityCompare(Pmod.DEBUG_TRACE_STATE(), M.truth_value)() is M.truth_value:
            premise_head_text = _debug_term(premise, self.registry)
        premise_started_at = time.time()
        match_premise = premise
        if M.IdentityCompare(bindings, M.EmptyList)() is M.false_value:
            instantiated_premise = M.Instantiate(premise, bindings)()
            match_premise = M.Head(instantiated_premise)()
        if IsVarPattern(match_premise)() is M.false_value:
            if ContainsVar(match_premise)() is M.false_value:
                ground_present = M.false_value
                if M.IdentityCompare(knowledge_exact_trie, M.EmptyList)() is M.truth_value:
                    ground_present = self._knowledge_has_fact(facts, match_premise)
                else:
                    ground_present = K.KnowledgeTrieHasFact(knowledge_exact_trie, match_premise, self.registry)()
                if M.IdentityCompare(ground_present, M.false_value)() is M.truth_value:
                    if M.IdentityCompare(Pmod.DEBUG_TRACE_STATE(), M.truth_value)() is M.truth_value:
                        _debug(
                            "premise-join: premise "
                            + str(premise_index)
                            + " head="
                            + premise_head_text
                            + " elapsed="
                            + "{:.3f}".format(time.time() - premise_started_at)
                            + "s candidates=ground matched=no"
                        )
                    return M.EmptyList
                next_used_delta = used_delta
                remaining_delta = delta
                while M.IdentityCompare(remaining_delta, M.EmptyList)() is M.false_value:
                    if M.TermEqual(M.Head(remaining_delta)(), match_premise)() is M.truth_value:
                        next_used_delta = M.truth_value
                        remaining_delta = M.EmptyList
                    else:
                        remaining_delta = M.Tail(remaining_delta)()
                if M.IdentityCompare(Pmod.DEBUG_TRACE_STATE(), M.truth_value)() is M.truth_value:
                    _debug(
                        "premise-join: premise "
                        + str(premise_index)
                        + " head="
                        + premise_head_text
                        + " elapsed="
                        + "{:.3f}".format(time.time() - premise_started_at)
                        + "s candidates=ground matched=yes"
                    )
                return self._match_premises(
                    rest,
                    facts,
                    bindings,
                    knowledge_head_index,
                    knowledge_exact_trie,
                    delta,
                    next_used_delta,
                    premise_index + 1,
                )
        candidate_facts = facts
        if IsVarPattern(match_premise)() is M.false_value:
            candidate_facts = K.KnowledgeHeadIndexBucket(knowledge_head_index, match_premise, self.registry)()
        result = self._match_premise_against_facts(
            match_premise,
            rest,
            candidate_facts,
            facts,
            bindings,
            knowledge_head_index,
            knowledge_exact_trie,
            delta,
            used_delta,
            premise_index,
        )
        if M.IdentityCompare(Pmod.DEBUG_TRACE_STATE(), M.truth_value)() is M.truth_value:
            matched_text = "no"
            if M.IdentityCompare(result, M.EmptyList)() is M.false_value:
                matched_text = "yes"
            _debug(
                "premise-join: premise "
                + str(premise_index)
                + " head="
                + premise_head_text
                + " elapsed="
                + "{:.3f}".format(time.time() - premise_started_at)
                + "s candidates="
                + M.GMPRepText(M.CountRep(candidate_facts)())()
                + " matched="
                + matched_text
            )
        return result

    def _match_premise_against_facts(
        self,
        premise,
        rest_premises,
        facts,
        all_facts,
        bindings,
        knowledge_head_index,
        knowledge_exact_trie,
        delta,
        used_delta,
        premise_index=0,
    ):
        matches = M.EmptyList
        remaining = facts
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            fact = M.Head(remaining)()
            candidate_matches = M.truth_value
            premise_constructor = M.GetConstructor(premise, self.registry)()
            fact_constructor = M.GetConstructor(fact, self.registry)()
            if M.IdentityCompare(premise_constructor, M.EmptyList)() is M.false_value:
                if M.IdentityCompare(fact_constructor, M.EmptyList)() is M.false_value:
                    premise_label = M.Head(premise_constructor)()
                    fact_label = M.Head(fact_constructor)()
                    if M.IdentityCompare(premise_label, fact_label)() is M.false_value:
                        candidate_matches = M.false_value
                    elif M.IdentityCompare(premise_label, SolvedLabel)() is M.truth_value:
                        premise_args = M.Tail(premise_constructor)()
                        fact_args = M.Tail(fact_constructor)()
                        premise_inner = M.Head(premise_args)()
                        fact_inner = M.Head(fact_args)()
                        premise_inner_constructor = M.GetConstructor(premise_inner, self.registry)()
                        fact_inner_constructor = M.GetConstructor(fact_inner, self.registry)()
                        if M.IdentityCompare(premise_inner_constructor, M.EmptyList)() is M.false_value:
                            if M.IdentityCompare(fact_inner_constructor, M.EmptyList)() is M.false_value:
                                premise_inner_label = M.Head(premise_inner_constructor)()
                                fact_inner_label = M.Head(fact_inner_constructor)()
                                if M.IdentityCompare(premise_inner_label, fact_inner_label)() is M.false_value:
                                    candidate_matches = M.false_value
                                elif M.IdentityCompare(premise_inner_label, ExprEqLabel)() is M.truth_value:
                                    premise_equation_args = M.Tail(premise_inner_constructor)()
                                    fact_equation_args = M.Tail(fact_inner_constructor)()
                                    premise_left = M.Head(premise_equation_args)()
                                    fact_left = M.Head(fact_equation_args)()
                                    left_match = M.Match(premise_left, fact_left)()
                                    if M.IdentityCompare(M.Head(left_match)(), M.truth_value)() is M.false_value:
                                        candidate_matches = M.false_value
            if M.IdentityCompare(candidate_matches, M.truth_value)() is M.truth_value:
                match = M.Match(premise, fact)()
            else:
                match = M.Pair(M.false_value, M.EmptyList)
            flag = M.Head(match)()
            bound = M.Tail(match)()
            if M.IdentityCompare(flag, M.truth_value)() is M.truth_value:
                merged = M.MergeBindings(bindings, bound)()
                merged_flag = M.Head(merged)()
                merged_bindings = M.Tail(merged)()
                if M.IdentityCompare(merged_flag, M.truth_value)() is M.truth_value:
                    next_used_delta = used_delta
                    remaining_delta = delta
                    while M.IdentityCompare(remaining_delta, M.EmptyList)() is M.false_value:
                        if M.TermEqual(M.Head(remaining_delta)(), fact)() is M.truth_value:
                            next_used_delta = M.truth_value
                            break
                        remaining_delta = M.Tail(remaining_delta)()
                    rest_matches = self._match_premises(
                        rest_premises,
                        all_facts,
                        merged_bindings,
                        knowledge_head_index,
                        knowledge_exact_trie,
                        delta,
                        next_used_delta,
                        premise_index + 1,
                    )
                    while M.IdentityCompare(rest_matches, M.EmptyList)() is M.false_value:
                        matches = M.Pair(M.Head(rest_matches)(), matches)
                        rest_matches = M.Tail(rest_matches)()
            remaining = M.Tail(remaining)()
        return matches

    def _apply_theorem_rule_to_knowledge(
        self,
        rule,
        current,
        knowledge_head_index=None,
        knowledge_exact_trie=None,
        delta=None,
        next_delta=None,
        actions_rev=None,
    ):
        facts = KnowledgeFacts(current)()
        if knowledge_head_index is None or knowledge_exact_trie is None:
            indexes = self._theorem_indexes_for(current)
            knowledge_head_index = M.Head(indexes)()
            knowledge_exact_trie = M.Head(M.Tail(indexes)())()
        if delta is None:
            self._stage_debug("theorem rule: reconstructing default delta from exact trie start")
            delta_started_at = time.time()
            delta = K.KnowledgeTrieFacts(knowledge_exact_trie, self.registry)()
            self._stage_debug(
                "theorem rule: reconstructing default delta from exact trie complete; elapsed="
                + "{:.3f}".format(time.time() - delta_started_at)
                + "s facts="
                + M.GMPRepText(M.CountRep(delta)())()
            )
        if next_delta is None:
            next_delta = M.EmptyList
        if actions_rev is None:
            actions_rev = M.EmptyList
        rule_delta_facts = M.EmptyList
        if M.IdentityCompare(Pmod.DEBUG_TRACE_STATE(), M.truth_value)() is M.truth_value:
            premise_probe = RulePremises(rule)()
            premise_index = M.Zero
            while M.IdentityCompare(premise_probe, M.EmptyList)() is M.false_value:
                premise_term = M.Head(premise_probe)()
                if ContainsVar(premise_term)() is M.false_value:
                    ground_present = self._knowledge_has_fact(facts, premise_term)
                    if ground_present is M.truth_value:
                        ground_text = "yes"
                    else:
                        ground_text = "no"
                    self._stage_debug(
                        "theorem rule premise "
                        + M.GMPRepText(premise_index())()
                        + " ground-present="
                        + ground_text
                        + " premise="
                        + M.PrettyTerm(premise_term, self.registry)()
                    )
                else:
                    premise_bucket = K.KnowledgeHeadIndexBucket(knowledge_head_index, premise_term, self.registry)()
                    self._stage_debug(
                        "theorem rule premise "
                        + M.GMPRepText(premise_index())()
                        + " bucket-size="
                        + M.GMPRepText(M.CountRep(premise_bucket)())()
                        + " premise="
                        + M.PrettyTerm(premise_term, self.registry)()
                    )
                premise_probe = M.Tail(premise_probe)()
                premise_index = self._succ_nat(premise_index)
        matching_bindings = M.EmptyList
        premise_key = M.ExactKey(RulePremises(rule)(), self.registry)()
        # The join result depends on the facts and the delta it was computed
        # against, not on the rule premises alone. Drop the cache whenever
        # either changes; keep it across cursor advances that change neither.
        cache_state_key = self._state_key(current)
        cache_state_stale = M.false_value
        if M.TermEqual(cache_state_key, self._premise_bindings_cache_state_key)() is M.false_value:
            cache_state_stale = M.truth_value
        elif M.IdentityCompare(delta, self._premise_bindings_cache_delta)() is M.false_value:
            cache_state_stale = M.truth_value
        if M.IdentityCompare(cache_state_stale, M.truth_value)() is M.truth_value:
            self._premise_bindings_cache = M.EmptyList
            self._premise_bindings_cache_state_key = cache_state_key
            self._premise_bindings_cache_delta = delta
        cache_lookup = self._premise_bindings_cache
        cache_found = M.false_value
        while M.IdentityCompare(cache_lookup, M.EmptyList)() is M.false_value:
            cache_entry = M.Head(cache_lookup)()
            cache_key = M.Head(cache_entry)()
            if M.TermEqual(cache_key, premise_key)() is M.truth_value:
                matching_bindings = M.Head(M.Tail(cache_entry)())()
                cache_found = M.truth_value
                cache_lookup = M.EmptyList
            else:
                cache_lookup = M.Tail(cache_lookup)()
        if M.IdentityCompare(cache_found, M.false_value)() is M.truth_value:
            matching_bindings = self._match_premises(
                RulePremises(rule)(),
                facts,
                M.EmptyList,
                knowledge_head_index,
                knowledge_exact_trie,
                delta,
                M.false_value,
            )
            self._premise_bindings_cache = M.Pair(
                M.Pair(premise_key, M.Pair(matching_bindings, M.EmptyList)),
                self._premise_bindings_cache,
            )
        self._stage_debug(
            "theorem rule: matching bindings ready count="
            + M.GMPRepText(M.CountRep(matching_bindings)())()
            + " join="
            + ("cached" if M.IdentityCompare(cache_found, M.truth_value)() is M.truth_value else "fresh")
        )
        remaining_bindings = matching_bindings
        while M.IdentityCompare(remaining_bindings, M.EmptyList)() is M.false_value:
            bindings = M.Head(remaining_bindings)()
            instantiate_started_at = time.time()
            inst = M.Instantiate(RuleReplacement(rule)(), bindings)()
            self._stage_debug(
                "theorem rule: instantiate complete elapsed="
                + "{:.3f}".format(time.time() - instantiate_started_at)
                + "s"
            )
            conclusion = M.Head(inst)()
            if M.IdentityCompare(knowledge_exact_trie, M.EmptyList)() is M.truth_value:
                already_known = self._knowledge_has_fact(facts, conclusion)
            else:
                already_known = K.KnowledgeTrieHasFact(knowledge_exact_trie, conclusion, self.registry)()
            already_pending = self._knowledge_has_fact(next_delta, conclusion)
            if M.IdentityCompare(already_known, M.false_value)() is M.truth_value:
                if M.IdentityCompare(already_pending, M.false_value)() is M.truth_value:
                    action = TheoremAction(rule, bindings)()
                    next_delta = M.Pair(conclusion, next_delta)
                    rule_delta_facts = M.Pair(conclusion, rule_delta_facts)
                    actions_rev = M.Pair(action, actions_rev)
            remaining_bindings = M.Tail(remaining_bindings)()
        return M.Pair(next_delta, M.Pair(actions_rev, M.Pair(rule_delta_facts, M.EmptyList)))

    def _premises_satisfied_by_bindings(self, premises, facts, bindings):
        if M.IdentityCompare(premises, M.EmptyList)() is M.truth_value:
            return M.truth_value
        premise = M.Head(premises)()
        instantiated = M.Instantiate(premise, bindings)()
        concrete_premise = M.Head(instantiated)()
        if self._knowledge_has_fact(facts, concrete_premise) is M.false_value:
            return M.false_value
        return self._premises_satisfied_by_bindings(M.Tail(premises)(), facts, bindings)

    def _apply_goal_directed_theorem_rule_to_knowledge(self, rule, current, goal):
        facts = KnowledgeFacts(current)()
        replacement_match = M.Match(RuleReplacement(rule)(), goal)()
        replacement_flag = M.Head(replacement_match)()
        replacement_bindings = M.Tail(replacement_match)()
        if M.IdentityCompare(replacement_flag, M.truth_value)() is M.false_value:
            return current
        if self._premises_satisfied_by_bindings(RulePremises(rule)(), facts, replacement_bindings) is M.false_value:
            return current
        inst = M.Instantiate(RuleReplacement(rule)(), replacement_bindings)()
        conclusion = M.Head(inst)()
        if self._knowledge_has_fact(facts, conclusion) is M.truth_value:
            return current
        return NormalizeKnowledge(Knowledge(M.Pair(conclusion, facts))(), self.registry)()

    def _apply_goal_directed_theorem_rule_at_root(self, rule, current, goal):
        if IsKnowledge(current)() is M.truth_value:
            return self._apply_goal_directed_theorem_rule_to_knowledge(rule, current, goal)
        if RuleIsUnary(rule)() is M.false_value:
            return current
        replacement_match = M.Match(RuleReplacement(rule)(), goal)()
        replacement_flag = M.Head(replacement_match)()
        replacement_bindings = M.Tail(replacement_match)()
        if M.IdentityCompare(replacement_flag, M.truth_value)() is M.false_value:
            return current
        match = M.Match(RulePattern(rule)(), current)()
        flag = M.Head(match)()
        premise_bindings = M.Tail(match)()
        if M.IdentityCompare(flag, M.truth_value)() is M.false_value:
            return current
        merged = M.MergeBindings(replacement_bindings, premise_bindings)()
        merged_flag = M.Head(merged)()
        merged_bindings = M.Tail(merged)()
        if M.IdentityCompare(merged_flag, M.truth_value)() is M.false_value:
            return current
        inst = M.Instantiate(RuleReplacement(rule)(), merged_bindings)()
        return M.Head(inst)()

    def _apply_theorem_rule_at_root(self, rule, current, knowledge_head_index=None, knowledge_exact_trie=None):
        if IsKnowledge(current)() is M.truth_value:
            closure_result = self._apply_theorem_rule_to_knowledge(
                rule,
                current,
                knowledge_head_index,
                knowledge_exact_trie,
            )
            next_delta = M.Head(closure_result)()
            if M.IdentityCompare(M.TreeRoot(next_delta)(), M.EmptyList)() is M.truth_value:
                return current
            next_exact_trie = K.KnowledgeTrieInsertChain(
                knowledge_exact_trie,
                K.KnowledgeTrieFacts(next_delta, self.registry)(),
                self.registry,
            )()
            return Knowledge(K.KnowledgeTrieFacts(next_exact_trie, self.registry)())()
        if RuleIsUnary(rule)() is M.false_value:
            return current
        pattern = RulePattern(rule)()
        replacement = RuleReplacement(rule)()
        match = M.Match(pattern, current)()
        flag = M.Head(match)()
        binds = M.Tail(match)()
        if M.IdentityCompare(flag, M.truth_value)() is M.truth_value:
            inst = M.Instantiate(replacement, binds)()
            return M.Head(inst)()
        return current

    def _comparison_uses_raw_theorem_branches(self):
        if M.IdentityCompare(self.graph._search_compare_ignore_root_fast_paths, M.truth_value)() is M.truth_value:
            return M.truth_value
        if M.IdentityCompare(self.graph._search_compare_discovery_mode, M.truth_value)() is M.truth_value:
            return M.truth_value
        return M.false_value

    def _append_segment(self, path, segment):
        return Append(path, M.Pair(segment, M.EmptyList))()

    def _search(self, current, goal, steps_remaining, derivation_so_far, seen, depth):
        # legacy recursive search retained for compatibility; the active engine uses SearchStep
        return self._search_result(M.EmptyList, M.Zero, M.Zero, M.Zero)

    def __call__(self):
        return self.result


class SearchDFS(Search):
    pass


class SearchRewriteDFS(Search):
    pass


class SearchBFS(Search):
    def __init__(self, graph, start, goal, ordered_rules, heuristic, registry):
        super().__init__(graph, start, goal, ordered_rules, heuristic, registry)

    def _make_state(self, current, plan_rev, seen, steps_remaining, cursor=None):
        return SearchState(current, plan_rev, seen, steps_remaining, cursor)()

    def _state_current(self, state):
        return SearchStateCurrent(state)()

    def _state_plan(self, state):
        return SearchStatePlan(state)()

    def _state_seen(self, state):
        return SearchStateSeen(state)()

    def _state_steps_remaining(self, state):
        return SearchStateStepsRemaining(state)()

    def _state_cursor(self, state):
        return SearchStateCursor(state)()

    def _state_with_cursor(self, state, cursor):
        return self._make_state(
            self._state_current(state),
            self._state_plan(state),
            self._state_seen(state),
            self._state_steps_remaining(state),
            cursor,
        )

    def _advance_result(self, success, child, continuation, generated):
        return M.Pair(success, M.Pair(child, M.Pair(continuation, M.Pair(generated, M.EmptyList))))

    def _advance_result_success(self, result):
        return M.Head(result)()

    def _advance_result_child(self, result):
        return M.Head(M.Tail(result)())()

    def _advance_result_continuation(self, result):
        return M.Head(M.Tail(M.Tail(result)())())()

    def _advance_result_generated(self, result):
        return M.Head(M.Tail(M.Tail(M.Tail(result)())())())()

    def _cursor_is_theorem(self, cursor):
        if M.IsPair(cursor)() is M.false_value:
            return M.false_value
        return M.IdentityCompare(M.Head(cursor)(), SearchTheoremCursorLabel)()

    def _cursor_is_rewrite(self, cursor):
        if M.IsPair(cursor)() is M.false_value:
            return M.false_value
        return M.IdentityCompare(M.Head(cursor)(), SearchRewriteCursorLabel)()

    def _checkpoint_state_cursor(self, state, cursor):
        self._maybe_prompt_to_continue()
        if self.search_aborted is M.truth_value:
            if M.IdentityCompare(self.search_outcome_on_abort, SearchPausedLabel)() is M.truth_value:
                if M.IdentityCompare(cursor, M.EmptyList)() is M.truth_value:
                    self._paused_state = state
                else:
                    self._paused_state = self._state_with_cursor(state, cursor)
            return M.truth_value
        return M.false_value

    def _advance_theorem_cursor(self, state, cursor, goal):
        current = self._state_current(state)
        cursor_current = SearchTheoremCursorCurrent(cursor)()
        if M.IdentityCompare(cursor_current, M.EmptyList)() is M.false_value:
            current = cursor_current
        rules = SearchTheoremCursorRules(cursor)()
        generated = SearchTheoremCursorGenerated(cursor)()
        knowledge_head_index = SearchTheoremCursorHeadIndex(cursor)()
        knowledge_exact_trie = SearchTheoremCursorExactTrie(cursor)()
        if IsKnowledge(current)() is M.truth_value:
            if M.IdentityCompare(knowledge_head_index, M.EmptyList)() is M.truth_value:
                indexes = self._theorem_indexes_for(current)
                knowledge_head_index = M.Head(indexes)()
                knowledge_exact_trie = M.Head(M.Tail(indexes)())()
            elif M.IdentityCompare(knowledge_exact_trie, M.EmptyList)() is M.truth_value:
                indexes = self._theorem_indexes_for(current)
                knowledge_head_index = M.Head(indexes)()
                knowledge_exact_trie = M.Head(M.Tail(indexes)())()
        delta = SearchTheoremCursorDelta(cursor)()
        next_delta = SearchTheoremCursorNextDelta(cursor)()
        actions_rev = SearchTheoremCursorActions(cursor)()
        if IsKnowledge(current)() is M.truth_value:
            while M.IdentityCompare(rules, M.EmptyList)() is M.false_value:
                active_cursor = SearchTheoremCursor(
                    rules,
                    generated,
                    knowledge_head_index,
                    knowledge_exact_trie,
                    delta,
                    next_delta,
                    actions_rev,
                    current,
                )()
                if self._checkpoint_state_cursor(state, active_cursor) is M.truth_value:
                    return self._advance_result(M.EmptyList, M.EmptyList, M.EmptyList, M.Zero)
                rule = M.Head(rules)()
                rule_started_at = time.time()
                if M.IdentityCompare(Pmod.DEBUG_TRACE_STATE(), M.truth_value)() is M.truth_value:
                    self._stage_debug(
                        "theorem rule: premise join starting"
                        + " premises="
                        + M.GMPRepText(M.CountRep(RulePremises(rule)())())()
                        + " delta-facts="
                        + M.GMPRepText(M.CountRep(delta)())()
                        + " delta-source=cursor-chain trie-reconstruction=no"
                        + " rule="
                        + Pmod.PrettyRule(rule, self.registry)()
                    )
                closure_result = self._apply_theorem_rule_to_knowledge(
                    rule,
                    current,
                    knowledge_head_index,
                    knowledge_exact_trie,
                    delta,
                    next_delta,
                    actions_rev,
                )
                next_delta = M.Head(closure_result)()
                actions_rev = M.Head(M.Tail(closure_result)())()
                rule_delta_facts = M.Head(M.Tail(M.Tail(closure_result)())())()
                if M.IdentityCompare(Pmod.DEBUG_TRACE_STATE(), M.truth_value)() is M.truth_value:
                    self._stage_debug(
                        "theorem rule result"
                        + " rule="
                        + Pmod.PrettyRule(rule, self.registry)()
                        + " derived-facts="
                        + _debug_term(rule_delta_facts, self.registry)
                    )
                if M.IdentityCompare(rule_delta_facts, M.EmptyList)() is M.false_value:
                    trie_insert_started_at = time.time()
                    knowledge_exact_trie = K.KnowledgeTrieInsertChain(
                        knowledge_exact_trie,
                        rule_delta_facts,
                        self.registry,
                    )()
                    if M.IdentityCompare(Pmod.DEBUG_TRACE_STATE(), M.truth_value)() is M.truth_value:
                        self._stage_debug(
                            "post-rule: exact-trie insert complete; elapsed="
                            + "{:.3f}".format(time.time() - trie_insert_started_at)
                            + "s derived="
                            + M.GMPRepText(M.CountRep(rule_delta_facts)())()
                        )
                    head_insert_started_at = time.time()
                    knowledge_head_index = K.KnowledgeHeadIndexInsertChain(
                        knowledge_head_index,
                        rule_delta_facts,
                        self.registry,
                    )()
                    if M.IdentityCompare(Pmod.DEBUG_TRACE_STATE(), M.truth_value)() is M.truth_value:
                        self._stage_debug(
                            "post-rule: head-index insert complete; elapsed="
                            + "{:.3f}".format(time.time() - head_insert_started_at)
                            + "s"
                        )
                    current_rebuild_started_at = time.time()
                    current = Knowledge(Append(rule_delta_facts, KnowledgeFacts(current)())())()
                    if M.IdentityCompare(Pmod.DEBUG_TRACE_STATE(), M.truth_value)() is M.truth_value:
                        self._stage_debug(
                            "post-rule: current rebuild complete; elapsed="
                            + "{:.3f}".format(time.time() - current_rebuild_started_at)
                            + "s facts="
                            + M.GMPRepText(M.CountRep(KnowledgeFacts(current)())())()
                        )
                    goal_check_started_at = time.time()
                    goal_reached = self._goal_reached(current, goal, knowledge_exact_trie)
                    if M.IdentityCompare(Pmod.DEBUG_TRACE_STATE(), M.truth_value)() is M.truth_value:
                        self._stage_debug(
                            "post-rule: goal check complete; elapsed="
                            + "{:.3f}".format(time.time() - goal_check_started_at)
                            + "s reached="
                            + ("yes" if M.IdentityCompare(goal_reached, M.truth_value)() is M.truth_value else "no")
                        )
                    if M.IdentityCompare(goal_reached, M.truth_value)() is M.truth_value:
                        self._stage_debug(
                            "goal reached after theorem rule"
                            + " rule="
                            + Pmod.PrettyRule(rule, self.registry)()
                            + " derived-facts="
                            + _debug_term(rule_delta_facts, self.registry)
                        )
                        generated_count = M.Zero
                        pending_facts = K.KnowledgeTrieFacts(next_delta, self.registry)()
                        while M.IdentityCompare(pending_facts, M.EmptyList)() is M.false_value:
                            self._record_prompt_generated_one()
                            generated_count = self._succ_nat(generated_count)
                            pending_facts = M.Tail(pending_facts)()
                        next_plan_rev = Append(actions_rev, self._state_plan(state))()
                        return self._advance_result(
                            self._reverse(next_plan_rev, M.EmptyList),
                            M.EmptyList,
                            M.EmptyList,
                            generated_count,
                        )
                if M.IdentityCompare(Pmod.DEBUG_TRACE_STATE(), M.truth_value)() is M.truth_value:
                    self._stage_debug(
                        "theorem rule: premise join complete"
                        + " elapsed="
                        + "{:.3f}".format(time.time() - rule_started_at)
                        + "s derived-facts="
                        + M.GMPRepText(M.CountRep(rule_delta_facts)())()
                        + " facts="
                        + _debug_term(rule_delta_facts, self.registry)
                    )
                if M.IdentityCompare(Pmod.DEBUG_TRACE_STATE(), M.truth_value)() is M.truth_value:
                    remaining_rules = M.GMPRepText(M.CountRep(rules)())()
                    self._stage_debug(
                        "post-rule: advancing to next rule; remaining-rules="
                        + remaining_rules
                        + " pass-elapsed="
                        + "{:.3f}".format(time.time() - rule_started_at)
                        + "s"
                    )
                rules = M.Tail(rules)()
            if M.IdentityCompare(Pmod.DEBUG_TRACE_STATE(), M.truth_value)() is M.truth_value:
                self._stage_debug(
                    "theorm-pass: per-pass rule loop complete; derived-this-pass="
                    + M.GMPRepText(M.CountRep(next_delta)())()
                )
            if M.IdentityCompare(next_delta, M.EmptyList)() is M.truth_value:
                self._stage_debug("theorem saturation reached fixed point; no new facts")
                return self._advance_result(M.EmptyList, M.EmptyList, M.EmptyList, M.Zero)
            delta_facts = next_delta
            next_exact_trie = knowledge_exact_trie
            next_head_index = knowledge_head_index
            next_current = current
            next_plan_rev = Append(actions_rev, self._state_plan(state))()
            generated_count = M.Zero
            remaining_delta = delta_facts
            while M.IdentityCompare(remaining_delta, M.EmptyList)() is M.false_value:
                self._record_prompt_generated_one()
                generated_count = self._succ_nat(generated_count)
                remaining_delta = M.Tail(remaining_delta)()
            if self._goal_reached(next_current, goal, next_exact_trie) is M.truth_value:
                self._stage_debug(
                    "goal reached after theorem saturation"
                    + " derived-facts="
                    + _debug_term(delta_facts, self.registry)
                )
                return self._advance_result(
                    self._reverse(next_plan_rev, M.EmptyList),
                    M.EmptyList,
                    M.EmptyList,
                    generated_count,
                )
            next_steps = self._state_steps_remaining(state)
            if M.IdentityCompare(next_steps, M.EmptyList)() is M.false_value:
                next_steps_pair = M.NatPred(next_steps, self.registry)()
                next_steps = M.Head(next_steps_pair)()
                self.registry = M.Head(M.Tail(next_steps_pair)())()
                if M.NatEq(next_steps, M.Zero, self.registry)() is M.truth_value:
                    return self._advance_result(M.EmptyList, M.EmptyList, M.EmptyList, generated_count)
            next_cursor = SearchTheoremCursor(
                self.rules,
                generated,
                next_head_index,
                next_exact_trie,
                delta_facts,
                M.EmptyList,
                M.EmptyList,
                next_current,
            )()
            child = self._make_state(
                next_current,
                next_plan_rev,
                M.Pair(current, self._state_seen(state)),
                next_steps,
                next_cursor,
            )
            return self._advance_result(M.EmptyList, child, M.EmptyList, generated_count)
        while M.IdentityCompare(rules, M.EmptyList)() is M.false_value:
            active_cursor = SearchTheoremCursor(rules, generated)()
            if self._checkpoint_state_cursor(state, active_cursor) is M.truth_value:
                return self._advance_result(M.EmptyList, M.EmptyList, M.EmptyList, M.Zero)
            rule = M.Head(rules)()
            rest_rules = M.Tail(rules)()
            action = TheoremAction(rule)()
            next_term = self._canonical_term(self._apply_theorem_rule_at_root(rule, current))
            if M.TermEqual(next_term, current)() is M.truth_value:
                rules = rest_rules
                continue
            if self._tree_contains(generated, next_term) is M.truth_value:
                rules = rest_rules
                continue
            next_generated = self._tree_insert(generated, next_term)
            next_plan_rev = M.Pair(action, self._state_plan(state))
            self._record_prompt_generated_one()
            if self._goal_reached(next_term, goal) is M.truth_value:
                return self._advance_result(self._reverse(next_plan_rev, M.EmptyList), M.EmptyList, M.EmptyList, M.one)
            next_steps = self._state_steps_remaining(state)
            if M.IdentityCompare(next_steps, M.EmptyList)() is M.false_value:
                next_steps_pair = M.NatPred(next_steps, self.registry)()
                next_steps = M.Head(next_steps_pair)()
                self.registry = M.Head(M.Tail(next_steps_pair)())()
            child = self._make_state(next_term, next_plan_rev, M.Pair(current, self._state_seen(state)), next_steps)
            continuation = self._state_with_cursor(state, SearchTheoremCursor(rest_rules, next_generated)())
            return self._advance_result(M.EmptyList, child, continuation, M.one)
        rewrite_cursor = SearchRewriteCursor(M.EmptyList, M.EmptyList, M.Pair(self._rewrite_frame(current, M.EmptyList), M.EmptyList), generated)()
        return self._advance_rewrite_cursor(state, rewrite_cursor, goal)

    def _advance_rewrite_cursor(self, state, cursor, goal):
        current = self._state_current(state)
        frame = SearchRewriteCursorRule(cursor)()
        frame_rules = SearchRewriteCursorRestRules(cursor)()
        agenda = SearchRewriteCursorAgenda(cursor)()
        generated = SearchRewriteCursorGenerated(cursor)()

        if M.IdentityCompare(frame, M.EmptyList)() is M.truth_value:
            if M.IdentityCompare(agenda, M.EmptyList)() is M.truth_value:
                return self._advance_result(M.EmptyList, M.EmptyList, M.EmptyList, M.Zero)
            next_frame = M.Head(agenda)()
            next_agenda = M.Tail(agenda)()
            next_rules = SearchRewritePathFrameRules(next_frame)()
            if M.IdentityCompare(next_rules, M.EmptyList)() is M.truth_value:
                next_cursor = SearchRewriteCursor(M.EmptyList, M.EmptyList, next_agenda, generated)()
            else:
                next_cursor = SearchRewriteCursor(next_frame, next_rules, next_agenda, generated)()
            return self._advance_rewrite_cursor(state, next_cursor, goal)

        if self._checkpoint_state_cursor(state, cursor) is M.truth_value:
            return self._advance_result(M.EmptyList, M.EmptyList, M.EmptyList, M.Zero)

        subterm = SearchRewritePathFrameSubterm(frame)()
        path = SearchRewritePathFramePath(frame)()
        next_agenda = agenda
        next_frame = frame
        if M.IdentityCompare(SearchRewritePathFrameExpanded(frame)(), M.truth_value)() is M.false_value:
            if M.IsPair(subterm)() is M.truth_value:
                tail_frame = self._rewrite_frame(M.Tail(subterm)(), self._append_segment(path, M.one))
                head_frame = self._rewrite_frame(M.Head(subterm)(), self._append_segment(path, M.Zero))
                if M.IdentityCompare(SearchRewritePathFrameRules(tail_frame)(), M.EmptyList)() is M.false_value:
                    next_agenda = M.Pair(tail_frame, next_agenda)
                if M.IdentityCompare(SearchRewritePathFrameRules(head_frame)(), M.EmptyList)() is M.false_value:
                    next_agenda = M.Pair(head_frame, next_agenda)
            next_frame = SearchRewritePathFrame(subterm, path, SearchRewritePathFrameRules(frame)(), M.truth_value)()

        if M.IdentityCompare(frame_rules, M.EmptyList)() is M.truth_value:
            next_cursor = SearchRewriteCursor(M.EmptyList, M.EmptyList, next_agenda, generated)()
            return self._advance_rewrite_cursor(state, next_cursor, goal)

        active_rule = M.Head(frame_rules)()
        remaining_rules = M.Tail(frame_rules)()
        next_cursor = SearchRewriteCursor(next_frame, remaining_rules, next_agenda, generated)()
        if self._rewrite_rule_may_match_subterm(active_rule, subterm) is M.false_value:
            return self._advance_rewrite_cursor(state, next_cursor, goal)

        action = RewriteAction(active_rule, path)()
        self._stage_debug("trying rewrite")
        next_term = RewriteAtPath(active_rule, current, path, self.registry)()
        next_term = self._canonical_term(next_term)
        if M.TermEqual(next_term, current)() is M.truth_value:
            return self._advance_rewrite_cursor(state, next_cursor, goal)
        if self._tree_contains(generated, next_term) is M.truth_value:
            return self._advance_rewrite_cursor(state, next_cursor, goal)

        self._stage_debug("advanced via rewrite")
        next_generated = self._tree_insert(generated, next_term)
        self._record_prompt_generated_one()
        next_plan_rev = M.Pair(action, self._state_plan(state))
        if self._goal_reached(next_term, goal) is M.truth_value:
            self._stage_debug("goal reached directly via rewrite")
            return self._advance_result(self._reverse(next_plan_rev, M.EmptyList), M.EmptyList, M.EmptyList, M.one)

        next_steps_pair = M.NatPred(self._state_steps_remaining(state), self.registry)()
        next_steps = M.Head(next_steps_pair)()
        self.registry = M.Head(M.Tail(next_steps_pair)())()
        child = self._make_state(next_term, next_plan_rev, M.Pair(current, self._state_seen(state)), next_steps)
        continuation = self._state_with_cursor(state, SearchRewriteCursor(next_frame, remaining_rules, next_agenda, next_generated)())
        return self._advance_result(M.EmptyList, child, continuation, M.one)

    def _advance_state(self, state, goal):
        current = self._state_current(state)
        plan_rev = self._state_plan(state)
        cursor = self._state_cursor(state)
        if M.IdentityCompare(cursor, M.EmptyList)() is M.truth_value:
            self._stage_debug("advance_state: fresh state start")
            self._record_prompt_expansion()
            if self._checkpoint_state_cursor(state, M.EmptyList) is M.truth_value:
                return self._advance_result(M.EmptyList, M.EmptyList, M.EmptyList, M.Zero)
            if self._goal_reached(current, goal) is M.truth_value:
                self._stage_debug("advance_state: goal already reached")
                return self._advance_result(self._reverse(plan_rev, M.EmptyList), M.EmptyList, M.EmptyList, M.Zero)
            self._stage_debug("advance_state: after goal check")
            cached_solution = self._cached_solution(current, goal, plan_rev, self._state_steps_remaining(state))
            if M.Compare(cached_solution, M.EmptyList)() is not M.truth_value:
                return self._advance_result(cached_solution, M.EmptyList, M.EmptyList, M.Zero)
            self._stage_debug("advance_state: after cached-solution check")
            if M.NatEq(self._state_steps_remaining(state), M.Zero, self.registry)() is M.truth_value:
                self._stage_debug("exhausted step budget")
                return self._advance_result(M.EmptyList, M.EmptyList, M.EmptyList, M.Zero)
            if self._seen_term(self._state_seen(state), current) is M.truth_value:
                self._stage_debug("seen current before, pruning")
                return self._advance_result(M.EmptyList, M.EmptyList, M.EmptyList, M.Zero)
            self._stage_debug("advance_state: before cursor construction")
            cursor = self._theorem_cursor_for(current, goal)
            self._stage_debug("advance_state: after cursor construction")
            state = self._state_with_cursor(state, cursor)
        if self._cursor_is_theorem(cursor) is M.truth_value:
            theorem_result = self._advance_theorem_cursor(state, cursor, goal)
            if M.IdentityCompare(self._advance_result_success(theorem_result), M.EmptyList)() is M.false_value:
                return theorem_result
            if M.IdentityCompare(self._advance_result_child(theorem_result), M.EmptyList)() is M.false_value:
                return theorem_result
            if M.IdentityCompare(self._advance_result_continuation(theorem_result), M.EmptyList)() is M.false_value:
                return theorem_result
            if IsKnowledge(current)() is M.truth_value:
                return theorem_result
            rewrite_cursor = SearchRewriteCursor(M.EmptyList, M.EmptyList, M.Pair(self._rewrite_frame(current, M.EmptyList), M.EmptyList), M.EmptyList)()
            return self._advance_rewrite_cursor(self._state_with_cursor(state, rewrite_cursor), rewrite_cursor, goal)
        if self._cursor_is_rewrite(cursor) is M.truth_value:
            return self._advance_rewrite_cursor(state, cursor, goal)
        return self._advance_result(M.EmptyList, M.EmptyList, M.EmptyList, M.Zero)

    def _cached_solution(self, current, goal, plan_rev, steps_remaining):
        current_has_var = ContainsVar(current)()
        goal_has_var = ContainsVar(goal)()
        schematic_search = M.OrAtom(current_has_var, goal_has_var)()
        if schematic_search is M.truth_value:
            return M.EmptyList

        if M.IdentityCompare(self.graph._search_compare_ignore_root_fast_paths, M.truth_value)() is M.truth_value:
            if M.Compare(plan_rev, M.EmptyList)() is M.truth_value:
                if M.TermEqual(current, self.graph._search_compare_root_start)() is M.truth_value:
                    if M.TermEqual(goal, self.graph._search_compare_root_goal)() is M.truth_value:
                        self._stage_debug("comparison root skips cached/schema proof replay")
                        return M.EmptyList

        memo_hit = self._lookup_search_memo(current, goal, steps_remaining)
        if M.Compare(memo_hit, M.EmptyList)() is not M.truth_value:
            memo_status = SearchMemoEntryStatus(memo_hit)()
            if M.IdentityCompare(memo_status, SearchSuccessLabel)() is M.truth_value:
                memo_plan = SearchMemoEntryPlan(memo_hit)()
                self._stage_debug("memo hit")
                return self._reverse(M.Pair(memo_plan, plan_rev), M.EmptyList)
            self._stage_debug("memo failure hit")
            return M.EmptyList

        cached = self.graph.lookup_derivation(current, goal)
        if M.Compare(cached, M.EmptyList)() is not M.truth_value:
            self._stage_debug("cache hit")
            return self._reverse(M.Pair(cached, plan_rev), M.EmptyList)

        schema_hit = self.graph.lookup_derivation_schema(current, goal)
        if M.Compare(schema_hit, M.EmptyList)() is M.truth_value:
            return M.EmptyList

        plan = M.Head(schema_hit)()
        bindings = M.Head(M.Tail(schema_hit)())()
        self._stage_debug("schema hit")
        self._stage_debug("schema plan=" + PrettyPlanChain(plan, self.registry)())
        instantiated_pair = InstantiateDerivation(current, plan, bindings, self.registry)()
        instantiated_derivation = M.Head(instantiated_pair)()
        self.registry = M.Head(M.Tail(instantiated_pair)())()
        self.graph._replace_context(constructors=self.registry)
        if M.Compare(instantiated_derivation, M.EmptyList)() is not M.truth_value and self._derivation_reaches_goal(instantiated_derivation, goal) is M.truth_value:
            self._stage_debug("schema derivation reaches goal")
            return self._reverse(M.Pair(instantiated_derivation, plan_rev), M.EmptyList)
        return M.EmptyList

    def __call__(self):
        return self.result


class SearchBeam(Search):
    def __init__(self, graph, start, goal, ordered_rules, heuristic, registry):
        super().__init__(graph, start, goal, ordered_rules, heuristic, registry)

    def _take_frontier(self, frontier, width):
        if M.IdentityCompare(frontier, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        if M.NatEq(width, M.Zero, self.registry)() is M.truth_value:
            return M.EmptyList
        next_width_pair = M.NatPred(width, self.registry)()
        next_width = M.Head(next_width_pair)()
        return M.Pair(M.Head(frontier)(), self._take_frontier(M.Tail(frontier)(), next_width))

    def _limit_frontier(self, frontier):
        width = HeuristicBeamWidth(self.heuristic)()
        if M.NatEq(width, M.Zero, self.registry)() is M.truth_value:
            return frontier
        limited = self._take_frontier(frontier, width)
        _debug("search-beam: frontier limited")
        return limited


class SearchAStar(Search):
    def __init__(self, graph, start, goal, ordered_rules, heuristic, registry):
        super().__init__(graph, start, goal, ordered_rules, heuristic, registry)


class _SearchStepKernel(SearchBFS):
    def __init__(self, graph, job, rules, heuristic, goal, registry, stop_listener, progress_owner):
        self.graph = graph
        self.job = job
        self.registry = registry
        self.rules = rules
        if M.IdentityCompare(self.rules, M.EmptyList)() is M.false_value:
            if IsCompiledRule(M.Head(self.rules)())() is M.false_value:
                self.rules = CompileRuleChain(self.rules, registry)()
        self.heuristic = heuristic
        self._stop_listener = stop_listener
        self._progress_owner = progress_owner
        self._active_search_job = job
        self._paused_state = M.EmptyList
        self._console_input = self.graph._search_console_input
        if self._console_input is None:
            self._console_input = _SearchConsoleInput()
            self.graph._search_console_input = self._console_input
        self._init_search_prompt_state()
        self._init_search_order_state(
            goal,
            SearchJobTheoremRuleCache(job)(),
            SearchJobRewriteRules(job)(),
        )

    def _pause_progress_ticker(self):
        if self._progress_owner is None:
            return
        self._progress_owner._pause_progress_ticker()

    def _resume_progress_ticker(self):
        if self._progress_owner is None:
            return
        self._progress_owner._resume_progress_ticker()

    def _pause_stop_listener(self):
        if self._stop_listener is None:
            return
        self._stop_listener.pause()

    def _resume_stop_listener(self):
        if self._stop_listener is None:
            return
        self._stop_listener.resume()

    def _comparison_prompt_guard(self):
        return self.graph._search_comparison_prompt_guard

    def _read_console_line(self, prompt_text):
        return self._console_input.read_prompt(prompt_text)

    def _timeout_requested(self):
        if self._progress_owner is None:
            return M.false_value
        return self._progress_owner._timeout_requested()


class SearchStep(M.Edge):
    def __init__(self, graph, job, registry, stop_listener=None, progress_owner=None):
        self.graph = graph
        self.job = job
        self.registry = registry
        self.stop_listener = stop_listener
        self.progress_owner = progress_owner
        self.result = self._step()
        super().__init__(inputs=M.Pair(graph, M.Pair(job, M.Pair(registry, M.EmptyList))), results=self.result)

    def _succ_nat(self, value):
        pair = M.Succ(value, self.registry)()
        self.registry = M.Head(M.Tail(pair)())()
        return M.Head(pair)()

    def _nat_add(self, left, right):
        pair = M.Add(left, right, self.registry)()
        self.registry = M.Head(M.Tail(pair)())()
        return M.Head(pair)()

    def _nat_max(self, left, right):
        if M.NatLess(left, right, self.registry)() is M.truth_value:
            return right
        return left

    def _count_chain(self, chain):
        pair = M.Count(chain, self.registry)()
        count = M.Head(pair)()
        self.registry = M.Head(M.Tail(pair)())()
        return count

    def _job_frontier_size(self, frontier):
        frontier_size = SearchJobFrontierSize(self.job)()
        if M.IdentityCompare(frontier_size, M.EmptyList)() is M.false_value:
            return frontier_size
        return self._count_chain(frontier)

    def _pred_nat_or_zero(self, value):
        if M.NatEq(value, M.Zero, self.registry)() is M.truth_value:
            return M.Zero
        next_value_pair = M.NatPred(value, self.registry)()
        next_value = M.Head(next_value_pair)()
        self.registry = M.Head(M.Tail(next_value_pair)())()
        return next_value

    def _frontier_size_with_progress(self, rest_size, continuation, child):
        next_size = rest_size
        if M.IdentityCompare(continuation, M.EmptyList)() is M.false_value:
            next_size = self._succ_nat(next_size)
        if M.IdentityCompare(child, M.EmptyList)() is M.false_value:
            next_size = self._succ_nat(next_size)
        return next_size

    def _limit_frontier_size(self, mode, frontier_size):
        if M.IdentityCompare(mode, BeamLabel)() is M.false_value:
            return frontier_size
        width = HeuristicBeamWidth(SearchJobHeuristic(self.job)())()
        if M.NatEq(width, M.Zero, self.registry)() is M.truth_value:
            return frontier_size
        if M.NatLess(width, frontier_size, self.registry)() is M.truth_value:
            return width
        return frontier_size

    def _take_frontier(self, frontier, width):
        if M.IdentityCompare(frontier, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        if M.NatEq(width, M.Zero, self.registry)() is M.truth_value:
            return M.EmptyList
        next_width_pair = M.NatPred(width, self.registry)()
        next_width = M.Head(next_width_pair)()
        self.registry = M.Head(M.Tail(next_width_pair)())()
        return M.Pair(M.Head(frontier)(), self._take_frontier(M.Tail(frontier)(), next_width))

    def _prepend_if_present(self, x, chain):
        if M.IdentityCompare(x, M.EmptyList)() is M.truth_value:
            return chain
        return M.Pair(x, chain)

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
            return self._nat_add(head_distance, tail_distance)
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
        return self._count_chain(SearchStatePlan(state)())

    def _astar_frontier_score(self, state):
        path_cost = self._astar_path_cost(state)
        goal_distance = self._astar_goal_distance(SearchStateCurrent(state)(), SearchJobGoal(self.job)())
        return self._nat_add(path_cost, goal_distance)

    def _astar_insert(self, frontier, state):
        if M.IdentityCompare(frontier, M.EmptyList)() is M.truth_value:
            return M.Pair(state, M.EmptyList)
        head_state = M.Head(frontier)()
        if M.NatLess(self._astar_frontier_score(state), self._astar_frontier_score(head_state), self.registry)() is M.truth_value:
            return M.Pair(state, frontier)
        return M.Pair(head_state, self._astar_insert(M.Tail(frontier)(), state))

    def _astar_enqueue(self, rest, continuation, child):
        frontier = rest
        if M.IdentityCompare(continuation, M.EmptyList)() is M.false_value:
            frontier = self._astar_insert(frontier, continuation)
        if M.IdentityCompare(child, M.EmptyList)() is M.false_value:
            frontier = self._astar_insert(frontier, child)
        return frontier

    def _enqueue_progress(self, mode, rest, continuation, child):
        if M.IdentityCompare(self.graph._search_compare_discovery_mode, M.truth_value)() is M.truth_value:
            frontier = rest
            frontier = self._prepend_if_present(continuation, frontier)
            if M.IdentityCompare(child, M.EmptyList)() is M.false_value:
                frontier = Append(frontier, M.Pair(child, M.EmptyList))()
            return frontier
        if M.IdentityCompare(mode, DFSLabel)() is M.truth_value:
            frontier = rest
            frontier = self._prepend_if_present(continuation, frontier)
            frontier = self._prepend_if_present(child, frontier)
            return frontier
        if M.IdentityCompare(mode, RewriteDFSLabel)() is M.truth_value:
            frontier = rest
            frontier = self._prepend_if_present(child, frontier)
            frontier = self._prepend_if_present(continuation, frontier)
            return frontier
        if M.IdentityCompare(mode, AStarLabel)() is M.truth_value:
            return self._astar_enqueue(rest, continuation, child)
        frontier = self._prepend_if_present(continuation, rest)
        if M.IdentityCompare(child, M.EmptyList)() is M.false_value:
            frontier = Append(frontier, M.Pair(child, M.EmptyList))()
        if M.IdentityCompare(mode, BeamLabel)() is M.false_value:
            return frontier
        width = HeuristicBeamWidth(SearchJobHeuristic(self.job)())()
        if M.NatEq(width, M.Zero, self.registry)() is M.truth_value:
            return frontier
        limited = self._take_frontier(frontier, width)
        _debug("search-beam: frontier limited")
        return limited

    def _rebuild_job(
        self,
        status,
        frontier,
        expanded,
        generated,
        frontier_peak,
        result_plan,
        visited=None,
        theorem_rule_cache=None,
        rewrite_rules=None,
        frontier_size=None,
    ):
        if visited is None:
            visited = SearchJobVisited(self.job)()
        if theorem_rule_cache is None:
            theorem_rule_cache = SearchJobTheoremRuleCache(self.job)()
        if rewrite_rules is None:
            rewrite_rules = SearchJobRewriteRules(self.job)()
        if frontier_size is None:
            frontier_size = SearchJobFrontierSize(self.job)()
            if M.IdentityCompare(frontier_size, M.EmptyList)() is M.truth_value:
                frontier_size = self._count_chain(frontier)
        return SearchJob(
            SearchJobStart(self.job)(),
            SearchJobGoal(self.job)(),
            SearchJobRules(self.job)(),
            SearchJobHeuristic(self.job)(),
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

    def _reverse(self, chain, acc):
        remaining = chain
        reversed_chain = acc
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            reversed_chain = M.Pair(M.Head(remaining)(), reversed_chain)
            remaining = M.Tail(remaining)()
        return reversed_chain

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

    def _insert_seen_chain(self, seen, tree):
        if M.IdentityCompare(seen, M.EmptyList)() is M.truth_value:
            return tree
        next_tree = self._tree_insert(tree, M.Head(seen)())
        return self._insert_seen_chain(M.Tail(seen)(), next_tree)

    def _collect_frontier_discovered(self, frontier, tree):
        if M.IdentityCompare(frontier, M.EmptyList)() is M.truth_value:
            return tree
        state = M.Head(frontier)()
        next_tree = self._tree_insert(tree, SearchStateCurrent(state)())
        next_tree = self._insert_seen_chain(SearchStateSeen(state)(), next_tree)
        return self._collect_frontier_discovered(M.Tail(frontier)(), next_tree)

    def _initialize_job_visited(self, mode, frontier, visited):
        if self._mode_uses_global_visited(mode) is M.false_value:
            return M.EmptyList
        if M.IdentityCompare(visited, M.EmptyList)() is M.false_value:
            return visited
        return self._collect_frontier_discovered(frontier, M.EmptyList)

    def _filter_new_child(self, child, visited):
        if M.IdentityCompare(child, M.EmptyList)() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(visited, M.EmptyList))
        child_current = SearchStateCurrent(child)()
        if self._tree_contains(visited, child_current) is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(visited, M.EmptyList))
        next_visited = self._tree_insert(visited, child_current)
        return M.Pair(child, M.Pair(next_visited, M.EmptyList))

    def _maybe_store_success_derivation(self, state, plan):
        if M.Compare(plan, M.EmptyList)() is M.truth_value:
            return

        start = SearchStateCurrent(state)()
        goal = SearchJobGoal(self.job)()
        steps_remaining = SearchStateStepsRemaining(state)()

        schematic = M.OrAtom(ContainsVar(start)(), ContainsVar(goal)())()
        if schematic is M.truth_value:
            return

        steps_rep = M.NatRepOf(steps_remaining, self.registry)()
        steps_key = steps_remaining
        if M.IdentityCompare(steps_rep, M.EmptyList)() is M.false_value:
            steps_key = Gmpmod.GMPRepDigitList(steps_rep)()

        self.graph.store_search_memo(
            SearchMemoKey(
                Tmod.ExactKey(start, self.registry)(),
                Tmod.ExactKey(goal, self.registry)(),
                steps_key,
            )(),
            SearchMemoEntry(SearchSuccessLabel, plan)(),
        )

        if M.IdentityCompare(self.graph._search_worker_defer_derivation_materialization, M.truth_value)() is M.truth_value:
            _debug("search-step: skipping success derivation materialization for deferred worker")
            return

        derivation_pair = BuildDerivation(start, plan, self.registry)()
        derivation = M.Head(derivation_pair)()
        self.registry = M.Head(M.Tail(derivation_pair)())()
        self.graph._replace_context(constructors=self.registry)

        if M.Compare(derivation, M.EmptyList)() is M.false_value:
            self.graph.add_derivation(start, goal, derivation)

    def _maybe_store_failure_memo(self, state):
        start = SearchStateCurrent(state)()
        goal = SearchJobGoal(self.job)()
        steps_remaining = SearchStateStepsRemaining(state)()
        schematic = M.OrAtom(ContainsVar(start)(), ContainsVar(goal)())()
        if schematic is M.truth_value:
            return
        steps_rep = M.NatRepOf(steps_remaining, self.registry)()
        steps_key = steps_remaining
        if M.IdentityCompare(steps_rep, M.EmptyList)() is M.false_value:
            steps_key = Gmpmod.GMPRepDigitList(steps_rep)()
        self.graph.store_search_memo(
            SearchMemoKey(
                Tmod.ExactKey(start, self.registry)(),
                Tmod.ExactKey(goal, self.registry)(),
                steps_key,
            )(),
            SearchMemoEntry(SearchFailureLabel, M.EmptyList)(),
        )

    def _step(self):
        _debug("search-step: start")
        frontier = SearchJobFrontier(self.job)()
        _debug("search-step: after frontier extraction")
        mode = HeuristicSearchMode(SearchJobHeuristic(self.job)())()
        visited = self._initialize_job_visited(mode, frontier, SearchJobVisited(self.job)())
        _debug("search-step: after visited initialization")

        if M.IdentityCompare(frontier, M.EmptyList)() is M.truth_value:
            finished = self._rebuild_job(
                SearchFailureLabel,
                M.EmptyList,
                SearchJobExpanded(self.job)(),
                SearchJobGenerated(self.job)(),
                SearchJobFrontierPeak(self.job)(),
                M.EmptyList,
                visited,
                frontier_size=M.Zero,
            )
            return M.Pair(finished, M.Pair(self.registry, M.EmptyList))

        frontier_size = self._job_frontier_size(frontier)
        frontier_peak = self._nat_max(SearchJobFrontierPeak(self.job)(), frontier_size)
        state = M.Head(frontier)()
        rest = M.Tail(frontier)()
        rest_size = self._pred_nat_or_zero(frontier_size)
        fresh_state = M.IdentityCompare(SearchStateCursor(state)(), M.EmptyList)()

        job_rules = SearchJobRules(self.job)()
        compiled_text = "no"
        if M.IdentityCompare(job_rules, M.EmptyList)() is M.false_value:
            if IsCompiledRule(M.Head(job_rules)())() is M.truth_value:
                compiled_text = "yes"
            else:
                job_rules = CompileRuleChain(job_rules, self.registry)()
                self.job = SearchJob(
                    SearchJobStart(self.job)(),
                    SearchJobGoal(self.job)(),
                    job_rules,
                    SearchJobHeuristic(self.job)(),
                    SearchJobStatus(self.job)(),
                    SearchJobFrontier(self.job)(),
                    SearchJobExpanded(self.job)(),
                    SearchJobGenerated(self.job)(),
                    SearchJobFrontierPeak(self.job)(),
                    SearchJobResultPlan(self.job)(),
                    SearchJobVisited(self.job)(),
                    SearchJobTheoremRuleCache(self.job)(),
                    SearchJobRewriteRules(self.job)(),
                    SearchJobFrontierSize(self.job)(),
                )()
                compiled_text = "yes"
        _debug("search-step: job rules compiled=" + compiled_text)
        kernel = _SearchStepKernel(
            self.graph,
            self.job,
            job_rules,
            SearchJobHeuristic(self.job)(),
            SearchJobGoal(self.job)(),
            self.registry,
            self.stop_listener,
            self.progress_owner,
        )
        _debug("search-step: after kernel construction")
        advanced = kernel._advance_state(state, SearchJobGoal(self.job)())
        if kernel.search_aborted is M.truth_value:
            self.registry = kernel.registry
            interrupted = kernel.search_outcome_on_abort
            if M.IdentityCompare(interrupted, SearchPausedLabel)() is M.truth_value:
                paused_frontier = frontier
                if M.IdentityCompare(kernel._paused_state, M.EmptyList)() is M.false_value:
                    paused_frontier = M.Pair(kernel._paused_state, rest)
                paused = self._rebuild_job(
                    SearchPausedLabel,
                    paused_frontier,
                    SearchJobExpanded(self.job)(),
                    SearchJobGenerated(self.job)(),
                    SearchJobFrontierPeak(self.job)(),
                    SearchJobResultPlan(self.job)(),
                    visited,
                    kernel._theorem_rule_cache,
                    kernel._rewrite_rules,
                    frontier_size,
                )
                return M.Pair(paused, M.Pair(self.registry, M.EmptyList))
            failed = self._rebuild_job(
                SearchFailureLabel,
                M.EmptyList,
                SearchJobExpanded(self.job)(),
                SearchJobGenerated(self.job)(),
                SearchJobFrontierPeak(self.job)(),
                M.EmptyList,
                visited,
                kernel._theorem_rule_cache,
                kernel._rewrite_rules,
                M.Zero,
            )
            return M.Pair(failed, M.Pair(self.registry, M.EmptyList))

        success = kernel._advance_result_success(advanced)
        raw_child = kernel._advance_result_child(advanced)
        continuation = kernel._advance_result_continuation(advanced)
        generated_increment = kernel._advance_result_generated(advanced)
        self.registry = kernel.registry

        next_visited = visited
        child = raw_child
        if self._mode_uses_global_visited(mode) is M.truth_value:
            filtered = self._filter_new_child(raw_child, visited)
            child = M.Head(filtered)()
            next_visited = M.Head(M.Tail(filtered)())()
            if M.Compare(success, M.EmptyList)() is M.truth_value and M.IdentityCompare(child, M.EmptyList)() is M.truth_value:
                generated_increment = M.Zero

        expanded_total = SearchJobExpanded(self.job)()
        if fresh_state is M.truth_value:
            expanded_total = self._succ_nat(expanded_total)
        generated_total = self._nat_add(generated_increment, SearchJobGenerated(self.job)())

        if M.Compare(success, M.EmptyList)() is M.false_value:
            self._maybe_store_success_derivation(state, success)
            finished = self._rebuild_job(
                SearchSuccessLabel,
                M.EmptyList,
                expanded_total,
                generated_total,
                frontier_peak,
                success,
                next_visited,
                kernel._theorem_rule_cache,
                kernel._rewrite_rules,
                M.Zero,
            )
            return M.Pair(finished, M.Pair(self.registry, M.EmptyList))

        if M.IdentityCompare(continuation, M.EmptyList)() is M.truth_value and M.IdentityCompare(child, M.EmptyList)() is M.truth_value:
            self._maybe_store_failure_memo(state)

        next_frontier = self._enqueue_progress(mode, rest, continuation, child)
        next_frontier_size = self._frontier_size_with_progress(rest_size, continuation, child)
        next_frontier_size = self._limit_frontier_size(mode, next_frontier_size)
        final_peak = self._nat_max(frontier_peak, next_frontier_size)
        if M.IdentityCompare(next_frontier, M.EmptyList)() is M.truth_value:
            finished = self._rebuild_job(
                SearchFailureLabel,
                M.EmptyList,
                expanded_total,
                generated_total,
                final_peak,
                M.EmptyList,
                next_visited,
                kernel._theorem_rule_cache,
                kernel._rewrite_rules,
                M.Zero,
            )
            return M.Pair(finished, M.Pair(self.registry, M.EmptyList))

        running = self._rebuild_job(
            SearchRunningLabel,
            next_frontier,
            expanded_total,
            generated_total,
            final_peak,
            M.EmptyList,
            next_visited,
            kernel._theorem_rule_cache,
            kernel._rewrite_rules,
            next_frontier_size,
        )
        return M.Pair(running, M.Pair(self.registry, M.EmptyList))

    def __call__(self):
        return self.result


class SearchBurst(M.Edge):
    def __init__(self, graph, job, step_budget, registry, stop_listener=None, progress_owner=None):
        self.graph = graph
        self.job = job
        self.step_budget = step_budget
        self.registry = registry
        self.stop_listener = stop_listener
        self.progress_owner = progress_owner
        self.result = self._run(job, step_budget)
        super().__init__(
            inputs=M.Pair(
                graph,
                M.Pair(
                    job,
                    M.Pair(
                        step_budget,
                        M.Pair(registry, M.EmptyList),
                    ),
                ),
            ),
            results=self.result,
        )

    def _pred_nat(self, value):
        next_value_pair = M.NatPred(value, self.registry)()
        next_value = M.Head(next_value_pair)()
        self.registry = M.Head(M.Tail(next_value_pair)())()
        return next_value

    def _mode_text(self, job):
        return SearchModeText(HeuristicSearchMode(SearchJobHeuristic(job)())())()

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

    def _reverse(self, chain, acc):
        if M.IdentityCompare(chain, M.EmptyList)() is M.truth_value:
            return acc
        return self._reverse(M.Tail(chain)(), M.Pair(M.Head(chain)(), acc))

    def _frontier_focus_text(self, job):
        frontier = SearchJobFrontier(job)()
        if M.IdentityCompare(frontier, M.EmptyList)() is M.truth_value:
            return "empty"
        current = SearchStateCurrent(M.Head(frontier)())()
        return _debug_term(current, self.registry)

    def _plan_prefix_text(self, plan_rev):
        if M.IdentityCompare(plan_rev, M.EmptyList)() is M.truth_value:
            return "[]"
        return PrettyPlanChain(self._reverse(plan_rev, M.EmptyList), self.registry)()

    def _frontier_prefix_text(self, job):
        frontier = SearchJobFrontier(job)()
        if M.IdentityCompare(frontier, M.EmptyList)() is M.truth_value:
            return "[]"
        return self._plan_prefix_text(SearchStatePlan(M.Head(frontier)())())

    def _job_result_plan_text(self, job):
        plan = SearchJobResultPlan(job)()
        if M.IdentityCompare(plan, M.EmptyList)() is M.truth_value:
            return "[]"
        return PrettyPlanChain(plan, self.registry)()

    def _job_progress_text(self, job, remaining):
        return (
            "status="
            + SearchStatusText(SearchJobStatus(job)())()
            + " start="
            + _debug_term(SearchJobStart(job)(), self.registry)
            + " current="
            + self._frontier_focus_text(job)
            + " goal="
            + _debug_term(SearchJobGoal(job)(), self.registry)
            + " prefix="
            + self._frontier_prefix_text(job)
            + " frontier="
            + self._nat_text(SearchJobFrontierSize(job)())
            + " expanded="
            + self._nat_text(SearchJobExpanded(job)())
            + " generated="
            + self._nat_text(SearchJobGenerated(job)())
            + " peak="
            + self._nat_text(SearchJobFrontierPeak(job)())
            + " remaining-budget="
            + self._nat_text(remaining)
        )

    def _run(self, job, step_budget):
        current_job = job
        remaining = step_budget
        step_count = 0
        mode_text = self._mode_text(job)
        pid = multiprocessing.current_process().pid
        packet_started_at = time.time()
        discovery_mode = M.false_value
        discovery_current = M.EmptyList
        seeded_branch_probe = M.false_value
        if M.IdentityCompare(self.graph._search_compare_discovery_mode, M.truth_value)() is M.truth_value:
            discovery_mode = M.truth_value
            if M.IdentityCompare(SearchJobFrontier(job)(), M.EmptyList)() is M.false_value:
                initial_state = M.Head(SearchJobFrontier(job)())()
                discovery_current = SearchStateCurrent(initial_state)()
                if M.IdentityCompare(SearchStateCursor(initial_state)(), M.EmptyList)() is M.false_value:
                    seeded_branch_probe = M.truth_value
        if self.progress_owner is None:
            _debug(
                mode_text
                + ": worker pid="
                + str(pid)
                + " packet start "
                + self._job_progress_text(current_job, remaining)
            )
        while M.IdentityCompare(SearchJobStatus(current_job)(), SearchRunningLabel)() is M.truth_value:
            if M.NatEq(remaining, M.Zero, self.registry)() is M.truth_value:
                break
            step_pair = SearchStep(self.graph, current_job, self.registry, self.stop_listener, self.progress_owner)()
            current_job = M.Head(step_pair)()
            self.registry = M.Head(M.Tail(step_pair)())()
            self.graph._replace_context(constructors=self.registry)
            if self.progress_owner is not None:
                self.progress_owner._active_search_job = current_job
            remaining = self._pred_nat(remaining)
            step_count += 1
            if M.IdentityCompare(discovery_mode, M.truth_value)() is M.truth_value:
                if M.IdentityCompare(seeded_branch_probe, M.truth_value)() is M.truth_value:
                    if M.IdentityCompare(SearchJobStatus(current_job)(), SearchRunningLabel)() is M.truth_value:
                        if self.progress_owner is None:
                            _debug(
                                mode_text
                                + ": worker pid="
                                + str(pid)
                                + " "
                                + "{:.1f}".format(time.time() - packet_started_at)
                                + "s elapsed; seeded branch packet resolved; "
                                + self._job_progress_text(current_job, remaining)
                        )
                    break
                frontier = SearchJobFrontier(current_job)()
                if M.IdentityCompare(frontier, M.EmptyList)() is M.false_value:
                    next_current = SearchStateCurrent(M.Head(frontier)())()
                    frontier_size = SearchJobFrontierSize(current_job)()
                    widened_frontier = M.NatLess(M.one, frontier_size, self.registry)()
                    if M.TermEqual(next_current, discovery_current)() is M.false_value and widened_frontier is M.truth_value:
                        if self.progress_owner is None:
                            _debug(
                                mode_text
                                + ": worker pid="
                                + str(pid)
                                + " "
                                + "{:.1f}".format(time.time() - packet_started_at)
                                + "s elapsed; immediate branches ready; "
                                + self._job_progress_text(current_job, remaining)
                            )
                        break
                    if M.TermEqual(next_current, discovery_current)() is M.false_value:
                        if self.progress_owner is None:
                            _debug(
                                mode_text
                                + ": worker pid="
                                + str(pid)
                                + " "
                                + "{:.1f}".format(time.time() - packet_started_at)
                                + "s elapsed; linear frontier continues via "
                                + _debug_term(next_current, self.registry)
                                + "; "
                                + self._job_progress_text(current_job, remaining)
                            )
                        discovery_current = next_current
            if self.progress_owner is None and (step_count <= 5 or step_count % 5 == 0):
                _debug(
                    mode_text
                    + ": worker pid="
                    + str(pid)
                    + " "
                    + "{:.1f}".format(time.time() - packet_started_at)
                    + "s elapsed; "
                    + self._job_progress_text(current_job, remaining)
                )
        if self.progress_owner is None:
            status = SearchJobStatus(current_job)()
            if M.IdentityCompare(status, SearchSuccessLabel)() is M.truth_value:
                _debug(
                    mode_text
                    + ": worker pid="
                    + str(pid)
                    + " "
                    + "{:.1f}".format(time.time() - packet_started_at)
                    + "s elapsed; packet found result "
                    + _debug_term(SearchJobGoal(current_job)(), self.registry)
                    + " plan="
                    + self._job_result_plan_text(current_job)
                    + "; "
                    + self._job_progress_text(current_job, remaining)
                )
            elif M.IdentityCompare(status, SearchFailureLabel)() is M.truth_value:
                _debug(
                    mode_text
                    + ": worker pid="
                    + str(pid)
                    + " "
                    + "{:.1f}".format(time.time() - packet_started_at)
                    + "s elapsed; packet found no result; "
                    + self._job_progress_text(current_job, remaining)
                )
            else:
                _debug(
                    mode_text
                    + ": worker pid="
                    + str(pid)
                    + " "
                    + "{:.1f}".format(time.time() - packet_started_at)
                    + "s elapsed; packet yielded more work; "
                    + self._job_progress_text(current_job, remaining)
                )
        return M.Pair(current_job, M.Pair(self.registry, M.EmptyList))

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
        "SearchRootImmediateResultLabel"
    ):
        if name in namespace:
            globals()[name] = namespace[name]
