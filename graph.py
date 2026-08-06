from __future__ import annotations

from . import context as Ctx
from . import machine as M
from . import proof as P
from . import schemata as S


class Hypergraph:
    def __init__(self, constructor_registry, rep_label=M.HypergraphLabel, rep_args=None):
        if constructor_registry is None:
            constructor_registry = M.Tree(M.EmptyList)
            M.AllConstructors = M.set_all_constructors(constructor_registry)
        self.rep = M.HypergraphRep()
        self.default_tests_installed = M.false_value
        self._search_console_input = None
        self._search_disable_console = M.false_value
        self._search_disable_progress_ticker = M.false_value
        self._search_stop_help_shown = M.false_value
        self._search_comparison_prompt_guard = None
        self._search_compare_ignore_root_fast_paths = M.false_value
        self._search_compare_root_start = M.EmptyList
        self._search_compare_root_goal = M.EmptyList
        self._search_compare_discovery_mode = M.false_value
        self._search_probe_disable_applicable_shards = M.false_value
        self._search_compare_live_signature = M.EmptyList
        self._search_compare_live_start = M.EmptyList
        self._search_compare_live_goal = M.EmptyList
        self._search_compare_live_states = M.EmptyList
        self._search_compare_live_workers = M.EmptyList
        self._search_compare_live_idle_executors = M.EmptyList
        self._last_search_comparison_outcome = M.EmptyList
        # self.context = Ctx.Context(
        #     constructor_registry,
        #     M.EmptyList,
        #     M.EmptyList,
        #     M.EmptyList,
        #     M.EmptyList,
        #     M.Tree(M.EmptyList),
        #     M.Zero,
        #     M.EmptyList,
        #     M.Tree(M.EmptyList),
        #     M.Tree(M.EmptyList),
        #     M.EmptyList,
        #     M.EmptyList,
        #     M.EmptyList,
        #     M.Tree(M.EmptyList),
        # )

        self.context = Ctx.Context(
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
            M.Tree(M.EmptyList),
            M.Tree(M.EmptyList),
        )
        self._sync_from_context()

        if rep_args is None:
            rep_args = M.Pair(self.nodes, M.Pair(self.edges, M.EmptyList))

        prov = M.ConstructedBy(self.rep, rep_label, rep_args, self.constructor_registry)()
        self._replace_context(constructors=M.Head(M.Tail(prov)())())

    def _sync_from_context(self):
        self.constructor_registry = Ctx.ContextConstructors(self.context)()
        self.nodes = Ctx.ContextNodes(self.context)()
        self.edges = Ctx.ContextEdges(self.context)()
        self.our_tests = Ctx.ContextTests(self.context)()
        self.test_results = Ctx.ContextTestResults(self.context)()
        self.all_rules = Ctx.ContextAllRules(self.context)()
        self.next_rule_index = Ctx.ContextNextRuleIndex(self.context)()
        self.rule_order = Ctx.ContextRuleOrder(self.context)()
        self.derivations = Ctx.ContextDerivations(self.context)()
        self.derivation_schemata = Ctx.ContextDerivationSchemata(self.context)()
        # self.search_history = Ctx.ContextSearchHistory(self.context)()
        # self.search_comparisons = Ctx.ContextSearchComparisons(self.context)()
        # self.search_jobs = Ctx.ContextSearchJobs(self.context)()
        # self.search_memo = Ctx.ContextSearchMemo(self.context)()
        self.search_history = Ctx.ContextSearchHistory(self.context)()
        self.search_comparisons = Ctx.ContextSearchComparisons(self.context)()
        self.search_comparison_jobs = Ctx.ContextSearchComparisonJobs(self.context)()
        self.search_jobs = Ctx.ContextSearchJobs(self.context)()
        self.search_memo = Ctx.ContextSearchMemo(self.context)()
        self.nat_value_index = Ctx.ContextNatValueIndex(self.context)()
        M.AllConstructors = M.set_all_constructors(self.constructor_registry)
        M.NatValueIndex = self.nat_value_index
        return self.context

    def _replace_context(self, **changes):
        self.context = Ctx.ReplaceContext(self.context, **changes)()
        return self._sync_from_context()

    def refresh_context(self):
        return self._sync_from_context()

    def add_node(self, x):
        registry = Ctx.ContextConstructors(self.context)()
        atom_ok = M.IsAtom(x, registry)()
        edge_ok = M.IsEdge(x, registry)()
        ok = M.OrAtom(atom_ok, edge_ok)()
        if ok is not M.truth_value:
            raise TypeError("Node must be Atom, Edge, or Hypergraph representative")
        self._replace_context(nodes=M.Pair(x, Ctx.ContextNodes(self.context)()))
        return x

    def add_hypergraph(self, hg):
        hg_ok = M.IsHypergraph(hg.rep, Ctx.ContextConstructors(self.context)())()
        if hg_ok is not M.truth_value:
            raise TypeError("You're using `add_hypergraph` on something not recognised as a Hypergraph")
        self._replace_context(nodes=M.Pair(hg.rep, Ctx.ContextNodes(self.context)()))
        return hg.rep

    def add_edge(self, e):
        edge_ok = M.IsEdge(e, Ctx.ContextConstructors(self.context)())()
        if edge_ok is not M.truth_value:
            raise TypeError("Edge must be an Edge instance")
        self._replace_context(edges=M.Pair(e, Ctx.ContextEdges(self.context)()))
        return e

    def add_rule(self, rule):
        registry = Ctx.ContextConstructors(self.context)()
        key = M.Atom()
        updated_rules = M.TreeInsert(Ctx.ContextAllRules(self.context)(), key, rule, registry)()
        updated_order = M.Pair(rule, Ctx.ContextRuleOrder(self.context)())
        # Maintain a cheap rule-count in the context.
        current_index = Ctx.ContextNextRuleIndex(self.context)()
        next_pair = M.Succ(current_index, registry)()
        next_index = M.Head(next_pair)()
        registry = M.Head(M.Tail(next_pair)())()
        self._replace_context(all_rules=updated_rules, rule_order=updated_order, next_rule_index=next_index, constructors=registry)
        return rule

    def lookup_derivation(self, start, goal):
        return P.LookupDerivation(start, goal, Ctx.ContextDerivations(self.context)())()

    def add_derivation(self, start, goal, derivation):
        cached = self.lookup_derivation(start, goal)
        if M.Compare(cached, M.EmptyList)() is not M.truth_value:
            return cached

        stored_pair = P.StoreDerivation(
            start,
            goal,
            derivation,
            Ctx.ContextDerivations(self.context)(),
            Ctx.ContextConstructors(self.context)(),
        )()
        self._replace_context(derivations=M.Head(stored_pair)())
        return derivation

    def lookup_derivation_schema(self, start, goal):
        return S.LookupDerivationSchema(start, goal, Ctx.ContextDerivationSchemata(self.context)())()

    def add_derivation_schema(self, start_pattern, goal_pattern, plan):
        stored_pair = S.StoreDerivationSchema(
            start_pattern,
            goal_pattern,
            plan,
            Ctx.ContextDerivationSchemata(self.context)(),
            Ctx.ContextConstructors(self.context)(),
        )()
        self._replace_context(derivation_schemata=M.Head(stored_pair)())
        return plan

    def add_search_attempt(self, attempt):
        self._replace_context(search_history=M.Pair(attempt, Ctx.ContextSearchHistory(self.context)()))
        return attempt

    def add_search_comparison(self, comparison):
        self._replace_context(search_comparisons=M.Pair(comparison, Ctx.ContextSearchComparisons(self.context)()))
        return comparison

    def lookup_search_comparison_job(self, signature):
        from .search import LookupSearchComparisonJob

        return LookupSearchComparisonJob(signature, Ctx.ContextSearchComparisonJobs(self.context)())()

    def store_search_comparison_job(self, comparison_job):
        from .search import RemoveSearchComparisonJob, SearchComparisonJobSignature

        signature = SearchComparisonJobSignature(comparison_job)()
        remaining = RemoveSearchComparisonJob(signature, Ctx.ContextSearchComparisonJobs(self.context)())()
        self._replace_context(search_comparison_jobs=M.Pair(comparison_job, remaining))
        return comparison_job

    def remove_search_comparison_job(self, signature):
        from .search import RemoveSearchComparisonJob

        updated = RemoveSearchComparisonJob(signature, Ctx.ContextSearchComparisonJobs(self.context)())()
        self._replace_context(search_comparison_jobs=updated)
        return updated

    def lookup_search_memo(self, key):
        from .search import SearchPatriciaLookupByKey

        return SearchPatriciaLookupByKey(Ctx.ContextSearchMemo(self.context)(), key, Ctx.ContextConstructors(self.context)())()

    def store_search_memo(self, key, value):
        from .search import SearchPatriciaInsertByKey

        updated = SearchPatriciaInsertByKey(
            Ctx.ContextSearchMemo(self.context)(),
            key,
            value,
            Ctx.ContextConstructors(self.context)(),
        )()
        self._replace_context(search_memo=updated)
        return value

    def lookup_search_job(self, start, goal, heuristic):
        from .search import LookupSearchJob

        return LookupSearchJob(start, goal, heuristic, Ctx.ContextSearchJobs(self.context)())()

    def store_search_job(self, job):
        from .search import RemoveSearchJob, SearchJobGoal, SearchJobHeuristic, SearchJobStart

        start = SearchJobStart(job)()
        goal = SearchJobGoal(job)()
        heuristic = SearchJobHeuristic(job)()
        remaining = RemoveSearchJob(start, goal, heuristic, Ctx.ContextSearchJobs(self.context)())()
        self._replace_context(search_jobs=M.Pair(job, remaining))
        return job

    def remove_search_job(self, start, goal, heuristic):
        from .search import RemoveSearchJob

        updated = RemoveSearchJob(start, goal, heuristic, Ctx.ContextSearchJobs(self.context)())()
        self._replace_context(search_jobs=updated)
        return updated

    def _prepend_node_unchecked(self, x):
        self._replace_context(nodes=M.Pair(x, Ctx.ContextNodes(self.context)()))
        return x

    def _prepend_edge_unchecked(self, e):
        self._replace_context(edges=M.Pair(e, Ctx.ContextEdges(self.context)()))
        return e


class Reverse(M.Edge):
    def __init__(self, chain):
        self.result = self._rev(chain, M.EmptyList)
        super().__init__(inputs=M.Pair(chain, M.EmptyList), results=self.result)

    def _rev(self, chain, acc):
        if M.IdentityCompare(chain, M.EmptyList)() is M.truth_value:
            return acc
        return self._rev(M.Tail(chain)(), M.Pair(M.Head(chain)(), acc))

    def __call__(self):
        return self.result


class Test(Hypergraph):
    def __init__(self, graph, name, input_nodes, computation_edge, expected):
        self.graph = graph
        self.name = name
        self.input_nodes = input_nodes
        self.computation_edge = computation_edge
        self.expected = expected

        args = M.Pair(input_nodes, M.Pair(computation_edge, M.Pair(expected, M.EmptyList)))
        super().__init__(
            constructor_registry=M.FromContextGetConstructors(graph)(),
            rep_label=M.TestLabel,
            rep_args=args,
        )
        graph._replace_context(constructors=M.FromContextGetConstructors(self)())

        self.add_node(input_nodes)
        self.add_node(expected)
        self._prepend_edge_unchecked(computation_edge)
        graph._replace_context(tests=M.Pair(self, M.FromContextGetTests(graph)()))
        self.result = None

    def run(self):
        result = self.computation_edge()

        if M.IsPair(result)() is M.truth_value:
            value = M.Head(result)()
            rest = M.Tail(result)()
            if M.IsPair(rest)() is M.truth_value:
                maybe_registry = M.Head(rest)()
                maybe_rest = M.Tail(rest)()
                value_is_true = M.IdentityCompare(value, M.truth_value)()
                value_is_false = M.IdentityCompare(value, M.false_value)()
                registry_like_value = M.OrAtom(value_is_true, value_is_false)()
                maybe_registry_is_pair = M.IsPair(maybe_registry)()
                if (
                    M.Compare(maybe_rest, M.EmptyList)() is M.truth_value
                    and registry_like_value is M.false_value
                    and maybe_registry_is_pair is M.false_value
                ):
                    self.graph._replace_context(constructors=maybe_registry)
            cmp = M.CompareIn(value, self.expected, M.FromContextGetConstructors(self.graph)())()
        else:
            cmp = M.CompareIn(result, self.expected, M.FromContextGetConstructors(self.graph)())()

        if cmp is M.truth_value:
            outcome = M.TestOK(M.FromContextGetConstructors(self.graph)())
        else:
            outcome = M.TestFail(M.FromContextGetConstructors(self.graph)())

        self.result = outcome
        entry = M.Pair(self.name, M.Pair(outcome, M.EmptyList))
        self.graph._replace_context(test_results=M.Pair(entry, M.FromContextGetTestResults(self.graph)()))
        return entry


class RunTests(M.Edge):
    def __init__(self, graph):
        self.graph = graph
        self.graph._replace_context(test_results=M.EmptyList)
        self.result = self._run(M.FromContextGetTests(graph)())
        super().__init__(inputs=M.Pair(graph, M.EmptyList), results=M.Pair(self.result, M.EmptyList))

    def _run(self, chain):
        if M.Compare(chain, M.EmptyList)() is M.truth_value:
            return M.EmptyList

        test = M.Head(chain)()
        result = test.run()
        rest = self._run(M.Tail(chain)())
        return M.Pair(result, rest)

    def __call__(self):
        return self.result


class TestResultsReport(M.Edge):
    def __init__(self, graph):
        self.graph = graph
        self.result = self._report(M.FromContextGetTestResults(graph)())
        super().__init__(inputs=M.Pair(graph, M.EmptyList), results=self.result)

    def _report(self, results):
        if M.Compare(results, M.EmptyList)() is M.truth_value:
            return "No tests were run."

        failed_names = self._failed_names(results)
        if failed_names:
            return "\n".join(failed_names)
        return "All the tests have passed."

    def _failed_names(self, results):
        if M.Compare(results, M.EmptyList)() is M.truth_value:
            return []

        entry = M.Head(results)()
        rest = M.Tail(results)()
        failed = self._failed_names(rest)

        name = M.Head(entry)()
        outcome = M.Head(M.Tail(entry)())()
        if self._is_test_ok(outcome) is M.truth_value:
            return failed

        failed.append(self._name_text(name))
        return failed

    def _is_test_ok(self, outcome):
        value = outcome()
        if value == "TestOK":
            return M.truth_value
        if value == "TestFail":
            return M.false_value
        constructor = M.GetConstructor(outcome, M.FromContextGetConstructors(self.graph)())()
        if M.IdentityCompare(constructor, M.EmptyList)() is M.truth_value:
            return M.false_value
        label = M.Head(constructor)()
        return M.IdentityCompare(label, M.TestOKLabel)()

    def _name_text(self, name):
        constructor = M.GetConstructor(name, M.FromContextGetConstructors(self.graph)())()
        if M.IdentityCompare(constructor, M.EmptyList)() is M.false_value:
            label = M.Head(constructor)()
            if M.IdentityCompare(label, M.TestNameLabel)() is M.truth_value:
                name_atom = M.Head(M.Tail(constructor)())()
                value = name_atom()
                return str(value)
        value = name()
        if value is None:
            return str(name)
        return str(value)

    def __call__(self):
        return self.result


__all__ = [name for name in globals() if not name.startswith("_")]
