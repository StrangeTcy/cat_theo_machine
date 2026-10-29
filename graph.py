from __future__ import annotations

from . import context as Ctx
from . import machine as M
from . import proof as P
from . import schemata as S
from . import labels as Lmod
from .search.patricia import SearchPatriciaIsTree, SearchPatriciaEntries


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
        self._search_worker_timeout_seconds = None
        self._search_worker_defer_derivation_materialization = M.false_value
        self._search_cached_burst_budget_default = M.EmptyList
        self._search_cached_burst_budget_dfs = M.EmptyList
        self._search_comparison_prompt_guard = None
        self._search_compare_enable_shared_root_fast_paths = M.false_value
        self._search_compare_ignore_root_fast_paths = M.false_value
        self._search_compare_root_start = M.EmptyList
        self._search_compare_root_goal = M.EmptyList
        self._search_compare_discovery_mode = M.false_value
        self._search_probe_disable_applicable_cache = M.false_value
        self._search_probe_disable_applicable_shards = M.false_value
        self._search_compare_live_signature = M.EmptyList
        self._search_compare_live_start = M.EmptyList
        self._search_compare_live_goal = M.EmptyList
        self._search_compare_live_states = M.EmptyList
        self._search_compare_live_workers = M.EmptyList
        self._search_compare_live_idle_executors = M.EmptyList
        self._last_search_comparison_outcome = M.EmptyList
        self.promotion_ledger = M.EmptyList
        self._active_unproved_goal = M.EmptyList
        self._active_unproved_claim = M.EmptyList
        self._last_discovered_invariant = M.EmptyList
        self._pending_discovery = M.EmptyList
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

    def current_version(self):
        return GraphVersion(self.nodes, self.edges, M.EmptyList)()

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


class Boundary(M.Edge):
    def __init__(self, graph, end):
        self.result = M.Pair(Lmod.BoundaryLabel, M.Pair(graph, M.Pair(end, M.EmptyList)))
        super().__init__(inputs=M.Pair(graph, M.Pair(end, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class Map(M.Edge):
    def __init__(self, pattern_graph, host_graph, root):
        self.result = M.Pair(Lmod.MapLabel, M.Pair(pattern_graph, M.Pair(host_graph, M.Pair(root, M.EmptyList))))
        super().__init__(inputs=M.Pair(pattern_graph, M.Pair(host_graph, M.Pair(root, M.EmptyList))), results=self.result)

    def __call__(self):
        return self.result


class Send(M.Edge):
    def __init__(self, pat, host):
        self.result = M.Pair(Lmod.SendLabel, M.Pair(pat, M.Pair(host, M.EmptyList)))
        super().__init__(inputs=M.Pair(pat, M.Pair(host, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class Apart(M.Edge):
    def __init__(self, left, right):
        self.result = M.Pair(Lmod.ApartLabel, M.Pair(left, M.Pair(right, M.EmptyList)))
        super().__init__(inputs=M.Pair(left, M.Pair(right, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class Miss(M.Edge):
    def __init__(self, pat, reason):
        self.result = M.Pair(Lmod.MissLabel, M.Pair(pat, M.Pair(reason, M.EmptyList)))
        super().__init__(inputs=M.Pair(pat, M.Pair(reason, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class Law(M.Edge):
    def __init__(self, left, interface, right, k_to_left_map, k_to_right_map, obligations):
        self.result = M.Pair(
            Lmod.LawLabel,
            M.Pair(left, M.Pair(interface, M.Pair(right, M.Pair(k_to_left_map, M.Pair(k_to_right_map, M.Pair(obligations, M.EmptyList))))))
        )
        super().__init__(
            inputs=M.Pair(left, M.Pair(interface, M.Pair(right, M.Pair(k_to_left_map, M.Pair(k_to_right_map, M.Pair(obligations, M.EmptyList)))))),
            results=self.result
        )

    def __call__(self):
        return self.result


class KObligation(M.Edge):
    def __init__(self, obligation_name, structure):
        self.result = M.Pair(Lmod.KObligationLabel, M.Pair(obligation_name, M.Pair(structure, M.EmptyList)))
        super().__init__(inputs=M.Pair(obligation_name, M.Pair(structure, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class Fire(M.Edge):
    def __init__(self, law, mapping):
        self.result = M.Pair(Lmod.FireLabel, M.Pair(law, M.Pair(mapping, M.EmptyList)))
        super().__init__(inputs=M.Pair(law, M.Pair(mapping, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class Next(M.Edge):
    def __init__(self, g0, fire, g1):
        self.result = M.Pair(Lmod.NextLabel, M.Pair(g0, M.Pair(fire, M.Pair(g1, M.EmptyList))))
        super().__init__(inputs=M.Pair(g0, M.Pair(fire, M.Pair(g1, M.EmptyList))), results=self.result)

    def __call__(self):
        return self.result


class GraphVersion(M.Edge):
    def __init__(self, node_store, edge_store, invariant_store):
        self.node_store = node_store
        self.edge_store = edge_store
        self.invariant_store = invariant_store
        self.result = M.Pair(
            Lmod.GraphVersionLabel,
            M.Pair(node_store, M.Pair(edge_store, M.Pair(invariant_store, M.EmptyList)))
        )
        super().__init__(
            inputs=M.Pair(node_store, M.Pair(edge_store, M.Pair(invariant_store, M.EmptyList))),
            results=self.result
        )

    def __call__(self):
        return self.result


class IsGraphVersion(M.Edge):
    def __init__(self, graph):
        slots = M.Pair(M.EmptyList, M.Pair(M.EmptyList, M.Pair(M.EmptyList, M.EmptyList)))
        self.result = GraphTermShape(graph, Lmod.GraphVersionLabel, slots)()
        super().__init__(inputs=M.Pair(graph, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class GraphVersionNodes(M.Edge):
    def __init__(self, graph):
        self.result = M.Head(M.Tail(graph)())()
        super().__init__(inputs=M.Pair(graph, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class GraphVersionEdges(M.Edge):
    def __init__(self, graph):
        self.result = M.Head(M.Tail(M.Tail(graph)())())()
        super().__init__(inputs=M.Pair(graph, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class GraphVersionInvariants(M.Edge):
    def __init__(self, graph):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(graph)())())())()
        super().__init__(inputs=M.Pair(graph, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class GraphNodes(M.Edge):
    """
    The one canonical way to read a graph's node store.

    Accepts every graph shape the matcher already handled: a GraphVersion
    term, a Pair-shaped Hypergraph term, and a Hypergraph constructor. The
    branches are the ones lifted out of MapExtendOneStep._graph_nodes and
    behave identically.
    """

    def __init__(self, graph):
        self.result = self._nodes(graph)
        super().__init__(inputs=M.Pair(graph, M.EmptyList), results=self.result)

    def _nodes(self, graph):
        if IsGraphVersion(graph)() is M.truth_value:
            return GraphVersionNodes(graph)()
        if M.IsPair(graph)() is M.truth_value:
            if M.IdentityCompare(M.Head(graph)(), M.HypergraphLabel)() is M.truth_value:
                return M.Head(M.Tail(graph)())()
        constructor = M.GetConstructor(graph)()
        if M.IdentityCompare(constructor, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        if M.IdentityCompare(M.Head(constructor)(), M.HypergraphLabel)() is M.false_value:
            return M.EmptyList
        args = M.Tail(constructor)()
        return M.Head(args)()

    def __call__(self):
        return self.result


class GraphEdges(M.Edge):
    """The one canonical way to read a graph's edge store. See GraphNodes."""

    def __init__(self, graph):
        self.result = self._edges(graph)
        super().__init__(inputs=M.Pair(graph, M.EmptyList), results=self.result)

    def _edges(self, graph):
        if IsGraphVersion(graph)() is M.truth_value:
            return GraphVersionEdges(graph)()
        if M.IsPair(graph)() is M.truth_value:
            if M.IdentityCompare(M.Head(graph)(), M.HypergraphLabel)() is M.truth_value:
                return M.Head(M.Tail(M.Tail(graph)())())()
        constructor = M.GetConstructor(graph)()
        if M.IdentityCompare(constructor, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        if M.IdentityCompare(M.Head(constructor)(), M.HypergraphLabel)() is M.false_value:
            return M.EmptyList
        args = M.Tail(constructor)()
        return M.Head(M.Tail(args)())()

    def __call__(self):
        return self.result


class IsSend(M.Edge):
    def __init__(self, term):
        self.result = GraphTermShape(term, Lmod.SendLabel, M.Pair(M.EmptyList, M.Pair(M.EmptyList, M.EmptyList)))()
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SendPat(M.Edge):
    def __init__(self, term):
        self.result = M.Head(M.Tail(term)())()
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SendHost(M.Edge):
    def __init__(self, term):
        self.result = M.Head(M.Tail(M.Tail(term)())())()
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class MappedHostForPat(M.Edge):
    """Pair(truth_value, host) when the mapping already sends pat, else Pair(false_value, EmptyList)."""

    def __init__(self, root, pat):
        self.result = M.Pair(M.false_value, M.EmptyList)
        if M.IsPair(root)() is M.truth_value:
            item = M.Head(root)()
            if IsSend(item)() is M.truth_value:
                if M.IdentityCompare(SendPat(item)(), pat)() is M.truth_value:
                    self.result = M.Pair(M.truth_value, SendHost(item)())
            if M.Head(self.result)() is M.false_value:
                self.result = MappedHostForPat(M.Tail(root)(), pat)()
        super().__init__(inputs=M.Pair(root, M.Pair(pat, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class EdgeEndpoints(M.Edge):
    """The ordered endpoint chain an edge term references."""

    def __init__(self, edge_term):
        atom_result = M.EmptyList
        if M.IsPair(edge_term)() is M.truth_value:
            atom_result = M.Tail(edge_term)()
        self.result = atom_result
        super().__init__(inputs=M.Pair(edge_term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class EdgeSendConsistent(M.Edge):
    """
    Positional agreement between a pattern edge and a host edge.

    The endpoints are ordered, so sending a pattern edge to a host edge only
    makes sense when the two carry the same number of endpoints and every
    already-mapped pattern endpoint lands on the host endpoint in the same
    position. Endpoints the mapping has not committed to yet impose nothing.
    """

    def __init__(self, mapping_root, pat_edge, host_edge):
        self.result = M.false_value
        if M.IsPair(pat_edge)() is M.truth_value:
            if M.IsPair(host_edge)() is M.truth_value:
                if M.Compare(M.Head(pat_edge)(), M.Head(host_edge)())() is M.truth_value:
                    self.result = EdgeEndpointsConsistent(
                        mapping_root, EdgeEndpoints(pat_edge)(), EdgeEndpoints(host_edge)()
                    )()
        super().__init__(
            inputs=M.Pair(mapping_root, M.Pair(pat_edge, M.Pair(host_edge, M.EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class EdgeEndpointsConsistent(M.Edge):
    def __init__(self, root, pattern_endpoints, host_endpoints):
        self.result = M.false_value
        if M.IdentityCompare(pattern_endpoints, M.EmptyList)() is M.truth_value:
            self.result = M.IdentityCompare(host_endpoints, M.EmptyList)()
        elif M.IsPair(pattern_endpoints)() is M.truth_value:
            if M.IsPair(host_endpoints)() is M.truth_value:
                found = MappedHostForPat(root, M.Head(pattern_endpoints)())()
                agrees = M.truth_value
                if M.Head(found)() is M.truth_value:
                    agrees = M.IdentityCompare(M.Tail(found)(), M.Head(host_endpoints)())()
                if agrees is M.truth_value:
                    self.result = EdgeEndpointsConsistent(
                        root, M.Tail(pattern_endpoints)(), M.Tail(host_endpoints)()
                    )()
        super().__init__(
            inputs=M.Pair(root, M.Pair(pattern_endpoints, M.Pair(host_endpoints, M.EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class GraphChainHasIdentity(M.Edge):
    def __init__(self, chain, term):
        self.result = M.false_value
        if M.IsPair(chain)() is M.truth_value:
            self.result = M.IdentityCompare(M.Head(chain)(), term)()
            if self.result is M.false_value:
                self.result = GraphChainHasIdentity(M.Tail(chain)(), term)()
        super().__init__(inputs=M.Pair(chain, M.Pair(term, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class GraphPatriciaValues(M.Edge):
    def __init__(self, entries, accumulated=M.EmptyList):
        self.result = accumulated
        if M.IsPair(entries)() is M.truth_value:
            entry = M.Head(entries)()
            self.result = GraphPatriciaValues(
                M.Tail(entries)(), M.Pair(M.Head(M.Tail(entry)())(), accumulated)
            )()
        super().__init__(inputs=M.Pair(entries, M.Pair(accumulated, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class GraphStoreValues(M.Edge):
    def __init__(self, store):
        self.result = store
        if SearchPatriciaIsTree(store)() is M.truth_value:
            self.result = GraphPatriciaValues(SearchPatriciaEntries(store)())()
        super().__init__(inputs=M.Pair(store, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class GraphChainAppend(M.Edge):
    def __init__(self, first, second):
        self.result = second
        if M.IsPair(first)() is M.truth_value:
            self.result = M.Pair(M.Head(first)(), GraphChainAppend(M.Tail(first)(), second)())
        super().__init__(inputs=M.Pair(first, M.Pair(second, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class GraphHasElement(M.Edge):
    def __init__(self, graph, term):
        self.result = GraphChainHasIdentity(GraphStoreValues(GraphNodes(graph)())(), term)()
        if self.result is M.false_value:
            self.result = GraphChainHasIdentity(GraphStoreValues(GraphEdges(graph)())(), term)()
        super().__init__(inputs=M.Pair(graph, M.Pair(term, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class GraphFieldsShape(M.Edge):
    def __init__(self, fields, slots):
        self.result = M.false_value
        if M.IdentityCompare(slots, M.EmptyList)() is M.truth_value:
            self.result = M.IdentityCompare(fields, M.EmptyList)()
        elif M.IsPair(fields)() is M.truth_value:
            self.result = GraphFieldsShape(M.Tail(fields)(), M.Tail(slots)())()
        super().__init__(inputs=M.Pair(fields, M.Pair(slots, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class GraphTermShape(M.Edge):
    def __init__(self, term, label, slots):
        self.result = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if M.IdentityCompare(M.Head(term)(), label)() is M.truth_value:
                self.result = GraphFieldsShape(M.Tail(term)(), slots)()
        super().__init__(inputs=M.Pair(term, M.Pair(label, M.Pair(slots, M.EmptyList))), results=self.result)

    def __call__(self):
        return self.result


class IsGraphValue(M.Edge):
    def __init__(self, graph):
        self.result = IsGraphVersion(graph)()
        if self.result is M.false_value:
            slots = M.Pair(M.EmptyList, M.Pair(M.EmptyList, M.EmptyList))
            self.result = GraphTermShape(graph, M.HypergraphLabel, slots)()
            if self.result is M.false_value:
                constructor = M.GetConstructor(graph)()
                self.result = GraphTermShape(constructor, M.HypergraphLabel, slots)()
        super().__init__(inputs=M.Pair(graph, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class IsMap(M.Edge):
    def __init__(self, term):
        self.result = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if M.IdentityCompare(M.Head(term)(), Lmod.MapLabel)() is M.truth_value:
                fields = M.Tail(term)()
                if M.IsPair(fields)() is M.truth_value:
                    fields = M.Tail(fields)()
                    if M.IsPair(fields)() is M.truth_value:
                        fields = M.Tail(fields)()
                        if M.IsPair(fields)() is M.truth_value:
                            self.result = M.IdentityCompare(M.Tail(fields)(), M.EmptyList)()
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class MapPattern(M.Edge):
    def __init__(self, mapping):
        self.result = M.Head(M.Tail(mapping)())()
        super().__init__(inputs=M.Pair(mapping, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class MapHost(M.Edge):
    def __init__(self, mapping):
        self.result = M.Head(M.Tail(M.Tail(mapping)())())()
        super().__init__(inputs=M.Pair(mapping, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class MapRoot(M.Edge):
    def __init__(self, mapping):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(mapping)())())())()
        super().__init__(inputs=M.Pair(mapping, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class MappedPatForHost(M.Edge):
    def __init__(self, root, host):
        self.result = M.Pair(M.false_value, M.EmptyList)
        if M.IsPair(root)() is M.truth_value:
            item = M.Head(root)()
            if IsSend(item)() is M.truth_value:
                if M.IdentityCompare(SendHost(item)(), host)() is M.truth_value:
                    self.result = M.Pair(M.truth_value, SendPat(item)())
            if M.Head(self.result)() is M.false_value:
                self.result = MappedPatForHost(M.Tail(root)(), host)()
        super().__init__(inputs=M.Pair(root, M.Pair(host, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class MapElementKindsAgree(M.Edge):
    def __init__(self, pattern_graph, host_graph, pat, host):
        pattern_node = GraphChainHasIdentity(GraphStoreValues(GraphNodes(pattern_graph)())(), pat)()
        host_node = GraphChainHasIdentity(GraphStoreValues(GraphNodes(host_graph)())(), host)()
        pattern_edge = GraphChainHasIdentity(GraphStoreValues(GraphEdges(pattern_graph)())(), pat)()
        host_edge = GraphChainHasIdentity(GraphStoreValues(GraphEdges(host_graph)())(), host)()
        self.result = M.AndAtom(
            M.IdentityCompare(pattern_node, host_node)(),
            M.IdentityCompare(pattern_edge, host_edge)(),
        )()
        super().__init__(
            inputs=M.Pair(pattern_graph, M.Pair(host_graph, M.Pair(pat, M.Pair(host, M.EmptyList)))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class ReasonShape(M.Edge):
    """
    A mapping step rejected on shape: the mapping was not a Map, or the
    pattern or host element was absent from its graph. Carries the term that
    was wrong instead of a string.
    """

    def __init__(self, subject):
        self.result = M.Pair(Lmod.ReasonShapeLabel, M.Pair(subject, M.EmptyList))
        super().__init__(inputs=M.Pair(subject, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ReasonAlreadyMapped(M.Edge):
    """The pattern element already had a Send; carries it and its host image."""

    def __init__(self, pat, existing_host):
        self.result = M.Pair(
            Lmod.ReasonAlreadyMappedLabel,
            M.Pair(pat, M.Pair(existing_host, M.EmptyList)),
        )
        super().__init__(
            inputs=M.Pair(pat, M.Pair(existing_host, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class ReasonApart(M.Edge):
    """An Apart commitment forbade this Send; carries the Apart term itself."""

    def __init__(self, apart, pat, host):
        self.result = M.Pair(
            Lmod.ReasonApartLabel,
            M.Pair(apart, M.Pair(pat, M.Pair(host, M.EmptyList))),
        )
        super().__init__(
            inputs=M.Pair(apart, M.Pair(pat, M.Pair(host, M.EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class ReasonPositional(M.Edge):
    """Edge endpoints disagreed positionally; carries both edges."""

    def __init__(self, pat_edge, host_edge):
        self.result = M.Pair(
            Lmod.ReasonPositionalLabel,
            M.Pair(pat_edge, M.Pair(host_edge, M.EmptyList)),
        )
        super().__init__(
            inputs=M.Pair(pat_edge, M.Pair(host_edge, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class IsLawTerm(M.Edge):
    def __init__(self, term):
        slots = M.Pair(M.EmptyList, M.Pair(M.EmptyList, M.Pair(M.EmptyList,
            M.Pair(M.EmptyList, M.Pair(M.EmptyList, M.Pair(M.EmptyList, M.EmptyList))))))
        self.result = GraphTermShape(term, Lmod.LawLabel, slots)()
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class LawLeft(M.Edge):
    def __init__(self, law):
        self.result = M.Head(M.Tail(law)())()
        super().__init__(inputs=M.Pair(law, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class LawInterface(M.Edge):
    def __init__(self, law):
        self.result = M.Head(M.Tail(M.Tail(law)())())()
        super().__init__(inputs=M.Pair(law, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class LawRight(M.Edge):
    def __init__(self, law):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(law)())())())()
        super().__init__(inputs=M.Pair(law, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class LawKToLeft(M.Edge):
    def __init__(self, law):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(law)())())())())()
        super().__init__(inputs=M.Pair(law, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class LawKToRight(M.Edge):
    def __init__(self, law):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(law)())())())())())()
        super().__init__(inputs=M.Pair(law, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class LawObligations(M.Edge):
    def __init__(self, law):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(law)())())())())())())()
        super().__init__(inputs=M.Pair(law, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class MapSendsEveryElement(M.Edge):
    """
    True when `mapping` has a Send for every node and edge of `source_graph`,
    and every edge Send is positionally consistent under Step 3.
    """

    def __init__(self, mapping, source_graph):
        self.result = M.false_value
        if IsMap(mapping)() is M.truth_value:
            if M.IdentityCompare(MapPattern(mapping)(), source_graph)() is M.truth_value:
                root = MapRoot(mapping)()
                graphs_valid = M.AndAtom(IsGraphValue(source_graph)(), IsGraphValue(MapHost(mapping)())())()
                if graphs_valid is M.truth_value:
                    if MapRootValid(root, source_graph, MapHost(mapping)())() is M.truth_value:
                        if MapSendsChain(root, GraphStoreValues(GraphNodes(source_graph)())())() is M.truth_value:
                            if MapSendsChain(root, GraphStoreValues(GraphEdges(source_graph)())())() is M.truth_value:
                                inconsistent = MapFirstInconsistentEdge(root, source_graph, root)()
                                self.result = M.IdentityCompare(inconsistent, M.EmptyList)()
        super().__init__(
            inputs=M.Pair(mapping, M.Pair(source_graph, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class MapSendsChain(M.Edge):
    def __init__(self, root, elements):
        self.result = M.IdentityCompare(elements, M.EmptyList)()
        if M.IsPair(elements)() is M.truth_value:
            found = MappedHostForPat(root, M.Head(elements)())()
            if M.Head(found)() is M.truth_value:
                self.result = MapSendsChain(root, M.Tail(elements)())()
        super().__init__(inputs=M.Pair(root, M.Pair(elements, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class IsApart(M.Edge):
    def __init__(self, term):
        self.result = GraphTermShape(term, Lmod.ApartLabel, M.Pair(M.EmptyList, M.Pair(M.EmptyList, M.EmptyList)))()
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ApartLeft(M.Edge):
    def __init__(self, term):
        self.result = M.Head(M.Tail(term)())()
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ApartRight(M.Edge):
    def __init__(self, term):
        self.result = M.Head(M.Tail(M.Tail(term)())())()
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class MapRootValid(M.Edge):
    """Every Send belongs to its graphs, has the right role, and is injective."""

    def __init__(self, root, pattern_graph, host_graph):
        self.result = M.IdentityCompare(root, M.EmptyList)()
        if M.IsPair(root)() is M.truth_value:
            item = M.Head(root)()
            rest = M.Tail(root)()
            admitted = M.false_value
            if IsSend(item)() is M.truth_value:
                pat = SendPat(item)()
                host = SendHost(item)()
                admitted = M.AndAtom(
                    GraphHasElement(pattern_graph, pat)(), GraphHasElement(host_graph, host)()
                )()
                if admitted is M.truth_value:
                    admitted = MapElementKindsAgree(pattern_graph, host_graph, pat, host)()
                if admitted is M.truth_value:
                    admitted = M.NotAtom(M.Head(MappedHostForPat(rest, pat)())())()
                if admitted is M.truth_value:
                    admitted = M.NotAtom(M.Head(MappedPatForHost(rest, host)())())()
            elif IsApart(item)() is M.truth_value:
                left = ApartLeft(item)()
                right = ApartRight(item)()
                admitted = M.AndAtom(
                    GraphHasElement(pattern_graph, left)(), GraphHasElement(pattern_graph, right)()
                )()
                if admitted is M.truth_value:
                    admitted = M.NotAtom(M.IdentityCompare(left, right)())()
            elif IsMapAttempt(item)() is M.truth_value:
                admitted = M.truth_value
            if admitted is M.truth_value:
                self.result = MapRootValid(rest, pattern_graph, host_graph)()
        super().__init__(
            inputs=M.Pair(root, M.Pair(pattern_graph, M.Pair(host_graph, M.EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class MapFirstInconsistentEdge(M.Edge):
    def __init__(self, remaining, pattern_graph, root):
        self.result = M.EmptyList
        if M.IsPair(remaining)() is M.truth_value:
            item = M.Head(remaining)()
            if IsSend(item)() is M.truth_value:
                pat = SendPat(item)()
                if GraphChainHasIdentity(GraphStoreValues(GraphEdges(pattern_graph)())(), pat)() is M.truth_value:
                    host = SendHost(item)()
                    if EdgeSendConsistent(root, pat, host)() is M.false_value:
                        self.result = M.Pair(pat, host)
            if M.IdentityCompare(self.result, M.EmptyList)() is M.truth_value:
                self.result = MapFirstInconsistentEdge(M.Tail(remaining)(), pattern_graph, root)()
        super().__init__(
            inputs=M.Pair(remaining, M.Pair(pattern_graph, M.Pair(root, M.EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class LawMapsComplete(M.Edge):
    """
    Both interface maps are complete monomorphisms into the declared sides.
    """

    def __init__(self, law):
        self.result = M.false_value
        if IsLawTerm(law)() is M.truth_value:
            interface = LawInterface(law)()
            left_map = LawKToLeft(law)()
            right_map = LawKToRight(law)()
            if MapSendsEveryElement(left_map, interface)() is M.truth_value:
                if MapSendsEveryElement(right_map, interface)() is M.truth_value:
                    self.result = M.AndAtom(
                        M.IdentityCompare(MapHost(left_map)(), LawLeft(law)())(),
                        M.IdentityCompare(MapHost(right_map)(), LawRight(law)())(),
                    )()
        super().__init__(inputs=M.Pair(law, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class DanglingForbid(M.Edge):
    """Dangling mode atom: refuse to fire if the deletion would strand an edge."""

    def __init__(self):
        self.result = M.Pair(Lmod.DanglingForbidLabel, M.EmptyList)
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class DanglingDelete(M.Edge):
    """Dangling mode atom: sweep stranded edges into the delete set."""

    def __init__(self):
        self.result = M.Pair(Lmod.DanglingDeleteLabel, M.EmptyList)
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class ChainHasTerm(M.Edge):
    def __init__(self, chain, term):
        atom_result = M.false_value
        remaining = chain
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if M.TermEqual(M.Head(remaining)(), term)() is M.truth_value:
                atom_result = M.truth_value
                remaining = M.EmptyList
            else:
                remaining = M.Tail(remaining)()
        self.result = atom_result
        super().__init__(inputs=M.Pair(chain, M.Pair(term, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class ChainWithout(M.Edge):
    """Remove graph elements by identity, preserving the surviving order."""

    def __init__(self, chain, removals):
        self.result = M.EmptyList
        if M.IsPair(chain)() is M.truth_value:
            item = M.Head(chain)()
            self.result = ChainWithout(M.Tail(chain)(), removals)()
            if GraphChainHasIdentity(removals, item)() is M.false_value:
                self.result = M.Pair(item, self.result)
        super().__init__(inputs=M.Pair(chain, M.Pair(removals, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class MappedImages(M.Edge):
    """
    Host images, under `root`, of every element of `source` that the interface
    `keep` does not preserve. Elements with no Send contribute nothing.
    """

    def __init__(self, root, source, keep):
        self.result = M.EmptyList
        if M.IsPair(source)() is M.truth_value:
            element = M.Head(source)()
            self.result = MappedImages(root, M.Tail(source)(), keep)()
            if GraphChainHasIdentity(keep, element)() is M.false_value:
                found = MappedHostForPat(root, element)()
                if M.Head(found)() is M.truth_value:
                    self.result = M.Pair(M.Tail(found)(), self.result)
        super().__init__(
            inputs=M.Pair(root, M.Pair(source, M.Pair(keep, M.EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class InterfacePreimages(M.Edge):
    """
    The elements of a side graph that the interface pins down: for each K
    element, its image under `k_to_side`.
    """

    def __init__(self, interface, k_to_side):
        self.result = M.EmptyList
        if IsMap(k_to_side)() is M.truth_value:
            elements = GraphChainAppend(
                GraphStoreValues(GraphNodes(interface)())(),
                GraphStoreValues(GraphEdges(interface)())(),
            )()
            self.result = MappedImages(MapRoot(k_to_side)(), elements, M.EmptyList)()
        super().__init__(
            inputs=M.Pair(interface, M.Pair(k_to_side, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class InterfaceHostBindings(M.Edge):
    """Compose K-to-R, K-to-L and the match into explicit R-to-host Sends."""

    def __init__(self, elements, k_left_root, k_right_root, match_root):
        verdict = M.IdentityCompare(elements, M.EmptyList)()
        bindings = M.EmptyList
        if M.IsPair(elements)() is M.truth_value:
            element = M.Head(elements)()
            left = MappedHostForPat(k_left_root, element)()
            right = MappedHostForPat(k_right_root, element)()
            if M.AndAtom(M.Head(left)(), M.Head(right)())() is M.truth_value:
                host = MappedHostForPat(match_root, M.Tail(left)())()
                if M.Head(host)() is M.truth_value:
                    remaining = InterfaceHostBindings(
                        M.Tail(elements)(), k_left_root, k_right_root, match_root,
                    )()
                    verdict = M.Head(remaining)()
                    if verdict is M.truth_value:
                        bindings = M.Pair(
                            Send(M.Tail(right)(), M.Tail(host)())(), M.Tail(remaining)(),
                        )
        super().__init__(
            inputs=M.Pair(elements, M.Pair(k_left_root, M.Pair(k_right_root,
                M.Pair(match_root, M.EmptyList)))), results=M.Pair(verdict, bindings),
        )


class InsertionNodeBindings(M.Edge):
    """Admit explicit R-minus-K nodes once and retain their endpoint bindings.

    This graph representation supplies node objects as part of R. It does
    not define a payload-preserving allocator for fresh copies of arbitrary
    nodes, so an admission that collides with the host is refused.
    """

    def __init__(self, nodes, host_graph, bindings):
        verdict = M.IdentityCompare(nodes, M.EmptyList)()
        result = bindings
        if M.IsPair(nodes)() is M.truth_value:
            node = M.Head(nodes)()
            present = MappedHostForPat(bindings, node)()
            if M.AndAtom(
                M.NotAtom(GraphHasElement(host_graph, node)())(),
                M.NotAtom(M.Head(present)())(),
            )() is M.truth_value:
                remaining = InsertionNodeBindings(
                    M.Tail(nodes)(), host_graph, M.Pair(Send(node, node)(), bindings),
                )()
                verdict = M.Head(remaining)()
                result = M.Tail(remaining)()
        super().__init__(
            inputs=M.Pair(nodes, M.Pair(host_graph, M.Pair(bindings, M.EmptyList))),
            results=M.Pair(verdict, result),
        )


class GluedEndpoints(M.Edge):
    """Resolve every positional endpoint through the explicit insertion map."""

    def __init__(self, endpoints, bindings):
        verdict = M.IdentityCompare(endpoints, M.EmptyList)()
        result = M.EmptyList
        if M.IsPair(endpoints)() is M.truth_value:
            found = MappedHostForPat(bindings, M.Head(endpoints)())()
            if M.Head(found)() is M.truth_value:
                remaining = GluedEndpoints(M.Tail(endpoints)(), bindings)()
                verdict = M.Head(remaining)()
                if verdict is M.truth_value:
                    result = M.Pair(M.Tail(found)(), M.Tail(remaining)())
        super().__init__(
            inputs=M.Pair(endpoints, M.Pair(bindings, M.EmptyList)),
            results=M.Pair(verdict, result),
        )


class GluedInsertionEdges(M.Edge):
    """Build fresh edge terms; an unbound endpoint refuses the insertion."""

    def __init__(self, edges, bindings):
        verdict = M.IdentityCompare(edges, M.EmptyList)()
        result = M.EmptyList
        if M.IsPair(edges)() is M.truth_value:
            edge = M.Head(edges)()
            if M.IsPair(edge)() is M.truth_value:
                glued = GluedEndpoints(EdgeEndpoints(edge)(), bindings)()
                if M.Head(glued)() is M.truth_value:
                    remaining = GluedInsertionEdges(M.Tail(edges)(), bindings)()
                    verdict = M.Head(remaining)()
                    if verdict is M.truth_value:
                        result = M.Pair(
                            M.Pair(M.Head(edge)(), M.Tail(glued)()), M.Tail(remaining)(),
                        )
        super().__init__(
            inputs=M.Pair(edges, M.Pair(bindings, M.EmptyList)),
            results=M.Pair(verdict, result),
        )


class InsertionEdgeBindings(M.Edge):
    """Record the source identity of each freshly constructed edge."""

    def __init__(self, source_edges, inserted_edges, bindings):
        result = bindings
        if M.IsPair(source_edges)() is M.truth_value:
            result = InsertionEdgeBindings(
                M.Tail(source_edges)(), M.Tail(inserted_edges)(),
                M.Pair(Send(M.Head(source_edges)(), M.Head(inserted_edges)())(), bindings),
            )()
        super().__init__(
            inputs=M.Pair(source_edges, M.Pair(inserted_edges, M.Pair(bindings, M.EmptyList))),
            results=result,
        )


class SurgeryUniqueStore(M.Edge):
    """Require a proper finite store with one occurrence per graph identity."""

    def __init__(self, store, seen=M.EmptyList):
        verdict = M.IdentityCompare(store, M.EmptyList)()
        if M.IsPair(store)() is M.truth_value:
            element = M.Head(store)()
            if GraphChainHasIdentity(seen, element)() is M.false_value:
                verdict = SurgeryUniqueStore(M.Tail(store)(), M.Pair(element, seen))()
        super().__init__(inputs=M.Pair(store, M.Pair(seen, M.EmptyList)), results=verdict)


class SurgeryEndpointMembership(M.Edge):
    """Every positional endpoint must belong to the graph being checked."""

    def __init__(self, endpoints, elements):
        verdict = M.IdentityCompare(endpoints, M.EmptyList)()
        if M.IsPair(endpoints)() is M.truth_value:
            if GraphChainHasIdentity(elements, M.Head(endpoints)())() is M.truth_value:
                verdict = SurgeryEndpointMembership(M.Tail(endpoints)(), elements)()
        super().__init__(inputs=M.Pair(endpoints, M.Pair(elements, M.EmptyList)), results=verdict)


class SurgeryEdgeIncidence(M.Edge):
    """Check every edge body without interpreting missing endpoints as empty."""

    def __init__(self, edges, elements):
        verdict = M.IdentityCompare(edges, M.EmptyList)()
        if M.IsPair(edges)() is M.truth_value:
            edge = M.Head(edges)()
            if M.IsPair(edge)() is M.truth_value:
                if SurgeryEndpointMembership(M.Tail(edge)(), elements)() is M.truth_value:
                    verdict = SurgeryEdgeIncidence(M.Tail(edges)(), elements)()
        super().__init__(inputs=M.Pair(edges, M.Pair(elements, M.EmptyList)), results=verdict)


class SurgeryGraphValid(M.Edge):
    """Admission evidence for proper, disjoint stores and closed incidence."""

    def __init__(self, graph):
        verdict = IsGraphValue(graph)()
        if verdict is M.truth_value:
            nodes = GraphStoreValues(GraphNodes(graph)())()
            edges = GraphStoreValues(GraphEdges(graph)())()
            verdict = SurgeryUniqueStore(nodes)()
            if verdict is M.truth_value:
                verdict = SurgeryUniqueStore(edges, nodes)()
            if verdict is M.truth_value:
                elements = GraphChainAppend(nodes, edges)()
                verdict = SurgeryEdgeIncidence(edges, elements)()
            if verdict is M.truth_value:
                if IsGraphVersion(graph)() is M.truth_value:
                    verdict = SurgeryUniqueStore(GraphStoreValues(GraphVersionInvariants(graph)())())()
        super().__init__(inputs=M.Pair(graph, M.EmptyList), results=verdict)


class FireLaw(M.Edge):
    """
    Step 8. Staged double-pushout surgery over a GraphVersion.

    Stages, each appended to the returned trace as a labeled term:
    MatchPrepared, DeletionAdmitted, ComplementProduced, InsertionPrepared,
    GraphVersionCommitted. `dangling_mode` is DanglingForbid or DanglingDelete.

    Returns Pair(committed_version_or_EmptyList, Pair(trace, EmptyList)); a
    refused firing yields M.EmptyList for the version and a trace whose last
    entry says which stage refused. Version history is append-only: g0 is
    never mutated.
    """

    def __init__(self, graph_version, law, mapping, dangling_mode):
        trace = M.EmptyList
        stage = M.Pair(
            Lmod.MatchPreparedLabel, M.Pair(law, M.Pair(mapping, M.EmptyList)),
        )
        committed = M.EmptyList
        admitted = M.AndAtom(IsGraphVersion(graph_version)(), IsLawTerm(law)())()
        if admitted is M.truth_value:
            admitted = M.AndAtom(
                SurgeryGraphValid(graph_version)(), SurgeryGraphValid(LawLeft(law)())(),
            )()
        if admitted is M.truth_value:
            admitted = M.AndAtom(
                SurgeryGraphValid(LawInterface(law)())(), SurgeryGraphValid(LawRight(law)())(),
            )()
        if admitted is M.truth_value:
            admitted = LawMapsComplete(law)()
        if admitted is M.truth_value:
            left = LawLeft(law)()
            admitted = MapSendsEveryElement(mapping, left)()
        if admitted is M.truth_value:
            admitted = M.AndAtom(
                M.IdentityCompare(MapHost(mapping)(), graph_version)(),
                M.IdentityCompare(LawObligations(law)(), M.EmptyList)(),
            )()
        forbid = M.TermEqual(dangling_mode, DanglingForbid()())()
        sweep = M.TermEqual(dangling_mode, DanglingDelete()())()
        admitted = M.AndAtom(admitted, M.OrAtom(forbid, sweep)())()
        if admitted is M.truth_value:
            trace = M.Pair(stage, M.EmptyList)
            root = MapRoot(mapping)()
            interface = LawInterface(law)()
            kept_left = InterfacePreimages(interface, LawKToLeft(law)())()
            left_nodes = GraphStoreValues(GraphNodes(left)())()
            left_edges = GraphStoreValues(GraphEdges(left)())()
            deleted_nodes = MappedImages(root, left_nodes, kept_left)()
            deleted_edges = MappedImages(root, left_edges, kept_left)()
            stranded = ChainWithout(DanglingEdges(
                graph_version, GraphChainAppend(deleted_nodes, deleted_edges)(),
            )(), deleted_edges)()
            admitted = M.OrAtom(M.IdentityCompare(stranded, M.EmptyList)(), sweep)()
            if admitted is M.truth_value:
                deleted_edges = DeletionEdgeClosure(graph_version, deleted_nodes, deleted_edges)()
                preserved_images = MappedImages(root, kept_left, M.EmptyList)()
                admitted = M.NotAtom(EndpointsTouchDeleted(deleted_edges, preserved_images)())()
            stage = M.Pair(
                Lmod.DeletionAdmittedLabel,
                M.Pair(deleted_nodes, M.Pair(deleted_edges, M.Pair(stranded, M.EmptyList))),
            )
        if admitted is M.truth_value:
            trace = GraphChainAppend(trace, M.Pair(stage, M.EmptyList))()
            host_nodes = GraphStoreValues(GraphNodes(graph_version)())()
            host_edges = GraphStoreValues(GraphEdges(graph_version)())()
            new_nodes = ChainWithout(host_nodes, deleted_nodes)()
            new_edges = ChainWithout(host_edges, deleted_edges)()
            stage = M.Pair(
                Lmod.ComplementProducedLabel, M.Pair(new_nodes, M.Pair(new_edges, M.EmptyList)),
            )
            trace = GraphChainAppend(trace, M.Pair(stage, M.EmptyList))()

            right = LawRight(law)()
            kept_right = InterfacePreimages(interface, LawKToRight(law)())()
            inserted_nodes = ChainWithout(GraphStoreValues(GraphNodes(right)())(), kept_right)()
            right_inserted_edges = ChainWithout(GraphStoreValues(GraphEdges(right)())(), kept_right)()
            interface_elements = GraphChainAppend(
                GraphStoreValues(GraphNodes(interface)())(),
                GraphStoreValues(GraphEdges(interface)())(),
            )()
            glued_interface = InterfaceHostBindings(
                interface_elements, MapRoot(LawKToLeft(law)())(),
                MapRoot(LawKToRight(law)())(), root,
            )()
            admitted = M.Head(glued_interface)()
            bindings = M.Tail(glued_interface)()
            if admitted is M.truth_value:
                node_bindings = InsertionNodeBindings(inserted_nodes, graph_version, bindings)()
                admitted = M.Head(node_bindings)()
                bindings = M.Tail(node_bindings)()
            inserted_edges = M.EmptyList
            if admitted is M.truth_value:
                glued_edges = GluedInsertionEdges(right_inserted_edges, bindings)()
                admitted = M.Head(glued_edges)()
                inserted_edges = M.Tail(glued_edges)()
                if admitted is M.truth_value:
                    bindings = InsertionEdgeBindings(right_inserted_edges, inserted_edges, bindings)()
            stage = M.Pair(
                Lmod.InsertionPreparedLabel,
                M.Pair(inserted_nodes, M.Pair(inserted_edges, M.Pair(bindings, M.EmptyList))),
            )
        if admitted is M.truth_value:
            trace = GraphChainAppend(trace, M.Pair(stage, M.EmptyList))()
            new_nodes = GraphChainAppend(inserted_nodes, new_nodes)()
            new_edges = GraphChainAppend(inserted_edges, new_edges)()
            committed = GraphVersion(new_nodes, new_edges, GraphVersionInvariants(graph_version)())()
            stage = M.Pair(Lmod.GraphVersionCommittedLabel, M.Pair(M.EmptyList, M.EmptyList))
            trace = GraphChainAppend(trace, M.Pair(stage, M.EmptyList))()
            trace = GraphChainAppend(
                trace, M.Pair(Next(graph_version, Fire(law, mapping)(), committed)(), M.EmptyList),
            )()
        else:
            refusal = M.Pair(Lmod.FireRejectedLabel, M.Pair(stage, M.EmptyList))
            trace = GraphChainAppend(trace, M.Pair(refusal, M.EmptyList))()
        self.result = M.Pair(committed, M.Pair(trace, M.EmptyList))
        super().__init__(
            inputs=M.Pair(graph_version, M.Pair(law, M.Pair(mapping,
                M.Pair(dangling_mode, M.EmptyList)))), results=self.result,
        )

    def __call__(self):
        return self.result


class EndpointsTouchDeleted(M.Edge):
    """Recognize a shared graph endpoint by identity."""

    def __init__(self, endpoints, deleted_nodes):
        verdict = M.false_value
        if M.IsPair(endpoints)() is M.truth_value:
            verdict = GraphChainHasIdentity(deleted_nodes, M.Head(endpoints)())()
            if verdict is M.false_value:
                verdict = EndpointsTouchDeleted(M.Tail(endpoints)(), deleted_nodes)()
        super().__init__(
            inputs=M.Pair(endpoints, M.Pair(deleted_nodes, M.EmptyList)), results=verdict,
        )


class EdgesTouchingDeleted(M.Edge):
    def __init__(self, edges, deleted_nodes):
        result = M.EmptyList
        if M.IsPair(edges)() is M.truth_value:
            edge = M.Head(edges)()
            result = EdgesTouchingDeleted(M.Tail(edges)(), deleted_nodes)()
            if EndpointsTouchDeleted(EdgeEndpoints(edge)(), deleted_nodes)() is M.truth_value:
                result = M.Pair(edge, result)
        super().__init__(
            inputs=M.Pair(edges, M.Pair(deleted_nodes, M.EmptyList)), results=result,
        )


class DanglingEdges(M.Edge):
    """Record the identity-based boundary scan as a machine operation."""

    def __init__(self, graph_version, deleted_nodes):
        self.result = EdgesTouchingDeleted(GraphStoreValues(GraphEdges(graph_version)())(), deleted_nodes)()
        super().__init__(
            inputs=M.Pair(graph_version, M.Pair(deleted_nodes, M.EmptyList)), results=self.result,
        )

    def __call__(self):
        return self.result


class MapAttempt(M.Edge):
    """A mapping extension together with its source state and recorded outcome."""

    def __init__(self, mapping, pat, host, outcome):
        self.result = M.Pair(
            Lmod.MapAttemptLabel,
            M.Pair(mapping, M.Pair(pat, M.Pair(host, M.Pair(outcome, M.EmptyList)))),
        )
        super().__init__(
            inputs=M.Pair(mapping, M.Pair(pat, M.Pair(host, M.Pair(outcome, M.EmptyList)))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class IsMapAttempt(M.Edge):
    def __init__(self, term):
        slots = M.Pair(M.EmptyList, M.Pair(M.EmptyList, M.Pair(M.EmptyList, M.Pair(M.EmptyList, M.EmptyList))))
        self.result = GraphTermShape(term, Lmod.MapAttemptLabel, slots)()
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class MapAttemptMapping(M.Edge):
    def __init__(self, attempt):
        self.result = M.Head(M.Tail(attempt)())()
        super().__init__(inputs=M.Pair(attempt, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class MapAttemptPat(M.Edge):
    def __init__(self, attempt):
        self.result = M.Head(M.Tail(M.Tail(attempt)())())()
        super().__init__(inputs=M.Pair(attempt, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class MapAttemptHost(M.Edge):
    def __init__(self, attempt):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(attempt)())())())()
        super().__init__(inputs=M.Pair(attempt, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class MapAttemptOutcome(M.Edge):
    def __init__(self, attempt):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(attempt)())())())())()
        super().__init__(inputs=M.Pair(attempt, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class MapExploration(M.Edge):
    """Alternatives and every attempted extension, with newest attempts first."""

    def __init__(self, mapping, alternatives, attempts):
        self.result = M.Pair(
            Lmod.MapExplorationLabel,
            M.Pair(mapping, M.Pair(alternatives, M.Pair(attempts, M.EmptyList))),
        )
        super().__init__(
            inputs=M.Pair(mapping, M.Pair(alternatives, M.Pair(attempts, M.EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class IsMapExploration(M.Edge):
    def __init__(self, term):
        slots = M.Pair(M.EmptyList, M.Pair(M.EmptyList, M.Pair(M.EmptyList, M.EmptyList)))
        self.result = GraphTermShape(term, Lmod.MapExplorationLabel, slots)()
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class MapExplorationMapping(M.Edge):
    def __init__(self, exploration):
        self.result = M.Head(M.Tail(exploration)())()
        super().__init__(inputs=M.Pair(exploration, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class MapExplorationAlternatives(M.Edge):
    def __init__(self, exploration):
        self.result = M.Head(M.Tail(M.Tail(exploration)())())()
        super().__init__(inputs=M.Pair(exploration, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class MapExplorationAttempts(M.Edge):
    def __init__(self, exploration):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(exploration)())())())()
        super().__init__(inputs=M.Pair(exploration, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class MapAttemptHistory(M.Edge):
    def __init__(self, root):
        self.result = M.EmptyList
        if M.IsPair(root)() is M.truth_value:
            rest = MapAttemptHistory(M.Tail(root)())()
            item = M.Head(root)()
            self.result = rest
            if IsMapAttempt(item)() is M.truth_value:
                self.result = M.Pair(item, rest)
        super().__init__(inputs=M.Pair(root, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class MapHistoryMerge(M.Edge):
    def __init__(self, additions, history):
        self.result = history
        if M.IsPair(additions)() is M.truth_value:
            item = M.Head(additions)()
            extended = history
            if GraphChainHasIdentity(history, item)() is M.false_value:
                extended = M.Pair(item, history)
            self.result = MapHistoryMerge(M.Tail(additions)(), extended)()
        super().__init__(inputs=M.Pair(additions, M.Pair(history, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class MapFindAttempt(M.Edge):
    def __init__(self, attempts, mapping, pat, host):
        self.result = M.EmptyList
        if M.IsPair(attempts)() is M.truth_value:
            attempt = M.Head(attempts)()
            if IsMapAttempt(attempt)() is M.truth_value:
                if M.IdentityCompare(MapAttemptMapping(attempt)(), mapping)() is M.truth_value:
                    if M.IdentityCompare(MapAttemptPat(attempt)(), pat)() is M.truth_value:
                        if M.IdentityCompare(MapAttemptHost(attempt)(), host)() is M.truth_value:
                            self.result = attempt
            if M.IdentityCompare(self.result, M.EmptyList)() is M.truth_value:
                self.result = MapFindAttempt(M.Tail(attempts)(), mapping, pat, host)()
        super().__init__(
            inputs=M.Pair(attempts, M.Pair(mapping, M.Pair(pat, M.Pair(host, M.EmptyList)))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class MapRootWithoutAttempts(M.Edge):
    def __init__(self, root):
        self.result = M.EmptyList
        if M.IsPair(root)() is M.truth_value:
            item = M.Head(root)()
            rest = MapRootWithoutAttempts(M.Tail(root)())()
            self.result = rest
            if IsMapAttempt(item)() is M.false_value:
                self.result = M.Pair(item, rest)
        super().__init__(inputs=M.Pair(root, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class MapWithAttempts(M.Edge):
    def __init__(self, mapping, attempts):
        root = GraphChainAppend(MapRootWithoutAttempts(MapRoot(mapping)())(), attempts)()
        self.result = Map(MapPattern(mapping)(), MapHost(mapping)(), root)()
        super().__init__(inputs=M.Pair(mapping, M.Pair(attempts, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class MapAlternativesWithAttempts(M.Edge):
    def __init__(self, alternatives, attempts):
        self.result = M.EmptyList
        if M.IsPair(alternatives)() is M.truth_value:
            self.result = M.Pair(
                MapWithAttempts(M.Head(alternatives)(), attempts)(),
                MapAlternativesWithAttempts(M.Tail(alternatives)(), attempts)(),
            )
        super().__init__(inputs=M.Pair(alternatives, M.Pair(attempts, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class GraphIdentityFieldsAgree(M.Edge):
    def __init__(self, left, right):
        self.result = M.false_value
        if M.IdentityCompare(left, M.EmptyList)() is M.truth_value:
            self.result = M.IdentityCompare(right, M.EmptyList)()
        elif M.IsPair(left)() is M.truth_value:
            if M.IsPair(right)() is M.truth_value:
                if M.IdentityCompare(M.Head(left)(), M.Head(right)())() is M.truth_value:
                    self.result = GraphIdentityFieldsAgree(M.Tail(left)(), M.Tail(right)())()
        super().__init__(inputs=M.Pair(left, M.Pair(right, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class MapRootsAgree(M.Edge):
    def __init__(self, left, right):
        self.result = M.false_value
        if M.IdentityCompare(left, M.EmptyList)() is M.truth_value:
            self.result = M.IdentityCompare(right, M.EmptyList)()
        elif M.IsPair(left)() is M.truth_value:
            if M.IsPair(right)() is M.truth_value:
                left_item = M.Head(left)()
                right_item = M.Head(right)()
                agrees = M.IdentityCompare(left_item, right_item)()
                if IsSend(left_item)() is M.truth_value:
                    if IsSend(right_item)() is M.truth_value:
                        agrees = GraphIdentityFieldsAgree(M.Tail(left_item)(), M.Tail(right_item)())()
                elif IsApart(left_item)() is M.truth_value:
                    if IsApart(right_item)() is M.truth_value:
                        agrees = GraphIdentityFieldsAgree(M.Tail(left_item)(), M.Tail(right_item)())()
                if agrees is M.truth_value:
                    self.result = MapRootsAgree(M.Tail(left)(), M.Tail(right)())()
        super().__init__(inputs=M.Pair(left, M.Pair(right, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class MapReasonsAgree(M.Edge):
    def __init__(self, left, right):
        self.result = M.false_value
        if M.IsPair(left)() is M.truth_value:
            if M.IsPair(right)() is M.truth_value:
                if M.IdentityCompare(M.Head(left)(), M.Head(right)())() is M.truth_value:
                    if M.IdentityCompare(M.Head(right)(), Lmod.ReasonApartLabel)() is M.truth_value:
                        slots = M.Pair(M.EmptyList, M.Pair(M.EmptyList, M.Pair(M.EmptyList, M.EmptyList)))
                        if GraphTermShape(left, Lmod.ReasonApartLabel, slots)() is M.truth_value:
                            left_apart = M.Head(M.Tail(left)())()
                            right_apart = M.Head(M.Tail(right)())()
                            if IsApart(left_apart)() is M.truth_value:
                                if IsApart(right_apart)() is M.truth_value:
                                    self.result = M.AndAtom(
                                        GraphIdentityFieldsAgree(M.Tail(left_apart)(), M.Tail(right_apart)())(),
                                        GraphIdentityFieldsAgree(M.Tail(M.Tail(left)())(), M.Tail(M.Tail(right)())())(),
                                    )()
                    else:
                        self.result = GraphIdentityFieldsAgree(M.Tail(left)(), M.Tail(right)())()
        super().__init__(inputs=M.Pair(left, M.Pair(right, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class MapOutcomesAgree(M.Edge):
    def __init__(self, recorded, checked):
        self.result = M.false_value
        if IsMap(checked)() is M.truth_value:
            if IsMap(recorded)() is M.truth_value:
                if M.IdentityCompare(MapPattern(recorded)(), MapPattern(checked)())() is M.truth_value:
                    if M.IdentityCompare(MapHost(recorded)(), MapHost(checked)())() is M.truth_value:
                        self.result = MapRootsAgree(MapRoot(recorded)(), MapRoot(checked)())()
        else:
            slots = M.Pair(M.EmptyList, M.Pair(M.EmptyList, M.EmptyList))
            if GraphTermShape(recorded, Lmod.MissLabel, slots)() is M.truth_value:
                if GraphTermShape(checked, Lmod.MissLabel, slots)() is M.truth_value:
                    if M.IdentityCompare(M.Head(M.Tail(recorded)())(), M.Head(M.Tail(checked)())())() is M.truth_value:
                        self.result = MapReasonsAgree(
                            M.Head(M.Tail(M.Tail(recorded)())())(),
                            M.Head(M.Tail(M.Tail(checked)())())(),
                        )()
        super().__init__(inputs=M.Pair(recorded, M.Pair(checked, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class MapHistoryValid(M.Edge):
    def __init__(self, history):
        self.result = M.IdentityCompare(history, M.EmptyList)()
        if M.IsPair(history)() is M.truth_value:
            if IsMapAttempt(M.Head(history)())() is M.truth_value:
                self.result = MapHistoryValid(M.Tail(history)())()
        super().__init__(inputs=M.Pair(history, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class MapExploreCandidates(M.Edge):
    def __init__(self, mapping, pat, candidates, attempts):
        self.result = MapExploration(mapping, M.EmptyList, attempts)()
        if M.IsPair(candidates)() is M.truth_value:
            host = M.Head(candidates)()
            attempt = MapFindAttempt(attempts, mapping, pat, host)()
            history = attempts
            outcome = MapExtendOneStep(mapping, pat, host)()
            reusable = M.false_value
            if IsMapAttempt(attempt)() is M.truth_value:
                reusable = MapOutcomesAgree(MapAttemptOutcome(attempt)(), outcome)()
            if reusable is M.false_value:
                attempt = MapAttempt(mapping, pat, host, outcome)()
                history = M.Pair(attempt, attempts)
            rest = MapExploreCandidates(mapping, pat, M.Tail(candidates)(), history)()
            alternatives = MapExplorationAlternatives(rest)()
            if IsMap(outcome)() is M.truth_value:
                alternatives = M.Pair(outcome, alternatives)
            self.result = MapExploration(mapping, alternatives, MapExplorationAttempts(rest)())()
        super().__init__(
            inputs=M.Pair(mapping, M.Pair(pat, M.Pair(candidates, M.Pair(attempts, M.EmptyList)))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class MapExtensionExploration(M.Edge):
    """Retain failures even when no extension is admitted; previous retains prior attempts."""

    def __init__(self, mapping, pat, host_graph, previous=M.EmptyList):
        source = host_graph
        attempts = M.EmptyList
        if IsMap(mapping)() is M.truth_value:
            attempts = MapAttemptHistory(MapRoot(mapping)())()
            if M.IdentityCompare(source, M.EmptyList)() is M.truth_value:
                source = MapHost(mapping)()
        if IsMapExploration(previous)() is M.truth_value:
            previous_attempts = MapExplorationAttempts(previous)()
            if MapHistoryValid(previous_attempts)() is M.truth_value:
                attempts = MapHistoryMerge(attempts, previous_attempts)()
        candidates = GraphChainAppend(
            GraphStoreValues(GraphNodes(source)())(), GraphStoreValues(GraphEdges(source)())()
        )()
        exploration = MapExploreCandidates(mapping, pat, candidates, attempts)()
        history = MapExplorationAttempts(exploration)()
        alternatives = MapAlternativesWithAttempts(MapExplorationAlternatives(exploration)(), history)()
        self.result = MapExploration(mapping, alternatives, history)()
        super().__init__(
            inputs=M.Pair(mapping, M.Pair(pat, M.Pair(host_graph, M.Pair(previous, M.EmptyList)))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class DeletionEdgeClosure(M.Edge):
    """Sweep all dependent edges, including edges attached to removed edges."""

    def __init__(self, graph_version, deleted_nodes, deleted_edges):
        deleted = GraphChainAppend(deleted_nodes, deleted_edges)()
        additional = ChainWithout(DanglingEdges(graph_version, deleted)(), deleted_edges)()
        result = deleted_edges
        if M.IsPair(additional)() is M.truth_value:
            result = DeletionEdgeClosure(
                graph_version, deleted_nodes, GraphChainAppend(additional, deleted_edges)(),
            )()
        super().__init__(
            inputs=M.Pair(graph_version, M.Pair(deleted_nodes, M.Pair(deleted_edges, M.EmptyList))),
            results=result,
        )


class MapExtensionAlternatives(M.Edge):
    """Compatibility projection; accepted maps retain the entire exploration history."""

    def __init__(self, mapping, pat, host_graph):
        self.result = MapExplorationAlternatives(MapExtensionExploration(mapping, pat, host_graph)())()
        super().__init__(
            inputs=M.Pair(mapping, M.Pair(pat, M.Pair(host_graph, M.EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class MapApartCommitments(M.Edge):
    def __init__(self, root, pat):
        self.result = M.EmptyList
        if M.IsPair(root)() is M.truth_value:
            item = M.Head(root)()
            rest = MapApartCommitments(M.Tail(root)(), pat)()
            self.result = rest
            if IsSend(item)() is M.truth_value:
                self.result = M.Pair(Apart(pat, SendPat(item)())(), rest)
        super().__init__(inputs=M.Pair(root, M.Pair(pat, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class MapExtendOneStep(M.Edge):
    """Extend a monomorphism using identity, preserving history and explicit distinctness."""

    def __init__(self, mapping, pat, host):
        self.result = Miss(pat, ReasonShape(mapping)())()
        if IsMap(mapping)() is M.truth_value:
            pattern_graph = MapPattern(mapping)()
            host_graph = MapHost(mapping)()
            root = MapRoot(mapping)()
            if GraphHasElement(pattern_graph, pat)() is M.false_value:
                self.result = Miss(pat, ReasonShape(pat)())()
            elif GraphHasElement(host_graph, host)() is M.false_value:
                self.result = Miss(pat, ReasonShape(host)())()
            elif MapElementKindsAgree(pattern_graph, host_graph, pat, host)() is M.false_value:
                self.result = Miss(pat, ReasonShape(host)())()
            elif MapRootValid(root, pattern_graph, host_graph)() is M.truth_value:
                existing = MappedHostForPat(root, pat)()
                used_host = MappedPatForHost(root, host)()
                if M.Head(existing)() is M.truth_value:
                    self.result = Miss(pat, ReasonAlreadyMapped(pat, M.Tail(existing)())())()
                elif M.Head(used_host)() is M.truth_value:
                    self.result = Miss(pat, ReasonApart(Apart(pat, M.Tail(used_host)())(), pat, host)())()
                else:
                    distinctness = MapApartCommitments(root, pat)()
                    extended_root = M.Pair(Send(pat, host)(), GraphChainAppend(distinctness, root)())
                    inconsistent = MapFirstInconsistentEdge(extended_root, pattern_graph, extended_root)()
                    if M.IdentityCompare(inconsistent, M.EmptyList)() is M.false_value:
                        self.result = Miss(
                            pat, ReasonPositional(M.Head(inconsistent)(), M.Tail(inconsistent)())()
                        )()
                    else:
                        self.result = Map(pattern_graph, host_graph, extended_root)()
        super().__init__(inputs=M.Pair(mapping, M.Pair(pat, M.Pair(host, M.EmptyList))), results=self.result)

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
