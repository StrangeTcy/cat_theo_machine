from __future__ import annotations

from .. import machine as M
from ..labels import *
from .model import *


class _ComparisonStateMixin:
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





def sync_from_namespace(namespace):
    for name in (
        "SearchSuccessLabel",
        "SearchFailureLabel",
        "SearchRunningLabel",
        "SearchPausedLabel",
        "SearchRootFastPathPhaseLabel",
        "SearchPacketSearchPhaseLabel",
    ):
        if name in namespace:
            globals()[name] = namespace[name]


__all__ = [name for name in globals() if not name.startswith("_") or name.startswith("_ComparisonStateMixin")]
