from __future__ import annotations

import json
import os
import pickle
import queue
import shutil
import sys
import tempfile

from . import machine as M
from . import graph as Gmod
from . import heuristics as Hmod
from . import labels as Lmod
from . import matching as Xmod
from . import proof as Pmod
from . import rewrite_rules as Rmod
from . import rewrite_strategies as RSmod
from . import search as Smod
from . import theorem_rules as Theoremmod
from . import trees as Tmod
from .graph import Test
from .persistence import SnapshotCodec
from .proof import BuildDerivation, CollectRules, Rule, RulePremises, RuleReplacement
from .runtime import boot_from_snapshot, make_fresh_runtime, save_runtime
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
        term = M.Pair(
            Lmod.SideOfLabel,
            M.Pair(
                M.Pair(Lmod.SegmentLabel, M.Pair(M.Char("v"), M.Pair(M.Char("w"), empty))),
                M.Pair(M.Char("t"), empty),
            ),
        )
        snapshot = SnapshotCodec(namespace).capture_objects({"term": term})
        loaded = SnapshotCodec(namespace).load_snapshot(snapshot).roots["term"]
        self.result = RawTermEqual(loaded, term, M.AllConstructors)()
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
            self.result = M.truth_value
            if stage_text != "running-derivation":
                self.result = M.false_value
            elif M.Compare(resume_plan, M.EmptyList)() is M.truth_value:
                self.result = M.false_value
            elif RawTermEqual(resume_plan, plan, registry)() is M.false_value:
                self.result = M.false_value
            elif RawTermEqual(resume_search_cost, search_cost, registry)() is M.false_value:
                self.result = M.false_value
            elif elapsed_milliseconds != 1234:
                self.result = M.false_value
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
                M.Head(M.Head(loaded_probe._comparison_state_pending_packets(loaded_state))()),
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


def _set_registry(graph, registry):
    graph._replace_context(constructors=registry)
    return registry


def _registry(graph):
    return M.FromContextGetConstructors(graph)()


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

    _register_test(graph, "cmp1_test", M.Pair(a, M.Pair(a, empty)), M.Compare(a, a), M.truth_value)
    _register_test(graph, "cmp2_test", M.Pair(a, M.Pair(b, empty)), M.Compare(a, b), M.false_value)
    _register_test(graph, "cmp3_test", M.Pair(empty, empty), M.Compare(empty, M.EmptyList), M.truth_value)
    _register_test(graph, "cmp4_test", M.Pair(a, M.Pair(empty, empty)), M.Compare(a, empty), M.false_value)

    _register_test(
        graph,
        "nand_test",
        M.Pair(M.truth_value, M.Pair(M.truth_value, empty)),
        M.NandAtom(M.truth_value, M.truth_value),
        M.false_value,
    )
    _register_test(
        graph,
        "nat_test",
        M.Pair(M.one, M.Pair(M.two, empty)),
        M.NatLess(M.one, M.two, _registry(graph)),
        M.truth_value,
    )

    pair1_input = M.Pair(a, empty)
    pair2_input = M.Pair(a, M.Pair(b, empty))
    _register_test(graph, "count1_test", pair1_input, M.Count(pair1_input, _registry(graph)), M.one)
    _register_test(graph, "count2_test", pair2_input, M.Count(pair2_input, _registry(graph)), M.two)
    _register_test(graph, "thingy1_test", a, M.IsAtom(a, _registry(graph)), M.truth_value)

    numbers = M.Pair(M.one, M.Pair(M.two, M.Pair(M.three, empty)))
    numbers_with_zero = M.Pair(M.Zero, numbers)
    _register_test(graph, "exists_test_1", numbers, Exists(numbers, IsNonZero), M.truth_value)
    _register_test(graph, "forall_test_1", numbers, ForAll(numbers, IsNonZero), M.truth_value)
    _register_test(graph, "exists_test_2", numbers_with_zero, Exists(numbers_with_zero, IsNonZero), M.truth_value)
    _register_test(graph, "forall_test_2", numbers_with_zero, ForAll(numbers_with_zero, IsNonZero), M.false_value)

    _register_test(
        graph,
        "id_comp_test",
        M.Pair(a, M.Pair(b, empty)),
        M.IdentityCompare(a, b),
        M.false_value,
    )
    _register_test(
        graph,
        "is_one_two_test",
        M.Pair(M.one, M.Pair(M.two, empty)),
        M.NatEq(M.one, M.two, _registry(graph)),
        M.false_value,
    )
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

    _register_test(
        graph,
        "sim_pairs_test",
        M.Pair(pair1_input, M.Pair(pair3_input, empty)),
        M.CompareIn(sim_count1, sim_count2, _registry(graph)),
        M.truth_value,
    )

    _register_test(graph, "is_zero0", M.Pair(M.Zero, M.Pair(M.Zero, empty)), M.Compare(M.Zero, M.Zero), M.truth_value)
    _register_test(graph, "is_zero1", M.Pair(M.Zero, M.Pair(M.one, empty)), M.Compare(M.Zero, M.one), M.false_value)
    succ_one_pair = M.Succ(M.one, _registry(graph))()
    succ_one = M.Head(succ_one_pair)()
    _set_registry(graph, M.Head(M.Tail(succ_one_pair)())())

    pred_succ_pair = M.NatPred(succ_one, _registry(graph))()
    pred_succ = M.Head(pred_succ_pair)()
    _set_registry(graph, M.Head(M.Tail(pred_succ_pair)())())

    _register_test(
        graph,
        "pred_succ_test",
        M.Pair(pred_succ, M.Pair(M.one, empty)),
        M.CompareIn(pred_succ, M.one, _registry(graph)),
        M.truth_value,
    )
    _register_test(
        graph,
        "zero_less_zero",
        M.Pair(M.Zero, M.Pair(M.Zero, empty)),
        M.NatLess(M.Zero, M.Zero, _registry(graph)),
        M.false_value,
    )
    _register_test(graph, "is_two_nat", M.Pair(M.two, empty), M.IsNat(M.two, _registry(graph)), M.truth_value)

    name_x = M.Thingy()
    var_x = M.Pair(M.VarTag, M.Pair(name_x, empty))
    pattern1 = M.Pair(var_x, empty)
    target1 = M.Pair(M.Thingy(), empty)
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
    _register_test(
        graph,
        "match2_test",
        M.Pair(pattern2, M.Pair(target2, empty)),
        M.Match(pattern2, target2),
        M.truth_value,
    )

    pattern3 = M.Pair(var_x, empty)
    target3 = M.Pair(M.Pair(M.Thingy(), empty), empty)
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
    _register_test(
        graph,
        "rewrite_test",
        M.Pair(pattern3, M.Pair(var_x, M.Pair(rewrite_target, empty))),
        M.Rewrite(rewrite_rule, rewrite_target, _registry(graph)),
        target_head,
    )

    _register_test(
        graph,
        "comparison_prompt_abort_test",
        empty,
        ComparisonPromptAbortTest(),
        M.truth_value,
    )

    _register_test(
        graph,
        "search_structural_key_equality_test",
        empty,
        SearchStructuralKeyEqualityTest(),
        M.truth_value,
    )
    _register_test(
        graph,
        "shared_exact_key_vocabulary_test",
        empty,
        SharedExactKeyVocabularyTest(),
        M.truth_value,
    )
    _register_test(
        graph,
        "opaque_exact_key_uses_atom_key_test",
        empty,
        OpaqueExactKeyUsesAtomKeyTest(),
        M.truth_value,
    )
    _register_test(
        graph,
        "tree_lookup_uses_structural_keys_test",
        empty,
        TreeLookupUsesStructuralKeysTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "tree_lookup_uses_index_buckets_test",
        empty,
        TreeLookupUsesIndexBucketsTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "legacy_tree_lookup_remains_readable_test",
        empty,
        LegacyTreeLookupRemainsReadableTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "tree_insert_migrates_legacy_tree_test",
        empty,
        TreeInsertMigratesLegacyTreeTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "getconstructor_sees_patricia_tree_terms_test",
        empty,
        GetConstructorSeesPatriciaTreeTermsTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "comparein_sees_patricia_tree_terms_test",
        empty,
        CompareInSeesPatriciaTreeTermsTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "comparein_sees_tree_wrapper_test",
        empty,
        CompareInSeesTreeWrapperTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "search_prompt_cost_step_builds_hundred_test",
        empty,
        SearchPromptCostStepBuildsHundredTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "compare_search_modes_builds_deep_root_wave_shards_without_recursion_test",
        empty,
        CompareSearchModesBuildsDeepRootWaveShardsWithoutRecursionTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "compare_search_modes_resident_executor_ready_handshake_test",
        empty,
        CompareSearchModesResidentExecutorReadyHandshakeTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "compare_search_modes_root_wave_uses_resident_executor_test",
        empty,
        CompareSearchModesRootWaveUsesResidentExecutorTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "compare_search_modes_root_wave_requires_resident_executor_test",
        empty,
        CompareSearchModesRootWaveRequiresResidentExecutorTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "compare_search_modes_fill_warms_resident_pool_before_root_wave_test",
        empty,
        CompareSearchModesFillWarmsResidentPoolBeforeRootWaveTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "compare_search_modes_root_wave_retries_failed_shard_on_resident_test",
        empty,
        CompareSearchModesRootWaveRetriesFailedShardOnResidentTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "compare_search_modes_root_wave_replaces_exhausted_resident_test",
        empty,
        CompareSearchModesRootWaveReplacesExhaustedResidentTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "compare_search_modes_root_wave_seeds_single_rewrite_handoff_test",
        empty,
        CompareSearchModesRootWaveSeedsSingleRewriteHandoffTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "compare_search_modes_root_wave_records_empty_expansion_test",
        empty,
        CompareSearchModesRootWaveRecordsEmptyExpansionTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "search_theorem_cursor_skips_deep_stale_rule_runs_without_recursion_test",
        empty,
        SearchTheoremCursorSkipsDeepStaleRuleRunsWithoutRecursionTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "compare_search_modes_packetizes_non_root_frontier_test",
        empty,
        CompareSearchModesPacketizesNonRootFrontierTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "compare_search_modes_packetizes_wide_frontier_in_chunks_test",
        empty,
        CompareSearchModesPacketizesWideFrontierInChunksTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "compare_search_modes_prunes_packets_after_best_attempt_test",
        empty,
        CompareSearchModesPrunesPacketsAfterBestAttemptTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "compare_search_modes_fresh_root_jobs_packetize_whole_state_test",
        empty,
        CompareSearchModesFreshRootJobsPacketizeWholeStateTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "compare_search_modes_merges_packet_job_test",
        empty,
        CompareSearchModesMergesPacketJobTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "search_tree_delta_skips_structurally_equal_trees_test",
        empty,
        SearchTreeDeltaSkipsStructurallyEqualTreesTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "search_patricia_lookup_uses_structural_keys_test",
        empty,
        SearchPatriciaLookupUsesStructuralKeysTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "search_tree_delta_skips_structurally_equal_patricia_trees_test",
        empty,
        SearchTreeDeltaSkipsStructurallyEqualPatriciaTreesTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "search_tree_delta_skips_equal_content_different_shape_trees_test",
        empty,
        SearchTreeDeltaSkipsEqualContentDifferentShapeTreesTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "tree_insert_deep_pair_lookup_avoids_recursion_test",
        empty,
        TreeInsertDeepPairLookupAvoidsRecursionTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "compare_search_modes_drops_exhausted_pending_packets_test",
        empty,
        CompareSearchModesDropsExhaustedPendingPacketsTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "compare_search_modes_enqueue_all_packets_after_exhausted_backlog_test",
        empty,
        CompareSearchModesEnqueueAllPacketsAfterExhaustedBacklogTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "compare_search_modes_refill_widens_pending_packets_test",
        empty,
        CompareSearchModesRefillWidensPendingPacketsTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "compare_search_modes_live_budget_uses_soft_window_test",
        empty,
        CompareSearchModesLiveBudgetUsesSoftWindowTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "compare_search_modes_packet_budget_uses_quantum_test",
        empty,
        CompareSearchModesPacketBudgetUsesQuantumTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "compare_search_modes_packet_budget_zero_beam_uses_packet_width_fallback_test",
        empty,
        CompareSearchModesPacketBudgetZeroBeamUsesPacketWidthFallbackTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "compare_search_modes_skips_root_cache_during_raw_benchmark_test",
        empty,
        CompareSearchModesSkipsRootCacheDuringRawBenchmarkTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "compare_search_modes_skips_shared_root_schema_during_raw_benchmark_test",
        empty,
        CompareSearchModesSkipsSharedRootSchemaDuringRawBenchmarkTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "compare_search_modes_stores_derivation_backed_attempt_test",
        empty,
        CompareSearchModesStoresDerivationBackedAttemptTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "compare_search_modes_worker_entry_tracks_packet_job_test",
        empty,
        CompareSearchModesWorkerEntryTracksPacketJobTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "compare_search_modes_finds_reusable_worker_snapshot_dir_test",
        empty,
        CompareSearchModesFindsReusableWorkerSnapshotDirTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "rewrite_strategy_goal_demand_allows_goal_head_test",
        empty,
        RewriteStrategyGoalDemandAllowsGoalHeadTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "search_comparison_outcome_field_test",
        empty,
        SearchComparisonOutcomeFieldTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "search_comparison_job_roundtrip_test",
        empty,
        SearchComparisonJobRoundtripTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "search_comparison_job_uses_grouped_blocks_test",
        empty,
        SearchComparisonJobUsesGroupedBlocksTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "search_worker_baseline_uses_grouped_problem_block_test",
        empty,
        SearchWorkerBaselineUsesGroupedProblemBlockTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "search_worker_packet_uses_grouped_blocks_test",
        empty,
        SearchWorkerPacketUsesGroupedBlocksTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "search_worker_launch_uses_grouped_dispatch_test",
        empty,
        SearchWorkerLaunchUsesGroupedDispatchTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "search_worker_launch_pickle_roundtrip_test",
        empty,
        SearchWorkerLaunchPickleRoundtripTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "search_worker_result_pickle_roundtrip_test",
        empty,
        SearchWorkerResultPickleRoundtripTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "paused_search_job_snapshot_roundtrip_test",
        empty,
        PausedSearchJobSnapshotRoundtripTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "nat_value_index_snapshot_roundtrip_test",
        empty,
        NatValueIndexSnapshotRoundtripTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "snapshot_preserves_machine_edge_structure_test",
        empty,
        SnapshotPreservesMachineEdgeStructureTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "snapshot_preserves_constructor_labels_and_chars_test",
        empty,
        SnapshotPreservesConstructorLabelsAndCharsTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "snapshot_preserves_rule_edge_inputs_test",
        empty,
        SnapshotPreservesRuleEdgeInputsTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "search_worker_resume_state_restores_saved_plan_test",
        empty,
        SearchWorkerResumeStateRestoresSavedPlanTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "search_worker_snapshot_boot_with_runtime_namespace_test",
        empty,
        SearchWorkerSnapshotBootWithRuntimeNamespaceTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "paused_comparison_job_snapshot_roundtrip_test",
        empty,
        PausedComparisonJobSnapshotRoundtripTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "paused_comparison_job_snapshot_resume_test",
        empty,
        PausedComparisonJobSnapshotResumeTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "compare_search_modes_stop_mode_marks_only_requested_mode_test",
        empty,
        CompareSearchModesStopModeMarksOnlyRequestedModeTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "compare_search_modes_stop_outcome_clears_pending_packet_count_test",
        empty,
        CompareSearchModesStopOutcomeClearsPendingPacketCountTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "compare_search_modes_stopped_state_does_not_enqueue_job_frontier_test",
        empty,
        CompareSearchModesStoppedStateDoesNotEnqueueJobFrontierTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "compare_search_modes_pause_state_preserves_backlog_test",
        empty,
        CompareSearchModesPauseStatePreservesBacklogTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "compare_search_modes_pause_requeues_active_packet_into_job_test",
        empty,
        CompareSearchModesPauseRequeuesActivePacketIntoJobTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "compare_search_modes_integrates_returned_ready_packets_test",
        empty,
        CompareSearchModesIntegratesReturnedReadyPacketsTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "compare_search_modes_empty_ready_result_refills_job_frontier_test",
        empty,
        CompareSearchModesEmptyReadyResultRefillsJobFrontierTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "compare_search_modes_returned_ready_packet_count_follows_packet_shape_test",
        empty,
        CompareSearchModesReturnedReadyPacketCountFollowsPacketShapeTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "compare_search_modes_returned_ready_overreported_count_keeps_packet_shape_test",
        empty,
        CompareSearchModesReturnedReadyOverreportedCountKeepsPacketShapeTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "compare_search_modes_resident_unavailable_leaves_packet_queued_test",
        empty,
        CompareSearchModesResidentUnavailableLeavesPacketQueuedTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "compare_search_modes_batches_large_returned_ready_packet_wave_test",
        empty,
        CompareSearchModesBatchesLargeReturnedReadyPacketWaveTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "compare_search_modes_success_clears_pending_packets_test",
        empty,
        CompareSearchModesSuccessClearsPendingPacketsTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "compare_search_modes_ignores_stopped_mode_result_test",
        empty,
        CompareSearchModesIgnoresStoppedModeResultTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "compare_search_modes_ignores_mismatched_packet_token_result_test",
        empty,
        CompareSearchModesIgnoresMismatchedPacketTokenResultTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "compare_search_modes_stale_token_retry_requeues_original_packet_test",
        empty,
        CompareSearchModesStaleTokenRetryRequeuesOriginalPacketTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "compare_search_modes_ignores_missing_packet_token_result_test",
        empty,
        CompareSearchModesIgnoresMissingPacketTokenResultTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "compare_search_modes_decode_missing_payload_uses_expected_token_test",
        empty,
        CompareSearchModesDecodeMissingPayloadUsesExpectedTokenTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "compare_search_modes_missing_payload_retry_requeues_original_packet_test",
        empty,
        CompareSearchModesMissingPayloadRetryRequeuesOriginalPacketTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "compare_search_modes_empty_cursor_theorem_fanout_test",
        empty,
        CompareSearchModesEmptyCursorTheoremFanoutTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "compare_search_modes_theorem_fanout_preserves_generated_test",
        empty,
        CompareSearchModesTheoremFanoutPreservesGeneratedTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "compare_search_modes_theorem_fanout_adds_single_rewrite_handoff_test",
        empty,
        CompareSearchModesTheoremFanoutAddsSingleRewriteHandoffTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "compare_search_modes_empty_cursor_theorem_fanout_seeds_generated_tree_test",
        empty,
        CompareSearchModesEmptyCursorTheoremFanoutSeedsGeneratedTreeTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "compare_search_modes_rewrite_fanout_produces_one_rule_packets_test",
        empty,
        CompareSearchModesRewriteFanoutProducesOneRulePacketsTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "search_worker_packet_delta_uses_resident_baseline_test",
        empty,
        SearchWorkerPacketDeltaUsesResidentBaselineTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "search_worker_filters_seeded_theorem_continuation_test",
        empty,
        SearchWorkerFiltersSeededTheoremContinuationTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "compare_search_modes_resident_executor_refreshes_baseline_on_generation_change_test",
        empty,
        CompareSearchModesResidentExecutorRefreshesBaselineOnGenerationChangeTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "compare_search_modes_batched_wave_matches_sequential_success_test",
        empty,
        CompareSearchModesBatchedWaveMatchesSequentialSuccessTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "loaded_rules_avoid_symmetric_notation_fact_test",
        empty,
        LoadedRulesAvoidSymmetricNotationFactTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "loaded_rules_have_direct_progression_edge_equations_test",
        empty,
        LoadedRulesHaveDirectProgressionEdgeEquationsTest(graph),
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
    _register_test(
        graph,
        "search_state_cursor_roundtrip_test",
        M.Pair(cursor_state, empty),
        ComputedRawTermEqual(M.SearchStateCursor(cursor_state), theorem_cursor, _registry(graph)),
        M.truth_value,
    )
    _register_test(
        graph,
        "search_theorem_cursor_head_index_roundtrip_test",
        M.Pair(theorem_cursor, empty),
        ComputedRawTermEqual(M.SearchTheoremCursorHeadIndex(theorem_cursor), theorem_cursor_head_index, _registry(graph)),
        M.truth_value,
    )
    _register_test(
        graph,
        "search_theorem_cursor_exact_trie_roundtrip_test",
        M.Pair(theorem_cursor, empty),
        ComputedRawTermEqual(M.SearchTheoremCursorExactTrie(theorem_cursor), theorem_cursor_exact_trie, _registry(graph)),
        M.truth_value,
    )
    _register_test(
        graph,
        "search_theorem_cursor_delta_roundtrip_test",
        M.Pair(theorem_cursor, empty),
        ComputedRawTermEqual(M.SearchTheoremCursorDelta(theorem_cursor), theorem_cursor_delta, _registry(graph)),
        M.truth_value,
    )
    _register_test(
        graph,
        "search_theorem_cursor_next_delta_roundtrip_test",
        M.Pair(theorem_cursor, empty),
        ComputedRawTermEqual(M.SearchTheoremCursorNextDelta(theorem_cursor), theorem_cursor_next_delta, _registry(graph)),
        M.truth_value,
    )
    _register_test(
        graph,
        "search_theorem_cursor_actions_roundtrip_test",
        M.Pair(theorem_cursor, empty),
        ComputedRawTermEqual(M.SearchTheoremCursorActions(theorem_cursor), theorem_cursor_actions, _registry(graph)),
        M.truth_value,
    )

    rewrite_path = M.Pair(M.Zero, empty)
    rewrite_frame = M.SearchRewritePathFrame(b, rewrite_path)()
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
    _register_test(
        graph,
        "search_rewrite_cursor_agenda_roundtrip_test",
        M.Pair(rewrite_cursor, empty),
        ComputedRawTermEqual(M.SearchRewriteCursorAgenda(rewrite_cursor), rewrite_cursor_agenda, _registry(graph)),
        M.truth_value,
    )
    _register_test(
        graph,
        "goal_head_neighborhood_reachback_test",
        empty,
        GoalHeadNeighborhoodReachbackTest(graph),
        M.truth_value,
    )
    _register_test(
        graph,
        "heuristic_canonical_knowledge_agreement_test",
        empty,
        HeuristicCanonicalKnowledgeAgreementTest(graph),
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
    _register_test(
        graph,
        "search_job_frontier_size_roundtrip_test",
        M.Pair(job, empty),
        M.SearchJobFrontierSize(job),
        job_frontier_size,
    )
    _register_test(
        graph,
        "search_job_theorem_cache_roundtrip_test",
        M.Pair(job, empty),
        M.SearchJobTheoremRuleCache(job),
        job_theorem_cache,
    )
    _register_test(
        graph,
        "search_job_rewrite_rules_roundtrip_test",
        M.Pair(job, empty),
        ComputedRawTermEqual(M.SearchJobRewriteRules(job), job_rewrite_rules, _registry(graph)),
        M.truth_value,
    )

    _register_test(
        graph,
        "true_atom_test",
        M.Pair(M.TrueAtom(), empty),
        M.Compare(M.TrueAtom()(), M.truth_value),
        M.truth_value,
    )
    _register_test(
        graph,
        "false_atom_test",
        M.Pair(M.FalseAtom(), empty),
        M.Compare(M.FalseAtom()(), M.false_value),
        M.truth_value,
    )

    _register_test(
        graph,
        "nat_eq_zero_zero_test",
        M.Pair(M.Zero, M.Pair(M.Zero, empty)),
        M.NatEq(M.Zero, M.Zero, _registry(graph)),
        M.truth_value,
    )
    _register_test(
        graph,
        "nat_eq_zero_one_test",
        M.Pair(M.Zero, M.Pair(M.one, empty)),
        M.NatEq(M.Zero, M.one, _registry(graph)),
        M.false_value,
    )
    _register_test(
        graph,
        "nat_eq_one_two_test",
        M.Pair(M.one, M.Pair(M.two, empty)),
        M.NatEq(M.one, M.two, _registry(graph)),
        M.false_value,
    )
    _register_test(
        graph,
        "nat_less_zero_zero_print_test",
        M.Pair(M.Zero, M.Pair(M.Zero, empty)),
        M.NatLess(M.Zero, M.Zero, _registry(graph)),
        M.false_value,
    )
    _register_test(
        graph,
        "nat_less_zero_one_print_test",
        M.Pair(M.Zero, M.Pair(M.one, empty)),
        M.NatLess(M.Zero, M.one, _registry(graph)),
        M.truth_value,
    )
    _register_test(
        graph,
        "nat_less_one_two_print_test",
        M.Pair(M.one, M.Pair(M.two, empty)),
        M.NatLess(M.one, M.two, _registry(graph)),
        M.truth_value,
    )
    _register_test(
        graph,
        "nat_less_two_one_print_test",
        M.Pair(M.two, M.Pair(M.one, empty)),
        M.NatLess(M.two, M.one, _registry(graph)),
        M.false_value,
    )

    _register_test(graph, "is_atom_one_test", M.Pair(M.one, empty), M.IsAtom(M.one, _registry(graph)), M.truth_value)
    _register_test(graph, "is_edge_thingy_test", M.Pair(a, empty), M.IsEdge(a, _registry(graph)), M.false_value)
    _register_test(graph, "is_atom_pair_test", M.Pair(M.Pair(a, empty), empty), M.IsAtom(M.Pair(a, empty), _registry(graph)), M.truth_value)
    _register_test(graph, "is_two_nat_print_test", M.Pair(M.two, empty), M.IsNat(M.two, _registry(graph)), M.truth_value)

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

    _register_test(graph, "fraction_is_fraction_test", M.Pair(half, empty), M.IsFraction(half, _registry(graph)), M.truth_value)
    _register_test(graph, "fraction_left_test", M.Pair(half, empty), M.FractionLeft(half, _registry(graph)), M.one)
    _register_test(graph, "fraction_right_test", M.Pair(half, empty), M.FractionRight(half, _registry(graph)), M.two)

    _register_test(
        graph,
        "multiply_two_three_test",
        M.Pair(M.two, M.Pair(M.three, empty)),
        M.Multiply(M.two, M.three, _registry(graph)),
        M.six,
    )
    _register_test(
        graph,
        "multiply_three_three_test",
        M.Pair(M.three, M.Pair(M.three, empty)),
        M.Multiply(M.three, M.three, _registry(graph)),
        M.nine,
    )
    _register_test(
        graph,
        "multiply_four_two_test",
        M.Pair(M.four, M.Pair(M.two, empty)),
        M.Multiply(M.four, M.two, _registry(graph)),
        M.eight,
    )
    _register_test(
        graph,
        "multiply_zero_three_test",
        M.Pair(M.Zero, M.Pair(M.three, empty)),
        M.Multiply(M.Zero, M.three, _registry(graph)),
        M.Zero,
    )
    _register_test(
        graph,
        "multiply_three_zero_test",
        M.Pair(M.three, M.Pair(M.Zero, empty)),
        M.Multiply(M.three, M.Zero, _registry(graph)),
        M.Zero,
    )

    _register_test(graph, "is_whole_plus3_test", M.Pair(plus3, empty), M.IsWhole(plus3, _registry(graph)), M.truth_value)
    _register_test(graph, "is_whole_minus2_test", M.Pair(minus2, empty), M.IsWhole(minus2, _registry(graph)), M.truth_value)
    _register_test(graph, "whole_left_plus3_test", M.Pair(plus3, empty), M.WholeLeft(plus3, _registry(graph)), M.three)
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

    _register_test(
        graph,
        "whole_add_pos_neg_test",
        M.Pair(plus3, M.Pair(minus2, empty)),
        M.WholeAdd(plus3, minus2, _registry(graph)),
        whole_three_two,
    )
    _register_test(
        graph,
        "whole_add_one_neg_two_test",
        M.Pair(plus1, M.Pair(minus2, empty)),
        M.WholeAdd(plus1, minus2, _registry(graph)),
        whole_three_four,
    )
    _register_test(
        graph,
        "whole_mul_pos_neg_test",
        M.Pair(plus3, M.Pair(minus2, empty)),
        M.WholeMultiply(plus3, minus2, _registry(graph)),
        whole_zero_six,
    )
    _register_test(
        graph,
        "whole_mul_neg_neg_test",
        M.Pair(minus2, M.Pair(minus2, empty)),
        M.WholeMultiply(minus2, minus2, _registry(graph)),
        whole_four_zero,
    )

    graph.default_tests_installed = M.truth_value
    return graph


__all__ = [name for name in globals() if not name.startswith("_")]
