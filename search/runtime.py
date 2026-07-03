from __future__ import annotations

import copyreg
import multiprocessing
import queue
import sys
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
from .model import *
from .patricia import *
from .engine import SearchBurst
class _SearchWorkerRuntime:
    def __init__(self, constructor_registry, search_memo):
        self._search_console_input = None
        self._search_disable_console = M.truth_value
        self._search_stop_help_shown = M.truth_value
        self._search_comparison_prompt_guard = None
        self._search_compare_ignore_root_fast_paths = M.false_value
        self._search_compare_root_start = M.EmptyList
        self._search_compare_root_goal = M.EmptyList
        self._search_compare_discovery_mode = M.false_value
        self._last_search_comparison_outcome = SearchSuccessLabel
        self.context = Ctxmod.Context(
            constructor_registry,
            M.EmptyList,
            M.EmptyList,
            M.EmptyList,
            M.EmptyList,
            M.Tree(M.EmptyList),
            M.Zero,
            M.EmptyList,
            M.Tree(M.EmptyList),
            M.Tree(M.EmptyList),
            M.EmptyList,
            M.EmptyList,
            M.EmptyList,
            M.EmptyList,
            search_memo,
            M.Tree(M.EmptyList),
        )
        self.constructor_registry = Ctxmod.ContextConstructors(self.context)()
        self.derivations = Ctxmod.ContextDerivations(self.context)()
        self.derivation_schemata = Ctxmod.ContextDerivationSchemata(self.context)()
        self.search_memo = Ctxmod.ContextSearchMemo(self.context)()
        self.nat_value_index = Ctxmod.ContextNatValueIndex(self.context)()
        M.AllConstructors = M.set_all_constructors(self.constructor_registry)
        M.NatValueIndex = self.nat_value_index

    def _replace_context(
        self,
        constructors=Ctxmod.ReplaceContext.KEEP,
        derivations=Ctxmod.ReplaceContext.KEEP,
        derivation_schemata=Ctxmod.ReplaceContext.KEEP,
        search_memo=Ctxmod.ReplaceContext.KEEP,
    ):
        self.context = Ctxmod.ReplaceContext(
            self.context,
            constructors=constructors,
            derivations=derivations,
            derivation_schemata=derivation_schemata,
            search_memo=search_memo,
        )()
        self.constructor_registry = Ctxmod.ContextConstructors(self.context)()
        self.derivations = Ctxmod.ContextDerivations(self.context)()
        self.derivation_schemata = Ctxmod.ContextDerivationSchemata(self.context)()
        self.search_memo = Ctxmod.ContextSearchMemo(self.context)()
        self.nat_value_index = Ctxmod.ContextNatValueIndex(self.context)()
        M.AllConstructors = M.set_all_constructors(self.constructor_registry)
        M.NatValueIndex = self.nat_value_index
        return self.context

    def lookup_derivation(self, start, goal):
        return Pmod.LookupDerivation(start, goal, self.derivations)()

    def add_derivation(self, start, goal, derivation):
        cached = self.lookup_derivation(start, goal)
        if M.Compare(cached, M.EmptyList)() is M.false_value:
            return cached
        stored_pair = Pmod.StoreDerivation(start, goal, derivation, self.derivations, self.constructor_registry)()
        self._replace_context(derivations=M.Head(stored_pair)())
        return derivation

    def lookup_derivation_schema(self, start, goal):
        return Smod.LookupDerivationSchema(start, goal, self.derivation_schemata)()

    def lookup_search_memo(self, key):
        return SearchPatriciaLookupByKey(self.search_memo, key, self.constructor_registry)()

    def store_search_memo(self, key, value):
        updated = SearchPatriciaInsertByKey(self.search_memo, key, value, self.constructor_registry)()
        self._replace_context(search_memo=updated)
        return value


def _worker_packet_frontier_state(packet_descriptor):
    if M.IsPair(packet_descriptor)() is M.false_value:
        return M.EmptyList
    if M.IdentityCompare(M.Head(packet_descriptor)(), SearchFrontierStatePacketLabel)() is M.false_value:
        return M.EmptyList
    return SearchFrontierStatePacketState(packet_descriptor)()


def _worker_seeded_singleton_theorem_state(packet_descriptor):
    packet_state = _worker_packet_frontier_state(packet_descriptor)
    if M.IdentityCompare(packet_state, M.EmptyList)() is M.truth_value:
        return M.EmptyList
    cursor = SearchStateCursor(packet_state)()
    if M.IdentityCompare(cursor, M.EmptyList)() is M.truth_value:
        return M.EmptyList
    if M.IdentityCompare(M.Head(cursor)(), SearchTheoremCursorLabel)() is M.false_value:
        return M.EmptyList
    rules = SearchTheoremCursorRules(cursor)()
    if M.IdentityCompare(rules, M.EmptyList)() is M.truth_value:
        return M.EmptyList
    if M.IdentityCompare(M.Tail(rules)(), M.EmptyList)() is M.false_value:
        return M.EmptyList
    return packet_state


def _worker_is_seeded_theorem_continuation(seed_state, candidate_state):
    cursor = SearchStateCursor(candidate_state)()
    if M.IdentityCompare(cursor, M.EmptyList)() is M.truth_value:
        return M.false_value
    if M.IdentityCompare(M.Head(cursor)(), SearchTheoremCursorLabel)() is M.false_value:
        return M.false_value
    if M.IdentityCompare(SearchTheoremCursorRules(cursor)(), M.EmptyList)() is M.false_value:
        return M.false_value
    if M.TermEqual(SearchStateCurrent(seed_state)(), SearchStateCurrent(candidate_state)())() is M.false_value:
        return M.false_value
    if M.TermEqual(SearchStatePlan(seed_state)(), SearchStatePlan(candidate_state)())() is M.false_value:
        return M.false_value
    if M.TermEqual(SearchStateSeen(seed_state)(), SearchStateSeen(candidate_state)())() is M.false_value:
        return M.false_value
    return M.TermEqual(SearchStateStepsRemaining(seed_state)(), SearchStateStepsRemaining(candidate_state)())()


def _worker_filter_seeded_theorem_continuations(packet_descriptor, frontier):
    seed_state = _worker_seeded_singleton_theorem_state(packet_descriptor)
    if M.IdentityCompare(seed_state, M.EmptyList)() is M.truth_value:
        return frontier
    filtered_rev = M.EmptyList
    remaining = frontier
    while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
        candidate_state = M.Head(remaining)()
        if _worker_is_seeded_theorem_continuation(seed_state, candidate_state) is M.false_value:
            filtered_rev = M.Pair(candidate_state, filtered_rev)
        remaining = M.Tail(remaining)()
    filtered = M.EmptyList
    remaining = filtered_rev
    while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
        filtered = M.Pair(M.Head(remaining)(), filtered)
        remaining = M.Tail(remaining)()
    return filtered


class _SearchModeWorkerResult:
    def __init__(self, problem_packet, baseline):
        pid = multiprocessing.current_process().pid
        worker_started_at = time.time()
        if M.Compare(baseline, M.EmptyList)() is M.truth_value:
            raise RuntimeError("search worker baseline missing")

        packet_descriptor = SearchWorkerPacketDescriptor(problem_packet)()
        packet_search_memo = SearchWorkerPacketSearchMemo(problem_packet)()
        packet_visited = SearchWorkerPacketVisited(problem_packet)()
        packet_theorem_rule_cache = SearchWorkerPacketTheoremRuleCache(problem_packet)()
        packet_rewrite_rules = SearchWorkerPacketRewriteRules(problem_packet)()
        step_budget = SearchWorkerPacketStepBudget(problem_packet)()
        debug_trace_enabled = SearchWorkerPacketDebugTrace(problem_packet)()
        ignore_root_fast_paths = SearchWorkerPacketIgnoreRootFastPaths(problem_packet)()
        discovery_mode = SearchWorkerPacketDiscoveryMode(problem_packet)()
        packet_token = SearchWorkerPacketPacketToken(problem_packet)()
        packet_generation = SearchWorkerPacketGeneration(problem_packet)()

        baseline_generation = SearchWorkerBaselineGeneration(baseline)()
        if M.TermEqual(packet_generation, baseline_generation)() is M.false_value:
            raise RuntimeError("search worker baseline generation mismatch")

        packet_registry = SearchWorkerBaselineConstructors(baseline)()
        start = SearchWorkerBaselineStart(baseline)()
        goal = SearchWorkerBaselineGoal(baseline)()
        rules = SearchWorkerBaselineRules(baseline)()
        heuristic = SearchWorkerBaselineHeuristic(baseline)()
        rewrite_rules = packet_rewrite_rules
        if M.IdentityCompare(rewrite_rules, M.EmptyList)() is M.truth_value:
            rewrite_rules = SearchWorkerBaselineRewriteRules(baseline)()

        mode = HeuristicSearchMode(heuristic)()
        mode_text = SearchModeText(mode)()
        Pmod.SetDebugTrace(debug_trace_enabled)()

        packet_job = M.EmptyList
        if M.IsPair(packet_descriptor)() is M.truth_value:
            if M.IdentityCompare(M.Head(packet_descriptor)(), SearchJobLabel)() is M.truth_value:
                packet_job = packet_descriptor
        if M.Compare(packet_job, M.EmptyList)() is M.truth_value:
            packet_state = M.EmptyList
            if M.IdentityCompare(M.Head(packet_descriptor)(), SearchRootRulePacketLabel)() is M.truth_value:
                packet_state = SearchState(
                    start,
                    M.EmptyList,
                    M.EmptyList,
                    step_budget,
                    SearchTheoremCursor(M.Pair(SearchRootRulePacketRule(packet_descriptor)(), M.EmptyList), M.Tree(M.EmptyList))(),
                )()
            else:
                packet_state = SearchFrontierStatePacketState(packet_descriptor)()

            packet_job = SearchJob(
                start,
                goal,
                rules,
                heuristic,
                SearchRunningLabel,
                M.Pair(packet_state, M.EmptyList),
                M.Zero,
                M.Zero,
                M.Zero,
                M.EmptyList,
                packet_visited,
                packet_theorem_rule_cache,
                rewrite_rules,
                M.one,
            )()

        graph = _SearchWorkerRuntime(packet_registry, packet_search_memo)
        graph._search_disable_console = M.truth_value
        graph._search_stop_help_shown = M.truth_value
        graph._search_comparison_prompt_guard = None
        graph._search_compare_ignore_root_fast_paths = ignore_root_fast_paths
        graph._search_compare_root_start = start
        graph._search_compare_root_goal = goal
        graph._search_compare_discovery_mode = discovery_mode
        graph._last_search_comparison_outcome = SearchSuccessLabel

        job = packet_job
        burst_pair = SearchBurst(graph, job, step_budget, M.FromContextGetConstructors(graph)())()
        job = M.Head(burst_pair)()
        registry = M.Head(M.Tail(burst_pair)())()
        graph._replace_context(constructors=registry)
        status = SearchJobStatus(job)()

        plan = SearchJobResultPlan(job)()
        if M.IdentityCompare(status, SearchSuccessLabel)() is M.false_value:
            plan = M.EmptyList

        total_value = M.Zero
        proof_value = M.Zero
        search_value = M.Zero
        expanded = SearchJobExpanded(job)()
        generated = SearchJobGenerated(job)()
        frontier_peak = SearchJobFrontierPeak(job)()
        found_depth = M.Zero
        if M.IdentityCompare(status, SearchSuccessLabel)() is M.truth_value:
            search_cost_pair = BuildSearchCost(
                plan,
                SearchJobExpanded(job)(),
                SearchJobGenerated(job)(),
                SearchJobFrontierPeak(job)(),
                status,
                registry,
            )()
            search_cost = M.Head(search_cost_pair)()
            registry = M.Head(M.Tail(search_cost_pair)())()
            graph._replace_context(constructors=registry)

            proof_cost = ProofCost(M.Zero, M.Zero, M.Zero, M.Zero)()
            derivation_pair = BuildDerivation(start, plan, registry)()
            derivation = M.Head(derivation_pair)()
            registry = M.Head(M.Tail(derivation_pair)())()
            if M.Compare(derivation, M.EmptyList)() is M.false_value:
                proof_cost_pair = DerivationCost(derivation, registry)()
                proof_cost = M.Head(proof_cost_pair)()
                registry = M.Head(M.Tail(proof_cost_pair)())()

            total_cost_pair = BuildTotalCost(proof_cost, search_cost, heuristic, registry)()
            total_cost = M.Head(total_cost_pair)()
            registry = M.Head(M.Tail(total_cost_pair)())()
            graph._replace_context(constructors=registry)

            total_value = TotalCostValue(total_cost)()
            proof_value = Pmod.ProofCostValue(proof_cost)()
            search_value = SearchCostValue(search_cost)()
            expanded = SearchCostExpanded(search_cost)()
            generated = SearchCostGenerated(search_cost)()
            frontier_peak = SearchCostFrontierPeak(search_cost)()
            found_depth = SearchCostFoundDepth(search_cost)()
        finished_frontier_rep = M.NatRepOf(SearchJobFrontierSize(job)(), registry)()
        finished_expanded_rep = M.NatRepOf(SearchJobExpanded(job)(), registry)()
        finished_generated_rep = M.NatRepOf(SearchJobGenerated(job)(), registry)()
        finished_peak_rep = M.NatRepOf(SearchJobFrontierPeak(job)(), registry)()
        finished_frontier_text = (
            Gmpmod.GMPRepText(finished_frontier_rep)()
            if M.IdentityCompare(finished_frontier_rep, M.EmptyList)() is M.false_value
            else M.PrettyTerm(SearchJobFrontierSize(job)(), registry)()
        )
        finished_expanded_text = (
            Gmpmod.GMPRepText(finished_expanded_rep)()
            if M.IdentityCompare(finished_expanded_rep, M.EmptyList)() is M.false_value
            else M.PrettyTerm(SearchJobExpanded(job)(), registry)()
        )
        finished_generated_text = (
            Gmpmod.GMPRepText(finished_generated_rep)()
            if M.IdentityCompare(finished_generated_rep, M.EmptyList)() is M.false_value
            else M.PrettyTerm(SearchJobGenerated(job)(), registry)()
        )
        finished_peak_text = (
            Gmpmod.GMPRepText(finished_peak_rep)()
            if M.IdentityCompare(finished_peak_rep, M.EmptyList)() is M.false_value
            else M.PrettyTerm(SearchJobFrontierPeak(job)(), registry)()
        )

        returned_search_memo = M.EmptyList
        current_search_memo = M.FromContextGetSearchMemo(graph)()
        if M.Compare(current_search_memo, packet_search_memo)() is M.false_value:
            returned_search_memo = SearchTreeDelta(current_search_memo, packet_search_memo, registry)()

        returned_visited = M.EmptyList
        current_visited = SearchJobVisited(job)()
        if M.Compare(current_visited, packet_visited)() is M.false_value:
            returned_visited = SearchTreeDelta(current_visited, packet_visited, registry)()

        returned_theorem_rule_cache = M.EmptyList
        current_theorem_rule_cache = SearchJobTheoremRuleCache(job)()
        if M.Compare(current_theorem_rule_cache, packet_theorem_rule_cache)() is M.false_value:
            returned_theorem_rule_cache = SearchTreeDelta(
                current_theorem_rule_cache,
                packet_theorem_rule_cache,
                registry,
            )()

        returned_registry = M.EmptyList
        if M.Compare(registry, packet_registry)() is M.false_value:
            returned_registry = SearchTreeDelta(registry, packet_registry, registry)()

        ready_packets = M.EmptyList
        ready_packet_count = M.Zero
        packetized_job = SearchJob(
            SearchJobStart(job)(),
            SearchJobGoal(job)(),
            SearchJobRules(job)(),
            SearchJobHeuristic(job)(),
            SearchJobStatus(job)(),
            SearchJobFrontier(job)(),
            SearchJobExpanded(job)(),
            SearchJobGenerated(job)(),
            SearchJobFrontierPeak(job)(),
            SearchJobResultPlan(job)(),
            returned_visited,
            returned_theorem_rule_cache,
            SearchJobRewriteRules(job)(),
            SearchJobFrontierSize(job)(),
        )()
        if M.IdentityCompare(discovery_mode, M.truth_value)() is M.truth_value:
            returned_frontier = SearchJobFrontier(job)()
            returned_frontier = _worker_filter_seeded_theorem_continuations(packet_descriptor, returned_frontier)
            if M.IdentityCompare(returned_frontier, M.EmptyList)() is M.false_value:
                packet_count_pair = M.Count(returned_frontier, registry)()
                ready_packet_count = M.Head(packet_count_pair)()
                registry = M.Head(M.Tail(packet_count_pair)())()
                packets_rev = M.EmptyList
                remaining_frontier = returned_frontier
                while M.IdentityCompare(remaining_frontier, M.EmptyList)() is M.false_value:
                    frontier_state = M.Head(remaining_frontier)()
                    ready_packet = SearchFrontierStatePacket(frontier_state)()
                    packets_rev = M.Pair(ready_packet, packets_rev)
                    remaining_frontier = M.Tail(remaining_frontier)()
                ready_packets = M.EmptyList
                remaining_packets_rev = packets_rev
                while M.IdentityCompare(remaining_packets_rev, M.EmptyList)() is M.false_value:
                    ready_packets = M.Pair(M.Head(remaining_packets_rev)(), ready_packets)
                    remaining_packets_rev = M.Tail(remaining_packets_rev)()
                packetized_job = SearchJob(
                    SearchJobStart(job)(),
                    SearchJobGoal(job)(),
                    SearchJobRules(job)(),
                    SearchJobHeuristic(job)(),
                    SearchJobStatus(job)(),
                    M.EmptyList,
                    SearchJobExpanded(job)(),
                    SearchJobGenerated(job)(),
                    SearchJobFrontierPeak(job)(),
                    SearchJobResultPlan(job)(),
                    returned_visited,
                    returned_theorem_rule_cache,
                    SearchJobRewriteRules(job)(),
                    M.Zero,
                )()
                _debug(
                    "search-compare: "
                    + mode_text
                    + " worker pid="
                    + str(pid)
                    + " produced a returned frontier wave with "
                    + _debug_term(ready_packet_count, registry)
                    + " ready packets"
                )

        _debug(
            "search-compare: "
            + mode_text
            + " worker pid="
            + str(pid)
            + " elapsed="
            + "{:.1f}".format(time.time() - worker_started_at)
            + "s"
            + " completed packet status="
            + SearchStatusText(status)()
            + " frontier="
            + finished_frontier_text
            + " expanded="
            + finished_expanded_text
            + " generated="
            + finished_generated_text
            + " peak="
            + finished_peak_text
            + " total="
            + _debug_term(total_value, registry)
        )

        self.result = SearchWorkerResult(
            mode,
            status,
            total_value,
            proof_value,
            search_value,
            expanded,
            generated,
            frontier_peak,
            found_depth,
            packetized_job,
            returned_search_memo,
            ready_packets,
            ready_packet_count,
            returned_registry,
            packet_token,
        )()

    def __call__(self):
        return self.result


class _SearchRootWaveShardResult:
    def __init__(self, shard_packet, baseline=M.EmptyList):
        registry = SearchRootWaveShardPacketConstructors(shard_packet)()
        if M.IdentityCompare(registry, M.EmptyList)() is M.truth_value:
            if M.Compare(baseline, M.EmptyList)() is M.truth_value:
                raise RuntimeError("search root-wave shard baseline missing")
            registry = SearchWorkerBaselineConstructors(baseline)()
        rules = SearchRootWaveShardPacketRules(shard_packet)()
        current = SearchRootWaveShardPacketCurrent(shard_packet)()
        debug_trace_enabled = SearchRootWaveShardPacketDebugTrace(shard_packet)()
        Pmod.SetDebugTrace(debug_trace_enabled)()

        applicable = FilterApplicableRules(rules, current, registry)()
        immediate_rules = M.EmptyList
        goal_rules = M.EmptyList
        other_rules = applicable

        self.result = SearchRootWaveShardResult(immediate_rules, goal_rules, other_rules)()

    def __call__(self):
        return self.result


class _SearchModeWorkerExecutor:
    def __init__(self, slot_text, task_queue, result_queue):
        pid = multiprocessing.current_process().pid
        baseline = M.EmptyList
        while M.IdentityCompare(M.truth_value, M.truth_value)() is M.truth_value:
            launch = task_queue.get()
            if launch is None:
                break
            if M.IsPair(launch)() is M.truth_value:
                if M.IdentityCompare(M.Head(launch)(), SearchWorkerSetupLabel)() is M.truth_value:
                    baseline = SearchWorkerSetupBaseline(launch)()
                    M.AllConstructors = M.set_all_constructors(SearchWorkerBaselineConstructors(baseline)())
                    continue
                if M.IdentityCompare(M.Head(launch)(), SearchRootWaveShardLaunchLabel)() is M.truth_value:
                    shard_slot = SearchRootWaveShardLaunchSlot(launch)()
                    shard_packet = SearchRootWaveShardLaunchPacket(launch)()
                    try:
                        _debug(
                            "search-compare: resident executor "
                            + slot_text
                            + " pid="
                            + str(pid)
                            + " starting root-wave shard "
                            + _debug_term(shard_slot, M.AllConstructors)
                        )
                        result_queue.put(_SearchRootWaveShardResult(shard_packet, baseline)())
                    except Exception as error:
                        import traceback

                        print(
                            "search-worker: failed root-wave shard pid="
                            + str(pid)
                            + " ("
                            + str(error)
                            + ")",
                        )
                        traceback.print_exc()
                        result_queue.put(None)
                    continue
            mode = SearchWorkerLaunchMode(launch)()
            mode_text = SearchModeText(mode)()
            branch_serial = SearchWorkerLaunchBranchSerial(launch)()
            payload = SearchWorkerLaunchPayload(launch)()
            try:
                _debug(
                    "search-compare: resident executor "
                    + slot_text
                    + " pid="
                    + str(pid)
                    + " starting "
                    + mode_text
                    + " packet "
                    + _debug_term(branch_serial, M.AllConstructors)
                )
                result_queue.put(_SearchModeWorkerResult(payload, baseline)())
            except Exception as error:
                import traceback
                print(
                    "search-worker: failed "
                    + mode_text
                    + " pid="
                    + str(pid)
                    + " ("
                    + str(error)
                    + ")",
                )
                traceback.print_exc()
                result_queue.put(None)



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
