from __future__ import annotations

import queue
import time

from .. import machine as M
from .. import proof as Pmod
from ..heuristics import *
from ..labels import *
from ..proof import *
from ..proof import _debug, _debug_term
from .engine import *
from .engine import _SearchStepKernel
from .model import *


class _ComparisonPacketMixin:
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


def sync_from_namespace(namespace):
    for name in (
        "DFSLabel",
        "BFSLabel",
        "BeamLabel",
        "AStarLabel",
        "RewriteDFSLabel",
        "GoalHeadOrderLabel",
        "SearchJobLabel",
        "SearchSuccessLabel",
        "SearchFailureLabel",
        "SearchRunningLabel",
        "SearchPacketSearchPhaseLabel",
        "SearchTheoremCursorLabel",
        "SearchRewriteCursorLabel",
        "SearchRootRulePacketLabel",
        "SearchFrontierStatePacketLabel",
    ):
        if name in namespace:
            globals()[name] = namespace[name]


__all__ = [name for name in globals() if not name.startswith("_") or name.startswith("_ComparisonPacketMixin")]
