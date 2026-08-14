from __future__ import annotations

from .. import machine as M
from ..heuristics import *
from ..proof import *
from ..proof import _debug
from .model import *


class _ComparisonRuleMatchMixin:
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



def sync_from_namespace(namespace):
    for name in (
        "SearchSuccessLabel",
        "SearchFailureLabel",
        "SearchRootCacheResultLabel",
        "SearchRootSchemaResultLabel",
        "SearchRootGoalResultLabel",
        "SearchRootImmediateResultLabel",
        "SearchNoRootFastPathLabel",
        "BFSLabel",
    ):
        if name in namespace:
            globals()[name] = namespace[name]


__all__ = [name for name in globals() if not name.startswith("_") or name.startswith("_ComparisonRuleMatchMixin")]
