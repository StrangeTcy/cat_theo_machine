from __future__ import annotations

from .. import machine as M
from .. import labels as Lmod
from .. import proof as Pmod
from ..labels import *
from ..proof import *
from ..proof import _debug_term
from .model import *


class _ComparisonSemanticMixin:
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



def sync_from_namespace(namespace):
    for name in (
        "SearchRunningLabel",
        "SearchRootFastPathPhaseLabel",
        "SearchPacketSearchPhaseLabel",
        "SearchNoRootFastPathLabel",
        "SearchRootCacheResultLabel",
        "SearchRootSchemaResultLabel",
        "SearchRootGoalResultLabel",
        "SearchRootImmediateResultLabel",
        "SearchTheoremCursorLabel",
    ):
        if name in namespace:
            globals()[name] = namespace[name]


__all__ = [name for name in globals() if not name.startswith("_") or name.startswith("_ComparisonSemanticMixin")]
