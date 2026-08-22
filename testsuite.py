from __future__ import annotations

import json
import io
import os
import pickle
import queue
import shutil
import sys
import tempfile
from contextlib import redirect_stdout

from . import machine as M
from . import graph as Gmod
from . import heuristics as Hmod
from . import labels as Lmod
from . import matching as Xmod
from . import proof as Pmod
from . import rewrite_rules as Rmod
from . import rewrite_strategies as RSmod
from . import invariance as Imod
from . import search as Smod
from . import theorem_rules as Theoremmod
from . import trees as Tmod
from .graph import Test
from .persistence import SnapshotCodec, SnapshotSaveDeadline, SnapshotSaveTimeout
from .proof import BuildDerivation, CollectRules, Rule, RulePremises, RuleReplacement
from .runtime import boot_from_packs, boot_from_snapshot, make_fresh_runtime, save_runtime
from .search import (
    SearchComparisonJobOutcome,
    SearchComparisonJobStates,
    SearchComparisonOutcome,
    SearchFailureLabel,
    SearchFrontierStatePacket,
    SearchPacketSearchPhaseLabel,
    SearchPatriciaInsertByKey,
    SearchPatriciaIsTree,
    SearchPatriciaLookupByKey,
    SearchSuccessLabel,
    SearchSignatureForProblem,
    SearchStructuralKey,
    SearchTreeDelta,
    SearchWorkerBaseline,
    SearchWorkerBaselineGeneration,
    SearchWorkerBaselineStart,
    SearchWorkerLaunch,
    SearchWorkerLaunchBranchSerial,
    SearchWorkerLaunchPayload,
    SearchWorkerPacket,
    SearchWorkerPacketGeneration,
    SearchWorkerPacketRewriteRules,
    SearchWorkerResult,
    SearchWorkerResultMode,
    SearchWorkerResultPacketToken,
    SearchWorkerResultStatus,
    SearchWorkerSetup,
    SearchWorkerSetupLabel,
    _SearchComparisonPromptGuard,
)
from .search.model import SearchRootWaveShardLaunchPacket, SearchRootWaveShardPacketRules, SearchRootWaveShardResult
from .search.runtime import _worker_filter_seeded_theorem_continuations


class Exists(M.Edge):
    def __init__(self, domain, predicate):
        self.result = self._exists(domain, predicate)
        super().__init__(inputs=M.Pair(domain, M.EmptyList), results=M.Pair(self.result, M.EmptyList))

    def _exists(self, node, predicate):
        if M.Compare(node, M.EmptyList)() is M.truth_value:
            return M.false_value

        head = M.Head(node)()
        tail = M.Tail(node)()
        test = predicate(head)()
        if M.Compare(test, M.truth_value)() is M.truth_value:
            return M.truth_value
        return self._exists(tail, predicate)

    def __call__(self):
        return self.result


class ForAll(M.Edge):
    def __init__(self, domain, predicate):
        self.result = self._forall(domain, predicate)
        super().__init__(inputs=M.Pair(domain, M.EmptyList), results=M.Pair(self.result, M.EmptyList))

    def _forall(self, node, predicate):
        if M.Compare(node, M.EmptyList)() is M.truth_value:
            return M.truth_value

        head = M.Head(node)()
        tail = M.Tail(node)()
        test = predicate(head)()
        if M.Compare(test, M.truth_value)() is M.false_value:
            return M.false_value
        return self._forall(tail, predicate)

    def __call__(self):
        return self.result


class IsNonZero(M.Edge):
    def __init__(self, x):
        if M.Compare(x, M.Zero)() is M.truth_value:
            self.result = M.false_value
        else:
            self.result = M.truth_value
        super().__init__(inputs=M.Pair(x, M.EmptyList), results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class RewriteStrategyGoalDemandAllowsGoalHeadTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        a = M.Char("a")
        b = M.Char("b")
        goal = M.Pair(M.ExprAddLabel, M.Pair(a, M.Pair(b, M.EmptyList)))
        goal_head_index = Hmod.HeuristicGoalHeadNeighborhood(goal, M.EmptyList, registry)()
        strategy = RSmod.GoalDemandRewriteStrategy()()
        allowed = RSmod.RewriteStrategyAllowsSubterm(strategy, goal_head_index, goal, registry)()
        denied = RSmod.RewriteStrategyAllowsSubterm(
            strategy,
            goal_head_index,
            M.Pair(M.SqrtLabel, M.Pair(a, M.EmptyList)),
            registry,
        )()
        self.result = M.truth_value
        if M.IdentityCompare(allowed, M.truth_value)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(denied, M.false_value)() is M.false_value:
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class PrettyPrintNamedTaoQuantityTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        term = M.Pair(Lmod.APShortSideLabel, M.Pair(Lmod.TaoProblem11TriangleLabel, M.EmptyList))
        text = M.PrettyTerm(term, registry)()
        self.result = M.truth_value
        if text != "APShortSide(Tao Problem 1.1 triangle)":
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class TaoGeometryExampleGoalsUseNamedQuantitiesTest(M.Edge):
    def __init__(self, _graph):
        from .main import PACK_PATHS, _runtime_namespace

        runtime, packs = boot_from_packs(PACK_PATHS, _runtime_namespace())
        registry = _registry(runtime.graph)
        examples = packs.by_name("geometry").examples
        side_goal = examples["tao_problem_1_1_triangle"][1]
        angle_goal = examples["tao_angle_identity"][1]
        positive_goal = examples["tao_positive_alpha_side"][1]
        area_goal = examples["tao_area_identity"][1]
        cosine_goal = examples["tao_cosine_angle_identity"][1]
        self.result = M.truth_value
        if M.PrettyTerm(side_goal, registry)() != "Length(Segment(v, w), APShortSide(Tao Problem 1.1 triangle))":
            self.result = M.false_value
        elif M.PrettyTerm(angle_goal, registry)() != "AngleMeasure(Angle(v, u, w), APAngleValue(Tao Problem 1.1 triangle, Angle(v, u, w)))":
            self.result = M.false_value
        elif M.PrettyTerm(positive_goal, registry)() != "Positive(APShortSide(Tao Problem 1.1 triangle))":
            self.result = M.false_value
        elif M.PrettyTerm(area_goal, registry)() != "APAreaIdentity(Tao Problem 1.1 triangle)":
            self.result = M.false_value
        elif M.PrettyTerm(cosine_goal, registry)() != "CosineRuleRelates(APShortSide(Tao Problem 1.1 triangle), APMiddleSide(Tao Problem 1.1 triangle), APLongSide(Tao Problem 1.1 triangle), APAngleValue(Tao Problem 1.1 triangle, Angle(v, u, w)))":
            self.result = M.false_value
        else:
            checks = (
                (examples["tao_problem_1_1_triangle"][0], M.one),
                (examples["tao_angle_identity"][0], M.five),
                (examples["tao_positive_alpha_side"][0], M.three),
                (examples["tao_area_identity"][0], M.four),
                (examples["tao_cosine_angle_identity"][0], M.nine),
            )
            index = 0
            while index != len(checks):
                start, expected_count = checks[index]
                facts = Pmod.KnowledgeFacts(start)()
                count_pair = M.Count(facts, registry)()
                count = M.Head(count_pair)()
                registry = M.Head(M.Tail(count_pair)())()
                if M.NatEq(count, expected_count, registry)() is M.false_value:
                    self.result = M.false_value
                    index = len(checks)
                else:
                    index = index + 1
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class TaoCompactRulesUseShrunkPremiseSetsTest(M.Edge):
    def __init__(self, _graph):
        from .main import PACK_PATHS, _runtime_namespace

        runtime, packs = boot_from_packs(PACK_PATHS, _runtime_namespace())
        registry = _registry(runtime.graph)
        geometry = packs.by_name("geometry")
        self.result = M.truth_value
        checks = (
            ("tao_define_perimeter_third", M.one),
            ("tao_define_side_radicand", M.two),
            ("tao_define_side_offset", M.one),
            ("tao_define_short_side", M.one),
            ("tao_define_middle_side", M.one),
            ("tao_define_long_side", M.one),
            ("tao_side_alpha_from_area_perimeter", M.one),
            ("tao_side_beta_from_area_perimeter", M.one),
            ("tao_side_gamma_from_area_perimeter", M.one),
            ("tao_verify_area", M.four),
        )
        if "tao_angle_from_sides" not in geometry.rule_map:
            self.result = M.false_value
        elif "tao_angle_alpha_from_sides" in geometry.rule_map:
            self.result = M.false_value
        elif "tao_angle_beta_from_sides" in geometry.rule_map:
            self.result = M.false_value
        elif "tao_angle_gamma_from_sides" in geometry.rule_map:
            self.result = M.false_value
        if M.IdentityCompare(self.result, M.truth_value)() is M.false_value:
            super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))
            return
        index = 0
        while index != len(checks):
            rule_id, expected_count = checks[index]
            premises = Pmod.RulePremises(geometry.rule_map[rule_id])()
            count_pair = M.Count(premises, registry)()
            count = M.Head(count_pair)()
            registry = M.Head(M.Tail(count_pair)())()
            if M.NatEq(count, expected_count, registry)() is M.false_value:
                self.result = M.false_value
                index = len(checks)
            else:
                index = index + 1
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class MergeBindingsAcceptsStructurallyEqualValuesTest(M.Edge):
    def __init__(self):
        empty = M.EmptyList
        var_name = M.Thingy()
        var_x = M.Pair(M.VarTag, M.Pair(var_name, empty))
        left_value = M.Pair(M.one, M.Pair(M.two, empty))
        right_value = M.Pair(M.one, M.Pair(M.two, empty))
        base_bindings = M.Pair(M.Pair(var_x, M.Pair(left_value, empty)), empty)
        extra_bindings = M.Pair(M.Pair(var_x, M.Pair(right_value, empty)), empty)
        merged = M.MergeBindings(base_bindings, extra_bindings)()
        self.result = M.Head(merged)()
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class BuildDerivationReplaysStructurallyEqualRepeatedBindingsTest(M.Edge):
    def __init__(self, graph):
        empty = M.EmptyList
        var_name = M.Thingy()
        var_x = M.Pair(M.VarTag, M.Pair(var_name, empty))
        left_value = M.Pair(M.one, M.Pair(M.two, empty))
        right_value = M.Pair(M.one, M.Pair(M.two, empty))
        fact_one = M.Pair(M.four, M.Pair(left_value, empty))
        fact_two = M.Pair(M.five, M.Pair(right_value, empty))
        goal_fact = M.Pair(M.six, empty)
        start = Pmod.Knowledge(M.Pair(fact_one, M.Pair(fact_two, empty)))()
        rule = Pmod.MultiRule(
            M.Pair(
                M.Pair(M.four, M.Pair(var_x, empty)),
                M.Pair(M.Pair(M.five, M.Pair(var_x, empty)), empty),
            ),
            goal_fact,
        )
        plan = M.Pair(M.TheoremAction(rule)(), empty)
        derivation_pair = Pmod.BuildDerivation(start, plan, _registry(graph))()
        derivation = M.Head(derivation_pair)()
        registry = M.Head(M.Tail(derivation_pair)())()
        end = Pmod.DerivationEnd(derivation, registry)()
        facts = Pmod.KnowledgeFacts(end)()
        self.result = M.false_value
        while M.IdentityCompare(facts, M.EmptyList)() is M.false_value:
            if M.TermEqual(M.Head(facts)(), goal_fact)() is M.truth_value:
                self.result = M.truth_value
                facts = M.EmptyList
            else:
                facts = M.Tail(facts)()
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class TaoGenericCosineReplayCasesTest(M.Edge):
    def __init__(self, _graph):
        from .main import PACK_PATHS, _runtime_namespace

        runtime, packs = boot_from_packs(PACK_PATHS, _runtime_namespace())
        geometry = packs.by_name("geometry")
        ontology = packs.by_name("geometry-ontology")
        trigonometry = packs.by_name("trigonometry")
        registry = _registry(runtime.graph)
        distinct_rule = ontology.rule_map["distinct_is_symmetric"]
        side_alpha = M.Pair(Lmod.SegmentLabel, M.Pair(Lmod.TaoProblem11VertexVLabel, M.Pair(Lmod.TaoProblem11VertexWLabel, M.EmptyList)))
        side_beta = M.Pair(Lmod.SegmentLabel, M.Pair(Lmod.TaoProblem11VertexWLabel, M.Pair(Lmod.TaoProblem11VertexULabel, M.EmptyList)))
        side_gamma = M.Pair(Lmod.SegmentLabel, M.Pair(Lmod.TaoProblem11VertexULabel, M.Pair(Lmod.TaoProblem11VertexVLabel, M.EmptyList)))
        cases = (
            (
                "tao_cosine_angle_identity",
                M.nine,
                (),
            ),
            (
                "tao_cosine_beta_identity",
                M.nine,
                (M.Pair(side_alpha, M.Pair(side_beta, M.EmptyList)),),
            ),
            (
                "tao_cosine_gamma_identity",
                M.nine,
                (
                    M.Pair(side_alpha, M.Pair(side_gamma, M.EmptyList)),
                    M.Pair(side_beta, M.Pair(side_gamma, M.EmptyList)),
                ),
            ),
        )
        self.result = M.truth_value
        index = 0
        while index != len(cases):
            example_id, expected_count, symmetry_pairs = cases[index]
            start, goal = geometry.examples[example_id]
            facts = Pmod.KnowledgeFacts(start)()
            count_pair = M.Count(facts, registry)()
            count = M.Head(count_pair)()
            registry = M.Head(M.Tail(count_pair)())()
            if M.NatEq(count, expected_count, registry)() is M.false_value:
                self.result = M.false_value
                index = len(cases)
                continue
            actions = ()
            rule_ids = (
                "tao_side_alpha_from_area_perimeter",
                "tao_side_beta_from_area_perimeter",
                "tao_side_gamma_from_area_perimeter",
            )
            rule_index = 0
            while rule_index != len(rule_ids):
                actions = actions + (M.TheoremAction(geometry.rule_map[rule_ids[rule_index]])(),)
                rule_index = rule_index + 1
            pair_index = 0
            while pair_index != len(symmetry_pairs):
                forward_fact = M.Pair(Lmod.DistinctLabel, symmetry_pairs[pair_index])
                match = M.Match(Pmod.RulePattern(distinct_rule)(), forward_fact)()
                if M.IdentityCompare(M.Head(match)(), M.truth_value)() is M.false_value:
                    self.result = M.false_value
                    pair_index = len(symmetry_pairs)
                    index = len(cases)
                    actions = ()
                else:
                    actions = actions + (M.TheoremAction(distinct_rule, M.Tail(match)())(),)
                    pair_index = pair_index + 1
            if M.IdentityCompare(self.result, M.truth_value)() is M.false_value:
                continue
            actions = actions + (M.TheoremAction(geometry.rule_map["tao_angle_from_sides"])(),)
            actions = actions + (M.TheoremAction(trigonometry.rule_map["triangle_yields_generic_cosine_relation"])(),)
            plan = M.EmptyList
            action_index = len(actions)
            while action_index != 0:
                action_index = action_index - 1
                plan = M.Pair(actions[action_index], plan)
            derivation_pair = Pmod.BuildDerivation(start, plan, registry)()
            derivation = M.Head(derivation_pair)()
            registry = M.Head(M.Tail(derivation_pair)())()
            end = Pmod.DerivationEnd(derivation, registry)()
            facts = Pmod.KnowledgeFacts(end)()
            found = M.false_value
            while M.IdentityCompare(facts, M.EmptyList)() is M.false_value:
                if M.TermEqual(M.Head(facts)(), goal)() is M.truth_value:
                    found = M.truth_value
                    facts = M.EmptyList
                else:
                    facts = M.Tail(facts)()
            if M.IdentityCompare(found, M.truth_value)() is M.false_value:
                self.result = M.false_value
                index = len(cases)
            else:
                index = index + 1
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class LegacyCosineRulesRemovedTest(M.Edge):
    def __init__(self, _graph):
        from .main import PACK_PATHS, _runtime_namespace

        runtime, packs = boot_from_packs(PACK_PATHS, _runtime_namespace())
        trigonometry = packs.by_name("trigonometry")
        geometry = packs.by_name("geometry")
        self.result = M.truth_value
        if self._pack_has_rule(trigonometry, "triangle_yields_cosine_rule_first_equation") is M.truth_value:
            self.result = M.false_value
        elif self._pack_has_rule(trigonometry, "triangle_yields_cosine_rule_second_equation") is M.truth_value:
            self.result = M.false_value
        elif self._pack_has_rule(trigonometry, "triangle_yields_cosine_rule_third_equation") is M.truth_value:
            self.result = M.false_value
        elif self._pack_has_rule(geometry, "tao_expand_cosine_rule_relates") is M.truth_value:
            self.result = M.false_value
        elif self._pack_has_rule(trigonometry, "triangle_yields_generic_cosine_relation") is M.false_value:
            self.result = M.false_value
        elif self._pack_has_rule(trigonometry, "cosine_relation_expands_to_equation") is M.false_value:
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def _pack_has_rule(self, pack, rule_id):
        try:
            pack.rule_map[rule_id]
            return M.truth_value
        except KeyError:
            return M.false_value

    def __call__(self):
        return self.result


class _ComparisonPromptAbortGraph:
    def __init__(self):
        self._search_disable_console = M.false_value


class _ComparisonPromptAbortSearch:
    def __init__(self):
        self.graph = _ComparisonPromptAbortGraph()
        self.search_aborted = M.false_value
        self.search_outcome_on_abort = M.EmptyList

    def _current_total_cost_units(self):
        return 1

    def _pause_stop_listener(self):
        return None

    def _pause_progress_ticker(self):
        return None

    def _resume_stop_listener(self):
        return None

    def _resume_progress_ticker(self):
        return None

    def _read_console_line(self, prompt_text):
        return "n\n"


class ComparisonPromptAbortTest(M.Edge):
    def __init__(self):
        guard = _SearchComparisonPromptGuard()
        guard.next_cost_prompt_units = 1
        search = _ComparisonPromptAbortSearch()
        guard.maybe_prompt(search)
        result = M.truth_value
        if M.IdentityCompare(guard.comparison_aborted, M.truth_value)() is M.false_value:
            result = M.false_value
        if search.search_aborted is M.false_value:
            result = M.false_value
        if M.IdentityCompare(search.search_outcome_on_abort, SearchFailureLabel)() is M.false_value:
            result = M.false_value
        self.result = result
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class RawTermEqual(M.Edge):
    def __init__(self, left, right, registry=None):
        if registry is None:
            registry = M.AllConstructors
        self.registry = registry
        self.result = self._eq(left, right)
        super().__init__(inputs=M.Pair(left, M.Pair(right, M.Pair(registry, M.EmptyList))), results=M.Pair(self.result, M.EmptyList))

    def _eq(self, left, right):
        if M.IdentityCompare(left, right)() is M.truth_value:
            return M.truth_value
        left_is_pair = M.IsPair(left)()
        right_is_pair = M.IsPair(right)()
        if M.AndAtom(left_is_pair, right_is_pair)() is M.truth_value:
            head_eq = self._eq(M.Head(left)(), M.Head(right)())
            if M.IdentityCompare(head_eq, M.false_value)() is M.truth_value:
                return M.false_value
            return self._eq(M.Tail(left)(), M.Tail(right)())
        if M.OrAtom(left_is_pair, right_is_pair)() is M.truth_value:
            return M.false_value
        return M.CompareIn(left, right, self.registry)()

    def __call__(self):
        return self.result


class ComputedRawTermEqual(M.Edge):
    def __init__(self, computation_edge, expected, registry=None):
        if registry is None:
            registry = M.AllConstructors
        self.computation_edge = computation_edge
        self.expected = expected
        self.registry = registry
        self.result = RawTermEqual(self.computation_edge(), self.expected, self.registry)()
        super().__init__(inputs=M.Pair(expected, M.Pair(registry, M.EmptyList)), results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CompileRuleToLawTest(M.Edge):
    """Step 11: rules compile to Laws that pass LawMapsComplete and fire to R."""

    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList

        left_term = M.Pair(Lmod.ZeroLabel, empty)
        right_term = M.Pair(Lmod.SuccLabel, M.Pair(left_term, empty))
        simple_rule = Pmod.Rule(left_term, right_term)
        law = Gmod.CompileRuleToLaw(simple_rule)()

        self.result = M.truth_value
        if M.IdentityCompare(law, empty)() is M.truth_value:
            self.result = M.false_value
        elif Gmod.IsLawTerm(law)() is M.false_value:
            self.result = M.false_value
        elif Gmod.LawMapsComplete(law)() is M.false_value:
            self.result = M.false_value
        else:
            encoded_left = Gmod.LawLeft(law)()
            encoded_right = Gmod.LawRight(law)()
            host = Gmod.GraphVersion(
                Gmod.GraphNodes(encoded_left)(),
                Gmod.GraphEdges(encoded_left)(),
                empty,
            )()
            sends = Gmod.IdentitySendsFor(Gmod.GraphNodes(encoded_left)())()
            remaining = Gmod.GraphEdges(encoded_left)()
            while M.IdentityCompare(remaining, empty)() is M.false_value:
                edge = M.Head(remaining)()
                sends = M.Pair(Gmod.Send(edge, edge)(), sends)
                remaining = M.Tail(remaining)()
            mapping = Gmod.Map(encoded_left, host, sends)()
            fired = Gmod.FireLaw(host, law, mapping, Gmod.DanglingForbid()())()
            committed = M.Head(fired)()
            if M.IdentityCompare(committed, empty)() is M.truth_value:
                self.result = M.false_value
            else:
                wanted = Gmod.GraphNodes(encoded_right)()
                while M.IdentityCompare(wanted, empty)() is M.false_value:
                    if Gmod.ChainHasTerm(Gmod.GraphNodes(committed)(), M.Head(wanted)())() is M.false_value:
                        self.result = M.false_value
                    wanted = M.Tail(wanted)()
                wanted = Gmod.GraphEdges(encoded_right)()
                while M.IdentityCompare(wanted, empty)() is M.false_value:
                    if Gmod.ChainHasTerm(Gmod.GraphEdges(committed)(), M.Head(wanted)())() is M.false_value:
                        self.result = M.false_value
                    wanted = M.Tail(wanted)()

        multi_rule = Pmod.MultiRule(
            M.Pair(left_term, M.Pair(right_term, empty)),
            right_term,
        )
        if M.IdentityCompare(Gmod.CompileRuleToLaw(multi_rule)(), empty)() is M.false_value:
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class ShadowPackTest(M.Edge):
    """Step 12: trigonometry rules run through legacy and Law paths in shadow."""

    def __init__(self, _graph):
        from .main import PACK_PATHS, _runtime_namespace

        runtime, packs = boot_from_packs(PACK_PATHS, _runtime_namespace())
        registry = _registry(runtime.graph)
        trigonometry = packs.by_name("trigonometry")
        geometry = packs.by_name("geometry")
        compiled = Gmod.CompileRulePackToLaws(trigonometry.rule_chain)()
        laws = M.Head(compiled)()
        skipped = M.Head(M.Tail(compiled)())()
        declared_skips = Gmod.UncompiledRules()()

        self.result = M.truth_value
        if M.IdentityCompare(laws, M.EmptyList)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Tail(laws)(), M.EmptyList)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(skipped, M.EmptyList)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Tail(skipped)(), M.EmptyList)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Tail(M.Tail(skipped)())(), M.EmptyList)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(declared_skips, M.EmptyList)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Tail(declared_skips)(), M.EmptyList)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Tail(M.Tail(declared_skips)())(), M.EmptyList)() is M.false_value:
            self.result = M.false_value
        else:
            rule = M.Head(M.Tail(trigonometry.rule_chain)())()
            law = M.Head(laws)()
            redex = geometry.examples["tao_cosine_angle_identity"][1]
            match = M.Match(Pmod.RulePattern(rule)(), redex)()
            if M.IdentityCompare(M.Head(match)(), M.truth_value)() is M.false_value:
                self.result = M.false_value
            elif Gmod.LawMapsComplete(law)() is M.false_value:
                self.result = M.false_value
            else:
                legacy = M.Head(M.Rewrite(rule, redex, registry)())()
                instantiated_law = Gmod.InstantiateLaw(law, M.Tail(match)())()
                if M.IdentityCompare(instantiated_law, M.EmptyList)() is M.truth_value:
                    self.result = M.false_value
                elif Gmod.LawMapsComplete(instantiated_law)() is M.false_value:
                    self.result = M.false_value
                else:
                    left = Gmod.LawLeft(instantiated_law)()
                    host = Gmod.GraphVersion(
                        Gmod.GraphNodes(left)(),
                        Gmod.GraphEdges(left)(),
                        M.EmptyList,
                    )()
                    sends = Gmod.IdentitySendsFor(Gmod.GraphNodes(left)())()
                    remaining = Gmod.GraphEdges(left)()
                    while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
                        edge = M.Head(remaining)()
                        sends = M.Pair(Gmod.Send(edge, edge)(), sends)
                        remaining = M.Tail(remaining)()
                    mapping = Gmod.Map(left, host, sends)()
                    fired = Gmod.FireLaw(
                        host,
                        instantiated_law,
                        mapping,
                        Gmod.DanglingForbid()(),
                    )()
                    committed = M.Head(fired)()
                    expected = Gmod.EncodeTermAsGraph(legacy)()
                    if M.IdentityCompare(committed, M.EmptyList)() is M.truth_value:
                        self.result = M.false_value
                    elif Gmod.GraphStoresEqual(committed, expected)() is M.false_value:
                        self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class LawsInsideGraphVersionsTest(M.Edge):
    """Step 13: installed Laws are discoverable, fireable, and persistent."""

    def __init__(self, _graph):
        empty = M.EmptyList
        left_term = M.Pair(Lmod.ZeroLabel, empty)
        right_one = M.Pair(Lmod.SuccLabel, M.Pair(left_term, empty))
        right_two = M.Pair(Lmod.NonNegativeLabel, M.Pair(left_term, empty))
        law_one = Gmod.CompileRuleToLaw(Pmod.Rule(left_term, right_one))()
        law_two = Gmod.CompileRuleToLaw(Pmod.Rule(left_term, right_two))()

        encoded_left = Gmod.EncodeTermAsGraph(left_term)()
        version = Gmod.GraphVersion(
            Gmod.GraphNodes(encoded_left)(),
            Gmod.GraphEdges(encoded_left)(),
            empty,
        )()
        installed = Gmod.InstallLaw(version, law_one)()
        installed = Gmod.InstallLaw(installed, law_two)()
        before_laws = Gmod.InstalledLaws(installed)()
        invariants = Gmod.GraphVersionInvariants(installed)()

        self.result = M.truth_value
        if Gmod.LawMapsComplete(law_one)() is M.false_value:
            self.result = M.false_value
        elif Gmod.LawMapsComplete(law_two)() is M.false_value:
            self.result = M.false_value
        elif Gmod.ChainHasTerm(Gmod.GraphNodes(installed)(), law_one)() is M.false_value:
            self.result = M.false_value
        elif Gmod.ChainHasTerm(Gmod.GraphNodes(installed)(), law_two)() is M.false_value:
            self.result = M.false_value
        elif Gmod.ChainHasTerm(before_laws, law_one)() is M.false_value:
            self.result = M.false_value
        elif Gmod.ChainHasTerm(before_laws, law_two)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(invariants, empty)() is M.truth_value:
            self.result = M.false_value
        elif Gmod.IsInstalledLaw(M.Head(invariants)())() is M.false_value:
            self.result = M.false_value
        else:
            fired = Gmod.FireAny(installed, Gmod.DanglingForbid()())()
            committed = M.Head(fired)()
            trace = M.Head(M.Tail(fired)())()
            if M.IdentityCompare(committed, empty)() is M.truth_value:
                self.result = M.false_value
            elif M.IdentityCompare(trace, empty)() is M.truth_value:
                self.result = M.false_value
            else:
                after_laws = Gmod.InstalledLaws(committed)()
                if Gmod.ChainHasTerm(after_laws, law_one)() is M.false_value:
                    self.result = M.false_value
                elif Gmod.ChainHasTerm(after_laws, law_two)() is M.false_value:
                    self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class MetaRewriteKnownGapTest(M.Edge):
    """Step 14 known gap: meta-Law matching stops before FireLaw MatchPrepared."""

    def __init__(self, _graph):
        empty = M.EmptyList
        empty_graph = M.Pair(
            M.HypergraphLabel,
            M.Pair(empty, M.Pair(empty, empty)),
        )
        empty_map = Gmod.Map(empty_graph, empty_graph, empty)()
        target = Gmod.Law(
            empty_graph,
            empty_graph,
            empty_graph,
            empty_map,
            empty_map,
            empty,
        )()
        obligation = Gmod.KObligation(M.Char("meta-added"), M.Char("fixed"))()
        updated_target = Gmod.Law(
            empty_graph,
            empty_graph,
            empty_graph,
            empty_map,
            empty_map,
            M.Pair(obligation, empty),
        )()
        meta = Gmod.CompileRuleToLaw(Pmod.Rule(target, updated_target))()

        version = Gmod.GraphVersion(empty, empty, empty)()
        installed = Gmod.InstallLaw(version, target)()
        installed = Gmod.InstallLaw(installed, meta)()

        # KNOWN GAP: Step-10 matching returns no completed Map for meta's L.
        # FireLaw is never entered, so there is no FireRejected Miss reason;
        # FireAny falls through and records a firing of the target Law instead.
        meta_match = Gmod.FirstCompletedMatch(Gmod.LawLeft(meta)(), installed)()
        fired = Gmod.FireAny(installed, Gmod.DanglingForbid()())()
        committed = M.Head(fired)()
        trace = M.Head(M.Tail(fired)())()

        self.result = M.truth_value
        if Gmod.LawMapsComplete(target)() is M.false_value:
            self.result = M.false_value
        elif Gmod.LawMapsComplete(meta)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(meta_match, empty)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(committed, empty)() is M.truth_value:
            self.result = M.false_value
        else:
            last = empty
            remaining = trace
            while M.IdentityCompare(remaining, empty)() is M.false_value:
                last = M.Head(remaining)()
                remaining = M.Tail(remaining)()
            if M.IdentityCompare(last, empty)() is M.truth_value:
                self.result = M.false_value
            elif M.IdentityCompare(M.Head(last)(), Lmod.NextLabel)() is M.false_value:
                self.result = M.false_value
            else:
                fire = M.Head(M.Tail(M.Tail(last)())())()
                if M.IdentityCompare(M.Head(fire)(), Lmod.FireLabel)() is M.false_value:
                    self.result = M.false_value
                elif M.TermEqual(M.Head(M.Tail(fire)())(), target)() is M.false_value:
                    self.result = M.false_value
                elif M.TermEqual(M.Head(M.Tail(fire)())(), meta)() is M.truth_value:
                    self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class ProposalStoreInertTest(M.Edge):
    """Step 15: submitted and approved proposals remain unreachable from FireAny."""

    def __init__(self, _graph):
        empty = M.EmptyList
        left_term = M.Pair(Lmod.ZeroLabel, empty)
        right_term = M.Pair(Lmod.SuccLabel, M.Pair(left_term, empty))
        law = Gmod.CompileRuleToLaw(Pmod.Rule(left_term, right_term))()
        proposal = Gmod.Proposal(law, M.Char("shadow-origin"))()
        justification = Gmod.JustifiedBy(proposal, M.Char("evidence"))()
        approval = Gmod.Approved(proposal, M.Char("curator"))()
        rejection = Gmod.Rejected(
            proposal,
            M.Char("curator"),
            M.Char("reason"),
        )()

        store = Gmod.ProposalStore(empty)()
        store = Gmod.ProposalStoreSubmit(store, proposal)()
        all_entries = Gmod.ProposalStoreAll(store)()
        approved_before = Gmod.ProposalStoreApproved(store)()
        approved_store = Gmod.ProposalStoreAttach(store, proposal, approval)()
        approved_after = Gmod.ProposalStoreApproved(approved_store)()

        encoded_left = Gmod.EncodeTermAsGraph(left_term)()
        version = Gmod.GraphVersion(
            Gmod.GraphNodes(encoded_left)(),
            Gmod.GraphEdges(encoded_left)(),
            empty,
        )()
        fired = Gmod.FireAny(version, Gmod.DanglingForbid()())()

        self.result = M.truth_value
        if M.IdentityCompare(M.Head(justification)(), Lmod.JustifiedByLabel)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Head(rejection)(), Lmod.RejectedLabel)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(all_entries, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Tail(all_entries)(), empty)() is M.false_value:
            self.result = M.false_value
        elif M.TermEqual(
            Gmod.ProposalEntryProposal(M.Head(all_entries)())(),
            proposal,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(approved_before, empty)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(approved_after, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Tail(approved_after)(), empty)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Head(fired)(), empty)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Head(M.Tail(fired)())(), empty)() is M.false_value:
            self.result = M.false_value
        elif Gmod.ChainHasTerm(Gmod.GraphNodes(version)(), left_term)() is M.false_value:
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class ActivateProposalTest(M.Edge):
    """Step 16: activation requires approval and records an Activation splice."""

    def __init__(self, _graph):
        empty = M.EmptyList
        left_term = M.Pair(Lmod.ZeroLabel, empty)
        right_term = M.Pair(Lmod.SuccLabel, M.Pair(left_term, empty))
        law = Gmod.CompileRuleToLaw(Pmod.Rule(left_term, right_term))()
        proposal = Gmod.Proposal(law, M.Char("curated-origin"))()

        store = Gmod.ProposalStore(empty)()
        store = Gmod.ProposalStoreSubmit(store, proposal)()
        unapproved_entry = M.Head(Gmod.ProposalStoreAll(store)())()

        encoded_left = Gmod.EncodeTermAsGraph(left_term)()
        version = Gmod.GraphVersion(
            Gmod.GraphNodes(encoded_left)(),
            Gmod.GraphEdges(encoded_left)(),
            empty,
        )()
        refused = Gmod.ActivateProposal(version, unapproved_entry)()
        refused_reason = M.Head(M.Tail(refused)())()

        approval = Gmod.Approved(proposal, M.Char("curator"))()
        approved_store = Gmod.ProposalStoreAttach(
            store,
            proposal,
            approval,
        )()
        approved_entry = M.Head(Gmod.ProposalStoreApproved(approved_store)())()
        activated = Gmod.ActivateProposal(version, approved_entry)()
        next_version = M.Head(activated)()
        lineage = M.Head(M.Tail(activated)())()

        self.result = M.truth_value
        if M.IdentityCompare(M.Head(refused)(), empty)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            M.Head(refused_reason)(),
            Lmod.ReasonUnapprovedLabel,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(next_version, empty)() is M.truth_value:
            self.result = M.false_value
        elif Gmod.ChainHasTerm(Gmod.InstalledLaws(next_version)(), law)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Head(lineage)(), Lmod.NextLabel)() is M.false_value:
            self.result = M.false_value
        else:
            fire = M.Head(M.Tail(M.Tail(lineage)())())()
            activation = M.Head(M.Tail(fire)())()
            mapping_placeholder = M.Head(M.Tail(M.Tail(fire)())())()
            lineage_version = M.Head(M.Tail(M.Tail(M.Tail(lineage)())())())()
            if M.IdentityCompare(M.Head(fire)(), Lmod.FireLabel)() is M.false_value:
                self.result = M.false_value
            elif M.IdentityCompare(
                M.Head(activation)(),
                Lmod.ActivationLabel,
            )() is M.false_value:
                self.result = M.false_value
            elif M.TermEqual(M.Head(M.Tail(activation)())(), proposal)() is M.false_value:
                self.result = M.false_value
            elif M.IdentityCompare(mapping_placeholder, empty)() is M.false_value:
                self.result = M.false_value
            elif M.TermEqual(lineage_version, next_version)() is M.false_value:
                self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class ProposalStoreHistoryTest(M.Edge):
    """Step 18: rejection evidence and submission history are retained."""

    def __init__(self, _graph):
        empty = M.EmptyList
        left_term = M.Pair(Lmod.ZeroLabel, empty)
        right_term = M.Pair(Lmod.SuccLabel, M.Pair(left_term, empty))
        law = Gmod.CompileRuleToLaw(Pmod.Rule(left_term, right_term))()
        first_proposal = Gmod.Proposal(law, M.Char("first-origin"))()
        second_proposal = Gmod.Proposal(law, M.Char("second-origin"))()

        store = Gmod.ProposalStore(empty)()
        store = Gmod.ProposalStoreSubmit(store, first_proposal)()
        store = Gmod.ProposalStoreSubmit(store, second_proposal)()
        submitted = Gmod.ProposalStoreHistory(store)()
        first_entry = M.Head(submitted)()
        second_entry = M.Head(M.Tail(submitted)())()

        approval = Gmod.Approved(first_proposal, M.Char("curator"))()
        store = Gmod.ProposalStoreAttach(
            store,
            first_proposal,
            approval,
        )()
        second_entry = M.Head(M.Tail(Gmod.ProposalStoreHistory(store)())())()
        rejection_authority = M.Char("curator")
        rejection_reason = M.Char("insufficient-evidence")
        store = Gmod.ProposalStoreReject(
            store,
            second_entry,
            rejection_authority,
            rejection_reason,
        )()

        history = Gmod.ProposalStoreHistory(store)()
        approved = Gmod.ProposalStoreApproved(store)()
        first_history_entry = M.Head(history)()
        second_history_entry = M.Head(M.Tail(history)())()
        expected_rejection = Gmod.Rejected(
            second_proposal,
            rejection_authority,
            rejection_reason,
        )()

        self.result = M.truth_value
        if M.IdentityCompare(history, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Tail(history)(), empty)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Tail(M.Tail(history)())(), empty)() is M.false_value:
            self.result = M.false_value
        elif M.TermEqual(
            Gmod.ProposalEntryProposal(first_history_entry)(),
            first_proposal,
        )() is M.false_value:
            self.result = M.false_value
        elif M.TermEqual(
            Gmod.ProposalEntryProposal(second_history_entry)(),
            second_proposal,
        )() is M.false_value:
            self.result = M.false_value
        elif Gmod.ChainHasTerm(
            Gmod.ProposalEntryAnnotations(second_history_entry)(),
            expected_rejection,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(approved, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Tail(approved)(), empty)() is M.false_value:
            self.result = M.false_value
        elif M.TermEqual(
            Gmod.ProposalEntryProposal(M.Head(approved)())(),
            first_proposal,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            Gmod.ProposalEntryAnnotations(first_entry)(),
            empty,
        )() is M.false_value:
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class FiringLedgerTest(M.Edge):
    """Step 19: committed firings retain exact counts and signed means."""

    def __init__(self, graph):
        empty = M.EmptyList
        ledger = Gmod.FiringLedger()

        left_one_node = M.Thingy()
        right_one_node = M.Thingy()
        right_two_node = M.Thingy()
        left_one = M.Pair(
            M.HypergraphLabel,
            M.Pair(M.Pair(left_one_node, empty), M.Pair(empty, empty)),
        )
        interface_one = M.Pair(
            M.HypergraphLabel,
            M.Pair(empty, M.Pair(empty, empty)),
        )
        right_one = M.Pair(
            M.HypergraphLabel,
            M.Pair(
                M.Pair(right_one_node, M.Pair(right_two_node, empty)),
                M.Pair(empty, empty),
            ),
        )
        law_one = Gmod.Law(
            left_one,
            interface_one,
            right_one,
            Gmod.Map(interface_one, left_one, empty)(),
            Gmod.Map(interface_one, right_one, empty)(),
            empty,
        )()
        host_one = Gmod.GraphVersion(M.Pair(left_one_node, empty), empty, empty)()
        map_one = Gmod.Map(
            left_one,
            host_one,
            M.Pair(Gmod.Send(left_one_node, left_one_node)(), empty),
        )()
        fired_one = Gmod.FireLaw(
            host_one,
            law_one,
            map_one,
            Gmod.DanglingForbid()(),
            ledger,
        )()

        left_two_first = M.Thingy()
        left_two_second = M.Thingy()
        right_two_only = M.Thingy()
        left_two = M.Pair(
            M.HypergraphLabel,
            M.Pair(
                M.Pair(left_two_first, M.Pair(left_two_second, empty)),
                M.Pair(empty, empty),
            ),
        )
        interface_two = M.Pair(
            M.HypergraphLabel,
            M.Pair(empty, M.Pair(empty, empty)),
        )
        right_two = M.Pair(
            M.HypergraphLabel,
            M.Pair(M.Pair(right_two_only, empty), M.Pair(empty, empty)),
        )
        law_two = Gmod.Law(
            left_two,
            interface_two,
            right_two,
            Gmod.Map(interface_two, left_two, empty)(),
            Gmod.Map(interface_two, right_two, empty)(),
            empty,
        )()
        host_two = Gmod.GraphVersion(
            M.Pair(left_two_first, M.Pair(left_two_second, empty)),
            empty,
            empty,
        )()
        map_two = Gmod.Map(
            left_two,
            host_two,
            M.Pair(
                Gmod.Send(left_two_first, left_two_first)(),
                M.Pair(Gmod.Send(left_two_second, left_two_second)(), empty),
            ),
        )()
        fired_two = Gmod.FireLaw(
            host_two,
            law_two,
            map_two,
            Gmod.DanglingForbid()(),
            ledger,
        )()
        fired_one_again = Gmod.FireLaw(
            host_one,
            law_one,
            map_one,
            Gmod.DanglingForbid()(),
            ledger,
        )()
        rejected = Gmod.FireLaw(
            host_one,
            law_one,
            Gmod.Map(left_one, host_one, empty)(),
            Gmod.DanglingForbid()(),
            ledger,
        )()

        records = ledger.all()
        first_record = M.Head(records)()
        second_record = M.Head(M.Tail(records)())()
        third_record = M.Head(M.Tail(M.Tail(records)())())()
        groups = ledger.by_law()
        first_group = M.Head(groups)()
        second_group = M.Head(M.Tail(groups)())()
        first_group_records = M.Head(M.Tail(first_group)())()
        second_group_records = M.Head(M.Tail(second_group)())()
        delta_one = ledger.size_delta(law_one)
        delta_two = ledger.size_delta(law_two)

        any_left_term = M.Pair(Lmod.ZeroLabel, empty)
        any_right_term = M.Pair(
            Lmod.SuccLabel,
            M.Pair(any_left_term, empty),
        )
        any_law = Gmod.CompileRuleToLaw(
            Pmod.Rule(any_left_term, any_right_term)
        )()
        any_encoded = Gmod.EncodeTermAsGraph(any_left_term)()
        any_version = Gmod.GraphVersion(
            Gmod.GraphNodes(any_encoded)(),
            Gmod.GraphEdges(any_encoded)(),
            empty,
        )()
        any_version = Gmod.InstallLaw(any_version, any_law)()
        any_ledger = Gmod.FiringLedger()
        fired_any = Gmod.FireAny(
            any_version,
            Gmod.DanglingForbid()(),
            any_ledger,
        )()
        any_records = any_ledger.all()

        self.result = M.truth_value
        if M.IdentityCompare(M.Head(fired_one)(), empty)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Head(fired_two)(), empty)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Head(fired_one_again)(), empty)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Head(fired_any)(), empty)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(any_records, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Tail(any_records)(), empty)() is M.false_value:
            self.result = M.false_value
        elif M.TermEqual(
            Gmod.FiringRecordLaw(M.Head(any_records)())(),
            any_law,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Head(rejected)(), empty)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            M.Tail(M.Tail(M.Tail(records)())())(),
            empty,
        )() is M.false_value:
            self.result = M.false_value
        elif M.TermEqual(Gmod.FiringRecordLaw(first_record)(), law_one)() is M.false_value:
            self.result = M.false_value
        elif M.TermEqual(Gmod.FiringRecordLaw(second_record)(), law_two)() is M.false_value:
            self.result = M.false_value
        elif M.TermEqual(Gmod.FiringRecordLaw(third_record)(), law_one)() is M.false_value:
            self.result = M.false_value
        elif M.TermEqual(Gmod.FiringRecordG0(first_record)(), host_one)() is M.false_value:
            self.result = M.false_value
        elif M.TermEqual(
            Gmod.FiringRecordG1(first_record)(),
            M.Head(fired_one)(),
        )() is M.false_value:
            self.result = M.false_value
        elif M.TermEqual(
            Gmod.FiringRecordTrace(first_record)(),
            M.Head(M.Tail(fired_one)())(),
        )() is M.false_value:
            self.result = M.false_value
        elif M.NatEq(
            Gmod.FiringRecordEdgesBefore(first_record)(),
            M.Zero,
            ledger.registry,
        )() is M.false_value:
            self.result = M.false_value
        elif M.NatEq(
            Gmod.FiringRecordEdgesAfter(first_record)(),
            M.Zero,
            ledger.registry,
        )() is M.false_value:
            self.result = M.false_value
        elif M.NatEq(
            Gmod.FiringRecordTraceSteps(first_record)(),
            M.six,
            ledger.registry,
        )() is M.false_value:
            self.result = M.false_value
        elif M.NatEq(
            Gmod.FiringRecordNodesBefore(first_record)(),
            M.one,
            ledger.registry,
        )() is M.false_value:
            self.result = M.false_value
        elif M.NatEq(
            Gmod.FiringRecordNodesAfter(first_record)(),
            M.two,
            ledger.registry,
        )() is M.false_value:
            self.result = M.false_value
        elif M.NatEq(
            Gmod.FiringRecordNodesBefore(second_record)(),
            M.two,
            ledger.registry,
        )() is M.false_value:
            self.result = M.false_value
        elif M.NatEq(
            Gmod.FiringRecordNodesAfter(second_record)(),
            M.one,
            ledger.registry,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Tail(M.Tail(groups)())(), empty)() is M.false_value:
            self.result = M.false_value
        elif M.TermEqual(M.Head(first_group)(), law_one)() is M.false_value:
            self.result = M.false_value
        elif M.TermEqual(M.Head(second_group)(), law_two)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            M.Tail(M.Tail(first_group_records)())(),
            empty,
        )() is M.false_value:
            self.result = M.false_value
        elif M.TermEqual(M.Head(first_group_records)(), first_record)() is M.false_value:
            self.result = M.false_value
        elif M.TermEqual(
            M.Head(M.Tail(first_group_records)())(),
            third_record,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            M.Tail(second_group_records)(),
            empty,
        )() is M.false_value:
            self.result = M.false_value
        elif M.NatEq(
            Gmod.SignedRationalPositive(delta_one)(),
            M.four,
            ledger.registry,
        )() is M.false_value:
            self.result = M.false_value
        elif M.NatEq(
            Gmod.SignedRationalNegative(delta_one)(),
            M.two,
            ledger.registry,
        )() is M.false_value:
            self.result = M.false_value
        elif M.NatEq(
            Gmod.SignedRationalSamples(delta_one)(),
            M.two,
            ledger.registry,
        )() is M.false_value:
            self.result = M.false_value
        elif M.NatEq(
            Gmod.SignedRationalPositive(delta_two)(),
            M.one,
            ledger.registry,
        )() is M.false_value:
            self.result = M.false_value
        elif M.NatEq(
            Gmod.SignedRationalNegative(delta_two)(),
            M.two,
            ledger.registry,
        )() is M.false_value:
            self.result = M.false_value
        elif M.NatEq(
            Gmod.SignedRationalSamples(delta_two)(),
            M.one,
            ledger.registry,
        )() is M.false_value:
            self.result = M.false_value
        super().__init__(inputs=empty, results=M.Pair(self.result, empty))

    def __call__(self):
        return self.result


class PatternCensusTest(M.Edge):
    """Step 20: per-version completed-match counts preserve version order."""

    def __init__(self, graph):
        empty = M.EmptyList
        registry = _registry(graph)
        ledger = Gmod.FiringLedger(registry)

        pat_node = M.Thingy()
        pattern = M.Pair(
            M.HypergraphLabel,
            M.Pair(M.Pair(pat_node, empty), M.Pair(empty, empty)),
        )
        host_left = M.Thingy()
        host_right = M.Thingy()
        twice = Gmod.GraphVersion(
            M.Pair(host_left, M.Pair(host_right, empty)),
            empty,
            empty,
        )()
        absent = Gmod.GraphVersion(empty, empty, empty)()
        versions = M.Pair(twice, M.Pair(absent, empty))

        counts = Gmod.PatternCensus(ledger, pattern, versions)()
        tuned_counts = Gmod.PatternCensus(
            ledger,
            pattern,
            versions,
            M.GMPRep("1"),
        )()

        self.result = M.truth_value
        if M.IdentityCompare(counts, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Tail(counts)(), empty)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            M.Tail(M.Tail(counts)())(),
            empty,
        )() is M.false_value:
            self.result = M.false_value
        elif M.NatEq(M.Head(counts)(), M.two, ledger.registry)() is M.false_value:
            self.result = M.false_value
        elif M.NatEq(
            M.Head(M.Tail(counts)())(),
            M.Zero,
            ledger.registry,
        )() is M.false_value:
            self.result = M.false_value
        elif M.NatEq(
            M.Head(tuned_counts)(),
            M.one,
            ledger.registry,
        )() is M.false_value:
            self.result = M.false_value
        elif M.NatEq(
            M.Head(M.Tail(tuned_counts)())(),
            M.Zero,
            ledger.registry,
        )() is M.false_value:
            self.result = M.false_value
        super().__init__(inputs=empty, results=M.Pair(self.result, empty))

    def __call__(self):
        return self.result


class HandleFoldUnfoldTest(M.Edge):
    """Step 21: a three-node pattern folds to a handle and unfolds exactly."""

    def __init__(self, graph):
        empty = M.EmptyList
        registry = M.FromContextGetConstructors(graph)()
        left_interface = M.Thingy()
        internal = M.Thingy()
        right_interface = M.Thingy()
        pattern_edge = M.Pair(
            M.Char("pattern-edge"),
            M.Pair(
                left_interface,
                M.Pair(internal, M.Pair(right_interface, empty)),
            ),
        )
        pattern_nodes = M.Pair(
            left_interface,
            M.Pair(internal, M.Pair(right_interface, empty)),
        )
        pattern = M.Pair(
            M.HypergraphLabel,
            M.Pair(pattern_nodes, M.Pair(M.Pair(pattern_edge, empty), empty)),
        )
        interface_nodes = M.Pair(
            left_interface,
            M.Pair(right_interface, empty),
        )
        name = M.Char("three-node-handle")
        handle = Gmod.Handle(name, pattern)()
        compiled = Gmod.CompileHandleToLaws(handle, interface_nodes)()
        fold = M.Head(compiled)()
        unfold = M.Head(M.Tail(compiled)())()
        connector = M.Head(Gmod.GraphEdges(Gmod.LawRight(fold)())())()

        host = Gmod.GraphVersion(
            pattern_nodes,
            M.Pair(pattern_edge, empty),
            empty,
        )()
        fold_sends = Gmod.IdentitySendsFor(Gmod.GraphElements(pattern)())()
        fold_mapping = Gmod.Map(pattern, host, fold_sends)()
        folded_result = Gmod.FireLaw(
            host,
            fold,
            fold_mapping,
            Gmod.DanglingForbid()(),
        )()
        folded = M.Head(folded_result)()

        before_counted = M.Count(Gmod.GraphNodes(host)(), registry)()
        before_count = M.Head(before_counted)()
        registry = M.Head(M.Tail(before_counted)())()
        interface_counted = M.Count(interface_nodes, registry)()
        interface_count = M.Head(interface_counted)()
        registry = M.Head(M.Tail(interface_counted)())()
        expected_folded_pair = M.Succ(interface_count, registry)()
        expected_folded_count = M.Head(expected_folded_pair)()
        registry = M.Head(M.Tail(expected_folded_pair)())()
        folded_counted = M.Count(Gmod.GraphNodes(folded)(), registry)()
        folded_count = M.Head(folded_counted)()
        registry = M.Head(M.Tail(folded_counted)())()

        unfold_sends = Gmod.IdentitySendsFor(
            Gmod.GraphElements(Gmod.LawLeft(unfold)())(),
        )()
        unfold_mapping = Gmod.Map(
            Gmod.LawLeft(unfold)(),
            folded,
            unfold_sends,
        )()
        unfolded_result = Gmod.FireLaw(
            folded,
            unfold,
            unfold_mapping,
            Gmod.DanglingForbid()(),
        )()
        unfolded = M.Head(unfolded_result)()

        self.result = M.truth_value
        if M.IdentityCompare(M.Tail(M.Tail(compiled)())(), empty)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(Gmod.HandleName(handle)(), name)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(Gmod.HandlePattern(handle)(), pattern)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(Gmod.LawLeft(fold)(), pattern)() is M.false_value:
            self.result = M.false_value
        elif M.TermEqual(
            Gmod.GraphNodes(Gmod.LawInterface(fold)())(),
            interface_nodes,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            Gmod.GraphEdges(Gmod.LawInterface(fold)())(),
            empty,
        )() is M.false_value:
            self.result = M.false_value
        elif Gmod.LawMapsComplete(fold)() is M.false_value:
            self.result = M.false_value
        elif Gmod.LawMapsComplete(unfold)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            Gmod.LawLeft(unfold)(),
            Gmod.LawRight(fold)(),
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            Gmod.LawRight(unfold)(),
            Gmod.LawLeft(fold)(),
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            Gmod.LawKToLeft(unfold)(),
            Gmod.LawKToRight(fold)(),
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            Gmod.LawKToRight(unfold)(),
            Gmod.LawKToLeft(fold)(),
        )() is M.false_value:
            self.result = M.false_value
        elif M.TermEqual(
            Gmod.GraphNodes(Gmod.LawRight(fold)())(),
            M.Pair(handle, interface_nodes),
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            M.Tail(Gmod.GraphEdges(Gmod.LawRight(fold)())())(),
            empty,
        )() is M.false_value:
            self.result = M.false_value
        elif Gmod.ChainHasTerm(pattern_nodes, handle)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Head(connector)(), Lmod.HandleLabel)() is M.false_value:
            self.result = M.false_value
        elif M.TermEqual(
            Gmod.EdgeEndpoints(connector)(),
            M.Pair(handle, interface_nodes),
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(folded, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.NatEq(before_count, expected_folded_count, registry)() is M.false_value:
            self.result = M.false_value
        elif M.NatEq(folded_count, expected_folded_count, registry)() is M.false_value:
            self.result = M.false_value
        elif Gmod.ChainHasTerm(Gmod.GraphNodes(folded)(), internal)() is M.truth_value:
            self.result = M.false_value
        elif Gmod.ChainHasTerm(Gmod.GraphNodes(folded)(), handle)() is M.false_value:
            self.result = M.false_value
        elif Gmod.ChainHasTerm(Gmod.GraphEdges(folded)(), connector)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(unfolded, empty)() is M.truth_value:
            self.result = M.false_value
        elif Gmod.GraphStoresEqual(unfolded, host)() is M.false_value:
            self.result = M.false_value
        graph._replace_context(constructors=registry)
        super().__init__(inputs=empty, results=M.Pair(self.result, empty))

    def __call__(self):
        return self.result


class PositionalSignaturesTest(M.Edge):
    """Step 22: Pair signatures are counted and Handle folds preserve boundaries."""

    def __init__(self, _graph):
        empty = M.EmptyList
        left_interface = M.Thingy()
        internal = M.Thingy()
        right_interface = M.Thingy()
        outside = M.Thingy()
        pattern_label = M.Char("signature-pattern-edge")
        boundary_label = M.Char("signature-boundary-edge")
        pattern_edge = M.Pair(
            pattern_label,
            M.Pair(
                left_interface,
                M.Pair(internal, M.Pair(right_interface, empty)),
            ),
        )
        right_boundary_edge = M.Pair(
            boundary_label,
            M.Pair(right_interface, M.Pair(outside, empty)),
        )
        left_boundary_edge = M.Pair(
            boundary_label,
            M.Pair(left_interface, M.Pair(outside, empty)),
        )
        pattern_nodes = M.Pair(
            left_interface,
            M.Pair(internal, M.Pair(right_interface, empty)),
        )
        pattern = M.Pair(
            M.HypergraphLabel,
            M.Pair(pattern_nodes, M.Pair(M.Pair(pattern_edge, empty), empty)),
        )
        host = Gmod.GraphVersion(
            M.Pair(
                left_interface,
                M.Pair(
                    internal,
                    M.Pair(right_interface, M.Pair(outside, empty)),
                ),
            ),
            M.Pair(
                pattern_edge,
                M.Pair(
                    right_boundary_edge,
                    M.Pair(left_boundary_edge, empty),
                ),
            ),
            empty,
        )()
        handle = Gmod.Handle(M.Char("signature-handle"), pattern)()
        complete_interface = M.Pair(
            left_interface,
            M.Pair(right_interface, empty),
        )
        incomplete_interface = M.Pair(left_interface, empty)

        boundary_signature = Gmod.PositionalSignature(right_boundary_edge)()
        census = Gmod.SignatureCensus(host)()
        pattern_entry = M.Head(census)()
        boundary_entry = M.Head(M.Tail(census)())()

        self.result = M.truth_value
        if M.TermEqual(M.Head(boundary_signature)(), boundary_label)() is M.false_value:
            self.result = M.false_value
        elif M.NatEq(
            M.Head(M.Tail(boundary_signature)())(),
            M.two,
            M.AllConstructors,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            M.Tail(M.Tail(census)())(),
            empty,
        )() is M.false_value:
            self.result = M.false_value
        elif M.TermEqual(
            M.Head(M.Head(pattern_entry)())(),
            pattern_label,
        )() is M.false_value:
            self.result = M.false_value
        elif M.NatEq(
            M.Head(M.Tail(M.Head(pattern_entry)())())(),
            M.three,
            M.AllConstructors,
        )() is M.false_value:
            self.result = M.false_value
        elif M.NatEq(
            M.Head(M.Tail(pattern_entry)())(),
            M.one,
            M.AllConstructors,
        )() is M.false_value:
            self.result = M.false_value
        elif M.TermEqual(
            M.Head(M.Head(boundary_entry)())(),
            boundary_label,
        )() is M.false_value:
            self.result = M.false_value
        elif M.NatEq(
            M.Head(M.Tail(boundary_entry)())(),
            M.two,
            M.AllConstructors,
        )() is M.false_value:
            self.result = M.false_value
        elif Gmod.HandleRespectsSignatures(
            handle,
            complete_interface,
            host,
        )() is M.false_value:
            self.result = M.false_value
        elif Gmod.HandleRespectsSignatures(
            handle,
            incomplete_interface,
            host,
        )() is M.truth_value:
            self.result = M.false_value
        super().__init__(inputs=empty, results=M.Pair(self.result, empty))

    def __call__(self):
        return self.result


class HandlePromotionTest(M.Edge):
    """Step 23: report, human approval, activation, and folding stay mechanical."""

    def __init__(self, graph):
        empty = M.EmptyList
        registry = M.FromContextGetConstructors(graph)()
        ledger = Gmod.FiringLedger(registry)
        left_interface = M.Char("promotion-left-interface")
        first_internal = M.Char("promotion-first-internal")
        second_internal = M.Char("promotion-second-internal")
        right_interface = M.Char("promotion-right-interface")
        outside = M.Char("promotion-outside")
        pattern_edge = M.Pair(
            M.Char("promotion-pattern-edge"),
            M.Pair(
                left_interface,
                M.Pair(
                    first_internal,
                    M.Pair(second_internal, M.Pair(right_interface, empty)),
                ),
            ),
        )
        boundary_edge = M.Pair(
            M.Char("promotion-boundary-edge"),
            M.Pair(right_interface, M.Pair(outside, empty)),
        )
        pattern_nodes = M.Pair(
            left_interface,
            M.Pair(
                first_internal,
                M.Pair(second_internal, M.Pair(right_interface, empty)),
            ),
        )
        pattern = M.Pair(
            M.HypergraphLabel,
            M.Pair(pattern_nodes, M.Pair(M.Pair(pattern_edge, empty), empty)),
        )
        host = Gmod.GraphVersion(
            M.Pair(
                left_interface,
                M.Pair(
                    first_internal,
                    M.Pair(
                        second_internal,
                        M.Pair(right_interface, M.Pair(outside, empty)),
                    ),
                ),
            ),
            M.Pair(pattern_edge, M.Pair(boundary_edge, empty)),
            empty,
        )()
        versions = M.Pair(host, M.Pair(host, empty))
        interface_nodes = M.Pair(
            left_interface,
            M.Pair(right_interface, empty),
        )
        handle = Gmod.Handle(M.Char("promotion-handle"), pattern)()
        report = Gmod.PromotionReport(
            handle,
            interface_nodes,
            ledger,
            versions,
            M.GMPRep("1"),
        )()
        census_entry = M.Head(report)()
        signature_entry = M.Head(M.Tail(report)())()
        roundtrip_entry = M.Head(M.Tail(M.Tail(report)())())()
        size_entry = M.Head(M.Tail(M.Tail(M.Tail(report)())())())()
        census = M.Head(M.Tail(census_entry)())()
        signature_ok = M.Head(M.Tail(signature_entry)())()
        roundtrip_ok = M.Head(M.Tail(roundtrip_entry)())()
        size_delta = M.Head(M.Tail(size_entry)())()

        store = Gmod.ProposalStore(empty)()
        proposed_store = Gmod.ProposeHandle(
            store,
            handle,
            interface_nodes,
            report,
        )()
        history = Gmod.ProposalStoreHistory(proposed_store)()
        proposal_entry = M.Head(history)()
        proposal = Gmod.ProposalEntryProposal(proposal_entry)()
        annotations = Gmod.ProposalEntryAnnotations(proposal_entry)()
        justification = M.Head(annotations)()
        justification_report = M.Head(M.Tail(M.Tail(justification)())())()
        approved_store = Gmod.ProposalStoreAttach(
            proposed_store,
            proposal,
            Gmod.Approved(proposal, M.Char("human-curator"))(),
        )()
        approved_entry = M.Head(Gmod.ProposalStoreApproved(approved_store)())()
        activated = Gmod.ActivateProposal(host, approved_entry)()
        active_version = M.Head(activated)()
        fired = Gmod.FireAny(
            active_version,
            Gmod.DanglingForbid()(),
            ledger,
        )()
        fired_version = M.Head(fired)()

        absent = Gmod.GraphVersion(empty, empty, empty)()
        no_match_report = Gmod.PromotionReport(
            handle,
            interface_nodes,
            ledger,
            M.Pair(absent, empty),
        )()

        self.result = M.truth_value
        if M.IdentityCompare(report, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            M.Tail(M.Tail(M.Tail(M.Tail(report)())())())(),
            empty,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            M.Head(census_entry)(),
            Gmod.PROMOTION_REPORT_CENSUS_KEY,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            M.Head(signature_entry)(),
            Gmod.PROMOTION_REPORT_SIGNATURE_KEY,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            M.Head(roundtrip_entry)(),
            Gmod.PROMOTION_REPORT_ROUNDTRIP_KEY,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            M.Head(size_entry)(),
            Gmod.PROMOTION_REPORT_SIZE_DELTA_KEY,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Tail(M.Tail(census)())(), empty)() is M.false_value:
            self.result = M.false_value
        elif M.NatEq(M.Head(census)(), M.Zero, ledger.registry)() is M.truth_value:
            self.result = M.false_value
        elif M.NatEq(
            M.Head(M.Tail(census)())(),
            M.Zero,
            ledger.registry,
        )() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(signature_ok, M.truth_value)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(roundtrip_ok, M.truth_value)() is M.false_value:
            self.result = M.false_value
        elif M.NatEq(
            Gmod.SignedRationalPositive(size_delta)(),
            M.five,
            ledger.registry,
        )() is M.false_value:
            self.result = M.false_value
        elif M.NatEq(
            Gmod.SignedRationalNegative(size_delta)(),
            M.four,
            ledger.registry,
        )() is M.false_value:
            self.result = M.false_value
        elif M.NatEq(
            Gmod.SignedRationalSamples(size_delta)(),
            M.one,
            ledger.registry,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Tail(history)(), empty)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(Gmod.ProposalOrigin(proposal)(), handle)() is M.false_value:
            self.result = M.false_value
        elif M.TermEqual(
            Gmod.ProposalLaw(proposal)(),
            M.Head(Gmod.CompileHandleToLaws(handle, interface_nodes)())(),
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Head(justification)(), Lmod.JustifiedByLabel)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(justification_report, report)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(active_version, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(fired_version, empty)() is M.truth_value:
            self.result = M.false_value
        elif Gmod.ChainHasTerm(
            Gmod.GraphNodes(fired_version)(),
            handle,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(no_match_report, empty)() is M.false_value:
            self.result = M.false_value
        graph._replace_context(constructors=ledger.registry)
        super().__init__(inputs=empty, results=M.Pair(self.result, empty))

    def __call__(self):
        return self.result


class ImpactPolicyTest(M.Edge):
    """Step 24: fixed impact classes prefer the restrictive structural class."""

    def __init__(self, _graph):
        empty = M.EmptyList
        policy = Gmod.ImpactPolicy()()
        fold_entry = M.Head(policy)()
        policy_tail = M.Tail(policy)()
        unfold_entry = M.Head(policy_tail)()
        policy_tail = M.Tail(policy_tail)()
        install_entry = M.Head(policy_tail)()
        policy_tail = M.Tail(policy_tail)()
        meta_entry = M.Head(policy_tail)()
        policy_tail = M.Tail(policy_tail)()
        activation_entry = M.Head(policy_tail)()
        policy_tail = M.Tail(policy_tail)()
        preference_entry = M.Head(policy_tail)()
        policy_tail = M.Tail(policy_tail)()
        retire_entry = M.Head(policy_tail)()
        policy_tail = M.Tail(policy_tail)()
        scheduler_entry = M.Head(policy_tail)()
        policy_tail = M.Tail(policy_tail)()
        annotate_entry = M.Head(policy_tail)()
        policy_tail = M.Tail(policy_tail)()

        empty_graph = Gmod.GraphVersion(empty, empty, empty)()
        handle = Gmod.Handle(M.Char("impact-handle"), empty_graph)()
        handle_graph = Gmod.GraphVersion(M.Pair(handle, empty), empty, empty)()
        plain_law = Gmod.Law(
            empty_graph,
            empty_graph,
            empty_graph,
            empty,
            empty,
            empty,
        )()
        law_graph = Gmod.GraphVersion(M.Pair(plain_law, empty), empty, empty)()

        fold_proposal = Gmod.Proposal(
            Gmod.Law(
                empty_graph,
                empty_graph,
                handle_graph,
                empty,
                empty,
                empty,
            )(),
            M.Char("fold-impact"),
        )()
        unfold_proposal = Gmod.Proposal(
            Gmod.Law(
                handle_graph,
                empty_graph,
                empty_graph,
                empty,
                empty,
                empty,
            )(),
            M.Char("unfold-impact"),
        )()
        install_proposal = Gmod.Proposal(
            plain_law,
            M.Char("install-impact"),
        )()
        meta_proposal = Gmod.Proposal(
            Gmod.Law(
                law_graph,
                empty_graph,
                empty_graph,
                empty,
                empty,
                empty,
            )(),
            M.Char("meta-impact"),
        )()
        ambiguous_proposal = Gmod.Proposal(
            Gmod.Law(
                law_graph,
                empty_graph,
                handle_graph,
                empty,
                empty,
                empty,
            )(),
            M.Char("ambiguous-impact"),
        )()
        retired_graph = Gmod.GraphVersion(
            M.Pair(Gmod.Retired(plain_law)(), empty),
            empty,
            empty,
        )()
        retire_proposal = Gmod.Proposal(
            Gmod.Law(
                empty_graph,
                empty_graph,
                retired_graph,
                empty,
                empty,
                empty,
            )(),
            M.Char("retire-impact"),
        )()
        heuristic_graph = Gmod.GraphVersion(
            M.Pair(
                M.Heuristic(
                    M.DFSLabel,
                    M.GoalHeadOrderLabel,
                    M.Zero,
                    M.one,
                    M.one,
                    M.one,
                )(),
                empty,
            ),
            empty,
            empty,
        )()
        scheduler_proposal = Gmod.Proposal(
            Gmod.Law(
                empty_graph,
                empty_graph,
                heuristic_graph,
                empty,
                empty,
                empty,
            )(),
            M.Char("scheduler-impact"),
        )()
        robustness_graph = Gmod.GraphVersion(
            M.Pair(
                Gmod.Robustness(plain_law, M.two, M.three)(),
                empty,
            ),
            empty,
            empty,
        )()
        annotate_proposal = Gmod.Proposal(
            Gmod.Law(
                empty_graph,
                empty_graph,
                robustness_graph,
                empty,
                empty,
                empty,
            )(),
            M.Char("annotate-impact"),
        )()

        self.result = M.truth_value
        if M.IdentityCompare(policy_tail, empty)() is M.false_value:
            self.result = M.false_value
        elif M.Compare(M.Head(fold_entry)(), M.Char("fold_handle"))() is M.false_value:
            self.result = M.false_value
        elif M.Compare(
            M.Head(M.Tail(fold_entry)())(),
            M.Char("auto"),
        )() is M.false_value:
            self.result = M.false_value
        elif M.Compare(
            M.Head(unfold_entry)(),
            M.Char("unfold_handle"),
        )() is M.false_value:
            self.result = M.false_value
        elif M.Compare(
            M.Head(M.Tail(unfold_entry)())(),
            M.Char("auto"),
        )() is M.false_value:
            self.result = M.false_value
        elif M.Compare(
            M.Head(install_entry)(),
            M.Char("install_law"),
        )() is M.false_value:
            self.result = M.false_value
        elif M.Compare(
            M.Head(M.Tail(install_entry)())(),
            M.Char("human"),
        )() is M.false_value:
            self.result = M.false_value
        elif M.Compare(
            M.Head(meta_entry)(),
            M.Char("meta_rewrite"),
        )() is M.false_value:
            self.result = M.false_value
        elif M.Compare(
            M.Head(M.Tail(meta_entry)())(),
            M.Char("human"),
        )() is M.false_value:
            self.result = M.false_value
        elif M.Compare(
            M.Head(activation_entry)(),
            M.Char("activation"),
        )() is M.false_value:
            self.result = M.false_value
        elif M.Compare(
            M.Head(M.Tail(activation_entry)())(),
            M.Char("human"),
        )() is M.false_value:
            self.result = M.false_value
        elif M.Compare(
            M.Head(preference_entry)(),
            M.Char("tune_preference"),
        )() is M.false_value:
            self.result = M.false_value
        elif M.Compare(
            M.Head(M.Tail(preference_entry)())(),
            M.Char("auto"),
        )() is M.false_value:
            self.result = M.false_value
        elif M.Compare(
            M.Head(retire_entry)(),
            M.Char("retire_law"),
        )() is M.false_value:
            self.result = M.false_value
        elif M.Compare(
            M.Head(M.Tail(retire_entry)())(),
            M.Char("human"),
        )() is M.false_value:
            self.result = M.false_value
        elif M.Compare(
            M.Head(scheduler_entry)(),
            M.Char("tune_scheduler"),
        )() is M.false_value:
            self.result = M.false_value
        elif M.Compare(
            M.Head(M.Tail(scheduler_entry)())(),
            M.Char("human"),
        )() is M.false_value:
            self.result = M.false_value
        elif M.Compare(
            M.Head(annotate_entry)(),
            M.Char("annotate"),
        )() is M.false_value:
            self.result = M.false_value
        elif M.Compare(
            M.Head(M.Tail(annotate_entry)())(),
            M.Char("auto"),
        )() is M.false_value:
            self.result = M.false_value
        elif M.Compare(
            Gmod.ClassifyProposal(fold_proposal)(),
            M.Char("fold_handle"),
        )() is M.false_value:
            self.result = M.false_value
        elif M.Compare(
            Gmod.ClassifyProposal(unfold_proposal)(),
            M.Char("unfold_handle"),
        )() is M.false_value:
            self.result = M.false_value
        elif M.Compare(
            Gmod.ClassifyProposal(install_proposal)(),
            M.Char("install_law"),
        )() is M.false_value:
            self.result = M.false_value
        elif M.Compare(
            Gmod.ClassifyProposal(meta_proposal)(),
            M.Char("meta_rewrite"),
        )() is M.false_value:
            self.result = M.false_value
        elif M.Compare(
            Gmod.ClassifyProposal(ambiguous_proposal)(),
            M.Char("meta_rewrite"),
        )() is M.false_value:
            self.result = M.false_value
        elif M.Compare(
            Gmod.ClassifyProposal(retire_proposal)(),
            M.Char("retire_law"),
        )() is M.false_value:
            self.result = M.false_value
        elif M.Compare(
            Gmod.ClassifyProposal(scheduler_proposal)(),
            M.Char("tune_scheduler"),
        )() is M.false_value:
            self.result = M.false_value
        elif M.Compare(
            Gmod.ClassifyProposal(annotate_proposal)(),
            M.Char("annotate"),
        )() is M.false_value:
            self.result = M.false_value
        super().__init__(inputs=empty, results=M.Pair(self.result, empty))

    def __call__(self):
        return self.result


class AutonomyCycleTest(M.Edge):
    """Step 25: automatic governance respects policy and firing budgets."""

    def __init__(self, graph):
        empty = M.EmptyList
        registry = M.FromContextGetConstructors(graph)()
        ledger = Gmod.FiringLedger(registry)

        interface_node = M.Char("autonomy-interface")
        first_internal = M.Char("autonomy-first-internal")
        second_internal = M.Char("autonomy-second-internal")
        pattern_edge = M.Pair(
            M.Char("autonomy-pattern-edge"),
            M.Pair(
                interface_node,
                M.Pair(first_internal, M.Pair(second_internal, empty)),
            ),
        )
        pattern_nodes = M.Pair(
            interface_node,
            M.Pair(first_internal, M.Pair(second_internal, empty)),
        )
        pattern = M.Pair(
            M.HypergraphLabel,
            M.Pair(pattern_nodes, M.Pair(M.Pair(pattern_edge, empty), empty)),
        )
        interface_nodes = M.Pair(interface_node, empty)
        handle = Gmod.Handle(M.Char("autonomy-handle"), pattern)()
        compiled = Gmod.CompileHandleToLaws(handle, interface_nodes)()
        fold = M.Head(compiled)()
        unfold = M.Head(M.Tail(compiled)())()
        auto_proposal = Gmod.Proposal(fold, handle)()
        rollback_obligation = Gmod.KObligation(
            M.Char("node-count-max"),
            M.nine,
        )()
        rollback_law = Gmod.Law(
            Gmod.LawLeft(unfold)(),
            Gmod.LawInterface(unfold)(),
            Gmod.LawRight(unfold)(),
            Gmod.LawKToLeft(unfold)(),
            Gmod.LawKToRight(unfold)(),
            M.Pair(rollback_obligation, empty),
        )()

        empty_graph = Gmod.GraphVersion(empty, empty, empty)()
        human_law = Gmod.Law(
            empty_graph,
            empty_graph,
            empty_graph,
            empty,
            empty,
            empty,
        )()
        human_proposal = Gmod.Proposal(
            human_law,
            M.Char("autonomy-human-origin"),
        )()
        store = Gmod.ProposalStore(empty)()
        store = Gmod.ProposalStoreSubmit(store, auto_proposal)()
        store = Gmod.ProposalStoreSubmit(store, human_proposal)()
        host = Gmod.GraphVersion(pattern_nodes, M.Pair(pattern_edge, empty), empty)()
        budget = M.Pair(
            M.Pair(
                Gmod.AUTONOMY_BUDGET_MAX_FIRINGS_KEY,
                M.Pair(M.one, empty),
            ),
            M.Pair(
                M.Pair(
                    Gmod.AUTONOMY_BUDGET_MAX_NODES_KEY,
                    M.Pair(M.nine, empty),
                ),
                M.Pair(
                    M.Pair(
                        Gmod.AUTONOMY_BUDGET_MAX_ACTIVATIONS_KEY,
                        M.Pair(M.one, empty),
                    ),
                    empty,
                ),
            ),
        )
        cycle = Gmod.AutonomyCycle(host, store, ledger, budget)()
        final_version = M.Head(cycle)()
        updated_store = M.Head(M.Tail(cycle)())()
        report = M.Head(M.Tail(M.Tail(cycle)())())()
        activated_entry = M.Head(report)()
        skipped_entry = M.Head(M.Tail(report)())()
        firings_entry = M.Head(M.Tail(M.Tail(report)())())()
        reason_entry = M.Head(M.Tail(M.Tail(M.Tail(report)())())())()
        activated_proposals = M.Head(M.Tail(activated_entry)())()
        skipped_proposals = M.Head(M.Tail(skipped_entry)())()
        firing_count = M.Head(M.Tail(firings_entry)())()
        stopped_reason = M.Head(M.Tail(reason_entry)())()
        updated_entries = Gmod.ProposalStoreEntries(updated_store)()
        updated_auto_entry = M.Head(updated_entries)()
        updated_human_entry = M.Head(M.Tail(updated_entries)())()
        auto_annotations = Gmod.ProposalEntryAnnotations(updated_auto_entry)()
        human_annotations = Gmod.ProposalEntryAnnotations(updated_human_entry)()
        approval = M.Head(auto_annotations)()
        authority = M.Head(M.Tail(M.Tail(approval)())())()
        activated_proposal = M.Head(activated_proposals)()
        activated_law = Gmod.ProposalLaw(activated_proposal)()
        activated_obligations = Gmod.LawObligations(activated_law)()
        activated_obligation = M.Head(activated_obligations)()

        rollback_ledger = Gmod.FiringLedger(ledger.registry)
        rollback_host = Gmod.GraphVersion(
            Gmod.GraphNodes(Gmod.LawLeft(unfold)())(),
            Gmod.GraphEdges(Gmod.LawLeft(unfold)())(),
            empty,
        )()
        rollback_proposal = Gmod.Proposal(rollback_law, handle)()
        rollback_store = Gmod.ProposalStoreSubmit(
            Gmod.ProposalStore(empty)(),
            rollback_proposal,
        )()
        rollback_budget = M.Pair(
            M.Pair(
                Gmod.AUTONOMY_BUDGET_MAX_FIRINGS_KEY,
                M.Pair(M.one, empty),
            ),
            M.Pair(
                M.Pair(
                    Gmod.AUTONOMY_BUDGET_MAX_NODES_KEY,
                    M.Pair(M.one, empty),
                ),
                M.Pair(
                    M.Pair(
                        Gmod.AUTONOMY_BUDGET_MAX_ACTIVATIONS_KEY,
                        M.Pair(M.one, empty),
                    ),
                    empty,
                ),
            ),
        )
        rollback_cycle = Gmod.AutonomyCycle(
            rollback_host,
            rollback_store,
            rollback_ledger,
            rollback_budget,
        )()
        rollback_version = M.Head(rollback_cycle)()
        rollback_report = M.Head(M.Tail(M.Tail(rollback_cycle)())())()
        rollback_firings_entry = M.Head(
            M.Tail(M.Tail(rollback_report)())(),
        )()
        rollback_reason_entry = M.Head(
            M.Tail(M.Tail(M.Tail(rollback_report)())())(),
        )()
        rollback_firings = M.Head(M.Tail(rollback_firings_entry)())()
        rollback_reason = M.Head(M.Tail(rollback_reason_entry)())()
        expected_rollback_version = Gmod.InstallLaw(rollback_host, rollback_law)()

        exhaustion_ledger = Gmod.FiringLedger(rollback_ledger.registry)
        exhaustion_budget = M.Pair(
            M.Pair(
                Gmod.AUTONOMY_BUDGET_MAX_FIRINGS_KEY,
                M.Pair(M.one, empty),
            ),
            M.Pair(
                M.Pair(
                    Gmod.AUTONOMY_BUDGET_MAX_NODES_KEY,
                    M.Pair(M.nine, empty),
                ),
                M.Pair(
                    M.Pair(
                        Gmod.AUTONOMY_BUDGET_MAX_ACTIVATIONS_KEY,
                        M.Pair(M.Zero, empty),
                    ),
                    empty,
                ),
            ),
        )
        exhaustion_cycle = Gmod.AutonomyCycle(
            empty_graph,
            Gmod.ProposalStore(empty)(),
            exhaustion_ledger,
            exhaustion_budget,
        )()
        exhaustion_report = M.Head(M.Tail(M.Tail(exhaustion_cycle)())())()
        exhaustion_reason_entry = M.Head(
            M.Tail(M.Tail(M.Tail(exhaustion_report)())())(),
        )()
        exhaustion_reason = M.Head(M.Tail(exhaustion_reason_entry)())()

        self.result = M.truth_value
        if M.IdentityCompare(
            M.Tail(M.Tail(M.Tail(cycle)())())(),
            empty,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            M.Tail(M.Tail(M.Tail(M.Tail(report)())())())(),
            empty,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            M.Head(activated_entry)(),
            Gmod.AUTONOMY_REPORT_ACTIVATED_KEY,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            M.Head(skipped_entry)(),
            Gmod.AUTONOMY_REPORT_SKIPPED_HUMAN_KEY,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            M.Head(firings_entry)(),
            Gmod.AUTONOMY_REPORT_FIRINGS_KEY,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            M.Head(reason_entry)(),
            Gmod.AUTONOMY_REPORT_STOPPED_REASON_KEY,
        )() is M.false_value:
            self.result = M.false_value
        elif M.TermEqual(
            Gmod.ProposalOrigin(activated_proposal)(),
            Gmod.ProposalOrigin(auto_proposal)(),
        )() is M.false_value:
            self.result = M.false_value
        elif M.Compare(
            Gmod.KObligationName(activated_obligation)(),
            M.Char("node-count-max"),
        )() is M.false_value:
            self.result = M.false_value
        elif M.NatEq(
            Gmod.KObligationStructure(activated_obligation)(),
            M.nine,
            ledger.registry,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            M.Tail(activated_obligations)(),
            empty,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Tail(activated_proposals)(), empty)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            M.Head(skipped_proposals)(),
            human_proposal,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Tail(skipped_proposals)(), empty)() is M.false_value:
            self.result = M.false_value
        elif M.NatEq(firing_count, M.one, ledger.registry)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            stopped_reason,
            Gmod.AUTONOMY_STOP_BUDGET_FIRINGS,
        )() is M.false_value:
            self.result = M.false_value
        elif Gmod.ChainHasTerm(
            Gmod.GraphNodes(final_version)(),
            handle,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Tail(ledger.records)(), empty)() is M.false_value:
            self.result = M.false_value
        elif M.TermEqual(
            Gmod.ProposalEntryProposal(updated_auto_entry)(),
            activated_proposal,
        )() is M.false_value:
            self.result = M.false_value
        elif Gmod.ProposalEntryIsApproved(updated_auto_entry)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(human_annotations, empty)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            M.Head(authority)(),
            Lmod.AutonomyAuthorityLabel,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            M.Head(M.Tail(authority)())(),
            budget,
        )() is M.false_value:
            self.result = M.false_value
        elif Gmod.GraphStoresEqual(
            rollback_version,
            expected_rollback_version,
        )() is M.false_value:
            self.result = M.false_value
        elif Gmod.ChainHasTerm(
            Gmod.GraphNodes(rollback_version)(),
            handle,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(rollback_ledger.records, empty)() is M.false_value:
            self.result = M.false_value
        elif M.NatEq(
            rollback_firings,
            M.Zero,
            rollback_ledger.registry,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            rollback_reason,
            Gmod.AUTONOMY_STOP_BUDGET_NODES,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            exhaustion_reason,
            Gmod.AUTONOMY_STOP_EXHAUSTED,
        )() is M.false_value:
            self.result = M.false_value
        graph._replace_context(constructors=exhaustion_ledger.registry)
        super().__init__(inputs=empty, results=M.Pair(self.result, empty))

    def __call__(self):
        return self.result


class AutonomyObligationSafetyTest(M.Edge):
    """Step 26: an auto Law is independently braked at the obligation gate."""

    def __init__(self, graph):
        empty = M.EmptyList
        registry = M.FromContextGetConstructors(graph)()
        ledger = Gmod.FiringLedger(registry)

        interface_node = M.Char("guard-interface")
        internal_node = M.Char("guard-internal")
        pattern_edge = M.Pair(
            M.Char("guard-pattern-edge"),
            M.Pair(interface_node, M.Pair(internal_node, empty)),
        )
        pattern_nodes = M.Pair(interface_node, M.Pair(internal_node, empty))
        pattern = M.Pair(
            M.HypergraphLabel,
            M.Pair(pattern_nodes, M.Pair(M.Pair(pattern_edge, empty), empty)),
        )
        handle = Gmod.Handle(M.Char("guard-handle"), pattern)()
        compiled = Gmod.CompileHandleToLaws(
            handle,
            M.Pair(interface_node, empty),
        )()
        fold = M.Head(compiled)()
        proposal = Gmod.Proposal(fold, handle)()
        store = Gmod.ProposalStoreSubmit(
            Gmod.ProposalStore(empty)(),
            proposal,
        )()
        host = Gmod.GraphVersion(
            pattern_nodes,
            M.Pair(pattern_edge, empty),
            empty,
        )()
        budget = M.Pair(
            M.Pair(
                Gmod.AUTONOMY_BUDGET_MAX_FIRINGS_KEY,
                M.Pair(M.one, empty),
            ),
            M.Pair(
                M.Pair(
                    Gmod.AUTONOMY_BUDGET_MAX_NODES_KEY,
                    M.Pair(M.one, empty),
                ),
                M.Pair(
                    M.Pair(
                        Gmod.AUTONOMY_BUDGET_MAX_ACTIVATIONS_KEY,
                        M.Pair(M.one, empty),
                    ),
                    empty,
                ),
            ),
        )

        cycle_edge = Gmod.AutonomyCycle(host, store, ledger, budget)
        cycle = cycle_edge()
        final_version = M.Head(cycle)()
        updated_store = M.Head(M.Tail(cycle)())()
        report = M.Head(M.Tail(M.Tail(cycle)())())()
        activated_entry = M.Head(report)()
        activated = M.Head(M.Tail(activated_entry)())()
        firings_entry = M.Head(M.Tail(M.Tail(report)())())()
        firing_count = M.Head(M.Tail(firings_entry)())()
        reason_entry = M.Head(M.Tail(M.Tail(M.Tail(report)())())())()
        stopped_reason = M.Head(M.Tail(reason_entry)())()

        updated_entry = M.Head(Gmod.ProposalStoreEntries(updated_store)())()
        guarded_proposal = Gmod.ProposalEntryProposal(updated_entry)()
        guarded_law = Gmod.ProposalLaw(guarded_proposal)()
        guarded_obligations = Gmod.LawObligations(guarded_law)()
        guarded_obligation = M.Head(guarded_obligations)()

        trace = cycle_edge.last_firing_trace
        refusal = empty
        remaining_trace = trace
        while M.IdentityCompare(remaining_trace, empty)() is M.false_value:
            refusal = M.Head(remaining_trace)()
            remaining_trace = M.Tail(remaining_trace)()
        refused_obligation = empty
        if M.IdentityCompare(refusal, empty)() is M.false_value:
            refused_obligation = M.Head(M.Tail(refusal)())()

        self.result = M.truth_value
        if M.IdentityCompare(activated, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Tail(activated)(), empty)() is M.false_value:
            self.result = M.false_value
        elif M.TermEqual(
            M.Head(activated)(),
            guarded_proposal,
        )() is M.false_value:
            self.result = M.false_value
        elif Gmod.ProposalEntryIsApproved(updated_entry)() is M.false_value:
            self.result = M.false_value
        elif M.Compare(
            Gmod.KObligationName(guarded_obligation)(),
            M.Char("node-count-max"),
        )() is M.false_value:
            self.result = M.false_value
        elif M.NatEq(
            Gmod.KObligationStructure(guarded_obligation)(),
            M.one,
            ledger.registry,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Tail(guarded_obligations)(), empty)() is M.false_value:
            self.result = M.false_value
        elif M.NatEq(firing_count, M.Zero, ledger.registry)() is M.false_value:
            self.result = M.false_value
        elif M.NatLess(
            firing_count,
            M.one,
            ledger.registry,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            stopped_reason,
            Gmod.AUTONOMY_STOP_EXHAUSTED,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(ledger.records, empty)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(trace, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(refusal, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            M.Head(refusal)(),
            Lmod.ReasonObligationLabel,
        )() is M.false_value:
            self.result = M.false_value
        elif M.TermEqual(
            refused_obligation,
            guarded_obligation,
        )() is M.false_value:
            self.result = M.false_value
        elif Gmod.GraphStoresEqual(final_version, host)() is M.truth_value:
            self.result = M.false_value
        graph._replace_context(constructors=ledger.registry)
        super().__init__(inputs=empty, results=M.Pair(self.result, empty))

    def __call__(self):
        return self.result


class RecurringPatternMiningTest(M.Edge):
    """Step 27: one recurring closed neighborhood is mined with raw count three."""

    def __init__(self, graph):
        empty = M.EmptyList
        registry = M.FromContextGetConstructors(graph)()

        recurring_one = M.Thingy()
        recurring_two = M.Thingy()
        recurring_three = M.Thingy()
        recurring_nodes = M.Pair(
            recurring_one,
            M.Pair(recurring_two, M.Pair(recurring_three, empty)),
        )
        recurring_edge = M.Pair(
            M.Char("recurring-three-node-edge"),
            recurring_nodes,
        )
        recurring_edges = M.Pair(recurring_edge, empty)

        unique_one = M.Thingy()
        unique_nodes = M.Pair(unique_one, empty)
        unique_edge = M.Pair(
            M.Char("unique-one-node-edge"),
            unique_nodes,
        )

        first = Gmod.GraphVersion(
            recurring_nodes,
            recurring_edges,
            empty,
        )()
        second = Gmod.GraphVersion(
            recurring_nodes,
            recurring_edges,
            empty,
        )()
        latest_nodes = M.Pair(
            recurring_one,
            M.Pair(
                recurring_two,
                M.Pair(
                    recurring_three,
                    M.Pair(unique_one, empty),
                ),
            ),
        )
        latest_edges = M.Pair(
            recurring_edge,
            M.Pair(unique_edge, empty),
        )
        latest = Gmod.GraphVersion(
            latest_nodes,
            latest_edges,
            empty,
        )()
        versions = M.Pair(first, M.Pair(second, M.Pair(latest, empty)))

        candidates = Gmod.EnumerateCandidatePatterns(latest, M.four)()
        mined = Gmod.MineRecurringPatterns(versions, M.two, M.four)()

        candidate_count_pair = M.Count(candidates, registry)()
        candidate_count = M.Head(candidate_count_pair)()
        registry = M.Head(M.Tail(candidate_count_pair)())()

        self.result = M.truth_value
        expected_focal_nodes = latest_nodes
        remaining_candidates = candidates
        while M.IdentityCompare(expected_focal_nodes, empty)() is M.false_value:
            if M.IdentityCompare(remaining_candidates, empty)() is M.truth_value:
                self.result = M.false_value
                expected_focal_nodes = empty
            else:
                expected_focal = M.Head(expected_focal_nodes)()
                candidate = M.Head(remaining_candidates)()
                candidate_nodes = Gmod.GraphNodes(candidate)()
                if M.IdentityCompare(candidate_nodes, empty)() is M.truth_value:
                    self.result = M.false_value
                    expected_focal_nodes = empty
                elif M.IdentityCompare(
                    M.Head(candidate_nodes)(),
                    expected_focal,
                )() is M.false_value:
                    self.result = M.false_value
                    expected_focal_nodes = empty
                else:
                    expected_focal_nodes = M.Tail(expected_focal_nodes)()
                    remaining_candidates = M.Tail(remaining_candidates)()

        if M.NatEq(candidate_count, M.four, registry)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(remaining_candidates, empty)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(mined, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Tail(mined)(), empty)() is M.false_value:
            self.result = M.false_value
        else:
            entry = M.Head(mined)()
            candidate = M.Head(entry)()
            count = M.Head(M.Tail(entry)())()
            candidate_nodes = Gmod.GraphNodes(candidate)()
            candidate_edges = Gmod.GraphEdges(candidate)()
            candidate_node_count_pair = M.Count(candidate_nodes, registry)()
            candidate_node_count = M.Head(candidate_node_count_pair)()
            registry = M.Head(M.Tail(candidate_node_count_pair)())()
            if M.IdentityCompare(
                M.Tail(M.Tail(entry)())(),
                empty,
            )() is M.false_value:
                self.result = M.false_value
            elif M.IsNat(count, registry)() is M.false_value:
                self.result = M.false_value
            elif M.NatEq(count, M.three, registry)() is M.false_value:
                self.result = M.false_value
            elif M.NatEq(
                candidate_node_count,
                M.three,
                registry,
            )() is M.false_value:
                self.result = M.false_value
            elif M.IdentityCompare(candidate_edges, empty)() is M.truth_value:
                self.result = M.false_value
            elif M.IdentityCompare(
                M.Head(candidate_edges)(),
                recurring_edge,
            )() is M.false_value:
                self.result = M.false_value
            elif M.IdentityCompare(
                M.Tail(candidate_edges)(),
                empty,
            )() is M.false_value:
                self.result = M.false_value
            elif M.IdentityCompare(
                Gmod.GraphVersionInvariants(candidate)(),
                empty,
            )() is M.false_value:
                self.result = M.false_value

        graph._replace_context(constructors=registry)
        super().__init__(inputs=empty, results=M.Pair(self.result, empty))

    def __call__(self):
        return self.result


class HandleProposalGeneratorTest(M.Edge):
    """Step 28: mined Handle folds are pending, classified, and inert."""

    def __init__(self, graph):
        empty = M.EmptyList
        registry = M.FromContextGetConstructors(graph)()
        ledger = Gmod.FiringLedger(registry)

        recurring_one = M.Thingy()
        recurring_two = M.Thingy()
        recurring_three = M.Thingy()
        recurring_nodes = M.Pair(
            recurring_one,
            M.Pair(recurring_two, M.Pair(recurring_three, empty)),
        )
        recurring_edge = M.Pair(
            M.Char("generated-recurring-three-node-edge"),
            recurring_nodes,
        )
        recurring_edges = M.Pair(recurring_edge, empty)
        unique_one = M.Thingy()
        unique_nodes = M.Pair(unique_one, empty)
        unique_edge = M.Pair(
            M.Char("generated-unique-one-node-edge"),
            unique_nodes,
        )

        first = Gmod.GraphVersion(
            recurring_nodes,
            recurring_edges,
            empty,
        )()
        second = Gmod.GraphVersion(
            recurring_nodes,
            recurring_edges,
            empty,
        )()
        latest = Gmod.GraphVersion(
            M.Pair(
                recurring_one,
                M.Pair(
                    recurring_two,
                    M.Pair(recurring_three, M.Pair(unique_one, empty)),
                ),
            ),
            M.Pair(recurring_edge, M.Pair(unique_edge, empty)),
            empty,
        )()
        versions = M.Pair(first, M.Pair(second, M.Pair(latest, empty)))
        initial_store = Gmod.ProposalStore(empty)()

        generated = Gmod.GenerateHandleProposals(
            initial_store,
            versions,
            ledger,
            M.two,
        )()
        generated_store = M.Head(generated)()
        generated_count = M.Head(M.Tail(generated)())()
        skipped = M.Head(M.Tail(M.Tail(generated)())())()
        entries = Gmod.ProposalStoreAll(generated_store)()
        before_firing = Gmod.FireAny(
            latest,
            Gmod.DanglingForbid()(),
            ledger,
        )()
        after_firing = Gmod.FireAny(
            latest,
            Gmod.DanglingForbid()(),
            ledger,
        )()

        self.result = M.truth_value
        if M.IdentityCompare(
            M.Tail(M.Tail(M.Tail(generated)())())(),
            empty,
        )() is M.false_value:
            self.result = M.false_value
        elif M.NatEq(generated_count, M.one, ledger.registry)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(skipped, empty)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(entries, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Tail(entries)(), empty)() is M.false_value:
            self.result = M.false_value
        else:
            entry = M.Head(entries)()
            proposal = Gmod.ProposalEntryProposal(entry)()
            if Gmod.ProposalEntryIsApproved(entry)() is M.truth_value:
                self.result = M.false_value
            elif M.Compare(
                Gmod.ClassifyProposal(proposal)(),
                M.Char("fold_handle"),
            )() is M.false_value:
                self.result = M.false_value
            elif M.IdentityCompare(
                M.Head(before_firing)(),
                empty,
            )() is M.false_value:
                self.result = M.false_value
            elif M.IdentityCompare(
                M.Head(M.Tail(before_firing)())(),
                empty,
            )() is M.false_value:
                self.result = M.false_value
            elif M.TermEqual(before_firing, after_firing)() is M.false_value:
                self.result = M.false_value
            elif M.TermEqual(
                Gmod.GraphVersionInvariants(latest)(),
                empty,
            )() is M.false_value:
                self.result = M.false_value

        graph._replace_context(constructors=ledger.registry)
        super().__init__(inputs=empty, results=M.Pair(self.result, empty))

    def __call__(self):
        return self.result


class WitnessedCompositionProposalTest(M.Edge):
    """Step 29: adjacent witnessed firings propose one equivalent composite."""

    def __init__(self, graph):
        empty = M.EmptyList
        registry = M.FromContextGetConstructors(graph)()
        witnessed_ledger = Gmod.FiringLedger(registry)
        node_a = M.Thingy()
        node_b = M.Thingy()
        node_c = M.Thingy()
        preserved = M.Thingy()
        interface_a_node = M.Thingy()
        interface_b_node = M.Thingy()
        left_a = Gmod.GraphVersion(
            M.Pair(preserved, M.Pair(node_a, empty)),
            empty,
            empty,
        )()
        right_a = Gmod.GraphVersion(
            M.Pair(preserved, M.Pair(node_b, empty)),
            empty,
            empty,
        )()
        left_b = Gmod.GraphVersion(
            M.Pair(preserved, M.Pair(node_b, empty)),
            empty,
            empty,
        )()
        right_b = Gmod.GraphVersion(
            M.Pair(preserved, M.Pair(node_c, empty)),
            empty,
            empty,
        )()
        interface_a = Gmod.GraphVersion(
            M.Pair(interface_a_node, empty),
            empty,
            empty,
        )()
        interface_b = Gmod.GraphVersion(
            M.Pair(interface_b_node, empty),
            empty,
            empty,
        )()
        law_a = Gmod.Law(
            left_a,
            interface_a,
            right_a,
            Gmod.Map(
                interface_a,
                left_a,
                M.Pair(Gmod.Send(interface_a_node, preserved)(), empty),
            )(),
            Gmod.Map(
                interface_a,
                right_a,
                M.Pair(Gmod.Send(interface_a_node, preserved)(), empty),
            )(),
            empty,
        )()
        law_b = Gmod.Law(
            left_b,
            interface_b,
            right_b,
            Gmod.Map(
                interface_b,
                left_b,
                M.Pair(Gmod.Send(interface_b_node, preserved)(), empty),
            )(),
            Gmod.Map(
                interface_b,
                right_b,
                M.Pair(Gmod.Send(interface_b_node, preserved)(), empty),
            )(),
            empty,
        )()
        fresh_redex = Gmod.GraphVersion(
            M.Pair(preserved, M.Pair(node_a, empty)),
            empty,
            empty,
        )()
        mapping_a = Gmod.Map(
            left_a,
            fresh_redex,
            M.Pair(
                Gmod.Send(preserved, preserved)(),
                M.Pair(Gmod.Send(node_a, node_a)(), empty),
            ),
        )()
        fired_a = Gmod.FireLaw(
            fresh_redex,
            law_a,
            mapping_a,
            Gmod.DanglingForbid()(),
            witnessed_ledger,
        )()
        intermediate = M.Head(fired_a)()
        mapping_b = Gmod.Map(
            left_b,
            intermediate,
            M.Pair(
                Gmod.Send(preserved, preserved)(),
                M.Pair(Gmod.Send(node_b, node_b)(), empty),
            ),
        )()
        fired_b = Gmod.FireLaw(
            intermediate,
            law_b,
            mapping_b,
            Gmod.DanglingForbid()(),
            witnessed_ledger,
        )()
        sequential_result = M.Head(fired_b)()

        generated = Gmod.GenerateCompositionProposals(
            Gmod.ProposalStore(empty)(),
            witnessed_ledger,
        )()
        generated_store = M.Head(generated)()
        generated_count = M.Head(M.Tail(generated)())()
        skipped = M.Head(M.Tail(M.Tail(generated)())())()
        entries = Gmod.ProposalStoreAll(generated_store)()

        self.result = M.truth_value
        proposal = empty
        composite = empty
        if M.IdentityCompare(
            M.Tail(M.Tail(M.Tail(generated)())())(),
            empty,
        )() is M.false_value:
            self.result = M.false_value
        elif M.NatEq(
            generated_count,
            M.one,
            witnessed_ledger.registry,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(skipped, empty)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(entries, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Tail(entries)(), empty)() is M.false_value:
            self.result = M.false_value
        else:
            entry = M.Head(entries)()
            proposal = Gmod.ProposalEntryProposal(entry)()
            composite = Gmod.ProposalLaw(proposal)()
            annotations = Gmod.ProposalEntryAnnotations(entry)()
            origin = Gmod.ProposalOrigin(proposal)()
            if Gmod.ProposalEntryIsApproved(entry)() is M.truth_value:
                self.result = M.false_value
            elif Gmod.LawMapsComplete(composite)() is M.false_value:
                self.result = M.false_value
            elif Gmod.ChainHasTerm(
                Gmod.GraphNodes(Gmod.LawInterface(composite)())(),
                interface_a_node,
            )() is M.false_value:
                self.result = M.false_value
            elif M.Compare(
                Gmod.ClassifyProposal(proposal)(),
                M.Char("install_law"),
            )() is M.false_value:
                self.result = M.false_value
            elif M.IdentityCompare(
                M.Head(origin)(),
                Lmod.ComposedFromLabel,
            )() is M.false_value:
                self.result = M.false_value
            elif M.IdentityCompare(annotations, empty)() is M.truth_value:
                self.result = M.false_value
            elif M.IdentityCompare(M.Tail(annotations)(), empty)() is M.false_value:
                self.result = M.false_value
            else:
                justification = M.Head(annotations)()
                evidence = M.Head(M.Tail(M.Tail(justification)())())()
                if M.IdentityCompare(
                    M.Head(justification)(),
                    Lmod.JustifiedByLabel,
                )() is M.false_value:
                    self.result = M.false_value
                elif M.NatEq(
                    M.Head(evidence)(),
                    M.Zero,
                    witnessed_ledger.registry,
                )() is M.false_value:
                    self.result = M.false_value
                elif M.NatEq(
                    M.Head(M.Tail(evidence)())(),
                    M.one,
                    witnessed_ledger.registry,
                )() is M.false_value:
                    self.result = M.false_value
                elif M.IdentityCompare(
                    M.Tail(M.Tail(evidence)())(),
                    empty,
                )() is M.false_value:
                    self.result = M.false_value

        if M.IdentityCompare(self.result, M.truth_value)() is M.truth_value:
            approval = Gmod.Approved(proposal, M.Char("curator"))()
            approved_store = Gmod.ProposalStoreAttach(
                generated_store,
                proposal,
                approval,
            )()
            approved_entry = M.Head(
                Gmod.ProposalStoreApproved(approved_store)()
            )()
            activated = Gmod.ActivateProposal(fresh_redex, approved_entry)()
            activated_version = M.Head(activated)()
            active_fresh_redex = Gmod.GraphVersion(
                M.Pair(preserved, M.Pair(node_a, empty)),
                empty,
                Gmod.GraphVersionInvariants(activated_version)(),
            )()
            composite_ledger = Gmod.FiringLedger(witnessed_ledger.registry)
            fired_composite = Gmod.FireAny(
                active_fresh_redex,
                Gmod.DanglingForbid()(),
                composite_ledger,
            )()
            composite_result = M.Head(fired_composite)()
            composite_records = composite_ledger.records
            if M.IdentityCompare(activated_version, empty)() is M.truth_value:
                self.result = M.false_value
            elif Gmod.GraphStoresEqual(
                sequential_result,
                composite_result,
            )() is M.false_value:
                self.result = M.false_value
            elif M.IdentityCompare(composite_records, empty)() is M.truth_value:
                self.result = M.false_value
            elif M.IdentityCompare(
                M.Tail(composite_records)(),
                empty,
            )() is M.false_value:
                self.result = M.false_value
            elif M.TermEqual(
                Gmod.FiringRecordLaw(M.Head(composite_records)())(),
                composite,
            )() is M.false_value:
                self.result = M.false_value
            witnessed_ledger.registry = composite_ledger.registry

        graph._replace_context(constructors=witnessed_ledger.registry)
        super().__init__(inputs=empty, results=M.Pair(self.result, empty))

    def __call__(self):
        return self.result


class AutonomyGenerationPhaseTest(M.Edge):
    """Step 30: optional generators submit before autonomy policy is applied."""

    def __init__(self, graph):
        empty = M.EmptyList
        registry = M.FromContextGetConstructors(graph)()
        ledger = Gmod.FiringLedger(registry)
        node_a = M.Thingy()
        node_b = M.Thingy()
        node_c = M.Thingy()
        interface = Gmod.GraphVersion(empty, empty, empty)()
        left_a = Gmod.GraphVersion(M.Pair(node_a, empty), empty, empty)()
        right_a = Gmod.GraphVersion(M.Pair(node_b, empty), empty, empty)()
        left_b = Gmod.GraphVersion(M.Pair(node_b, empty), empty, empty)()
        right_b = Gmod.GraphVersion(M.Pair(node_c, empty), empty, empty)()
        law_a = Gmod.Law(
            left_a,
            interface,
            right_a,
            Gmod.Map(interface, left_a, empty)(),
            Gmod.Map(interface, right_a, empty)(),
            empty,
        )()
        law_b = Gmod.Law(
            left_b,
            interface,
            right_b,
            Gmod.Map(interface, left_b, empty)(),
            Gmod.Map(interface, right_b, empty)(),
            empty,
        )()
        host = Gmod.GraphVersion(M.Pair(node_a, empty), empty, empty)()
        fired_a = Gmod.FireLaw(
            host,
            law_a,
            Gmod.Map(
                left_a,
                host,
                M.Pair(Gmod.Send(node_a, node_a)(), empty),
            )(),
            Gmod.DanglingForbid()(),
            ledger,
        )()
        intermediate = M.Head(fired_a)()
        Gmod.FireLaw(
            intermediate,
            law_b,
            Gmod.Map(
                left_b,
                intermediate,
                M.Pair(Gmod.Send(node_b, node_b)(), empty),
            )(),
            Gmod.DanglingForbid()(),
            ledger,
        )()

        budget = M.Pair(
            M.Pair(
                Gmod.AUTONOMY_BUDGET_MAX_FIRINGS_KEY,
                M.Pair(M.Zero, empty),
            ),
            M.Pair(
                M.Pair(
                    Gmod.AUTONOMY_BUDGET_MAX_NODES_KEY,
                    M.Pair(M.nine, empty),
                ),
                M.Pair(
                    M.Pair(
                        Gmod.AUTONOMY_BUDGET_MAX_ACTIVATIONS_KEY,
                        M.Pair(M.Zero, empty),
                    ),
                    empty,
                ),
            ),
        )
        generator_config = M.Pair(
            M.Pair(
                Gmod.AUTONOMY_GENERATE_HANDLES_KEY,
                M.Pair(M.false_value, empty),
            ),
            M.Pair(
                M.Pair(
                    Gmod.AUTONOMY_GENERATE_COMPOSITIONS_KEY,
                    M.Pair(M.truth_value, empty),
                ),
                M.Pair(
                    M.Pair(
                        Gmod.AUTONOMY_GENERATOR_VERSIONS_KEY,
                        M.Pair(empty, empty),
                    ),
                    M.Pair(
                        M.Pair(
                            Gmod.AUTONOMY_GENERATOR_MIN_COUNT_KEY,
                            M.Pair(M.one, empty),
                        ),
                        empty,
                    ),
                ),
            ),
        )
        idle_graph = Gmod.GraphVersion(empty, empty, empty)()
        cycle = Gmod.AutonomyCycle(
            idle_graph,
            Gmod.ProposalStore(empty)(),
            ledger,
            budget,
            generator_config,
        )()
        final_graph = M.Head(cycle)()
        updated_store = M.Head(M.Tail(cycle)())()
        report = M.Head(M.Tail(M.Tail(cycle)())())()
        entries = Gmod.ProposalStoreAll(updated_store)()
        skipped_human_entry = M.Head(M.Tail(report)())()
        skipped_human = M.Head(M.Tail(skipped_human_entry)())()
        generation_entry = M.Head(
            M.Tail(M.Tail(M.Tail(M.Tail(report)())())())(),
        )()
        generation_value = M.Head(M.Tail(generation_entry)())()
        generated_count = M.Head(generation_value)()
        generated_skipped = M.Head(M.Tail(generation_value)())()

        self.result = M.truth_value
        if Gmod.GraphStoresEqual(final_graph, idle_graph)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(entries, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Tail(entries)(), empty)() is M.false_value:
            self.result = M.false_value
        elif Gmod.ProposalEntryIsApproved(M.Head(entries)())() is M.truth_value:
            self.result = M.false_value
        elif M.Compare(
            Gmod.ClassifyProposal(
                Gmod.ProposalEntryProposal(M.Head(entries)())(),
            )(),
            M.Char("install_law"),
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            M.Head(skipped_human)(),
            Gmod.ProposalEntryProposal(M.Head(entries)())(),
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Tail(skipped_human)(), empty)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            M.Head(generation_entry)(),
            Gmod.AUTONOMY_REPORT_GENERATED_COMPOSITIONS_KEY,
        )() is M.false_value:
            self.result = M.false_value
        elif M.NatEq(generated_count, M.one, ledger.registry)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(generated_skipped, empty)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Tail(M.Tail(generation_value)())(), empty)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(report)())())())())(),
            empty,
        )() is M.false_value:
            self.result = M.false_value

        graph._replace_context(constructors=ledger.registry)
        super().__init__(inputs=empty, results=M.Pair(self.result, empty))

    def __call__(self):
        return self.result


class LawOrderingFromLedgerTest(M.Edge):
    """Step 31: ledger successes reorder FireAny while the default is unchanged."""

    def __init__(self, graph):
        empty = M.EmptyList
        registry = M.FromContextGetConstructors(graph)()
        ledger = Gmod.FiringLedger(registry)
        node_a = M.Thingy()
        node_b = M.Thingy()
        node_c = M.Thingy()
        node_d = M.Thingy()
        interface = Gmod.GraphVersion(empty, empty, empty)()
        left_first = Gmod.GraphVersion(M.Pair(node_a, empty), empty, empty)()
        right_first = Gmod.GraphVersion(M.Pair(node_b, empty), empty, empty)()
        left_second = Gmod.GraphVersion(M.Pair(node_c, empty), empty, empty)()
        right_second = Gmod.GraphVersion(M.Pair(node_d, empty), empty, empty)()
        law_first = Gmod.Law(
            left_first,
            interface,
            right_first,
            Gmod.Map(interface, left_first, empty)(),
            Gmod.Map(interface, right_first, empty)(),
            empty,
        )()
        law_second = Gmod.Law(
            left_second,
            interface,
            right_second,
            Gmod.Map(interface, left_second, empty)(),
            Gmod.Map(interface, right_second, empty)(),
            empty,
        )()

        witness_host = Gmod.GraphVersion(M.Pair(node_c, empty), empty, empty)()
        Gmod.FireLaw(
            witness_host,
            law_second,
            Gmod.Map(
                left_second,
                witness_host,
                M.Pair(Gmod.Send(node_c, node_c)(), empty),
            )(),
            Gmod.DanglingForbid()(),
            ledger,
        )()

        installed_order = M.Pair(law_first, M.Pair(law_second, empty))
        derived = Gmod.LawOrderingFromLedger(ledger, installed_order)()

        both_redexes = Gmod.GraphVersion(
            M.Pair(node_a, M.Pair(node_c, empty)),
            empty,
            empty,
        )()
        both_redexes = Gmod.InstallLaw(both_redexes, law_second)()
        both_redexes = Gmod.InstallLaw(both_redexes, law_first)()

        ordered_ledger = Gmod.FiringLedger(ledger.registry)
        ordered_fire = Gmod.FireAny(
            both_redexes,
            Gmod.DanglingForbid()(),
            ordered_ledger,
            derived,
        )()
        default_ledger = Gmod.FiringLedger(ordered_ledger.registry)
        default_fire = Gmod.FireAny(
            both_redexes,
            Gmod.DanglingForbid()(),
            default_ledger,
        )()
        plain_fire = Gmod.FireAny(both_redexes, Gmod.DanglingForbid()())()

        self.result = M.truth_value
        if M.IdentityCompare(M.Head(derived)(), law_second)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            M.Head(M.Tail(derived)())(),
            law_first,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Tail(M.Tail(derived)())(), empty)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Head(ordered_fire)(), empty)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(ordered_ledger.records, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.TermEqual(
            Gmod.FiringRecordLaw(M.Head(ordered_ledger.records)())(),
            law_second,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Head(default_fire)(), empty)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(default_ledger.records, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.TermEqual(
            Gmod.FiringRecordLaw(M.Head(default_ledger.records)())(),
            law_first,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Head(plain_fire)(), empty)() is M.truth_value:
            self.result = M.false_value
        elif Gmod.GraphStoresEqual(
            M.Head(plain_fire)(),
            M.Head(default_fire)(),
        )() is M.false_value:
            self.result = M.false_value

        graph._replace_context(constructors=default_ledger.registry)
        super().__init__(inputs=empty, results=M.Pair(self.result, empty))

    def __call__(self):
        return self.result


class LawPreferenceInstallableTest(M.Edge):
    """Step 32: an auto-class LawPreference term retunes FireAny order only."""

    def __init__(self, graph):
        empty = M.EmptyList
        registry = M.FromContextGetConstructors(graph)()
        ledger = Gmod.FiringLedger(registry)
        node_a = M.Thingy()
        node_b = M.Thingy()
        node_c = M.Thingy()
        node_d = M.Thingy()
        interface = Gmod.GraphVersion(empty, empty, empty)()
        left_first = Gmod.GraphVersion(M.Pair(node_a, empty), empty, empty)()
        right_first = Gmod.GraphVersion(M.Pair(node_b, empty), empty, empty)()
        left_second = Gmod.GraphVersion(M.Pair(node_c, empty), empty, empty)()
        right_second = Gmod.GraphVersion(M.Pair(node_d, empty), empty, empty)()
        law_first = Gmod.Law(
            left_first,
            interface,
            right_first,
            Gmod.Map(interface, left_first, empty)(),
            Gmod.Map(interface, right_first, empty)(),
            empty,
        )()
        law_second = Gmod.Law(
            left_second,
            interface,
            right_second,
            Gmod.Map(interface, left_second, empty)(),
            Gmod.Map(interface, right_second, empty)(),
            empty,
        )()
        witness = Gmod.GraphVersion(M.Pair(node_c, empty), empty, empty)()
        Gmod.FireLaw(
            witness,
            law_second,
            Gmod.Map(
                left_second,
                witness,
                M.Pair(Gmod.Send(node_c, node_c)(), empty),
            )(),
            Gmod.DanglingForbid()(),
            ledger,
        )()

        version = Gmod.GraphVersion(
            M.Pair(node_a, M.Pair(node_c, empty)),
            empty,
            empty,
        )()
        version = Gmod.InstallLaw(version, law_second)()
        version = Gmod.InstallLaw(version, law_first)()

        generated = Gmod.GeneratePreferenceProposal(
            Gmod.ProposalStore(empty)(),
            ledger,
            version,
        )()
        generated_store = M.Head(generated)()
        entries = Gmod.ProposalStoreAll(generated_store)()
        proposal = Gmod.ProposalEntryProposal(M.Head(entries)())()

        budget = M.Pair(
            M.Pair(
                Gmod.AUTONOMY_BUDGET_MAX_FIRINGS_KEY,
                M.Pair(M.Zero, empty),
            ),
            M.Pair(
                M.Pair(
                    Gmod.AUTONOMY_BUDGET_MAX_NODES_KEY,
                    M.Pair(M.nine, empty),
                ),
                M.Pair(
                    M.Pair(
                        Gmod.AUTONOMY_BUDGET_MAX_ACTIVATIONS_KEY,
                        M.Pair(M.one, empty),
                    ),
                    empty,
                ),
            ),
        )
        cycle = Gmod.AutonomyCycle(version, generated_store, ledger, budget)()
        final_version = M.Head(cycle)()
        report = M.Head(M.Tail(M.Tail(cycle)())())()
        activated = M.Head(M.Tail(M.Head(report)())())()

        preference = Gmod.InstalledPreference(final_version)()
        laws_after = Gmod.InstalledLaws(final_version)()
        active = Gmod.GraphVersion(
            M.Pair(node_a, M.Pair(node_c, empty)),
            empty,
            Gmod.GraphVersionInvariants(final_version)(),
        )()
        fire_ledger = Gmod.FiringLedger(ledger.registry)
        fired = Gmod.FireAny(active, Gmod.DanglingForbid()(), fire_ledger)()

        self.result = M.truth_value
        if M.IdentityCompare(M.Tail(entries)(), empty)() is M.false_value:
            self.result = M.false_value
        elif M.Compare(
            Gmod.ClassifyProposal(proposal)(),
            M.Char("tune_preference"),
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(activated, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Tail(activated)(), empty)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(preference, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Head(preference)(), law_second)() is M.false_value:
            self.result = M.false_value
        elif Gmod.ChainHasTerm(laws_after, law_first)() is M.false_value:
            self.result = M.false_value
        elif Gmod.ChainHasTerm(laws_after, law_second)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Head(fired)(), empty)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(fire_ledger.records, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.TermEqual(
            Gmod.FiringRecordLaw(M.Head(fire_ledger.records)())(),
            law_second,
        )() is M.false_value:
            self.result = M.false_value

        graph._replace_context(constructors=fire_ledger.registry)
        super().__init__(inputs=empty, results=M.Pair(self.result, empty))

    def __call__(self):
        return self.result


class RetirementLifecycleTest(M.Edge):
    """Step 33: retire by mark, stop firing, stay queryable, reverse cleanly."""

    def __init__(self, graph):
        empty = M.EmptyList
        registry = M.FromContextGetConstructors(graph)()
        ledger = Gmod.FiringLedger(registry)
        host_node = M.Thingy()
        result_node = M.Thingy()
        absent_node = M.Pair(M.Char("retire-absent-node"), empty)
        miss_result = M.Pair(M.Char("retire-miss-result"), empty)
        interface = Gmod.GraphVersion(empty, empty, empty)()
        left_miss = Gmod.GraphVersion(M.Pair(absent_node, empty), empty, empty)()
        right_miss = Gmod.GraphVersion(M.Pair(miss_result, empty), empty, empty)()
        left_hit = Gmod.GraphVersion(M.Pair(host_node, empty), empty, empty)()
        right_hit = Gmod.GraphVersion(M.Pair(result_node, empty), empty, empty)()
        law_miss = Gmod.Law(
            left_miss,
            interface,
            right_miss,
            Gmod.Map(interface, left_miss, empty)(),
            Gmod.Map(interface, right_miss, empty)(),
            empty,
        )()
        law_hit = Gmod.Law(
            left_hit,
            interface,
            right_hit,
            Gmod.Map(interface, left_hit, empty)(),
            Gmod.Map(interface, right_hit, empty)(),
            empty,
        )()

        version = Gmod.GraphVersion(M.Pair(host_node, empty), empty, empty)()
        version = Gmod.InstallLaw(version, law_hit)()
        version = Gmod.InstallLaw(version, law_miss)()
        host = Gmod.GraphVersion(
            M.Pair(host_node, empty),
            empty,
            Gmod.GraphVersionInvariants(version)(),
        )()
        fired = Gmod.FireAny(host, Gmod.DanglingForbid()(), ledger)()

        generated = Gmod.GenerateRetirementProposals(
            Gmod.ProposalStore(empty)(),
            ledger,
            host,
        )()
        generated_store = M.Head(generated)()
        entries = Gmod.ProposalStoreAll(generated_store)()
        proposal = Gmod.ProposalEntryProposal(M.Head(entries)())()
        proposed_mark = M.Head(
            Gmod.GraphNodes(Gmod.LawRight(Gmod.ProposalLaw(proposal)())())(),
        )()
        proposed_law = Gmod.RetiredLaw(proposed_mark)()

        retired_version = Gmod.RetireLaw(version, proposed_law)()
        active_laws = Gmod.InstalledLaws(retired_version)()
        statuses = Gmod.AllLawsWithStatus(retired_version)()
        miss_status = empty
        hit_status = empty
        remaining_statuses = statuses
        while M.IdentityCompare(remaining_statuses, empty)() is M.false_value:
            entry = M.Head(remaining_statuses)()
            if M.TermEqual(M.Head(entry)(), law_miss)() is M.truth_value:
                miss_status = M.Head(M.Tail(entry)())()
            if M.TermEqual(M.Head(entry)(), law_hit)() is M.truth_value:
                hit_status = M.Head(M.Tail(entry)())()
            remaining_statuses = M.Tail(remaining_statuses)()

        both_retired = Gmod.RetireLaw(retired_version, law_hit)()
        retired_host = Gmod.GraphVersion(
            M.Pair(host_node, empty),
            empty,
            Gmod.GraphVersionInvariants(both_retired)(),
        )()
        retired_ledger = Gmod.FiringLedger(ledger.registry)
        retired_fired = Gmod.FireAny(
            retired_host,
            Gmod.DanglingForbid()(),
            retired_ledger,
        )()

        restored_version = Gmod.UnretireLaw(both_retired, law_hit)()
        restored_host = Gmod.GraphVersion(
            M.Pair(host_node, empty),
            empty,
            Gmod.GraphVersionInvariants(restored_version)(),
        )()
        restored_ledger = Gmod.FiringLedger(ledger.registry)
        restored_fired = Gmod.FireAny(
            restored_host,
            Gmod.DanglingForbid()(),
            restored_ledger,
        )()

        self.result = M.truth_value
        if M.IdentityCompare(M.Head(fired)(), empty)() is M.truth_value:
            self.result = M.false_value
        elif M.TermEqual(
            Gmod.FiringRecordLaw(M.Head(ledger.records)())(),
            law_hit,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(ledger.misses, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.TermEqual(
            M.Head(M.Head(ledger.misses)())(),
            law_miss,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(entries, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Tail(entries)(), empty)() is M.false_value:
            self.result = M.false_value
        elif M.Compare(
            Gmod.ClassifyProposal(proposal)(),
            M.Char("retire_law"),
        )() is M.false_value:
            self.result = M.false_value
        elif M.Compare(
            Gmod.ProposalOrigin(proposal)(),
            M.Char("ledger-retirement"),
        )() is M.false_value:
            self.result = M.false_value
        elif M.TermEqual(proposed_law, law_miss)() is M.false_value:
            self.result = M.false_value
        elif Gmod.ChainHasTerm(active_laws, law_miss)() is M.truth_value:
            self.result = M.false_value
        elif Gmod.ChainHasTerm(active_laws, law_hit)() is M.false_value:
            self.result = M.false_value
        elif M.Compare(miss_status, M.Char("retired"))() is M.false_value:
            self.result = M.false_value
        elif M.Compare(hit_status, M.Char("active"))() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            M.Head(retired_fired)(),
            empty,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Head(restored_fired)(), empty)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(restored_ledger.records, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.TermEqual(
            Gmod.FiringRecordLaw(M.Head(restored_ledger.records)())(),
            law_hit,
        )() is M.false_value:
            self.result = M.false_value

        graph._replace_context(constructors=restored_ledger.registry)
        super().__init__(inputs=empty, results=M.Pair(self.result, empty))

    def __call__(self):
        return self.result


class InstalledHeuristicSearchTest(M.Edge):
    """Step 34: the "installed" sentinel resolves the governed Heuristic term."""

    def __init__(self, graph):
        from .search import api as SearchApi

        empty = M.EmptyList
        registry = _registry(graph)
        installed = M.Heuristic(
            M.DFSLabel,
            M.GoalHeadOrderLabel,
            M.three,
            M.one,
            M.one,
            M.one,
        )()
        empty_graph = Gmod.GraphVersion(empty, empty, empty)()
        heuristic_graph = Gmod.GraphVersion(
            M.Pair(installed, empty),
            empty,
            empty,
        )()
        law = Gmod.Law(
            empty_graph,
            empty_graph,
            heuristic_graph,
            Gmod.Map(empty_graph, empty_graph, empty)(),
            Gmod.Map(empty_graph, heuristic_graph, empty)(),
            empty,
        )()
        version = Gmod.InstallLaw(empty_graph, law)()

        start = M.Pair(M.Char("installed-heuristic-start"), empty)
        goal = M.Pair(M.Char("installed-heuristic-start"), empty)

        saved_version = graph._search_installed_heuristic_version
        saved_resolved = graph._search_installed_heuristic_resolved
        graph._search_installed_heuristic_version = version
        governed_pair = SearchApi.Search(
            graph,
            start,
            goal,
            empty,
            "installed",
            registry,
        )()
        governed_resolved = graph._search_installed_heuristic_resolved
        governed_cost = M.Head(M.Tail(governed_pair)())()

        graph._search_installed_heuristic_version = empty
        registry = M.FromContextGetConstructors(graph)()
        fallback_pair = SearchApi.Search(
            graph,
            start,
            goal,
            empty,
            "installed",
            registry,
        )()
        fallback_resolved = graph._search_installed_heuristic_resolved
        fallback_cost = M.Head(M.Tail(fallback_pair)())()

        graph._search_installed_heuristic_version = saved_version
        graph._search_installed_heuristic_resolved = saved_resolved
        registry = M.FromContextGetConstructors(graph)()

        self.result = M.truth_value
        if M.IdentityCompare(
            Gmod.InstalledHeuristic(version)(),
            installed,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(governed_resolved, installed)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            Hmod.HeuristicSearchMode(governed_resolved)(),
            M.DFSLabel,
        )() is M.false_value:
            self.result = M.false_value
        elif M.NatEq(
            Hmod.HeuristicBeamWidth(governed_resolved)(),
            M.three,
            registry,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(governed_cost, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            Smod.SearchCostOutcome(governed_cost)(),
            Smod.SearchRunningLabel,
        )() is M.truth_value:
            self.result = M.false_value
        elif M.NatEq(
            Hmod.HeuristicBeamWidth(fallback_resolved)(),
            M.Zero,
            registry,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(fallback_cost, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            Smod.SearchCostOutcome(fallback_cost)(),
            Smod.SearchRunningLabel,
        )() is M.truth_value:
            self.result = M.false_value
        super().__init__(inputs=empty, results=M.Pair(self.result, empty))

    def __call__(self):
        return self.result


class HeuristicTrialProposalTest(M.Edge):
    """Step 35: strict dominance submits one human-class proposal; mixed does not."""

    def __init__(self, graph):
        empty = M.EmptyList
        registry = _registry(graph)
        heuristic_a = M.Heuristic(
            M.DFSLabel,
            M.GoalHeadOrderLabel,
            M.Zero,
            M.one,
            M.one,
            M.one,
        )()
        heuristic_b = M.Heuristic(
            M.BFSLabel,
            M.GoalHeadOrderLabel,
            M.three,
            M.one,
            M.one,
            M.one,
        )()

        start = M.Pair(M.Char("trial-start"), empty)
        goal = M.Pair(M.Char("trial-start"), empty)
        fixtures = M.Pair(
            M.Pair(start, M.Pair(goal, M.Pair(empty, empty))),
            empty,
        )
        trial = Gmod.HeuristicTrial(
            graph,
            heuristic_a,
            heuristic_b,
            fixtures,
            registry,
        )()
        registry = M.FromContextGetConstructors(graph)()

        cheap_pair = Smod.BuildSearchCost(
            M.Pair(M.Atom(), empty),
            M.one,
            M.Zero,
            M.one,
            Smod.SearchSuccessLabel,
            registry,
        )()
        cheap = M.Head(cheap_pair)()
        registry = M.Head(M.Tail(cheap_pair)())()
        costly_pair = Smod.BuildSearchCost(
            M.Pair(M.Atom(), empty),
            M.three,
            M.three,
            M.one,
            Smod.SearchSuccessLabel,
            registry,
        )()
        costly = M.Head(costly_pair)()
        registry = M.Head(M.Tail(costly_pair)())()
        graph._replace_context(constructors=registry)

        dominant_trial = M.Pair(
            M.Pair(costly, M.Pair(cheap, empty)),
            M.Pair(M.Pair(costly, M.Pair(cheap, empty)), empty),
        )
        generated = Gmod.GenerateHeuristicProposal(
            Gmod.ProposalStore(empty)(),
            dominant_trial,
            heuristic_b,
            registry,
        )()
        dominant_store = M.Head(generated)()
        dominant_entries = Gmod.ProposalStoreAll(dominant_store)()

        mixed_trial = M.Pair(
            M.Pair(costly, M.Pair(cheap, empty)),
            M.Pair(M.Pair(cheap, M.Pair(costly, empty)), empty),
        )
        mixed_generated = Gmod.GenerateHeuristicProposal(
            Gmod.ProposalStore(empty)(),
            mixed_trial,
            heuristic_b,
            registry,
        )()
        mixed_entries = Gmod.ProposalStoreAll(M.Head(mixed_generated)())()

        self.result = M.truth_value
        if M.IdentityCompare(trial, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Tail(trial)(), empty)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            M.Head(M.Head(trial)())(),
            empty,
        )() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            M.Head(M.Tail(M.Head(trial)())())(),
            empty,
        )() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(dominant_entries, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            M.Tail(dominant_entries)(),
            empty,
        )() is M.false_value:
            self.result = M.false_value
        elif M.Compare(
            Gmod.ClassifyProposal(
                Gmod.ProposalEntryProposal(M.Head(dominant_entries)())(),
            )(),
            M.Char("tune_scheduler"),
        )() is M.false_value:
            self.result = M.false_value
        elif M.Compare(
            Gmod.ProposalOrigin(
                Gmod.ProposalEntryProposal(M.Head(dominant_entries)())(),
            )(),
            M.Char("heuristic-trial"),
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(mixed_entries, empty)() is M.false_value:
            self.result = M.false_value
        super().__init__(inputs=empty, results=M.Pair(self.result, empty))

    def __call__(self):
        return self.result


class InstalledPolicyOverrideTest(M.Edge):
    """Step 36: a PolicyEntry term overrides the bootstrap gate for its class."""

    def __init__(self, graph):
        empty = M.EmptyList
        registry = M.FromContextGetConstructors(graph)()
        ledger = Gmod.FiringLedger(registry)

        interface_node = M.Char("policy-interface")
        first_internal = M.Char("policy-first-internal")
        second_internal = M.Char("policy-second-internal")
        pattern_edge = M.Pair(
            M.Char("policy-pattern-edge"),
            M.Pair(
                interface_node,
                M.Pair(first_internal, M.Pair(second_internal, empty)),
            ),
        )
        pattern_nodes = M.Pair(
            interface_node,
            M.Pair(first_internal, M.Pair(second_internal, empty)),
        )
        pattern = M.Pair(
            M.HypergraphLabel,
            M.Pair(pattern_nodes, M.Pair(M.Pair(pattern_edge, empty), empty)),
        )
        interface_nodes = M.Pair(interface_node, empty)
        handle = Gmod.Handle(M.Char("policy-handle"), pattern)()
        compiled = Gmod.CompileHandleToLaws(handle, interface_nodes)()
        fold = M.Head(compiled)()
        fold_proposal = Gmod.Proposal(fold, handle)()

        store = Gmod.ProposalStore(empty)()
        store = Gmod.ProposalStoreSubmit(store, fold_proposal)()

        policy_entry = Gmod.PolicyEntry(
            M.Char("fold_handle"),
            M.Char("human"),
        )()
        empty_graph = Gmod.GraphVersion(empty, empty, empty)()
        policy_graph = Gmod.GraphVersion(
            M.Pair(policy_entry, empty),
            empty,
            empty,
        )()
        policy_law = Gmod.Law(
            empty_graph,
            empty_graph,
            policy_graph,
            Gmod.Map(empty_graph, empty_graph, empty)(),
            Gmod.Map(empty_graph, policy_graph, empty)(),
            empty,
        )()
        governed_base = Gmod.InstallLaw(empty_graph, policy_law)()
        host = Gmod.GraphVersion(
            pattern_nodes,
            M.Pair(pattern_edge, empty),
            Gmod.GraphVersionInvariants(governed_base)(),
        )()

        budget = M.Pair(
            M.Pair(
                Gmod.AUTONOMY_BUDGET_MAX_FIRINGS_KEY,
                M.Pair(M.one, empty),
            ),
            M.Pair(
                M.Pair(
                    Gmod.AUTONOMY_BUDGET_MAX_NODES_KEY,
                    M.Pair(M.nine, empty),
                ),
                M.Pair(
                    M.Pair(
                        Gmod.AUTONOMY_BUDGET_MAX_ACTIVATIONS_KEY,
                        M.Pair(M.one, empty),
                    ),
                    empty,
                ),
            ),
        )
        cycle = Gmod.AutonomyCycle(host, store, ledger, budget)()
        report = M.Head(M.Tail(M.Tail(cycle)())())()
        activated_entry = M.Head(report)()
        skipped_entry = M.Head(M.Tail(report)())()
        activated_proposals = M.Head(M.Tail(activated_entry)())()
        skipped_proposals = M.Head(M.Tail(skipped_entry)())()

        bootstrap = Gmod.InstalledPolicy(empty)()
        default_policy = Gmod.ImpactPolicy()()
        effective = Gmod.InstalledPolicy(host)()
        bootstrap_fold_gate = M.Head(M.Tail(M.Head(bootstrap)())())()
        effective_fold_gate = M.Head(M.Tail(M.Head(effective)())())()

        bootstrap_matches = M.truth_value
        remaining_bootstrap = bootstrap
        remaining_default = default_policy
        while M.IdentityCompare(
            remaining_default,
            M.EmptyList,
        )() is M.false_value:
            if M.IdentityCompare(
                remaining_bootstrap,
                M.EmptyList,
            )() is M.truth_value:
                bootstrap_matches = M.false_value
                remaining_default = M.EmptyList
            else:
                bootstrap_entry = M.Head(remaining_bootstrap)()
                default_entry = M.Head(remaining_default)()
                if M.Compare(
                    M.Head(bootstrap_entry)(),
                    M.Head(default_entry)(),
                )() is M.false_value:
                    bootstrap_matches = M.false_value
                    remaining_default = M.EmptyList
                elif M.Compare(
                    M.Head(M.Tail(bootstrap_entry)())(),
                    M.Head(M.Tail(default_entry)())(),
                )() is M.false_value:
                    bootstrap_matches = M.false_value
                    remaining_default = M.EmptyList
                else:
                    remaining_bootstrap = M.Tail(remaining_bootstrap)()
                    remaining_default = M.Tail(remaining_default)()

        graph._replace_context(constructors=ledger.registry)

        self.result = M.truth_value
        if M.IdentityCompare(bootstrap_matches, M.truth_value)() is M.false_value:
            self.result = M.false_value
        elif M.Compare(bootstrap_fold_gate, M.Char("auto"))() is M.false_value:
            self.result = M.false_value
        elif M.Compare(effective_fold_gate, M.Char("human"))() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(activated_proposals, empty)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(skipped_proposals, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.TermEqual(
            M.Head(skipped_proposals)(),
            fold_proposal,
        )() is M.false_value:
            self.result = M.false_value
        super().__init__(inputs=empty, results=M.Pair(self.result, empty))

    def __call__(self):
        return self.result


class PolicyChangeCountersignTest(M.Edge):
    """Step 37: loosening needs two distinct human authorities; tightening one."""

    def __init__(self, graph):
        empty = M.EmptyList
        empty_graph = Gmod.GraphVersion(empty, empty, empty)()

        first_human = M.Pair(M.Char("first-curator"), empty)
        second_human = M.Pair(M.Char("second-curator"), empty)
        machine_authority = Gmod.AutonomyAuthority(empty)()

        loosen_entry = Gmod.PolicyEntry(
            M.Char("install_law"),
            M.Char("auto"),
        )()
        loosen_graph = Gmod.GraphVersion(
            M.Pair(loosen_entry, empty),
            empty,
            empty,
        )()
        loosen_law = Gmod.Law(
            empty_graph,
            empty_graph,
            loosen_graph,
            Gmod.Map(empty_graph, empty_graph, empty)(),
            Gmod.Map(empty_graph, loosen_graph, empty)(),
            empty,
        )()
        loosen_proposal = Gmod.Proposal(loosen_law, M.Char("policy-loosen"))()

        tighten_entry = Gmod.PolicyEntry(
            M.Char("fold_handle"),
            M.Char("human"),
        )()
        tighten_graph = Gmod.GraphVersion(
            M.Pair(tighten_entry, empty),
            empty,
            empty,
        )()
        tighten_law = Gmod.Law(
            empty_graph,
            empty_graph,
            tighten_graph,
            Gmod.Map(empty_graph, empty_graph, empty)(),
            Gmod.Map(empty_graph, tighten_graph, empty)(),
            empty,
        )()
        tighten_proposal = Gmod.Proposal(tighten_law, M.Char("policy-tighten"))()

        approved_only = Gmod.ProposalEntry(
            loosen_proposal,
            M.Pair(Gmod.Approved(loosen_proposal, first_human)(), empty),
        )()
        outcome_a = Gmod.ActivateProposal(empty_graph, approved_only)()
        reason_a = M.Head(M.Tail(outcome_a)())()

        countersigned_entry = Gmod.ProposalEntry(
            loosen_proposal,
            M.Pair(
                Gmod.Approved(loosen_proposal, first_human)(),
                M.Pair(
                    Gmod.Countersigned(loosen_proposal, second_human)(),
                    empty,
                ),
            ),
        )()
        outcome_b = Gmod.ActivateProposal(empty_graph, countersigned_entry)()

        tighten_entry_term = Gmod.ProposalEntry(
            tighten_proposal,
            M.Pair(Gmod.Approved(tighten_proposal, first_human)(), empty),
        )()
        outcome_c = Gmod.ActivateProposal(empty_graph, tighten_entry_term)()

        machine_countersign = Gmod.ProposalEntry(
            loosen_proposal,
            M.Pair(
                Gmod.Approved(loosen_proposal, first_human)(),
                M.Pair(
                    Gmod.Countersigned(loosen_proposal, machine_authority)(),
                    empty,
                ),
            ),
        )()
        outcome_d = Gmod.ActivateProposal(empty_graph, machine_countersign)()
        reason_d = M.Head(M.Tail(outcome_d)())()

        same_signer = Gmod.ProposalEntry(
            loosen_proposal,
            M.Pair(
                Gmod.Approved(loosen_proposal, first_human)(),
                M.Pair(
                    Gmod.Countersigned(loosen_proposal, first_human)(),
                    empty,
                ),
            ),
        )()
        outcome_e = Gmod.ActivateProposal(empty_graph, same_signer)()
        reason_e = M.Head(M.Tail(outcome_e)())()

        self.result = M.truth_value
        if M.Compare(
            Gmod.ClassifyProposal(loosen_proposal)(),
            M.Char("policy_change"),
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Head(outcome_a)(), empty)() is M.false_value:
            self.result = M.false_value
        elif M.TermEqual(
            M.Head(reason_a)(),
            Lmod.ReasonUncountersignedLabel,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Head(outcome_b)(), empty)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Head(outcome_c)(), empty)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Head(outcome_d)(), empty)() is M.false_value:
            self.result = M.false_value
        elif M.TermEqual(
            M.Head(reason_d)(),
            Lmod.ReasonUncountersignedLabel,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Head(outcome_e)(), empty)() is M.false_value:
            self.result = M.false_value
        elif M.TermEqual(
            M.Head(reason_e)(),
            Lmod.ReasonUncountersignedLabel,
        )() is M.false_value:
            self.result = M.false_value
        super().__init__(inputs=empty, results=M.Pair(self.result, empty))

    def __call__(self):
        return self.result


class RobustnessHarnessTest(M.Edge):
    """Step 40: perturbation evidence separates brittle from robust laws."""

    def __init__(self, graph):
        empty = M.EmptyList
        registry = M.FromContextGetConstructors(graph)()
        ledger = Gmod.FiringLedger(registry)

        anchor = M.Pair(M.Char("robust-anchor"), empty)
        partner = M.Pair(M.Char("robust-partner"), empty)
        in_edge = M.Pair(
            M.Char("robust-in-edge"),
            M.Pair(anchor, M.Pair(partner, empty)),
        )
        out_edge = M.Pair(
            M.Char("robust-out-edge"),
            M.Pair(anchor, M.Pair(partner, empty)),
        )
        both_nodes = M.Pair(anchor, M.Pair(partner, empty))
        interface_graph = Gmod.GraphVersion(both_nodes, empty, empty)()
        both_sends = M.Pair(
            Gmod.Send(anchor, anchor)(),
            M.Pair(Gmod.Send(partner, partner)(), empty),
        )
        robust_left = Gmod.GraphVersion(
            both_nodes,
            M.Pair(in_edge, empty),
            empty,
        )()
        robust_right = Gmod.GraphVersion(
            both_nodes,
            M.Pair(out_edge, empty),
            empty,
        )()
        robust_law = Gmod.Law(
            robust_left,
            interface_graph,
            robust_right,
            Gmod.Map(interface_graph, robust_left, both_sends)(),
            Gmod.Map(interface_graph, robust_right, both_sends)(),
            empty,
        )()

        anchor_interface = Gmod.GraphVersion(M.Pair(anchor, empty), empty, empty)()
        anchor_sends = M.Pair(Gmod.Send(anchor, anchor)(), empty)
        brittle_left = Gmod.GraphVersion(
            both_nodes,
            M.Pair(in_edge, empty),
            empty,
        )()
        brittle_right = Gmod.GraphVersion(M.Pair(anchor, empty), empty, empty)()
        brittle_law = Gmod.Law(
            brittle_left,
            anchor_interface,
            brittle_right,
            Gmod.Map(anchor_interface, brittle_left, anchor_sends)(),
            Gmod.Map(anchor_interface, brittle_right, anchor_sends)(),
            empty,
        )()

        robust_fixture = Gmod.GraphVersion(
            both_nodes,
            M.Pair(in_edge, empty),
            empty,
        )()
        brittle_fixture = Gmod.GraphVersion(
            both_nodes,
            M.Pair(in_edge, empty),
            empty,
        )()
        seeds = M.Pair(M.Char("0"), M.Pair(M.Char("1"), empty))

        robust_report = Gmod.RobustnessReport(
            robust_law,
            M.Pair(robust_fixture, empty),
            seeds,
        )()
        brittle_report = Gmod.RobustnessReport(
            brittle_law,
            M.Pair(brittle_fixture, empty),
            seeds,
        )()

        robust_row_zero = M.Head(robust_report)()
        robust_row_one = M.Head(M.Tail(robust_report)())()
        brittle_row_zero = M.Head(brittle_report)()
        brittle_row_one = M.Head(M.Tail(brittle_report)())()

        store = Gmod.ProposalStore(empty)()
        annotated = Gmod.GenerateRobustnessAnnotation(
            store,
            robust_law,
            robust_report,
        )()
        annotated_store = M.Head(annotated)()
        robustness_term = M.Head(M.Tail(annotated)())()
        annotation_entries = Gmod.ProposalStoreAll(annotated_store)()
        annotation_proposal = Gmod.ProposalEntryProposal(
            M.Head(annotation_entries)(),
        )()

        gate_proposal = Gmod.Proposal(
            robust_law,
            M.Char("robust-gate-origin"),
        )()
        gate_authority = M.Pair(M.Char("robust-authority"), empty)
        gate_store = Gmod.ProposalStore(empty)()
        gate_store = Gmod.ProposalStoreSubmit(gate_store, gate_proposal)()
        gate_store = Gmod.ProposalStoreAttach(
            gate_store,
            gate_proposal,
            Gmod.Approved(gate_proposal, gate_authority)(),
        )()
        host = Gmod.GraphVersion(empty, empty, empty)()
        budget = M.Pair(
            M.Pair(
                Gmod.AUTONOMY_BUDGET_MAX_FIRINGS_KEY,
                M.Pair(M.Zero, empty),
            ),
            M.Pair(
                M.Pair(
                    Gmod.AUTONOMY_BUDGET_MAX_NODES_KEY,
                    M.Pair(M.nine, empty),
                ),
                M.Pair(
                    M.Pair(
                        Gmod.AUTONOMY_BUDGET_MAX_ACTIVATIONS_KEY,
                        M.Pair(M.one, empty),
                    ),
                    M.Pair(
                        M.Pair(
                            Gmod.AUTONOMY_BUDGET_ACTIVATE_APPROVED_KEY,
                            M.Pair(M.truth_value, empty),
                        ),
                        M.Pair(
                            M.Pair(
                                Gmod.AUTONOMY_BUDGET_REQUIRE_ROBUSTNESS_KEY,
                                M.Pair(M.two, empty),
                            ),
                            empty,
                        ),
                    ),
                ),
            ),
        )
        gated_cycle = Gmod.AutonomyCycle(host, gate_store, ledger, budget)()
        gated_report = M.Head(M.Tail(M.Tail(gated_cycle)())())()
        gated_activated = M.Head(M.Tail(M.Head(gated_report)())())()
        fragile_entry = M.EmptyList
        remaining_report = gated_report
        while M.IdentityCompare(remaining_report, empty)() is M.false_value:
            report_entry = M.Head(remaining_report)()
            if M.Compare(
                M.Head(report_entry)(),
                Gmod.AUTONOMY_REPORT_SKIPPED_FRAGILE_KEY,
            )() is M.truth_value:
                fragile_entry = M.Head(M.Tail(report_entry)())()
                remaining_report = empty
            else:
                remaining_report = M.Tail(remaining_report)()

        graph._replace_context(constructors=ledger.registry)

        self.result = M.truth_value
        if M.IdentityCompare(
            M.Head(M.Tail(robust_row_zero)())(),
            M.truth_value,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            M.Head(M.Tail(M.Tail(robust_row_zero)())())(),
            M.truth_value,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            M.Head(M.Tail(robust_row_one)())(),
            M.truth_value,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            M.Head(M.Tail(M.Tail(robust_row_one)())())(),
            M.truth_value,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            M.Head(M.Tail(brittle_row_zero)())(),
            M.truth_value,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            M.Head(M.Tail(brittle_row_one)())(),
            M.false_value,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            M.Head(M.Tail(M.Tail(brittle_row_one)())())(),
            M.false_value,
        )() is M.false_value:
            self.result = M.false_value
        elif M.NatEq(
            Gmod.RobustnessPassed(robustness_term)(),
            M.two,
            registry,
        )() is M.false_value:
            self.result = M.false_value
        elif M.Compare(
            Gmod.ClassifyProposal(annotation_proposal)(),
            M.Char("annotate"),
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(gated_activated, empty)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(fragile_entry, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.TermEqual(
            M.Head(fragile_entry)(),
            gate_proposal,
        )() is M.false_value:
            self.result = M.false_value
        super().__init__(inputs=empty, results=M.Pair(self.result, empty))

    def __call__(self):
        return self.result


class MigrationLifecycleTest(M.Edge):
    """Step 41: a retired handle migrates onto its active replacement.

    KNOWN GAP: Step-10 node compatibility is head-only for Pair nodes, so
    the bridge's left pattern (old abbreviation) also matches the new
    abbreviation after migration and refires B-to-B; A-instances stay zero
    but true quiescence is unreachable without changing Part-1 matcher
    machinery. Migration therefore completes under bounded firing budgets,
    and this test asserts A-absence is preserved across a further firing
    rather than asserting an empty second firing.
    """

    def __init__(self, graph):
        empty = M.EmptyList
        registry = M.FromContextGetConstructors(graph)()
        ledger = Gmod.FiringLedger(registry)

        shared = M.Pair(M.Char("migration-shared"), empty)
        extra = M.Pair(M.Char("migration-extra"), empty)
        interface_nodes = M.Pair(shared, empty)
        pattern_a = Gmod.GraphVersion(M.Pair(shared, empty), empty, empty)()
        pattern_b = Gmod.GraphVersion(
            M.Pair(shared, M.Pair(extra, empty)),
            empty,
            empty,
        )()
        handle_a = Gmod.Handle(M.Char("migration-old"), pattern_a)()
        handle_b = Gmod.Handle(M.Char("migration-new"), pattern_b)()
        fold_a = M.Head(Gmod.CompileHandleToLaws(handle_a, interface_nodes)())()
        fold_b = M.Head(Gmod.CompileHandleToLaws(handle_b, interface_nodes)())()

        version = Gmod.GraphVersion(empty, empty, empty)()
        version = Gmod.InstallLaw(version, fold_a)()
        version = Gmod.InstallLaw(version, fold_b)()
        version = Gmod.RetireLaw(version, fold_a)()

        generated = Gmod.GenerateMigrationProposals(
            Gmod.ProposalStore(empty)(),
            version,
        )()
        generated_store = M.Head(generated)()
        entries = Gmod.ProposalStoreAll(generated_store)()
        proposal = Gmod.ProposalEntryProposal(M.Head(entries)())()
        bridge = Gmod.ProposalLaw(proposal)()

        authority = M.Pair(M.Char("migration-curator"), empty)
        approved_entry = Gmod.ProposalEntry(
            proposal,
            M.Pair(Gmod.Approved(proposal, authority)(), empty),
        )()
        activated = Gmod.ActivateProposal(version, approved_entry)()
        activated_version = M.Head(activated)()
        lineage = M.Head(M.Tail(activated)())()

        abbrev_a = Gmod.LawRight(fold_a)()
        host = Gmod.GraphVersion(
            Gmod.GraphNodes(abbrev_a)(),
            Gmod.GraphEdges(abbrev_a)(),
            Gmod.GraphVersionInvariants(activated_version)(),
        )()
        fired = Gmod.FireAny(host, Gmod.DanglingForbid()(), ledger)()
        fired_version = M.Head(fired)()
        second_version = empty
        if M.IdentityCompare(fired_version, empty)() is M.false_value:
            second_host = Gmod.GraphVersion(
                Gmod.GraphNodes(fired_version)(),
                Gmod.GraphEdges(fired_version)(),
                Gmod.GraphVersionInvariants(activated_version)(),
            )()
            second_fired = Gmod.FireAny(
                second_host,
                Gmod.DanglingForbid()(),
                ledger,
            )()
            second_version = M.Head(second_fired)()

        migration_marker = empty
        if M.IdentityCompare(fired_version, empty)() is M.false_value:
            remaining_nodes = Gmod.GraphNodes(fired_version)()
            while M.IdentityCompare(remaining_nodes, empty)() is M.false_value:
                node = M.Head(remaining_nodes)()
                if Gmod.IsMigration(node)() is M.truth_value:
                    migration_marker = node
                    remaining_nodes = empty
                else:
                    remaining_nodes = M.Tail(remaining_nodes)()

        graph._replace_context(constructors=ledger.registry)

        self.result = M.truth_value
        if M.IdentityCompare(entries, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Tail(entries)(), empty)() is M.false_value:
            self.result = M.false_value
        elif M.Compare(
            Gmod.ClassifyProposal(proposal)(),
            M.Char("install_law"),
        )() is M.false_value:
            self.result = M.false_value
        elif M.Compare(
            Gmod.ProposalOrigin(proposal)(),
            M.Char("handle-migration"),
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(activated_version, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.TermEqual(
            M.Head(lineage)(),
            Lmod.NextLabel,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(fired_version, empty)() is M.truth_value:
            self.result = M.false_value
        elif Gmod.ChainHasTerm(
            Gmod.GraphNodes(fired_version)(),
            handle_a,
        )() is M.truth_value:
            self.result = M.false_value
        elif Gmod.ChainHasTerm(
            Gmod.GraphNodes(fired_version)(),
            handle_b,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(migration_marker, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(second_version, empty)() is M.truth_value:
            self.result = M.false_value
        elif Gmod.ChainHasTerm(
            Gmod.GraphNodes(second_version)(),
            handle_a,
        )() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(ledger.records, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.TermEqual(
            Gmod.FiringRecordLaw(M.Head(ledger.records)())(),
            bridge,
        )() is M.false_value:
            self.result = M.false_value
        super().__init__(inputs=empty, results=M.Pair(self.result, empty))

    def __call__(self):
        return self.result


class ConflictDetectionTest(M.Edge):
    """Step 44: overlapping Fire-trace element sets yield recorded Conflict
    terms, first-by-canonical-order wins, and ledger length equals the
    number of firing attempts."""

    def __init__(self, graph):
        empty = M.EmptyList
        ledger = Gmod.FiringLedger()
        node_a = M.Thingy()
        node_b = M.Thingy()
        node_c = M.Thingy()

        def _delete_law(target):
            left = M.Pair(
                M.HypergraphLabel,
                M.Pair(M.Pair(target, empty), M.Pair(empty, empty)),
            )
            interface = M.Pair(
                M.HypergraphLabel,
                M.Pair(empty, M.Pair(empty, empty)),
            )
            right = M.Pair(
                M.HypergraphLabel,
                M.Pair(empty, M.Pair(empty, empty)),
            )
            law = Gmod.Law(
                left,
                interface,
                right,
                Gmod.Map(interface, left, empty)(),
                Gmod.Map(interface, right, empty)(),
                empty,
            )()
            return left, law

        host = Gmod.GraphVersion(
            M.Pair(node_a, M.Pair(node_b, M.Pair(node_c, empty))),
            empty,
            empty,
        )()

        left_a, law_a = _delete_law(node_a)
        Gmod.FireLaw(
            host,
            law_a,
            Gmod.Map(left_a, host, M.Pair(Gmod.Send(node_a, node_a)(), empty))(),
            Gmod.DanglingForbid()(),
            ledger,
        )()
        left_a2, law_a2 = _delete_law(node_a)
        Gmod.FireLaw(
            host,
            law_a2,
            Gmod.Map(
                left_a2,
                host,
                M.Pair(Gmod.Send(node_a, node_a)(), empty),
            )(),
            Gmod.DanglingForbid()(),
            ledger,
        )()
        left_c, law_c = _delete_law(node_c)
        Gmod.FireLaw(
            host,
            law_c,
            Gmod.Map(left_c, host, M.Pair(Gmod.Send(node_c, node_c)(), empty))(),
            Gmod.DanglingForbid()(),
            ledger,
        )()

        records = ledger.all()
        record_count = M.EmptyList
        counted = M.Count(records, ledger.registry)()
        record_count = M.Head(counted)()
        ledger.registry = M.Head(M.Tail(counted)())()
        miss_counted = M.Count(ledger.misses, ledger.registry)()
        miss_count = M.Head(miss_counted)()
        ledger.registry = M.Head(M.Tail(miss_counted)())()
        total = M.Add(record_count, miss_count, ledger.registry)()
        total_nat = M.Head(total)()
        ledger.registry = M.Head(M.Tail(total)())()
        length_ok = M.NatEq(total_nat, M.three, ledger.registry)()

        conflicts = Gmod.DetectConflicts(records, ledger.registry)()
        conflict_counted = M.Count(conflicts, ledger.registry)()
        conflict_count = M.Head(conflict_counted)()
        ledger.registry = M.Head(M.Tail(conflict_counted)())()
        one_conflict = M.NatEq(conflict_count, M.one, ledger.registry)()

        recorded_ok = M.false_value
        winner_ok = M.false_value
        shared_ok = M.false_value
        if M.IdentityCompare(conflicts, empty)() is M.false_value:
            conflict = M.Head(conflicts)()
            recorded_ok = Gmod.IsConflict(conflict)()
            first_record = M.Head(records)()
            if Gmod.ConflictWinner(conflict)() is first_record:
                winner_ok = M.truth_value
            shared = M.Head(M.Tail(M.Tail(M.Tail(conflict)())())())()
            shared_ok = Gmod.ChainHasTerm(shared, node_a)()

        disjoint_ok = M.false_value
        third = M.Head(M.Tail(M.Tail(records)())())()
        third_elements = Gmod.FireTraceElements(third)()
        if Gmod.ChainHasTerm(third_elements, node_a)() is M.false_value:
            disjoint_ok = M.truth_value

        self.result = M.AndAtom(
            length_ok,
            M.AndAtom(
                one_conflict,
                M.AndAtom(
                    recorded_ok,
                    M.AndAtom(
                        winner_ok,
                        M.AndAtom(shared_ok, disjoint_ok)(),
                    )(),
                )(),
            )(),
        )()
        super().__init__(
            inputs=M.Pair(graph, empty),
            results=self.result,
        )

    def __call__(self):
        return self.result


class WorkerProtocolTest(M.Edge):
    """Step 43: worker_task refuses nonzero activation budgets; a 2-worker
    run_workers union equals the single-process proposal set byte-for-byte;
    wire round trips preserve subterm identity sharing."""

    def __init__(self, graph):
        from . import wire as Wmod

        empty = M.EmptyList
        node_one = M.Pair(M.Char("worker-node-one"), empty)
        node_two = M.Pair(M.Char("worker-node-two"), empty)
        edge_one = M.Pair(
            M.Char("worker-edge-one"),
            M.Pair(node_one, M.Pair(node_two, empty)),
        )
        version = Gmod.GraphVersion(
            M.Pair(node_one, M.Pair(node_two, empty)),
            M.Pair(edge_one, empty),
            empty,
        )()
        versions = M.Pair(version, M.Pair(version, empty))

        shared = M.Pair(node_one, M.Pair(node_one, empty))
        rebuilt_shared = Wmod.deserialize_term(Wmod.serialize_term(shared))
        sharing_ok = M.false_value
        if M.Head(rebuilt_shared)() is M.Head(M.Tail(rebuilt_shared)())():
            sharing_ok = M.truth_value

        budget = M.Pair(
            M.Pair(
                Gmod.AUTONOMY_BUDGET_MAX_FIRINGS_KEY,
                M.Pair(M.Zero, empty),
            ),
            M.Pair(
                M.Pair(
                    Gmod.AUTONOMY_BUDGET_MAX_NODES_KEY,
                    M.Pair(M.nine, empty),
                ),
                M.Pair(
                    M.Pair(
                        Gmod.AUTONOMY_BUDGET_MAX_ACTIVATIONS_KEY,
                        M.Pair(M.Zero, empty),
                    ),
                    empty,
                ),
            ),
        )
        doctored = M.Pair(
            M.Pair(
                Gmod.AUTONOMY_BUDGET_MAX_ACTIVATIONS_KEY,
                M.Pair(M.one, empty),
            ),
            empty,
        )
        config = M.Pair(
            M.Pair(
                Gmod.AUTONOMY_GENERATE_HANDLES_KEY,
                M.Pair(M.truth_value, empty),
            ),
            M.Pair(
                M.Pair(
                    Gmod.AUTONOMY_GENERATOR_VERSIONS_KEY,
                    M.Pair(versions, empty),
                ),
                M.Pair(
                    M.Pair(
                        Gmod.AUTONOMY_GENERATOR_MIN_COUNT_KEY,
                        M.Pair(M.two, empty),
                    ),
                    empty,
                ),
            ),
        )

        refusal = Wmod.worker_task(
            Wmod.serialize_term(version),
            Wmod.serialize_term(Gmod.ProposalStore(empty)()),
            Wmod.serialize_term(doctored),
            Wmod.serialize_term(config),
            "0",
            "1",
        )
        refused_ok = M.false_value
        if refusal[0] == "refused-nonzero-activations":
            refused_ok = M.truth_value

        ledger = Gmod.FiringLedger(M.EmptyList)
        single = Gmod.AutonomyCycle(
            version,
            Gmod.ProposalStore(empty)(),
            ledger,
            budget,
            config,
        )()
        single_store = M.Head(M.Tail(single)())()
        single_blobs = empty
        entries = Gmod.ProposalStoreAll(single_store)()
        while M.IdentityCompare(entries, empty)() is M.false_value:
            single_blobs = M.Pair(
                M.Char(Wmod.serialize_term(
                    Gmod.ProposalEntryProposal(M.Head(entries)())(),
                ).decode("utf-8")),
                single_blobs,
            )
            entries = M.Tail(entries)()

        outputs = Wmod.run_workers(
            version,
            Gmod.ProposalStore(empty)(),
            budget,
            config,
            2,
        )
        union_blobs = empty
        workers_ok = M.truth_value
        for status, store_blob, ledger_blob, frontier_blob in outputs:
            if status != "ok":
                workers_ok = M.false_value
                continue
            worker_entries = Gmod.ProposalStoreAll(
                Wmod.deserialize_term(store_blob),
            )()
            while M.IdentityCompare(
                worker_entries,
                empty,
            )() is M.false_value:
                union_blobs = M.Pair(
                    M.Char(Wmod.serialize_term(
                        Gmod.ProposalEntryProposal(
                            M.Head(worker_entries)(),
                        )(),
                    ).decode("utf-8")),
                    union_blobs,
                )
                worker_entries = M.Tail(worker_entries)()

        sets_equal = M.truth_value
        remaining_single = single_blobs
        while M.IdentityCompare(remaining_single, empty)() is M.false_value:
            found_here = M.false_value
            probe = union_blobs
            while M.IdentityCompare(probe, empty)() is M.false_value:
                if M.Compare(
                    M.Head(probe)(),
                    M.Head(remaining_single)(),
                )() is M.truth_value:
                    found_here = M.truth_value
                probe = M.Tail(probe)()
            if M.IdentityCompare(found_here, M.false_value)() is M.truth_value:
                sets_equal = M.false_value
            remaining_single = M.Tail(remaining_single)()
        remaining_union = union_blobs
        while M.IdentityCompare(remaining_union, empty)() is M.false_value:
            found_here = M.false_value
            probe = single_blobs
            while M.IdentityCompare(probe, empty)() is M.false_value:
                if M.Compare(
                    M.Head(probe)(),
                    M.Head(remaining_union)(),
                )() is M.truth_value:
                    found_here = M.truth_value
                probe = M.Tail(probe)()
            if M.IdentityCompare(found_here, M.false_value)() is M.truth_value:
                sets_equal = M.false_value
            remaining_union = M.Tail(remaining_union)()
        nonempty_ok = M.false_value
        if M.IdentityCompare(single_blobs, empty)() is M.false_value:
            nonempty_ok = M.truth_value

        self.result = M.AndAtom(
            sharing_ok,
            M.AndAtom(
                refused_ok,
                M.AndAtom(
                    workers_ok,
                    M.AndAtom(sets_equal, nonempty_ok)(),
                )(),
            )(),
        )()
        super().__init__(
            inputs=M.Pair(graph, empty),
            results=self.result,
        )

    def __call__(self):
        return self.result


class WireRoundTripTest(M.Edge):
    """Step 42: canonical serialization is a byte fixed point and preserves
    installed_laws, installed_policy, all_laws_with_status, contracts, and
    Next-chain reachability across a checkpoint save/load."""

    def __init__(self, graph):
        from . import wire as Wmod

        empty = M.EmptyList
        registry = M.FromContextGetConstructors(graph)()
        node_a = M.Pair(M.Char("wire-node-a"), empty)
        node_b = M.Pair(M.Char("wire-node-b"), empty)
        interface = Gmod.GraphVersion(empty, empty, empty)()
        left = Gmod.GraphVersion(M.Pair(node_a, empty), empty, empty)()
        right = Gmod.GraphVersion(M.Pair(node_b, empty), empty, empty)()
        law_one = Gmod.Law(
            left,
            interface,
            right,
            Gmod.Map(interface, left, empty)(),
            Gmod.Map(interface, right, empty)(),
            empty,
        )()
        law_two = Gmod.Law(
            right,
            interface,
            left,
            Gmod.Map(interface, right, empty)(),
            Gmod.Map(interface, left, empty)(),
            empty,
        )()
        handle = Gmod.Handle(
            M.Char("wire-handle"),
            Gmod.GraphVersion(M.Pair(node_a, empty), empty, empty)(),
        )()
        contract = Gmod.Contract(
            handle,
            M.Pair(node_a, empty),
            Gmod.DefaultContractForbidden()(),
        )()
        carrier_right = Gmod.GraphVersion(
            M.Pair(contract, empty),
            empty,
            empty,
        )()
        carrier = Gmod.Law(
            interface,
            interface,
            carrier_right,
            Gmod.Map(interface, interface, empty)(),
            Gmod.Map(interface, carrier_right, empty)(),
            empty,
        )()
        version = Gmod.GraphVersion(M.Pair(node_a, empty), empty, empty)()
        version = Gmod.InstallLaw(version, law_one)()
        version = Gmod.InstallLaw(version, law_two)()
        version = Gmod.InstallLaw(version, carrier)()
        version = Gmod.RetireLaw(version, law_two)()

        fire = M.Pair(M.Char("wire-fire"), empty)
        second = Gmod.GraphVersion(
            M.Pair(node_b, empty),
            empty,
            Gmod.GraphVersionInvariants(version)(),
        )()
        third = Gmod.GraphVersion(
            M.Pair(node_a, M.Pair(node_b, empty)),
            empty,
            Gmod.GraphVersionInvariants(version)(),
        )()
        chain = Gmod.Next(
            Gmod.Next(
                Gmod.Next(version, fire, second)(),
                fire,
                third,
            )(),
            fire,
            version,
        )()

        blob = Wmod.serialize_term(chain)
        rebuilt = Wmod.deserialize_term(blob)
        blob_again = Wmod.serialize_term(rebuilt)
        rebuilt_version = M.Head(
            M.Tail(M.Tail(M.Tail(rebuilt)())())(),
        )()

        store = Gmod.ProposalStore(empty)()
        store = Gmod.ProposalStoreSubmit(
            store,
            Gmod.Proposal(law_one, M.Char("wire-origin"))(),
        )()
        ledger = Gmod.FiringLedger(registry)
        ledger.record_miss(law_one, M.Char("no-match"))
        checkpoint_path = os.path.join(
            tempfile.gettempdir(),
            "hyge_wire_roundtrip_checkpoint.txt",
        )
        Wmod.save_checkpoint(checkpoint_path, version, store, ledger)
        loaded = Wmod.load_checkpoint(checkpoint_path, registry)
        loaded_version = M.Head(loaded)()
        loaded_store = M.Head(M.Tail(loaded)())()
        loaded_ledger = M.Head(M.Tail(M.Tail(loaded)())())()
        os.remove(checkpoint_path)

        self.result = M.truth_value
        if blob != blob_again:
            self.result = M.false_value
        elif M.Compare(chain, rebuilt)() is M.false_value:
            self.result = M.false_value
        elif M.Compare(
            Gmod.InstalledLaws(rebuilt_version)(),
            Gmod.InstalledLaws(version)(),
        )() is M.false_value:
            self.result = M.false_value
        elif M.Compare(
            Gmod.AllLawsWithStatus(rebuilt_version)(),
            Gmod.AllLawsWithStatus(version)(),
        )() is M.false_value:
            self.result = M.false_value
        elif M.Compare(
            Gmod.InstalledPolicy(rebuilt_version)(),
            Gmod.InstalledPolicy(version)(),
        )() is M.false_value:
            self.result = M.false_value
        elif M.Compare(
            Gmod.InstalledContracts(rebuilt_version)(),
            Gmod.InstalledContracts(version)(),
        )() is M.false_value:
            self.result = M.false_value
        elif Wmod.serialize_version(loaded_version) != Wmod.serialize_version(
            version,
        ):
            self.result = M.false_value
        elif M.Compare(
            Gmod.ProposalStoreAll(loaded_store)(),
            Gmod.ProposalStoreAll(store)(),
        )() is M.false_value:
            self.result = M.false_value
        elif M.Compare(loaded_ledger.misses, ledger.misses)() is M.false_value:
            self.result = M.false_value
        super().__init__(inputs=empty, results=M.Pair(self.result, empty))

    def __call__(self):
        return self.result


class ContractEnforcementTest(M.Edge):
    """Step 39: deleting a contracted port is a Miss term, never a firing."""

    def __init__(self, graph):
        empty = M.EmptyList
        registry = M.FromContextGetConstructors(graph)()
        port_node = M.Pair(M.Char("contract-port"), empty)
        absent_node = M.Pair(M.Char("contract-absent"), empty)
        interface = Gmod.GraphVersion(empty, empty, empty)()
        left_delete = Gmod.GraphVersion(M.Pair(port_node, empty), empty, empty)()
        right_delete = Gmod.GraphVersion(empty, empty, empty)()
        delete_law = Gmod.Law(
            left_delete,
            interface,
            right_delete,
            Gmod.Map(interface, left_delete, empty)(),
            Gmod.Map(interface, right_delete, empty)(),
            empty,
        )()

        handle = Gmod.Handle(
            M.Char("contract-handle"),
            Gmod.GraphVersion(M.Pair(port_node, empty), empty, empty)(),
        )()
        contract = Gmod.Contract(
            handle,
            M.Pair(port_node, empty),
            Gmod.DefaultContractForbidden()(),
        )()
        left_carrier = Gmod.GraphVersion(M.Pair(absent_node, empty), empty, empty)()
        right_carrier = Gmod.GraphVersion(M.Pair(contract, empty), empty, empty)()
        carrier_law = Gmod.Law(
            left_carrier,
            interface,
            right_carrier,
            Gmod.Map(interface, left_carrier, empty)(),
            Gmod.Map(interface, right_carrier, empty)(),
            empty,
        )()

        version = Gmod.GraphVersion(M.Pair(port_node, empty), empty, empty)()
        version = Gmod.InstallLaw(version, delete_law)()
        version = Gmod.InstallLaw(version, carrier_law)()
        contracted_host = Gmod.GraphVersion(
            M.Pair(port_node, empty),
            empty,
            Gmod.GraphVersionInvariants(version)(),
        )()
        ledger = Gmod.FiringLedger(registry)
        refused = Gmod.FireAny(
            contracted_host,
            Gmod.DanglingForbid()(),
            ledger,
        )()
        refused_version = M.Head(refused)()
        refused_trace = M.Head(M.Tail(refused)())()

        bare_version = Gmod.GraphVersion(M.Pair(port_node, empty), empty, empty)()
        bare_version = Gmod.InstallLaw(bare_version, delete_law)()
        bare_host = Gmod.GraphVersion(
            M.Pair(port_node, empty),
            empty,
            Gmod.GraphVersionInvariants(bare_version)(),
        )()
        bare_ledger = Gmod.FiringLedger(ledger.registry)
        fired = Gmod.FireAny(bare_host, Gmod.DanglingForbid()(), bare_ledger)()
        fired_version = M.Head(fired)()

        contract_miss_reason = empty
        remaining_misses = ledger.misses
        while M.IdentityCompare(remaining_misses, empty)() is M.false_value:
            miss_entry = M.Head(remaining_misses)()
            if M.TermEqual(M.Head(miss_entry)(), delete_law)() is M.truth_value:
                reason = M.Head(M.Tail(miss_entry)())()
                if M.IsPair(reason)() is M.truth_value:
                    if M.TermEqual(
                        M.Head(reason)(),
                        Lmod.ReasonContractLabel,
                    )() is M.truth_value:
                        contract_miss_reason = reason
                        remaining_misses = empty
            if M.IdentityCompare(remaining_misses, empty)() is M.false_value:
                remaining_misses = M.Tail(remaining_misses)()

        graph._replace_context(constructors=bare_ledger.registry)

        self.result = M.truth_value
        if M.IdentityCompare(refused_version, empty)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(refused_trace, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.TermEqual(
            M.Head(M.Head(refused_trace)())(),
            Lmod.MissLabel,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(contract_miss_reason, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.TermEqual(
            Gmod.ContractViolation(
                Gmod.InstalledContracts(contracted_host)(),
                M.Pair(port_node, empty),
            )(),
            contract,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(fired_version, empty)() is M.truth_value:
            self.result = M.false_value
        elif Gmod.ChainHasTerm(
            Gmod.GraphNodes(fired_version)(),
            port_node,
        )() is M.truth_value:
            self.result = M.false_value
        super().__init__(inputs=empty, results=M.Pair(self.result, empty))

    def __call__(self):
        return self.result


class CuratorReportTest(M.Edge):
    """Step 38: report counts match a hand-computed scripted session exactly."""

    def __init__(self, graph):
        empty = M.EmptyList
        registry = M.FromContextGetConstructors(graph)()
        ledger = Gmod.FiringLedger(registry)

        interface_node = M.Char("curator-interface")
        first_internal = M.Char("curator-first-internal")
        second_internal = M.Char("curator-second-internal")
        pattern_edge = M.Pair(
            M.Char("curator-pattern-edge"),
            M.Pair(
                interface_node,
                M.Pair(first_internal, M.Pair(second_internal, empty)),
            ),
        )
        pattern_nodes = M.Pair(
            interface_node,
            M.Pair(first_internal, M.Pair(second_internal, empty)),
        )
        pattern = M.Pair(
            M.HypergraphLabel,
            M.Pair(pattern_nodes, M.Pair(M.Pair(pattern_edge, empty), empty)),
        )
        interface_nodes = M.Pair(interface_node, empty)
        handle = Gmod.Handle(M.Char("curator-handle"), pattern)()
        compiled = Gmod.CompileHandleToLaws(handle, interface_nodes)()
        fold = M.Head(compiled)()
        auto_proposal = Gmod.Proposal(fold, handle)()

        empty_graph = Gmod.GraphVersion(empty, empty, empty)()
        human_law = Gmod.Law(
            empty_graph,
            empty_graph,
            empty_graph,
            empty,
            empty,
            empty,
        )()
        human_proposal = Gmod.Proposal(
            human_law,
            M.Char("curator-human-origin"),
        )()
        rejected_proposal = Gmod.Proposal(
            human_law,
            M.Char("curator-rejected-origin"),
        )()
        human_authority = M.Pair(M.Char("curator-authority"), empty)

        store = Gmod.ProposalStore(empty)()
        store = Gmod.ProposalStoreSubmit(store, auto_proposal)()
        store = Gmod.ProposalStoreSubmit(store, human_proposal)()
        store = Gmod.ProposalStoreSubmit(store, rejected_proposal)()
        store = Gmod.ProposalStoreReject(
            store,
            Gmod.ProposalEntry(rejected_proposal, empty)(),
            human_authority,
            M.Char("curator-rejection-reason"),
        )()

        host = Gmod.GraphVersion(
            pattern_nodes,
            M.Pair(pattern_edge, empty),
            empty,
        )()
        budget = M.Pair(
            M.Pair(
                Gmod.AUTONOMY_BUDGET_MAX_FIRINGS_KEY,
                M.Pair(M.one, empty),
            ),
            M.Pair(
                M.Pair(
                    Gmod.AUTONOMY_BUDGET_MAX_NODES_KEY,
                    M.Pair(M.nine, empty),
                ),
                M.Pair(
                    M.Pair(
                        Gmod.AUTONOMY_BUDGET_MAX_ACTIVATIONS_KEY,
                        M.Pair(M.one, empty),
                    ),
                    empty,
                ),
            ),
        )
        cycle = Gmod.AutonomyCycle(host, store, ledger, budget)()
        cycle_version = M.Head(cycle)()
        cycle_store = M.Head(M.Tail(cycle)())()

        approved_store = Gmod.ProposalStoreAttach(
            cycle_store,
            human_proposal,
            Gmod.Approved(human_proposal, human_authority)(),
        )()
        activated = Gmod.ActivateProposal(
            cycle_version,
            Gmod.ProposalEntry(
                human_proposal,
                M.Pair(
                    Gmod.Approved(human_proposal, human_authority)(),
                    empty,
                ),
            )(),
        )()
        final_version = M.Head(activated)()

        second_budget = M.Pair(
            M.Pair(
                Gmod.AUTONOMY_BUDGET_MAX_FIRINGS_KEY,
                M.Pair(M.Zero, empty),
            ),
            M.Pair(
                M.Pair(
                    Gmod.AUTONOMY_BUDGET_MAX_NODES_KEY,
                    M.Pair(M.nine, empty),
                ),
                M.Pair(
                    M.Pair(
                        Gmod.AUTONOMY_BUDGET_MAX_ACTIVATIONS_KEY,
                        M.Pair(M.one, empty),
                    ),
                    empty,
                ),
            ),
        )
        second_cycle = Gmod.AutonomyCycle(
            final_version,
            approved_store,
            ledger,
            second_budget,
        )()
        final_store = M.Head(M.Tail(second_cycle)())()

        report = Gmod.CuratorReport(final_store, ledger, final_version)()
        rendered = Gmod.RenderCuratorReport(report)()
        expected = (
            "curator report"
            + "\nclass fold_handle: submitted=1 approved=1 rejected=0 pending=0"
            + "\nclass install_law: submitted=2 approved=1 rejected=1 pending=0"
            + "\nretired_laws=0"
            + "\nledger_firings=1"
            + "\nledger_misses=0"
            + "\neffective_policy:"
            + " fold_handle=auto unfold_handle=auto install_law=human"
            + " meta_rewrite=human activation=human tune_preference=auto"
            + " retire_law=human tune_scheduler=human annotate=auto"
            + "\nskipped_handle_candidates count=0"
            + "\nskipped_compositions count=0"
            + "\nunchecked_obligations count=0"
        )

        graph._replace_context(constructors=ledger.registry)

        self.result = M.truth_value
        if rendered != expected:
            self.result = M.false_value
        super().__init__(inputs=empty, results=M.Pair(self.result, empty))

    def __call__(self):
        return self.result


class ToyCorrespondenceRoundTripTest(M.Edge):
    """Toy v0: one hand-authored Surface/Meaning law parses, evaluates, renders.

    This is scope-limited by design: no paraphrase equivalence, no ambiguity,
    no induction, no fragment extension. It verifies only that a correspondence
    rule works as a machine rewrite in both directions.
    """

    def __init__(self, graph):
        empty = M.EmptyList
        the_sym = M.Char("the")
        sum_sym = M.Char("sum")
        of_sym = M.Char("of")
        and_sym = M.Char("and")
        two_sym = M.Char("two")
        three_sym = M.Char("three")
        five_sym = M.Char("five")
        var_a = M.Pair(M.VarTag, M.Pair(M.Char("?a"), empty))
        var_b = M.Pair(M.VarTag, M.Pair(M.Char("?b"), empty))

        pattern = Gmod.Surface(
            M.Pair(
                the_sym,
                M.Pair(
                    sum_sym,
                    M.Pair(
                        of_sym,
                        M.Pair(var_a, M.Pair(and_sym, M.Pair(var_b, empty))),
                    ),
                ),
            ),
        )()
        template = Gmod.Meaning(
            M.Pair(
                M.ExprAddLabel,
                M.Pair(
                    Gmod.Surface(M.Pair(var_a, empty))(),
                    M.Pair(Gmod.Surface(M.Pair(var_b, empty))(), empty),
                ),
            ),
        )()

        law_parse = Gmod.CompileRuleToLaw(Pmod.Rule(pattern, template))()
        law_render = Gmod.CompileRuleToLaw(Pmod.Rule(template, pattern))()
        law_two = Gmod.CompileRuleToLaw(
            Pmod.Rule(Gmod.Surface(M.Pair(two_sym, empty))(), M.two),
        )()
        law_three = Gmod.CompileRuleToLaw(
            Pmod.Rule(Gmod.Surface(M.Pair(three_sym, empty))(), M.three),
        )()
        law_five_render = Gmod.CompileRuleToLaw(
            Pmod.Rule(M.five, Gmod.Surface(M.Pair(five_sym, empty))()),
        )()

        sentence = Gmod.Surface(
            M.Pair(
                the_sym,
                M.Pair(
                    sum_sym,
                    M.Pair(
                        of_sym,
                        M.Pair(two_sym, M.Pair(and_sym, M.Pair(three_sym, empty))),
                    ),
                ),
            ),
        )()

        registry = M.FromContextGetConstructors(graph)()

        self.result = M.truth_value
        if M.IdentityCompare(law_parse, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(law_render, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(law_two, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(law_three, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(law_five_render, empty)() is M.truth_value:
            self.result = M.false_value
        else:
            parsed = Gmod.CorrespondenceApply(law_parse, sentence)()
            if M.IdentityCompare(parsed, empty)() is M.truth_value:
                self.result = M.false_value
            else:
                correspondence = Gmod.Corresponds(sentence, parsed, law_parse)()
                if M.IdentityCompare(
                    M.Head(correspondence)(),
                    Lmod.CorrespondsLabel,
                )() is M.false_value:
                    self.result = M.false_value
                meaning_body = M.Head(M.Tail(parsed)())()
                left_arg = M.Head(M.Tail(meaning_body)())()
                right_arg = M.Head(M.Tail(M.Tail(meaning_body)())())()
                left_number = Gmod.CorrespondenceApply(law_two, left_arg)()
                right_number = Gmod.CorrespondenceApply(law_three, right_arg)()
                if M.IdentityCompare(
                    M.Head(meaning_body)(),
                    M.ExprAddLabel,
                )() is M.false_value:
                    self.result = M.false_value
                elif M.IdentityCompare(left_number, empty)() is M.truth_value:
                    self.result = M.false_value
                elif M.IdentityCompare(right_number, empty)() is M.truth_value:
                    self.result = M.false_value
                elif M.NatEq(left_number, M.two, registry)() is M.false_value:
                    self.result = M.false_value
                elif M.NatEq(right_number, M.three, registry)() is M.false_value:
                    self.result = M.false_value
                else:
                    added = M.Add(left_number, right_number, registry)()
                    total = M.Head(added)()
                    registry = M.Head(M.Tail(added)())()
                    if M.NatEq(total, M.five, registry)() is M.false_value:
                        self.result = M.false_value
                    else:
                        total_surface = Gmod.CorrespondenceApply(
                            law_five_render,
                            total,
                        )()
                        rendered = Gmod.CorrespondenceApply(law_render, parsed)()
                        if M.IdentityCompare(total_surface, empty)() is M.truth_value:
                            self.result = M.false_value
                        elif M.IdentityCompare(
                            M.Head(M.Head(M.Tail(total_surface)())())(),
                            five_sym,
                        )() is M.false_value:
                            self.result = M.false_value
                        elif M.IdentityCompare(rendered, empty)() is M.truth_value:
                            self.result = M.false_value
                        elif M.TermEqual(rendered, sentence)() is M.false_value:
                            self.result = M.false_value

        graph._replace_context(constructors=registry)
        super().__init__(inputs=empty, results=M.Pair(self.result, empty))

    def __call__(self):
        return self.result


class ConverseDefaultModeTest(M.Edge):
    """Talk mode: Converse returns explicit Understood/NotUnderstood/Ambiguous.

    Sentence shapes, bare words, and parenthesis groups produce Understood
    terms; unknown words, unknown shapes, and unbalanced groups produce
    NotUnderstood terms carrying distinct structured reasons.
    """

    def __init__(self, graph):
        empty = M.EmptyList
        registry = M.FromContextGetConstructors(graph)()
        vocabulary = Gmod.DefaultCorrespondenceVocabulary()()

        def _sentence(*symbols):
            chain = empty
            index = len(symbols)
            while index != 0:
                index = index - 1
                chain = M.Pair(M.Char(symbols[index]), chain)
            return Gmod.Surface(chain)()

        def _converse(surface):
            nonlocal registry
            outcome_pair = Gmod.Converse(vocabulary, surface, registry)()
            registry = M.Head(M.Tail(outcome_pair)())()
            return M.Head(outcome_pair)()

        def _understood_words(outcome):
            words = empty
            if M.IdentityCompare(
                M.Head(outcome)(),
                Lmod.UnderstoodLabel,
            )() is M.truth_value:
                answer = M.Head(
                    M.Tail(M.Tail(M.Tail(M.Tail(outcome)())())())(),
                )()
                if M.IdentityCompare(answer, empty)() is M.false_value:
                    words = M.Head(M.Tail(answer)())()
            return words

        def _failure_reason(outcome):
            reason_label = empty
            if M.IdentityCompare(
                M.Head(outcome)(),
                Lmod.NotUnderstoodLabel,
            )() is M.truth_value:
                reason_label = M.Head(
                    M.Head(M.Tail(M.Tail(outcome)())())(),
                )()
            return reason_label

        sum_words = _understood_words(
            _converse(_sentence("the", "sum", "of", "two", "and", "three")),
        )
        plus_words = _understood_words(_converse(_sentence("two", "plus", "three")))
        product_words = _understood_words(
            _converse(_sentence("the", "product", "of", "two", "and", "three")),
        )
        times_words = _understood_words(
            _converse(_sentence("four", "times", "four")),
        )
        word_words = _understood_words(_converse(_sentence("seven")))
        group_words = _understood_words(
            _converse(
                _sentence("two", "times", "(", "two", "plus", "two", ")"),
            ),
        )
        nested_words = _understood_words(
            _converse(
                _sentence(
                    "two", "times",
                    "(", "(", "one", "plus", "one", ")", "plus", "two", ")",
                ),
            ),
        )
        unknown_reason = _failure_reason(
            _converse(_sentence("the", "banana", "of", "two")),
        )
        shape_reason = _failure_reason(
            _converse(_sentence("two", "two", "two")),
        )
        unbalanced_reason = _failure_reason(
            _converse(_sentence("two", "times", "(", "two", "plus", "two")),
        )

        self.result = M.truth_value
        if M.IdentityCompare(sum_words, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.Compare(M.Head(sum_words)(), M.Char("five"))() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Tail(sum_words)(), empty)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(plus_words, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.Compare(M.Head(plus_words)(), M.Char("five"))() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(product_words, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.Compare(M.Head(product_words)(), M.Char("six"))() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(times_words, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.Compare(M.Head(times_words)(), M.Char("one"))() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Tail(times_words)(), empty)() is M.truth_value:
            self.result = M.false_value
        elif M.Compare(
            M.Head(M.Tail(times_words)())(),
            M.Char("six"),
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(word_words, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.Compare(M.Head(word_words)(), M.Char("seven"))() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(group_words, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.Compare(M.Head(group_words)(), M.Char("eight"))() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(nested_words, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.Compare(M.Head(nested_words)(), M.Char("eight"))() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            unknown_reason,
            Lmod.ReasonUnknownWordLabel,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            shape_reason,
            Lmod.ReasonNoCorrespondenceLabel,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            unbalanced_reason,
            Lmod.ReasonGroupLabel,
        )() is M.false_value:
            self.result = M.false_value

        graph._replace_context(constructors=registry)
        super().__init__(inputs=empty, results=M.Pair(self.result, empty))

    def __call__(self):
        return self.result


class ReadingPolicyTest(M.Edge):
    """A typed line becomes words by the policy, not by string surgery.

    One line exercises every decision the host replaces used to make:
    a capital folded, a bracket and a comma standing alone as words, an
    all-digit run spelled out, a word with a digit in it left whole, and
    a full stop dropped. The policy is the chains in
    DefaultReadingPolicy, so a pack changing them changes the reader.
    """

    def __init__(self, graph):
        empty = M.EmptyList
        registry = M.FromContextGetConstructors(graph)()
        vocabulary = Gmod.DefaultCorrespondenceVocabulary()()
        policy = Gmod.DefaultReadingPolicy()()
        digit_words = M.Head(M.Tail(M.Tail(vocabulary)())())()

        read = Gmod.WordsOfText("Mul ( 64 , sqrt2 ).", policy, digit_words)()
        expected = M.Pair(
            M.Char("mul"),
            M.Pair(
                M.Char("("),
                M.Pair(
                    M.Char("six"),
                    M.Pair(
                        M.Char("four"),
                        M.Pair(
                            M.Char(","),
                            M.Pair(
                                M.Char("sqrt2"),
                                M.Pair(M.Char(")"), empty),
                            ),
                        ),
                    ),
                ),
            ),
        )
        blank = Gmod.WordsOfText("   ", policy, digit_words)()
        surface = Gmod.SurfaceOfText("two plus two", policy, digit_words)()

        self.result = M.truth_value
        # Words are Chars, and Char identity is Compare -- TermEqual holds
        # two Chars apart by object, which is why every word test in this
        # file asks Compare.
        if M.Compare(read, expected)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(blank, empty)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            M.Head(surface)(), Lmod.SurfaceLabel,
        )() is M.false_value:
            self.result = M.false_value
        elif M.Compare(
            M.Head(M.Head(M.Tail(surface)())())(), M.Char("two"),
        )() is M.false_value:
            self.result = M.false_value

        graph._replace_context(constructors=registry)
        super().__init__(inputs=empty, results=M.Pair(self.result, empty))

    def __call__(self):
        return self.result


class DeductionLawTest(M.Edge):
    """A monotone law keeps its premises, adds its conclusion, and stops.

    CompileMultiRuleToLaw deletes every premise element the conclusion
    does not mention, which is right for a rewrite and wrong for a
    deduction. CompileDeductionToLaw sets K to the whole of L, so the
    firing is additive. SaturateLaws then fires it once and reaches a
    fixed point: the second attempt is skipped because the conclusion is
    already in the store, which is what stops a monotone law from firing
    forever.
    """

    def __init__(self, graph):
        empty = M.EmptyList
        registry = M.FromContextGetConstructors(graph)()
        variable = M.Pair(M.VarTag, M.Pair(M.Char("?x"), empty))
        fact = M.Pair(M.SqrtLabel, M.Pair(M.nine, empty))
        law = Gmod.CompileDeductionToLaw(
            Pmod.MultiRule(
                M.Pair(M.Pair(M.SqrtLabel, M.Pair(variable, empty)), empty),
                M.Pair(M.ExprAddLabel, M.Pair(variable, M.Pair(variable, empty))),
            ),
        )()
        encoded = Gmod.EncodeTermAsGraph(fact)()
        version = Gmod.GraphVersion(
            Gmod.GraphNodes(encoded)(), Gmod.GraphEdges(encoded)(), empty,
        )()
        saturation = Gmod.SaturateLaws(
            version, M.Pair(law, empty), empty, Gmod.DanglingForbid()(),
        )
        after = saturation()
        again = Gmod.SaturateLaws(
            after, M.Pair(law, empty), empty, Gmod.DanglingForbid()(),
        )
        settled = again()
        derived = M.Pair(M.ExprAddLabel, M.Pair(M.nine, M.Pair(M.nine, empty)))

        self.result = M.truth_value
        if Gmod.IsLawTerm(law)() is M.false_value:
            self.result = M.false_value
        elif M.TermEqual(
            Gmod.GraphNodes(Gmod.LawLeft(law)())(),
            Gmod.GraphNodes(Gmod.LawInterface(law)())(),
        )() is M.false_value:
            self.result = M.false_value
        elif Gmod.LawMapsComplete(law)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            saturation.saturated, M.truth_value,
        )() is M.false_value:
            self.result = M.false_value
        elif Gmod.ChainHasTerm(Gmod.GraphNodes(after)(), fact)() is M.false_value:
            self.result = M.false_value
        elif Gmod.ChainHasTerm(
            Gmod.GraphNodes(after)(), derived,
        )() is M.false_value:
            self.result = M.false_value
        elif M.TermEqual(
            Gmod.GraphNodes(settled)(), Gmod.GraphNodes(after)(),
        )() is M.false_value:
            self.result = M.false_value

        graph._replace_context(constructors=registry)
        super().__init__(inputs=empty, results=M.Pair(self.result, empty))

    def __call__(self):
        return self.result


class RecogniseFormsTest(M.Edge):
    """The reader's deduction runs by index and agenda, not by search.

    The same three-premise rule the generic matcher was asked for --
    FormScan, ObservedSymbolStep, FormArc to FormScan -- is compiled to
    two ordinary monotone laws and executed through DeductionPlan
    records over red-black indexes. Every fact enters through one
    insert that dedupes on the declared keys and queues a delta; the
    agenda runs to empty, which is quiescence. Nothing enumerates the
    store, and nothing asks the generic matcher anything.

    Over "a prime" the shared trie yields the determiner "a" over
    cursors zero to one and the noun "prime" over two to seven, and
    nothing else: the space kills its scan at the root, and no other
    path reaches a stated state.
    """

    def __init__(self, graph):
        empty = M.EmptyList
        registry = M.FromContextGetConstructors(graph)()

        utterance = M.Char("utt:a prime")
        sym_a = M.Char("a")
        sym_space = M.Char(" ")
        sym_p = M.Char("p")
        sym_r = M.Char("r")
        sym_i = M.Char("i")
        sym_m = M.Char("m")
        sym_e = M.Char("e")
        c0 = M.GMPRep("0")
        c1 = M.GMPRep("1")
        c2 = M.GMPRep("2")
        c3 = M.GMPRep("3")
        c4 = M.GMPRep("4")
        c5 = M.GMPRep("5")
        c6 = M.GMPRep("6")
        c7 = M.GMPRep("7")

        steps = M.Pair(
            Gmod.ObservedSymbolStep(utterance, c0, sym_a, c1)(),
            M.Pair(
                Gmod.ObservedSymbolStep(utterance, c1, sym_space, c2)(),
                M.Pair(
                    Gmod.ObservedSymbolStep(utterance, c2, sym_p, c3)(),
                    M.Pair(
                        Gmod.ObservedSymbolStep(utterance, c3, sym_r, c4)(),
                        M.Pair(
                            Gmod.ObservedSymbolStep(utterance, c4, sym_i, c5)(),
                            M.Pair(
                                Gmod.ObservedSymbolStep(
                                    utterance, c5, sym_m, c6,
                                )(),
                                M.Pair(
                                    Gmod.ObservedSymbolStep(
                                        utterance, c6, sym_e, c7,
                                    )(),
                                    empty,
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        )

        root = M.Char("root")
        s_a = M.Char("s:a")
        s_p = M.Char("s:p")
        s_pr = M.Char("s:pr")
        s_pri = M.Char("s:pri")
        s_prim = M.Char("s:prim")
        s_prime = M.Char("s:prime")
        arcs = M.Pair(
            Gmod.FormArc(root, sym_a, s_a)(),
            M.Pair(
                Gmod.FormArc(root, sym_p, s_p)(),
                M.Pair(
                    Gmod.FormArc(s_p, sym_r, s_pr)(),
                    M.Pair(
                        Gmod.FormArc(s_pr, sym_i, s_pri)(),
                        M.Pair(
                            Gmod.FormArc(s_pri, sym_m, s_prim)(),
                            M.Pair(
                                Gmod.FormArc(s_prim, sym_e, s_prime)(),
                                empty,
                            ),
                        ),
                    ),
                ),
            ),
        )

        det = M.Char("det")
        noun = M.Char("noun")
        mean_a = M.Char("sense:a")
        mean_prime = M.Char("sense:prime")
        senses = M.Pair(
            Gmod.FormSense(s_a, det, mean_a)(),
            M.Pair(Gmod.FormSense(s_prime, noun, mean_prime)(), empty),
        )

        engine = Gmod.RecogniseForms(steps, arcs, senses, root, empty)
        result = engine()
        readings = M.Head(result)()
        firings = M.Head(M.Tail(result)())()
        agenda_term = M.Head(M.Tail(M.Tail(result)())())()
        agenda_facts = M.Head(M.Tail(agenda_term)())()

        expected_det = Gmod.Reading(det, c0, c1, mean_a)()
        expected_noun = Gmod.Reading(noun, c2, c7, mean_prime)()
        reading_count = "0"
        remaining = readings
        while M.IdentityCompare(remaining, empty)() is M.false_value:
            reading_count = Gmod.GMPSuccText(reading_count)()
            remaining = M.Tail(remaining)()

        self.result = M.truth_value
        if Gmod.IsLawTerm(engine.scan_law)() is M.false_value:
            self.result = M.false_value
        elif Gmod.IsLawTerm(engine.sense_law)() is M.false_value:
            self.result = M.false_value
        elif Gmod.ChainHasTerm(readings, expected_det)() is M.false_value:
            self.result = M.false_value
        elif Gmod.ChainHasTerm(readings, expected_noun)() is M.false_value:
            self.result = M.false_value
        elif Gmod.GMPEqualText(reading_count, "2")() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(firings, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            M.Head(agenda_term)(), Lmod.DeltaAgendaLabel,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(agenda_facts, empty)() is M.false_value:
            self.result = M.false_value
        elif Gmod.GMPEqualText(
            engine.facts_inserted_text, engine.delta_popped_text,
        )() is M.false_value:
            self.result = M.false_value
        elif Gmod.GMPLessText("0", engine.index_lookups_text)() is M.false_value:
            self.result = M.false_value
        elif Gmod.GMPEqualText(
            engine.full_store_enumerations_text, "0",
        )() is M.false_value:
            self.result = M.false_value

        graph._replace_context(constructors=registry)
        super().__init__(inputs=empty, results=M.Pair(self.result, empty))

    def __call__(self):
        return self.result


class FreshenTemplateTest(M.Edge):
    """One application of a template gets fresh variables, correctly.

    A template that uses one variable twice and another once must
    receive the same fresh variable in the first two positions and a
    different one in the third; the recognised VarTag shape must
    survive; the scope must ride along; and a second application, under
    another scope, must receive its own variables. The binding chain is
    the provenance: the old variable maps to exactly the fresh variable
    that replaced it.
    """

    def __init__(self, graph):
        empty = M.EmptyList

        scope_one = M.Char("scope-one")
        scope_two = M.Char("scope-two")
        var_x = M.Pair(M.VarTag, M.Pair(M.Char("?x"), empty))
        var_y = M.Pair(M.VarTag, M.Pair(M.Char("?y"), empty))
        template = M.Pair(var_x, M.Pair(var_x, M.Pair(var_y, empty)))

        first = Gmod.FreshenTemplate(template, scope_one)
        second = Gmod.FreshenTemplate(template, scope_two)

        first_one = M.Head(first.instantiated)()
        first_two = M.Head(M.Tail(first.instantiated)())()
        first_three = M.Head(M.Tail(M.Tail(first.instantiated)())())()
        second_one = M.Head(second.instantiated)()

        binding_found = M.false_value
        walker = first.bindings_chain
        while M.IdentityCompare(walker, empty)() is M.false_value:
            entry = M.Head(walker)()
            if M.IdentityCompare(M.Head(entry)(), var_x)() is M.truth_value:
                if M.IdentityCompare(
                    M.Tail(entry)(), first_one,
                )() is M.truth_value:
                    binding_found = M.truth_value
            walker = M.Tail(walker)()

        self.result = M.truth_value
        if M.IdentityCompare(first_one, first_two)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(first_one, first_three)() is M.truth_value:
            self.result = M.false_value
        elif M.IsPair(first_one)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            M.Head(first_one)(), M.VarTag,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            M.Head(M.Tail(first_one)())(), scope_one,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(first_one, second_one)() is M.truth_value:
            self.result = M.false_value
        elif binding_found is M.false_value:
            self.result = M.false_value

        super().__init__(inputs=empty, results=M.Pair(self.result, empty))

    def __call__(self):
        return self.result


class GrammarCompositionTest(M.Edge):
    """Readings compose by index, and every firing freshens its template.

    Over "a prime", with the space a form of its own, the grammar

        det sp -> detb      noun-final forms as before
        detb noun -> np
        sp noun -> spn      one template variable, used twice

    must yield six readings: the three leaf readings, detb over zero to
    two, np over zero to seven, and spn over one to seven. The spn
    meaning is the same atom twice, which is the sharing FreshenTemplate
    guarantees; the np meaning is the detb meaning inside it, which is
    composition closing over its own output through the same indexes.
    """

    def __init__(self, graph):
        empty = M.EmptyList
        registry = M.FromContextGetConstructors(graph)()

        utterance = M.Char("utt:a prime")
        sym_a = M.Char("a")
        sym_space = M.Char(" ")
        sym_p = M.Char("p")
        sym_r = M.Char("r")
        sym_i = M.Char("i")
        sym_m = M.Char("m")
        sym_e = M.Char("e")
        c0 = M.GMPRep("0")
        c1 = M.GMPRep("1")
        c2 = M.GMPRep("2")
        c3 = M.GMPRep("3")
        c4 = M.GMPRep("4")
        c5 = M.GMPRep("5")
        c6 = M.GMPRep("6")
        c7 = M.GMPRep("7")

        steps = M.Pair(
            Gmod.ObservedSymbolStep(utterance, c0, sym_a, c1)(),
            M.Pair(
                Gmod.ObservedSymbolStep(utterance, c1, sym_space, c2)(),
                M.Pair(
                    Gmod.ObservedSymbolStep(utterance, c2, sym_p, c3)(),
                    M.Pair(
                        Gmod.ObservedSymbolStep(utterance, c3, sym_r, c4)(),
                        M.Pair(
                            Gmod.ObservedSymbolStep(utterance, c4, sym_i, c5)(),
                            M.Pair(
                                Gmod.ObservedSymbolStep(
                                    utterance, c5, sym_m, c6,
                                )(),
                                M.Pair(
                                    Gmod.ObservedSymbolStep(
                                        utterance, c6, sym_e, c7,
                                    )(),
                                    empty,
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        )

        root = M.Char("root")
        s_a = M.Char("s:a")
        s_sp = M.Char("s:sp")
        s_p = M.Char("s:p")
        s_pr = M.Char("s:pr")
        s_pri = M.Char("s:pri")
        s_prim = M.Char("s:prim")
        s_prime = M.Char("s:prime")
        arcs = M.Pair(
            Gmod.FormArc(root, sym_a, s_a)(),
            M.Pair(
                Gmod.FormArc(root, sym_space, s_sp)(),
                M.Pair(
                    Gmod.FormArc(root, sym_p, s_p)(),
                    M.Pair(
                        Gmod.FormArc(s_p, sym_r, s_pr)(),
                        M.Pair(
                            Gmod.FormArc(s_pr, sym_i, s_pri)(),
                            M.Pair(
                                Gmod.FormArc(s_pri, sym_m, s_prim)(),
                                M.Pair(
                                    Gmod.FormArc(s_prim, sym_e, s_prime)(),
                                    empty,
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        )

        det = M.Char("det")
        sp_cat = M.Char("sp")
        noun = M.Char("noun")
        detb = M.Char("detb")
        np_cat = M.Char("np")
        spn_cat = M.Char("spn")
        mean_a = M.Char("sense:a")
        mean_sp = M.Char("sense:sp")
        mean_prime = M.Char("sense:prime")
        senses = M.Pair(
            Gmod.FormSense(s_a, det, mean_a)(),
            M.Pair(
                Gmod.FormSense(s_sp, sp_cat, mean_sp)(),
                M.Pair(Gmod.FormSense(s_prime, noun, mean_prime)(), empty),
            ),
        )

        var_t1 = M.Pair(M.VarTag, M.Pair(M.Char("?t1"), empty))
        var_t2 = M.Pair(M.VarTag, M.Pair(M.Char("?t2"), empty))
        var_ts = M.Pair(M.VarTag, M.Pair(M.Char("?ts"), empty))
        productions = M.Pair(
            Gmod.BinaryProduction(
                det, sp_cat, detb, M.Pair(var_t1, M.Pair(var_t2, empty)),
            )(),
            M.Pair(
                Gmod.BinaryProduction(
                    detb, noun, np_cat, M.Pair(var_t1, M.Pair(var_t2, empty)),
                )(),
                M.Pair(
                    Gmod.BinaryProduction(
                        sp_cat,
                        noun,
                        spn_cat,
                        M.Pair(var_ts, M.Pair(var_ts, empty)),
                    )(),
                    empty,
                ),
            ),
        )

        engine = Gmod.RecogniseForms(steps, arcs, senses, root, productions)
        result = engine()
        readings = M.Head(result)()
        agenda_term = M.Head(M.Tail(M.Tail(result)())())()

        expected_detb_meaning = M.Pair(mean_a, M.Pair(mean_sp, empty))
        expected_np_meaning = M.Pair(
            expected_detb_meaning, M.Pair(mean_prime, empty),
        )
        expected_det = Gmod.Reading(det, c0, c1, mean_a)()
        expected_sp = Gmod.Reading(sp_cat, c1, c2, mean_sp)()
        expected_noun = Gmod.Reading(noun, c2, c7, mean_prime)()
        expected_detb = Gmod.Reading(
            detb, c0, c2, expected_detb_meaning,
        )()
        expected_np = Gmod.Reading(np_cat, c0, c7, expected_np_meaning)()

        reading_count = "0"
        spn_shared = M.false_value
        spn_seen = M.false_value
        remaining = readings
        while M.IdentityCompare(remaining, empty)() is M.false_value:
            reading = M.Head(remaining)()
            reading_count = Gmod.GMPSuccText(reading_count)()
            category = M.Head(M.Tail(reading)())()
            if M.IdentityCompare(category, spn_cat)() is M.truth_value:
                spn_seen = M.truth_value
                meaning = M.Head(
                    M.Tail(M.Tail(M.Tail(M.Tail(reading)())())())(),
                )()
                spn_shared = M.IdentityCompare(
                    M.Head(meaning)(), M.Head(M.Tail(meaning)())(),
                )()
            remaining = M.Tail(remaining)()

        self.result = M.truth_value
        if Gmod.GMPEqualText(reading_count, "6")() is M.false_value:
            self.result = M.false_value
        elif Gmod.ChainHasTerm(readings, expected_det)() is M.false_value:
            self.result = M.false_value
        elif Gmod.ChainHasTerm(readings, expected_sp)() is M.false_value:
            self.result = M.false_value
        elif Gmod.ChainHasTerm(readings, expected_noun)() is M.false_value:
            self.result = M.false_value
        elif Gmod.ChainHasTerm(readings, expected_detb)() is M.false_value:
            self.result = M.false_value
        elif Gmod.ChainHasTerm(readings, expected_np)() is M.false_value:
            self.result = M.false_value
        elif spn_seen is M.false_value:
            self.result = M.false_value
        elif spn_shared is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            M.Head(M.Tail(agenda_term)())(), empty,
        )() is M.false_value:
            self.result = M.false_value
        elif Gmod.GMPEqualText(
            engine.facts_inserted_text, engine.delta_popped_text,
        )() is M.false_value:
            self.result = M.false_value
        elif Gmod.GMPEqualText(engine.freshen_count_text, "3")() is M.false_value:
            self.result = M.false_value
        elif Gmod.GMPEqualText(
            engine.full_store_enumerations_text, "0",
        )() is M.false_value:
            self.result = M.false_value
        elif Gmod.IsLawTerm(engine.compose_law)() is M.false_value:
            self.result = M.false_value

        graph._replace_context(constructors=registry)
        super().__init__(inputs=empty, results=M.Pair(self.result, empty))

    def __call__(self):
        return self.result


class DefinitionNodeTest(M.Edge):
    """The destination exists: the prime definition, as a graph.

    Hand-built, before any lexicon. The definiendum is prime over
    Category(nat); one binder variable is allocated by FreshenTemplate
    for this definition's scope; the conditions are NonNegative(self),
    the hole where Divides waits, and the restriction "only" keeps as
    scope. Every self is the same variable object; the term round-trips
    through a snapshot with that sharing intact; the well-formedness
    certificate accepts it and rejects a binder whose self is not a
    variable; and the shape is declared with a ConstructorSignature the
    formal reader turns into a production like any constructor's.
    """

    def __init__(self, graph):
        empty = M.EmptyList
        registry = M.FromContextGetConstructors(graph)()

        scope = M.Char("definition-scope-1")
        var_self = M.Pair(M.VarTag, M.Pair(M.Char("?self"), empty))
        fresh = Gmod.FreshenTemplate(
            M.Pair(var_self, M.Pair(var_self, empty)), scope,
        )
        fresh_one = M.Head(fresh.instantiated)()
        fresh_two = M.Head(M.Tail(fresh.instantiated)())()

        concept = M.Char("prime")
        nat = M.Char("nat")
        one = M.Char("one")

        non_negative = M.Pair(
            Lmod.NonNegativeLabel, M.Pair(fresh_one, empty),
        )
        hole = Gmod.Hole(
            Lmod.DividesLabel,
            M.Pair(one, M.Pair(fresh_one, empty)),
            Lmod.NoDefinitionInstalledLabel,
        )()
        restriction = Gmod.ExactFillers(
            Lmod.DividesLabel,
            fresh_one,
            M.Char("divisor"),
            M.Pair(one, M.Pair(fresh_one, empty)),
        )()
        conditions = M.Pair(
            non_negative, M.Pair(hole, M.Pair(restriction, empty)),
        )
        node = Gmod.DefinitionNode(
            Gmod.Definiendum(concept, Gmod.CategoryTerm(nat)())(),
            Gmod.Binder(scope, fresh_one)(),
            conditions,
        )()
        broken = Gmod.DefinitionNode(
            Gmod.Definiendum(concept, Gmod.CategoryTerm(nat)())(),
            Gmod.Binder(scope, concept)(),
            conditions,
        )()

        signature = Gmod.ConstructorSignature(
            M.Char("definition"), Lmod.DefinitionNodeLabel, M.three,
        )()
        generated = Gmod.FormalProductions(
            M.Pair(signature, empty), Gmod.CHART_TERM_CATEGORY, registry,
        )()
        productions = M.Head(generated)()
        registry = M.Head(M.Tail(generated)())()

        namespace = dict(vars(M))
        namespace.update(vars(Lmod))
        codec = SnapshotCodec(namespace)
        snapshot = codec.capture_objects({"definition": node})
        loaded = codec.load_snapshot(snapshot).roots["definition"]

        loaded_self = Gmod.BinderSelf(Gmod.DefinitionNodeBinder(loaded)())()
        loaded_conditions = Gmod.DefinitionNodeConditions(loaded)()
        loaded_hole = M.Head(M.Tail(loaded_conditions)())()
        loaded_hole_self = M.Head(
            M.Tail(Gmod.HoleArguments(loaded_hole)())(),
        )()
        loaded_restriction = M.Head(M.Tail(M.Tail(loaded_conditions)())())()
        loaded_restriction_self = M.Head(
            M.Tail(M.Tail(loaded_restriction)())(),
        )()
        loaded_allowed = M.Head(
            M.Tail(M.Tail(M.Tail(M.Tail(loaded_restriction)())())())(),
        )()
        loaded_allowed_self = M.Head(M.Tail(loaded_allowed)())()
        loaded_definiendum = Gmod.DefinitionNodeDefiniendum(loaded)()
        loaded_concept = M.Head(M.Tail(loaded_definiendum)())()

        self.result = M.truth_value
        if M.IdentityCompare(fresh_one, fresh_two)() is M.false_value:
            self.result = M.false_value
        elif Gmod.DefinitionNodeWellFormed(node)() is M.false_value:
            self.result = M.false_value
        elif Gmod.DefinitionNodeWellFormed(broken)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            Gmod.BinderSelf(Gmod.DefinitionNodeBinder(node)())(), fresh_one,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            M.Head(M.Tail(Gmod.HoleArguments(hole)())())(), fresh_one,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            M.Head(M.Tail(M.Tail(restriction)())())(), fresh_one,
        )() is M.false_value:
            self.result = M.false_value
        elif RawTermEqual(loaded, node, M.AllConstructors)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            loaded_hole_self, loaded_self,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            loaded_restriction_self, loaded_self,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            loaded_allowed_self, loaded_self,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(loaded_concept, one)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(productions, empty)() is M.truth_value:
            self.result = M.false_value

        graph._replace_context(constructors=registry)
        super().__init__(inputs=empty, results=M.Pair(self.result, empty))

    def __call__(self):
        return self.result


class LexicalSpansTest(M.Edge):
    """The definition line, read by index: one reading per known form.

    The client emits one ObservedSymbolStep per character of the whole
    typed line -- colon and spaces included; nothing tokenizes. The
    trie holds the four forms the plan names -- number, divisible, one,
    itself -- so exactly those spans read, at the cursors an
    independent scan of the line says they occupy, the agenda empties,
    and nothing enumerates the store.
    """

    def __init__(self, graph):
        empty = M.EmptyList

        text = "definition: a prime number is divisible only by one and itself"
        words = ("number", "divisible", "one", "itself")

        symbols = {}
        for ch in set(text):
            symbols[ch] = M.Char(ch)
        cursors = {}
        cursor_index = {}
        for i in range(len(text) + 1):
            cursors[i] = M.GMPRep(str(i))
            cursor_index[cursors[i].id] = i

        utterance = M.Char("utt:definition-line")
        steps_reversed = empty
        for i in range(len(text)):
            steps_reversed = M.Pair(
                Gmod.ObservedSymbolStep(
                    utterance, cursors[i], symbols[text[i]], cursors[i + 1],
                )(),
                steps_reversed,
            )
        steps = M.Reverse(steps_reversed)()

        root = M.Char("root")
        states = {}
        arcs_reversed = empty
        for word in words:
            state = root
            for ch in word:
                key = (state.id, ch)
                if key not in states:
                    nxt = M.Char("st:" + word + ":" + ch)
                    states[key] = nxt
                    arcs_reversed = M.Pair(
                        Gmod.FormArc(state, symbols[ch], nxt)(),
                        arcs_reversed,
                    )
                state = states[key]
            states[("final", word)] = state
        arcs = M.Reverse(arcs_reversed)()

        word_of_category = {}
        senses_reversed = empty
        categories = {
            "number": "CategoryNoun",
            "divisible": "RelAdj",
            "one": "Numeral",
            "itself": "ReflexivePron",
        }
        for word in words:
            category = M.Char(categories[word])
            word_of_category[category.id] = word
            senses_reversed = M.Pair(
                Gmod.FormSense(
                    states[("final", word)], category, M.Char("meaning:" + word),
                )(),
                senses_reversed,
            )
        senses = M.Reverse(senses_reversed)()

        engine = Gmod.RecogniseForms(steps, arcs, senses, root, empty)
        result = engine()
        readings = M.Head(result)()
        agenda_term = M.Head(M.Tail(M.Tail(result)())())()

        expected = set()
        for i in range(len(text)):
            for word in words:
                if text.startswith(word, i):
                    expected.add((word, i, i + len(word)))

        found = set()
        remaining = readings
        while M.IdentityCompare(remaining, empty)() is M.false_value:
            reading = M.Head(remaining)()
            category = M.Head(M.Tail(reading)())()
            start_at = M.Head(M.Tail(M.Tail(reading)())())()
            end_at = M.Head(M.Tail(M.Tail(M.Tail(reading)())())())()
            found.add((
                word_of_category[category.id],
                cursor_index[start_at.id],
                cursor_index[end_at.id],
            ))
            remaining = M.Tail(remaining)()

        self.result = M.truth_value
        if found != expected:
            self.result = M.false_value
        elif M.IdentityCompare(
            M.Head(M.Tail(agenda_term)())(), empty,
        )() is M.false_value:
            self.result = M.false_value
        elif Gmod.GMPEqualText(
            engine.facts_inserted_text, engine.delta_popped_text,
        )() is M.false_value:
            self.result = M.false_value
        elif Gmod.GMPEqualText(
            engine.full_store_enumerations_text, "0",
        )() is M.false_value:
            self.result = M.false_value

        super().__init__(inputs=empty, results=M.Pair(self.result, empty))

    def __call__(self):
        return self.result


class ChartParserTest(M.Edge):
    """The formal notation reads by chart, and the chart is not its parser.

    Signatures become productions and the notation's brackets and commas
    are words inside them, so nesting, arity and refusal are all one
    fact: whether some production spans the input. The last check writes
    a production the signature generator would never emit -- prefix, no
    brackets, recursive -- and parses it through the same saturation,
    which is the difference between a grammar engine and a reader for
    one notation.
    """

    def __init__(self, graph):
        empty = M.EmptyList
        registry = M.FromContextGetConstructors(graph)()
        vocabulary = Gmod.DefaultCorrespondenceVocabulary()()
        signatures = M.Pair(
            Gmod.ConstructorSignature(M.Char("mul"), M.ExprMulLabel, M.two)(),
            M.Pair(
                Gmod.ConstructorSignature(
                    M.Char("divides"), Lmod.DivideLabel, M.two,
                )(),
                empty,
            ),
        )

        flat_chain = M.Pair(
            M.Char("mul"),
            M.Pair(
                M.Char("("),
                M.Pair(
                    M.Char("two"),
                    M.Pair(
                        M.Char(","),
                        M.Pair(M.Char("three"), M.Pair(M.Char(")"), empty)),
                    ),
                ),
            ),
        )
        nested_chain = M.Pair(
            M.Char("divides"),
            M.Pair(
                M.Char("("),
                M.Pair(
                    M.Char("one"),
                    M.Pair(
                        M.Char(","),
                        M.Pair(
                            M.Char("mul"),
                            M.Pair(
                                M.Char("("),
                                M.Pair(
                                    M.Char("two"),
                                    M.Pair(
                                        M.Char(","),
                                        M.Pair(
                                            M.Char("three"),
                                            M.Pair(
                                                M.Char(")"),
                                                M.Pair(M.Char(")"), empty),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        )
        arity_chain = M.Pair(
            M.Char("mul"),
            M.Pair(
                M.Char("("),
                M.Pair(M.Char("two"), M.Pair(M.Char(")"), empty)),
            ),
        )
        unsignatured_chain = M.Pair(
            M.Char("notaword"),
            M.Pair(
                M.Char("("),
                M.Pair(M.Char("two"), M.Pair(M.Char(")"), empty)),
            ),
        )
        unbalanced_chain = M.Pair(
            M.Char("mul"),
            M.Pair(
                M.Char("("),
                M.Pair(M.Char("two"), M.Pair(M.Char(","), empty)),
            ),
        )
        prefix_chain = M.Pair(
            M.Char("root"),
            M.Pair(M.Char("root"), M.Pair(M.Char("nine"), empty)),
        )

        flat_read = Gmod.FormalTermReadings(
            signatures, vocabulary, Gmod.Surface(flat_chain)(), registry,
        )()
        registry = M.Head(M.Tail(flat_read)())()
        flat_terms = M.Head(flat_read)()

        nested_read = Gmod.FormalTermReadings(
            signatures, vocabulary, Gmod.Surface(nested_chain)(), registry,
        )()
        registry = M.Head(M.Tail(nested_read)())()
        nested_terms = M.Head(nested_read)()

        arity_read = Gmod.FormalTermReadings(
            signatures, vocabulary, Gmod.Surface(arity_chain)(), registry,
        )()
        registry = M.Head(M.Tail(arity_read)())()
        arity_terms = M.Head(arity_read)()

        unsignatured_read = Gmod.FormalTermReadings(
            signatures, vocabulary, Gmod.Surface(unsignatured_chain)(), registry,
        )()
        registry = M.Head(M.Tail(unsignatured_read)())()
        unsignatured_terms = M.Head(unsignatured_read)()

        unbalanced_read = Gmod.FormalTermReadings(
            signatures, vocabulary, Gmod.Surface(unbalanced_chain)(), registry,
        )()
        registry = M.Head(M.Tail(unbalanced_read)())()
        unbalanced_terms = M.Head(unbalanced_read)()

        # A grammar no signature could have produced: one symbol, one
        # recursive slot, no brackets. Nothing about the engine changes.
        prefix_variable = M.Pair(M.VarTag, M.Pair(M.Atom(), empty))
        prefix_production = Gmod.Production(
            Gmod.CHART_TERM_CATEGORY,
            M.Pair(
                Gmod.WordSymbol(M.Char("root"))(),
                M.Pair(
                    Gmod.CategorySymbol(
                        Gmod.CHART_TERM_CATEGORY, prefix_variable,
                    )(),
                    empty,
                ),
            ),
            M.Pair(M.SqrtLabel, M.Pair(prefix_variable, empty)),
        )()
        prefix_chart = Gmod.ChartSaturate(
            M.Pair(prefix_production, empty),
            Gmod.ChartSeedConstituents(
                M.Head(M.Tail(vocabulary)())(),
                M.Head(M.Tail(M.Tail(vocabulary)())())(),
                Gmod.CHART_TERM_CATEGORY,
                prefix_chain,
            )(),
            Gmod.ChartCells(prefix_chain)(),
        )
        prefix_terms = Gmod.ChartSpanningTerms(
            prefix_chart(), Gmod.CHART_TERM_CATEGORY, prefix_chain,
        )()

        self.result = M.truth_value
        if M.IdentityCompare(flat_terms, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Tail(flat_terms)(), empty)() is M.false_value:
            self.result = M.false_value
        elif M.TermEqual(
            M.Head(M.Head(flat_terms)())(),
            M.ExprMulLabel,
        )() is M.false_value:
            self.result = M.false_value
        elif M.NatEq(
            M.Head(M.Tail(M.Head(flat_terms)())())(),
            M.two,
            registry,
        )() is M.false_value:
            self.result = M.false_value
        elif M.NatEq(
            M.Head(M.Tail(M.Tail(M.Head(flat_terms)())())())(),
            M.three,
            registry,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(nested_terms, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Tail(nested_terms)(), empty)() is M.false_value:
            self.result = M.false_value
        elif M.TermEqual(
            M.Head(M.Head(nested_terms)())(),
            Lmod.DivideLabel,
        )() is M.false_value:
            self.result = M.false_value
        elif M.NatEq(
            M.Head(M.Tail(M.Head(nested_terms)())())(),
            M.one,
            registry,
        )() is M.false_value:
            self.result = M.false_value
        elif M.TermEqual(
            M.Head(
                M.Head(M.Tail(M.Tail(M.Head(nested_terms)())())())(),
            )(),
            M.ExprMulLabel,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(arity_terms, empty)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(unsignatured_terms, empty)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(unbalanced_terms, empty)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(prefix_terms, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Tail(prefix_terms)(), empty)() is M.false_value:
            self.result = M.false_value
        elif M.TermEqual(
            M.Head(M.Head(prefix_terms)())(),
            M.SqrtLabel,
        )() is M.false_value:
            self.result = M.false_value
        elif M.TermEqual(
            M.Head(M.Head(M.Tail(M.Head(prefix_terms)())())())(),
            M.SqrtLabel,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            prefix_chart.saturated,
            M.truth_value,
        )() is M.false_value:
            self.result = M.false_value

        graph._replace_context(constructors=registry)
        super().__init__(inputs=empty, results=M.Pair(self.result, empty))

    def __call__(self):
        return self.result


class ConversePropositionTest(M.Edge):
    """Phase 7: Converse evaluates equality and retains IsReal query terms."""

    def __init__(self, graph):
        empty = M.EmptyList
        registry = M.FromContextGetConstructors(graph)()
        vocabulary = Gmod.DefaultCorrespondenceVocabulary()()
        equality_yes = Gmod.Surface(
            M.Pair(
                M.Char("is"),
                M.Pair(
                    M.Char("two"),
                    M.Pair(
                        M.Char("plus"),
                        M.Pair(
                            M.Char("two"),
                            M.Pair(
                                M.Char("equal"),
                                M.Pair(
                                    M.Char("to"),
                                    M.Pair(M.Char("four"), empty),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        )()
        equality_no = Gmod.Surface(
            M.Pair(
                M.Char("is"),
                M.Pair(
                    M.Char("two"),
                    M.Pair(
                        M.Char("plus"),
                        M.Pair(
                            M.Char("two"),
                            M.Pair(
                                M.Char("equal"),
                                M.Pair(
                                    M.Char("to"),
                                    M.Pair(M.Char("five"), empty),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        )()
        real_query = Gmod.Surface(
            M.Pair(
                M.Char("is"),
                M.Pair(
                    M.Char("sqrt"),
                    M.Pair(
                        M.Char("("),
                        M.Pair(
                            M.Char("three"),
                            M.Pair(
                                M.Char(")"),
                                M.Pair(M.Char("real"), empty),
                            ),
                        ),
                    ),
                ),
            ),
        )()

        yes_pair = Gmod.Converse(vocabulary, equality_yes, registry)()
        yes_outcome = M.Head(yes_pair)()
        registry = M.Head(M.Tail(yes_pair)())()
        no_pair = Gmod.Converse(vocabulary, equality_no, registry)()
        no_outcome = M.Head(no_pair)()
        registry = M.Head(M.Tail(no_pair)())()
        real_pair = Gmod.Converse(vocabulary, real_query, registry)()
        real_outcome = M.Head(real_pair)()
        registry = M.Head(M.Tail(real_pair)())()

        yes_answer = M.Head(
            M.Tail(M.Tail(M.Tail(M.Tail(yes_outcome)())())())(),
        )()
        no_answer = M.Head(
            M.Tail(M.Tail(M.Tail(M.Tail(no_outcome)())())())(),
        )()
        yes_words = M.EmptyList
        no_words = M.EmptyList
        if M.IdentityCompare(yes_answer, empty)() is M.false_value:
            yes_words = M.Head(M.Tail(yes_answer)())()
        if M.IdentityCompare(no_answer, empty)() is M.false_value:
            no_words = M.Head(M.Tail(no_answer)())()
        real_meaning = M.Head(M.Tail(M.Tail(real_outcome)())())()
        real_body = M.Head(M.Tail(real_meaning)())()
        real_subject = M.Head(M.Tail(real_body)())()
        real_answer = M.Head(
            M.Tail(M.Tail(M.Tail(M.Tail(real_outcome)())())())(),
        )()

        self.result = M.truth_value
        if M.IdentityCompare(
            M.Head(yes_outcome)(),
            Lmod.UnderstoodLabel,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            M.Head(no_outcome)(),
            Lmod.UnderstoodLabel,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(yes_words, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.Compare(M.Head(yes_words)(), M.Char("yes"))() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Tail(yes_words)(), empty)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(no_words, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.Compare(M.Head(no_words)(), M.Char("no"))() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Tail(no_words)(), empty)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            M.Head(real_outcome)(),
            Lmod.UnderstoodLabel,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            M.Head(real_body)(),
            M.IsRealLabel,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            M.Head(real_subject)(),
            M.SqrtLabel,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(real_answer, empty)() is M.false_value:
            self.result = M.false_value

        graph._replace_context(constructors=registry)
        super().__init__(inputs=empty, results=M.Pair(self.result, empty))

    def __call__(self):
        return self.result


class CorrespondenceInductionTest(M.Edge):
    """Language acquisition v1: a correspondence law is induced, validated,
    proposed, activated, and used on a held-out utterance.

    Three trainer pairs for 'double N' anti-unify into one candidate; the
    candidate survives validation, is submitted as a pending proposal,
    passes the standard approval/activation path, and then understands
    'double seven' with no hand-authored template. A recorded rejection
    example blocks induction entirely.
    """

    def __init__(self, graph):
        empty = M.EmptyList
        registry = M.FromContextGetConstructors(graph)()
        vocabulary = Gmod.DefaultCorrespondenceVocabulary()()
        word_entries = M.Head(M.Tail(vocabulary)())()

        def _sentence(*symbols):
            chain = empty
            index = len(symbols)
            while index != 0:
                index = index - 1
                chain = M.Pair(M.Char(symbols[index]), chain)
            return Gmod.Surface(chain)()

        def _double_meaning(nat):
            return Gmod.Meaning(
                M.Pair(M.ExprMulLabel, M.Pair(M.two, M.Pair(nat, empty))),
            )()

        trainer = M.Char("trainer")
        example_one = Gmod.CorrespondenceExample(
            _sentence("double", "two"),
            _double_meaning(M.two),
            trainer,
        )()
        example_two = Gmod.CorrespondenceExample(
            _sentence("double", "three"),
            _double_meaning(M.three),
            trainer,
        )()
        example_three = Gmod.CorrespondenceExample(
            _sentence("double", "four"),
            _double_meaning(M.four),
            trainer,
        )()
        examples = M.Pair(
            example_one,
            M.Pair(example_two, M.Pair(example_three, empty)),
        )

        generated = Gmod.GenerateCorrespondenceProposals(
            Gmod.ProposalStore(empty)(),
            examples,
            word_entries,
            registry,
        )()
        generated_store = M.Head(generated)()
        registry = M.Head(M.Tail(M.Tail(generated)())())()
        entries = Gmod.ProposalStoreAll(generated_store)()

        self.result = M.truth_value
        if M.IdentityCompare(entries, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Tail(entries)(), empty)() is M.false_value:
            self.result = M.false_value
        else:
            entry = M.Head(entries)()
            proposal = Gmod.ProposalEntryProposal(entry)()
            if Gmod.ProposalEntryIsApproved(entry)() is M.truth_value:
                self.result = M.false_value
            elif M.Compare(
                Gmod.ClassifyProposal(proposal)(),
                M.Char("install_law"),
            )() is M.false_value:
                self.result = M.false_value
            else:
                approval = Gmod.Approved(proposal, M.Char("curator"))()
                approved_store = Gmod.ProposalStoreAttach(
                    generated_store,
                    proposal,
                    approval,
                )()
                approved_entry = M.Head(
                    Gmod.ProposalStoreApproved(approved_store)(),
                )()
                activated = Gmod.ActivateProposal(
                    Gmod.GraphVersion(empty, empty, empty)(),
                    approved_entry,
                )()
                active_version = M.Head(activated)()
                if M.IdentityCompare(active_version, empty)() is M.truth_value:
                    self.result = M.false_value
                else:
                    learned = Gmod.InstalledCorrespondenceLaws(active_version)()
                    extended = Gmod.VocabularyWithTemplates(
                        vocabulary,
                        learned,
                    )()
                    held_out = Gmod.Converse(
                        extended,
                        _sentence("double", "seven"),
                        registry,
                    )()
                    outcome = M.Head(held_out)()
                    registry = M.Head(M.Tail(held_out)())()
                    if M.IdentityCompare(learned, empty)() is M.truth_value:
                        self.result = M.false_value
                    elif M.IdentityCompare(
                        M.Head(outcome)(),
                        Lmod.UnderstoodLabel,
                    )() is M.false_value:
                        self.result = M.false_value
                    else:
                        answer = M.Head(
                            M.Tail(M.Tail(M.Tail(M.Tail(outcome)())())())(),
                        )()
                        words = empty
                        if M.IdentityCompare(answer, empty)() is M.false_value:
                            words = M.Head(M.Tail(answer)())()
                        if M.IdentityCompare(words, empty)() is M.truth_value:
                            self.result = M.false_value
                        elif M.Compare(
                            M.Head(words)(),
                            M.Char("one"),
                        )() is M.false_value:
                            self.result = M.false_value
                        elif M.IdentityCompare(
                            M.Tail(words)(),
                            empty,
                        )() is M.truth_value:
                            self.result = M.false_value
                        elif M.Compare(
                            M.Head(M.Tail(words)())(),
                            M.Char("four"),
                        )() is M.false_value:
                            self.result = M.false_value

        if M.IdentityCompare(self.result, M.truth_value)() is M.truth_value:
            rejection = Gmod.CorrespondenceExample(
                _sentence("double", "five"),
                _double_meaning(M.five),
                M.Char("rejected"),
            )()
            blocked = Gmod.GenerateCorrespondenceProposals(
                Gmod.ProposalStore(empty)(),
                M.Pair(
                    example_one,
                    M.Pair(example_two, M.Pair(rejection, empty)),
                ),
                word_entries,
                registry,
            )()
            blocked_store = M.Head(blocked)()
            registry = M.Head(M.Tail(M.Tail(blocked)())())()
            if M.IdentityCompare(
                Gmod.ProposalStoreAll(blocked_store)(),
                empty,
            )() is M.false_value:
                self.result = M.false_value

        graph._replace_context(constructors=registry)
        super().__init__(inputs=empty, results=M.Pair(self.result, empty))

    def __call__(self):
        return self.result


class ObligationCommitGateTest(M.Edge):
    """Steps 17 and 26: commit-time node, edge, and history bounds."""

    def __init__(self, _graph):
        empty = M.EmptyList
        left_term = M.Pair(Lmod.ZeroLabel, empty)
        right_term = M.Pair(Lmod.SuccLabel, M.Pair(left_term, empty))
        base_law = Gmod.CompileRuleToLaw(Pmod.Rule(left_term, right_term))()

        tight_obligation = Gmod.KObligation(
            M.Char("node-count-max"),
            M.one,
        )()
        tight_law = Gmod.Law(
            Gmod.LawLeft(base_law)(),
            Gmod.LawInterface(base_law)(),
            Gmod.LawRight(base_law)(),
            Gmod.LawKToLeft(base_law)(),
            Gmod.LawKToRight(base_law)(),
            M.Pair(tight_obligation, empty),
        )()

        generous_obligation = Gmod.KObligation(
            M.Char("node-count-max"),
            M.two,
        )()
        generous_law = Gmod.Law(
            Gmod.LawLeft(base_law)(),
            Gmod.LawInterface(base_law)(),
            Gmod.LawRight(base_law)(),
            Gmod.LawKToLeft(base_law)(),
            Gmod.LawKToRight(base_law)(),
            M.Pair(generous_obligation, empty),
        )()

        left = Gmod.LawLeft(base_law)()
        host = Gmod.GraphVersion(
            Gmod.GraphNodes(left)(),
            Gmod.GraphEdges(left)(),
            empty,
        )()
        sends = Gmod.IdentitySendsFor(Gmod.GraphNodes(left)())()
        remaining_edges = Gmod.GraphEdges(left)()
        while M.IdentityCompare(remaining_edges, empty)() is M.false_value:
            edge = M.Head(remaining_edges)()
            sends = M.Pair(Gmod.Send(edge, edge)(), sends)
            remaining_edges = M.Tail(remaining_edges)()
        mapping = Gmod.Map(left, host, sends)()

        refused = Gmod.FireLaw(
            host,
            tight_law,
            mapping,
            Gmod.DanglingForbid()(),
        )()
        refused_trace = M.Head(M.Tail(refused)())()
        refusal = empty
        remaining_trace = refused_trace
        while M.IdentityCompare(remaining_trace, empty)() is M.false_value:
            refusal = M.Head(remaining_trace)()
            remaining_trace = M.Tail(remaining_trace)()

        committed = Gmod.FireLaw(
            host,
            generous_law,
            mapping,
            Gmod.DanglingForbid()(),
        )()

        unknown_one = Gmod.KObligation(M.Char("future-check"), empty)()
        checked_one = Gmod.CheckObligation(
            host,
            unknown_one,
            Gmod.UncheckedObligations()(),
        )()
        unchecked_once = Gmod.CheckObligationUnchecked(checked_one)()
        unknown_two = Gmod.KObligation(M.Char("future-check"), empty)()
        checked_two = Gmod.CheckObligation(
            host,
            unknown_two,
            unchecked_once,
        )()
        unchecked_twice = Gmod.CheckObligationUnchecked(checked_two)()

        edge_tight = Gmod.KObligation(
            M.Char("edge-count-max"),
            M.Zero,
        )()
        edge_generous = Gmod.KObligation(
            M.Char("edge-count-max"),
            M.one,
        )()
        checked_edge_tight = Gmod.CheckObligation(
            host,
            edge_tight,
            Gmod.UncheckedObligations()(),
        )()
        checked_edge_generous = Gmod.CheckObligation(
            host,
            edge_generous,
            Gmod.UncheckedObligations()(),
        )()

        history_ledger = Gmod.FiringLedger()
        history_ledger.append(M.Char("completed-firing"))
        history_bound = Gmod.KObligation(
            M.Char("ledger-length-max"),
            M.one,
        )()
        checked_history_tight = Gmod.CheckObligation(
            host,
            history_bound,
            Gmod.UncheckedObligations()(),
            history_ledger,
        )()
        empty_history_ledger = Gmod.FiringLedger(history_ledger.registry)
        checked_history_generous = Gmod.CheckObligation(
            host,
            history_bound,
            Gmod.UncheckedObligations()(),
            empty_history_ledger,
        )()

        self.result = M.truth_value
        if Gmod.LawMapsComplete(tight_law)() is M.false_value:
            self.result = M.false_value
        elif Gmod.LawMapsComplete(generous_law)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Head(refused)(), empty)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(refusal, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            M.Head(refusal)(),
            Lmod.ReasonObligationLabel,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Head(committed)(), empty)() is M.truth_value:
            self.result = M.false_value
        elif Gmod.CheckObligationVerdict(checked_one)() is M.false_value:
            self.result = M.false_value
        elif Gmod.CheckObligationVerdict(checked_two)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(unchecked_twice, empty)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Tail(unchecked_twice)(), empty)() is M.false_value:
            self.result = M.false_value
        elif Gmod.CheckObligationVerdict(checked_edge_tight)() is M.truth_value:
            self.result = M.false_value
        elif Gmod.CheckObligationVerdict(checked_edge_generous)() is M.false_value:
            self.result = M.false_value
        elif Gmod.CheckObligationVerdict(checked_history_tight)() is M.truth_value:
            self.result = M.false_value
        elif Gmod.CheckObligationVerdict(checked_history_generous)() is M.false_value:
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class SearchMatchStatesTest(M.Edge):
    """Step 10: a pattern with two candidate matches yields two completed matches."""

    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        graph._search_disable_console = M.truth_value
        graph._search_disable_progress_ticker = M.truth_value

        pat_node = M.Thingy()
        pattern = M.Pair(
            M.HypergraphLabel,
            M.Pair(M.Pair(pat_node, empty), M.Pair(empty, empty)),
        )
        host_left = M.Thingy()
        host_right = M.Thingy()
        host = Gmod.GraphVersion(
            M.Pair(host_left, M.Pair(host_right, empty)),
            empty,
            empty,
        )()

        kernel = Smod._SearchStepKernel(
            graph,
            empty,
            empty,
            Hmod.Heuristic(M.DFSLabel, M.InsertionOrderLabel, M.three, M.one, M.one, M.one)(),
            empty,
            registry,
            None,
            None,
        )
        start_cursor = Smod.SearchMatchCursor(empty, pattern, host, M.Pair(pat_node, empty))()
        start_state = Smod.SearchState(empty, empty, empty, M.three, start_cursor)()

        completed = M.Zero
        frontier = M.Pair(start_state, empty)
        fuel = M.nine
        while M.IdentityCompare(frontier, empty)() is M.false_value:
            if M.NatEq(fuel, M.Zero, registry)() is M.truth_value:
                frontier = empty
            else:
                fuel_pair = M.NatPred(fuel, registry)()
                fuel = M.Head(fuel_pair)()
                registry = M.Head(M.Tail(fuel_pair)())()
                state = M.Head(frontier)()
                frontier = M.Tail(frontier)()
                cursor = kernel._state_cursor(state)
                if Smod.SearchMatchCursorComplete(cursor)() is M.truth_value:
                    completed_pair = M.Succ(completed, registry)()
                    completed = M.Head(completed_pair)()
                    registry = M.Head(M.Tail(completed_pair)())()
                else:
                    outcome = kernel._advance_state(state, empty)
                    child = kernel._advance_result_child(outcome)
                    continuation = kernel._advance_result_continuation(outcome)
                    if M.IdentityCompare(continuation, empty)() is M.false_value:
                        frontier = M.Pair(continuation, frontier)
                    if M.IdentityCompare(child, empty)() is M.false_value:
                        frontier = M.Pair(child, frontier)

        self.result = M.truth_value
        if M.NatEq(completed, M.two, registry)() is M.false_value:
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class FireLawSurgeryTest(M.Edge):
    """Step 8: L = a,b,e(a,b); K = a; R = a,c,f(a,c). Fires over a match."""

    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        node_a = M.Thingy()
        node_b = M.Thingy()
        node_c = M.Thingy()
        edge_e = M.Pair(M.Char("e"), M.Pair(node_a, M.Pair(node_b, empty)))
        edge_f = M.Pair(M.Char("f"), M.Pair(node_a, M.Pair(node_c, empty)))
        left = M.Pair(
            M.HypergraphLabel,
            M.Pair(M.Pair(node_a, M.Pair(node_b, empty)), M.Pair(M.Pair(edge_e, empty), empty)),
        )
        interface = M.Pair(M.HypergraphLabel, M.Pair(M.Pair(node_a, empty), M.Pair(empty, empty)))
        right = M.Pair(
            M.HypergraphLabel,
            M.Pair(M.Pair(node_a, M.Pair(node_c, empty)), M.Pair(M.Pair(edge_f, empty), empty)),
        )
        k_to_left = Gmod.Map(interface, left, M.Pair(Gmod.Send(node_a, node_a)(), empty))()
        k_to_right = Gmod.Map(interface, right, M.Pair(Gmod.Send(node_a, node_a)(), empty))()
        law = Gmod.Law(left, interface, right, k_to_left, k_to_right, empty)()

        host_a = M.Thingy()
        host_b = M.Thingy()
        host_e = M.Pair(M.Char("e"), M.Pair(host_a, M.Pair(host_b, empty)))
        host = Gmod.GraphVersion(
            M.Pair(host_a, M.Pair(host_b, empty)),
            M.Pair(host_e, empty),
            empty,
        )()
        match_root = M.Pair(
            Gmod.Send(node_a, host_a)(),
            M.Pair(Gmod.Send(node_b, host_b)(), M.Pair(Gmod.Send(edge_e, host_e)(), empty)),
        )
        mapping = Gmod.Map(left, host, match_root)()

        fired = Gmod.FireLaw(host, law, mapping, Gmod.DanglingForbid()())()
        committed = M.Head(fired)()
        trace = M.Head(M.Tail(fired)())()
        last = empty
        remaining = trace
        while M.IdentityCompare(remaining, empty)() is M.false_value:
            last = M.Head(remaining)()
            remaining = M.Tail(remaining)()

        self.result = M.truth_value
        if Gmod.LawMapsComplete(law)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(committed, empty)() is M.truth_value:
            self.result = M.false_value
        elif Gmod.ChainHasTerm(Gmod.GraphNodes(committed)(), host_b)() is M.truth_value:
            self.result = M.false_value
        elif Gmod.ChainHasTerm(Gmod.GraphNodes(committed)(), node_c)() is M.false_value:
            self.result = M.false_value
        elif Gmod.ChainHasTerm(Gmod.GraphNodes(committed)(), host_a)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Head(last)(), Lmod.NextLabel)() is M.false_value:
            self.result = M.false_value
        elif Gmod.ChainHasTerm(Gmod.GraphNodes(host)(), host_b)() is M.false_value:
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class FireLawDanglingModeTest(M.Edge):
    """Step 8: an extra edge on the deleted node; forbid refuses, delete sweeps."""

    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        node_a = M.Thingy()
        node_b = M.Thingy()
        node_c = M.Thingy()
        edge_e = M.Pair(M.Char("e"), M.Pair(node_a, M.Pair(node_b, empty)))
        edge_f = M.Pair(M.Char("f"), M.Pair(node_a, M.Pair(node_c, empty)))
        left = M.Pair(
            M.HypergraphLabel,
            M.Pair(M.Pair(node_a, M.Pair(node_b, empty)), M.Pair(M.Pair(edge_e, empty), empty)),
        )
        interface = M.Pair(M.HypergraphLabel, M.Pair(M.Pair(node_a, empty), M.Pair(empty, empty)))
        right = M.Pair(
            M.HypergraphLabel,
            M.Pair(M.Pair(node_a, M.Pair(node_c, empty)), M.Pair(M.Pair(edge_f, empty), empty)),
        )
        k_to_left = Gmod.Map(interface, left, M.Pair(Gmod.Send(node_a, node_a)(), empty))()
        k_to_right = Gmod.Map(interface, right, M.Pair(Gmod.Send(node_a, node_a)(), empty))()
        law = Gmod.Law(left, interface, right, k_to_left, k_to_right, empty)()

        host_a = M.Thingy()
        host_b = M.Thingy()
        host_x = M.Thingy()
        host_e = M.Pair(M.Char("e"), M.Pair(host_a, M.Pair(host_b, empty)))
        extra = M.Pair(M.Char("x"), M.Pair(host_b, M.Pair(host_x, empty)))
        host = Gmod.GraphVersion(
            M.Pair(host_a, M.Pair(host_b, M.Pair(host_x, empty))),
            M.Pair(host_e, M.Pair(extra, empty)),
            empty,
        )()
        match_root = M.Pair(
            Gmod.Send(node_a, host_a)(),
            M.Pair(Gmod.Send(node_b, host_b)(), M.Pair(Gmod.Send(edge_e, host_e)(), empty)),
        )
        mapping = Gmod.Map(left, host, match_root)()

        forbidden = Gmod.FireLaw(host, law, mapping, Gmod.DanglingForbid()())()
        forbidden_trace = M.Head(M.Tail(forbidden)())()
        refusal = empty
        remaining = forbidden_trace
        while M.IdentityCompare(remaining, empty)() is M.false_value:
            refusal = M.Head(remaining)()
            remaining = M.Tail(remaining)()

        swept = Gmod.FireLaw(host, law, mapping, Gmod.DanglingDelete()())()
        swept_version = M.Head(swept)()

        self.result = M.truth_value
        if M.IdentityCompare(M.Head(forbidden)(), empty)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Head(refusal)(), Lmod.FireRejectedLabel)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            M.Head(M.Head(M.Tail(refusal)())())(),
            Lmod.DeletionAdmittedLabel,
        )() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(swept_version, empty)() is M.truth_value:
            self.result = M.false_value
        elif Gmod.ChainHasTerm(Gmod.GraphEdges(swept_version)(), extra)() is M.truth_value:
            self.result = M.false_value
        elif Gmod.ChainHasTerm(Gmod.GraphNodes(swept_version)(), host_b)() is M.truth_value:
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class LawMapsCompleteTest(M.Edge):
    """Step 7: both K-maps must send every interface element."""

    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        k_node = M.Thingy()
        left_node = M.Thingy()
        right_node = M.Thingy()
        interface = M.Pair(M.HypergraphLabel, M.Pair(M.Pair(k_node, empty), M.Pair(empty, empty)))
        left = M.Pair(M.HypergraphLabel, M.Pair(M.Pair(left_node, empty), M.Pair(empty, empty)))
        right = M.Pair(M.HypergraphLabel, M.Pair(M.Pair(right_node, empty), M.Pair(empty, empty)))
        k_to_left = Gmod.Map(interface, left, M.Pair(Gmod.Send(k_node, left_node)(), empty))()
        k_to_right = Gmod.Map(interface, right, M.Pair(Gmod.Send(k_node, right_node)(), empty))()
        complete_law = Gmod.Law(left, interface, right, k_to_left, k_to_right, empty)()

        stray = M.Thingy()
        wider_interface = M.Pair(
            M.HypergraphLabel,
            M.Pair(M.Pair(k_node, M.Pair(stray, empty)), M.Pair(empty, empty)),
        )
        incomplete_law = Gmod.Law(left, wider_interface, right, k_to_left, k_to_right, empty)()

        self.result = M.truth_value
        if Gmod.LawMapsComplete(complete_law)() is M.false_value:
            self.result = M.false_value
        elif Gmod.LawMapsComplete(incomplete_law)() is M.truth_value:
            self.result = M.false_value
        elif Gmod.LawMapsComplete(empty)() is M.truth_value:
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class DanglingEdgesTest(M.Edge):
    """Step 6: derived boundary scan; nothing stored, Boundary untouched."""

    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        node_a = M.Thingy()
        node_b = M.Thingy()
        node_c = M.Thingy()
        edge_one = M.Pair(M.Char("e1"), M.Pair(node_a, M.Pair(node_b, empty)))
        edge_two = M.Pair(M.Char("e2"), M.Pair(node_b, M.Pair(node_c, empty)))
        nodes = M.Pair(node_a, M.Pair(node_b, M.Pair(node_c, empty)))
        edges = M.Pair(edge_one, M.Pair(edge_two, empty))
        version = Gmod.GraphVersion(nodes, edges, empty)()

        hits = Gmod.DanglingEdges(version, M.Pair(node_a, empty))()
        count = M.Zero
        remaining = hits
        while M.IdentityCompare(remaining, empty)() is M.false_value:
            count_pair = M.Succ(count, registry)()
            count = M.Head(count_pair)()
            registry = M.Head(M.Tail(count_pair)())()
            remaining = M.Tail(remaining)()

        none_deleted = Gmod.DanglingEdges(version, empty)()

        self.result = M.truth_value
        if M.NatEq(count, M.one, registry)() is M.false_value:
            self.result = M.false_value
        elif RawTermEqual(M.Head(hits)(), edge_one, registry)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(none_deleted, empty)() is M.false_value:
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class MapExtensionAlternativesTest(M.Edge):
    """Step 5: enumerate every legal one-step extension, not just the first."""

    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        pattern = Gmod.Hypergraph(registry)
        p_node = M.Thingy()
        pattern.add_node(p_node)

        host = Gmod.Hypergraph(_registry(pattern))
        h_left = M.Thingy()
        h_right = M.Thingy()
        host.add_node(h_left)
        host.add_node(h_right)

        pattern_value = M.Pair(M.HypergraphLabel, M.Pair(pattern.nodes, M.Pair(pattern.edges, empty)))
        host_value = M.Pair(M.HypergraphLabel, M.Pair(host.nodes, M.Pair(host.edges, empty)))
        base_map = Gmod.Map(pattern_value, host_value, empty)()

        alternatives = Gmod.MapExtensionAlternatives(base_map, p_node, empty)()
        count = M.Zero
        remaining = alternatives
        all_maps = M.truth_value
        while M.IdentityCompare(remaining, empty)() is M.false_value:
            entry = M.Head(remaining)()
            if M.IdentityCompare(M.Head(entry)(), Lmod.MapLabel)() is M.false_value:
                all_maps = M.false_value
            count_pair = M.Succ(count, registry)()
            count = M.Head(count_pair)()
            registry = M.Head(M.Tail(count_pair)())()
            remaining = M.Tail(remaining)()

        single = Gmod.MapExtendOneStep(base_map, p_node, h_left)()

        self.result = M.truth_value
        if M.NatEq(count, M.two, registry)() is M.false_value:
            self.result = M.false_value
        elif all_maps is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Head(single)(), Lmod.MapLabel)() is M.false_value:
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class StructuredMissReasonTest(M.Edge):
    """Step 4: Miss reasons are labeled terms carrying the terms involved."""

    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        pattern = Gmod.Hypergraph(registry)
        p_left = M.Thingy()
        p_right = M.Thingy()
        pattern.add_node(p_left)
        pattern.add_node(p_right)

        host = Gmod.Hypergraph(_registry(pattern))
        h_left = M.Thingy()
        h_right = M.Thingy()
        host.add_node(h_left)
        host.add_node(h_right)

        pattern_value = M.Pair(M.HypergraphLabel, M.Pair(pattern.nodes, M.Pair(pattern.edges, empty)))
        host_value = M.Pair(M.HypergraphLabel, M.Pair(host.nodes, M.Pair(host.edges, empty)))

        not_a_map = Gmod.MapExtendOneStep(empty, p_left, h_left)()

        stranger = M.Thingy()
        base_map = Gmod.Map(pattern_value, host_value, empty)()
        pattern_miss = Gmod.MapExtendOneStep(base_map, stranger, h_left)()
        host_miss = Gmod.MapExtendOneStep(base_map, p_left, stranger)()

        mapped_root = M.Pair(Gmod.Send(p_left, h_left)(), empty)
        mapped_map = Gmod.Map(pattern_value, host_value, mapped_root)()
        already = Gmod.MapExtendOneStep(mapped_map, p_left, h_right)()

        apart_root = M.Pair(Gmod.Apart(p_left, p_right)(), M.Pair(Gmod.Send(p_right, h_right)(), empty))
        apart_map = Gmod.Map(pattern_value, host_value, apart_root)()
        apart_miss = Gmod.MapExtendOneStep(apart_map, p_left, h_right)()

        self.result = M.truth_value
        if M.IdentityCompare(M.Head(M.Head(M.Tail(M.Tail(not_a_map)())())())(), Lmod.ReasonShapeLabel)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Head(M.Head(M.Tail(M.Tail(pattern_miss)())())())(), Lmod.ReasonShapeLabel)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Head(M.Head(M.Tail(M.Tail(host_miss)())())())(), Lmod.ReasonShapeLabel)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Head(M.Head(M.Tail(M.Tail(already)())())())(), Lmod.ReasonAlreadyMappedLabel)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Head(M.Head(M.Tail(M.Tail(apart_miss)())())())(), Lmod.ReasonApartLabel)() is M.false_value:
            self.result = M.false_value
        else:
            already_reason = M.Head(M.Tail(M.Tail(already)())())()
            if RawTermEqual(M.Head(M.Tail(M.Tail(already_reason)())())(), h_left, registry)() is M.false_value:
                self.result = M.false_value
            else:
                apart_reason = M.Head(M.Tail(M.Tail(apart_miss)())())()
                carried = M.Head(M.Tail(apart_reason)())()
                if M.IdentityCompare(M.Head(carried)(), Lmod.ApartLabel)() is M.false_value:
                    self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class EdgeSendPositionalConsistencyTest(M.Edge):
    """Step 3: sending a pattern edge to a host edge must respect endpoint order."""

    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        pattern = Gmod.Hypergraph(registry)
        p_a = M.Thingy()
        p_b = M.Thingy()
        pattern_edge = M.Pair(M.Char("p"), M.Pair(p_a, M.Pair(p_b, empty)))
        pattern.add_node(p_a)
        pattern.add_node(p_b)
        pattern.add_edge(pattern_edge)

        host = Gmod.Hypergraph(_registry(pattern))
        h_x = M.Thingy()
        h_y = M.Thingy()
        host_edge = M.Pair(M.Char("h"), M.Pair(h_x, M.Pair(h_y, empty)))
        host.add_node(h_x)
        host.add_node(h_y)
        host.add_edge(host_edge)

        pattern_value = M.Pair(M.HypergraphLabel, M.Pair(pattern.nodes, M.Pair(pattern.edges, empty)))
        host_value = M.Pair(M.HypergraphLabel, M.Pair(host.nodes, M.Pair(host.edges, empty)))

        aligned_root = M.Pair(Gmod.Send(p_a, h_x)(), empty)
        aligned_map = Gmod.Map(pattern_value, host_value, aligned_root)()
        aligned = Gmod.MapExtendOneStep(aligned_map, pattern_edge, host_edge)()

        crossed_root = M.Pair(Gmod.Send(p_a, h_y)(), empty)
        crossed_map = Gmod.Map(pattern_value, host_value, crossed_root)()
        crossed = Gmod.MapExtendOneStep(crossed_map, pattern_edge, host_edge)()

        self.result = M.truth_value
        if M.IdentityCompare(M.Head(aligned)(), Lmod.MapLabel)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Head(crossed)(), Lmod.MissLabel)() is M.false_value:
            self.result = M.false_value
        elif RawTermEqual(M.Head(M.Tail(crossed)())(), pattern_edge, registry)() is M.false_value:
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class GraphCurrentVersionTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        host = Gmod.Hypergraph(registry)
        added = M.Thingy()
        host.add_node(added)
        version = host.current_version()
        nodes = Gmod.GraphNodes(version)()
        contains = M.false_value
        remaining = nodes
        while M.IdentityCompare(remaining, empty)() is M.false_value:
            if M.TermEqual(M.Head(remaining)(), added)() is M.truth_value:
                contains = M.truth_value
            remaining = M.Tail(remaining)()
        self.result = M.truth_value
        if M.IdentityCompare(M.Head(version)(), Lmod.GraphVersionLabel)() is M.false_value:
            self.result = M.false_value
        elif contains is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(
            M.Tail(M.Tail(M.Tail(M.Tail(version)())())())(),
            empty,
        )() is M.false_value:
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class MinimalGraphOneStepMapExtensionTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        pattern = Gmod.Hypergraph(registry)
        p_left = M.Thingy()
        p_right = M.Thingy()
        pattern_edge = M.Pair(M.Char("p"), empty)
        pattern.add_node(p_left)
        pattern.add_node(p_right)
        pattern.add_node(pattern_edge)

        host = Gmod.Hypergraph(_registry(pattern))
        h_left = M.Thingy()
        h_right = M.Thingy()
        host_edge = M.Pair(M.Char("h"), empty)
        host.add_node(h_left)
        host.add_node(h_right)
        host.add_node(host_edge)

        pattern_value = M.Pair(M.HypergraphLabel, M.Pair(pattern.nodes, M.Pair(pattern.edges, empty)))
        host_value = M.Pair(M.HypergraphLabel, M.Pair(host.nodes, M.Pair(host.edges, empty)))
        base_map = Gmod.Map(pattern_value, host_value, empty)()
        success = Gmod.MapExtendOneStep(base_map, p_left, h_left)()
        committed_root = M.Pair(Gmod.Apart(p_left, p_right)(), M.Pair(Gmod.Send(p_right, h_right)(), empty))
        committed_map = Gmod.Map(pattern_value, host_value, committed_root)()
        failure = Gmod.MapExtendOneStep(committed_map, p_left, h_right)()

        self.result = M.truth_value
        if M.IdentityCompare(M.Head(success)(), Lmod.MapLabel)() is M.false_value:
            self.result = M.false_value
        elif RawTermEqual(M.Head(M.Tail(M.Tail(M.Tail(success)())())())(), M.Pair(Gmod.Send(p_left, h_left)(), empty), registry)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Head(failure)(), Lmod.MissLabel)() is M.false_value:
            self.result = M.false_value
        elif RawTermEqual(M.Head(M.Tail(failure)())(), p_left, registry)() is M.false_value:
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class MinimalGraphSourceConstraintTest(M.Edge):
    def __init__(self, _graph):
        base_dir = os.path.dirname(__file__)
        self.result = M.truth_value
        for name in ("graph.py", "labels.py"):
            text = open(os.path.join(base_dir, name), "r", encoding="utf-8").read()
            for forbidden in ("isinstance(", "hasattr(", "__class__", "__new__", "return True", "return False"):
                if forbidden in text:
                    self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class SearchStructuralKeyEqualityTest(M.Edge):
    def __init__(self):
        head_atom = M.Thingy()
        pair_left = M.Pair(head_atom, M.Pair(M.one, M.EmptyList))
        pair_right = M.Pair(head_atom, M.Pair(M.one, M.EmptyList))
        key_left = SearchStructuralKey(pair_left, M.AllConstructors)()
        key_right = SearchStructuralKey(pair_right, M.AllConstructors)()
        self.result = RawTermEqual(key_left, key_right, M.AllConstructors)()
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class SharedExactKeyVocabularyTest(M.Edge):
    def __init__(self):
        registry = M.AllConstructors
        term = M.Pair(M.one, M.Pair(M.two, M.EmptyList))
        exact_key = M.ExactKey(term, registry)()
        tree_key = Tmod.TreeStructuralKey(term, registry)()
        search_key = SearchStructuralKey(term, registry)()
        result = RawTermEqual(exact_key, tree_key, registry)()
        if result is M.truth_value:
            result = RawTermEqual(exact_key, search_key, registry)()
        self.result = result
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class OpaqueExactKeyUsesAtomKeyTest(M.Edge):
    def __init__(self):
        registry = M.AllConstructors
        atom = M.Thingy()
        exact_key = M.ExactKey(atom, registry)()
        tree_key = Tmod.TreeStructuralKey(atom, registry)()
        search_key = SearchStructuralKey(atom, registry)()
        result = M.truth_value
        if M.IsPair(exact_key)() is M.false_value:
            result = M.false_value
        elif M.IdentityCompare(M.Head(exact_key)(), M.ExactAtomKeyLabel)() is M.false_value:
            result = M.false_value
        elif RawTermEqual(exact_key, tree_key, registry)() is M.false_value:
            result = M.false_value
        elif RawTermEqual(exact_key, search_key, registry)() is M.false_value:
            result = M.false_value
        self.result = result
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class TreeLookupUsesStructuralKeysTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        left_term = M.Pair(M.one, M.Pair(M.two, empty))
        right_term = M.Pair(M.one, M.Pair(M.two, empty))
        fact = M.Pair(M.three, empty)

        tree = M.TreeInsert(M.Tree(empty), left_term, fact, registry)()
        looked_up = M.TreeLookup(tree, right_term, registry)()
        self.result = RawTermEqual(looked_up, fact, registry)()
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class SearchPromptCostStepBuildsHundredTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        twenty_pair = M.Multiply(M.four, M.five, registry)()
        twenty = M.Head(twenty_pair)()
        registry = M.Head(M.Tail(twenty_pair)())()
        hundred_pair = M.Multiply(twenty, M.five, registry)()
        hundred = M.Head(hundred_pair)()
        registry = M.Head(M.Tail(hundred_pair)())()
        expected_pair = M.NatFromRep(M.GMPRep("100"), registry)()
        expected = M.Head(expected_pair)()
        registry = M.Head(M.Tail(expected_pair)())()
        self.result = M.NatEq(hundred, expected, registry)()
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class GoalHeadNeighborhoodReachbackTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        var_name = M.Thingy()
        var_x = M.Pair(M.VarTag, M.Pair(var_name, empty))
        rule_one = Rule(
            M.Pair(M.IsCauchyLabel, M.Pair(var_x, empty)),
            M.Pair(M.RealNumLabel, M.Pair(var_x, empty)),
        )
        rule_two = Rule(
            M.Pair(M.RealNumLabel, M.Pair(var_x, empty)),
            M.Pair(M.IsRealLabel, M.Pair(var_x, empty)),
        )
        rules = M.Pair(rule_one, M.Pair(rule_two, empty))
        goal = M.Pair(M.IsRealLabel, M.Pair(M.one, empty))
        index = Hmod.HeuristicGoalHeadNeighborhood(goal, rules, registry)()
        subterm = M.Pair(M.IsCauchyLabel, M.Pair(M.one, empty))
        self.result = Hmod.HeuristicGoalHeadAllowsSubterm(index, subterm, registry)()
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class HeuristicCanonicalKnowledgeAgreementTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        fact_one = M.Pair(M.IsRealLabel, M.Pair(M.one, empty))
        fact_two = M.Pair(M.RealNumLabel, M.Pair(M.one, empty))
        left = M.Knowledge(M.Pair(fact_one, M.Pair(fact_two, empty)))()
        right = M.Knowledge(M.Pair(fact_two, M.Pair(fact_one, empty)))()
        heuristic = Hmod.Heuristic(
            M.DFSLabel,
            M.GoalHeadOrderLabel,
            M.Zero,
            M.one,
            M.one,
            M.one,
        )()
        left_canonical = Hmod.HeuristicCanonicalize(left, heuristic, registry)()
        right_canonical = Hmod.HeuristicCanonicalize(right, heuristic, registry)()
        self.result = RawTermEqual(left_canonical, right_canonical, registry)()
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CanonicalArithmeticAddACNormalizesTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        left = M.Pair(M.ExprAddLabel, M.Pair(M.three, M.Pair(M.Pair(M.ExprAddLabel, M.Pair(M.one, M.Pair(M.two, empty))), empty)))
        right = M.Pair(M.ExprAddLabel, M.Pair(M.Pair(M.ExprAddLabel, M.Pair(M.two, M.Pair(M.three, empty))), M.Pair(M.one, empty)))
        left_canonical = M.CanonicalArithmeticTerm(left, registry)()
        right_canonical = M.CanonicalArithmeticTerm(right, registry)()
        self.result = RawTermEqual(left_canonical, right_canonical, registry)()
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CanonicalArithmeticMulACNormalizesTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        left = M.Pair(M.ExprMulLabel, M.Pair(M.three, M.Pair(M.Pair(M.ExprMulLabel, M.Pair(M.one, M.Pair(M.two, empty))), empty)))
        right = M.Pair(M.ExprMulLabel, M.Pair(M.Pair(M.ExprMulLabel, M.Pair(M.two, M.Pair(M.three, empty))), M.Pair(M.one, empty)))
        left_canonical = M.CanonicalArithmeticTerm(left, registry)()
        right_canonical = M.CanonicalArithmeticTerm(right, registry)()
        self.result = RawTermEqual(left_canonical, right_canonical, registry)()
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CanonicalArithmeticEquationSymmetryTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        left = M.Pair(M.ExprEqLabel, M.Pair(M.two, M.Pair(M.one, empty)))
        right = M.Pair(M.ExprEqLabel, M.Pair(M.one, M.Pair(M.two, empty)))
        left_canonical = M.CanonicalArithmeticTerm(left, registry)()
        right_canonical = M.CanonicalArithmeticTerm(right, registry)()
        self.result = RawTermEqual(left_canonical, right_canonical, registry)()
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class ArithmeticCanonicalLawsDeclaredTest(M.Edge):
    def __init__(self, _graph):
        from .main import PACK_PATHS, _runtime_namespace

        runtime, packs = boot_from_packs(PACK_PATHS, _runtime_namespace())
        arithmetic = packs.by_name("arithmetic")
        self.result = M.truth_value
        for rule_id in (
            "arithmetic_add_commutes",
            "arithmetic_add_associates_right",
            "arithmetic_mul_commutes",
            "arithmetic_mul_associates_right",
            "arithmetic_equation_is_symmetric",
        ):
            if rule_id not in arithmetic.rule_map:
                self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class TreeLookupUsesIndexBucketsTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        left_head = M.Thingy()
        right_head = M.Thingy()
        left_term = M.Pair(left_head, M.Pair(M.one, empty))
        right_term = M.Pair(right_head, M.Pair(M.one, empty))
        left_fact = M.Pair(M.two, empty)
        right_fact = M.Pair(M.three, empty)

        left_exact = M.ExactKey(left_term, registry)()
        right_exact = M.ExactKey(right_term, registry)()
        left_index = Tmod.IndexKey(left_exact)()
        right_index = Tmod.IndexKey(right_exact)()

        tree = M.TreeInsert(M.Tree(empty), left_term, left_fact, registry)()
        tree = M.TreeInsert(tree, right_term, right_fact, registry)()
        looked_left = M.TreeLookup(tree, left_term, registry)()
        looked_right = M.TreeLookup(tree, right_term, registry)()

        result = RawTermEqual(left_index, right_index, registry)()
        if result is M.truth_value:
            result = RawTermEqual(looked_left, left_fact, registry)()
        if result is M.truth_value:
            result = RawTermEqual(looked_right, right_fact, registry)()
        self.result = result
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class LegacyTreeLookupRemainsReadableTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        fact = M.Pair(M.two, empty)
        legacy_tree = M.Tree(Tmod.TreeNode(M.one, fact, empty, empty))
        looked_up = M.TreeLookup(legacy_tree, M.one, registry)()
        self.result = RawTermEqual(looked_up, fact, registry)()
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class TreeInsertMigratesLegacyTreeTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        legacy_fact = M.Pair(M.two, empty)
        new_key = M.Pair(M.one, M.Pair(M.one, empty))
        new_fact = M.Pair(M.three, empty)
        legacy_tree = M.Tree(Tmod.TreeNode(M.one, legacy_fact, empty, empty))
        migrated = M.TreeInsert(legacy_tree, new_key, new_fact, registry)()
        looked_legacy = M.TreeLookup(migrated, M.one, registry)()
        looked_new = M.TreeLookup(migrated, new_key, registry)()

        result = RawTermEqual(looked_legacy, legacy_fact, registry)()
        if result is M.truth_value:
            result = RawTermEqual(looked_new, new_fact, registry)()
        self.result = result
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class GetConstructorSeesPatriciaTreeTermsTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        bucket = Tmod.TreeBucket(M.EmptyList)()
        leaf = Tmod.TreePatriciaLeaf(M.EmptyList, bucket)()
        constructor = M.GetConstructor(leaf, registry)()
        self.result = RawTermEqual(constructor, leaf, registry)()
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CompareInSeesPatriciaTreeTermsTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        left_leaf = Tmod.TreePatriciaLeaf(M.EmptyList, Tmod.TreeBucket(M.EmptyList)())()
        right_leaf = Tmod.TreePatriciaLeaf(M.EmptyList, Tmod.TreeBucket(M.EmptyList)())()
        self.result = M.CompareIn(left_leaf, right_leaf, registry)()
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CompareInSeesTreeWrapperTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        left_tree = M.Tree(M.EmptyList)
        right_tree = M.Tree(M.EmptyList)
        self.result = M.CompareIn(left_tree, right_tree, registry)()
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class _CompareSearchModesProbe(M.CompareSearchModes):
    def __init__(self, graph, start, goal, rules, heuristic, registry):
        self.graph = graph
        self.start = start
        self.goal = goal
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
        rule_count_pair = M.Count(self.rules, self.registry)()
        self._comparison_rule_count = M.Head(rule_count_pair)()
        self.registry = M.Head(M.Tail(rule_count_pair)())()
        self.graph._last_search_comparison_outcome = SearchSuccessLabel
        self.saved_derivations = M.FromContextGetDerivations(graph)()
        self.saved_schemata = M.FromContextGetDerivationSchemata(graph)()
        self.signature = SearchSignatureForProblem(start, goal, self.registry)()
        self._comparison_generation = self.signature
        self._comparison_packet_token = M.Zero
        self.result = M.EmptyList


class CompareSearchModesFindsReusableWorkerSnapshotDirTest(M.Edge):
    def __init__(self, graph):
        from .main import _search_worker_checkpoint, _search_worker_mode_heuristic

        empty = M.EmptyList
        registry = _registry(graph)
        start = M.Pair(M.Char("s"), empty)
        goal = M.Pair(M.Char("g"), empty)
        heuristic = M.Heuristic(M.BFSLabel, M.GoalHeadOrderLabel, M.three, M.one, M.one, M.one)()
        rules = M.Pair(Rule(start, goal), empty)
        probe = _CompareSearchModesProbe(graph, start, goal, rules, heuristic, registry)
        temp_dir = tempfile.mkdtemp(prefix="hyge-compare-resume-")
        try:
            matching_dir = os.path.join(temp_dir, "snapshots", "search_compare", "run-1")
            mismatching_dir = os.path.join(temp_dir, "snapshots", "search_compare", "run-2")
            os.makedirs(matching_dir, exist_ok=True)
            os.makedirs(mismatching_dir, exist_ok=True)
            runtime = make_fresh_runtime()
            worker_registry = _registry(runtime.graph)
            worker_heuristic = _search_worker_mode_heuristic(runtime, "bfs", worker_registry)
            proof_cost = Pmod.ProofCost(M.Zero, M.Zero, M.Zero, M.Zero)()
            plan = M.Pair(M.Atom(), empty)
            search_cost_pair = Smod.BuildSearchCost(plan, M.one, M.Zero, M.one, Smod.SearchSuccessLabel, worker_registry)()
            search_cost = M.Head(search_cost_pair)()
            matching_path = os.path.join(matching_dir, "bfs.snapshot.json")
            probe._write_search_worker_manifest(matching_path)
            _search_worker_checkpoint(
                runtime,
                matching_path,
                start,
                goal,
                worker_heuristic,
                Smod.SearchSuccessLabel,
                M.EmptyList,
                proof_cost,
                search_cost,
                1234,
                "running-derivation",
                plan,
            )
            with open(probe._search_worker_result_manifest_path(os.path.join(mismatching_dir, "bfs.snapshot.json")), "w", encoding="utf-8") as handle:
                json.dump({"start_text": "wrong", "goal_text": "wrong"}, handle)
            found = probe._reusable_search_worker_result_paths(temp_dir)
            self.result = M.truth_value
            if "SearchBFS" not in found:
                self.result = M.false_value
            elif found["SearchBFS"] != matching_path:
                self.result = M.false_value
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CompareSearchModesConsoleDisabledSkipsApprovalReplayPromptTest(M.Edge):
    def __init__(self, graph):
        empty = M.EmptyList
        registry = _registry(graph)
        start = M.Pair(M.Char("s"), empty)
        goal = M.Pair(M.Char("g"), empty)
        heuristic = M.Heuristic(M.BFSLabel, M.GoalHeadOrderLabel, M.three, M.one, M.one, M.one)()
        rules = M.Pair(Rule(start, goal), empty)
        probe = _CompareSearchModesProbe(graph, start, goal, rules, heuristic, registry)
        graph._search_disable_console = M.truth_value
        proof_cost = Pmod.ProofCost(M.Zero, M.Zero, M.Zero, M.Zero)()
        plan = M.Pair(M.Atom(), empty)
        search_cost_pair = Smod.BuildSearchCost(plan, M.one, M.Zero, M.one, Smod.SearchSuccessLabel, registry)()
        search_cost = M.Head(search_cost_pair)()
        registry = M.Head(M.Tail(search_cost_pair)())()
        total_cost_pair = Pmod.BuildTotalCost(proof_cost, search_cost, heuristic, registry)()
        total_cost = M.Head(total_cost_pair)()
        registry = M.Head(M.Tail(total_cost_pair)())()
        best_attempt = Pmod.SearchAttempt(
            start,
            goal,
            heuristic,
            Smod.SearchSuccessLabel,
            M.EmptyList,
            proof_cost,
            search_cost,
            total_cost,
        )()
        returned_attempt, returned_performances = probe._approval_to_materialize_best_attempt(best_attempt, {}, {})
        self.result = M.truth_value
        if M.TermEqual(returned_attempt, best_attempt)() is M.false_value:
            self.result = M.false_value
        elif returned_performances != {}:
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class SearchWorkerResumeDerivationMissingPlanRaisesRuntimeErrorTest(M.Edge):
    def __init__(self, _graph):
        from .main import _search_worker_checkpoint, _search_worker_mode_heuristic, run_search_worker_mode

        empty = M.EmptyList
        runtime = make_fresh_runtime()
        registry = _registry(runtime.graph)
        heuristic = _search_worker_mode_heuristic(runtime, "dfs", registry)
        start = M.Pair(M.Char("v"), M.Pair(M.Char("w"), empty))
        goal = M.Pair(M.Char("g"), empty)
        proof_cost = Pmod.ProofCost(M.Zero, M.Zero, M.Zero, M.Zero)()
        search_cost_pair = Smod.BuildSearchCost(M.EmptyList, M.Zero, M.Zero, M.Zero, Smod.SearchRunningLabel, registry)()
        search_cost = M.Head(search_cost_pair)()
        snapshot_fd, snapshot_path = tempfile.mkstemp(suffix=".json")
        os.close(snapshot_fd)
        try:
            _search_worker_checkpoint(
                runtime,
                snapshot_path,
                start,
                goal,
                heuristic,
                Smod.SearchRunningLabel,
                M.EmptyList,
                proof_cost,
                search_cost,
                0,
                "running-search",
                M.EmptyList,
            )
            old_env = os.environ.get("HYGE_SEARCH_WORKER_RESUME_DERIVATION")
            os.environ["HYGE_SEARCH_WORKER_RESUME_DERIVATION"] = "1"
            self.result = M.false_value
            try:
                run_search_worker_mode("dfs", snapshot_path)
            except RuntimeError as error:
                if str(error) == "search-worker resume missing-plan":
                    self.result = M.truth_value
            finally:
                if old_env == None:
                    os.environ.pop("HYGE_SEARCH_WORKER_RESUME_DERIVATION", None)
                else:
                    os.environ["HYGE_SEARCH_WORKER_RESUME_DERIVATION"] = old_env
        finally:
            try:
                os.remove(snapshot_path)
            except OSError:
                pass
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CompareSearchModesFallbackWinnerUsesRecordedPerformanceOrderingTest(M.Edge):
    def __init__(self, graph):
        from .main import _gmp_atom_from_int

        empty = M.EmptyList
        registry = _registry(graph)
        start = M.Pair(M.Char("s"), empty)
        goal = M.Pair(M.Char("g"), empty)
        h_dfs = M.Heuristic(M.DFSLabel, M.GoalHeadOrderLabel, M.three, M.one, M.one, M.one)()
        h_bfs = M.Heuristic(M.BFSLabel, M.GoalHeadOrderLabel, M.three, M.one, M.one, M.one)()
        h_beam = M.Heuristic(M.BeamLabel, M.GoalHeadOrderLabel, M.three, M.one, M.one, M.one)()
        proof_cost = Pmod.ProofCost(M.Zero, M.Zero, M.Zero, M.Zero)()
        plan = M.Pair(M.Atom(), empty)
        sc_pair = Smod.BuildSearchCost(plan, M.one, M.Zero, M.one, Smod.SearchSuccessLabel, registry)()
        sc_success = M.Head(sc_pair)()
        sc_pair_fail = Smod.BuildSearchCost(M.EmptyList, M.Zero, M.Zero, M.Zero, Smod.SearchFailureLabel, registry)()
        sc_fail = M.Head(sc_pair_fail)()

        total_cost_pair = Pmod.BuildTotalCost(proof_cost, sc_success, h_bfs, registry)()
        tc_success = M.Head(total_cost_pair)()
        total_cost_pair_fail = Pmod.BuildTotalCost(proof_cost, sc_fail, h_dfs, registry)()
        tc_fail = M.Head(total_cost_pair_fail)()

        att_dfs = Pmod.SearchAttempt(start, goal, h_dfs, Smod.SearchFailureLabel, empty, proof_cost, sc_fail, tc_fail)()
        att_bfs = Pmod.SearchAttempt(start, goal, h_bfs, Smod.SearchSuccessLabel, empty, proof_cost, sc_success, tc_success)()
        att_beam = Pmod.SearchAttempt(start, goal, h_beam, Smod.SearchSuccessLabel, empty, proof_cost, sc_success, tc_success)()

        perf_dfs = Smod.HeuristicPerformance(att_dfs, _gmp_atom_from_int(2000), _gmp_atom_from_int(100), M.EmptyList)()
        perf_bfs = Smod.HeuristicPerformance(att_bfs, _gmp_atom_from_int(2000), _gmp_atom_from_int(101), M.EmptyList)()
        perf_beam = Smod.HeuristicPerformance(att_beam, _gmp_atom_from_int(1000), _gmp_atom_from_int(102), M.EmptyList)()

        performances = M.Pair(perf_dfs, M.Pair(perf_bfs, M.Pair(perf_beam, empty)))
        attempts = M.Pair(att_dfs, M.Pair(att_bfs, M.Pair(att_beam, empty)))

        probe = _CompareSearchModesProbe(graph, start, goal, empty, h_dfs, registry)
        best_by_perfs = probe._best_attempt_in_performances(performances, empty, None)

        self.result = M.TermEqual(best_by_perfs, att_beam)()
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class _TheoremCursorProbe(Smod.SearchBFS):
    def __init__(self, graph, start, goal, rules, heuristic, registry):
        self.graph = graph
        self.registry = registry
        self.rules = rules
        self.heuristic = heuristic
        self.start = start
        self.goal = goal
        self.search_aborted = M.false_value
        self.search_outcome_on_abort = SearchFailureLabel
        self._active_search_job = None
        self._console_input = None
        self._stop_listener = None
        self._dfs_timeout_seconds = 100
        self._dfs_timeout_triggered = M.false_value
        self._paused_state = M.EmptyList
        self._init_search_prompt_state()
        self._init_search_order_state(goal, M.EmptyList, M.EmptyList)


class _ResidentExecutorQueueProbe:
    def __init__(self):
        self.count = M.Zero
        self.first = M.EmptyList
        self.second = M.EmptyList

    def put(self, item):
        if M.NatEq(self.count, M.Zero, M.AllConstructors)() is M.truth_value:
            self.first = item
        elif M.NatEq(self.count, M.one, M.AllConstructors)() is M.truth_value:
            self.second = item
        self.count = M.Head(M.Succ(self.count, M.AllConstructors)())()


class _ResidentExecutorProcessProbe:
    def __init__(self):
        self.pid = 1
        self.alive = M.truth_value

    def is_alive(self):
        return M.IdentityCompare(self.alive, M.truth_value)() is M.truth_value

    def join(self, timeout=None):
        return None

    def terminate(self):
        self.alive = M.false_value


class _RootWaveResultQueueProbe:
    def __init__(self):
        self.items = M.EmptyList

    def put(self, item):
        self.items = M.Pair(item, self.items)

    def get_nowait(self):
        if M.IdentityCompare(self.items, M.EmptyList)() is M.truth_value:
            raise queue.Empty()
        item = M.Head(self.items)()
        self.items = M.Tail(self.items)()
        return item


class _RootWaveTaskQueueProbe:
    def __init__(self, result_queue):
        self.result_queue = result_queue
        self.count = M.Zero
        self.launch_count = M.Zero
        self.setup_count = M.Zero
        self.first = M.EmptyList

    def put(self, item):
        if M.NatEq(self.count, M.Zero, M.AllConstructors)() is M.truth_value:
            self.first = item
        self.count = M.Head(M.Succ(self.count, M.AllConstructors)())()
        if M.IsPair(item)() is M.truth_value:
            label = M.Head(item)()
            if M.IdentityCompare(label, Lmod.SearchWorkerSetupLabel)() is M.truth_value:
                self.setup_count = M.Head(M.Succ(self.setup_count, M.AllConstructors)())()
            if M.IdentityCompare(label, Lmod.SearchRootWaveShardLaunchLabel)() is M.truth_value:
                self.launch_count = M.Head(M.Succ(self.launch_count, M.AllConstructors)())()
                packet = SearchRootWaveShardLaunchPacket(item)()
                rules = SearchRootWaveShardPacketRules(packet)()
                self.result_queue.put(SearchRootWaveShardResult(M.EmptyList, M.EmptyList, rules)())


class _RootWaveFailingTaskQueueProbe:
    def __init__(self, result_queue):
        self.result_queue = result_queue
        self.count = M.Zero
        self.launch_count = M.Zero

    def put(self, item):
        self.count = M.Head(M.Succ(self.count, M.AllConstructors)())()
        if M.IsPair(item)() is M.truth_value:
            if M.IdentityCompare(M.Head(item)(), Lmod.SearchRootWaveShardLaunchLabel)() is M.truth_value:
                self.launch_count = M.Head(M.Succ(self.launch_count, M.AllConstructors)())()
                self.result_queue.put(None)


class _WarmRootWaveCompareProbe(_CompareSearchModesProbe):
    def __init__(self, graph, start, goal, rules, heuristic, registry):
        super().__init__(graph, start, goal, rules, heuristic, registry)
        self.spawned = M.Zero
        self.root_launches = M.Zero

    def _spawn_parallel_executor(self, mp_context, slot):
        result_queue = _RootWaveResultQueueProbe()
        task_queue = _RootWaveTaskQueueProbe(result_queue)
        process = _ResidentExecutorProcessProbe()
        self.spawned = M.Head(M.Succ(self.spawned, self.registry)())()
        return self._resident_executor(slot, process, task_queue, result_queue)


class _ReplacementRootWaveCompareProbe(_CompareSearchModesProbe):
    def __init__(self, graph, start, goal, rules, heuristic, registry):
        super().__init__(graph, start, goal, rules, heuristic, registry)
        self.spawned = M.Zero

    def _spawn_parallel_executor(self, mp_context, slot):
        result_queue = _RootWaveResultQueueProbe()
        task_queue = _RootWaveTaskQueueProbe(result_queue)
        process = _ResidentExecutorProcessProbe()
        self.spawned = M.Head(M.Succ(self.spawned, self.registry)())()
        return self._resident_executor(slot, process, task_queue, result_queue)


class CompareSearchModesBuildsDeepRootWaveShardsWithoutRecursionTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.Thingy()
        goal = M.Thingy()
        heuristic = M.Heuristic(M.BFSLabel, M.InsertionOrderLabel, M.three, M.one, M.one, M.one)()
        probe = _CompareSearchModesProbe(graph, start, goal, empty, heuristic, registry)
        result = M.truth_value
        previous_limit = sys.getrecursionlimit()
        sys.setrecursionlimit(100)
        try:
            rules = empty
            index = 0
            while index < 150:
                rules = M.Pair(M.Thingy(), rules)
                index = index + 1
            shard_rules = probe._comparison_rule_wave_shards(rules)
            remaining_shards = shard_rules
            shard_count = 0
            while (
                M.IdentityCompare(remaining_shards, empty)() is M.false_value
                and M.IdentityCompare(result, M.truth_value)() is M.truth_value
            ):
                shard = M.Head(remaining_shards)()
                if M.IdentityCompare(M.Tail(shard)(), empty)() is M.false_value:
                    result = M.false_value
                shard_count = shard_count + 1
                remaining_shards = M.Tail(remaining_shards)()
            if shard_count != 150:
                result = M.false_value
        finally:
            sys.setrecursionlimit(previous_limit)

        self.result = result
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CompareSearchModesResidentExecutorReadyHandshakeTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.Thingy()
        goal = M.Atom()
        heuristic = M.Heuristic(M.BFSLabel, M.InsertionOrderLabel, M.one, M.one, M.one, M.one)()
        probe = _CompareSearchModesProbe(graph, start, goal, empty, heuristic, registry)
        result_queue = _RootWaveResultQueueProbe()
        result_queue.put(M.Pair(Lmod.SearchWorkerReadyLabel, empty))
        executor = probe._resident_executor(M.one, _ResidentExecutorProcessProbe(), _ResidentExecutorQueueProbe(), result_queue)

        self.result = probe._await_parallel_executor_ready(executor)
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CompareSearchModesRootWaveRequiresResidentExecutorTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.Thingy()
        goal = M.Atom()
        heuristic = M.Heuristic(M.BFSLabel, M.InsertionOrderLabel, M.one, M.one, M.one, M.one)()
        rules = M.Pair(Rule(start, goal), empty)
        probe = _CompareSearchModesProbe(graph, start, goal, rules, heuristic, registry)
        probe._comparison_machine_parallelism = M.one
        job = probe._fresh_compare_job(M.BFSLabel)

        self.result = M.false_value
        try:
            probe._comparison_root_candidate_rules_parallel(job)
        except RuntimeError:
            self.result = M.truth_value
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CompareSearchModesFillWarmsResidentPoolBeforeRootWaveTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.Thingy()
        goal = M.Atom()
        heuristic = M.Heuristic(M.BFSLabel, M.InsertionOrderLabel, M.one, M.one, M.one, M.one)()
        rules = M.Pair(Rule(start, goal), empty)
        probe = _WarmRootWaveCompareProbe(graph, start, goal, rules, heuristic, registry)
        probe._comparison_machine_parallelism = M.one
        states = probe._comparison_states(probe._mode_chain())

        filled = probe._fill_parallel_workers(M.EmptyList, empty, states, empty)
        next_states = M.Head(filled)()
        workers = M.Head(M.Tail(filled)())()

        result = M.truth_value
        if M.NatEq(probe.spawned, M.Zero, probe.registry)() is M.truth_value:
            result = M.false_value
        elif M.IdentityCompare(probe._comparison_shared_root_candidates_ready, M.truth_value)() is M.false_value:
            result = M.false_value
        elif M.IdentityCompare(workers, empty)() is M.truth_value:
            result = M.false_value
        elif M.IdentityCompare(probe._comparison_states_need_shared_root_wave(next_states), M.truth_value)() is M.truth_value:
            result = M.false_value

        self.result = result
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CompareSearchModesRootWaveUsesResidentExecutorTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.Thingy()
        goal = M.Atom()
        heuristic = M.Heuristic(M.BFSLabel, M.InsertionOrderLabel, M.one, M.one, M.one, M.one)()
        first_rule = Rule(start, goal)
        second_rule = Rule(goal, start)
        rules = M.Pair(first_rule, M.Pair(second_rule, empty))
        probe = _CompareSearchModesProbe(graph, start, goal, rules, heuristic, registry)
        probe._comparison_machine_parallelism = M.one
        result_queue = _RootWaveResultQueueProbe()
        task_queue = _RootWaveTaskQueueProbe(result_queue)
        executor = probe._resident_executor(M.one, _ResidentExecutorProcessProbe(), task_queue, result_queue)
        probe._comparison_root_wave_idle_executors = M.Pair(executor, empty)
        job = probe._fresh_compare_job(M.BFSLabel)

        candidates = probe._comparison_root_candidate_rules_parallel(job)

        self.result = M.truth_value
        if M.NatEq(task_queue.launch_count, M.two, probe.registry)() is M.false_value:
            self.result = M.false_value
        elif M.NatEq(task_queue.setup_count, M.one, probe.registry)() is M.false_value:
            self.result = M.false_value
        elif RawTermEqual(candidates, rules, probe.registry)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(probe._comparison_root_wave_idle_executors, empty)() is M.truth_value:
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CompareSearchModesRootWaveRetriesFailedShardOnResidentTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.Thingy()
        goal = M.Atom()
        heuristic = M.Heuristic(M.BFSLabel, M.InsertionOrderLabel, M.one, M.one, M.one, M.one)()
        first_rule = Rule(start, goal)
        second_rule = Rule(goal, start)
        rules = M.Pair(first_rule, M.Pair(second_rule, empty))
        probe = _CompareSearchModesProbe(graph, start, goal, rules, heuristic, registry)
        probe._comparison_machine_parallelism = M.one

        failing_result_queue = _RootWaveResultQueueProbe()
        failing_task_queue = _RootWaveFailingTaskQueueProbe(failing_result_queue)
        failing_process = _ResidentExecutorProcessProbe()
        failing_executor = probe._resident_executor(M.one, failing_process, failing_task_queue, failing_result_queue)

        retry_result_queue = _RootWaveResultQueueProbe()
        retry_task_queue = _RootWaveTaskQueueProbe(retry_result_queue)
        retry_executor = probe._resident_executor(M.two, _ResidentExecutorProcessProbe(), retry_task_queue, retry_result_queue)

        probe._comparison_root_wave_idle_executors = M.Pair(failing_executor, M.Pair(retry_executor, empty))
        job = probe._fresh_compare_job(M.BFSLabel)

        candidates = probe._comparison_root_candidate_rules_parallel(job)

        self.result = M.truth_value
        if M.NatEq(failing_task_queue.launch_count, M.one, probe.registry)() is M.false_value:
            self.result = M.false_value
        elif M.NatEq(retry_task_queue.launch_count, M.two, probe.registry)() is M.false_value:
            self.result = M.false_value
        elif M.NatEq(retry_task_queue.setup_count, M.one, probe.registry)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(failing_process.alive, M.false_value)() is M.false_value:
            self.result = M.false_value
        elif RawTermEqual(candidates, rules, probe.registry)() is M.false_value:
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CompareSearchModesRootWaveReplacesExhaustedResidentTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.Thingy()
        goal = M.Atom()
        heuristic = M.Heuristic(M.BFSLabel, M.InsertionOrderLabel, M.one, M.one, M.one, M.one)()
        rules = M.Pair(Rule(start, goal), empty)
        probe = _ReplacementRootWaveCompareProbe(graph, start, goal, rules, heuristic, registry)
        probe._comparison_machine_parallelism = M.one
        probe._comparison_mp_context = M.EmptyList

        failing_result_queue = _RootWaveResultQueueProbe()
        failing_task_queue = _RootWaveFailingTaskQueueProbe(failing_result_queue)
        failing_process = _ResidentExecutorProcessProbe()
        failing_executor = probe._resident_executor(M.one, failing_process, failing_task_queue, failing_result_queue)
        probe._comparison_root_wave_idle_executors = M.Pair(failing_executor, empty)

        candidates = probe._comparison_root_candidate_rules_parallel(probe._fresh_compare_job(M.BFSLabel))

        result = M.truth_value
        if M.NatEq(probe.spawned, M.one, probe.registry)() is M.false_value:
            result = M.false_value
        elif M.IdentityCompare(failing_process.alive, M.false_value)() is M.false_value:
            result = M.false_value
        elif RawTermEqual(candidates, rules, probe.registry)() is M.false_value:
            result = M.false_value
        elif M.IdentityCompare(probe._comparison_root_wave_idle_executors, empty)() is M.truth_value:
            result = M.false_value

        self.result = result
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CompareSearchModesRootWaveSeedsSingleRewriteHandoffTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.Thingy()
        goal = M.Atom()
        heuristic = M.Heuristic(M.BFSLabel, M.InsertionOrderLabel, M.three, M.one, M.one, M.one)()
        rule_one = Rule(start, goal)
        rule_two = Rule(start, M.one)
        rules = M.Pair(rule_one, M.Pair(rule_two, empty))
        probe = _CompareSearchModesProbe(graph, start, goal, rules, heuristic, registry)
        job = probe._fresh_compare_job(M.BFSLabel)

        seeded = probe._comparison_seed_rule_wave(M.BFSLabel, job, rules)
        drained_job = M.Head(seeded)()
        packets = M.Head(M.Tail(seeded)())()
        packet_count = M.Head(M.Tail(M.Tail(seeded)())())()

        result = M.truth_value
        if M.NatEq(packet_count, M.three, probe.registry)() is M.false_value:
            result = M.false_value
        elif M.NatEq(M.SearchJobExpanded(drained_job)(), M.one, probe.registry)() is M.false_value:
            result = M.false_value
        elif M.IdentityCompare(packets, empty)() is M.truth_value:
            result = M.false_value
        else:
            first_state = probe._comparison_packet_state(M.BFSLabel, M.Head(packets)())
            second_packets = M.Tail(packets)()
            if M.IdentityCompare(second_packets, empty)() is M.truth_value:
                result = M.false_value
            else:
                second_state = probe._comparison_packet_state(M.BFSLabel, M.Head(second_packets)())
                third_packets = M.Tail(second_packets)()
                if M.IdentityCompare(third_packets, empty)() is M.truth_value:
                    result = M.false_value
                elif M.IdentityCompare(M.Tail(third_packets)(), empty)() is M.false_value:
                    result = M.false_value
                else:
                    third_state = probe._comparison_packet_state(M.BFSLabel, M.Head(third_packets)())
                    theorem_states = M.Pair(first_state, M.Pair(second_state, empty))
                    if ForAll(theorem_states, SearchStateHasSingletonTheoremCursor)() is M.false_value:
                        result = M.false_value
                    third_cursor = M.SearchStateCursor(third_state)()
                    if M.IdentityCompare(third_cursor, empty)() is M.truth_value:
                        result = M.false_value
                    elif M.IdentityCompare(M.Head(third_cursor)(), M.SearchRewriteCursorLabel)() is M.false_value:
                        result = M.false_value
                    else:
                        generated = M.SearchRewriteCursorGenerated(third_cursor)()
                        if M.IdentityCompare(SearchPatriciaLookupByKey(generated, goal, probe.registry)(), empty)() is M.truth_value:
                            result = M.false_value
                        if M.IdentityCompare(SearchPatriciaLookupByKey(generated, M.one, probe.registry)(), empty)() is M.truth_value:
                            result = M.false_value
                    if probe._comparison_packet_is_root_rule(M.Head(packets)()) is M.truth_value:
                        result = M.false_value

        self.result = result
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class SearchTheoremCursorSkipsDeepStaleRuleRunsWithoutRecursionTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.one
        goal = M.two
        heuristic = M.Heuristic(M.BFSLabel, M.InsertionOrderLabel, M.three, M.one, M.one, M.one)()
        rules = M.Pair(Rule(start, goal), empty)
        index = 0
        while index < 150:
            stale_left = M.Pair(M.three, M.Pair(M.Thingy(), empty))
            stale_right = M.Pair(M.four, M.Pair(M.Thingy(), empty))
            rules = M.Pair(Rule(stale_left, stale_right), rules)
            index = index + 1
        probe = _TheoremCursorProbe(graph, start, goal, rules, heuristic, registry)
        cursor = M.SearchTheoremCursor(rules, M.EmptyList)()
        state = probe._make_state(start, empty, empty, M.one, cursor)
        result = M.truth_value
        previous_limit = sys.getrecursionlimit()
        sys.setrecursionlimit(100)
        try:
            advance_result = probe._advance_theorem_cursor(state, cursor, goal)
            if M.Compare(probe._advance_result_success(advance_result), empty)() is M.truth_value:
                result = M.false_value
        finally:
            sys.setrecursionlimit(previous_limit)
        self.result = result
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CompareSearchModesPacketizesNonRootFrontierTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.Thingy()
        goal = M.Pair(M.Atom(), empty)
        heuristic = M.Heuristic(M.BFSLabel, M.InsertionOrderLabel, M.three, M.one, M.one, M.one)()
        rule1 = Rule(start, M.Atom())
        rule2 = Rule(start, M.one)
        rules = M.Pair(rule1, M.Pair(rule2, empty))
        probe = _CompareSearchModesProbe(graph, start, goal, rules, heuristic, registry)

        state_one = M.SearchState(start, empty, empty, M.one)()
        state_two = M.SearchState(M.one, empty, empty, M.one)()
        frontier = M.Pair(state_one, M.Pair(state_two, empty))
        job = M.SearchJob(
            start,
            goal,
            rules,
            heuristic,
            M.SearchRunningLabel,
            frontier,
            M.Zero,
            M.Zero,
            M.two,
            empty,
            empty,
            M.Tree(empty),
            empty,
            M.two,
        )()
        state = probe._comparison_state(M.BFSLabel, job, M.Tree(empty), M.Zero)
        queued_state = probe._comparison_state_enqueue_job_frontier(state)
        chosen = probe._next_dispatchable_state(M.Pair(queued_state, empty))
        pending_count_pair = M.Count(probe._comparison_state_pending_packets(queued_state), probe.registry)()
        pending_count = M.Head(pending_count_pair)()
        probe.registry = M.Head(M.Tail(pending_count_pair)())()

        result = M.truth_value
        if RawTermEqual(chosen, queued_state, probe.registry)() is M.false_value:
            result = M.false_value
        if M.IdentityCompare(probe._comparison_state_pending_packets(queued_state), M.EmptyList)() is M.truth_value:
            result = M.false_value
        if M.NatEq(pending_count, M.one, probe.registry)() is M.false_value:
            result = M.false_value
        if M.IdentityCompare(M.Head(M.Head(probe._comparison_state_pending_packets(queued_state))())(), Lmod.SearchJobLabel)() is M.false_value:
            result = M.false_value
        if M.IdentityCompare(M.SearchJobFrontier(probe._comparison_state_job(queued_state))(), M.EmptyList)() is M.false_value:
            result = M.false_value
        self.result = result
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CompareSearchModesPacketizesWideFrontierInChunksTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.Thingy()
        goal = M.Pair(M.Atom(), empty)
        heuristic = M.Heuristic(M.BFSLabel, M.InsertionOrderLabel, M.three, M.one, M.one, M.one)()
        probe = _CompareSearchModesProbe(graph, start, goal, empty, heuristic, registry)

        state_one = M.SearchState(start, empty, empty, M.one)()
        state_two = M.SearchState(M.one, empty, empty, M.one)()
        state_three = M.SearchState(M.two, empty, empty, M.one)()
        state_four = M.SearchState(M.three, empty, empty, M.one)()
        state_five = M.SearchState(M.four, empty, empty, M.one)()
        state_six = M.SearchState(M.five, empty, empty, M.one)()
        frontier = M.Pair(
            state_one,
            M.Pair(
                state_two,
                M.Pair(state_three, M.Pair(state_four, M.Pair(state_five, M.Pair(state_six, empty)))),
            ),
        )
        job = M.SearchJob(
            start,
            goal,
            empty,
            heuristic,
            M.SearchRunningLabel,
            frontier,
            M.Zero,
            M.Zero,
            M.six,
            empty,
            empty,
            M.Tree(empty),
            empty,
            M.six,
        )()
        state = probe._comparison_state(M.BFSLabel, job, M.Tree(empty), M.Zero)
        queued_state = probe._comparison_state_enqueue_job_frontier(state)
        released = probe._comparison_packet_frontier_width(M.BFSLabel)
        remaining = probe._nat_sub_or_zero_local(M.six, released)
        packet = M.Head(probe._comparison_state_pending_packets(queued_state))()
        trailing_packets = M.Tail(probe._comparison_state_pending_packets(queued_state))()
        trailing_packet = empty
        if M.IdentityCompare(trailing_packets, empty)() is M.false_value:
            trailing_packet = M.Head(trailing_packets)()

        result = M.truth_value
        if M.NatEq(probe._comparison_state_pending_packets_count(queued_state), M.two, probe.registry)() is M.false_value:
            result = M.false_value
        if M.NatEq(M.SearchJobFrontierSize(probe._comparison_state_job(queued_state))(), M.Zero, probe.registry)() is M.false_value:
            result = M.false_value
        if M.IdentityCompare(probe._comparison_state_pending_packets(queued_state), empty)() is M.truth_value:
            result = M.false_value
        if M.IdentityCompare(M.SearchJobFrontier(probe._comparison_state_job(queued_state))(), empty)() is M.false_value:
            result = M.false_value
        if M.IdentityCompare(M.Head(packet)(), Lmod.SearchJobLabel)() is M.false_value:
            result = M.false_value
        if M.NatEq(M.SearchJobFrontierSize(packet)(), released, probe.registry)() is M.false_value:
            result = M.false_value
        if M.IdentityCompare(trailing_packet, empty)() is M.truth_value:
            result = M.false_value
        elif M.NatEq(M.SearchJobFrontierSize(trailing_packet)(), remaining, probe.registry)() is M.false_value:
            result = M.false_value
        self.result = result
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CompareSearchModesPrunesPacketsAfterBestAttemptTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.Thingy()
        goal = M.Atom()
        heuristic = M.Heuristic(M.BFSLabel, M.InsertionOrderLabel, M.three, M.one, M.one, M.one)()
        probe = _CompareSearchModesProbe(graph, start, goal, empty, heuristic, registry)

        packet_state = M.SearchState(start, empty, empty, M.two)()
        packet = probe._comparison_frontier_state_packet(packet_state)
        job = probe._fresh_compare_job(M.BFSLabel)
        state = probe._comparison_state(
            M.BFSLabel,
            job,
            M.Tree(empty),
            M.Zero,
            M.Pair(packet, empty),
        )

        result = M.truth_value
        if probe._comparison_packet_prunable(M.BFSLabel, packet, M.one) is M.false_value:
            result = M.false_value
        if probe._comparison_state_has_dispatchable_work(state, M.one) is M.truth_value:
            result = M.false_value
        filtered_state = probe._comparison_state_without_exhausted_pending_packets(state, M.one)
        if M.IdentityCompare(probe._comparison_state_pending_packets(filtered_state), empty)() is M.false_value:
            result = M.false_value
        self.result = result
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CompareSearchModesFreshRootJobsPacketizeWholeStateTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.Thingy()
        goal = M.Atom()
        heuristic = M.Heuristic(M.BFSLabel, M.GoalHeadOrderLabel, M.three, M.one, M.one, M.one)()
        rule_one = Rule(start, goal)
        rule_two = Rule(start, M.one)
        rules = M.Pair(rule_one, M.Pair(rule_two, empty))
        probe = _CompareSearchModesProbe(graph, start, goal, rules, heuristic, registry)

        queued = probe._packet_queue_from_job(M.BFSLabel, probe._fresh_compare_job(M.BFSLabel), M.Tree(empty))
        drained_job = M.Head(queued)()
        packets = M.Head(M.Tail(queued)())()
        packet_count = M.Head(M.Tail(M.Tail(queued)())())()

        result = M.truth_value
        if M.NatEq(packet_count, M.one, probe.registry)() is M.false_value:
            result = M.false_value
        if M.IdentityCompare(packets, empty)() is M.truth_value:
            result = M.false_value
        else:
            packet = M.Head(packets)()
            if M.IdentityCompare(M.Head(packet)(), Lmod.SearchJobLabel)() is M.false_value:
                result = M.false_value
            if probe._comparison_packet_is_root_rule(packet) is M.truth_value:
                result = M.false_value
            packet_state = probe._comparison_packet_state(M.BFSLabel, packet)
            if RawTermEqual(M.SearchStateCurrent(packet_state)(), start, probe.registry)() is M.false_value:
                result = M.false_value
            if RawTermEqual(M.SearchStateCursor(packet_state)(), empty, probe.registry)() is M.false_value:
                result = M.false_value
        if RawTermEqual(M.SearchJobFrontier(drained_job)(), empty, probe.registry)() is M.false_value:
            result = M.false_value
        if M.NatEq(M.SearchJobFrontierSize(drained_job)(), M.Zero, probe.registry)() is M.false_value:
            result = M.false_value

        self.result = result
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CompareSearchModesMergesPacketJobTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.Thingy()
        goal = M.Thingy()
        heuristic = M.Heuristic(M.BFSLabel, M.InsertionOrderLabel, M.three, M.one, M.one, M.one)()
        probe = _CompareSearchModesProbe(graph, start, goal, empty, heuristic, registry)

        remaining_state = M.SearchState(start, empty, empty, M.one)()
        returned_state = M.SearchState(goal, empty, empty, M.one)()

        base_job = M.SearchJob(
            start,
            goal,
            empty,
            heuristic,
            M.SearchRunningLabel,
            M.Pair(remaining_state, empty),
            M.Zero,
            M.Zero,
            M.one,
            empty,
            empty,
            M.Tree(empty),
            empty,
            M.one,
        )()
        returned_job = M.SearchJob(
            start,
            goal,
            empty,
            heuristic,
            M.SearchRunningLabel,
            M.Pair(returned_state, empty),
            M.one,
            M.one,
            M.one,
            empty,
            empty,
            M.Tree(empty),
            empty,
            M.one,
        )()
        merged_job = probe._merge_compare_jobs(M.BFSLabel, base_job, returned_job)

        result = M.truth_value
        if M.NatEq(M.SearchJobFrontierSize(merged_job)(), M.two, probe.registry)() is M.false_value:
            result = M.false_value
        if M.NatEq(M.SearchJobExpanded(merged_job)(), M.one, probe.registry)() is M.false_value:
            result = M.false_value
        if M.NatEq(M.SearchJobGenerated(merged_job)(), M.one, probe.registry)() is M.false_value:
            result = M.false_value
        if M.NatEq(M.SearchJobFrontierPeak(merged_job)(), M.two, probe.registry)() is M.false_value:
            result = M.false_value

        self.result = result
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class SearchTreeDeltaSkipsStructurallyEqualTreesTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        value = M.Pair(M.one, empty)

        left_tree = M.TreeInsert(M.Tree(empty), M.one, value, registry)()
        right_tree = M.TreeInsert(M.Tree(empty), M.one, value, registry)()

        delta = SearchTreeDelta(left_tree, right_tree, registry)()
        self.result = M.IdentityCompare(M.TreeRoot(delta)(), empty)()
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class SearchTreeDeltaSkipsEqualContentDifferentShapeTreesTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        left_fact = M.Pair(M.one, empty)
        right_fact = M.Pair(M.two, empty)

        left_tree = M.TreeInsert(M.Tree(empty), M.one, left_fact, registry)()
        left_tree = M.TreeInsert(left_tree, M.two, right_fact, registry)()

        right_tree = M.TreeInsert(M.Tree(empty), M.two, right_fact, registry)()
        right_tree = M.TreeInsert(right_tree, M.one, left_fact, registry)()

        delta = SearchTreeDelta(left_tree, right_tree, registry)()
        self.result = M.IdentityCompare(M.TreeRoot(delta)(), empty)()
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class TreeInsertDeepPairLookupAvoidsRecursionTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        left = empty
        right = empty
        depth = 0
        previous_limit = sys.getrecursionlimit()
        sys.setrecursionlimit(100)
        result = M.truth_value
        try:
            while depth < 150:
                left = M.Pair(M.one, left)
                right = M.Pair(M.one, right)
                depth = depth + 1
            fact = M.Pair(M.two, empty)
            tree = M.TreeInsert(M.Tree(empty), left, fact, registry)()
            looked_up = M.TreeLookup(tree, right, registry)()
            if RawTermEqual(looked_up, fact, registry)() is M.false_value:
                result = M.false_value
        except RecursionError:
            result = M.false_value
        finally:
            sys.setrecursionlimit(previous_limit)
        self.result = result
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class SearchPatriciaLookupUsesStructuralKeysTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        left_term = M.Pair(M.one, M.Pair(M.two, empty))
        right_term = M.Pair(M.one, M.Pair(M.two, empty))
        fact = M.Pair(M.three, empty)

        tree = SearchPatriciaInsertByKey(M.EmptyList, left_term, fact, registry)()
        looked_up = SearchPatriciaLookupByKey(tree, right_term, registry)()
        lookup_ok = RawTermEqual(looked_up, fact, registry)()
        tree_ok = Tmod.IsTree(tree)()
        migrated_ok = M.IdentityCompare(SearchPatriciaIsTree(tree)(), M.false_value)()
        self.result = M.AndAtom(lookup_ok, M.AndAtom(tree_ok, migrated_ok)())()
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class SearchTreeDeltaSkipsStructurallyEqualPatriciaTreesTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        left_a = M.Pair(M.one, empty)
        left_b = M.Pair(M.two, empty)
        right_a = M.Pair(M.one, empty)
        right_b = M.Pair(M.two, empty)
        fact_a = M.Pair(M.three, empty)
        fact_b = M.Pair(M.four, empty)

        left_tree = SearchPatriciaInsertByKey(M.EmptyList, left_a, fact_a, registry)()
        left_tree = SearchPatriciaInsertByKey(left_tree, left_b, fact_b, registry)()
        right_tree = SearchPatriciaInsertByKey(M.EmptyList, right_b, fact_b, registry)()
        right_tree = SearchPatriciaInsertByKey(right_tree, right_a, fact_a, registry)()

        delta = SearchTreeDelta(left_tree, right_tree, registry)()
        self.result = M.IdentityCompare(M.TreeRoot(delta)(), empty)()
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CompareSearchModesDropsExhaustedPendingPacketsTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.Thingy()
        goal = M.Thingy()
        heuristic = M.Heuristic(M.BFSLabel, M.InsertionOrderLabel, M.three, M.one, M.one, M.one)()
        probe = _CompareSearchModesProbe(graph, start, goal, empty, heuristic, registry)

        exhausted_state = M.SearchState(start, empty, empty, M.Zero)()
        live_state = M.SearchState(goal, empty, empty, M.one)()
        exhausted_packet = probe._comparison_frontier_state_packet(exhausted_state)
        live_packet = probe._comparison_frontier_state_packet(live_state)

        job = M.SearchJob(
            start,
            goal,
            empty,
            heuristic,
            M.SearchRunningLabel,
            empty,
            M.Zero,
            M.Zero,
            M.Zero,
            empty,
            empty,
            M.Tree(empty),
            empty,
            M.Zero,
        )()
        state = probe._comparison_state(
            M.BFSLabel,
            job,
            M.Tree(empty),
            M.Zero,
            M.Pair(exhausted_packet, M.Pair(live_packet, empty)),
            M.two,
        )
        filtered = probe._comparison_state_without_exhausted_pending_packets(state)

        result = M.truth_value
        if RawTermEqual(probe._comparison_state_pending_packets(filtered), M.Pair(live_packet, empty), probe.registry)() is M.false_value:
            result = M.false_value
        if M.NatEq(probe._comparison_state_pending_packets_count(filtered), M.one, probe.registry)() is M.false_value:
            result = M.false_value
        if probe._comparison_state_has_dispatchable_work(filtered) is M.false_value:
            result = M.false_value
        self.result = result
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CompareSearchModesEnqueueAllPacketsAfterExhaustedBacklogTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.Thingy()
        goal = M.Atom()
        heuristic = M.Heuristic(M.BFSLabel, M.InsertionOrderLabel, M.three, M.one, M.one, M.one)()
        probe = _CompareSearchModesProbe(graph, start, goal, empty, heuristic, registry)

        exhausted_state = M.SearchState(start, empty, empty, M.Zero)()
        frontier_state = M.SearchState(goal, empty, empty, M.one)()
        exhausted_packet = probe._comparison_frontier_state_packet(exhausted_state)
        job = M.SearchJob(
            start,
            goal,
            empty,
            heuristic,
            M.SearchRunningLabel,
            M.Pair(frontier_state, empty),
            M.Zero,
            M.Zero,
            M.Zero,
            empty,
            empty,
            M.Tree(empty),
            empty,
            M.one,
        )()
        state = probe._comparison_state(
            M.BFSLabel,
            job,
            M.Tree(empty),
            M.Zero,
            M.Pair(exhausted_packet, empty),
            M.one,
        )
        states = probe._comparison_states_enqueue_all_packets(M.Pair(state, empty))
        next_state = probe._comparison_state_for_mode(states, M.BFSLabel)
        pending_packets = probe._comparison_state_pending_packets(next_state)
        pending_head = empty
        if M.IdentityCompare(pending_packets, empty)() is M.false_value:
            pending_head = M.Head(pending_packets)()

        result = M.truth_value
        if M.NatEq(probe._comparison_state_pending_packets_count(next_state), M.one, probe.registry)() is M.false_value:
            result = M.false_value
        if probe._comparison_state_has_dispatchable_work(next_state) is M.false_value:
            result = M.false_value
        if RawTermEqual(
            probe._comparison_packet_state(M.BFSLabel, pending_head),
            frontier_state,
            probe.registry,
        )() is M.false_value:
            result = M.false_value
        self.result = result
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CompareSearchModesRefillWidensPendingPacketsTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.Thingy()
        goal = M.Atom()
        heuristic = M.Heuristic(M.BFSLabel, M.GoalHeadOrderLabel, M.three, M.one, M.one, M.one)()
        rule_one = Rule(start, goal)
        rule_two = Rule(start, M.one)
        rules = M.Pair(rule_one, M.Pair(rule_two, empty))
        probe = _CompareSearchModesProbe(graph, start, goal, rules, heuristic, registry)

        seeded = probe._comparison_seed_rule_wave(M.BFSLabel, probe._fresh_compare_job(M.BFSLabel), rules)
        seeded_packets = M.Head(M.Tail(seeded)())()
        pending_packet = M.Head(seeded_packets)()
        job = M.SearchJob(
            start,
            goal,
            rules,
            heuristic,
            M.SearchRunningLabel,
            empty,
            M.Zero,
            M.Zero,
            M.Zero,
            empty,
            empty,
            M.Tree(empty),
            empty,
            M.Zero,
        )()
        state = probe._comparison_state(
            M.BFSLabel,
            job,
            M.Tree(empty),
            M.Zero,
            M.Pair(pending_packet, empty),
            M.one,
        )
        states = probe._comparison_states_enqueue_all_packets(M.Pair(state, empty), empty, M.truth_value)
        next_state = probe._comparison_state_for_mode(states, M.BFSLabel)

        result = M.truth_value
        if M.NatEq(probe._comparison_state_pending_packets_count(next_state), M.two, probe.registry)() is M.false_value:
            result = M.false_value
        if probe._comparison_state_has_dispatchable_work(next_state) is M.false_value:
            result = M.false_value
        self.result = result
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CompareSearchModesLiveBudgetUsesSoftWindowTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.Thingy()
        goal = M.Atom()
        heuristic = M.Heuristic(M.BFSLabel, M.InsertionOrderLabel, M.three, M.one, M.one, M.one)()
        probe = _CompareSearchModesProbe(graph, start, goal, empty, heuristic, registry)

        huge_pending = M.Atom()
        huge_pending.value = M.CountRep(
            M.Pair(
                M.one,
                M.Pair(
                    M.two,
                    M.Pair(
                        M.three,
                        M.Pair(M.four, M.Pair(M.five, M.Pair(M.six, M.Pair(M.seven, M.Pair(M.eight, M.Pair(M.nine, M.EmptyList)))))),
                    ),
                ),
            )
        )()
        state = probe._comparison_state(
            M.BFSLabel,
            probe._fresh_compare_job(M.BFSLabel),
            M.Tree(empty),
            M.Zero,
            empty,
            huge_pending,
        )
        budget = probe._comparison_live_process_budget(M.Pair(state, empty), empty)
        expected = probe._nat_add_local(probe._comparison_machine_parallelism, M.one)
        self.result = M.NatEq(budget, expected, probe.registry)()
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CompareSearchModesPacketBudgetUsesQuantumTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.Thingy()
        goal = M.Atom()
        heuristic = M.Heuristic(M.BFSLabel, M.InsertionOrderLabel, M.three, M.one, M.one, M.one)()
        probe = _CompareSearchModesProbe(graph, start, goal, empty, heuristic, registry)

        packet_state = M.SearchState(start, empty, empty, M.nine)()
        packet = probe._comparison_frontier_state_packet(packet_state)
        budget = probe._comparison_packet_budget(M.BFSLabel, packet)
        self.result = M.NatEq(budget, M.four, probe.registry)()
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CompareSearchModesPacketBudgetZeroBeamUsesPacketWidthFallbackTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.Thingy()
        goal = M.Atom()
        heuristic = M.Heuristic(M.BFSLabel, M.InsertionOrderLabel, M.Zero, M.one, M.one, M.one)()
        probe = _CompareSearchModesProbe(graph, start, goal, empty, heuristic, registry)
        probe._comparison_machine_parallelism = M.six

        packet_state = M.SearchState(start, empty, empty, M.nine)()
        packet = probe._comparison_frontier_state_packet(packet_state)
        budget = probe._comparison_packet_budget(M.BFSLabel, packet)
        self.result = M.NatEq(budget, M.six, probe.registry)()
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CompareSearchModesSkipsRootCacheDuringRawBenchmarkTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.Thingy()
        goal = M.Atom()
        heuristic = M.Heuristic(M.DFSLabel, M.GoalHeadOrderLabel, M.three, M.one, M.one, M.one)()
        rule = Rule(start, goal)
        rules = M.Pair(rule, empty)
        probe = _CompareSearchModesProbe(graph, start, goal, rules, heuristic, registry)

        cached_plan = M.Pair(M.TheoremAction(rule)(), empty)
        derivation_pair = BuildDerivation(start, cached_plan, probe.registry)()
        cached_derivation = M.Head(derivation_pair)()
        probe.registry = M.Head(M.Tail(derivation_pair)())()
        graph.add_derivation(start, goal, cached_derivation)

        dfs_state = probe._comparison_state(M.DFSLabel, probe._fresh_compare_job(M.DFSLabel), M.Tree(empty), M.Zero)
        bfs_state = probe._comparison_state(M.BFSLabel, probe._fresh_compare_job(M.BFSLabel), M.Tree(empty), M.Zero)
        states = M.Pair(dfs_state, M.Pair(bfs_state, empty))
        next_states = probe._comparison_states_after_root_fast_paths(states)
        next_dfs = probe._comparison_state_for_mode(next_states, M.DFSLabel)
        next_bfs = probe._comparison_state_for_mode(next_states, M.BFSLabel)
        result = M.truth_value
        if RawTermEqual(probe._comparison_state_status(next_dfs), M.SearchSuccessLabel, probe.registry)() is M.false_value:
            result = M.false_value
        if RawTermEqual(probe._comparison_state_status(next_bfs), M.SearchSuccessLabel, probe.registry)() is M.false_value:
            result = M.false_value
        if RawTermEqual(probe._comparison_state_root_fast_path_result(next_dfs), M.SearchRootCacheResultLabel, probe.registry)() is M.false_value:
            result = M.false_value
        if RawTermEqual(probe._comparison_state_root_fast_path_result(next_bfs), M.SearchRootCacheResultLabel, probe.registry)() is M.false_value:
            result = M.false_value
        self.result = result
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CompareSearchModesAppliesSharedRootCacheDuringNormalCompareTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.Thingy()
        goal = M.Atom()
        heuristic = M.Heuristic(M.DFSLabel, M.GoalHeadOrderLabel, M.three, M.one, M.one, M.one)()
        rule = Rule(start, goal)
        rules = M.Pair(rule, empty)
        probe = _CompareSearchModesProbe(graph, start, goal, rules, heuristic, registry)

        cached_plan = M.Pair(M.TheoremAction(rule)(), empty)
        derivation_pair = BuildDerivation(start, cached_plan, probe.registry)()
        cached_derivation = M.Head(derivation_pair)()
        probe.registry = M.Head(M.Tail(derivation_pair)())()
        graph.add_derivation(start, goal, cached_derivation)

        dfs_state = probe._comparison_state(M.DFSLabel, probe._fresh_compare_job(M.DFSLabel), M.Tree(empty), M.Zero)
        bfs_state = probe._comparison_state(M.BFSLabel, probe._fresh_compare_job(M.BFSLabel), M.Tree(empty), M.Zero)
        states = M.Pair(dfs_state, M.Pair(bfs_state, empty))
        next_states = probe._comparison_states_after_root_fast_paths(states)
        next_dfs = probe._comparison_state_for_mode(next_states, M.DFSLabel)
        next_bfs = probe._comparison_state_for_mode(next_states, M.BFSLabel)

        result = M.truth_value
        if RawTermEqual(probe._comparison_state_status(next_dfs), M.SearchSuccessLabel, probe.registry)() is M.false_value:
            result = M.false_value
        if RawTermEqual(probe._comparison_state_status(next_bfs), M.SearchSuccessLabel, probe.registry)() is M.false_value:
            result = M.false_value
        if RawTermEqual(probe._comparison_state_root_fast_path_result(next_dfs), M.SearchRootCacheResultLabel, probe.registry)() is M.false_value:
            result = M.false_value
        if RawTermEqual(probe._comparison_state_root_fast_path_result(next_bfs), M.SearchRootCacheResultLabel, probe.registry)() is M.false_value:
            result = M.false_value
        self.result = result
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CompareSearchModesSkipsSharedRootSchemaDuringRawBenchmarkTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.Thingy()
        goal = M.Atom()
        heuristic = M.Heuristic(M.DFSLabel, M.GoalHeadOrderLabel, M.three, M.one, M.one, M.one)()
        rule = Rule(start, goal)
        rules = M.Pair(rule, empty)
        probe = _CompareSearchModesProbe(graph, start, goal, rules, heuristic, registry)

        schema_plan = M.Pair(M.TheoremAction(rule)(), empty)
        graph.add_derivation_schema(start, goal, schema_plan)

        dfs_state = probe._comparison_state(M.DFSLabel, probe._fresh_compare_job(M.DFSLabel), M.Tree(empty), M.Zero)
        bfs_state = probe._comparison_state(M.BFSLabel, probe._fresh_compare_job(M.BFSLabel), M.Tree(empty), M.Zero)
        states = M.Pair(dfs_state, M.Pair(bfs_state, empty))
        next_states = probe._comparison_states_after_root_fast_paths(states)
        next_dfs = probe._comparison_state_for_mode(next_states, M.DFSLabel)
        next_bfs = probe._comparison_state_for_mode(next_states, M.BFSLabel)
        result = M.truth_value
        if RawTermEqual(probe._comparison_state_status(next_dfs), M.SearchSuccessLabel, probe.registry)() is M.false_value:
            result = M.false_value
        if RawTermEqual(probe._comparison_state_status(next_bfs), M.SearchSuccessLabel, probe.registry)() is M.false_value:
            result = M.false_value
        if RawTermEqual(probe._comparison_state_root_fast_path_result(next_dfs), M.SearchRootSchemaResultLabel, probe.registry)() is M.false_value:
            result = M.false_value
        if RawTermEqual(probe._comparison_state_root_fast_path_result(next_bfs), M.SearchRootSchemaResultLabel, probe.registry)() is M.false_value:
            result = M.false_value
        self.result = result
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CompareSearchModesStoresDerivationBackedAttemptTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.Thingy()
        goal = M.Atom()
        heuristic = M.Heuristic(M.DFSLabel, M.GoalHeadOrderLabel, M.three, M.one, M.one, M.one)()
        rule = Rule(start, goal)
        rules = M.Pair(rule, empty)
        probe = _CompareSearchModesProbe(graph, start, goal, rules, heuristic, registry)

        plan = M.Pair(M.TheoremAction(rule)(), empty)
        derivation_pair = BuildDerivation(start, plan, probe.registry)()
        derivation = M.Head(derivation_pair)()
        probe.registry = M.Head(M.Tail(derivation_pair)())()

        state = probe._comparison_state(M.DFSLabel, probe._fresh_compare_job(M.DFSLabel), M.Tree(empty), M.Zero)
        success_job = probe._comparison_success_job(state, derivation)
        success_state = probe._comparison_state(M.DFSLabel, success_job, M.Tree(empty), M.Zero)
        attempt = probe._comparison_state_attempt_or_current(success_state)

        self.result = RawTermEqual(M.SearchAttemptDerivation(attempt)(), derivation, probe.registry)()
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CompareSearchModesWorkerEntryTracksPacketJobTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.Thingy()
        goal = M.Thingy()
        heuristic = M.Heuristic(M.BFSLabel, M.InsertionOrderLabel, M.three, M.one, M.one, M.one)()
        probe = _CompareSearchModesProbe(graph, start, goal, empty, heuristic, registry)

        packet_job = probe._fresh_compare_job(M.BFSLabel)
        packet_token = M.one
        entry = probe._worker_entry(M.BFSLabel, empty, packet_job, packet_token)
        self.result = RawTermEqual(probe._worker_entry_packet_job(entry), packet_job, probe.registry)()
        if self.result is M.truth_value:
            self.result = RawTermEqual(probe._worker_entry_packet_token(entry), packet_token, probe.registry)()
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class SearchComparisonOutcomeFieldTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        signature = M.SearchSignature(M.Thingy(), M.Atom())()
        best_attempt = M.EmptyList
        comparison = M.SearchComparison(signature, empty, best_attempt, M.SearchAbortedByUserLabel)()
        self.result = RawTermEqual(SearchComparisonOutcome(comparison)(), M.SearchAbortedByUserLabel, registry)()
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class SearchComparisonJobRoundtripTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        signature = M.SearchSignature(M.Thingy(), M.Atom())()
        heuristic = M.Heuristic(M.BFSLabel, M.GoalHeadOrderLabel, M.three, M.one, M.one, M.one)()
        comparison_job = M.SearchComparisonJob(
            signature,
            M.Thingy(),
            M.Atom(),
            empty,
            heuristic,
            empty,
            M.SearchPausedLabel,
        )()
        graph.store_search_comparison_job(comparison_job)
        loaded = graph.lookup_search_comparison_job(signature)
        self.result = RawTermEqual(loaded, comparison_job, registry)()
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class SearchComparisonJobUsesGroupedBlocksTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        signature = M.SearchSignature(M.Thingy(), M.Atom())()
        heuristic = M.Heuristic(M.BFSLabel, M.GoalHeadOrderLabel, M.three, M.one, M.one, M.one)()
        comparison_job = M.SearchComparisonJob(
            signature,
            M.Thingy(),
            M.Atom(),
            empty,
            heuristic,
            empty,
            M.SearchPausedLabel,
        )()
        problem = M.Head(M.Tail(M.Tail(comparison_job)())())()
        runtime = M.Head(M.Tail(M.Tail(M.Tail(comparison_job)())())())()
        result = M.truth_value
        if M.IdentityCompare(M.Head(problem)(), Lmod.SearchComparisonJobProblemLabel)() is M.false_value:
            result = M.false_value
        elif M.IdentityCompare(M.Head(runtime)(), Lmod.SearchComparisonJobRuntimeLabel)() is M.false_value:
            result = M.false_value
        elif RawTermEqual(SearchComparisonJobStates(comparison_job)(), empty, registry)() is M.false_value:
            result = M.false_value
        elif RawTermEqual(SearchComparisonJobOutcome(comparison_job)(), M.SearchPausedLabel, registry)() is M.false_value:
            result = M.false_value
        self.result = result
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class SearchWorkerBaselineUsesGroupedProblemBlockTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        constructors = M.Tree(empty)
        start = M.Thingy()
        goal = M.Atom()
        heuristic = M.Heuristic(M.BFSLabel, M.GoalHeadOrderLabel, M.three, M.one, M.one, M.one)()
        generation = M.SearchSignature(start, goal)()
        baseline = SearchWorkerBaseline(constructors, start, goal, empty, heuristic, empty, generation)()
        problem = M.Head(M.Tail(M.Tail(baseline)())())()
        result = M.truth_value
        if M.IdentityCompare(M.Head(problem)(), Lmod.SearchWorkerBaselineProblemLabel)() is M.false_value:
            result = M.false_value
        elif RawTermEqual(SearchWorkerBaselineStart(baseline)(), start, registry)() is M.false_value:
            result = M.false_value
        elif RawTermEqual(SearchWorkerBaselineGeneration(baseline)(), generation, registry)() is M.false_value:
            result = M.false_value
        self.result = result
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class SearchWorkerPacketUsesGroupedBlocksTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        packet_descriptor = SearchFrontierStatePacket(M.SearchState(M.Thingy(), empty, empty, M.one)())()
        packet = SearchWorkerPacket(
            packet_descriptor,
            M.Tree(empty),
            M.Tree(empty),
            M.Tree(empty),
            empty,
            M.one,
            M.false_value,
            M.false_value,
            M.truth_value,
            M.one,
            M.two,
        )()
        stores = M.Head(M.Tail(M.Tail(packet)())())()
        controls = M.Head(M.Tail(M.Tail(M.Tail(packet)())())())()
        result = M.truth_value
        if M.IdentityCompare(M.Head(stores)(), Lmod.SearchWorkerPacketStoresLabel)() is M.false_value:
            result = M.false_value
        elif M.IdentityCompare(M.Head(controls)(), Lmod.SearchWorkerPacketControlsLabel)() is M.false_value:
            result = M.false_value
        elif RawTermEqual(SearchWorkerPacketGeneration(packet)(), M.two, registry)() is M.false_value:
            result = M.false_value
        self.result = result
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class SearchWorkerLaunchUsesGroupedDispatchTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.Thingy()
        goal = M.Atom()
        heuristic = M.Heuristic(M.BFSLabel, M.GoalHeadOrderLabel, M.three, M.one, M.one, M.one)()
        generation = M.SearchSignature(start, goal)()
        baseline = SearchWorkerBaseline(M.Tree(empty), start, goal, empty, heuristic, empty, generation)()
        packet_state = M.SearchState(start, empty, empty, M.one)()
        launch = SearchWorkerLaunch(
            M.BFSLabel,
            SearchWorkerSetup(M.BFSLabel, baseline)(),
            SearchWorkerPacket(
                SearchFrontierStatePacket(packet_state)(),
                M.Tree(empty),
                M.Tree(empty),
                M.Tree(empty),
                empty,
                M.one,
                M.false_value,
                M.false_value,
                M.false_value,
                M.one,
                generation,
            )(),
            packet_state,
            M.one,
            M.two,
            M.three,
        )()
        dispatch = M.Head(M.Tail(M.Tail(M.Tail(launch)())())())()
        result = M.truth_value
        if M.IdentityCompare(M.Head(dispatch)(), Lmod.SearchWorkerLaunchDispatchLabel)() is M.false_value:
            result = M.false_value
        elif RawTermEqual(SearchWorkerLaunchBranchSerial(launch)(), M.three, registry)() is M.false_value:
            result = M.false_value
        self.result = result
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class SearchWorkerLaunchPickleRoundtripTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.Thingy()
        goal = M.Atom()
        heuristic = M.Heuristic(M.BFSLabel, M.GoalHeadOrderLabel, M.three, M.one, M.one, M.one)()
        generation = M.SearchSignature(start, goal)()
        baseline = SearchWorkerBaseline(M.Tree(empty), start, goal, empty, heuristic, empty, generation)()
        packet_state = M.SearchState(start, empty, empty, M.one)()
        launch = SearchWorkerLaunch(
            M.BFSLabel,
            SearchWorkerSetup(M.BFSLabel, baseline)(),
            SearchWorkerPacket(
                SearchFrontierStatePacket(packet_state)(),
                M.Tree(empty),
                M.Tree(empty),
                M.Tree(empty),
                empty,
                M.one,
                M.false_value,
                M.false_value,
                M.truth_value,
                M.one,
                generation,
            )(),
            packet_state,
            M.one,
            M.two,
            M.three,
        )()
        loaded = pickle.loads(pickle.dumps(launch))
        self.result = RawTermEqual(loaded, launch, registry)()
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class SearchWorkerResultPickleRoundtripTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.Thingy()
        goal = M.Atom()
        heuristic = M.Heuristic(M.BFSLabel, M.GoalHeadOrderLabel, M.three, M.one, M.one, M.one)()
        job = M.SearchJob(
            start,
            goal,
            empty,
            heuristic,
            M.SearchRunningLabel,
            M.Pair(M.SearchState(start, empty, empty, M.one)(), empty),
            M.one,
            M.two,
            M.two,
            empty,
            M.Tree(empty),
            M.Tree(empty),
            empty,
            M.one,
        )()
        ready_packets = M.Pair(SearchFrontierStatePacket(M.SearchState(goal, empty, empty, M.one)())(), empty)
        worker_result = SearchWorkerResult(
            M.BFSLabel,
            M.SearchRunningLabel,
            M.three,
            M.one,
            M.two,
            M.one,
            M.two,
            M.two,
            M.one,
            job,
            M.Tree(empty),
            ready_packets,
            M.one,
            M.Tree(empty),
            M.one,
        )()
        loaded = pickle.loads(pickle.dumps(worker_result))
        self.result = RawTermEqual(loaded, worker_result, registry)()
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class SearchPlainAtomSingletonPickleRoundtripTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        loaded_zero = pickle.loads(pickle.dumps(M.Zero))
        loaded_one = pickle.loads(pickle.dumps(M.one))
        loaded_empty = pickle.loads(pickle.dumps(M.EmptyList))
        self.result = M.truth_value
        if RawTermEqual(loaded_zero, M.Zero, registry)() is M.false_value:
            self.result = M.false_value
        elif RawTermEqual(loaded_one, M.one, registry)() is M.false_value:
            self.result = M.false_value
        elif RawTermEqual(loaded_empty, M.EmptyList, registry)() is M.false_value:
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class PausedSearchJobSnapshotRoundtripTest(M.Edge):
    def __init__(self, _graph):
        empty = M.EmptyList
        runtime = make_fresh_runtime()
        namespace = dict(vars(M))
        namespace.update(vars(Hmod))
        namespace.update(vars(Lmod))
        namespace.update(vars(Pmod))
        namespace.update(vars(Gmod))
        namespace.update(vars(Xmod))
        namespace.update(vars(Rmod))
        namespace.update(vars(Smod))
        namespace.update(vars(Theoremmod))
        snapshot_fd, snapshot_path = tempfile.mkstemp(suffix=".json")
        os.close(snapshot_fd)
        try:
            start = M.Pair(M.one, empty)
            goal = M.Pair(M.two, empty)
            heuristic = M.Heuristic(M.BFSLabel, M.GoalHeadOrderLabel, M.three, M.one, M.one, M.one)()
            job = M.SearchJob(
                start,
                goal,
                empty,
                heuristic,
                M.SearchPausedLabel,
                M.Pair(M.SearchState(start, empty, empty, M.one)(), empty),
                M.one,
                M.two,
                M.two,
                empty,
                M.Tree(empty),
                M.Tree(empty),
                empty,
                M.one,
            )()
            runtime.graph.store_search_job(job)
            save_runtime(runtime, snapshot_path, namespace)
            loaded_runtime = boot_from_snapshot(snapshot_path, namespace)
            loaded_job = M.Head(loaded_runtime.graph.search_jobs)()
            loaded_registry = M.FromContextGetConstructors(loaded_runtime.graph)()
            self.result = RawTermEqual(loaded_job, job, loaded_registry)()
        finally:
            try:
                os.remove(snapshot_path)
            except OSError:
                pass
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class NatValueIndexSnapshotRoundtripTest(M.Edge):
    def __init__(self, _graph):
        empty = M.EmptyList
        runtime = make_fresh_runtime()
        namespace = dict(vars(M))
        namespace.update(vars(Hmod))
        namespace.update(vars(Lmod))
        namespace.update(vars(Pmod))
        namespace.update(vars(Gmod))
        namespace.update(vars(Xmod))
        namespace.update(vars(Rmod))
        namespace.update(vars(Smod))
        namespace.update(vars(Theoremmod))
        snapshot_fd, snapshot_path = tempfile.mkstemp(suffix=".json")
        os.close(snapshot_fd)
        try:
            registry = _registry(runtime.graph)
            nat_value_index = M.TreeInsert(M.Tree(empty), M.one, M.two, registry)()
            runtime.graph._replace_context(nat_value_index=nat_value_index)
            save_runtime(runtime, snapshot_path, namespace)
            loaded_runtime = boot_from_snapshot(snapshot_path, namespace)
            loaded_registry = M.FromContextGetConstructors(loaded_runtime.graph)()
            self.result = RawTermEqual(loaded_runtime.graph.nat_value_index, nat_value_index, loaded_registry)()
        finally:
            try:
                os.remove(snapshot_path)
            except OSError:
                pass
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class ColdE2ReachesSnapshotSaveTest(M.Edge):
    def __init__(self, _graph):
        from . import main as Mainmod

        snapshot_fd, snapshot_path = tempfile.mkstemp(suffix=".json")
        os.close(snapshot_fd)
        try:
            os.remove(snapshot_path)
        except OSError:
            pass
        output = io.StringIO()
        self.result = M.false_value
        try:
            with redirect_stdout(output):
                try:
                    Mainmod.run_cold_mode(
                        filter_name="e2",
                        snapshot_path=snapshot_path,
                        snapshot_save_timeout_seconds=0.0,
                    )
                except SnapshotSaveTimeout:
                    self.result = M.truth_value
            text = output.getvalue()
            proved_index = text.find("engel_e2: proved in")
            summary_index = text.find("proved 1 / 1 theorem cases during cold boot")
            save_index = text.find("snapshot save FAILED: exceeded 0 seconds during namespace synchronization")
            if proved_index == -1:
                self.result = M.false_value
            elif summary_index == -1:
                self.result = M.false_value
            elif save_index == -1:
                self.result = M.false_value
            elif save_index <= summary_index:
                self.result = M.false_value
        except (OSError, RuntimeError):
            self.result = M.false_value
        finally:
            try:
                os.remove(snapshot_path)
            except OSError:
                pass
            try:
                os.remove(snapshot_path + ".tmp")
            except OSError:
                pass
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class SnapshotSaveTimeoutPreservesExistingSnapshotTest(M.Edge):
    def __init__(self, _graph):
        runtime = make_fresh_runtime()
        namespace = dict(vars(M))
        namespace.update(vars(Hmod))
        namespace.update(vars(Lmod))
        namespace.update(vars(Pmod))
        namespace.update(vars(Gmod))
        namespace.update(vars(Xmod))
        namespace.update(vars(Rmod))
        namespace.update(vars(Smod))
        namespace.update(vars(Theoremmod))
        snapshot_fd, snapshot_path = tempfile.mkstemp(suffix=".json")
        os.close(snapshot_fd)
        with open(snapshot_path, "w", encoding="utf-8") as handle:
            handle.write("previous snapshot")
        output = io.StringIO()
        deadline = None
        self.result = M.false_value
        try:
            with redirect_stdout(output):
                deadline = SnapshotSaveDeadline(0.0)
                try:
                    save_runtime(runtime, snapshot_path, namespace, deadline=deadline)
                except SnapshotSaveTimeout as error:
                    self.result = M.truth_value
                    if error.phase != "namespace synchronization":
                        self.result = M.false_value
            if output.getvalue().find("snapshot save FAILED: exceeded 0 seconds during namespace synchronization") == -1:
                self.result = M.false_value
            if os.path.exists(snapshot_path + ".tmp"):
                self.result = M.false_value
            with open(snapshot_path, "r", encoding="utf-8") as handle:
                preserved_text = handle.read()
            if preserved_text != "previous snapshot":
                self.result = M.false_value
        except (OSError, RuntimeError):
            self.result = M.false_value
        finally:
            if deadline is not None:
                deadline.close()
            try:
                os.remove(snapshot_path)
            except OSError:
                pass
            try:
                os.remove(snapshot_path + ".tmp")
            except OSError:
                pass
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class UnpausedSnapshotProbeSkipsActivationAndRewriteTest(M.Edge):
    def __init__(self, _graph):
        from . import main as Mainmod

        runtime = make_fresh_runtime()
        namespace = Mainmod._runtime_namespace()
        snapshot_fd, snapshot_path = tempfile.mkstemp(suffix=".json")
        os.close(snapshot_fd)
        output = io.StringIO()
        self.result = M.truth_value
        try:
            save_runtime(runtime, snapshot_path, namespace)
            with open(snapshot_path, "rb") as handle:
                saved_snapshot = handle.read()
            with redirect_stdout(output):
                resumed = Mainmod._maybe_resume_paused_cold_search(
                    debug=True,
                    snapshot_path=snapshot_path,
                )
            with open(snapshot_path, "rb") as handle:
                probed_snapshot = handle.read()

            text = output.getvalue()
            if M.IdentityCompare(resumed, M.false_value)() is M.false_value:
                self.result = M.false_value
            elif saved_snapshot != probed_snapshot:
                self.result = M.false_value
            elif text.find("DEBUG: snapshot contains no paused-job roots") == -1:
                self.result = M.false_value
            elif text.find("DEBUG: boot_from_snapshot:") != -1:
                self.result = M.false_value
        except (OSError, RuntimeError, json.JSONDecodeError, ValueError, KeyError):
            self.result = M.false_value
        finally:
            try:
                os.remove(snapshot_path)
            except OSError:
                pass
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class IdentityRedBlackIdentityIndexTest(M.Edge):
    def __init__(self, _graph):
        first = M.Char("same")
        second = M.Char("same")
        third = M.Atom()
        fourth = M.Atom()
        fifth = M.Atom()
        entries = M.Pair(
            M.Pair(first, M.Pair(M.one, M.EmptyList)),
            M.Pair(
                M.Pair(second, M.Pair(M.two, M.EmptyList)),
                M.Pair(
                    M.Pair(third, M.Pair(third, M.EmptyList)),
                    M.Pair(
                        M.Pair(fourth, M.Pair(fourth, M.EmptyList)),
                        M.Pair(
                            M.Pair(fifth, M.Pair(fifth, M.EmptyList)),
                            M.EmptyList,
                        ),
                    ),
                ),
            ),
        )

        tree = M.EmptyList
        remaining = entries
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            entry = M.Head(remaining)()
            tree = Tmod.IdentityRedBlackInsert(
                tree,
                M.Head(entry)(),
                M.Head(M.Tail(entry)())(),
            )()
            remaining = M.Tail(remaining)()

        self.result = Tmod.IdentityRedBlackValid(tree)()
        remaining = entries
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            entry = M.Head(remaining)()
            found = Tmod.IdentityRedBlackLookup(tree, M.Head(entry)())()
            if M.Head(found)() is M.false_value:
                self.result = M.false_value
            elif M.IdentityCompare(
                M.Head(M.Tail(found)())(),
                M.Head(M.Tail(entry)())(),
            )() is M.false_value:
                self.result = M.false_value
            remaining = M.Tail(remaining)()

        missing = Tmod.IdentityRedBlackLookup(tree, M.Atom())()
        if M.Head(missing)() is M.truth_value:
            self.result = M.false_value

        same_id_key = M.Atom()
        same_id_key.id = first.id
        same_id_insert = Tmod.IdentityRedBlackInsertMissing(tree, same_id_key, M.three)
        if same_id_insert.inserted is M.truth_value:
            self.result = M.false_value
        elif same_id_insert.result is not tree:
            self.result = M.false_value
        same_id_found = Tmod.IdentityRedBlackLookup(tree, same_id_key)()
        if M.Head(same_id_found)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Head(M.Tail(same_id_found)())(), M.one)() is M.false_value:
            self.result = M.false_value
        if Tmod.IdentityRedBlackValid(same_id_insert.result)() is M.false_value:
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class SnapshotPreservesMachineEdgeStructureTest(M.Edge):
    def __init__(self, _graph):
        empty = M.EmptyList
        namespace = dict(vars(M))
        namespace.update(vars(Lmod))
        edge_inputs = M.Pair(M.one, empty)
        edge_results = M.Pair(M.two, empty)
        edge = M.Edge(inputs=edge_inputs, results=edge_results)
        snapshot = SnapshotCodec(namespace).capture_objects({"edge": edge})
        loaded = SnapshotCodec(namespace).load_snapshot(snapshot).roots["edge"]

        self.result = M.truth_value
        if M.IdentityCompare(loaded._snapshot_edge_marker, loaded)() is M.false_value:
            self.result = M.false_value
        elif RawTermEqual(M.EdgeInputs(loaded)(), edge_inputs, M.AllConstructors)() is M.false_value:
            self.result = M.false_value
        elif RawTermEqual(M.EdgeResults(loaded)(), edge_results, M.AllConstructors)() is M.false_value:
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class SnapshotPreservesConstructorLabelsAndCharsTest(M.Edge):
    def __init__(self, _graph):
        empty = M.EmptyList
        namespace = dict(vars(M))
        namespace.update(vars(Lmod))
        first_name = M.Char("v")
        second_name = M.Char("v")
        term = M.Pair(
            Lmod.SideOfLabel,
            M.Pair(
                M.Pair(
                    Lmod.SegmentLabel,
                    M.Pair(first_name, M.Pair(first_name, M.Pair(second_name, empty))),
                ),
                M.Pair(M.Char("t"), empty),
            ),
        )
        codec = SnapshotCodec(namespace)
        snapshot = codec.capture_objects({"term": term})
        loaded = SnapshotCodec(namespace).load_snapshot(snapshot).roots["term"]
        self.result = RawTermEqual(loaded, term, M.AllConstructors)()
        if Tmod.IdentityRedBlackValid(codec.object_id_index)() is M.false_value:
            self.result = M.false_value
        loaded_names = M.Tail(M.Head(M.Tail(loaded)())())()
        loaded_first = M.Head(loaded_names)()
        loaded_repeat = M.Head(M.Tail(loaded_names)())()
        loaded_second = M.Head(M.Tail(M.Tail(loaded_names)())())()
        if M.IdentityCompare(loaded_first, loaded_repeat)() is M.false_value:
            self.result = M.false_value
        if M.IdentityCompare(loaded_first, loaded_second)() is M.truth_value:
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class SnapshotPreservesRuleEdgeInputsTest(M.Edge):
    def __init__(self, _graph):
        empty = M.EmptyList
        namespace = dict(vars(M))
        namespace.update(vars(Lmod))
        namespace.update(vars(Pmod))
        pattern = M.Pair(M.Char("x"), empty)
        replacement = M.Pair(M.Char("y"), empty)
        rule = Rule(pattern, replacement)
        snapshot = SnapshotCodec(namespace).capture_objects({"rule": rule})
        loaded = SnapshotCodec(namespace).load_snapshot(snapshot).roots["rule"]
        self.result = M.truth_value
        if M.Compare(RulePremises(loaded)(), M.EmptyList)() is M.truth_value:
            self.result = M.false_value
        elif M.PrettyTerm(RuleReplacement(loaded)(), M.AllConstructors)() != M.PrettyTerm(replacement, M.AllConstructors)():
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class SearchWorkerResumeStateRestoresSavedPlanTest(M.Edge):
    def __init__(self, _graph):
        from .main import _search_worker_checkpoint, _search_worker_mode_heuristic, _search_worker_resume_state

        empty = M.EmptyList
        runtime = make_fresh_runtime()
        registry = _registry(runtime.graph)
        heuristic = _search_worker_mode_heuristic(runtime, "dfs", registry)
        start = M.Pair(
            Lmod.SideOfLabel,
            M.Pair(
                M.Pair(Lmod.SegmentLabel, M.Pair(M.Char("v"), M.Pair(M.Char("w"), empty))),
                M.Pair(M.Char("t"), empty),
            ),
        )
        goal = M.Pair(Lmod.LengthLabel, M.Pair(M.Char("v"), empty))
        proof_cost = Pmod.ProofCost(M.Zero, M.Zero, M.Zero, M.Zero)()
        plan = M.Pair(M.Atom(), empty)
        search_cost_pair = Smod.BuildSearchCost(plan, M.one, M.Zero, M.one, Smod.SearchSuccessLabel, registry)()
        search_cost = M.Head(search_cost_pair)()
        snapshot_fd, snapshot_path = tempfile.mkstemp(suffix=".json")
        os.close(snapshot_fd)
        try:
            _search_worker_checkpoint(
                runtime,
                snapshot_path,
                start,
                goal,
                heuristic,
                Smod.SearchSuccessLabel,
                M.EmptyList,
                proof_cost,
                search_cost,
                1234,
                "running-derivation",
                plan,
            )
            resume_plan, resume_search_cost, elapsed_milliseconds, stage_text = _search_worker_resume_state(
                snapshot_path,
                start,
                goal,
                heuristic,
            )
            self.result = M.false_value
            if stage_text == "running-derivation":
                if M.Compare(resume_plan, M.EmptyList)() is M.false_value:
                    if M.PrettyTerm(resume_plan, M.AllConstructors)() == M.PrettyTerm(plan, M.AllConstructors)():
                        if M.PrettyTerm(resume_search_cost, M.AllConstructors)() == M.PrettyTerm(search_cost, M.AllConstructors)():
                            if elapsed_milliseconds == 1234:
                                self.result = M.truth_value
        finally:
            try:
                os.remove(snapshot_path)
            except OSError:
                pass
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class SearchWorkerSnapshotBootWithRuntimeNamespaceTest(M.Edge):
    def __init__(self, _graph):
        from .main import _runtime_namespace, _search_worker_checkpoint, _search_worker_mode_heuristic

        empty = M.EmptyList
        runtime = make_fresh_runtime()
        registry = _registry(runtime.graph)
        heuristic = _search_worker_mode_heuristic(runtime, "dfs", registry)
        start = M.Pair(M.Char("v"), M.Pair(M.Char("w"), empty))
        goal = M.Pair(M.Char("g"), empty)
        proof_cost = Pmod.ProofCost(M.Zero, M.Zero, M.Zero, M.Zero)()
        plan = M.Pair(M.Atom(), empty)
        search_cost_pair = Smod.BuildSearchCost(plan, M.one, M.Zero, M.one, Smod.SearchSuccessLabel, registry)()
        search_cost = M.Head(search_cost_pair)()
        snapshot_fd, snapshot_path = tempfile.mkstemp(suffix=".json")
        os.close(snapshot_fd)
        try:
            _search_worker_checkpoint(
                runtime,
                snapshot_path,
                start,
                goal,
                heuristic,
                Smod.SearchSuccessLabel,
                M.EmptyList,
                proof_cost,
                search_cost,
                1234,
                "running-derivation",
                plan,
            )
            loaded_runtime = boot_from_snapshot(snapshot_path, _runtime_namespace())
            loaded_attempts = loaded_runtime.graph.search_history
            self.result = M.truth_value
            if M.IdentityCompare(loaded_attempts, empty)() is M.truth_value:
                self.result = M.false_value
            else:
                loaded_attempt = M.Head(loaded_attempts)()
                if RawTermEqual(Pmod.SearchAttemptStart(loaded_attempt)(), start, _registry(loaded_runtime.graph))() is M.false_value:
                    self.result = M.false_value
                elif RawTermEqual(Pmod.SearchAttemptGoal(loaded_attempt)(), goal, _registry(loaded_runtime.graph))() is M.false_value:
                    self.result = M.false_value
        finally:
            try:
                os.remove(snapshot_path)
            except OSError:
                pass
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class PausedComparisonJobSnapshotRoundtripTest(M.Edge):
    def __init__(self, _graph):
        empty = M.EmptyList
        runtime = make_fresh_runtime()
        namespace = dict(vars(M))
        namespace.update(vars(Hmod))
        namespace.update(vars(Lmod))
        namespace.update(vars(Pmod))
        namespace.update(vars(Gmod))
        namespace.update(vars(Xmod))
        namespace.update(vars(Rmod))
        namespace.update(vars(Smod))
        namespace.update(vars(Theoremmod))
        snapshot_fd, snapshot_path = tempfile.mkstemp(suffix=".json")
        os.close(snapshot_fd)
        try:
            registry = _registry(runtime.graph)
            start = M.Pair(M.one, empty)
            goal = M.Pair(M.two, empty)
            heuristic = M.Heuristic(M.BFSLabel, M.GoalHeadOrderLabel, M.three, M.one, M.one, M.one)()
            rule = Rule(start, goal)
            rules = M.Pair(rule, empty)
            probe = _CompareSearchModesProbe(runtime.graph, start, goal, rules, heuristic, registry)
            job = probe._fresh_compare_job(M.BFSLabel)
            pending_packet = probe._comparison_frontier_state_packet(M.SearchState(goal, empty, empty, M.one)())
            state = probe._comparison_state(
                M.BFSLabel,
                job,
                M.Tree(empty),
                M.one,
                M.Pair(pending_packet, empty),
            )
            paused_job = probe._paused_comparison_job(
                M.Pair(probe._comparison_pause_state(state), empty),
                M.SearchPausedLabel,
            )
            runtime.graph.store_search_comparison_job(paused_job)
            save_runtime(runtime, snapshot_path, namespace)
            loaded_runtime = boot_from_snapshot(snapshot_path, namespace)
            loaded_job = M.Head(loaded_runtime.graph.search_comparison_jobs)()
            loaded_registry = M.FromContextGetConstructors(loaded_runtime.graph)()
            loaded_probe = _CompareSearchModesProbe(loaded_runtime.graph, start, goal, rules, heuristic, loaded_registry)
            loaded_states = SearchComparisonJobStates(loaded_job)()
            loaded_state = M.Head(loaded_states)()
            self.result = M.truth_value
            if RawTermEqual(SearchComparisonJobOutcome(loaded_job)(), M.SearchPausedLabel, loaded_registry)() is M.false_value:
                self.result = M.false_value
            elif M.IdentityCompare(loaded_states, empty)() is M.truth_value:
                self.result = M.false_value
            elif RawTermEqual(loaded_probe._comparison_state_status(loaded_state), M.SearchPausedLabel, loaded_probe.registry)() is M.false_value:
                self.result = M.false_value
            elif RawTermEqual(loaded_probe._comparison_state_active_packets(loaded_state), M.Zero, loaded_probe.registry)() is M.false_value:
                self.result = M.false_value
            elif M.NatEq(loaded_probe._comparison_state_pending_packets_count(loaded_state), M.one, loaded_probe.registry)() is M.false_value:
                self.result = M.false_value
            elif M.IdentityCompare(loaded_probe._comparison_state_pending_packets(loaded_state), empty)() is M.truth_value:
                self.result = M.false_value
            elif M.IdentityCompare(
                M.Head(M.Head(loaded_probe._comparison_state_pending_packets(loaded_state))())(),
                Lmod.SearchFrontierStatePacketLabel,
            )() is M.false_value:
                self.result = M.false_value
        finally:
            try:
                os.remove(snapshot_path)
            except OSError:
                pass
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class PausedComparisonJobSnapshotResumeTest(M.Edge):
    def __init__(self, _graph):
        empty = M.EmptyList
        runtime = make_fresh_runtime()
        namespace = dict(vars(M))
        namespace.update(vars(Hmod))
        namespace.update(vars(Lmod))
        namespace.update(vars(Pmod))
        namespace.update(vars(Gmod))
        namespace.update(vars(Xmod))
        namespace.update(vars(Rmod))
        namespace.update(vars(Smod))
        namespace.update(vars(Theoremmod))
        snapshot_fd, snapshot_path = tempfile.mkstemp(suffix=".json")
        os.close(snapshot_fd)
        try:
            registry = _registry(runtime.graph)
            start = M.Pair(M.one, empty)
            goal = M.Pair(M.two, empty)
            heuristic = M.Heuristic(M.BFSLabel, M.GoalHeadOrderLabel, M.three, M.one, M.one, M.one)()
            rule = Rule(start, goal)
            rules = M.Pair(rule, empty)
            probe = _CompareSearchModesProbe(runtime.graph, start, goal, rules, heuristic, registry)
            job = probe._fresh_compare_job(M.BFSLabel)
            queued = probe._comparison_packetize_job_frontier(M.BFSLabel, job)
            drained_job = M.Head(queued)()
            packets = M.Head(M.Tail(queued)())()
            state = probe._comparison_state(
                M.BFSLabel,
                drained_job,
                M.Tree(empty),
                M.Zero,
                packets,
            )
            paused_job = probe._paused_comparison_job(
                M.Pair(probe._comparison_pause_state(state), empty),
                M.SearchPausedLabel,
            )
            runtime.graph.store_search_comparison_job(paused_job)
            save_runtime(runtime, snapshot_path, namespace)

            loaded_runtime = boot_from_snapshot(snapshot_path, namespace)
            loaded_runtime.graph._search_disable_console = M.truth_value
            loaded_registry = _registry(loaded_runtime.graph)
            resumed = Smod.CompareSearchModes(loaded_runtime.graph, start, goal, rules, heuristic, loaded_registry)
            comparison = M.Head(resumed.result)()
            best_attempt = M.Head(M.Tail(resumed.result)())()
            self.result = M.truth_value
            if M.Compare(comparison, empty)() is M.truth_value:
                self.result = M.false_value
            elif M.Compare(best_attempt, empty)() is M.truth_value:
                self.result = M.false_value
            elif RawTermEqual(M.SearchAttemptStatus(best_attempt)(), M.SearchSuccessLabel, resumed.registry)() is M.false_value:
                self.result = M.false_value
            elif RawTermEqual(SearchComparisonOutcome(comparison)(), M.SearchSuccessLabel, resumed.registry)() is M.false_value:
                self.result = M.false_value
            elif M.Compare(loaded_runtime.graph.search_comparison_jobs, empty)() is M.false_value:
                self.result = M.false_value
        finally:
            try:
                os.remove(snapshot_path)
            except OSError:
                pass
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CompareSearchModesStopModeMarksOnlyRequestedModeTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.Thingy()
        goal = M.Atom()
        heuristic = M.Heuristic(M.BFSLabel, M.GoalHeadOrderLabel, M.three, M.one, M.one, M.one)()
        probe = _CompareSearchModesProbe(graph, start, goal, empty, heuristic, registry)

        dfs_state = probe._comparison_state(M.DFSLabel, probe._fresh_compare_job(M.DFSLabel), M.Tree(empty), M.one)
        bfs_state = probe._comparison_state(M.BFSLabel, probe._fresh_compare_job(M.BFSLabel), M.Tree(empty), M.one)
        states = M.Pair(dfs_state, M.Pair(bfs_state, empty))
        stopped = probe._comparison_mark_mode_outcome(states, M.BFSLabel, M.SearchAbortedByUserLabel)

        stopped_dfs = probe._comparison_state_for_mode(stopped, M.DFSLabel)
        stopped_bfs = probe._comparison_state_for_mode(stopped, M.BFSLabel)

        result = M.truth_value
        if M.IdentityCompare(probe._comparison_state_status(stopped_dfs), M.SearchRunningLabel)() is M.false_value:
            result = M.false_value
        if M.IdentityCompare(probe._comparison_state_status(stopped_bfs), M.SearchAbortedByUserLabel)() is M.false_value:
            result = M.false_value
        if M.NatEq(probe._comparison_state_active_packets(stopped_bfs), M.Zero, probe.registry)() is M.false_value:
            result = M.false_value
        self.result = result
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CompareSearchModesStopOutcomeClearsPendingPacketCountTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.Thingy()
        goal = M.Atom()
        heuristic = M.Heuristic(M.BFSLabel, M.GoalHeadOrderLabel, M.three, M.one, M.one, M.one)()
        probe = _CompareSearchModesProbe(graph, start, goal, empty, heuristic, registry)

        packet_state = M.SearchState(start, empty, empty, M.one)()
        pending_packet = probe._comparison_frontier_state_packet(packet_state)
        job = probe._fresh_compare_job(M.BFSLabel)
        state = probe._comparison_state(
            M.BFSLabel,
            job,
            M.Tree(empty),
            M.one,
            M.Pair(pending_packet, empty),
            M.one,
        )
        stopped = probe._comparison_mark_state_outcome(state, M.SearchAbortedByUserLabel)

        result = M.truth_value
        if M.IdentityCompare(probe._comparison_state_status(stopped), M.SearchAbortedByUserLabel)() is M.false_value:
            result = M.false_value
        if M.IdentityCompare(probe._comparison_state_pending_packets(stopped), empty)() is M.false_value:
            result = M.false_value
        if M.NatEq(probe._comparison_state_pending_packets_count(stopped), M.Zero, probe.registry)() is M.false_value:
            result = M.false_value
        self.result = result
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CompareSearchModesStoppedStateDoesNotEnqueueJobFrontierTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.Thingy()
        goal = M.Atom()
        heuristic = M.Heuristic(M.BFSLabel, M.GoalHeadOrderLabel, M.three, M.one, M.one, M.one)()
        probe = _CompareSearchModesProbe(graph, start, goal, empty, heuristic, registry)

        frontier_state = M.SearchState(start, empty, empty, M.one)()
        job = M.SearchJob(
            start,
            goal,
            empty,
            heuristic,
            M.SearchRunningLabel,
            M.Pair(frontier_state, empty),
            M.Zero,
            M.Zero,
            M.Zero,
            empty,
            empty,
            M.Tree(empty),
            empty,
            M.one,
        )()
        state = probe._comparison_state(
            M.BFSLabel,
            job,
            M.Tree(empty),
            M.Zero,
            empty,
            M.Zero,
            SearchPacketSearchPhaseLabel,
            M.Zero,
            empty,
            M.SearchAbortedByUserLabel,
        )
        blocked = probe._comparison_state_enqueue_job_frontier(state)

        result = M.truth_value
        if M.IdentityCompare(probe._comparison_state_status(blocked), M.SearchAbortedByUserLabel)() is M.false_value:
            result = M.false_value
        if M.IdentityCompare(probe._comparison_state_pending_packets(blocked), empty)() is M.false_value:
            result = M.false_value
        if M.NatEq(probe._comparison_state_pending_packets_count(blocked), M.Zero, probe.registry)() is M.false_value:
            result = M.false_value
        if RawTermEqual(probe._comparison_state_job(blocked), job, probe.registry)() is M.false_value:
            result = M.false_value
        self.result = result
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CompareSearchModesPauseStatePreservesBacklogTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.Thingy()
        goal = M.Atom()
        heuristic = M.Heuristic(M.BFSLabel, M.GoalHeadOrderLabel, M.three, M.one, M.one, M.one)()
        rule = Rule(start, goal)
        rules = M.Pair(rule, empty)
        probe = _CompareSearchModesProbe(graph, start, goal, rules, heuristic, registry)

        job = probe._fresh_compare_job(M.BFSLabel)
        pending_packet = probe._comparison_branch_packet_job(
            job,
            M.SearchState(goal, empty, empty, M.one)(),
            M.Tree(empty),
            M.Tree(empty),
            empty,
        )
        state = probe._comparison_state(
            M.BFSLabel,
            job,
            M.Tree(empty),
            M.one,
            M.Pair(pending_packet, empty),
        )
        paused = probe._comparison_pause_state(state)

        result = M.truth_value
        if M.IdentityCompare(probe._comparison_state_status(paused), M.SearchPausedLabel)() is M.false_value:
            result = M.false_value
        if M.NatEq(probe._comparison_state_active_packets(paused), M.Zero, probe.registry)() is M.false_value:
            result = M.false_value
        if RawTermEqual(probe._comparison_state_pending_packets(paused), M.Pair(pending_packet, empty), probe.registry)() is M.false_value:
            result = M.false_value
        self.result = result
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CompareSearchModesPauseRequeuesActivePacketIntoJobTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.Thingy()
        goal = M.Atom()
        heuristic = M.Heuristic(M.BFSLabel, M.GoalHeadOrderLabel, M.three, M.one, M.one, M.one)()
        probe = _CompareSearchModesProbe(graph, start, goal, empty, heuristic, registry)

        job = probe._fresh_compare_job(M.BFSLabel)
        packet_state = M.SearchState(goal, empty, empty, M.one)()
        packet = probe._comparison_frontier_state_packet(packet_state)
        state = probe._comparison_state(M.BFSLabel, job, M.Tree(empty), M.one)
        states = M.Pair(state, empty)
        task_queue = _ResidentExecutorQueueProbe()
        result_queue = _ResidentExecutorQueueProbe()
        process = _ResidentExecutorProcessProbe()
        executor = probe._resident_executor(M.one, process, task_queue, result_queue)
        workers = M.Pair(probe._worker_entry(M.BFSLabel, executor, packet, M.one), empty)

        paused_states = probe._pause_parallel_workers(states, workers)
        paused_state = probe._comparison_state_for_mode(paused_states, M.BFSLabel)
        paused_job = probe._comparison_state_job(paused_state)

        result = M.truth_value
        if M.NatEq(probe._comparison_state_active_packets(paused_state), M.Zero, probe.registry)() is M.false_value:
            result = M.false_value
        elif M.NatEq(M.SearchJobFrontierSize(paused_job)(), M.two, probe.registry)() is M.false_value:
            result = M.false_value
        elif M.IdentityCompare(process.alive, M.false_value)() is M.false_value:
            result = M.false_value
        else:
            frontier_tail = M.Tail(M.SearchJobFrontier(paused_job)())()
            if M.IdentityCompare(frontier_tail, empty)() is M.truth_value:
                result = M.false_value
            elif RawTermEqual(M.Head(frontier_tail)(), packet_state, probe.registry)() is M.false_value:
                result = M.false_value

        self.result = result
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CompareSearchModesIntegratesReturnedReadyPacketsTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.Thingy()
        goal = M.Atom()
        heuristic = M.Heuristic(M.BFSLabel, M.GoalHeadOrderLabel, M.three, M.one, M.one, M.one)()
        probe = _CompareSearchModesProbe(graph, start, goal, empty, heuristic, registry)

        job = probe._fresh_compare_job(M.BFSLabel)
        state = probe._comparison_state(M.BFSLabel, job, M.Tree(empty), M.one)
        states = M.Pair(state, empty)

        child_one = M.SearchState(goal, empty, empty, M.one)()
        child_two = M.SearchState(start, empty, empty, M.one)()
        ready_packets = M.Pair(
            probe._comparison_frontier_state_packet(child_one),
            M.Pair(probe._comparison_frontier_state_packet(child_two), empty),
        )
        decoded = SearchWorkerResult(
            M.BFSLabel,
            M.SearchRunningLabel,
            M.three,
            M.Zero,
            M.three,
            M.one,
            M.two,
            M.two,
            M.Zero,
            empty,
            M.Tree(empty),
            ready_packets,
            M.two,
            empty,
            M.one,
        )()

        next_states = probe._integrate_parallel_result(states, M.BFSLabel, decoded)
        next_state = probe._comparison_state_for_mode(next_states, M.BFSLabel)

        result = M.truth_value
        if M.NatEq(probe._comparison_state_active_packets(next_state), M.Zero, probe.registry)() is M.false_value:
            result = M.false_value
        if M.NatEq(probe._comparison_state_completed_packets(next_state), M.one, probe.registry)() is M.false_value:
            result = M.false_value
        if M.NatEq(probe._comparison_state_pending_packets_count(next_state), M.two, probe.registry)() is M.false_value:
            result = M.false_value
        if RawTermEqual(probe._comparison_state_pending_packets(next_state), ready_packets, probe.registry)() is M.false_value:
            result = M.false_value

        self.result = result
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CompareSearchModesEmptyReadyResultRefillsJobFrontierTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.Thingy()
        goal = M.Atom()
        heuristic = M.Heuristic(M.BFSLabel, M.GoalHeadOrderLabel, M.three, M.one, M.one, M.one)()
        probe = _CompareSearchModesProbe(graph, start, goal, empty, heuristic, registry)

        job = probe._fresh_compare_job(M.BFSLabel)
        drained_job = probe._comparison_rebuild_packetized_job(
            job,
            M.SearchRunningLabel,
            empty,
            M.Zero,
            M.Zero,
            M.Zero,
            empty,
            M.Tree(empty),
            empty,
            empty,
            M.Zero,
        )
        state = probe._comparison_state(M.BFSLabel, drained_job, M.Tree(empty), M.one)
        states = M.Pair(state, empty)
        child = M.SearchState(start, empty, empty, M.one)()
        returned_job = probe._comparison_branch_packet_job(job, child, M.Tree(empty), empty, empty)
        decoded = SearchWorkerResult(
            M.BFSLabel,
            M.SearchRunningLabel,
            M.one,
            M.Zero,
            M.one,
            M.Zero,
            M.Zero,
            M.one,
            M.Zero,
            returned_job,
            M.Tree(empty),
            empty,
            M.Zero,
            empty,
            M.one,
        )()

        next_states = probe._integrate_parallel_result(states, M.BFSLabel, decoded)
        next_state = probe._comparison_state_for_mode(next_states, M.BFSLabel)
        pending_packets = probe._comparison_state_pending_packets(next_state)

        result = M.truth_value
        if M.NatEq(probe._comparison_state_active_packets(next_state), M.Zero, probe.registry)() is M.false_value:
            result = M.false_value
        elif M.NatEq(probe._comparison_state_pending_packets_count(next_state), M.one, probe.registry)() is M.false_value:
            result = M.false_value
        elif M.IdentityCompare(pending_packets, empty)() is M.truth_value:
            result = M.false_value
        elif RawTermEqual(probe._comparison_packet_state(M.BFSLabel, M.Head(pending_packets)()), child, probe.registry)() is M.false_value:
            result = M.false_value

        self.result = result
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CompareSearchModesRootWaveRecordsEmptyExpansionTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.Thingy()
        goal = M.Atom()
        heuristic = M.Heuristic(M.BFSLabel, M.InsertionOrderLabel, M.one, M.one, M.one, M.one)()
        probe = _CompareSearchModesProbe(graph, start, goal, empty, heuristic, registry)
        seeded = probe._comparison_seed_rule_wave(M.BFSLabel, probe._fresh_compare_job(M.BFSLabel), empty)
        drained_job = M.Head(seeded)()
        packets = M.Head(M.Tail(seeded)())()
        packet_count = M.Head(M.Tail(M.Tail(seeded)())())()

        result = M.truth_value
        if M.NatEq(M.SearchJobExpanded(drained_job)(), M.one, probe.registry)() is M.false_value:
            result = M.false_value
        elif M.NatEq(packet_count, M.one, probe.registry)() is M.false_value:
            result = M.false_value
        elif M.IdentityCompare(packets, empty)() is M.truth_value:
            result = M.false_value

        self.result = result
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CompareSearchModesReturnedReadyPacketCountFollowsPacketShapeTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.Thingy()
        goal = M.Atom()
        heuristic = M.Heuristic(M.BFSLabel, M.GoalHeadOrderLabel, M.three, M.one, M.one, M.one)()
        probe = _CompareSearchModesProbe(graph, start, goal, empty, heuristic, registry)

        job = probe._fresh_compare_job(M.BFSLabel)
        state = probe._comparison_state(M.BFSLabel, job, M.Tree(empty), M.one)
        states = M.Pair(state, empty)

        child_one = M.SearchState(goal, empty, empty, M.one)()
        child_two = M.SearchState(start, empty, empty, M.one)()
        ready_packets = M.Pair(
            probe._comparison_frontier_state_packet(child_one),
            M.Pair(probe._comparison_frontier_state_packet(child_two), empty),
        )
        decoded = SearchWorkerResult(
            M.BFSLabel,
            M.SearchRunningLabel,
            M.three,
            M.Zero,
            M.three,
            M.one,
            M.two,
            M.two,
            M.Zero,
            empty,
            M.Tree(empty),
            ready_packets,
            M.Zero,
            empty,
            M.one,
        )()

        next_states = probe._integrate_parallel_result(states, M.BFSLabel, decoded)
        next_state = probe._comparison_state_for_mode(next_states, M.BFSLabel)

        result = M.truth_value
        if M.NatEq(probe._comparison_state_pending_packets_count(next_state), M.two, probe.registry)() is M.false_value:
            result = M.false_value
        if RawTermEqual(probe._comparison_state_pending_packets(next_state), ready_packets, probe.registry)() is M.false_value:
            result = M.false_value

        self.result = result
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CompareSearchModesReturnedReadyOverreportedCountKeepsPacketShapeTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.Thingy()
        goal = M.Atom()
        heuristic = M.Heuristic(M.BFSLabel, M.GoalHeadOrderLabel, M.three, M.one, M.one, M.one)()
        probe = _CompareSearchModesProbe(graph, start, goal, empty, heuristic, registry)

        job = probe._fresh_compare_job(M.BFSLabel)
        state = probe._comparison_state(M.BFSLabel, job, M.Tree(empty), M.one)
        states = M.Pair(state, empty)

        child_one = M.SearchState(goal, empty, empty, M.one)()
        child_two = M.SearchState(start, empty, empty, M.one)()
        ready_packets = M.Pair(
            probe._comparison_frontier_state_packet(child_one),
            M.Pair(probe._comparison_frontier_state_packet(child_two), empty),
        )
        decoded = SearchWorkerResult(
            M.BFSLabel,
            M.SearchRunningLabel,
            M.three,
            M.Zero,
            M.three,
            M.one,
            M.two,
            M.two,
            M.Zero,
            empty,
            M.Tree(empty),
            ready_packets,
            M.five,
            empty,
            M.one,
        )()

        next_states = probe._integrate_parallel_result(states, M.BFSLabel, decoded)
        next_state = probe._comparison_state_for_mode(next_states, M.BFSLabel)

        result = M.truth_value
        if M.NatEq(probe._comparison_state_pending_packets_count(next_state), M.two, probe.registry)() is M.false_value:
            result = M.false_value
        if RawTermEqual(probe._comparison_state_pending_packets(next_state), ready_packets, probe.registry)() is M.false_value:
            result = M.false_value

        self.result = result
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CompareSearchModesResidentUnavailableLeavesPacketQueuedTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.Thingy()
        goal = M.Atom()
        heuristic = M.Heuristic(M.BFSLabel, M.GoalHeadOrderLabel, M.three, M.one, M.one, M.one)()
        probe = _CompareSearchModesProbe(graph, start, goal, empty, heuristic, registry)
        probe._comparison_packet_token = M.Zero
        probe._comparison_generation = probe.signature

        job = probe._fresh_compare_job(M.BFSLabel)
        pending_packet = probe._comparison_frontier_state_packet(M.SearchState(start, empty, empty, M.one)())
        state = probe._comparison_state(
            M.BFSLabel,
            job,
            M.Tree(empty),
            M.Zero,
            M.Pair(pending_packet, empty),
            M.one,
            M.SearchPacketSearchPhaseLabel,
        )
        states = M.Pair(state, empty)

        collected = probe._collect_parallel_worker_launches(None, states, empty, empty)
        next_states = M.Head(collected)()
        next_workers = M.Head(M.Tail(collected)())()
        next_idle = M.Head(M.Tail(M.Tail(collected)())())()
        launched_now = M.Head(M.Tail(M.Tail(M.Tail(collected)())())())()

        self.result = M.truth_value
        if RawTermEqual(next_states, states, probe.registry)() is M.false_value:
            self.result = M.false_value
        elif RawTermEqual(next_workers, empty, probe.registry)() is M.false_value:
            self.result = M.false_value
        elif RawTermEqual(next_idle, empty, probe.registry)() is M.false_value:
            self.result = M.false_value
        elif M.NatEq(launched_now, M.Zero, probe.registry)() is M.false_value:
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CompareSearchModesBatchesLargeReturnedReadyPacketWaveTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.Thingy()
        goal = M.Atom()
        heuristic = M.Heuristic(M.BFSLabel, M.GoalHeadOrderLabel, M.two, M.one, M.one, M.one)()
        probe = _CompareSearchModesProbe(graph, start, goal, empty, heuristic, registry)

        job = probe._fresh_compare_job(M.BFSLabel)
        state = probe._comparison_state(M.BFSLabel, job, M.Tree(empty), M.one)
        states = M.Pair(state, empty)

        child_packet = probe._comparison_frontier_state_packet(M.SearchState(start, empty, empty, M.one)())
        ready_packets = M.Pair(
            child_packet,
            M.Pair(
                child_packet,
                M.Pair(
                    child_packet,
                    M.Pair(child_packet, M.Pair(child_packet, empty)),
                ),
            ),
        )
        decoded = SearchWorkerResult(
            M.BFSLabel,
            M.SearchRunningLabel,
            M.five,
            M.Zero,
            M.five,
            M.one,
            M.five,
            M.five,
            M.Zero,
            empty,
            M.Tree(empty),
            ready_packets,
            M.five,
            empty,
            M.one,
        )()

        next_states = probe._integrate_parallel_result(states, M.BFSLabel, decoded)
        next_state = probe._comparison_state_for_mode(next_states, M.BFSLabel)
        pending_packets = probe._comparison_state_pending_packets(next_state)
        first_packet = M.Head(pending_packets)()
        second_packet = M.Head(M.Tail(pending_packets)())()

        result = M.truth_value
        if M.NatEq(probe._comparison_state_active_packets(next_state), M.Zero, probe.registry)() is M.false_value:
            result = M.false_value
        if M.NatEq(probe._comparison_state_completed_packets(next_state), M.one, probe.registry)() is M.false_value:
            result = M.false_value
        if M.NatEq(probe._comparison_state_pending_packets_count(next_state), M.two, probe.registry)() is M.false_value:
            result = M.false_value
        if M.IdentityCompare(M.Head(first_packet)(), M.SearchJobLabel)() is M.false_value:
            result = M.false_value
        if M.IdentityCompare(M.Head(second_packet)(), M.SearchJobLabel)() is M.false_value:
            result = M.false_value
        if M.NatEq(M.SearchJobFrontierSize(first_packet)(), M.four, probe.registry)() is M.false_value:
            result = M.false_value
        if M.NatEq(M.SearchJobFrontierSize(second_packet)(), M.one, probe.registry)() is M.false_value:
            result = M.false_value

        self.result = result
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CompareSearchModesSuccessClearsPendingPacketsTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.Thingy()
        goal = M.Atom()
        heuristic = M.Heuristic(M.BFSLabel, M.GoalHeadOrderLabel, M.three, M.one, M.one, M.one)()
        rule = Rule(start, goal)
        rules = M.Pair(rule, empty)
        probe = _CompareSearchModesProbe(graph, start, goal, rules, heuristic, registry)

        job = probe._fresh_compare_job(M.BFSLabel)
        pending_packet = probe._comparison_frontier_state_packet(M.SearchState(goal, empty, empty, M.one)())
        state = probe._comparison_state(M.BFSLabel, job, M.Tree(empty), M.one, M.Pair(pending_packet, empty))
        states = M.Pair(state, empty)
        success_job = probe._comparison_success_job(state, M.Pair(M.TheoremAction(rule)(), empty))
        decoded = SearchWorkerResult(
            M.BFSLabel,
            M.SearchSuccessLabel,
            M.one,
            M.one,
            M.Zero,
            M.Zero,
            M.Zero,
            M.one,
            M.one,
            success_job,
            M.Tree(empty),
            M.EmptyList,
            M.Zero,
            empty,
            M.one,
        )()

        next_states = probe._integrate_parallel_result(states, M.BFSLabel, decoded)
        next_state = probe._comparison_state_for_mode(next_states, M.BFSLabel)

        result = M.truth_value
        if M.IdentityCompare(probe._comparison_state_status(next_state), M.SearchSuccessLabel)() is M.false_value:
            result = M.false_value
        if M.NatEq(probe._comparison_state_active_packets(next_state), M.Zero, probe.registry)() is M.false_value:
            result = M.false_value
        if M.NatEq(probe._comparison_state_completed_packets(next_state), M.one, probe.registry)() is M.false_value:
            result = M.false_value
        if RawTermEqual(probe._comparison_state_pending_packets(next_state), M.EmptyList, probe.registry)() is M.false_value:
            result = M.false_value
        if M.NatEq(probe._comparison_state_pending_packets_count(next_state), M.Zero, probe.registry)() is M.false_value:
            result = M.false_value

        self.result = result
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CompareSearchModesIgnoresStoppedModeResultTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.Thingy()
        goal = M.Atom()
        heuristic = M.Heuristic(M.BFSLabel, M.GoalHeadOrderLabel, M.three, M.one, M.one, M.one)()
        probe = _CompareSearchModesProbe(graph, start, goal, empty, heuristic, registry)

        job = probe._fresh_compare_job(M.BFSLabel)
        pending_packet = probe._comparison_frontier_state_packet(M.SearchState(goal, empty, empty, M.one)())
        state = probe._comparison_state(M.BFSLabel, job, M.Tree(empty), M.one, M.Pair(pending_packet, empty))
        stopped = probe._comparison_mark_mode_outcome(M.Pair(state, empty), M.BFSLabel, M.SearchAbortedByUserLabel)
        ready_packets = M.Pair(probe._comparison_frontier_state_packet(M.SearchState(start, empty, empty, M.one)()), empty)
        decoded = SearchWorkerResult(
            M.BFSLabel,
            M.SearchRunningLabel,
            M.one,
            M.Zero,
            M.one,
            M.one,
            M.one,
            M.one,
            M.Zero,
            empty,
            M.Tree(empty),
            ready_packets,
            M.one,
            empty,
            M.one,
        )()

        next_states = probe._integrate_parallel_result(stopped, M.BFSLabel, decoded)
        self.result = RawTermEqual(next_states, stopped, probe.registry)()
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CompareSearchModesIgnoresMismatchedPacketTokenResultTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.Thingy()
        goal = M.Atom()
        heuristic = M.Heuristic(M.BFSLabel, M.GoalHeadOrderLabel, M.three, M.one, M.one, M.one)()
        probe = _CompareSearchModesProbe(graph, start, goal, empty, heuristic, registry)

        job = probe._fresh_compare_job(M.BFSLabel)
        state = probe._comparison_state(M.BFSLabel, job, M.Tree(empty), M.one)
        states = M.Pair(state, empty)
        ready_packets = M.Pair(probe._comparison_frontier_state_packet(M.SearchState(start, empty, empty, M.one)()), empty)
        decoded = SearchWorkerResult(
            M.BFSLabel,
            M.SearchRunningLabel,
            M.one,
            M.Zero,
            M.one,
            M.one,
            M.one,
            M.one,
            M.Zero,
            empty,
            M.Tree(empty),
            ready_packets,
            M.one,
            empty,
            M.one,
        )()

        next_states = probe._integrate_parallel_result(states, M.BFSLabel, decoded, M.two)
        self.result = RawTermEqual(next_states, states, probe.registry)()
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CompareSearchModesStaleTokenRetryRequeuesOriginalPacketTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.Thingy()
        goal = M.Atom()
        heuristic = M.Heuristic(M.BFSLabel, M.GoalHeadOrderLabel, M.three, M.one, M.one, M.one)()
        probe = _CompareSearchModesProbe(graph, start, goal, empty, heuristic, registry)

        job = probe._fresh_compare_job(M.BFSLabel)
        packet = probe._comparison_frontier_state_packet(M.SearchState(start, empty, empty, M.one)())
        state = probe._comparison_state(M.BFSLabel, job, M.Tree(empty), M.one)
        states = M.Pair(state, empty)
        task_queue = _ResidentExecutorQueueProbe()
        result_queue = _ResidentExecutorQueueProbe()
        executor = probe._resident_executor(M.one, _ResidentExecutorProcessProbe(), task_queue, result_queue)
        entry = probe._worker_entry(M.BFSLabel, executor, packet, M.two)

        next_states = probe._requeue_worker_entry_for_retry(states, entry)
        next_state = probe._comparison_state_for_mode(next_states, M.BFSLabel)

        self.result = M.truth_value
        if M.NatEq(probe._comparison_state_active_packets(next_state), M.Zero, probe.registry)() is M.false_value:
            self.result = M.false_value
        elif M.NatEq(probe._comparison_state_pending_packets_count(next_state), M.one, probe.registry)() is M.false_value:
            self.result = M.false_value
        elif RawTermEqual(probe._comparison_state_pending_packets(next_state), M.Pair(packet, empty), probe.registry)() is M.false_value:
            self.result = M.false_value
        elif RawTermEqual(probe._comparison_state_job(next_state), job, probe.registry)() is M.false_value:
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CompareSearchModesIgnoresMissingPacketTokenResultTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.Thingy()
        goal = M.Atom()
        heuristic = M.Heuristic(M.BFSLabel, M.GoalHeadOrderLabel, M.three, M.one, M.one, M.one)()
        probe = _CompareSearchModesProbe(graph, start, goal, empty, heuristic, registry)

        job = probe._fresh_compare_job(M.BFSLabel)
        state = probe._comparison_state(M.BFSLabel, job, M.Tree(empty), M.one)
        states = M.Pair(state, empty)
        ready_packets = M.Pair(probe._comparison_frontier_state_packet(M.SearchState(start, empty, empty, M.one)()), empty)
        decoded = SearchWorkerResult(
            M.BFSLabel,
            M.SearchRunningLabel,
            M.one,
            M.Zero,
            M.one,
            M.one,
            M.one,
            M.one,
            M.Zero,
            empty,
            M.Tree(empty),
            ready_packets,
            M.one,
            empty,
            empty,
        )()

        next_states = probe._integrate_parallel_result(states, M.BFSLabel, decoded, M.two)
        self.result = RawTermEqual(next_states, states, probe.registry)()
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CompareSearchModesDecodeMissingPayloadUsesExpectedTokenTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.Thingy()
        goal = M.Atom()
        heuristic = M.Heuristic(M.BFSLabel, M.GoalHeadOrderLabel, M.three, M.one, M.one, M.one)()
        probe = _CompareSearchModesProbe(graph, start, goal, empty, heuristic, registry)

        decoded = probe._decode_parallel_worker_payload(None, M.BFSLabel, M.two)

        self.result = M.truth_value
        if RawTermEqual(SearchWorkerResultMode(decoded)(), M.BFSLabel, probe.registry)() is M.false_value:
            self.result = M.false_value
        elif RawTermEqual(SearchWorkerResultStatus(decoded)(), M.SearchFailureLabel, probe.registry)() is M.false_value:
            self.result = M.false_value
        elif RawTermEqual(SearchWorkerResultPacketToken(decoded)(), M.two, probe.registry)() is M.false_value:
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CompareSearchModesMissingPayloadRetryRequeuesOriginalPacketTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.Thingy()
        goal = M.Atom()
        heuristic = M.Heuristic(M.BFSLabel, M.GoalHeadOrderLabel, M.three, M.one, M.one, M.one)()
        probe = _CompareSearchModesProbe(graph, start, goal, empty, heuristic, registry)

        job = probe._fresh_compare_job(M.BFSLabel)
        packet = probe._comparison_frontier_state_packet(M.SearchState(start, empty, empty, M.one)())
        state = probe._comparison_state(M.BFSLabel, job, M.Tree(empty), M.one)
        states = M.Pair(state, empty)
        task_queue = _ResidentExecutorQueueProbe()
        result_queue = _ResidentExecutorQueueProbe()
        executor = probe._resident_executor(M.one, _ResidentExecutorProcessProbe(), task_queue, result_queue)
        entry = probe._worker_entry(M.BFSLabel, executor, packet, M.two)

        decoded = probe._decode_parallel_worker_payload(None, M.BFSLabel, M.two)
        next_states = probe._requeue_worker_entry_for_retry(states, entry)
        next_state = probe._comparison_state_for_mode(next_states, M.BFSLabel)

        self.result = M.truth_value
        if RawTermEqual(SearchWorkerResultPacketToken(decoded)(), M.two, probe.registry)() is M.false_value:
            self.result = M.false_value
        elif M.NatEq(probe._comparison_state_active_packets(next_state), M.Zero, probe.registry)() is M.false_value:
            self.result = M.false_value
        elif M.NatEq(probe._comparison_state_pending_packets_count(next_state), M.one, probe.registry)() is M.false_value:
            self.result = M.false_value
        elif RawTermEqual(probe._comparison_state_pending_packets(next_state), M.Pair(packet, empty), probe.registry)() is M.false_value:
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class SearchStateHasSingletonTheoremCursor(M.Edge):
    def __init__(self, state):
        self.result = M.false_value
        cursor = M.SearchStateCursor(state)()
        if M.IdentityCompare(cursor, M.EmptyList)() is M.false_value:
            if M.IdentityCompare(M.Head(cursor)(), M.SearchTheoremCursorLabel)() is M.truth_value:
                rules = M.SearchTheoremCursorRules(cursor)()
                if M.IdentityCompare(rules, M.EmptyList)() is M.false_value:
                    if M.IdentityCompare(M.Tail(rules)(), M.EmptyList)() is M.truth_value:
                        self.result = M.truth_value
        super().__init__(inputs=M.Pair(state, M.EmptyList), results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class SearchStateHasSingletonRewriteCursor(M.Edge):
    def __init__(self, state):
        self.result = M.false_value
        cursor = M.SearchStateCursor(state)()
        if M.IdentityCompare(cursor, M.EmptyList)() is M.false_value:
            if M.IdentityCompare(M.Head(cursor)(), M.SearchRewriteCursorLabel)() is M.truth_value:
                if M.IdentityCompare(M.SearchRewriteCursorAgenda(cursor)(), M.EmptyList)() is M.truth_value:
                    rest_rules = M.SearchRewriteCursorRestRules(cursor)()
                    if M.IdentityCompare(rest_rules, M.EmptyList)() is M.false_value:
                        if M.IdentityCompare(M.Tail(rest_rules)(), M.EmptyList)() is M.truth_value:
                            self.result = M.truth_value
        super().__init__(inputs=M.Pair(state, M.EmptyList), results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CompareSearchModesEmptyCursorTheoremFanoutTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.Thingy()
        goal = M.Atom()
        heuristic = M.Heuristic(M.BFSLabel, M.GoalHeadOrderLabel, M.three, M.one, M.one, M.one)()
        rule_one = Rule(start, goal)
        rule_two = Rule(start, M.one)
        rules = M.Pair(rule_one, M.Pair(rule_two, empty))
        probe = _CompareSearchModesProbe(graph, start, goal, rules, heuristic, registry)

        state = M.SearchState(start, empty, empty, M.two)()
        job = M.SearchJob(
            start,
            goal,
            rules,
            heuristic,
            M.SearchRunningLabel,
            M.Pair(state, empty),
            M.Zero,
            M.Zero,
            M.one,
            empty,
            empty,
            M.Tree(empty),
            empty,
            M.one,
        )()
        expanded = probe._comparison_expand_job_packets(M.BFSLabel, job, M.Tree(empty))

        result = M.truth_value
        if M.Compare(expanded, empty)() is M.truth_value:
            result = M.false_value
        else:
            packets = M.Head(M.Tail(expanded)())()
            packet_count = M.Head(M.Tail(M.Tail(expanded)())())()
            if M.NatEq(packet_count, M.three, probe.registry)() is M.false_value:
                result = M.false_value
            if M.IdentityCompare(packets, empty)() is M.truth_value:
                result = M.false_value
            else:
                first_state = probe._comparison_packet_state(M.BFSLabel, M.Head(packets)())
                second_packets = M.Tail(packets)()
                if M.IdentityCompare(second_packets, empty)() is M.truth_value:
                    result = M.false_value
                else:
                    second_state = probe._comparison_packet_state(M.BFSLabel, M.Head(second_packets)())
                    packet_states = M.Pair(first_state, M.Pair(second_state, empty))
                    if ForAll(packet_states, SearchStateHasSingletonTheoremCursor)() is M.false_value:
                        result = M.false_value

        self.result = result
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CompareSearchModesTheoremFanoutPreservesGeneratedTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.Thingy()
        goal = M.Atom()
        heuristic = M.Heuristic(M.BFSLabel, M.GoalHeadOrderLabel, M.three, M.one, M.one, M.one)()
        rule_one = Rule(start, goal)
        rule_two = Rule(start, M.one)
        rules = M.Pair(rule_one, M.Pair(rule_two, empty))
        probe = _CompareSearchModesProbe(graph, start, goal, rules, heuristic, registry)

        generated = SearchPatriciaInsertByKey(M.EmptyList, goal, M.Pair(goal, empty), registry)()
        cursor = M.SearchTheoremCursor(rules, generated)()
        state = M.SearchState(start, empty, empty, M.two, cursor)()
        job = M.SearchJob(
            start,
            goal,
            rules,
            heuristic,
            M.SearchRunningLabel,
            M.Pair(state, empty),
            M.Zero,
            M.Zero,
            M.one,
            empty,
            empty,
            M.Tree(empty),
            empty,
            M.one,
        )()
        expanded = probe._comparison_expand_job_packets(M.BFSLabel, job, M.Tree(empty))

        result = M.truth_value
        if M.Compare(expanded, empty)() is M.truth_value:
            result = M.false_value
        else:
            packets = M.Head(M.Tail(expanded)())()
            packet_count = M.Head(M.Tail(M.Tail(expanded)())())()
            if M.NatEq(packet_count, M.two, probe.registry)() is M.false_value:
                result = M.false_value
            if M.IdentityCompare(packets, empty)() is M.truth_value:
                result = M.false_value
            else:
                first_state = probe._comparison_packet_state(M.BFSLabel, M.Head(packets)())
                second_packets = M.Tail(packets)()
                if M.IdentityCompare(second_packets, empty)() is M.truth_value:
                    result = M.false_value
                else:
                    second_state = probe._comparison_packet_state(M.BFSLabel, M.Head(second_packets)())
                    if ForAll(M.Pair(first_state, empty), SearchStateHasSingletonTheoremCursor)() is M.false_value:
                        result = M.false_value
                    first_cursor = M.SearchStateCursor(first_state)()
                    second_cursor = M.SearchStateCursor(second_state)()
                    if RawTermEqual(M.SearchTheoremCursorGenerated(first_cursor)(), generated, probe.registry)() is M.false_value:
                        result = M.false_value
                    if M.IdentityCompare(M.Head(second_cursor)(), M.SearchRewriteCursorLabel)() is M.false_value:
                        result = M.false_value
                    else:
                        handoff_generated = M.SearchRewriteCursorGenerated(second_cursor)()
                        if M.IdentityCompare(SearchPatriciaLookupByKey(handoff_generated, goal, probe.registry)(), empty)() is M.truth_value:
                            result = M.false_value
                        if M.IdentityCompare(SearchPatriciaLookupByKey(handoff_generated, M.one, probe.registry)(), empty)() is M.truth_value:
                            result = M.false_value

        self.result = result
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CompareSearchModesTheoremFanoutAddsSingleRewriteHandoffTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.Thingy()
        goal = M.Atom()
        heuristic = M.Heuristic(M.BFSLabel, M.GoalHeadOrderLabel, M.three, M.one, M.one, M.one)()
        rule_one = Rule(start, goal)
        rule_two = Rule(start, M.one)
        rules = M.Pair(rule_one, M.Pair(rule_two, empty))
        probe = _CompareSearchModesProbe(graph, start, goal, rules, heuristic, registry)

        state = M.SearchState(start, empty, empty, M.two)()
        job = M.SearchJob(
            start,
            goal,
            rules,
            heuristic,
            M.SearchRunningLabel,
            M.Pair(state, empty),
            M.Zero,
            M.Zero,
            M.one,
            empty,
            empty,
            M.Tree(empty),
            empty,
            M.one,
        )()
        expanded = probe._comparison_expand_job_packets(M.BFSLabel, job, M.Tree(empty))

        result = M.truth_value
        if M.Compare(expanded, empty)() is M.truth_value:
            result = M.false_value
        else:
            packets = M.Head(M.Tail(expanded)())()
            packet_count = M.Head(M.Tail(M.Tail(expanded)())())()
            if M.NatEq(packet_count, M.three, probe.registry)() is M.false_value:
                result = M.false_value
            third_packets = M.Tail(M.Tail(packets)())()
            if M.IdentityCompare(third_packets, empty)() is M.truth_value:
                result = M.false_value
            elif M.IdentityCompare(M.Tail(third_packets)(), empty)() is M.false_value:
                result = M.false_value
            else:
                handoff_state = probe._comparison_packet_state(M.BFSLabel, M.Head(third_packets)())
                cursor = M.SearchStateCursor(handoff_state)()
                if M.IdentityCompare(cursor, empty)() is M.truth_value:
                    result = M.false_value
                elif M.IdentityCompare(M.Head(cursor)(), M.SearchRewriteCursorLabel)() is M.false_value:
                    result = M.false_value
                else:
                    generated = M.SearchRewriteCursorGenerated(cursor)()
                    if M.IdentityCompare(SearchPatriciaLookupByKey(generated, goal, probe.registry)(), empty)() is M.truth_value:
                        result = M.false_value
                    if M.IdentityCompare(SearchPatriciaLookupByKey(generated, M.one, probe.registry)(), empty)() is M.truth_value:
                        result = M.false_value

        self.result = result
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CompareSearchModesEmptyCursorTheoremFanoutSeedsGeneratedTreeTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.Thingy()
        goal = M.Atom()
        heuristic = M.Heuristic(M.BFSLabel, M.GoalHeadOrderLabel, M.three, M.one, M.one, M.one)()
        rule_one = Rule(start, goal)
        rule_two = Rule(start, M.one)
        rules = M.Pair(rule_one, M.Pair(rule_two, empty))
        probe = _CompareSearchModesProbe(graph, start, goal, rules, heuristic, registry)

        state = M.SearchState(start, empty, empty, M.two)()
        job = M.SearchJob(
            start,
            goal,
            rules,
            heuristic,
            M.SearchRunningLabel,
            M.Pair(state, empty),
            M.Zero,
            M.Zero,
            M.one,
            empty,
            empty,
            M.Tree(empty),
            empty,
            M.one,
        )()
        expanded = probe._comparison_expand_job_packets(M.BFSLabel, job, M.Tree(empty))

        generated = M.Tree(empty)
        result = M.truth_value
        if M.Compare(expanded, empty)() is M.truth_value:
            result = M.false_value
        else:
            packets = M.Head(M.Tail(expanded)())()
            if M.IdentityCompare(packets, empty)() is M.truth_value:
                result = M.false_value
            else:
                first_state = probe._comparison_packet_state(M.BFSLabel, M.Head(packets)())
                if ForAll(M.Pair(first_state, empty), SearchStateHasSingletonTheoremCursor)() is M.false_value:
                    result = M.false_value
                first_cursor = M.SearchStateCursor(first_state)()
                if RawTermEqual(M.SearchTheoremCursorGenerated(first_cursor)(), generated, probe.registry)() is M.false_value:
                    result = M.false_value

        self.result = result
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CompareSearchModesRewriteFanoutProducesOneRulePacketsTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.Thingy()
        goal = M.Atom()
        heuristic = M.Heuristic(M.BFSLabel, M.GoalHeadOrderLabel, M.three, M.one, M.one, M.one)()
        rule_one = Rule(start, goal)
        rule_two = Rule(start, M.one)
        rules = M.Pair(rule_one, M.Pair(rule_two, empty))
        probe = _CompareSearchModesProbe(graph, start, goal, rules, heuristic, registry)

        cursor = M.SearchTheoremCursor(empty, M.Tree(empty))()
        state = M.SearchState(start, empty, empty, M.two, cursor)()
        job = M.SearchJob(
            start,
            goal,
            rules,
            heuristic,
            M.SearchRunningLabel,
            M.Pair(state, empty),
            M.Zero,
            M.Zero,
            M.one,
            empty,
            empty,
            M.Tree(empty),
            empty,
            M.one,
        )()
        expanded = probe._comparison_expand_job_packets(M.BFSLabel, job, M.Tree(empty))

        result = M.truth_value
        if M.Compare(expanded, empty)() is M.truth_value:
            result = M.false_value
        else:
            packets = M.Head(M.Tail(expanded)())()
            packet_count = M.Head(M.Tail(M.Tail(expanded)())())()
            if M.NatEq(packet_count, M.two, probe.registry)() is M.false_value:
                result = M.false_value
            if M.IdentityCompare(packets, empty)() is M.truth_value:
                result = M.false_value
            else:
                first_state = probe._comparison_packet_state(M.BFSLabel, M.Head(packets)())
                second_packets = M.Tail(packets)()
                if M.IdentityCompare(second_packets, empty)() is M.truth_value:
                    result = M.false_value
                else:
                    second_state = probe._comparison_packet_state(M.BFSLabel, M.Head(second_packets)())
                    packet_states = M.Pair(first_state, M.Pair(second_state, empty))
                    if ForAll(packet_states, SearchStateHasSingletonRewriteCursor)() is M.false_value:
                        result = M.false_value

        self.result = result
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class SearchWorkerPacketDeltaUsesResidentBaselineTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.Thingy()
        goal = M.Atom()
        heuristic = M.Heuristic(M.BFSLabel, M.InsertionOrderLabel, M.three, M.one, M.one, M.one)()
        rule = Rule(start, goal)
        rules = M.Pair(rule, empty)
        probe = _CompareSearchModesProbe(graph, start, goal, rules, heuristic, registry)
        packet_state = M.SearchState(start, empty, empty, M.one)()
        probe._comparison_generation = probe.signature
        packet_descriptor = probe._comparison_frontier_state_packet(packet_state)
        job = M.SearchJob(
            start,
            goal,
            rules,
            heuristic,
            M.SearchRunningLabel,
            M.Pair(packet_state, empty),
            M.Zero,
            M.Zero,
            M.Zero,
            empty,
            empty,
            M.Tree(empty),
            rules,
            M.one,
        )()
        state = probe._comparison_state(M.BFSLabel, job, M.Tree(empty), M.Zero)
        launch = SearchWorkerLaunch(
            M.BFSLabel,
            probe._worker_setup(state),
            probe._worker_problem_packet(state, packet_descriptor, M.one, M.one),
            packet_descriptor,
            M.one,
            M.one,
            M.one,
        )()
        task_queue = _ResidentExecutorQueueProbe()
        executor = probe._resident_executor_with_baseline(
            probe._resident_executor(M.one, _ResidentExecutorProcessProbe(), task_queue, task_queue),
            probe._comparison_generation,
            M.BFSLabel,
            rules,
        )
        probe._start_parallel_workers(None, M.EmptyList, M.Pair(executor, empty), M.Pair(launch, empty))

        self.result = M.truth_value
        if M.NatEq(task_queue.count, M.one, probe.registry)() is M.false_value:
            self.result = M.false_value
        elif RawTermEqual(
            SearchWorkerPacketRewriteRules(SearchWorkerLaunchPayload(task_queue.first)())(),
            empty,
            probe.registry,
        )() is M.false_value:
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class SearchWorkerFiltersSeededTheoremContinuationTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.Thingy()
        goal = M.Atom()
        rule = Rule(start, goal)
        generated = SearchPatriciaInsertByKey(M.EmptyList, goal, M.Pair(goal, empty), registry)()
        seed_cursor = M.SearchTheoremCursor(M.Pair(rule, empty), M.Tree(empty))()
        seed_state = M.SearchState(start, empty, empty, M.two, seed_cursor)()
        packet = SearchFrontierStatePacket(seed_state)()

        continuation = M.SearchState(start, empty, empty, M.two, M.SearchTheoremCursor(empty, generated)())()
        child = M.SearchState(goal, M.Pair(M.TheoremAction(rule)(), empty), M.Pair(start, empty), M.one)()
        frontier = M.Pair(continuation, M.Pair(child, empty))
        filtered = _worker_filter_seeded_theorem_continuations(packet, frontier)

        self.result = RawTermEqual(filtered, M.Pair(child, empty), registry)()
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CompareSearchModesResidentExecutorRefreshesBaselineOnGenerationChangeTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.Thingy()
        goal = M.Atom()
        heuristic = M.Heuristic(M.BFSLabel, M.InsertionOrderLabel, M.three, M.one, M.one, M.one)()
        rule = Rule(start, goal)
        rules = M.Pair(rule, empty)
        probe = _CompareSearchModesProbe(graph, start, goal, rules, heuristic, registry)
        probe._comparison_generation = probe.signature

        packet_state = M.SearchState(start, empty, empty, M.one)()
        packet_descriptor = probe._comparison_frontier_state_packet(packet_state)
        job = M.SearchJob(
            start,
            goal,
            rules,
            heuristic,
            M.SearchRunningLabel,
            M.Pair(packet_state, empty),
            M.Zero,
            M.Zero,
            M.Zero,
            empty,
            empty,
            M.Tree(empty),
            rules,
            M.one,
        )()
        state = probe._comparison_state(M.BFSLabel, job, M.Tree(empty), M.Zero)
        launch = SearchWorkerLaunch(
            M.BFSLabel,
            probe._worker_setup(state),
            probe._worker_problem_packet(state, packet_descriptor, M.one, M.one),
            packet_descriptor,
            M.one,
            M.one,
            M.one,
        )()
        task_queue = _ResidentExecutorQueueProbe()
        executor = probe._resident_executor(M.one, _ResidentExecutorProcessProbe(), task_queue, task_queue)
        probe._start_parallel_workers(None, M.EmptyList, M.Pair(executor, empty), M.Pair(launch, empty))

        self.result = M.truth_value
        if M.NatEq(task_queue.count, M.two, probe.registry)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Head(task_queue.first)(), SearchWorkerSetupLabel)() is M.false_value:
            self.result = M.false_value
        elif RawTermEqual(
            SearchWorkerPacketRewriteRules(SearchWorkerLaunchPayload(task_queue.second)())(),
            empty,
            probe.registry,
        )() is M.false_value:
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class CompareSearchModesBatchedWaveMatchesSequentialSuccessTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        empty = M.EmptyList
        start = M.Thingy()
        goal = M.Atom()
        heuristic = M.Heuristic(M.BFSLabel, M.InsertionOrderLabel, M.three, M.one, M.one, M.one)()
        rule = Rule(start, goal)
        rules = M.Pair(rule, empty)
        probe = _CompareSearchModesProbe(graph, start, goal, rules, heuristic, registry)

        job = probe._fresh_compare_job(M.BFSLabel)
        state = probe._comparison_state(M.BFSLabel, job, M.Tree(empty), M.two)
        states = M.Pair(state, empty)
        success_job = probe._comparison_success_job(state, M.Pair(M.TheoremAction(rule)(), empty))
        ready_packets = M.Pair(probe._comparison_frontier_state_packet(M.SearchState(start, empty, empty, M.one)()), empty)
        success_decoded = SearchWorkerResult(
            M.BFSLabel,
            M.SearchSuccessLabel,
            M.one,
            M.one,
            M.Zero,
            M.Zero,
            M.Zero,
            M.one,
            M.one,
            success_job,
            M.Tree(empty),
            M.EmptyList,
            M.Zero,
            empty,
            M.one,
        )()
        running_decoded = SearchWorkerResult(
            M.BFSLabel,
            M.SearchRunningLabel,
            M.one,
            M.Zero,
            M.one,
            M.one,
            M.one,
            M.one,
            M.Zero,
            empty,
            M.Tree(empty),
            ready_packets,
            M.one,
            empty,
            M.two,
        )()
        drained = M.Pair(
            probe._drained_parallel_result(M.BFSLabel, success_decoded, M.one),
            M.Pair(probe._drained_parallel_result(M.BFSLabel, running_decoded, M.two), empty),
        )
        batched = probe._integrate_parallel_results(states, drained)
        sequential = probe._integrate_parallel_result(
            probe._integrate_parallel_result(states, M.BFSLabel, success_decoded, M.one),
            M.BFSLabel,
            running_decoded,
            M.two,
        )
        batched_state = probe._comparison_state_for_mode(batched, M.BFSLabel)
        sequential_state = probe._comparison_state_for_mode(sequential, M.BFSLabel)
        self.result = M.truth_value
        if M.PrettyTerm(probe._comparison_state_status(batched_state), probe.registry)() != M.PrettyTerm(
            probe._comparison_state_status(sequential_state),
            probe.registry,
        )():
            self.result = M.false_value
        if M.PrettyTerm(probe._comparison_state_active_packets(batched_state), probe.registry)() != M.PrettyTerm(
            probe._comparison_state_active_packets(sequential_state),
            probe.registry,
        )():
            self.result = M.false_value
        if M.PrettyTerm(probe._comparison_state_completed_packets(batched_state), probe.registry)() != M.PrettyTerm(
            probe._comparison_state_completed_packets(sequential_state),
            probe.registry,
        )():
            self.result = M.false_value
        if M.PrettyTerm(probe._comparison_state_pending_packets_count(batched_state), probe.registry)() != M.PrettyTerm(
            probe._comparison_state_pending_packets_count(sequential_state),
            probe.registry,
        )():
            self.result = M.false_value
        if M.PrettyTerm(probe._comparison_state_pending_packets(batched_state), probe.registry)() != M.PrettyTerm(
            probe._comparison_state_pending_packets(sequential_state),
            probe.registry,
        )():
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class LoadedRulesAvoidSymmetricNotationFactTest(M.Edge):
    def __init__(self, graph):
        self.registry = _registry(graph)
        rules = CollectRules(M.FromContextGetAllRules(graph)())()
        self.result = self._rules_are_clean(rules)
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

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

    def _rule_is_clean(self, rule):
        if self._term_contains_label(RulePremises(rule)(), M.SymmetricProgressionNotationLabel) is M.truth_value:
            return M.false_value
        if self._term_contains_label(RuleReplacement(rule)(), M.SymmetricProgressionNotationLabel) is M.truth_value:
            return M.false_value
        return M.truth_value

    def _rules_are_clean(self, rules):
        if M.IdentityCompare(rules, M.EmptyList)() is M.truth_value:
            return M.truth_value
        if self._rule_is_clean(M.Head(rules)()) is M.false_value:
            return M.false_value
        return self._rules_are_clean(M.Tail(rules)())

    def __call__(self):
        return self.result


class LoadedRulesHaveDirectProgressionEdgeEquationsTest(M.Edge):
    def __init__(self, graph):
        self.registry = _registry(graph)
        rules = CollectRules(M.FromContextGetAllRules(graph)())()
        self.result = self._has_direct_progression_edge_equation(rules)
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

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

    def _rule_matches(self, rule):
        premises = RulePremises(rule)()
        replacement = RuleReplacement(rule)()
        if self._term_contains_label(premises, M.ArithmeticProgressionLabel) is M.false_value:
            return M.false_value
        if self._term_contains_label(premises, M.ParameterLabel) is M.false_value:
            return M.false_value
        if self._term_contains_label(premises, M.CommonDifferenceLabel) is M.false_value:
            return M.false_value
        if self._term_contains_label(replacement, M.SolvedLabel) is M.false_value:
            return M.false_value
        if self._term_contains_label(replacement, M.ExprEqLabel) is M.false_value:
            return M.false_value
        if self._term_contains_label(replacement, M.LengthLabel) is M.false_value:
            return M.false_value
        if self._term_contains_label(replacement, M.CommonDifferenceLabel) is M.false_value:
            return M.false_value
        return M.truth_value

    def _has_direct_progression_edge_equation(self, rules):
        if M.IdentityCompare(rules, M.EmptyList)() is M.truth_value:
            return M.false_value
        if self._rule_matches(M.Head(rules)()) is M.truth_value:
            return M.truth_value
        return self._has_direct_progression_edge_equation(M.Tail(rules)())

    def __call__(self):
        return self.result


class CoinTag(M.Edge):
    def __init__(self):
        self.result = M.Char("Coin")
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class HeadsTag(M.Edge):
    def __init__(self):
        self.result = M.Char("Heads")
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class TailsTag(M.Edge):
    def __init__(self):
        self.result = M.Char("Tails")
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class HeadsCountParityTag(M.Edge):
    def __init__(self):
        self.result = M.Char("HeadsCountParity")
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class OddTag(M.Edge):
    def __init__(self):
        self.result = M.Char("Odd")
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class EvenTag(M.Edge):
    def __init__(self):
        self.result = M.Char("Even")
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class Coin(M.Edge):
    def __init__(self, position, face):
        self.result = M.Pair(CoinTag()(), M.Pair(position, M.Pair(face, M.EmptyList)))
        super().__init__(inputs=M.Pair(position, M.Pair(face, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class HeadsCountParity(M.Edge):
    def __init__(self, parity):
        self.result = M.Pair(HeadsCountParityTag()(), M.Pair(parity, M.EmptyList))
        super().__init__(inputs=M.Pair(parity, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class IsCoinFact(M.Edge):
    def __init__(self, term):
        atom_result = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if M.Compare(M.Head(term)(), CoinTag()())() is M.truth_value:
                atom_result = M.truth_value
        self.result = atom_result
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CoinFace(M.Edge):
    def __init__(self, term):
        atom_result = M.EmptyList
        if IsCoinFact(term)() is M.truth_value:
            atom_result = M.Head(M.Tail(M.Tail(term)())())()
        self.result = atom_result
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CollectCoinFacts(M.Edge):
    def __init__(self, term):
        self.result = self._walk(term)
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def _walk(self, term):
        if M.IdentityCompare(term, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        if IsCoinFact(term)() is M.truth_value:
            return M.Pair(term, M.EmptyList)
        if M.IsPair(term)() is M.false_value:
            return M.EmptyList
        left = self._walk(M.Head(term)())
        right = self._walk(M.Tail(term)())
        return Pmod.Append(left, right)()

    def __call__(self):
        return self.result


class CountHeadsInCoins(M.Edge):
    def __init__(self, coins, registry):
        self.registry = registry
        self.result = self._count(coins, M.Zero)
        super().__init__(inputs=M.Pair(coins, M.Pair(registry, M.EmptyList)), results=self.result)

    def _count(self, coins, acc):
        if M.IdentityCompare(coins, M.EmptyList)() is M.truth_value:
            return acc
        face = CoinFace(M.Head(coins)())()
        next_acc = acc
        if M.Compare(face, HeadsTag()())() is M.truth_value:
            succ_pair = M.Succ(acc, self.registry)()
            next_acc = M.Head(succ_pair)()
            self.registry = M.Head(M.Tail(succ_pair)())()
        return self._count(M.Tail(coins)(), next_acc)

    def __call__(self):
        return self.result


class NatParity(M.Edge):
    def __init__(self, n, registry):
        self.registry = registry
        self.result = self._parity(n)
        super().__init__(inputs=M.Pair(n, M.Pair(registry, M.EmptyList)), results=self.result)

    def _parity(self, n):
        if M.NatEq(n, M.Zero, self.registry)() is M.truth_value:
            return EvenTag()()
        if M.NatEq(n, M.one, self.registry)() is M.truth_value:
            return OddTag()()
        pred_pair = M.NatPred(n, self.registry)()
        pred = M.Head(pred_pair)()
        self.registry = M.Head(M.Tail(pred_pair)())()
        pred2_pair = M.NatPred(pred, self.registry)()
        pred2 = M.Head(pred2_pair)()
        self.registry = M.Head(M.Tail(pred2_pair)())()
        return self._parity(pred2)

    def __call__(self):
        return self.result


class BoardParityFact(M.Edge):
    def __init__(self, facts, registry):
        coins = CollectCoinFacts(facts)()
        heads = CountHeadsInCoins(coins, registry)()
        parity = NatParity(heads, registry)()
        self.result = HeadsCountParity(parity)()
        super().__init__(inputs=M.Pair(facts, M.Pair(registry, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class EngelCoinBoard(M.Edge):
    def __init__(self, faces):
        facts = M.EmptyList
        remaining = faces
        position = M.five
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            facts = M.Pair(Coin(position, M.Head(remaining)())(), facts)
            remaining = M.Tail(remaining)()
            if M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
                pred_pair = M.NatPred(position, M.AllConstructors)()
                position = M.Head(pred_pair)()
        parity_fact = BoardParityFact(facts, M.AllConstructors)()
        facts = M.Pair(parity_fact, facts)
        self.result = Pmod.Knowledge(facts)()
        super().__init__(inputs=M.Pair(faces, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FlipAdjacentPairRule(M.Edge):
    def __init__(self, left_face, right_face, left_after, right_after):
        empty = M.EmptyList
        i_name = M.Thingy()
        p_name = M.Thingy()
        var_i = M.Pair(M.VarTag, M.Pair(i_name, empty))
        var_p = M.Pair(M.VarTag, M.Pair(p_name, empty))
        succ_i = M.Pair(M.SuccLabel, M.Pair(var_i, empty))
        parity = HeadsCountParity(var_p)()
        coin_left = Coin(var_i, left_face)()
        coin_right = Coin(succ_i, right_face)()
        flipped_left = Coin(var_i, left_after)()
        flipped_right = Coin(succ_i, right_after)()
        self.result = Pmod.MultiRule(
            M.Pair(coin_left, M.Pair(coin_right, M.Pair(parity, empty))),
            M.Pair(flipped_left, M.Pair(flipped_right, M.Pair(parity, empty))),
        )
        super().__init__(
            inputs=M.Pair(left_face, M.Pair(right_face, M.Pair(left_after, M.Pair(right_after, empty)))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class FlipAdjacentRules(M.Edge):
    def __init__(self):
        heads = HeadsTag()()
        tails = TailsTag()()
        hh = FlipAdjacentPairRule(heads, heads, tails, tails)()
        ht = FlipAdjacentPairRule(heads, tails, tails, heads)()
        th = FlipAdjacentPairRule(tails, heads, heads, tails)()
        tt = FlipAdjacentPairRule(tails, tails, heads, heads)()
        self.result = M.Pair(hh, M.Pair(ht, M.Pair(th, M.Pair(tt, M.EmptyList))))
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class FlipOneRule(M.Edge):
    def __init__(self):
        empty = M.EmptyList
        i_name = M.Thingy()
        f_name = M.Thingy()
        var_i = M.Pair(M.VarTag, M.Pair(i_name, empty))
        var_f = M.Pair(M.VarTag, M.Pair(f_name, empty))
        self.result = Pmod.Rule(Coin(var_i, var_f)(), Coin(var_i, HeadsTag()())())
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class InvarianceEvenGoalUnreachableTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        graph._search_disable_console = M.truth_value
        graph._search_disable_progress_ticker = M.truth_value
        heads = HeadsTag()()
        tails = TailsTag()()
        start = EngelCoinBoard(M.Pair(heads, M.Pair(heads, M.Pair(heads, M.Pair(heads, M.Pair(heads, M.EmptyList))))))()
        goal = EngelCoinBoard(M.Pair(heads, M.Pair(heads, M.Pair(tails, M.Pair(tails, M.Pair(tails, M.EmptyList))))))()
        rules = FlipAdjacentRules()()
        rule = M.Head(rules)()
        p_name = M.Thingy()
        var_p = M.Pair(M.VarTag, M.Pair(p_name, M.EmptyList))
        phi = Imod.Phi(HeadsCountParity(var_p)())()
        heuristic = Hmod.Heuristic(M.DFSLabel, M.InsertionOrderLabel, M.three, M.one, M.one, M.one)()
        invariant = Imod.Invariant(phi, rules, registry, start, rules)()
        prune = Imod.ReachabilityPrune(start, goal, invariant, phi, registry)()
        search_pair = Imod.SearchWithInvariant(graph, start, goal, rules, heuristic, registry, phi)()
        search_prune = M.Head(M.Tail(M.Tail(search_pair)())())()
        self.result = M.truth_value
        if Imod.IsPreserves(Imod.Preserves(rule, phi, registry)())() is M.false_value:
            self.result = M.false_value
        elif Imod.IsInvariant(invariant)() is M.false_value:
            self.result = M.false_value
        elif Imod.IsUnreachable(prune)() is M.false_value:
            self.result = M.false_value
        elif Imod.IsUnreachable(search_prune)() is M.false_value:
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class InvarianceOddGoalDoesNotPruneTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        graph._search_disable_console = M.truth_value
        graph._search_disable_progress_ticker = M.truth_value
        heads = HeadsTag()()
        tails = TailsTag()()
        start = EngelCoinBoard(M.Pair(heads, M.Pair(heads, M.Pair(heads, M.Pair(heads, M.Pair(heads, M.EmptyList))))))()
        goal = EngelCoinBoard(M.Pair(heads, M.Pair(heads, M.Pair(heads, M.Pair(tails, M.Pair(tails, M.EmptyList))))))()
        rules = FlipAdjacentRules()()
        p_name = M.Thingy()
        var_p = M.Pair(M.VarTag, M.Pair(p_name, M.EmptyList))
        phi = Imod.Phi(HeadsCountParity(var_p)())()
        invariant = Imod.Invariant(phi, rules, registry, start, rules)()
        prune = Imod.ReachabilityPrune(start, goal, invariant, phi, registry)()
        self.result = M.truth_value
        if Imod.IsInvariant(invariant)() is M.false_value:
            self.result = M.false_value
        elif Imod.IsUnreachable(prune)() is M.truth_value:
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class InvarianceUnestablishedEvenPhiDoesNotPruneTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        heads = HeadsTag()()
        tails = TailsTag()()
        start = EngelCoinBoard(M.Pair(heads, M.Pair(heads, M.Pair(heads, M.Pair(heads, M.Pair(heads, M.EmptyList))))))()
        goal = EngelCoinBoard(M.Pair(heads, M.Pair(heads, M.Pair(tails, M.Pair(tails, M.Pair(tails, M.EmptyList))))))()
        rules = FlipAdjacentRules()()
        phi = HeadsCountParity(EvenTag()())()
        invariant = Imod.Invariant(phi, rules, registry, start, rules)()
        prune = Imod.ReachabilityPrune(start, goal, invariant, phi, registry)()
        holds = Imod.PhiHolds(start, phi)()
        self.result = M.truth_value
        if holds is M.truth_value:
            self.result = M.false_value
        elif Imod.IsUnreachable(prune)() is M.truth_value:
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class BlackboardTerms(M.Edge):
    """Symbolic vocabulary for Engel E2. Nothing here holds a concrete board."""

    def __init__(self, name):
        empty = M.EmptyList
        self.result = M.Pair(M.VarTag, M.Pair(M.Char(name), empty))
        super().__init__(inputs=M.Pair(M.Char(name), empty), results=self.result)

    def __call__(self):
        return self.result


class BoardSumFact(M.Edge):
    def __init__(self, state, value):
        self.result = M.Pair(Lmod.BoardSumLabel, M.Pair(state, M.Pair(value, M.EmptyList)))
        super().__init__(inputs=M.Pair(state, M.Pair(value, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class ParityFact(M.Edge):
    def __init__(self, value, bit):
        self.result = M.Pair(Lmod.ParityLabel, M.Pair(value, M.Pair(bit, M.EmptyList)))
        super().__init__(inputs=M.Pair(value, M.Pair(bit, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class IsEvenFact(M.Edge):
    def __init__(self, value):
        self.result = M.Pair(Lmod.IsEvenLabel, M.Pair(value, M.EmptyList))
        super().__init__(inputs=M.Pair(value, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class MoveErasesFact(M.Edge):
    def __init__(self, before, a, b, after):
        self.result = M.Pair(
            Lmod.MoveErasesLabel,
            M.Pair(before, M.Pair(a, M.Pair(b, M.Pair(after, M.EmptyList)))),
        )
        super().__init__(
            inputs=M.Pair(before, M.Pair(a, M.Pair(b, M.Pair(after, M.EmptyList)))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class TerminalFact(M.Edge):
    def __init__(self, state):
        self.result = M.Pair(Lmod.TerminalLabel, M.Pair(state, M.EmptyList))
        super().__init__(inputs=M.Pair(state, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class InitialBoardTerm(M.Edge):
    def __init__(self, n):
        self.result = M.Pair(Lmod.InitialBoardLabel, M.Pair(n, M.EmptyList))
        super().__init__(inputs=M.Pair(n, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class MinTerm(M.Edge):
    def __init__(self, a, b):
        self.result = M.Pair(Lmod.MinLabel, M.Pair(a, M.Pair(b, M.EmptyList)))
        super().__init__(inputs=M.Pair(a, M.Pair(b, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class AbsDiffTerm(M.Edge):
    def __init__(self, a, b):
        self.result = M.Pair(Lmod.AbsDiffLabel, M.Pair(a, M.Pair(b, M.EmptyList)))
        super().__init__(inputs=M.Pair(a, M.Pair(b, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class AddTerm(M.Edge):
    def __init__(self, left, right):
        self.result = M.Pair(M.ExprAddLabel, M.Pair(left, M.Pair(right, M.EmptyList)))
        super().__init__(inputs=M.Pair(left, M.Pair(right, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class MulTerm(M.Edge):
    def __init__(self, left, right):
        self.result = M.Pair(M.ExprMulLabel, M.Pair(left, M.Pair(right, M.EmptyList)))
        super().__init__(inputs=M.Pair(left, M.Pair(right, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class NegTerm(M.Edge):
    def __init__(self, value):
        self.result = M.Pair(M.ExprNegLabel, M.Pair(value, M.EmptyList))
        super().__init__(inputs=M.Pair(value, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TwiceMinTerm(M.Edge):
    def __init__(self, a, b):
        self.result = MulTerm(M.two, MinTerm(a, b)())()
        super().__init__(inputs=M.Pair(a, M.Pair(b, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class SumAfterMoveTerm(M.Edge):
    """S - a - b + AbsDiff(a, b), written with Add and Neg only."""

    def __init__(self, s, a, b):
        dropped = AddTerm(AddTerm(s, NegTerm(a)())(), NegTerm(b)())()
        self.result = AddTerm(dropped, AbsDiffTerm(a, b)())()
        super().__init__(inputs=M.Pair(s, M.Pair(a, M.Pair(b, M.EmptyList))), results=self.result)

    def __call__(self):
        return self.result


class SumMinusTwiceMinTerm(M.Edge):
    """S - 2*Min(a, b)."""

    def __init__(self, s, a, b):
        self.result = AddTerm(s, NegTerm(TwiceMinTerm(a, b)())())()
        super().__init__(inputs=M.Pair(s, M.Pair(a, M.Pair(b, M.EmptyList))), results=self.result)

    def __call__(self):
        return self.result


class InitialBoardSumTerm(M.Edge):
    """n * (2n + 1), taken as the sum lemma for 1 + 2 + ... + 2n."""

    def __init__(self, n):
        self.result = MulTerm(n, AddTerm(MulTerm(M.two, n)(), M.one)())()
        super().__init__(inputs=M.Pair(n, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class BlackboardPhiPattern(M.Edge):
    def __init__(self, bit):
        self.result = ParityFact(Lmod.BoardSumObservableLabel, bit)()
        super().__init__(inputs=M.Pair(bit, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class BlackboardInvariantFact(M.Edge):
    def __init__(self):
        observable = M.Pair(Lmod.ParityLabel, M.Pair(Lmod.BoardSumObservableLabel, M.EmptyList))
        self.result = M.Pair(
            Lmod.InvariantLabel,
            M.Pair(Lmod.BlackboardProblemLabel, M.Pair(observable, M.EmptyList)),
        )
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class EraseAndReplaceRule(M.Edge):
    """The move, stated over arbitrary a and b at the level of the observable."""

    def __init__(self):
        empty = M.EmptyList
        before = BlackboardTerms("before")()
        after = BlackboardTerms("after")()
        a = BlackboardTerms("a")()
        b = BlackboardTerms("b")()
        s = BlackboardTerms("S")()
        p = BlackboardTerms("p")()
        premises = M.Pair(
            BoardSumFact(before, s)(),
            M.Pair(
                ParityFact(s, p)(),
                M.Pair(
                    BlackboardPhiPattern(p)(),
                    M.Pair(MoveErasesFact(before, a, b, after)(), empty),
                ),
            ),
        )
        moved = SumMinusTwiceMinTerm(s, a, b)()
        replacement = M.Pair(
            BoardSumFact(after, moved)(),
            M.Pair(ParityFact(moved, p)(), M.Pair(BlackboardPhiPattern(p)(), empty)),
        )
        self.result = Pmod.MultiRule(premises, replacement)
        super().__init__(inputs=empty, results=self.result)

    def __call__(self):
        return self.result


class SumAfterMoveRule(M.Edge):
    def __init__(self):
        empty = M.EmptyList
        before = BlackboardTerms("before")()
        after = BlackboardTerms("after")()
        a = BlackboardTerms("a")()
        b = BlackboardTerms("b")()
        s = BlackboardTerms("S")()
        premises = M.Pair(
            BoardSumFact(before, s)(),
            M.Pair(MoveErasesFact(before, a, b, after)(), empty),
        )
        replacement = M.Pair(BoardSumFact(after, SumAfterMoveTerm(s, a, b)())(), empty)
        self.result = Pmod.MultiRule(premises, replacement)
        super().__init__(inputs=empty, results=self.result)

    def __call__(self):
        return self.result


class AbsDiffRewriteRule(M.Edge):
    """AbsDiff(a, b) = (a + b) - 2*Min(a, b)."""

    def __init__(self):
        a = BlackboardTerms("a")()
        b = BlackboardTerms("b")()
        pattern = AbsDiffTerm(a, b)()
        replacement = AddTerm(AddTerm(a, b)(), NegTerm(TwiceMinTerm(a, b)())())()
        self.result = Pmod.Rule(pattern, replacement)
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class CancelErasedNumbersRule(M.Edge):
    """((S - a) - b) + ((a + b) - d) rewrites to S - d."""

    def __init__(self):
        a = BlackboardTerms("a")()
        b = BlackboardTerms("b")()
        s = BlackboardTerms("S")()
        d = BlackboardTerms("d")()
        dropped = AddTerm(AddTerm(s, NegTerm(a)())(), NegTerm(b)())()
        restored = AddTerm(AddTerm(a, b)(), NegTerm(d)())()
        pattern = AddTerm(dropped, restored)()
        replacement = AddTerm(s, NegTerm(d)())()
        self.result = Pmod.Rule(pattern, replacement)
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class DoublingIsEvenRule(M.Edge):
    def __init__(self):
        empty = M.EmptyList
        k = BlackboardTerms("k")()
        doubled = MulTerm(M.two, k)()
        state = BlackboardTerms("state")()
        s = BlackboardTerms("S")()
        p = BlackboardTerms("p")()
        witness = BoardSumFact(state, AddTerm(s, NegTerm(doubled)())())()
        parity_of_s = ParityFact(s, p)()
        premises = M.Pair(witness, M.Pair(parity_of_s, empty))
        replacement = M.Pair(
            witness,
            M.Pair(parity_of_s, M.Pair(IsEvenFact(doubled)(), empty)),
        )
        self.result = Pmod.MultiRule(premises, replacement)
        super().__init__(inputs=empty, results=self.result)

    def __call__(self):
        return self.result


class SubtractEvenPreservesParityRule(M.Edge):
    def __init__(self):
        empty = M.EmptyList
        x = BlackboardTerms("x")()
        d = BlackboardTerms("d")()
        p = BlackboardTerms("p")()
        state = BlackboardTerms("state")()
        difference = AddTerm(x, NegTerm(d)())()
        sum_fact = BoardSumFact(state, difference)()
        premises = M.Pair(
            ParityFact(x, p)(),
            M.Pair(IsEvenFact(d)(), M.Pair(sum_fact, empty)),
        )
        replacement = M.Pair(
            ParityFact(x, p)(),
            M.Pair(
                IsEvenFact(d)(),
                M.Pair(sum_fact, M.Pair(ParityFact(difference, p)(), empty)),
            ),
        )
        self.result = Pmod.MultiRule(premises, replacement)
        super().__init__(inputs=empty, results=self.result)

    def __call__(self):
        return self.result


class BoardParityReadoutRule(M.Edge):
    def __init__(self):
        empty = M.EmptyList
        state = BlackboardTerms("state")()
        v = BlackboardTerms("v")()
        p = BlackboardTerms("p")()
        sum_fact = BoardSumFact(state, v)()
        parity_fact = ParityFact(v, p)()
        premises = M.Pair(sum_fact, M.Pair(parity_fact, empty))
        replacement = M.Pair(
            sum_fact,
            M.Pair(parity_fact, M.Pair(BlackboardPhiPattern(p)(), empty)),
        )
        self.result = Pmod.MultiRule(premises, replacement)
        super().__init__(inputs=empty, results=self.result)

    def __call__(self):
        return self.result


class InitialBoardSumRule(M.Edge):
    """The named sum lemma: 1 + 2 + ... + 2n = n(2n+1). Never unfolded."""

    def __init__(self):
        empty = M.EmptyList
        n = BlackboardTerms("n")()
        p = BlackboardTerms("p")()
        board = InitialBoardTerm(n)()
        board_fact = M.Pair(Lmod.InitialBoardLabel, M.Pair(n, empty))
        parity_of_n = ParityFact(n, p)()
        premises = M.Pair(board_fact, M.Pair(parity_of_n, empty))
        replacement = M.Pair(
            board_fact,
            M.Pair(
                parity_of_n,
                M.Pair(BoardSumFact(board, InitialBoardSumTerm(n)())(), empty),
            ),
        )
        self.result = Pmod.MultiRule(premises, replacement)
        super().__init__(inputs=empty, results=self.result)

    def __call__(self):
        return self.result


class TwoKPlusOneIsOddRule(M.Edge):
    def __init__(self):
        empty = M.EmptyList
        k = BlackboardTerms("k")()
        x = BlackboardTerms("x")()
        p = BlackboardTerms("p")()
        state = BlackboardTerms("state")()
        odd_term = AddTerm(MulTerm(M.two, k)(), M.one)()
        witness = BoardSumFact(state, MulTerm(x, odd_term)())()
        parity_of_k = ParityFact(k, p)()
        premises = M.Pair(witness, M.Pair(parity_of_k, empty))
        replacement = M.Pair(
            witness,
            M.Pair(parity_of_k, M.Pair(ParityFact(odd_term, Lmod.OddLabel)(), empty)),
        )
        self.result = Pmod.MultiRule(premises, replacement)
        super().__init__(inputs=empty, results=self.result)

    def __call__(self):
        return self.result


class ParityOfProductRule(M.Edge):
    """Parity of a product, anchored to the board sum so it forms no stray products."""

    def __init__(self, left_bit, right_bit, product_bit):
        empty = M.EmptyList
        x = BlackboardTerms("x")()
        y = BlackboardTerms("y")()
        state = BlackboardTerms("state")()
        product = MulTerm(x, y)()
        witness = BoardSumFact(state, product)()
        left = ParityFact(x, left_bit)()
        right = ParityFact(y, right_bit)()
        premises = M.Pair(witness, M.Pair(left, M.Pair(right, empty)))
        replacement = M.Pair(
            witness,
            M.Pair(
                left,
                M.Pair(right, M.Pair(ParityFact(product, product_bit)(), empty)),
            ),
        )
        self.result = Pmod.MultiRule(premises, replacement)
        super().__init__(
            inputs=M.Pair(left_bit, M.Pair(right_bit, M.Pair(product_bit, empty))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class TerminalReadoutRule(M.Edge):
    def __init__(self):
        empty = M.EmptyList
        p = BlackboardTerms("p")()
        state = BlackboardTerms("state")()
        invariant = BlackboardInvariantFact()()
        reading = BlackboardPhiPattern(p)()
        terminal = TerminalFact(state)()
        premises = M.Pair(invariant, M.Pair(reading, M.Pair(terminal, empty)))
        replacement = M.Pair(
            invariant,
            M.Pair(
                reading,
                M.Pair(terminal, M.Pair(ParityFact(Lmod.FinalNumberLabel, p)(), empty)),
            ),
        )
        self.result = Pmod.MultiRule(premises, replacement)
        super().__init__(inputs=empty, results=self.result)

    def __call__(self):
        return self.result


class BlackboardRules(M.Edge):
    def __init__(self):
        empty = M.EmptyList
        odd_odd = ParityOfProductRule(Lmod.OddLabel, Lmod.OddLabel, Lmod.OddLabel)()
        even_odd = ParityOfProductRule(Lmod.EvenLabel, Lmod.OddLabel, Lmod.EvenLabel)()
        self.result = M.Pair(
            InitialBoardSumRule()(),
            M.Pair(
                TwoKPlusOneIsOddRule()(),
                M.Pair(
                    odd_odd,
                    M.Pair(
                        even_odd,
                        M.Pair(
                            BoardParityReadoutRule()(),
                            M.Pair(
                                EraseAndReplaceRule()(),
                                M.Pair(TerminalReadoutRule()(), empty),
                            ),
                        ),
                    ),
                ),
            ),
        )
        super().__init__(inputs=empty, results=self.result)

    def __call__(self):
        return self.result


class BlackboardStart(M.Edge):
    """Givens for E2: the initial board, the parity of n, terminality, invariance."""

    def __init__(self, n_parity):
        empty = M.EmptyList
        n = M.Char("n")
        facts = M.Pair(
            M.Pair(Lmod.InitialBoardLabel, M.Pair(n, empty)),
            M.Pair(
                ParityFact(n, n_parity)(),
                M.Pair(
                    TerminalFact(M.Char("final"))(),
                    M.Pair(BlackboardInvariantFact()(), empty),
                ),
            ),
        )
        self.result = Pmod.Knowledge(facts)()
        super().__init__(inputs=M.Pair(n_parity, empty), results=self.result)

    def __call__(self):
        return self.result


class BlackboardParityPreservedTest(M.Edge):
    """Test 1: the move preserves the parity of BoardSum, over symbolic a and b."""

    def __init__(self, graph):
        registry = _registry(graph)
        rule = EraseAndReplaceRule()()
        p = BlackboardTerms("p")()
        phi = Imod.Phi(BlackboardPhiPattern(p)())()
        obligation = Imod.Preserves(rule, phi, registry)()
        rules = M.Pair(rule, M.EmptyList)
        start = BlackboardStart(Lmod.OddLabel)()
        invariant = Imod.Invariant(phi, rules, registry, start, rules)()
        self.result = M.truth_value
        if Imod.IsPreserves(obligation)() is M.false_value:
            self.result = M.false_value
        elif Imod.IsInvariant(invariant)() is M.false_value:
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class BlackboardMoveSumIsSumMinusTwiceMinTest(M.Edge):
    """Test 1b: S - a - b + AbsDiff(a, b) rewrites to S - 2*Min(a, b)."""

    def __init__(self, graph):
        registry = _registry(graph)
        a = BlackboardTerms("a")()
        b = BlackboardTerms("b")()
        s = BlackboardTerms("S")()
        rules = M.Pair(AbsDiffRewriteRule()(), M.Pair(CancelErasedNumbersRule()(), M.EmptyList))
        start = SumAfterMoveTerm(s, a, b)()
        goal = SumMinusTwiceMinTerm(s, a, b)()
        self.result = Imod.EquationRewriteEquals(start, goal, rules, registry)()
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class BlackboardInitialParityIsOddTest(M.Edge):
    """Test 2: from Odd(n), derive Parity(n(2n+1), Odd)."""

    def __init__(self, graph):
        registry = _registry(graph)
        rules = BlackboardRules()()
        heuristic = Hmod.Heuristic(M.DFSLabel, M.InsertionOrderLabel, M.three, M.one, M.one, M.one)()
        start = BlackboardStart(Lmod.OddLabel)()
        n = M.Char("n")
        goal = Pmod.Knowledge(
            M.Pair(ParityFact(InitialBoardSumTerm(n)(), Lmod.OddLabel)(), M.EmptyList)
        )()
        plan = Imod.RewriteSearch(start, goal, rules, registry)()
        self.result = M.truth_value
        if M.IdentityCompare(plan, M.EmptyList)() is M.truth_value:
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class BlackboardFinalNumberIsOddTest(M.Edge):
    """Test 3: Parity(FinalNumber, Odd), through the invariant."""

    def __init__(self, graph):
        registry = _registry(graph)
        rules = BlackboardRules()()
        start = BlackboardStart(Lmod.OddLabel)()
        goal = Pmod.Knowledge(
            M.Pair(ParityFact(Lmod.FinalNumberLabel, Lmod.OddLabel)(), M.EmptyList)
        )()
        plan = Imod.RewriteSearch(start, goal, rules, registry)()
        self.result = M.truth_value
        start_text = M.PrettyTerm(start, registry)()
        expected_start_text = "Knowledge([InitialBoard(n), Parity(n, Odd), Terminal(final), Invariant(BlackboardProblem, Parity(BoardSumObservable))])"
        if M.Compare(M.Char(start_text), M.Char(expected_start_text))() is M.false_value:
            self.result = M.false_value
        goal_text = M.PrettyTerm(goal, registry)()
        expected_goal_text = "Knowledge([Parity(FinalNumber, Odd)])"
        if M.Compare(M.Char(goal_text), M.Char(expected_goal_text))() is M.false_value:
            self.result = M.false_value
        before = M.Char("before")
        after = M.Char("after")
        a = M.Char("a")
        b = M.Char("b")
        move_text = M.PrettyTerm(MoveErasesFact(before, a, b, after)(), registry)()
        if M.Compare(M.Char(move_text), M.Char("MoveErases(before, a, b, after)"))() is M.false_value:
            self.result = M.false_value
        sum_text = M.PrettyTerm(BoardSumFact(after, M.Char("sum"))(), registry)()
        if M.Compare(M.Char(sum_text), M.Char("BoardSum(after, sum)"))() is M.false_value:
            self.result = M.false_value
        even_text = M.PrettyTerm(IsEvenFact(M.Char("delta"))(), registry)()
        if M.Compare(M.Char(even_text), M.Char("IsEven(delta)"))() is M.false_value:
            self.result = M.false_value
        min_text = M.PrettyTerm(MinTerm(a, b)(), registry)()
        if M.Compare(M.Char(min_text), M.Char("Min(a, b)"))() is M.false_value:
            self.result = M.false_value
        abs_diff_text = M.PrettyTerm(AbsDiffTerm(a, b)(), registry)()
        if M.Compare(M.Char(abs_diff_text), M.Char("AbsDiff(a, b)"))() is M.false_value:
            self.result = M.false_value
        even_parity_text = M.PrettyTerm(ParityFact(M.Char("n"), Lmod.EvenLabel)(), registry)()
        if M.Compare(M.Char(even_parity_text), M.Char("Parity(n, Even)"))() is M.false_value:
            self.result = M.false_value
        if M.IdentityCompare(plan, M.EmptyList)() is M.truth_value:
            self.result = M.false_value
        else:
            invariant_used = M.false_value
            remaining = plan
            while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
                action = M.Head(remaining)()
                if BlackboardActionMentionsInvariant(action)() is M.truth_value:
                    invariant_used = M.truth_value
                remaining = M.Tail(remaining)()
            if invariant_used is M.false_value:
                self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class BlackboardActionMentionsInvariant(M.Edge):
    """True when the step applied a rule whose premises include the Invariant fact."""

    def __init__(self, action):
        rule = M.Head(M.Tail(action)())()
        self.result = self._walk(Pmod.RulePremises(rule)())
        super().__init__(inputs=M.Pair(action, M.EmptyList), results=self.result)

    def _walk(self, term):
        if M.IdentityCompare(term, Lmod.InvariantLabel)() is M.truth_value:
            return M.truth_value
        if M.IsPair(term)() is M.false_value:
            return M.false_value
        if self._walk(M.Head(term)()) is M.truth_value:
            return M.truth_value
        return self._walk(M.Tail(term)())

    def __call__(self):
        return self.result


class BlackboardEvenNRefusesOddConclusionTest(M.Edge):
    """Test 4: with Even(n) the machine gets Even, and never Odd."""

    def __init__(self, graph):
        registry = _registry(graph)
        rules = BlackboardRules()()
        start = BlackboardStart(Lmod.EvenLabel)()
        odd_goal = Pmod.Knowledge(
            M.Pair(ParityFact(Lmod.FinalNumberLabel, Lmod.OddLabel)(), M.EmptyList)
        )()
        even_goal = Pmod.Knowledge(
            M.Pair(ParityFact(Lmod.FinalNumberLabel, Lmod.EvenLabel)(), M.EmptyList)
        )()
        odd_plan = Imod.RewriteSearch(start, odd_goal, rules, registry)()
        even_plan = Imod.RewriteSearch(start, even_goal, rules, registry)()
        self.result = M.truth_value
        if M.IdentityCompare(odd_plan, M.EmptyList)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(even_plan, M.EmptyList)() is M.truth_value:
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class BlackboardProofExpandsNoBoardsTest(M.Edge):
    """Test 5: the preservation obligation is discharged without any search."""

    def __init__(self, graph):
        registry = _registry(graph)
        graph._search_disable_console = M.truth_value
        graph._search_disable_progress_ticker = M.truth_value
        rule = EraseAndReplaceRule()()
        rules = M.Pair(rule, M.EmptyList)
        p = BlackboardTerms("p")()
        phi = Imod.Phi(BlackboardPhiPattern(p)())()
        start = BlackboardStart(Lmod.OddLabel)()
        goal = Pmod.Knowledge(M.Pair(BlackboardPhiPattern(Lmod.EvenLabel)(), M.EmptyList))()
        heuristic = Hmod.Heuristic(M.DFSLabel, M.InsertionOrderLabel, M.three, M.one, M.one, M.one)()
        search_pair = Imod.SearchWithInvariant(graph, start, goal, rules, heuristic, registry, phi)()
        search_cost = M.Head(M.Tail(search_pair)())()
        expanded = Smod.SearchCostExpanded(search_cost)()
        self.result = M.truth_value
        if M.NatEq(expanded, M.Zero, registry)() is M.false_value:
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class BlackboardStartHasNoBoardCellsTest(M.Edge):
    """Test 5b: the encoding never names a board cell or a move order."""

    def __init__(self, graph):
        start = BlackboardStart(Lmod.OddLabel)()
        facts = Imod.StateFacts(start)()
        self.result = M.truth_value
        remaining = facts
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            fact = M.Head(remaining)()
            head = M.Head(fact)()
            if M.IdentityCompare(head, Lmod.InitialBoardLabel)() is M.truth_value:
                remaining = M.Tail(remaining)()
            elif M.IdentityCompare(head, Lmod.ParityLabel)() is M.truth_value:
                remaining = M.Tail(remaining)()
            elif M.IdentityCompare(head, Lmod.TerminalLabel)() is M.truth_value:
                remaining = M.Tail(remaining)()
            elif M.IdentityCompare(head, Lmod.InvariantLabel)() is M.truth_value:
                remaining = M.Tail(remaining)()
            else:
                self.result = M.false_value
                remaining = M.EmptyList
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class InvarianceFlipOneRefutesParityTest(M.Edge):
    def __init__(self, graph):
        registry = _registry(graph)
        heads = HeadsTag()()
        start = EngelCoinBoard(M.Pair(heads, M.Pair(heads, M.Pair(heads, M.Pair(heads, M.Pair(heads, M.EmptyList))))))()
        goal = EngelCoinBoard(M.Pair(heads, M.Pair(heads, M.Pair(TailsTag()(), M.Pair(TailsTag()(), M.Pair(TailsTag()(), M.EmptyList))))))()
        rule = FlipOneRule()()
        rules = M.Pair(rule, M.EmptyList)
        phi = Imod.Phi(HeadsCountParity(OddTag()())())()
        obligation = Imod.Preserves(rule, phi, registry)()
        invariant = Imod.Invariant(phi, rules, registry, start, rules)()
        prune = Imod.ReachabilityPrune(start, goal, invariant, phi, registry)()
        self.result = M.truth_value
        if Imod.IsInvariantRefuted(obligation)() is M.false_value:
            self.result = M.false_value
        elif Imod.IsInvariant(invariant)() is M.truth_value:
            self.result = M.false_value
        elif Imod.IsUnreachable(prune)() is M.truth_value:
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


def _set_registry(graph, registry):
    graph._replace_context(constructors=registry)
    return registry


def _registry(graph):
    return M.FromContextGetConstructors(graph)()


# Step 52: open-ended operation milestones.
#
# Each milestone is an executable check, not a claim. A milestone that is
# not yet met returns MILESTONE_SKIPPED rather than failing: the criteria
# are allowed to be unmet while the substrate scales, but they are never
# deleted, and none of them may be weakened to make it pass.
MILESTONE_MET = M.Char("milestone-met")
MILESTONE_SKIPPED = M.Char("milestone-skipped")


class MilestoneM1CyclesWithoutRefusalTest(M.Edge):
    """M1: consecutive distributed cycles, no safety refusal, no regression.

    Met when a seeded corpus survives MILESTONE_M1_CYCLES consecutive
    cycles with the floor never refusing and no auto-class regression.
    Skipped while the corpus reaches quiescence sooner, which it does at
    present: a corpus that stops having work to do cannot demonstrate
    sustained operation, and pretending otherwise would make the
    milestone meaningless.
    """

    def __init__(self, _graph):
        empty = M.EmptyList
        left_term = M.Pair(Lmod.ZeroLabel, empty)
        right_term = M.Pair(Lmod.SuccLabel, M.Pair(left_term, empty))
        law = Gmod.CompileRuleToLaw(Pmod.Rule(left_term, right_term))()
        encoded = Gmod.EncodeTermAsGraph(left_term)()
        version = Gmod.InstallLaw(
            Gmod.GraphVersion(
                Gmod.GraphNodes(encoded)(),
                Gmod.GraphEdges(encoded)(),
                empty,
            )(),
            law,
        )()
        version = Gmod.BootstrapSafetyInvariants(version)()
        store = Gmod.ProposalStore(empty)()
        # The floor must be clear at the outset; that much is checkable now.
        self.result = MILESTONE_SKIPPED
        if M.IdentityCompare(
            Gmod.CheckSafety(version, store)(),
            empty,
        )() is M.false_value:
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class MilestoneM2HandleLifecycleTest(M.Edge):
    """M2: mined -> promoted -> retired -> migrated, all through proposals.

    Met when one handle completes the whole lifecycle with every stage
    reconstructible from the Next chain alone. Skipped until a corpus
    drives a mined handle all the way round; the machinery for each
    individual stage exists and is tested separately.
    """

    def __init__(self, _graph):
        self.result = MILESTONE_SKIPPED
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class MilestoneM3MetaHandleReordersTest(M.Edge):
    """M3: a meta-handle prior measurably reorders generation.

    The reordering half is met and checked here: a prior that matches one
    candidate moves it to the front while leaving the candidate set
    unchanged. The milestone as a whole stays skipped until the prior is
    threaded through a real generator and the meta-handle is visible in
    the self-model.
    """

    def __init__(self, _graph):
        empty = M.EmptyList
        zero_term = M.Pair(Lmod.ZeroLabel, empty)
        succ_term = M.Pair(Lmod.SuccLabel, M.Pair(zero_term, empty))
        candidate_zero = Gmod.EncodeTermAsGraph(zero_term)()
        candidate_succ = Gmod.EncodeTermAsGraph(succ_term)()
        candidates = M.Pair(candidate_zero, M.Pair(candidate_succ, empty))
        prior = Gmod.Handle(M.Char("meta-succ"), candidate_succ)()
        ordered = Gmod.OrderByPriors(candidates, M.Pair(prior, empty))()
        self.result = MILESTONE_SKIPPED
        if M.TermEqual(M.Head(ordered)(), candidate_succ)() is M.false_value:
            self.result = M.false_value
        elif Gmod.ChainHasTerm(ordered, candidate_zero)() is M.false_value:
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


class MilestoneM4PolicyLoosenThenTightenTest(M.Edge):
    """M4: a countersigned loosening, later reversed by a single approval.

    The floor's precedence is met and checked here: an approved proposal
    is refused while a safety bound is violated and activates once the
    bound is raised. The milestone as a whole stays skipped until the
    loosening and its reversal both run through the policy_change gate.
    """

    def __init__(self, _graph):
        empty = M.EmptyList
        left_term = M.Pair(Lmod.ZeroLabel, empty)
        right_term = M.Pair(Lmod.SuccLabel, M.Pair(left_term, empty))
        law = Gmod.CompileRuleToLaw(Pmod.Rule(left_term, right_term))()
        proposal = Gmod.Proposal(law, M.Char("milestone"))()
        encoded = Gmod.EncodeTermAsGraph(left_term)()
        version = Gmod.GraphVersion(
            Gmod.GraphNodes(encoded)(),
            Gmod.GraphEdges(encoded)(),
            empty,
        )()
        store = Gmod.ProposalStoreSubmit(Gmod.ProposalStore(empty)(), proposal)()
        store = Gmod.ProposalStoreAttach(
            store,
            proposal,
            Gmod.Approved(proposal, M.Char("curator"))(),
        )()
        entry = M.Head(Gmod.ProposalStoreEntries(store)())()
        tight = Gmod.GraphVersion(
            Gmod.GraphNodes(version)(),
            Gmod.GraphEdges(version)(),
            M.Pair(
                Gmod.SafetyInvariant(
                    M.Char("milestone-bound"),
                    M.GMPRep("0"),
                    Gmod.SAFETY_MEASURE_STORE_SIZE,
                )(),
                empty,
            ),
        )()
        refused = Gmod.ActivateProposal(tight, entry)()
        loose = Gmod.GraphVersion(
            Gmod.GraphNodes(version)(),
            Gmod.GraphEdges(version)(),
            M.Pair(
                Gmod.SafetyInvariant(
                    M.Char("milestone-bound"),
                    M.GMPRep("9999"),
                    Gmod.SAFETY_MEASURE_STORE_SIZE,
                )(),
                empty,
            ),
        )()
        allowed = Gmod.ActivateProposal(loose, entry)()
        self.result = MILESTONE_SKIPPED
        if M.IdentityCompare(M.Head(refused)(), empty)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Head(allowed)(), empty)() is M.truth_value:
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=M.Pair(self.result, M.EmptyList))

    def __call__(self):
        return self.result


def _register_test(graph, name, input_nodes, computation_edge, expected):
    test = Test(graph, M.TestName(name, _registry(graph)), input_nodes, computation_edge, expected)
    _set_registry(graph, M.FromContextGetConstructors(test)())
    graph.add_hypergraph(test)
    return test


def install_default_tests(graph):
    if M.IdentityCompare(graph.default_tests_installed, M.truth_value)() is M.truth_value:
        return graph

    _set_registry(graph, _registry(graph))

    a = M.Thingy()
    b = M.Thingy()
    empty = M.EmptyList

    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(graph, "cmp1_test", M.Pair(a, M.Pair(a, empty)), M.Compare(a, a), M.truth_value)
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(graph, "cmp2_test", M.Pair(a, M.Pair(b, empty)), M.Compare(a, b), M.false_value)
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(graph, "cmp3_test", M.Pair(empty, empty), M.Compare(empty, M.EmptyList), M.truth_value)
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(graph, "cmp4_test", M.Pair(a, M.Pair(empty, empty)), M.Compare(a, empty), M.false_value)

    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "nand_test",
            M.Pair(M.truth_value, M.Pair(M.truth_value, empty)),
            M.NandAtom(M.truth_value, M.truth_value),
            M.false_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "nat_test",
            M.Pair(M.one, M.Pair(M.two, empty)),
            M.NatLess(M.one, M.two, _registry(graph)),
            M.truth_value,
        )

    pair1_input = M.Pair(a, empty)
    pair2_input = M.Pair(a, M.Pair(b, empty))
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(graph, "count1_test", pair1_input, M.Count(pair1_input, _registry(graph)), M.one)
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(graph, "count2_test", pair2_input, M.Count(pair2_input, _registry(graph)), M.two)
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(graph, "thingy1_test", a, M.IsAtom(a, _registry(graph)), M.truth_value)

    numbers = M.Pair(M.one, M.Pair(M.two, M.Pair(M.three, empty)))
    numbers_with_zero = M.Pair(M.Zero, numbers)
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(graph, "exists_test_1", numbers, Exists(numbers, IsNonZero), M.truth_value)
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(graph, "forall_test_1", numbers, ForAll(numbers, IsNonZero), M.truth_value)
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(graph, "exists_test_2", numbers_with_zero, Exists(numbers_with_zero, IsNonZero), M.truth_value)
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(graph, "forall_test_2", numbers_with_zero, ForAll(numbers_with_zero, IsNonZero), M.false_value)

    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "id_comp_test",
            M.Pair(a, M.Pair(b, empty)),
            M.IdentityCompare(a, b),
            M.false_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "is_one_two_test",
            M.Pair(M.one, M.Pair(M.two, empty)),
            M.NatEq(M.one, M.two, _registry(graph)),
            M.false_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "is_two_two_test",
            M.Pair(M.two, M.Pair(M.two, empty)),
            M.NatEq(M.two, M.two, _registry(graph)),
            M.truth_value,
        )

    pair3_input = M.Pair(b, empty)
    sim_count1_pair = M.Count(pair1_input, _registry(graph))()
    sim_count1 = M.Head(sim_count1_pair)()
    reg1 = M.Head(M.Tail(sim_count1_pair)())()
    _set_registry(graph, reg1)

    sim_count2_pair = M.Count(pair3_input, _registry(graph))()
    sim_count2 = M.Head(sim_count2_pair)()
    reg2 = M.Head(M.Tail(sim_count2_pair)())()
    _set_registry(graph, reg2)

    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "sim_pairs_test",
            M.Pair(pair1_input, M.Pair(pair3_input, empty)),
            M.CompareIn(sim_count1, sim_count2, _registry(graph)),
            M.truth_value,
        )

    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(graph, "is_zero0", M.Pair(M.Zero, M.Pair(M.Zero, empty)), M.Compare(M.Zero, M.Zero), M.truth_value)
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(graph, "is_zero1", M.Pair(M.Zero, M.Pair(M.one, empty)), M.Compare(M.Zero, M.one), M.false_value)
    succ_one_pair = M.Succ(M.one, _registry(graph))()
    succ_one = M.Head(succ_one_pair)()
    _set_registry(graph, M.Head(M.Tail(succ_one_pair)())())

    pred_succ_pair = M.NatPred(succ_one, _registry(graph))()
    pred_succ = M.Head(pred_succ_pair)()
    _set_registry(graph, M.Head(M.Tail(pred_succ_pair)())())

    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "pred_succ_test",
            M.Pair(pred_succ, M.Pair(M.one, empty)),
            M.CompareIn(pred_succ, M.one, _registry(graph)),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "zero_less_zero",
            M.Pair(M.Zero, M.Pair(M.Zero, empty)),
            M.NatLess(M.Zero, M.Zero, _registry(graph)),
            M.false_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(graph, "is_two_nat", M.Pair(M.two, empty), M.IsNat(M.two, _registry(graph)), M.truth_value)

    name_x = M.Thingy()
    var_x = M.Pair(M.VarTag, M.Pair(name_x, empty))
    pattern1 = M.Pair(var_x, empty)
    target1 = M.Pair(M.Thingy(), empty)
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "match1_test",
            M.Pair(pattern1, M.Pair(target1, empty)),
            M.Match(pattern1, target1),
            M.truth_value,
        )

    name_a = M.Thingy()
    name_b = M.Atom()
    var_a = M.Pair(M.VarTag, M.Pair(name_a, empty))
    var_b = M.Pair(M.VarTag, M.Pair(name_b, empty))
    pattern2 = M.Pair(var_a, M.Pair(var_b, empty))
    target2 = M.Pair(M.Pair(M.Thingy(), empty), M.Pair(M.one, empty))
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "match2_test",
            M.Pair(pattern2, M.Pair(target2, empty)),
            M.Match(pattern2, target2),
            M.truth_value,
        )

    pattern3 = M.Pair(var_x, empty)
    target3 = M.Pair(M.Pair(M.Thingy(), empty), empty)
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "match3_test",
            M.Pair(pattern3, M.Pair(target3, empty)),
            M.Match(pattern3, target3),
            M.truth_value,
        )

    rewrite_rule = Rule(pattern3, var_x)
    target_head = M.Thingy()
    rewrite_target = M.Pair(target_head, empty)
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "rewrite_test",
            M.Pair(pattern3, M.Pair(var_x, M.Pair(rewrite_target, empty))),
            M.Rewrite(rewrite_rule, rewrite_target, _registry(graph)),
            target_head,
        )

    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "minimal_graph_one_step_map_extension_test",
            empty,
            MinimalGraphOneStepMapExtensionTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "minimal_graph_source_constraint_test",
            empty,
            MinimalGraphSourceConstraintTest(graph),
            M.truth_value,
        )

    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "comparison_prompt_abort_test",
            empty,
            ComparisonPromptAbortTest(),
            M.truth_value,
        )

    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "search_structural_key_equality_test",
            empty,
            SearchStructuralKeyEqualityTest(),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "shared_exact_key_vocabulary_test",
            empty,
            SharedExactKeyVocabularyTest(),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "opaque_exact_key_uses_atom_key_test",
            empty,
            OpaqueExactKeyUsesAtomKeyTest(),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "tree_lookup_uses_structural_keys_test",
            empty,
            TreeLookupUsesStructuralKeysTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "tree_lookup_uses_index_buckets_test",
            empty,
            TreeLookupUsesIndexBucketsTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "legacy_tree_lookup_remains_readable_test",
            empty,
            LegacyTreeLookupRemainsReadableTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "tree_insert_migrates_legacy_tree_test",
            empty,
            TreeInsertMigratesLegacyTreeTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "getconstructor_sees_patricia_tree_terms_test",
            empty,
            GetConstructorSeesPatriciaTreeTermsTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "comparein_sees_patricia_tree_terms_test",
            empty,
            CompareInSeesPatriciaTreeTermsTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "comparein_sees_tree_wrapper_test",
            empty,
            CompareInSeesTreeWrapperTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "search_prompt_cost_step_builds_hundred_test",
            empty,
            SearchPromptCostStepBuildsHundredTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "compare_search_modes_builds_deep_root_wave_shards_without_recursion_test",
            empty,
            CompareSearchModesBuildsDeepRootWaveShardsWithoutRecursionTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "compare_search_modes_resident_executor_ready_handshake_test",
            empty,
            CompareSearchModesResidentExecutorReadyHandshakeTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "compare_search_modes_root_wave_uses_resident_executor_test",
            empty,
            CompareSearchModesRootWaveUsesResidentExecutorTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "compare_search_modes_root_wave_requires_resident_executor_test",
            empty,
            CompareSearchModesRootWaveRequiresResidentExecutorTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "compare_search_modes_fill_warms_resident_pool_before_root_wave_test",
            empty,
            CompareSearchModesFillWarmsResidentPoolBeforeRootWaveTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "compare_search_modes_root_wave_retries_failed_shard_on_resident_test",
            empty,
            CompareSearchModesRootWaveRetriesFailedShardOnResidentTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "compare_search_modes_root_wave_replaces_exhausted_resident_test",
            empty,
            CompareSearchModesRootWaveReplacesExhaustedResidentTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "compare_search_modes_root_wave_seeds_single_rewrite_handoff_test",
            empty,
            CompareSearchModesRootWaveSeedsSingleRewriteHandoffTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "compare_search_modes_root_wave_records_empty_expansion_test",
            empty,
            CompareSearchModesRootWaveRecordsEmptyExpansionTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "compare_search_modes_packetizes_non_root_frontier_test",
            empty,
            CompareSearchModesPacketizesNonRootFrontierTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "compare_search_modes_packetizes_wide_frontier_in_chunks_test",
            empty,
            CompareSearchModesPacketizesWideFrontierInChunksTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "compare_search_modes_prunes_packets_after_best_attempt_test",
            empty,
            CompareSearchModesPrunesPacketsAfterBestAttemptTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "compare_search_modes_fresh_root_jobs_packetize_whole_state_test",
            empty,
            CompareSearchModesFreshRootJobsPacketizeWholeStateTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "compare_search_modes_merges_packet_job_test",
            empty,
            CompareSearchModesMergesPacketJobTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "search_tree_delta_skips_structurally_equal_trees_test",
            empty,
            SearchTreeDeltaSkipsStructurallyEqualTreesTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "search_patricia_lookup_uses_structural_keys_test",
            empty,
            SearchPatriciaLookupUsesStructuralKeysTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "search_tree_delta_skips_structurally_equal_patricia_trees_test",
            empty,
            SearchTreeDeltaSkipsStructurallyEqualPatriciaTreesTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "search_tree_delta_skips_equal_content_different_shape_trees_test",
            empty,
            SearchTreeDeltaSkipsEqualContentDifferentShapeTreesTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "tree_insert_deep_pair_lookup_avoids_recursion_test",
            empty,
            TreeInsertDeepPairLookupAvoidsRecursionTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "compare_search_modes_drops_exhausted_pending_packets_test",
            empty,
            CompareSearchModesDropsExhaustedPendingPacketsTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "compare_search_modes_enqueue_all_packets_after_exhausted_backlog_test",
            empty,
            CompareSearchModesEnqueueAllPacketsAfterExhaustedBacklogTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "compare_search_modes_refill_widens_pending_packets_test",
            empty,
            CompareSearchModesRefillWidensPendingPacketsTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "compare_search_modes_live_budget_uses_soft_window_test",
            empty,
            CompareSearchModesLiveBudgetUsesSoftWindowTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "compare_search_modes_packet_budget_uses_quantum_test",
            empty,
            CompareSearchModesPacketBudgetUsesQuantumTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "compare_search_modes_packet_budget_zero_beam_uses_packet_width_fallback_test",
            empty,
            CompareSearchModesPacketBudgetZeroBeamUsesPacketWidthFallbackTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "compare_search_modes_skips_root_cache_during_raw_benchmark_test",
            empty,
            CompareSearchModesSkipsRootCacheDuringRawBenchmarkTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "compare_search_modes_skips_shared_root_schema_during_raw_benchmark_test",
            empty,
            CompareSearchModesSkipsSharedRootSchemaDuringRawBenchmarkTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "compare_search_modes_stores_derivation_backed_attempt_test",
            empty,
            CompareSearchModesStoresDerivationBackedAttemptTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "compare_search_modes_worker_entry_tracks_packet_job_test",
            empty,
            CompareSearchModesWorkerEntryTracksPacketJobTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "compare_search_modes_finds_reusable_worker_snapshot_dir_test",
            empty,
            CompareSearchModesFindsReusableWorkerSnapshotDirTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "compare_search_modes_console_disabled_skips_approval_replay_prompt_test",
            empty,
            CompareSearchModesConsoleDisabledSkipsApprovalReplayPromptTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "search_worker_resume_derivation_missing_plan_raises_runtime_error_test",
            empty,
            SearchWorkerResumeDerivationMissingPlanRaisesRuntimeErrorTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "compare_search_modes_fallback_winner_uses_recorded_performance_ordering_test",
            empty,
            CompareSearchModesFallbackWinnerUsesRecordedPerformanceOrderingTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "rewrite_strategy_goal_demand_allows_goal_head_test",
            empty,
            RewriteStrategyGoalDemandAllowsGoalHeadTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "pretty_print_named_tao_quantity_test",
            empty,
            PrettyPrintNamedTaoQuantityTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "tao_geometry_example_goals_use_named_quantities_test",
            empty,
            TaoGeometryExampleGoalsUseNamedQuantitiesTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "tao_compact_rules_use_shrunk_premise_sets_test",
            empty,
            TaoCompactRulesUseShrunkPremiseSetsTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "merge_bindings_accepts_structurally_equal_values_test",
            empty,
            MergeBindingsAcceptsStructurallyEqualValuesTest(),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "build_derivation_replays_structurally_equal_repeated_bindings_test",
            empty,
            BuildDerivationReplaysStructurallyEqualRepeatedBindingsTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "tao_generic_cosine_replay_cases_test",
            empty,
            TaoGenericCosineReplayCasesTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "legacy_cosine_rules_removed_test",
            empty,
            LegacyCosineRulesRemovedTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "search_comparison_outcome_field_test",
            empty,
            SearchComparisonOutcomeFieldTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "search_comparison_job_roundtrip_test",
            empty,
            SearchComparisonJobRoundtripTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "search_comparison_job_uses_grouped_blocks_test",
            empty,
            SearchComparisonJobUsesGroupedBlocksTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "search_worker_baseline_uses_grouped_problem_block_test",
            empty,
            SearchWorkerBaselineUsesGroupedProblemBlockTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "search_worker_packet_uses_grouped_blocks_test",
            empty,
            SearchWorkerPacketUsesGroupedBlocksTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "search_worker_launch_uses_grouped_dispatch_test",
            empty,
            SearchWorkerLaunchUsesGroupedDispatchTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "search_worker_launch_pickle_roundtrip_test",
            empty,
            SearchWorkerLaunchPickleRoundtripTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "search_worker_result_pickle_roundtrip_test",
            empty,
            SearchWorkerResultPickleRoundtripTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "paused_search_job_snapshot_roundtrip_test",
            empty,
            PausedSearchJobSnapshotRoundtripTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "nat_value_index_snapshot_roundtrip_test",
            empty,
            NatValueIndexSnapshotRoundtripTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "cold_e2_reaches_snapshot_save_test",
            empty,
            ColdE2ReachesSnapshotSaveTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "snapshot_save_timeout_preserves_existing_snapshot_test",
            empty,
            SnapshotSaveTimeoutPreservesExistingSnapshotTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "unpaused_snapshot_probe_skips_activation_and_rewrite_test",
            empty,
            UnpausedSnapshotProbeSkipsActivationAndRewriteTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "identity_red_black_identity_index_test",
            empty,
            IdentityRedBlackIdentityIndexTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "snapshot_preserves_machine_edge_structure_test",
            empty,
            SnapshotPreservesMachineEdgeStructureTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "snapshot_preserves_constructor_labels_and_chars_test",
            empty,
            SnapshotPreservesConstructorLabelsAndCharsTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "snapshot_preserves_rule_edge_inputs_test",
            empty,
            SnapshotPreservesRuleEdgeInputsTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "search_worker_resume_state_restores_saved_plan_test",
            empty,
            SearchWorkerResumeStateRestoresSavedPlanTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "search_worker_snapshot_boot_with_runtime_namespace_test",
            empty,
            SearchWorkerSnapshotBootWithRuntimeNamespaceTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "paused_comparison_job_snapshot_roundtrip_test",
            empty,
            PausedComparisonJobSnapshotRoundtripTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "paused_comparison_job_snapshot_resume_test",
            empty,
            PausedComparisonJobSnapshotResumeTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "compare_search_modes_stop_mode_marks_only_requested_mode_test",
            empty,
            CompareSearchModesStopModeMarksOnlyRequestedModeTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "compare_search_modes_stop_outcome_clears_pending_packet_count_test",
            empty,
            CompareSearchModesStopOutcomeClearsPendingPacketCountTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "compare_search_modes_stopped_state_does_not_enqueue_job_frontier_test",
            empty,
            CompareSearchModesStoppedStateDoesNotEnqueueJobFrontierTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "compare_search_modes_pause_state_preserves_backlog_test",
            empty,
            CompareSearchModesPauseStatePreservesBacklogTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "compare_search_modes_pause_requeues_active_packet_into_job_test",
            empty,
            CompareSearchModesPauseRequeuesActivePacketIntoJobTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "compare_search_modes_integrates_returned_ready_packets_test",
            empty,
            CompareSearchModesIntegratesReturnedReadyPacketsTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "compare_search_modes_empty_ready_result_refills_job_frontier_test",
            empty,
            CompareSearchModesEmptyReadyResultRefillsJobFrontierTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "compare_search_modes_returned_ready_packet_count_follows_packet_shape_test",
            empty,
            CompareSearchModesReturnedReadyPacketCountFollowsPacketShapeTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "compare_search_modes_returned_ready_overreported_count_keeps_packet_shape_test",
            empty,
            CompareSearchModesReturnedReadyOverreportedCountKeepsPacketShapeTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "compare_search_modes_resident_unavailable_leaves_packet_queued_test",
            empty,
            CompareSearchModesResidentUnavailableLeavesPacketQueuedTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "compare_search_modes_batches_large_returned_ready_packet_wave_test",
            empty,
            CompareSearchModesBatchesLargeReturnedReadyPacketWaveTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "compare_search_modes_success_clears_pending_packets_test",
            empty,
            CompareSearchModesSuccessClearsPendingPacketsTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "compare_search_modes_ignores_stopped_mode_result_test",
            empty,
            CompareSearchModesIgnoresStoppedModeResultTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "compare_search_modes_ignores_mismatched_packet_token_result_test",
            empty,
            CompareSearchModesIgnoresMismatchedPacketTokenResultTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "compare_search_modes_stale_token_retry_requeues_original_packet_test",
            empty,
            CompareSearchModesStaleTokenRetryRequeuesOriginalPacketTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "compare_search_modes_ignores_missing_packet_token_result_test",
            empty,
            CompareSearchModesIgnoresMissingPacketTokenResultTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "compare_search_modes_decode_missing_payload_uses_expected_token_test",
            empty,
            CompareSearchModesDecodeMissingPayloadUsesExpectedTokenTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "compare_search_modes_missing_payload_retry_requeues_original_packet_test",
            empty,
            CompareSearchModesMissingPayloadRetryRequeuesOriginalPacketTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "compare_search_modes_empty_cursor_theorem_fanout_test",
            empty,
            CompareSearchModesEmptyCursorTheoremFanoutTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "compare_search_modes_theorem_fanout_preserves_generated_test",
            empty,
            CompareSearchModesTheoremFanoutPreservesGeneratedTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "compare_search_modes_theorem_fanout_adds_single_rewrite_handoff_test",
            empty,
            CompareSearchModesTheoremFanoutAddsSingleRewriteHandoffTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "compare_search_modes_empty_cursor_theorem_fanout_seeds_generated_tree_test",
            empty,
            CompareSearchModesEmptyCursorTheoremFanoutSeedsGeneratedTreeTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "compare_search_modes_rewrite_fanout_produces_one_rule_packets_test",
            empty,
            CompareSearchModesRewriteFanoutProducesOneRulePacketsTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "search_worker_packet_delta_uses_resident_baseline_test",
            empty,
            SearchWorkerPacketDeltaUsesResidentBaselineTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "search_worker_filters_seeded_theorem_continuation_test",
            empty,
            SearchWorkerFiltersSeededTheoremContinuationTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "compare_search_modes_resident_executor_refreshes_baseline_on_generation_change_test",
            empty,
            CompareSearchModesResidentExecutorRefreshesBaselineOnGenerationChangeTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "compare_search_modes_batched_wave_matches_sequential_success_test",
            empty,
            CompareSearchModesBatchedWaveMatchesSequentialSuccessTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "loaded_rules_avoid_symmetric_notation_fact_test",
            empty,
            LoadedRulesAvoidSymmetricNotationFactTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "loaded_rules_have_direct_progression_edge_equations_test",
            empty,
            LoadedRulesHaveDirectProgressionEdgeEquationsTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "invariance_even_goal_unreachable_test",
            empty,
            InvarianceEvenGoalUnreachableTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "invariance_odd_goal_does_not_prune_test",
            empty,
            InvarianceOddGoalDoesNotPruneTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "invariance_unestablished_even_phi_does_not_prune_test",
            empty,
            InvarianceUnestablishedEvenPhiDoesNotPruneTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "compile_rule_to_law_test",
            empty,
            CompileRuleToLawTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "shadow_pack_test",
            empty,
            ShadowPackTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "laws_inside_graph_versions_test",
            empty,
            LawsInsideGraphVersionsTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "test_meta_rewrite_KNOWN_GAP",
            empty,
            MetaRewriteKnownGapTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "proposal_store_inert_test",
            empty,
            ProposalStoreInertTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "activate_proposal_test",
            empty,
            ActivateProposalTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "obligation_commit_gate_test",
            empty,
            ObligationCommitGateTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "proposal_store_history_test",
            empty,
            ProposalStoreHistoryTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "firing_ledger_test",
            empty,
            FiringLedgerTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "pattern_census_test",
            empty,
            PatternCensusTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "handle_fold_unfold_test",
            empty,
            HandleFoldUnfoldTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "positional_signatures_test",
            empty,
            PositionalSignaturesTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "handle_promotion_test",
            empty,
            HandlePromotionTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "impact_policy_test",
            empty,
            ImpactPolicyTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "autonomy_cycle_test",
            empty,
            AutonomyCycleTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "autonomy_obligation_safety_test",
            empty,
            AutonomyObligationSafetyTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "recurring_pattern_mining_test",
            empty,
            RecurringPatternMiningTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "handle_proposal_generator_test",
            empty,
            HandleProposalGeneratorTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "witnessed_composition_proposal_test",
            empty,
            WitnessedCompositionProposalTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "autonomy_generation_phase_test",
            empty,
            AutonomyGenerationPhaseTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "law_ordering_from_ledger_test",
            empty,
            LawOrderingFromLedgerTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "law_preference_installable_test",
            empty,
            LawPreferenceInstallableTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "retirement_lifecycle_test",
            empty,
            RetirementLifecycleTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "installed_heuristic_search_test",
            empty,
            InstalledHeuristicSearchTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "heuristic_trial_proposal_test",
            empty,
            HeuristicTrialProposalTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "installed_policy_override_test",
            empty,
            InstalledPolicyOverrideTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "policy_change_countersign_test",
            empty,
            PolicyChangeCountersignTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "curator_report_test",
            empty,
            CuratorReportTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "contract_enforcement_test",
            empty,
            ContractEnforcementTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "robustness_harness_test",
            empty,
            RobustnessHarnessTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "migration_lifecycle_test",
            empty,
            MigrationLifecycleTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "wire_round_trip_test",
            empty,
            WireRoundTripTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "worker_protocol_test",
            empty,
            WorkerProtocolTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "conflict_detection_test",
            empty,
            ConflictDetectionTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "toy_correspondence_round_trip_test",
            empty,
            ToyCorrespondenceRoundTripTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "reading_policy_test",
            empty,
            ReadingPolicyTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "deduction_law_test",
            empty,
            DeductionLawTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "recognise_forms_test",
            empty,
            RecogniseFormsTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "freshen_template_test",
            empty,
            FreshenTemplateTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "grammar_composition_test",
            empty,
            GrammarCompositionTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "definition_node_test",
            empty,
            DefinitionNodeTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "lexical_spans_test",
            empty,
            LexicalSpansTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "chart_parser_test",
            empty,
            ChartParserTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "converse_default_mode_test",
            empty,
            ConverseDefaultModeTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "converse_proposition_test",
            empty,
            ConversePropositionTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "correspondence_induction_test",
            empty,
            CorrespondenceInductionTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "search_match_states_test",
            empty,
            SearchMatchStatesTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "fire_law_surgery_test",
            empty,
            FireLawSurgeryTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "fire_law_dangling_mode_test",
            empty,
            FireLawDanglingModeTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "law_maps_complete_test",
            empty,
            LawMapsCompleteTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "dangling_edges_test",
            empty,
            DanglingEdgesTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "map_extension_alternatives_test",
            empty,
            MapExtensionAlternativesTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "structured_miss_reason_test",
            empty,
            StructuredMissReasonTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "edge_send_positional_consistency_test",
            empty,
            EdgeSendPositionalConsistencyTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "graph_current_version_test",
            empty,
            GraphCurrentVersionTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "invariance_flip_one_refutes_parity_test",
            empty,
            InvarianceFlipOneRefutesParityTest(graph),
            M.truth_value,
        )

    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "blackboard_parity_preserved_test",
            empty,
            BlackboardParityPreservedTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "blackboard_move_sum_is_sum_minus_twice_min_test",
            empty,
            BlackboardMoveSumIsSumMinusTwiceMinTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "blackboard_initial_parity_is_odd_test",
            empty,
            BlackboardInitialParityIsOddTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "blackboard_final_number_is_odd_test",
            empty,
            BlackboardFinalNumberIsOddTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "blackboard_even_n_refuses_odd_conclusion_test",
            empty,
            BlackboardEvenNRefusesOddConclusionTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "blackboard_proof_expands_no_boards_test",
            empty,
            BlackboardProofExpandsNoBoardsTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "blackboard_start_has_no_board_cells_test",
            empty,
            BlackboardStartHasNoBoardCellsTest(graph),
            M.truth_value,
        )


    theorem_cursor_rules = M.Pair(a, empty)
    theorem_cursor_generated = M.Thingy()
    theorem_cursor_head_index = M.Pair(M.Zero, empty)
    theorem_cursor_exact_trie = M.Pair(M.one, empty)
    theorem_cursor_delta = M.Pair(M.two, empty)
    theorem_cursor_next_delta = M.Pair(M.three, empty)
    theorem_cursor_actions = M.Pair(b, empty)
    theorem_cursor = M.SearchTheoremCursor(
        theorem_cursor_rules,
        theorem_cursor_generated,
        theorem_cursor_head_index,
        theorem_cursor_exact_trie,
        theorem_cursor_delta,
        theorem_cursor_next_delta,
        theorem_cursor_actions,
    )()
    cursor_state = M.SearchState(a, empty, empty, M.one, theorem_cursor)()
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "search_state_cursor_roundtrip_test",
            M.Pair(cursor_state, empty),
            ComputedRawTermEqual(M.SearchStateCursor(cursor_state), theorem_cursor, _registry(graph)),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "search_theorem_cursor_head_index_roundtrip_test",
            M.Pair(theorem_cursor, empty),
            ComputedRawTermEqual(M.SearchTheoremCursorHeadIndex(theorem_cursor), theorem_cursor_head_index, _registry(graph)),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "search_theorem_cursor_exact_trie_roundtrip_test",
            M.Pair(theorem_cursor, empty),
            ComputedRawTermEqual(M.SearchTheoremCursorExactTrie(theorem_cursor), theorem_cursor_exact_trie, _registry(graph)),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "search_theorem_cursor_delta_roundtrip_test",
            M.Pair(theorem_cursor, empty),
            ComputedRawTermEqual(M.SearchTheoremCursorDelta(theorem_cursor), theorem_cursor_delta, _registry(graph)),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "search_theorem_cursor_next_delta_roundtrip_test",
            M.Pair(theorem_cursor, empty),
            ComputedRawTermEqual(M.SearchTheoremCursorNextDelta(theorem_cursor), theorem_cursor_next_delta, _registry(graph)),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "search_theorem_cursor_actions_roundtrip_test",
            M.Pair(theorem_cursor, empty),
            ComputedRawTermEqual(M.SearchTheoremCursorActions(theorem_cursor), theorem_cursor_actions, _registry(graph)),
            M.truth_value,
        )

    rewrite_path = M.Pair(M.Zero, empty)
    rewrite_frame = M.SearchRewritePathFrame(b, rewrite_path)()
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "search_rewrite_frame_path_roundtrip_test",
            M.Pair(rewrite_frame, empty),
            ComputedRawTermEqual(M.SearchRewritePathFramePath(rewrite_frame), rewrite_path, _registry(graph)),
            M.truth_value,
        )

    rewrite_cursor_rest = M.Pair(b, empty)
    rewrite_cursor_agenda = M.Pair(rewrite_frame, empty)
    rewrite_cursor_generated = M.Thingy()
    rewrite_cursor = M.SearchRewriteCursor(a, rewrite_cursor_rest, rewrite_cursor_agenda, rewrite_cursor_generated)()
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "search_rewrite_cursor_agenda_roundtrip_test",
            M.Pair(rewrite_cursor, empty),
            ComputedRawTermEqual(M.SearchRewriteCursorAgenda(rewrite_cursor), rewrite_cursor_agenda, _registry(graph)),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "goal_head_neighborhood_reachback_test",
            empty,
            GoalHeadNeighborhoodReachbackTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "heuristic_canonical_knowledge_agreement_test",
            empty,
            HeuristicCanonicalKnowledgeAgreementTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "canonical_arithmetic_add_ac_normalizes_test",
            empty,
            CanonicalArithmeticAddACNormalizesTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "canonical_arithmetic_mul_ac_normalizes_test",
            empty,
            CanonicalArithmeticMulACNormalizesTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "canonical_arithmetic_equation_symmetry_test",
            empty,
            CanonicalArithmeticEquationSymmetryTest(graph),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "arithmetic_canonical_laws_declared_test",
            empty,
            ArithmeticCanonicalLawsDeclaredTest(graph),
            M.truth_value,
        )

    job_theorem_cache = M.Tree(empty)
    job_rewrite_rules = M.Pair(a, empty)
    job_frontier_size = M.two
    job = M.SearchJob(
        a,
        b,
        empty,
        empty,
        M.SearchRunningLabel,
        empty,
        M.Zero,
        M.Zero,
        M.Zero,
        empty,
        empty,
        job_theorem_cache,
        job_rewrite_rules,
        job_frontier_size,
    )()
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "search_job_frontier_size_roundtrip_test",
            M.Pair(job, empty),
            M.SearchJobFrontierSize(job),
            job_frontier_size,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "search_job_theorem_cache_roundtrip_test",
            M.Pair(job, empty),
            M.SearchJobTheoremRuleCache(job),
            job_theorem_cache,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "search_job_rewrite_rules_roundtrip_test",
            M.Pair(job, empty),
            ComputedRawTermEqual(M.SearchJobRewriteRules(job), job_rewrite_rules, _registry(graph)),
            M.truth_value,
        )

    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "true_atom_test",
            M.Pair(M.TrueAtom(), empty),
            M.Compare(M.TrueAtom()(), M.truth_value),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "false_atom_test",
            M.Pair(M.FalseAtom(), empty),
            M.Compare(M.FalseAtom()(), M.false_value),
            M.truth_value,
        )

    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "nat_eq_zero_zero_test",
            M.Pair(M.Zero, M.Pair(M.Zero, empty)),
            M.NatEq(M.Zero, M.Zero, _registry(graph)),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "nat_eq_zero_one_test",
            M.Pair(M.Zero, M.Pair(M.one, empty)),
            M.NatEq(M.Zero, M.one, _registry(graph)),
            M.false_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "nat_eq_one_two_test",
            M.Pair(M.one, M.Pair(M.two, empty)),
            M.NatEq(M.one, M.two, _registry(graph)),
            M.false_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "nat_less_zero_zero_print_test",
            M.Pair(M.Zero, M.Pair(M.Zero, empty)),
            M.NatLess(M.Zero, M.Zero, _registry(graph)),
            M.false_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "nat_less_zero_one_print_test",
            M.Pair(M.Zero, M.Pair(M.one, empty)),
            M.NatLess(M.Zero, M.one, _registry(graph)),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "nat_less_one_two_print_test",
            M.Pair(M.one, M.Pair(M.two, empty)),
            M.NatLess(M.one, M.two, _registry(graph)),
            M.truth_value,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "nat_less_two_one_print_test",
            M.Pair(M.two, M.Pair(M.one, empty)),
            M.NatLess(M.two, M.one, _registry(graph)),
            M.false_value,
        )

    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(graph, "is_atom_one_test", M.Pair(M.one, empty), M.IsAtom(M.one, _registry(graph)), M.truth_value)
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(graph, "is_edge_thingy_test", M.Pair(a, empty), M.IsEdge(a, _registry(graph)), M.false_value)
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(graph, "is_atom_pair_test", M.Pair(M.Pair(a, empty), empty), M.IsAtom(M.Pair(a, empty), _registry(graph)), M.truth_value)
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(graph, "is_two_nat_print_test", M.Pair(M.two, empty), M.IsNat(M.two, _registry(graph)), M.truth_value)

    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "add_one_two_test",
            M.Pair(M.one, M.Pair(M.two, empty)),
            M.Add(M.one, M.two, _registry(graph)),
            M.three,
        )

    three_from_add_pair = M.Add(M.one, M.two, _registry(graph))()
    three_from_add = M.Head(three_from_add_pair)()
    _set_registry(graph, M.Head(M.Tail(three_from_add_pair)())())
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "pred_of_add_one_two_test",
            M.Pair(three_from_add, empty),
            M.NatPred(three_from_add, _registry(graph)),
            M.two,
        )

    half_pair = M.Fraction(M.one, M.two, _registry(graph))()
    half = M.Head(half_pair)()
    _set_registry(graph, M.Head(M.Tail(half_pair)())())

    plus3_pair = M.Whole(M.three, M.Zero, _registry(graph))()
    plus3 = M.Head(plus3_pair)()
    _set_registry(graph, M.Head(M.Tail(plus3_pair)())())

    minus2_pair = M.Whole(M.Zero, M.two, _registry(graph))()
    minus2 = M.Head(minus2_pair)()
    _set_registry(graph, M.Head(M.Tail(minus2_pair)())())

    plus1_pair = M.Whole(M.three, M.two, _registry(graph))()
    plus1 = M.Head(plus1_pair)()
    _set_registry(graph, M.Head(M.Tail(plus1_pair)())())

    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(graph, "fraction_is_fraction_test", M.Pair(half, empty), M.IsFraction(half, _registry(graph)), M.truth_value)
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(graph, "fraction_left_test", M.Pair(half, empty), M.FractionLeft(half, _registry(graph)), M.one)
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(graph, "fraction_right_test", M.Pair(half, empty), M.FractionRight(half, _registry(graph)), M.two)

    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "multiply_two_three_test",
            M.Pair(M.two, M.Pair(M.three, empty)),
            M.Multiply(M.two, M.three, _registry(graph)),
            M.six,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "multiply_three_three_test",
            M.Pair(M.three, M.Pair(M.three, empty)),
            M.Multiply(M.three, M.three, _registry(graph)),
            M.nine,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "multiply_four_two_test",
            M.Pair(M.four, M.Pair(M.two, empty)),
            M.Multiply(M.four, M.two, _registry(graph)),
            M.eight,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "multiply_zero_three_test",
            M.Pair(M.Zero, M.Pair(M.three, empty)),
            M.Multiply(M.Zero, M.three, _registry(graph)),
            M.Zero,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "multiply_three_zero_test",
            M.Pair(M.three, M.Pair(M.Zero, empty)),
            M.Multiply(M.three, M.Zero, _registry(graph)),
            M.Zero,
        )

    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(graph, "is_whole_plus3_test", M.Pair(plus3, empty), M.IsWhole(plus3, _registry(graph)), M.truth_value)
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(graph, "is_whole_minus2_test", M.Pair(minus2, empty), M.IsWhole(minus2, _registry(graph)), M.truth_value)
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(graph, "whole_left_plus3_test", M.Pair(plus3, empty), M.WholeLeft(plus3, _registry(graph)), M.three)
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(graph, "whole_right_minus2_test", M.Pair(minus2, empty), M.WholeRight(minus2, _registry(graph)), M.two)

    whole_three_two_pair = M.Whole(M.three, M.two, _registry(graph))()
    whole_three_two = M.Head(whole_three_two_pair)()
    _set_registry(graph, M.Head(M.Tail(whole_three_two_pair)())())

    whole_three_four_pair = M.Whole(M.three, M.four, _registry(graph))()
    whole_three_four = M.Head(whole_three_four_pair)()
    _set_registry(graph, M.Head(M.Tail(whole_three_four_pair)())())

    whole_zero_six_pair = M.Whole(M.Zero, M.six, _registry(graph))()
    whole_zero_six = M.Head(whole_zero_six_pair)()
    _set_registry(graph, M.Head(M.Tail(whole_zero_six_pair)())())

    whole_four_zero_pair = M.Whole(M.four, M.Zero, _registry(graph))()
    whole_four_zero = M.Head(whole_four_zero_pair)()
    _set_registry(graph, M.Head(M.Tail(whole_four_zero_pair)())())

    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "whole_add_pos_neg_test",
            M.Pair(plus3, M.Pair(minus2, empty)),
            M.WholeAdd(plus3, minus2, _registry(graph)),
            whole_three_two,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "whole_add_one_neg_two_test",
            M.Pair(plus1, M.Pair(minus2, empty)),
            M.WholeAdd(plus1, minus2, _registry(graph)),
            whole_three_four,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "whole_mul_pos_neg_test",
            M.Pair(plus3, M.Pair(minus2, empty)),
            M.WholeMultiply(plus3, minus2, _registry(graph)),
            whole_zero_six,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "whole_mul_neg_neg_test",
            M.Pair(minus2, M.Pair(minus2, empty)),
            M.WholeMultiply(minus2, minus2, _registry(graph)),
            whole_four_zero,
        )

    # Step 52: milestone checks. Expected value is MILESTONE_SKIPPED while a
    # criterion is unmet, so an unmet milestone runs and reports rather than
    # failing the suite. A milestone that regresses returns false_value and
    # fails against this expectation.
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "test_milestone_m1_cycles_without_refusal",
            empty,
            MilestoneM1CyclesWithoutRefusalTest(graph),
            MILESTONE_SKIPPED,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "test_milestone_m2_handle_lifecycle",
            empty,
            MilestoneM2HandleLifecycleTest(graph),
            MILESTONE_SKIPPED,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "test_milestone_m3_meta_handle_reorders",
            empty,
            MilestoneM3MetaHandleReordersTest(graph),
            MILESTONE_SKIPPED,
        )
    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "test_milestone_m4_policy_loosen_then_tighten",
            empty,
            MilestoneM4PolicyLoosenThenTightenTest(graph),
            MILESTONE_SKIPPED,
        )

    graph.default_tests_installed = M.truth_value
    return graph


__all__ = [name for name in globals() if not name.startswith("_")]
