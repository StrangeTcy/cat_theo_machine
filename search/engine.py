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
            _debug(self.mode_text + ": start=" + _debug_term(self.start, registry))
            _debug(self.mode_text + ": goal=" + _debug_term(self.goal, registry))
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
        self._progress_ticker = _SearchProgressTicker(self.mode_text, self)
        self._progress_ticker.start()

    def _stop_progress_ticker(self):
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
        self._progress_ticker.pause()

    def _resume_progress_ticker(self):
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
            + " next="
            + self._frontier_focus_text(job)
            + " prefix="
            + self._frontier_prefix_text(job)
        )

    def _ticker_progress_text(self):
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
        if self._mode_is_plain_dfs() is M.false_value:
            return M.false_value
        if self._dfs_timeout_seconds is None:
            return M.false_value
        if self._progress_ticker._elapsed_seconds() <= self._dfs_timeout_seconds:
            return M.false_value
        if self._dfs_timeout_triggered is M.false_value:
            _debug("search-dfs: timeout requested")
            self._pause_progress_ticker()
            self._pause_stop_listener()
            self._dfs_timeout_triggered = M.truth_value
        return M.truth_value

    def _mode_is_plain_dfs(self):
        mode = HeuristicSearchMode(self.heuristic)()
        return M.IdentityCompare(mode, DFSLabel)()

    def _burst_budget(self):
        mode = HeuristicSearchMode(self.heuristic)()
        left = M.five
        if M.OrAtom(M.IdentityCompare(mode, DFSLabel)(), M.IdentityCompare(mode, RewriteDFSLabel)())() is M.truth_value:
            left = M.nine
        budget_pair = M.Multiply(left, M.five, self.registry)()
        budget = M.Head(budget_pair)()
        self.registry = M.Head(M.Tail(budget_pair)())()
        return budget

    def _maybe_abort_slow_dfs(self, job):
        if self._timeout_requested() is M.false_value:
            return job
        self.search_aborted = M.truth_value
        self.search_outcome_on_abort = SearchFailureLabel
        return self._search_job_with_status(job, SearchFailureLabel)

    def _completion_status_text(self, outcome):
        if self.search_aborted is M.truth_value:
            if M.IdentityCompare(self.search_outcome_on_abort, SearchPausedLabel)() is M.truth_value:
                return "paused"
            return "aborted"
        if M.IdentityCompare(outcome, SearchPausedLabel)() is M.truth_value:
            return "paused"
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
        max_steps = self.graph.next_rule_index
        if M.IdentityCompare(max_steps, M.EmptyList)() is M.truth_value:
            count_rep = M.CountRep(self.rules)()
            max_steps = M.Atom()
            max_steps.value = count_rep
        elif M.NatEq(max_steps, M.Zero, self.registry)() is M.truth_value:
            count_rep = M.CountRep(self.rules)()
            max_steps = M.Atom()
            max_steps.value = count_rep
        _debug(self.mode_text + ": max-steps=" + self._nat_text(max_steps))
        start_state = SearchState(self.start, M.EmptyList, M.EmptyList, max_steps)()
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
        self._rewrite_rules = rewrite_rules
        self._rewrite_rules_goal = goal
        self._goal_head_index = M.EmptyList
        self._goal_head_index_ready = M.false_value

    def _canonical_term(self, term):
        # Keep canonicalization inside the hypergraph kernel.
        return HeuristicCanonicalize(term, self.heuristic, self.registry)()

    def _goal_head_allows(self, subterm):
        if self._goal_head_index_ready is M.false_value:
            self._goal_head_index = HeuristicGoalHeadNeighborhood(self._rewrite_rules_goal, self.rules, self.registry)()
            self._goal_head_index_ready = M.truth_value
        return HeuristicGoalHeadAllowsSubterm(self._goal_head_index, subterm, self.registry)()

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

    def _theorem_applicable_rules_sharded(self, current, knowledge_head_index):
        from .runtime import _SearchApplicableRulesShardWorker

        shard_width = M.four
        host_parallelism = 1
        try:
            host_parallelism = multiprocessing.cpu_count()
        except Exception:
            host_parallelism = 1
        if host_parallelism <= 1:
            return FilterApplicableRulesWithIndex(self.rules, current, knowledge_head_index, self.registry)()

        try:
            mp_context = multiprocessing.get_context("fork")
        except Exception:
            mp_context = multiprocessing.get_context("spawn")
        remaining_rules = self.rules
        slot = 0
        workers = ()
        while M.IdentityCompare(remaining_rules, M.EmptyList)() is M.false_value:
            shard_rules = SearchChainTake(remaining_rules, shard_width)()
            remaining_rules = SearchChainDrop(remaining_rules, shard_width)()
            result_queue = mp_context.Queue()
            process = mp_context.Process(
                target=_SearchApplicableRulesShardWorker,
                args=(slot, shard_rules, current, knowledge_head_index, self.registry, result_queue),
            )
            process.start()
            workers = workers + ((slot, process, result_queue),)
            slot = slot + 1

        ordered_results = ()
        for worker in workers:
            slot = worker[0]
            process = worker[1]
            result_queue = worker[2]
            process.join()
            shard_payload = result_queue.get()
            shard_slot = shard_payload[0]
            shard_result = shard_payload[1]
            if shard_result is None:
                raise RuntimeError("search theorem applicability shard failed at slot " + str(shard_slot))
            if shard_slot != slot:
                raise RuntimeError("search theorem applicability shard order mismatch")
            ordered_results = ordered_results + (shard_result,)

        shard_results = M.EmptyList
        index = len(ordered_results)
        while index > 0:
            index = index - 1
            shard_results = M.Pair(ordered_results[index], shard_results)
        return SearchChainAppendMany(shard_results)()

    def _theorem_applicable_rules_for(self, current):
        started_at = time.time()
        self._stage_debug(
            "applicable theorem rules start for current="
            + _debug_term(current, self.registry)
        )
        cache_key = self._theorem_applicable_rule_cache_key(current)
        after_cache_key = time.time()
        self._stage_debug(
            "applicable theorem rules after cache key in "
            + "{:.3f}".format(after_cache_key - started_at)
            + "s"
        )
        cache_disabled = M.IdentityCompare(self.graph._search_probe_disable_applicable_cache, M.truth_value)() is M.truth_value
        cached = M.EmptyList
        if cache_disabled is M.false_value:
            cached = self._tree_lookup_fact(self._theorem_applicable_rule_cache, cache_key)
        after_cache_lookup = time.time()
        self._stage_debug(
            "applicable theorem rules after cache lookup in "
            + "{:.3f}".format(after_cache_lookup - after_cache_key)
            + "s"
        )
        if M.IdentityCompare(cached, M.EmptyList)() is M.false_value:
            cached_count_pair = M.Count(M.Head(cached)(), self.registry)()
            cached_count = M.Head(cached_count_pair)()
            self.registry = M.Head(M.Tail(cached_count_pair)())()
            self._stage_debug(
                "applicable theorem rules cache hit count="
                + M.PrettyTerm(cached_count, self.registry)()
                + " for current="
                + _debug_term(current, self.registry)
            )
            return M.Head(cached)()
        self._stage_debug(
            "computing applicable theorem rules for current="
            + _debug_term(current, self.registry)
        )
        knowledge_head_index = M.EmptyList
        if IsKnowledge(current)() is M.truth_value:
            knowledge_head_index = K.KnowledgeHeadIndexInsertChain(M.EmptyTree, KnowledgeFacts(current)(), self.registry)()
        after_head_index = time.time()
        self._stage_debug(
            "applicable theorem rules after head index in "
            + "{:.3f}".format(after_head_index - after_cache_lookup)
            + "s"
        )
        shard_disabled = M.IdentityCompare(self.graph._search_probe_disable_applicable_shards, M.truth_value)() is M.truth_value
        if shard_disabled is M.truth_value:
            applicable = FilterApplicableRulesWithIndex(self.rules, current, knowledge_head_index, self.registry)()
        else:
            applicable = self._theorem_applicable_rules_sharded(current, knowledge_head_index)
        after_filter = time.time()
        self._stage_debug(
            "applicable theorem rules after filtering in "
            + "{:.3f}".format(after_filter - after_head_index)
            + "s"
        )
        applicable_count_pair = M.Count(applicable, self.registry)()
        applicable_count = M.Head(applicable_count_pair)()
        self.registry = M.Head(M.Tail(applicable_count_pair)())()
        self._stage_debug(
            "applicable theorem rules ready count="
            + M.PrettyTerm(applicable_count, self.registry)()
            + " for current="
            + _debug_term(current, self.registry)
        )
        meta_disabled = M.IdentityCompare(self.graph._search_probe_disable_anchor_meta, M.truth_value)() is M.truth_value
        if meta_disabled is M.truth_value:
            self._stage_debug("applicable theorem rules note: anchor meta probe disabled flag is on, but no runtime fallback is wired")
        if cache_disabled is M.false_value:
            self._theorem_applicable_rule_cache = self._tree_insert_fact(
                self._theorem_applicable_rule_cache,
                cache_key,
                M.Pair(applicable, M.EmptyList),
            )
        after_cache_store = time.time()
        self._stage_debug(
            "applicable theorem rules after cache store in "
            + "{:.3f}".format(after_cache_store - after_filter)
            + "s total="
            + "{:.3f}".format(after_cache_store - started_at)
            + "s"
        )
        return applicable

    def _theorem_rules_for(self, current, goal):
        cache_key = self._theorem_rule_cache_key(current, goal)
        cached = self._tree_lookup_fact(self._theorem_rule_cache, cache_key)
        if M.IdentityCompare(cached, M.EmptyList)() is M.false_value:
            cached_count_pair = M.Count(M.Head(cached)(), self.registry)()
            cached_count = M.Head(cached_count_pair)()
            self.registry = M.Head(M.Tail(cached_count_pair)())()
            self._stage_debug(
                "theorem rule order cache hit count="
                + M.PrettyTerm(cached_count, self.registry)()
                + " for current="
                + _debug_term(current, self.registry)
                + " goal="
                + _debug_term(goal, self.registry)
            )
            return M.Head(cached)()

        applicable_rules = self._theorem_applicable_rules_for(current)
        knowledge_head_index = M.EmptyList
        if IsKnowledge(current)() is M.truth_value:
            knowledge_head_index = K.KnowledgeHeadIndexInsertChain(M.EmptyTree, KnowledgeFacts(current)(), self.registry)()
        if M.IdentityCompare(self.rule_order_mode, GoalHeadOrderLabel)() is M.truth_value:
            self._stage_debug(
                "ordering theorem rules toward goal="
                + _debug_term(goal, self.registry)
                + " for current="
                + _debug_term(current, self.registry)
            )
            ordered = GoalHeadRuleOrdererWithIndex(applicable_rules, current, goal, knowledge_head_index, self.registry)()
        else:
            ordered = applicable_rules
        ordered_count_pair = M.Count(ordered, self.registry)()
        ordered_count = M.Head(ordered_count_pair)()
        self.registry = M.Head(M.Tail(ordered_count_pair)())()
        self._stage_debug(
            "theorem rule order ready count="
            + M.PrettyTerm(ordered_count, self.registry)()
            + " for current="
            + _debug_term(current, self.registry)
            + " goal="
            + _debug_term(goal, self.registry)
        )
        self._theorem_rule_cache = self._tree_insert_fact(
            self._theorem_rule_cache,
            cache_key,
            M.Pair(ordered, M.EmptyList),
        )
        return ordered

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
        self.prompt_expanded = self._succ_nat(self.prompt_expanded)
        self.prompt_total_cost = self._succ_nat(self.prompt_total_cost)
        self.prompt_expanded_units += 1
        self.prompt_total_cost_units += 1

    def _record_prompt_generated_one(self):
        self.prompt_generated = self._succ_nat(self.prompt_generated)
        self.prompt_total_cost = self._succ_nat(self.prompt_total_cost)
        self.prompt_generated_units += 1
        self.prompt_total_cost_units += 1

    def _record_prompt_generated_count(self, count):
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

    def _goal_reached(self, current, goal):
        if IsKnowledge(current)() is M.truth_value:
            return self._knowledge_has_fact(KnowledgeFacts(current)(), goal)
        return M.TermEqual(current, goal)()

    def _derivation_reaches_goal(self, derivation, goal):
        end = DerivationEnd(derivation, self.registry)()
        return self._goal_reached(end, goal)

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

    def _apply_theorem_rule_to_knowledge(self, rule, current):
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
        return NormalizeKnowledge(Knowledge(M.Pair(conclusion, facts))(), self.registry)()

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

    def _apply_theorem_rule_at_root(self, rule, current):
        if IsKnowledge(current)() is M.truth_value:
            return self._apply_theorem_rule_to_knowledge(rule, current)
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
        rules = SearchTheoremCursorRules(cursor)()
        generated = SearchTheoremCursorGenerated(cursor)()
        while M.IdentityCompare(rules, M.EmptyList)() is M.false_value:
            active_cursor = SearchTheoremCursor(rules, generated)()
            if self._checkpoint_state_cursor(state, active_cursor) is M.truth_value:
                return self._advance_result(M.EmptyList, M.EmptyList, M.EmptyList, M.Zero)

            rule = M.Head(rules)()
            rest_rules = M.Tail(rules)()
            action = TheoremAction(rule)()
            self._stage_debug(
                "trying theorem; "
                + self._state_progress_text(state)
                + " goal="
                + _debug_term(goal, self.registry)
                + " action="
                + PrettyAction(action, self.registry)()
            )
            next_term = self._apply_theorem_rule_at_root(rule, current)
            next_term = self._canonical_term(next_term)
            if M.TermEqual(next_term, current)() is M.truth_value:
                rules = rest_rules
                continue
            if self._tree_contains(generated, next_term) is M.truth_value:
                rules = rest_rules
                continue

            self._stage_debug(
                "advanced via theorem="
                + _debug_term(rule, self.registry)
                + "; "
                + self._state_transition_text(state, action, next_term)
            )
            next_generated = self._tree_insert(generated, next_term)
            next_plan_rev = M.Pair(action, self._state_plan(state))
            self._record_prompt_generated_one()
            if self._goal_reached(next_term, goal) is M.truth_value:
                self._stage_debug(
                    "goal reached directly via theorem="
                    + _debug_term(rule, self.registry)
                    + "; "
                    + self._state_transition_text(state, action, next_term)
                )
                return self._advance_result(self._reverse(next_plan_rev, M.EmptyList), M.EmptyList, M.EmptyList, M.one)

            next_steps_pair = M.NatPred(self._state_steps_remaining(state), self.registry)()
            next_steps = M.Head(next_steps_pair)()
            self.registry = M.Head(M.Tail(next_steps_pair)())()
            child = self._make_state(next_term, next_plan_rev, M.Pair(current, self._state_seen(state)), next_steps)
            continuation = self._state_with_cursor(state, SearchTheoremCursor(rest_rules, next_generated)())
            return self._advance_result(M.EmptyList, child, continuation, M.one)

        if IsKnowledge(current)() is M.truth_value:
            self._stage_debug("knowledge state with no rewrite branch")
            return self._advance_result(M.EmptyList, M.EmptyList, M.EmptyList, M.Zero)
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
        self._stage_debug(
            "trying rewrite; "
            + self._state_progress_text(state)
            + " goal="
            + _debug_term(goal, self.registry)
            + " focus="
            + _debug_term(subterm, self.registry)
            + " action="
            + PrettyAction(action, self.registry)()
        )
        next_term = RewriteAtPath(active_rule, current, path, self.registry)()
        next_term = self._canonical_term(next_term)
        if M.TermEqual(next_term, current)() is M.truth_value:
            return self._advance_rewrite_cursor(state, next_cursor, goal)
        if self._tree_contains(generated, next_term) is M.truth_value:
            return self._advance_rewrite_cursor(state, next_cursor, goal)

        self._stage_debug("advanced via rewrite; " + self._state_transition_text(state, action, next_term))
        next_generated = self._tree_insert(generated, next_term)
        self._record_prompt_generated_one()
        next_plan_rev = M.Pair(action, self._state_plan(state))
        if self._goal_reached(next_term, goal) is M.truth_value:
            self._stage_debug("goal reached directly via rewrite; " + self._state_transition_text(state, action, next_term))
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
            self._stage_debug(
                self._state_progress_text(state)
                + " goal="
                + _debug_term(goal, self.registry)
                + " steps="
                + self._nat_text(self._state_steps_remaining(state))
            )
            self._record_prompt_expansion()
            if self._checkpoint_state_cursor(state, M.EmptyList) is M.truth_value:
                return self._advance_result(M.EmptyList, M.EmptyList, M.EmptyList, M.Zero)
            if self._goal_reached(current, goal) is M.truth_value:
                self._stage_debug("goal already reached")
                return self._advance_result(self._reverse(plan_rev, M.EmptyList), M.EmptyList, M.EmptyList, M.Zero)
            cached_solution = self._cached_solution(current, goal, plan_rev, self._state_steps_remaining(state))
            if M.Compare(cached_solution, M.EmptyList)() is not M.truth_value:
                return self._advance_result(cached_solution, M.EmptyList, M.EmptyList, M.Zero)
            if M.NatEq(self._state_steps_remaining(state), M.Zero, self.registry)() is M.truth_value:
                self._stage_debug("exhausted step budget")
                return self._advance_result(M.EmptyList, M.EmptyList, M.EmptyList, M.Zero)
            if self._seen_term(self._state_seen(state), current) is M.truth_value:
                self._stage_debug("seen current before, pruning")
                return self._advance_result(M.EmptyList, M.EmptyList, M.EmptyList, M.Zero)
            cursor = SearchTheoremCursor(self._theorem_rules_for(current, goal), M.EmptyList)()
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
        frontier = SearchJobFrontier(self.job)()
        mode = HeuristicSearchMode(SearchJobHeuristic(self.job)())()
        visited = self._initialize_job_visited(mode, frontier, SearchJobVisited(self.job)())

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

        kernel = _SearchStepKernel(
            self.graph,
            self.job,
            SearchJobRules(self.job)(),
            SearchJobHeuristic(self.job)(),
            SearchJobGoal(self.job)(),
            self.registry,
            self.stop_listener,
            self.progress_owner,
        )
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
