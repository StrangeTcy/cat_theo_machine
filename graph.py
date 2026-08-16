from __future__ import annotations

import multiprocessing

from . import context as Ctx
from . import machine as M
from . import proof as P
from . import schemata as S
from . import labels as Lmod
from .search.patricia import SearchPatriciaIsTree, SearchPatriciaEntries
from .search.model import (
    SearchMatchCursor,
    SearchMatchCursorComplete,
    SearchMatchCursorPending,
    SearchMatchCursorRoot,
    SearchState,
    SearchStateCursor,
)


class Hypergraph:
    def __init__(self, constructor_registry, rep_label=M.HypergraphLabel, rep_args=None):
        if constructor_registry is None:
            constructor_registry = M.Tree(M.EmptyList)
            M.AllConstructors = M.set_all_constructors(constructor_registry)
        self.rep = M.HypergraphRep()
        self.default_tests_installed = M.false_value
        self._test_shard_index = M.Zero
        self._test_shard_count = M.one
        self._test_shard_cursor = M.Zero
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


class InstalledLaw(M.Edge):
    def __init__(self, law):
        self.result = M.Pair(Lmod.InstalledLawLabel, M.Pair(law, M.EmptyList))
        super().__init__(inputs=M.Pair(law, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class IsInstalledLaw(M.Edge):
    def __init__(self, term):
        self.result = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if M.TermEqual(M.Head(term)(), Lmod.InstalledLawLabel)() is M.truth_value:
                self.result = M.truth_value
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class InstalledLawValue(M.Edge):
    def __init__(self, installed):
        self.result = M.Head(M.Tail(installed)())()
        super().__init__(inputs=M.Pair(installed, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class Proposal(M.Edge):
    def __init__(self, law, origin):
        self.result = M.Pair(
            Lmod.ProposalLabel,
            M.Pair(law, M.Pair(origin, M.EmptyList)),
        )
        super().__init__(
            inputs=M.Pair(law, M.Pair(origin, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class IsProposal(M.Edge):
    def __init__(self, term):
        self.result = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if M.TermEqual(M.Head(term)(), Lmod.ProposalLabel)() is M.truth_value:
                self.result = M.truth_value
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ProposalLaw(M.Edge):
    def __init__(self, proposal):
        self.result = M.Head(M.Tail(proposal)())()
        super().__init__(inputs=M.Pair(proposal, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ProposalOrigin(M.Edge):
    def __init__(self, proposal):
        self.result = M.Head(M.Tail(M.Tail(proposal)())())()
        super().__init__(inputs=M.Pair(proposal, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class JustifiedBy(M.Edge):
    def __init__(self, proposal, evidence):
        self.result = M.Pair(
            Lmod.JustifiedByLabel,
            M.Pair(proposal, M.Pair(evidence, M.EmptyList)),
        )
        super().__init__(
            inputs=M.Pair(proposal, M.Pair(evidence, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class Approved(M.Edge):
    def __init__(self, proposal, authority):
        self.result = M.Pair(
            Lmod.ApprovedLabel,
            M.Pair(proposal, M.Pair(authority, M.EmptyList)),
        )
        super().__init__(
            inputs=M.Pair(proposal, M.Pair(authority, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class IsApproved(M.Edge):
    def __init__(self, term):
        self.result = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if M.TermEqual(M.Head(term)(), Lmod.ApprovedLabel)() is M.truth_value:
                self.result = M.truth_value
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ApprovedProposal(M.Edge):
    def __init__(self, approved):
        self.result = M.Head(M.Tail(approved)())()
        super().__init__(inputs=M.Pair(approved, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class Rejected(M.Edge):
    def __init__(self, proposal, authority, reason):
        self.result = M.Pair(
            Lmod.RejectedLabel,
            M.Pair(proposal, M.Pair(authority, M.Pair(reason, M.EmptyList))),
        )
        super().__init__(
            inputs=M.Pair(
                proposal,
                M.Pair(authority, M.Pair(reason, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class ProposalEntry(M.Edge):
    def __init__(self, proposal, annotations):
        self.result = M.Pair(
            Lmod.ProposalEntryLabel,
            M.Pair(proposal, M.Pair(annotations, M.EmptyList)),
        )
        super().__init__(
            inputs=M.Pair(proposal, M.Pair(annotations, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class ProposalEntryProposal(M.Edge):
    def __init__(self, entry):
        self.result = M.Head(M.Tail(entry)())()
        super().__init__(inputs=M.Pair(entry, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ProposalEntryAnnotations(M.Edge):
    def __init__(self, entry):
        self.result = M.Head(M.Tail(M.Tail(entry)())())()
        super().__init__(inputs=M.Pair(entry, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ProposalEntryIsApproved(M.Edge):
    def __init__(self, entry):
        proposal = ProposalEntryProposal(entry)()
        annotations = ProposalEntryAnnotations(entry)()
        self.result = M.false_value
        remaining = annotations
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            annotation = M.Head(remaining)()
            if IsApproved(annotation)() is M.truth_value:
                if M.TermEqual(ApprovedProposal(annotation)(), proposal)() is M.truth_value:
                    self.result = M.truth_value
                    remaining = M.EmptyList
                else:
                    remaining = M.Tail(remaining)()
            else:
                remaining = M.Tail(remaining)()
        super().__init__(inputs=M.Pair(entry, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ProposalStore(M.Edge):
    """Immutable proposal-entry chain wrapped as a machine term."""

    def __init__(self, entries):
        self.result = M.Pair(
            Lmod.ProposalStoreLabel,
            M.Pair(entries, M.EmptyList),
        )
        super().__init__(inputs=M.Pair(entries, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ProposalStoreEntries(M.Edge):
    def __init__(self, store):
        self.result = M.Head(M.Tail(store)())()
        super().__init__(inputs=M.Pair(store, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ProposalStoreSubmit(M.Edge):
    def __init__(self, store, proposal):
        reversed_entries = Reverse(ProposalStoreEntries(store)())()
        entries = Reverse(
            M.Pair(ProposalEntry(proposal, M.EmptyList)(), reversed_entries)
        )()
        self.result = ProposalStore(entries)()
        super().__init__(
            inputs=M.Pair(store, M.Pair(proposal, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class ProposalStoreAll(M.Edge):
    def __init__(self, store):
        self.result = ProposalStoreEntries(store)()
        super().__init__(inputs=M.Pair(store, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ProposalStoreAttach(M.Edge):
    def __init__(self, store, proposal, annotation):
        reversed_entries = M.EmptyList
        remaining = ProposalStoreEntries(store)()
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            entry = M.Head(remaining)()
            if M.TermEqual(ProposalEntryProposal(entry)(), proposal)() is M.truth_value:
                annotations = ChainAddMissing(
                    ProposalEntryAnnotations(entry)(),
                    M.Pair(annotation, M.EmptyList),
                )()
                entry = ProposalEntry(proposal, annotations)()
            reversed_entries = M.Pair(entry, reversed_entries)
            remaining = M.Tail(remaining)()
        self.result = ProposalStore(Reverse(reversed_entries)())()
        super().__init__(
            inputs=M.Pair(
                store,
                M.Pair(proposal, M.Pair(annotation, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class ProposalStoreApproved(M.Edge):
    def __init__(self, store):
        reversed_entries = M.EmptyList
        remaining = ProposalStoreEntries(store)()
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            entry = M.Head(remaining)()
            if ProposalEntryIsApproved(entry)() is M.truth_value:
                reversed_entries = M.Pair(entry, reversed_entries)
            remaining = M.Tail(remaining)()
        self.result = Reverse(reversed_entries)()
        super().__init__(inputs=M.Pair(store, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ProposalStoreReject(M.Edge):
    """Retain a rejection annotation on an immutable proposal entry chain."""

    def __init__(self, store, proposal_entry, authority, reason):
        proposal = ProposalEntryProposal(proposal_entry)()
        rejection = Rejected(proposal, authority, reason)()
        self.result = ProposalStoreAttach(store, proposal, rejection)()
        super().__init__(
            inputs=M.Pair(
                store,
                M.Pair(
                    proposal_entry,
                    M.Pair(authority, M.Pair(reason, M.EmptyList)),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class ProposalStoreHistory(M.Edge):
    """Return every proposal entry, with annotations, in submission order."""

    def __init__(self, store):
        self.result = ProposalStoreEntries(store)()
        super().__init__(inputs=M.Pair(store, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class Activation(M.Edge):
    def __init__(self, proposal):
        self.result = M.Pair(
            Lmod.ActivationLabel,
            M.Pair(proposal, M.EmptyList),
        )
        super().__init__(inputs=M.Pair(proposal, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ReasonUnapproved(M.Edge):
    def __init__(self, proposal):
        self.result = M.Pair(
            Lmod.ReasonUnapprovedLabel,
            M.Pair(proposal, M.EmptyList),
        )
        super().__init__(inputs=M.Pair(proposal, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ActivateProposal(M.Edge):
    """Install an approved proposal and return its recorded Next splice."""

    def __init__(self, graph_version, proposal_entry):
        proposal = ProposalEntryProposal(proposal_entry)()
        if ProposalEntryIsApproved(proposal_entry)() is M.false_value:
            self.result = M.Pair(
                M.EmptyList,
                M.Pair(ReasonUnapproved(proposal)(), M.EmptyList),
            )
        else:
            installed = InstallLaw(graph_version, ProposalLaw(proposal)())()
            activation = Activation(proposal)()
            fire = Fire(activation, M.EmptyList)()
            lineage = Next(graph_version, fire, installed)()
            self.result = M.Pair(
                installed,
                M.Pair(lineage, M.EmptyList),
            )
        super().__init__(
            inputs=M.Pair(
                graph_version,
                M.Pair(proposal_entry, M.EmptyList),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class KObligation(M.Edge):
    def __init__(self, obligation_name, structure):
        self.result = M.Pair(Lmod.KObligationLabel, M.Pair(obligation_name, M.Pair(structure, M.EmptyList)))
        super().__init__(inputs=M.Pair(obligation_name, M.Pair(structure, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class KObligationName(M.Edge):
    def __init__(self, obligation):
        self.result = M.Head(M.Tail(obligation)())()
        super().__init__(inputs=M.Pair(obligation, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class KObligationStructure(M.Edge):
    def __init__(self, obligation):
        self.result = M.Head(M.Tail(M.Tail(obligation)())())()
        super().__init__(inputs=M.Pair(obligation, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class UncheckedObligations(M.Edge):
    """Initial immutable state for unknown obligation names."""

    def __init__(self):
        self.result = M.EmptyList
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class ReasonObligation(M.Edge):
    def __init__(self, obligation):
        self.result = M.Pair(
            Lmod.ReasonObligationLabel,
            M.Pair(obligation, M.EmptyList),
        )
        super().__init__(inputs=M.Pair(obligation, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CheckObligation(M.Edge):
    """Check one commit obligation and thread unknown-name state."""

    def __init__(self, graph_version, obligation, unchecked_obligations):
        name = KObligationName(obligation)()
        updated_unchecked = unchecked_obligations
        if M.Compare(name, M.Char("node-count-max"))() is M.truth_value:
            count_pair = M.Count(GraphNodes(graph_version)(), M.AllConstructors)()
            count = M.Head(count_pair)()
            registry = M.Head(M.Tail(count_pair)())()
            bound = KObligationStructure(obligation)()
            too_many = M.NatLess(bound, count, registry)()
            verdict = M.NotAtom(too_many)()
        else:
            verdict = M.truth_value
            seen = M.false_value
            remaining = unchecked_obligations
            while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
                if M.Compare(M.Head(remaining)(), name)() is M.truth_value:
                    seen = M.truth_value
                    remaining = M.EmptyList
                else:
                    remaining = M.Tail(remaining)()
            if M.IdentityCompare(seen, M.false_value)() is M.truth_value:
                updated_unchecked = M.Pair(name, updated_unchecked)
        self.result = M.Pair(
            verdict,
            M.Pair(updated_unchecked, M.EmptyList),
        )
        super().__init__(
            inputs=M.Pair(
                graph_version,
                M.Pair(
                    obligation,
                    M.Pair(unchecked_obligations, M.EmptyList),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class CheckObligationVerdict(M.Edge):
    def __init__(self, checked):
        self.result = M.Head(checked)()
        super().__init__(inputs=M.Pair(checked, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CheckObligationUnchecked(M.Edge):
    def __init__(self, checked):
        self.result = M.Head(M.Tail(checked)())()
        super().__init__(inputs=M.Pair(checked, M.EmptyList), results=self.result)

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
        atom_result = M.false_value
        if M.IsPair(graph)() is M.truth_value:
            if M.TermEqual(M.Head(graph)(), Lmod.GraphVersionLabel)() is M.truth_value:
                atom_result = M.truth_value
        self.result = atom_result
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
        atom_result = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if M.TermEqual(M.Head(term)(), Lmod.SendLabel)() is M.truth_value:
                atom_result = M.truth_value
        self.result = atom_result
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
        self.result = self._lookup(root, pat)
        super().__init__(inputs=M.Pair(root, M.Pair(pat, M.EmptyList)), results=self.result)

    def _lookup(self, root, pat):
        remaining = root
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            item = M.Head(remaining)()
            if IsSend(item)() is M.truth_value:
                if M.TermEqual(SendPat(item)(), pat)() is M.truth_value:
                    return M.Pair(M.truth_value, SendHost(item)())
            remaining = M.Tail(remaining)()
        return M.Pair(M.false_value, M.EmptyList)

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
        self.result = self._consistent(mapping_root, pat_edge, host_edge)
        super().__init__(
            inputs=M.Pair(mapping_root, M.Pair(pat_edge, M.Pair(host_edge, M.EmptyList))),
            results=self.result,
        )

    def _consistent(self, mapping_root, pat_edge, host_edge):
        pat_remaining = EdgeEndpoints(pat_edge)()
        host_remaining = EdgeEndpoints(host_edge)()
        while M.IdentityCompare(pat_remaining, M.EmptyList)() is M.false_value:
            if M.IdentityCompare(host_remaining, M.EmptyList)() is M.truth_value:
                return M.false_value
            pat_endpoint = M.Head(pat_remaining)()
            host_endpoint = M.Head(host_remaining)()
            existing = MappedHostForPat(mapping_root, pat_endpoint)()
            if M.IdentityCompare(M.Head(existing)(), M.truth_value)() is M.truth_value:
                if M.TermEqual(M.Tail(existing)(), host_endpoint)() is M.false_value:
                    return M.false_value
            pat_remaining = M.Tail(pat_remaining)()
            host_remaining = M.Tail(host_remaining)()
        if M.IdentityCompare(host_remaining, M.EmptyList)() is M.false_value:
            return M.false_value
        return M.truth_value

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
        atom_result = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if M.TermEqual(M.Head(term)(), Lmod.LawLabel)() is M.truth_value:
                atom_result = M.truth_value
        self.result = atom_result
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
        self.result = self._complete(mapping, source_graph)
        super().__init__(
            inputs=M.Pair(mapping, M.Pair(source_graph, M.EmptyList)),
            results=self.result,
        )

    def _complete(self, mapping, source_graph):
        if M.IsPair(mapping)() is M.false_value:
            return M.false_value
        if M.TermEqual(M.Head(mapping)(), Lmod.MapLabel)() is M.false_value:
            return M.false_value
        root = M.Head(M.Tail(M.Tail(M.Tail(mapping)())())())()
        probe = MapExtendOneStep(M.EmptyList, M.EmptyList, M.EmptyList)
        remaining = probe._normalize_store(GraphNodes(source_graph)())
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            found = MappedHostForPat(root, M.Head(remaining)())()
            if M.TermEqual(M.Head(found)(), M.truth_value)() is M.false_value:
                return M.false_value
            remaining = M.Tail(remaining)()
        remaining = probe._normalize_store(GraphEdges(source_graph)())
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            pat_edge = M.Head(remaining)()
            found = MappedHostForPat(root, pat_edge)()
            if M.TermEqual(M.Head(found)(), M.truth_value)() is M.false_value:
                return M.false_value
            if EdgeSendConsistent(root, pat_edge, M.Tail(found)())() is M.false_value:
                return M.false_value
            remaining = M.Tail(remaining)()
        return M.truth_value

    def __call__(self):
        return self.result


class LawMapsComplete(M.Edge):
    """
    Step 7. Every interface element must be sent by both K-maps, and every
    edge Send in them must be positionally consistent.

    _law_is_well_formed is deliberately left alone: it only checks the slots
    are Map-shaped, and tightening it would break laws built with incomplete
    K-maps.
    """

    def __init__(self, law):
        self.result = self._complete(law)
        super().__init__(inputs=M.Pair(law, M.EmptyList), results=self.result)

    def _complete(self, law):
        if IsLawTerm(law)() is M.false_value:
            return M.false_value
        interface = LawInterface(law)()
        if MapSendsEveryElement(LawKToLeft(law)(), interface)() is M.false_value:
            return M.false_value
        if MapSendsEveryElement(LawKToRight(law)(), interface)() is M.false_value:
            return M.false_value
        return M.truth_value

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
    """`chain` minus every element appearing in `removals`, order preserved."""

    def __init__(self, chain, removals):
        reversed_kept = M.EmptyList
        remaining = chain
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            item = M.Head(remaining)()
            if ChainHasTerm(removals, item)() is M.false_value:
                reversed_kept = M.Pair(item, reversed_kept)
            remaining = M.Tail(remaining)()
        kept = M.EmptyList
        while M.IdentityCompare(reversed_kept, M.EmptyList)() is M.false_value:
            kept = M.Pair(M.Head(reversed_kept)(), kept)
            reversed_kept = M.Tail(reversed_kept)()
        self.result = kept
        super().__init__(inputs=M.Pair(chain, M.Pair(removals, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class MappedImages(M.Edge):
    """
    Host images, under `root`, of every element of `source` that the interface
    `keep` does not preserve. Elements with no Send contribute nothing.
    """

    def __init__(self, root, source, keep):
        self.result = self._images(root, source, keep)
        super().__init__(
            inputs=M.Pair(root, M.Pair(source, M.Pair(keep, M.EmptyList))),
            results=self.result,
        )

    def _images(self, root, source, keep):
        reversed_hits = M.EmptyList
        remaining = source
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            element = M.Head(remaining)()
            if ChainHasTerm(keep, element)() is M.false_value:
                found = MappedHostForPat(root, element)()
                if M.TermEqual(M.Head(found)(), M.truth_value)() is M.truth_value:
                    reversed_hits = M.Pair(M.Tail(found)(), reversed_hits)
            remaining = M.Tail(remaining)()
        ordered = M.EmptyList
        while M.IdentityCompare(reversed_hits, M.EmptyList)() is M.false_value:
            ordered = M.Pair(M.Head(reversed_hits)(), ordered)
            reversed_hits = M.Tail(reversed_hits)()
        return ordered

    def __call__(self):
        return self.result


class InterfacePreimages(M.Edge):
    """
    The elements of a side graph that the interface pins down: for each K
    element, its image under `k_to_side`.
    """

    def __init__(self, interface, k_to_side):
        probe = MapExtendOneStep(M.EmptyList, M.EmptyList, M.EmptyList)
        root = M.EmptyList
        if M.IsPair(k_to_side)() is M.truth_value:
            if M.TermEqual(M.Head(k_to_side)(), Lmod.MapLabel)() is M.truth_value:
                root = M.Head(M.Tail(M.Tail(M.Tail(k_to_side)())())())()
        reversed_hits = M.EmptyList
        for store in (GraphNodes(interface)(), GraphEdges(interface)()):
            remaining = probe._normalize_store(store)
            while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
                found = MappedHostForPat(root, M.Head(remaining)())()
                if M.TermEqual(M.Head(found)(), M.truth_value)() is M.truth_value:
                    reversed_hits = M.Pair(M.Tail(found)(), reversed_hits)
                remaining = M.Tail(remaining)()
        ordered = M.EmptyList
        while M.IdentityCompare(reversed_hits, M.EmptyList)() is M.false_value:
            ordered = M.Pair(M.Head(reversed_hits)(), ordered)
            reversed_hits = M.Tail(reversed_hits)()
        self.result = ordered
        super().__init__(
            inputs=M.Pair(interface, M.Pair(k_to_side, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class TermSubterms(M.Edge):
    """
    Every subterm occurrence of `term`, parents before children.

    One entry per occurrence: the same structure appearing twice yields two
    entries, because a graph encoding needs a node per occurrence. Variable
    patterns are leaves -- their internal VarTag structure is not walked.
    """

    def __init__(self, term):
        self.result = self._walk(M.Pair(term, M.EmptyList), M.EmptyList)
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def _walk(self, agenda, seen_rev):
        while M.IdentityCompare(agenda, M.EmptyList)() is M.false_value:
            item = M.Head(agenda)()
            agenda = M.Tail(agenda)()
            seen_rev = M.Pair(item, seen_rev)
            if P.IsVarPattern(item)() is M.false_value:
                if M.IsPair(item)() is M.truth_value:
                    children = M.Tail(item)()
                    reversed_children = M.EmptyList
                    while M.IdentityCompare(children, M.EmptyList)() is M.false_value:
                        reversed_children = M.Pair(M.Head(children)(), reversed_children)
                        children = M.Tail(children)()
                    while M.IdentityCompare(reversed_children, M.EmptyList)() is M.false_value:
                        agenda = M.Pair(M.Head(reversed_children)(), agenda)
                        reversed_children = M.Tail(reversed_children)()
        ordered = M.EmptyList
        while M.IdentityCompare(seen_rev, M.EmptyList)() is M.false_value:
            ordered = M.Pair(M.Head(seen_rev)(), ordered)
            seen_rev = M.Tail(seen_rev)()
        return ordered

    def __call__(self):
        return self.result


class EncodeTermAsGraph(M.Edge):
    """
    The simplest term-to-graph encoding: one node per subterm occurrence, one
    edge per constructor application linking the result node to its argument
    nodes in order.

    No such encoder existed in the repo, so this is the literal construction
    the step prescribes.
    """

    def __init__(self, term):
        subterms = TermSubterms(term)()
        reversed_edges = M.EmptyList
        remaining = subterms
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            node = M.Head(remaining)()
            if P.IsVarPattern(node)() is M.false_value:
                if M.IsPair(node)() is M.truth_value:
                    reversed_edges = M.Pair(node, reversed_edges)
            remaining = M.Tail(remaining)()
        edges = M.EmptyList
        while M.IdentityCompare(reversed_edges, M.EmptyList)() is M.false_value:
            edges = M.Pair(M.Head(reversed_edges)(), edges)
            reversed_edges = M.Tail(reversed_edges)()
        self.result = M.Pair(M.HypergraphLabel, M.Pair(subterms, M.Pair(edges, M.EmptyList)))
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SharedSubterms(M.Edge):
    """Subterm occurrences present in both encodings: the interface K."""

    def __init__(self, left_term, right_term):
        right_subterms = TermSubterms(right_term)()
        reversed_shared = M.EmptyList
        remaining = TermSubterms(left_term)()
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            candidate = M.Head(remaining)()
            if ChainHasTerm(right_subterms, candidate)() is M.truth_value:
                if ChainHasTerm(reversed_shared, candidate)() is M.false_value:
                    reversed_shared = M.Pair(candidate, reversed_shared)
            remaining = M.Tail(remaining)()
        shared = M.EmptyList
        while M.IdentityCompare(reversed_shared, M.EmptyList)() is M.false_value:
            shared = M.Pair(M.Head(reversed_shared)(), shared)
            reversed_shared = M.Tail(reversed_shared)()
        self.result = shared
        super().__init__(
            inputs=M.Pair(left_term, M.Pair(right_term, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class IdentitySendsFor(M.Edge):
    """A Send chain carrying each element of `elements` to itself."""

    def __init__(self, elements):
        reversed_sends = M.EmptyList
        remaining = elements
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            element = M.Head(remaining)()
            reversed_sends = M.Pair(Send(element, element)(), reversed_sends)
            remaining = M.Tail(remaining)()
        sends = M.EmptyList
        while M.IdentityCompare(reversed_sends, M.EmptyList)() is M.false_value:
            sends = M.Pair(M.Head(reversed_sends)(), sends)
            reversed_sends = M.Tail(reversed_sends)()
        self.result = sends
        super().__init__(inputs=M.Pair(elements, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CompileRuleToLaw(M.Edge):
    """
    Step 11. A rewrite rule with left pattern P and right result R becomes the
    Law (L, K, R, k_to_left, k_to_right, obligations).

    L and R are the graph encodings of P and R; K is the subterm occurrences
    shared by both, so the K-maps are identity Sends into each side.
    Obligations are empty for now.

    Returns M.EmptyList for a rule this encoding cannot express: a rule with
    no pattern, or a multi-premise rule, whose left side is not a single term.
    """

    def __init__(self, rule):
        self.result = self._compile(rule)
        super().__init__(inputs=M.Pair(rule, M.EmptyList), results=self.result)

    def _compile(self, rule):
        premises = P.RulePremises(rule)()
        if M.IdentityCompare(premises, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        if M.IdentityCompare(M.Tail(premises)(), M.EmptyList)() is M.false_value:
            return M.EmptyList
        pattern = M.Head(premises)()
        replacement = P.RuleReplacement(rule)()
        if M.IdentityCompare(replacement, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        left = EncodeTermAsGraph(pattern)()
        right = EncodeTermAsGraph(replacement)()
        shared = SharedSubterms(pattern, replacement)()
        interface = M.Pair(M.HypergraphLabel, M.Pair(shared, M.Pair(M.EmptyList, M.EmptyList)))
        sends = IdentitySendsFor(shared)()
        k_to_left = Map(interface, left, sends)()
        k_to_right = Map(interface, right, sends)()
        return Law(left, interface, right, k_to_left, k_to_right, M.EmptyList)()

    def __call__(self):
        return self.result


class UncompiledRules(M.Edge):
    """Step 12 term-native record of rules skipped from the trigonometry pack."""

    def __init__(self):
        # Multiple premises cannot be represented by the Step 11 term encoder.
        sine_rule = M.Pair(
            M.Char("triangle_yields_sine_rule_equation"),
            M.Pair(M.Char("multiple premises"), M.EmptyList),
        )
        # Multiple premises cannot be represented by the Step 11 term encoder.
        cosine_rule = M.Pair(
            M.Char("triangle_yields_generic_cosine_relation"),
            M.Pair(M.Char("multiple premises"), M.EmptyList),
        )
        self.result = M.Pair(sine_rule, M.Pair(cosine_rule, M.EmptyList))
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class CompileRulePackToLaws(M.Edge):
    """Compile a Pair chain of rules, retaining compiled Laws and skipped rules."""

    def __init__(self, rules):
        reversed_laws = M.EmptyList
        reversed_uncompiled = M.EmptyList
        remaining = rules
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            rule = M.Head(remaining)()
            law = CompileRuleToLaw(rule)()
            if M.IdentityCompare(law, M.EmptyList)() is M.truth_value:
                reversed_uncompiled = M.Pair(rule, reversed_uncompiled)
            else:
                reversed_laws = M.Pair(law, reversed_laws)
            remaining = M.Tail(remaining)()
        laws = Reverse(reversed_laws)()
        uncompiled = Reverse(reversed_uncompiled)()
        self.result = M.Pair(laws, M.Pair(uncompiled, M.EmptyList))
        super().__init__(inputs=M.Pair(rules, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class InstantiateLaw(M.Edge):
    """Instantiate a compiled term Law with bindings from its legacy Rule match."""

    def __init__(self, law, bindings):
        self.result = M.EmptyList
        if IsLawTerm(law)() is M.truth_value:
            left_nodes = GraphNodes(LawLeft(law)())()
            right_nodes = GraphNodes(LawRight(law)())()
            if M.IdentityCompare(left_nodes, M.EmptyList)() is M.false_value:
                if M.IdentityCompare(right_nodes, M.EmptyList)() is M.false_value:
                    left_term = M.Head(M.Instantiate(M.Head(left_nodes)(), bindings)())()
                    right_term = M.Head(M.Instantiate(M.Head(right_nodes)(), bindings)())()
                    grounded = CompileRuleToLaw(P.Rule(left_term, right_term))()
                    if M.IdentityCompare(grounded, M.EmptyList)() is M.false_value:
                        self.result = Law(
                            LawLeft(grounded)(),
                            LawInterface(grounded)(),
                            LawRight(grounded)(),
                            LawKToLeft(grounded)(),
                            LawKToRight(grounded)(),
                            LawObligations(law)(),
                        )()
        super().__init__(
            inputs=M.Pair(law, M.Pair(bindings, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class ChainSetEqual(M.Edge):
    """Structural set equality of two Pair-chain graph stores."""

    def __init__(self, left, right):
        self.result = self._equal(left, right)
        super().__init__(inputs=M.Pair(left, M.Pair(right, M.EmptyList)), results=self.result)

    def _covered(self, source, target):
        remaining = source
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if ChainHasTerm(target, M.Head(remaining)())() is M.false_value:
                return M.false_value
            remaining = M.Tail(remaining)()
        return M.truth_value

    def _equal(self, left, right):
        left_covered = self._covered(left, right)
        right_covered = self._covered(right, left)
        return M.AndAtom(left_covered, right_covered)()

    def __call__(self):
        return self.result


class GraphStoresEqual(M.Edge):
    """Order-independent structural set equality of graph node and edge stores."""

    def __init__(self, left, right):
        nodes_equal = ChainSetEqual(GraphNodes(left)(), GraphNodes(right)())()
        edges_equal = ChainSetEqual(GraphEdges(left)(), GraphEdges(right)())()
        self.result = M.AndAtom(nodes_equal, edges_equal)()
        super().__init__(inputs=M.Pair(left, M.Pair(right, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class ChainAddMissing(M.Edge):
    """Add structurally absent elements to a Pair-chain store."""

    def __init__(self, store, additions):
        result = store
        remaining = additions
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            element = M.Head(remaining)()
            if ChainHasTerm(result, element)() is M.false_value:
                result = M.Pair(element, result)
            remaining = M.Tail(remaining)()
        self.result = result
        super().__init__(
            inputs=M.Pair(store, M.Pair(additions, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class InstallLaw(M.Edge):
    """Install a Law and its L/K/R elements in a fresh GraphVersion."""

    def __init__(self, graph_version, law):
        nodes = ChainAddMissing(
            GraphNodes(graph_version)(),
            M.Pair(law, M.EmptyList),
        )()
        edges = GraphEdges(graph_version)()

        left = LawLeft(law)()
        nodes = ChainAddMissing(nodes, GraphNodes(left)())()
        edges = ChainAddMissing(edges, GraphEdges(left)())()

        interface = LawInterface(law)()
        nodes = ChainAddMissing(nodes, GraphNodes(interface)())()
        edges = ChainAddMissing(edges, GraphEdges(interface)())()

        right = LawRight(law)()
        nodes = ChainAddMissing(nodes, GraphNodes(right)())()
        edges = ChainAddMissing(edges, GraphEdges(right)())()

        invariants = ChainAddMissing(
            GraphVersionInvariants(graph_version)(),
            M.Pair(InstalledLaw(law)(), M.EmptyList),
        )()
        self.result = GraphVersion(nodes, edges, invariants)()
        super().__init__(
            inputs=M.Pair(graph_version, M.Pair(law, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class InstalledLaws(M.Edge):
    """The installed Laws recorded in a GraphVersion invariant store."""

    def __init__(self, graph_version):
        reversed_laws = M.EmptyList
        remaining = GraphVersionInvariants(graph_version)()
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            invariant = M.Head(remaining)()
            if IsInstalledLaw(invariant)() is M.truth_value:
                reversed_laws = M.Pair(InstalledLawValue(invariant)(), reversed_laws)
            remaining = M.Tail(remaining)()
        self.result = Reverse(reversed_laws)()
        super().__init__(inputs=M.Pair(graph_version, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class GraphElements(M.Edge):
    """Unique structural elements of a graph, nodes followed by absent edges."""

    def __init__(self, graph):
        self.result = ChainAddMissing(GraphNodes(graph)(), GraphEdges(graph)())()
        super().__init__(inputs=M.Pair(graph, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class GraphElementCompatible(M.Edge):
    """Shape compatibility used while expanding Step-10 match states."""

    def __init__(self, pattern, candidate):
        self.result = M.false_value
        if P.IsVarPattern(pattern)() is M.truth_value:
            self.result = M.truth_value
        else:
            pattern_pair = M.IsPair(pattern)()
            candidate_pair = M.IsPair(candidate)()
            if M.AndAtom(pattern_pair, candidate_pair)() is M.truth_value:
                self.result = M.TermEqual(M.Head(pattern)(), M.Head(candidate)())()
            elif M.OrAtom(pattern_pair, candidate_pair)() is M.false_value:
                self.result = M.TermEqual(pattern, candidate)()
        super().__init__(
            inputs=M.Pair(pattern, M.Pair(candidate, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class FirstCompletedMatch(M.Edge):
    """First complete Step-10 SearchMatchCursor mapping for pattern in host."""

    def __init__(self, pattern, host):
        pending = GraphElements(pattern)()
        cursor = SearchMatchCursor(M.EmptyList, pattern, host, pending)()
        start = SearchState(M.EmptyList, M.EmptyList, M.EmptyList, M.one, cursor)()
        self.result = self._find(pattern, host, M.Pair(start, M.EmptyList))
        super().__init__(
            inputs=M.Pair(pattern, M.Pair(host, M.EmptyList)),
            results=self.result,
        )

    def _find(self, pattern, host, frontier):
        remaining_frontier = frontier
        while M.IdentityCompare(remaining_frontier, M.EmptyList)() is M.false_value:
            state = M.Head(remaining_frontier)()
            remaining_frontier = M.Tail(remaining_frontier)()
            cursor = SearchStateCursor(state)()
            if SearchMatchCursorComplete(cursor)() is M.truth_value:
                mapping = Map(pattern, host, SearchMatchCursorRoot(cursor)())()
                if MapSendsEveryElement(mapping, pattern)() is M.truth_value:
                    return mapping
            else:
                pending = SearchMatchCursorPending(cursor)()
                pat = M.Head(pending)()
                rest = M.Tail(pending)()
                mapping = Map(pattern, host, SearchMatchCursorRoot(cursor)())()
                alternatives = MapExtensionAlternatives(mapping, pat, host)()
                while M.IdentityCompare(alternatives, M.EmptyList)() is M.false_value:
                    alternative = M.Head(alternatives)()
                    root = M.Head(M.Tail(M.Tail(M.Tail(alternative)())())())()
                    found = MappedHostForPat(root, pat)()
                    if M.IdentityCompare(M.Head(found)(), M.truth_value)() is M.truth_value:
                        if GraphElementCompatible(pat, M.Tail(found)())() is M.truth_value:
                            child_cursor = SearchMatchCursor(root, pattern, host, rest)()
                            child = SearchState(
                                M.EmptyList,
                                M.EmptyList,
                                M.EmptyList,
                                M.one,
                                child_cursor,
                            )()
                            remaining_frontier = M.Pair(child, remaining_frontier)
                    alternatives = M.Tail(alternatives)()
        return M.EmptyList

    def __call__(self):
        return self.result


class LawMatchBindings(M.Edge):
    """Legacy variable bindings recovered from a completed Law match Map."""

    def __init__(self, law, mapping):
        bindings = M.EmptyList
        root = M.Head(M.Tail(M.Tail(M.Tail(mapping)())())())()
        remaining = GraphNodes(LawLeft(law)())()
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            node = M.Head(remaining)()
            if P.IsVarPattern(node)() is M.truth_value:
                existing = M.FindBinding(bindings, node)()
                if M.IdentityCompare(M.Head(existing)(), M.false_value)() is M.truth_value:
                    found = MappedHostForPat(root, node)()
                    if M.IdentityCompare(M.Head(found)(), M.truth_value)() is M.truth_value:
                        binding = M.Pair(node, M.Pair(M.Tail(found)(), M.EmptyList))
                        bindings = M.Pair(binding, bindings)
            remaining = M.Tail(remaining)()
        self.result = Reverse(bindings)()
        super().__init__(
            inputs=M.Pair(law, M.Pair(mapping, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class FireAny(M.Edge):
    """Fire the first installed Law having a completed Step-10 match."""

    def __init__(self, graph_version, dangling_mode, ledger=M.EmptyList):
        self.result = M.Pair(M.EmptyList, M.Pair(M.EmptyList, M.EmptyList))
        laws = InstalledLaws(graph_version)()
        remaining = laws
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            law = M.Head(remaining)()
            mapping = FirstCompletedMatch(LawLeft(law)(), graph_version)()
            active_law = law
            if M.IdentityCompare(mapping, M.EmptyList)() is M.false_value:
                bindings = LawMatchBindings(law, mapping)()
                if M.IdentityCompare(bindings, M.EmptyList)() is M.false_value:
                    active_law = InstantiateLaw(law, bindings)()
                    if M.IdentityCompare(active_law, M.EmptyList)() is M.false_value:
                        mapping = FirstCompletedMatch(LawLeft(active_law)(), graph_version)()
                if M.IdentityCompare(active_law, M.EmptyList)() is M.false_value:
                    if M.IdentityCompare(mapping, M.EmptyList)() is M.false_value:
                        fired = FireLaw(
                            graph_version,
                            active_law,
                            mapping,
                            dangling_mode,
                            ledger,
                        )()
                        if M.IdentityCompare(M.Head(fired)(), M.EmptyList)() is M.false_value:
                            self.result = fired
                            remaining = M.EmptyList
                        else:
                            remaining = M.Tail(remaining)()
                    else:
                        remaining = M.Tail(remaining)()
                else:
                    remaining = M.Tail(remaining)()
            else:
                remaining = M.Tail(remaining)()
        super().__init__(
            inputs=M.Pair(
                graph_version,
                M.Pair(dangling_mode, M.Pair(ledger, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class FiringRecord(M.Edge):
    """A committed firing together with its exact graph and trace counts."""

    def __init__(
        self,
        law,
        g0,
        g1,
        trace,
        nodes_before,
        nodes_after,
        edges_before,
        edges_after,
        trace_steps,
    ):
        self.result = M.Pair(
            Lmod.FiringRecordLabel,
            M.Pair(
                law,
                M.Pair(
                    g0,
                    M.Pair(
                        g1,
                        M.Pair(
                            trace,
                            M.Pair(
                                nodes_before,
                                M.Pair(
                                    nodes_after,
                                    M.Pair(
                                        edges_before,
                                        M.Pair(
                                            edges_after,
                                            M.Pair(trace_steps, M.EmptyList),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                law,
                M.Pair(
                    g0,
                    M.Pair(
                        g1,
                        M.Pair(
                            trace,
                            M.Pair(
                                nodes_before,
                                M.Pair(
                                    nodes_after,
                                    M.Pair(
                                        edges_before,
                                        M.Pair(
                                            edges_after,
                                            M.Pair(trace_steps, M.EmptyList),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class FiringRecordLaw(M.Edge):
    def __init__(self, record):
        self.result = M.Head(M.Tail(record)())()
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FiringRecordG0(M.Edge):
    def __init__(self, record):
        args = M.Tail(record)()
        args = M.Tail(args)()
        self.result = M.Head(args)()
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FiringRecordG1(M.Edge):
    def __init__(self, record):
        args = M.Tail(record)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        self.result = M.Head(args)()
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FiringRecordTrace(M.Edge):
    def __init__(self, record):
        args = M.Tail(record)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        self.result = M.Head(args)()
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FiringRecordNodesBefore(M.Edge):
    def __init__(self, record):
        args = M.Tail(record)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        self.result = M.Head(args)()
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FiringRecordNodesAfter(M.Edge):
    def __init__(self, record):
        args = M.Tail(record)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        self.result = M.Head(args)()
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FiringRecordEdgesBefore(M.Edge):
    def __init__(self, record):
        args = M.Tail(record)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        self.result = M.Head(args)()
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FiringRecordEdgesAfter(M.Edge):
    def __init__(self, record):
        args = M.Tail(record)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        self.result = M.Head(args)()
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FiringRecordTraceSteps(M.Edge):
    def __init__(self, record):
        args = M.Tail(record)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        self.result = M.Head(args)()
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SignedRational(M.Edge):
    """Exact signed rational (positive_total - negative_total) / samples."""

    def __init__(self, positive_total, negative_total, samples):
        self.result = M.Pair(
            Lmod.SignedRationalLabel,
            M.Pair(
                positive_total,
                M.Pair(negative_total, M.Pair(samples, M.EmptyList)),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                positive_total,
                M.Pair(negative_total, M.Pair(samples, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SignedRationalPositive(M.Edge):
    def __init__(self, signed_rational):
        self.result = M.Head(M.Tail(signed_rational)())()
        super().__init__(inputs=M.Pair(signed_rational, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SignedRationalNegative(M.Edge):
    def __init__(self, signed_rational):
        args = M.Tail(signed_rational)()
        self.result = M.Head(M.Tail(args)())()
        super().__init__(inputs=M.Pair(signed_rational, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SignedRationalSamples(M.Edge):
    def __init__(self, signed_rational):
        args = M.Tail(signed_rational)()
        args = M.Tail(args)()
        self.result = M.Head(M.Tail(args)())()
        super().__init__(inputs=M.Pair(signed_rational, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FiringLedgerByLaw(M.Edge):
    """Group a chronological record shard into Pair law associations."""

    def __init__(self, records):
        groups = M.EmptyList
        remaining_records = records
        while M.IdentityCompare(remaining_records, M.EmptyList)() is M.false_value:
            record = M.Head(remaining_records)()
            law = FiringRecordLaw(record)()
            remaining_groups = groups
            reversed_groups = M.EmptyList
            found = M.false_value
            while M.IdentityCompare(remaining_groups, M.EmptyList)() is M.false_value:
                group = M.Head(remaining_groups)()
                group_law = M.Head(group)()
                if M.TermEqual(group_law, law)() is M.truth_value:
                    group_records = M.Head(M.Tail(group)())()
                    reversed_group_records = M.Reverse(group_records)()
                    group_records = M.Reverse(M.Pair(record, reversed_group_records))()
                    group = M.Pair(law, M.Pair(group_records, M.EmptyList))
                    found = M.truth_value
                reversed_groups = M.Pair(group, reversed_groups)
                remaining_groups = M.Tail(remaining_groups)()
            groups = M.Reverse(reversed_groups)()
            if M.IdentityCompare(found, M.false_value)() is M.truth_value:
                reversed_groups = M.Reverse(groups)()
                groups = M.Reverse(
                    M.Pair(
                        M.Pair(law, M.Pair(M.Pair(record, M.EmptyList), M.EmptyList)),
                        reversed_groups,
                    )
                )()
            remaining_records = M.Tail(remaining_records)()
        self.result = groups
        super().__init__(inputs=M.Pair(records, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FiringLedgerByLawShard(M.Edge):
    """Spawn-safe worker edge for one by-law record shard."""

    def __init__(self, records, result_queue):
        self.result = FiringLedgerByLaw(records)()
        result_queue.put(self.result)
        super().__init__(inputs=M.Pair(records, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FiringLedgerDelta(M.Edge):
    """Exact node totals for one law over one chronological record shard."""

    def __init__(self, records, law, registry):
        positive_total = M.Zero
        negative_total = M.Zero
        samples = M.Zero
        remaining_records = records
        while M.IdentityCompare(remaining_records, M.EmptyList)() is M.false_value:
            record = M.Head(remaining_records)()
            if M.TermEqual(FiringRecordLaw(record)(), law)() is M.truth_value:
                positive_pair = M.Add(
                    positive_total,
                    FiringRecordNodesAfter(record)(),
                    registry,
                )()
                positive_total = M.Head(positive_pair)()
                registry = M.Head(M.Tail(positive_pair)())()
                negative_pair = M.Add(
                    negative_total,
                    FiringRecordNodesBefore(record)(),
                    registry,
                )()
                negative_total = M.Head(negative_pair)()
                registry = M.Head(M.Tail(negative_pair)())()
                samples_pair = M.Succ(samples, registry)()
                samples = M.Head(samples_pair)()
                registry = M.Head(M.Tail(samples_pair)())()
            remaining_records = M.Tail(remaining_records)()
        signed_rational = SignedRational(positive_total, negative_total, samples)()
        self.result = M.Pair(signed_rational, M.Pair(registry, M.EmptyList))
        super().__init__(
            inputs=M.Pair(records, M.Pair(law, M.Pair(registry, M.EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class FiringLedgerDeltaShard(M.Edge):
    """Spawn-safe worker edge for one exact-delta record shard."""

    def __init__(self, records, law, result_queue):
        registry = M.Tree(M.EmptyList)
        self.result = FiringLedgerDelta(records, law, registry)()
        result_queue.put(self.result)
        super().__init__(
            inputs=M.Pair(records, M.Pair(law, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class FiringLedger(M.Edge):
    """Mutable chronological ledger of committed firing records."""

    def __init__(self, registry=M.EmptyList):
        if M.IdentityCompare(registry, M.EmptyList)() is M.truth_value:
            registry = M.AllConstructors
        self.records = M.EmptyList
        self.registry = registry
        super().__init__(inputs=M.Pair(registry, M.EmptyList), results=self.records)

    def append(self, record):
        reversed_records = M.Reverse(self.records)()
        self.records = M.Reverse(M.Pair(record, reversed_records))()
        self.results = self.records
        return self.records

    def all(self):
        return self.records

    def by_law(self):
        record_count = 0
        remaining_records = self.records
        while M.IdentityCompare(remaining_records, M.EmptyList)() is M.false_value:
            record_count = record_count + 1
            remaining_records = M.Tail(remaining_records)()
        try:
            worker_capacity = multiprocessing.cpu_count()
        except NotImplementedError:
            return FiringLedgerByLaw(self.records)()
        if worker_capacity > record_count:
            worker_capacity = record_count
        if worker_capacity < 2:
            return FiringLedgerByLaw(self.records)()
        try:
            mp_context = multiprocessing.get_context("fork")
        except ValueError:
            mp_context = multiprocessing.get_context("spawn")

        shard_width = record_count // worker_capacity
        wide_shards = record_count % worker_capacity
        workers = M.EmptyList
        remaining_records = self.records
        slot = 0
        while slot != worker_capacity:
            active_width = shard_width
            if slot < wide_shards:
                active_width = active_width + 1
            reversed_shard = M.EmptyList
            copied = 0
            while copied != active_width:
                reversed_shard = M.Pair(M.Head(remaining_records)(), reversed_shard)
                remaining_records = M.Tail(remaining_records)()
                copied = copied + 1
            shard = M.Reverse(reversed_shard)()
            result_queue = mp_context.Queue()
            process = mp_context.Process(
                target=FiringLedgerByLawShard,
                args=(shard, result_queue),
            )
            process.start()
            worker = M.Pair(process, M.Pair(result_queue, M.EmptyList))
            workers = M.Pair(worker, workers)
            slot = slot + 1
        workers = M.Reverse(workers)()

        groups = M.EmptyList
        remaining_workers = workers
        while M.IdentityCompare(remaining_workers, M.EmptyList)() is M.false_value:
            worker = M.Head(remaining_workers)()
            process = M.Head(worker)()
            result_queue = M.Head(M.Tail(worker)())()
            shard_groups = result_queue.get()
            process.join()
            result_queue.close()
            remaining_shard_groups = shard_groups
            while M.IdentityCompare(remaining_shard_groups, M.EmptyList)() is M.false_value:
                shard_group = M.Head(remaining_shard_groups)()
                shard_law = M.Head(shard_group)()
                shard_records = M.Head(M.Tail(shard_group)())()
                remaining_groups = groups
                reversed_groups = M.EmptyList
                found = M.false_value
                while M.IdentityCompare(remaining_groups, M.EmptyList)() is M.false_value:
                    group = M.Head(remaining_groups)()
                    group_law = M.Head(group)()
                    if M.TermEqual(group_law, shard_law)() is M.truth_value:
                        group_records = M.Head(M.Tail(group)())()
                        reversed_group_records = M.Reverse(group_records)()
                        remaining_shard_records = shard_records
                        while M.IdentityCompare(
                            remaining_shard_records,
                            M.EmptyList,
                        )() is M.false_value:
                            reversed_group_records = M.Pair(
                                M.Head(remaining_shard_records)(),
                                reversed_group_records,
                            )
                            remaining_shard_records = M.Tail(remaining_shard_records)()
                        group = M.Pair(
                            shard_law,
                            M.Pair(M.Reverse(reversed_group_records)(), M.EmptyList),
                        )
                        found = M.truth_value
                    reversed_groups = M.Pair(group, reversed_groups)
                    remaining_groups = M.Tail(remaining_groups)()
                groups = M.Reverse(reversed_groups)()
                if M.IdentityCompare(found, M.false_value)() is M.truth_value:
                    reversed_groups = M.Reverse(groups)()
                    groups = M.Reverse(M.Pair(shard_group, reversed_groups))()
                remaining_shard_groups = M.Tail(remaining_shard_groups)()
            remaining_workers = M.Tail(remaining_workers)()
        return groups

    def size_delta(self, law):
        record_count = 0
        remaining_records = self.records
        while M.IdentityCompare(remaining_records, M.EmptyList)() is M.false_value:
            record_count = record_count + 1
            remaining_records = M.Tail(remaining_records)()
        try:
            worker_capacity = multiprocessing.cpu_count()
        except NotImplementedError:
            delta_pair = FiringLedgerDelta(self.records, law, self.registry)()
            self.registry = M.Head(M.Tail(delta_pair)())()
            return M.Head(delta_pair)()
        if worker_capacity > record_count:
            worker_capacity = record_count
        if worker_capacity < 2:
            delta_pair = FiringLedgerDelta(self.records, law, self.registry)()
            self.registry = M.Head(M.Tail(delta_pair)())()
            return M.Head(delta_pair)()
        try:
            mp_context = multiprocessing.get_context("fork")
        except ValueError:
            mp_context = multiprocessing.get_context("spawn")

        shard_width = record_count // worker_capacity
        wide_shards = record_count % worker_capacity
        workers = M.EmptyList
        remaining_records = self.records
        slot = 0
        while slot != worker_capacity:
            active_width = shard_width
            if slot < wide_shards:
                active_width = active_width + 1
            reversed_shard = M.EmptyList
            copied = 0
            while copied != active_width:
                reversed_shard = M.Pair(M.Head(remaining_records)(), reversed_shard)
                remaining_records = M.Tail(remaining_records)()
                copied = copied + 1
            shard = M.Reverse(reversed_shard)()
            result_queue = mp_context.Queue()
            process = mp_context.Process(
                target=FiringLedgerDeltaShard,
                args=(shard, law, result_queue),
            )
            process.start()
            worker = M.Pair(process, M.Pair(result_queue, M.EmptyList))
            workers = M.Pair(worker, workers)
            slot = slot + 1
        workers = M.Reverse(workers)()

        positive_total = M.Zero
        negative_total = M.Zero
        samples = M.Zero
        registry = self.registry
        remaining_workers = workers
        while M.IdentityCompare(remaining_workers, M.EmptyList)() is M.false_value:
            worker = M.Head(remaining_workers)()
            process = M.Head(worker)()
            result_queue = M.Head(M.Tail(worker)())()
            partial_pair = result_queue.get()
            process.join()
            result_queue.close()
            partial = M.Head(partial_pair)()
            positive_pair = M.Add(
                positive_total,
                SignedRationalPositive(partial)(),
                registry,
            )()
            positive_total = M.Head(positive_pair)()
            registry = M.Head(M.Tail(positive_pair)())()
            negative_pair = M.Add(
                negative_total,
                SignedRationalNegative(partial)(),
                registry,
            )()
            negative_total = M.Head(negative_pair)()
            registry = M.Head(M.Tail(negative_pair)())()
            samples_pair = M.Add(
                samples,
                SignedRationalSamples(partial)(),
                registry,
            )()
            samples = M.Head(samples_pair)()
            registry = M.Head(M.Tail(samples_pair)())()
            remaining_workers = M.Tail(remaining_workers)()
        self.registry = registry
        return SignedRational(positive_total, negative_total, samples)()

    def __call__(self):
        return self.records


CENSUS_MATCH_CAP = M.GMPRep("100")


class PatternCensusMatchCount(M.Edge):
    """Count completed Step-10 match states up to a machine Nat cap."""

    def __init__(self, pattern_graph, host_version, match_cap, registry):
        cap_pair = M.NatFromRep(match_cap, registry)()
        cap = M.Head(cap_pair)()
        registry = M.Head(M.Tail(cap_pair)())()
        completed = M.Zero
        pending = GraphElements(pattern_graph)()
        cursor = SearchMatchCursor(M.EmptyList, pattern_graph, host_version, pending)()
        start = SearchState(M.EmptyList, M.EmptyList, M.EmptyList, M.one, cursor)()
        frontier = M.Pair(start, M.EmptyList)

        while M.IdentityCompare(frontier, M.EmptyList)() is M.false_value:
            if M.NatEq(completed, cap, registry)() is M.truth_value:
                frontier = M.EmptyList
            else:
                state = M.Head(frontier)()
                frontier = M.Tail(frontier)()
                cursor = SearchStateCursor(state)()
                if SearchMatchCursorComplete(cursor)() is M.truth_value:
                    mapping = Map(
                        pattern_graph,
                        host_version,
                        SearchMatchCursorRoot(cursor)(),
                    )()
                    if MapSendsEveryElement(mapping, pattern_graph)() is M.truth_value:
                        completed_pair = M.Succ(completed, registry)()
                        completed = M.Head(completed_pair)()
                        registry = M.Head(M.Tail(completed_pair)())()
                else:
                    pending = SearchMatchCursorPending(cursor)()
                    pat = M.Head(pending)()
                    rest = M.Tail(pending)()
                    mapping = Map(
                        pattern_graph,
                        host_version,
                        SearchMatchCursorRoot(cursor)(),
                    )()
                    alternatives = MapExtensionAlternatives(mapping, pat, host_version)()
                    while M.IdentityCompare(alternatives, M.EmptyList)() is M.false_value:
                        alternative = M.Head(alternatives)()
                        root = M.Head(M.Tail(M.Tail(M.Tail(alternative)())())())()
                        child_cursor = SearchMatchCursor(
                            root,
                            pattern_graph,
                            host_version,
                            rest,
                        )()
                        child = SearchState(
                            M.EmptyList,
                            M.EmptyList,
                            M.EmptyList,
                            M.one,
                            child_cursor,
                        )()
                        frontier = M.Pair(child, frontier)
                        alternatives = M.Tail(alternatives)()

        self.result = M.Pair(completed, M.Pair(registry, M.EmptyList))
        super().__init__(
            inputs=M.Pair(
                pattern_graph,
                M.Pair(
                    host_version,
                    M.Pair(match_cap, M.Pair(registry, M.EmptyList)),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class PatternCensusShard(M.Edge):
    """Spawn-safe census worker for one chronological version shard."""

    def __init__(self, pattern_graph, versions, match_cap, result_queue):
        registry = M.Tree(M.EmptyList)
        reversed_counts = M.EmptyList
        remaining_versions = versions
        while M.IdentityCompare(remaining_versions, M.EmptyList)() is M.false_value:
            counted = PatternCensusMatchCount(
                pattern_graph,
                M.Head(remaining_versions)(),
                match_cap,
                registry,
            )()
            reversed_counts = M.Pair(M.Head(counted)(), reversed_counts)
            registry = M.Head(M.Tail(counted)())()
            remaining_versions = M.Tail(remaining_versions)()
        self.result = M.Reverse(reversed_counts)()
        result_queue.put(self.result)
        super().__init__(
            inputs=M.Pair(
                pattern_graph,
                M.Pair(versions, M.Pair(match_cap, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class PatternCensus(M.Edge):
    """
    Count a given pattern in each version, preserving Pair-chain input order.

    `match_cap` is a machine GMP value with a default of 100. Keeping it as an
    input allows later machine policy to tune the bound without changing this
    operation. Independent version shards run in parallel and are reduced in
    deterministic shard order. The firing ledger supplies the constructor
    registry; its records are intentionally not consulted.
    """

    def __init__(
        self,
        ledger,
        pattern_graph,
        versions,
        match_cap=CENSUS_MATCH_CAP,
    ):
        version_count = 0
        remaining_versions = versions
        while M.IdentityCompare(remaining_versions, M.EmptyList)() is M.false_value:
            version_count = version_count + 1
            remaining_versions = M.Tail(remaining_versions)()

        try:
            worker_capacity = multiprocessing.cpu_count()
        except NotImplementedError:
            worker_capacity = 1
        if worker_capacity > version_count:
            worker_capacity = version_count

        if worker_capacity < 2:
            reversed_counts = M.EmptyList
            registry = ledger.registry
            remaining_versions = versions
            while M.IdentityCompare(remaining_versions, M.EmptyList)() is M.false_value:
                counted = PatternCensusMatchCount(
                    pattern_graph,
                    M.Head(remaining_versions)(),
                    match_cap,
                    registry,
                )()
                reversed_counts = M.Pair(M.Head(counted)(), reversed_counts)
                registry = M.Head(M.Tail(counted)())()
                remaining_versions = M.Tail(remaining_versions)()
            ledger.registry = registry
            self.result = M.Reverse(reversed_counts)()
        else:
            try:
                mp_context = multiprocessing.get_context("fork")
            except ValueError:
                mp_context = multiprocessing.get_context("spawn")

            shard_width = version_count // worker_capacity
            wide_shards = version_count % worker_capacity
            workers = M.EmptyList
            remaining_versions = versions
            slot = 0
            while slot != worker_capacity:
                active_width = shard_width
                if slot < wide_shards:
                    active_width = active_width + 1
                reversed_shard = M.EmptyList
                copied = 0
                while copied != active_width:
                    reversed_shard = M.Pair(
                        M.Head(remaining_versions)(),
                        reversed_shard,
                    )
                    remaining_versions = M.Tail(remaining_versions)()
                    copied = copied + 1
                shard = M.Reverse(reversed_shard)()
                result_queue = mp_context.Queue()
                process = mp_context.Process(
                    target=PatternCensusShard,
                    args=(pattern_graph, shard, match_cap, result_queue),
                )
                process.start()
                workers = M.Pair(
                    M.Pair(process, M.Pair(result_queue, M.EmptyList)),
                    workers,
                )
                slot = slot + 1
            workers = M.Reverse(workers)()

            reversed_counts = M.EmptyList
            remaining_workers = workers
            while M.IdentityCompare(remaining_workers, M.EmptyList)() is M.false_value:
                worker = M.Head(remaining_workers)()
                process = M.Head(worker)()
                result_queue = M.Head(M.Tail(worker)())()
                shard_counts = result_queue.get()
                process.join()
                result_queue.close()
                remaining_shard_counts = shard_counts
                while M.IdentityCompare(
                    remaining_shard_counts,
                    M.EmptyList,
                )() is M.false_value:
                    reversed_counts = M.Pair(
                        M.Head(remaining_shard_counts)(),
                        reversed_counts,
                    )
                    remaining_shard_counts = M.Tail(remaining_shard_counts)()
                remaining_workers = M.Tail(remaining_workers)()
            self.result = M.Reverse(reversed_counts)()

        super().__init__(
            inputs=M.Pair(
                ledger,
                M.Pair(
                    pattern_graph,
                    M.Pair(versions, M.Pair(match_cap, M.EmptyList)),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


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

    def __init__(
        self,
        graph_version,
        law,
        mapping,
        dangling_mode,
        ledger=M.EmptyList,
    ):
        self.probe = MapExtendOneStep(M.EmptyList, M.EmptyList, M.EmptyList)
        self.result = self._fire(graph_version, law, mapping, dangling_mode, ledger)
        super().__init__(
            inputs=M.Pair(
                graph_version,
                M.Pair(
                    law,
                    M.Pair(
                        mapping,
                        M.Pair(dangling_mode, M.Pair(ledger, M.EmptyList)),
                    ),
                ),
            ),
            results=self.result,
        )

    def _append(self, trace, entry):
        reversed_trace = M.EmptyList
        remaining = trace
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            reversed_trace = M.Pair(M.Head(remaining)(), reversed_trace)
            remaining = M.Tail(remaining)()
        grown = M.Pair(entry, reversed_trace)
        ordered = M.EmptyList
        while M.IdentityCompare(grown, M.EmptyList)() is M.false_value:
            ordered = M.Pair(M.Head(grown)(), ordered)
            grown = M.Tail(grown)()
        return ordered

    def _reject(self, trace, stage):
        rejected = M.Pair(Lmod.FireRejectedLabel, M.Pair(stage, M.EmptyList))
        return M.Pair(M.EmptyList, M.Pair(self._append(trace, rejected), M.EmptyList))

    def _fire(self, graph_version, law, mapping, dangling_mode, ledger):
        trace = M.EmptyList

        # --- MatchPrepared -------------------------------------------------
        prepared = M.Pair(Lmod.MatchPreparedLabel, M.Pair(law, M.Pair(mapping, M.EmptyList)))
        if LawMapsComplete(law)() is M.false_value:
            return self._reject(trace, prepared)
        left = LawLeft(law)()
        if MapSendsEveryElement(mapping, left)() is M.false_value:
            return self._reject(trace, prepared)
        trace = self._append(trace, prepared)
        root = M.Head(M.Tail(M.Tail(M.Tail(mapping)())())())()

        # --- DeletionAdmitted ----------------------------------------------
        interface = LawInterface(law)()
        kept_left = InterfacePreimages(interface, LawKToLeft(law)())()
        left_nodes = self.probe._normalize_store(GraphNodes(left)())
        left_edges = self.probe._normalize_store(GraphEdges(left)())
        deleted_nodes = MappedImages(root, left_nodes, kept_left)()
        deleted_edges = MappedImages(root, left_edges, kept_left)()
        stranded = ChainWithout(DanglingEdges(graph_version, deleted_nodes)(), deleted_edges)()
        if M.IdentityCompare(stranded, M.EmptyList)() is M.false_value:
            if M.TermEqual(dangling_mode, DanglingForbid()())() is M.truth_value:
                admitted = M.Pair(
                    Lmod.DeletionAdmittedLabel,
                    M.Pair(deleted_nodes, M.Pair(deleted_edges, M.Pair(stranded, M.EmptyList))),
                )
                return self._reject(trace, admitted)
            remaining = stranded
            while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
                deleted_edges = M.Pair(M.Head(remaining)(), deleted_edges)
                remaining = M.Tail(remaining)()
        trace = self._append(
            trace,
            M.Pair(
                Lmod.DeletionAdmittedLabel,
                M.Pair(deleted_nodes, M.Pair(deleted_edges, M.Pair(stranded, M.EmptyList))),
            ),
        )

        # --- ComplementProduced --------------------------------------------
        host_nodes = self.probe._normalize_store(GraphNodes(graph_version)())
        host_edges = self.probe._normalize_store(GraphEdges(graph_version)())
        new_nodes = ChainWithout(host_nodes, deleted_nodes)()
        new_edges = ChainWithout(host_edges, deleted_edges)()
        trace = self._append(
            trace,
            M.Pair(Lmod.ComplementProducedLabel, M.Pair(new_nodes, M.Pair(new_edges, M.EmptyList))),
        )

        # --- InsertionPrepared ----------------------------------------------
        right = LawRight(law)()
        kept_right = InterfacePreimages(interface, LawKToRight(law)())()
        right_nodes = self.probe._normalize_store(GraphNodes(right)())
        right_edges = self.probe._normalize_store(GraphEdges(right)())
        inserted_nodes = ChainWithout(right_nodes, kept_right)()
        inserted_edges = ChainWithout(right_edges, kept_right)()
        remaining = inserted_nodes
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            new_nodes = M.Pair(M.Head(remaining)(), new_nodes)
            remaining = M.Tail(remaining)()
        remaining = inserted_edges
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            new_edges = M.Pair(M.Head(remaining)(), new_edges)
            remaining = M.Tail(remaining)()
        trace = self._append(
            trace,
            M.Pair(
                Lmod.InsertionPreparedLabel,
                M.Pair(inserted_nodes, M.Pair(inserted_edges, M.EmptyList)),
            ),
        )

        # --- GraphVersionCommitted ------------------------------------------
        committed = GraphVersion(new_nodes, new_edges, GraphVersionInvariants(graph_version)())()
        unchecked = UncheckedObligations()()
        remaining_obligations = LawObligations(law)()
        while M.IdentityCompare(remaining_obligations, M.EmptyList)() is M.false_value:
            obligation = M.Head(remaining_obligations)()
            checked = CheckObligation(committed, obligation, unchecked)()
            unchecked = CheckObligationUnchecked(checked)()
            if CheckObligationVerdict(checked)() is M.false_value:
                trace = self._append(trace, ReasonObligation(obligation)())
                return M.Pair(M.EmptyList, M.Pair(trace, M.EmptyList))
            remaining_obligations = M.Tail(remaining_obligations)()
        fire = Fire(law, mapping)()
        trace = self._append(
            trace,
            M.Pair(Lmod.GraphVersionCommittedLabel, M.Pair(LawObligations(law)(), M.EmptyList)),
        )
        trace = self._append(trace, Next(graph_version, fire, committed)())
        if M.IdentityCompare(ledger, M.EmptyList)() is M.false_value:
            registry = ledger.registry
            nodes_before_pair = M.Count(GraphNodes(graph_version)(), registry)()
            nodes_before = M.Head(nodes_before_pair)()
            registry = M.Head(M.Tail(nodes_before_pair)())()
            nodes_after_pair = M.Count(GraphNodes(committed)(), registry)()
            nodes_after = M.Head(nodes_after_pair)()
            registry = M.Head(M.Tail(nodes_after_pair)())()
            edges_before_pair = M.Count(GraphEdges(graph_version)(), registry)()
            edges_before = M.Head(edges_before_pair)()
            registry = M.Head(M.Tail(edges_before_pair)())()
            edges_after_pair = M.Count(GraphEdges(committed)(), registry)()
            edges_after = M.Head(edges_after_pair)()
            registry = M.Head(M.Tail(edges_after_pair)())()
            trace_steps_pair = M.Count(trace, registry)()
            trace_steps = M.Head(trace_steps_pair)()
            ledger.registry = M.Head(M.Tail(trace_steps_pair)())()
            ledger.append(
                FiringRecord(
                    law,
                    graph_version,
                    committed,
                    trace,
                    nodes_before,
                    nodes_after,
                    edges_before,
                    edges_after,
                    trace_steps,
                )()
            )
        return M.Pair(committed, M.Pair(trace, M.EmptyList))

    def __call__(self):
        return self.result


class DanglingEdges(M.Edge):
    """
    Edges of `graph_version` that touch a deleted node.

    Derived on demand by scanning the edge store: nothing is stored, no term
    records the result, and class Boundary is untouched. `deleted_nodes` and
    the answer are both Pair chains.
    """

    def __init__(self, graph_version, deleted_nodes):
        self.result = self._scan(graph_version, deleted_nodes)
        super().__init__(
            inputs=M.Pair(graph_version, M.Pair(deleted_nodes, M.EmptyList)),
            results=self.result,
        )

    def _touches_deleted(self, endpoints, deleted_nodes):
        remaining = endpoints
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            endpoint = M.Head(remaining)()
            candidates = deleted_nodes
            while M.IdentityCompare(candidates, M.EmptyList)() is M.false_value:
                if M.TermEqual(M.Head(candidates)(), endpoint)() is M.truth_value:
                    return M.truth_value
                candidates = M.Tail(candidates)()
            remaining = M.Tail(remaining)()
        return M.false_value

    def _scan(self, graph_version, deleted_nodes):
        probe = MapExtendOneStep(M.EmptyList, M.EmptyList, M.EmptyList)
        edges = probe._normalize_store(GraphEdges(graph_version)())
        reversed_hits = M.EmptyList
        remaining = edges
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            edge = M.Head(remaining)()
            if self._touches_deleted(EdgeEndpoints(edge)(), deleted_nodes) is M.truth_value:
                reversed_hits = M.Pair(edge, reversed_hits)
            remaining = M.Tail(remaining)()
        ordered = M.EmptyList
        while M.IdentityCompare(reversed_hits, M.EmptyList)() is M.false_value:
            ordered = M.Pair(M.Head(reversed_hits)(), ordered)
            reversed_hits = M.Tail(reversed_hits)()
        return ordered

    def __call__(self):
        return self.result


class MapExtensionAlternatives(M.Edge):
    """
    Every one-step extension of `mapping` that sends `pat` somewhere legal.

    `host_graph` is the graph to draw candidates from; pass M.EmptyList to use
    the mapping's own host graph. Each candidate is put through
    MapExtendOneStep, so the admitted extensions are exactly those the matcher
    would accept -- including the Step 3 positional check -- with no logic
    duplicated here.

    Returns a Pair chain of Map terms, in host-store order. MapExtendOneStep
    keeps its single-result behaviour: its answer is the Head of this chain.
    """

    def __init__(self, mapping, pat, host_graph):
        self.result = self._alternatives(mapping, pat, host_graph)
        super().__init__(
            inputs=M.Pair(mapping, M.Pair(pat, M.Pair(host_graph, M.EmptyList))),
            results=self.result,
        )

    def _candidates(self, mapping, host_graph):
        source = host_graph
        if M.IdentityCompare(source, M.EmptyList)() is M.truth_value:
            if M.IsPair(mapping)() is M.truth_value:
                if M.TermEqual(M.Head(mapping)(), Lmod.MapLabel)() is M.truth_value:
                    source = M.Head(M.Tail(M.Tail(mapping)())())()
        if M.IdentityCompare(source, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        probe = MapExtendOneStep(M.EmptyList, M.EmptyList, M.EmptyList)
        reversed_collected = M.EmptyList
        remaining = probe._normalize_store(GraphNodes(source)())
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            reversed_collected = M.Pair(M.Head(remaining)(), reversed_collected)
            remaining = M.Tail(remaining)()
        remaining = probe._normalize_store(GraphEdges(source)())
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            reversed_collected = M.Pair(M.Head(remaining)(), reversed_collected)
            remaining = M.Tail(remaining)()
        collected = M.EmptyList
        while M.IdentityCompare(reversed_collected, M.EmptyList)() is M.false_value:
            collected = M.Pair(M.Head(reversed_collected)(), collected)
            reversed_collected = M.Tail(reversed_collected)()
        return collected

    def _alternatives(self, mapping, pat, host_graph):
        reversed_hits = M.EmptyList
        remaining = self._candidates(mapping, host_graph)
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            candidate = M.Head(remaining)()
            extended = MapExtendOneStep(mapping, pat, candidate)()
            if M.IsPair(extended)() is M.truth_value:
                if M.TermEqual(M.Head(extended)(), Lmod.MapLabel)() is M.truth_value:
                    reversed_hits = M.Pair(extended, reversed_hits)
            remaining = M.Tail(remaining)()
        ordered = M.EmptyList
        while M.IdentityCompare(reversed_hits, M.EmptyList)() is M.false_value:
            ordered = M.Pair(M.Head(reversed_hits)(), ordered)
            reversed_hits = M.Tail(reversed_hits)()
        return ordered

    def __call__(self):
        return self.result


class MapExtendOneStep(M.Edge):
    def __init__(self, mapping, pat, host):
        self.mapping = mapping
        self.pat = pat
        self.host = host
        self.result = self._step()
        super().__init__(inputs=M.Pair(mapping, M.Pair(pat, M.Pair(host, M.EmptyList))), results=self.result)

    def _reason(self, text):
        atom = M.Atom()
        atom.value = text
        return atom

    def _is_graph_version(self, graph):
        return IsGraphVersion(graph)()

    def _graph_version_nodes(self, graph):
        return GraphVersionNodes(graph)()

    def _graph_version_edges(self, graph):
        return GraphVersionEdges(graph)()

    def _graph_version_invariants(self, graph):
        return GraphVersionInvariants(graph)()

    def _mapping_pattern_graph(self):
        return M.Head(M.Tail(self.mapping)())()

    def _mapping_host_graph(self):
        return M.Head(M.Tail(M.Tail(self.mapping)())())()

    def _mapping_root(self):
        return M.Head(M.Tail(M.Tail(M.Tail(self.mapping)())())())()

    def _is_patricia_tree(self, store):
        return SearchPatriciaIsTree(store)()

    def _flatten_patricia_to_values(self, tree):
        entries = SearchPatriciaEntries(tree)()
        values = M.EmptyList
        remaining = entries
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            entry = M.Head(remaining)()
            value = M.Head(M.Tail(entry)())()
            values = M.Pair(value, values)
            remaining = M.Tail(remaining)()
        return values

    def _normalize_store(self, store):
        if M.IdentityCompare(store, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        if self._is_patricia_tree(store) is M.truth_value:
            return self._flatten_patricia_to_values(store)
        return store

    def _is_law(self, term):
        if M.IsPair(term)() is M.false_value:
            return M.false_value
        if M.TermEqual(M.Head(term)(), Lmod.LawLabel)() is M.truth_value:
            return M.truth_value
        return M.false_value

    def _law_left(self, law):
        return M.Head(M.Tail(law)())()

    def _law_interface(self, law):
        return M.Head(M.Tail(M.Tail(law)())())()

    def _law_right(self, law):
        return M.Head(M.Tail(M.Tail(M.Tail(law)())())())()

    def _law_k_to_left(self, law):
        return M.Head(M.Tail(M.Tail(M.Tail(M.Tail(law)())())())())()

    def _law_k_to_right(self, law):
        return M.Head(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(law)())())())())())()

    def _law_obligations(self, law):
        return M.Head(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(law)())())())())())())()

    def _is_valid_map(self, potential_map):
        if M.IsPair(potential_map)() is M.false_value:
            return M.false_value
        if M.TermEqual(M.Head(potential_map)(), Lmod.MapLabel)() is M.truth_value:
            return M.truth_value
        return M.false_value

    def _law_is_well_formed(self, law):
        if self._is_law(law) is M.false_value:
            return M.false_value
        k_to_left = self._law_k_to_left(law)
        k_to_right = self._law_k_to_right(law)
        if self._is_valid_map(k_to_left) is M.false_value:
            return M.false_value
        if self._is_valid_map(k_to_right) is M.false_value:
            return M.false_value
        return M.truth_value

    def _graph_nodes(self, graph):
        return GraphNodes(graph)()

    def _graph_edges(self, graph):
        return GraphEdges(graph)()

    def _chain_has_term(self, chain, term):
        remaining = chain
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if M.TermEqual(M.Head(remaining)(), term)() is M.truth_value:
                return M.truth_value
            remaining = M.Tail(remaining)()
        return M.false_value

    def _graph_has_element(self, graph, term):
        nodes = self._normalize_store(self._graph_nodes(graph))
        if self._chain_has_term(nodes, term) is M.truth_value:
            return M.truth_value
        edges = self._normalize_store(self._graph_edges(graph))
        return self._chain_has_term(edges, term)

    def _is_send(self, term):
        return IsSend(term)()

    def _is_apart(self, term):
        if M.IsPair(term)() is M.false_value:
            return M.false_value
        if M.TermEqual(M.Head(term)(), Lmod.ApartLabel)() is M.truth_value:
            return M.truth_value
        return M.false_value

    def _send_pat(self, term):
        return SendPat(term)()

    def _send_host(self, term):
        return SendHost(term)()

    def _apart_left(self, term):
        return M.Head(M.Tail(term)())()

    def _apart_right(self, term):
        return M.Head(M.Tail(M.Tail(term)())())()

    def _has_apart_commitment(self, root, left, right):
        remaining = root
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            item = M.Head(remaining)()
            if self._is_apart(item) is M.truth_value:
                apart_left = self._apart_left(item)
                apart_right = self._apart_right(item)
                if M.AndAtom(M.TermEqual(apart_left, left)(), M.TermEqual(apart_right, right)())() is M.truth_value:
                    return M.truth_value
            remaining = M.Tail(remaining)()
        return M.false_value

    def _mapped_host_for_pat(self, root, pat):
        return MappedHostForPat(root, pat)()

    def _violates_apart(self, root, pat, host):
        remaining = root
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            item = M.Head(remaining)()
            if self._is_send(item) is M.truth_value:
                other_pat = self._send_pat(item)
                other_host = self._send_host(item)
                if M.TermEqual(other_host, host)() is M.truth_value:
                    if self._has_apart_commitment(root, pat, other_pat) is M.truth_value:
                        return M.truth_value
                    if self._has_apart_commitment(root, other_pat, pat) is M.truth_value:
                        return M.truth_value
            remaining = M.Tail(remaining)()
        return M.false_value

    def _violating_apart(self, root, pat, host):
        remaining = root
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            item = M.Head(remaining)()
            if self._is_send(item) is M.truth_value:
                other_pat = self._send_pat(item)
                other_host = self._send_host(item)
                if M.TermEqual(other_host, host)() is M.truth_value:
                    if self._has_apart_commitment(root, pat, other_pat) is M.truth_value:
                        return Apart(pat, other_pat)()
                    if self._has_apart_commitment(root, other_pat, pat) is M.truth_value:
                        return Apart(other_pat, pat)()
            remaining = M.Tail(remaining)()
        return M.EmptyList

    def _step(self):
        if M.IsPair(self.mapping)() is M.false_value:
            return Miss(self.pat, ReasonShape(self.mapping)())()
        if M.TermEqual(M.Head(self.mapping)(), Lmod.MapLabel)() is M.false_value:
            return Miss(self.pat, ReasonShape(self.mapping)())()
        pattern_graph = self._mapping_pattern_graph()
        host_graph = self._mapping_host_graph()
        root = self._mapping_root()
        if self._graph_has_element(pattern_graph, self.pat) is M.false_value:
            return Miss(self.pat, ReasonShape(self.pat)())()
        if self._graph_has_element(host_graph, self.host) is M.false_value:
            return Miss(self.pat, ReasonShape(self.host)())()
        existing = self._mapped_host_for_pat(root, self.pat)
        if M.TermEqual(M.Head(existing)(), M.truth_value)() is M.truth_value:
            return Miss(self.pat, ReasonAlreadyMapped(self.pat, M.Tail(existing)())())()
        violating_apart = self._violating_apart(root, self.pat, self.host)
        if M.IdentityCompare(violating_apart, M.EmptyList)() is M.false_value:
            return Miss(self.pat, ReasonApart(violating_apart, self.pat, self.host)())()
        if self._both_are_edges(pattern_graph, host_graph) is M.truth_value:
            if EdgeSendConsistent(root, self.pat, self.host)() is M.false_value:
                return Miss(self.pat, ReasonPositional(self.pat, self.host)())()
        return Map(pattern_graph, host_graph, M.Pair(Send(self.pat, self.host)(), root))()

    def _both_are_edges(self, pattern_graph, host_graph):
        pattern_edges = self._normalize_store(self._graph_edges(pattern_graph))
        if self._chain_has_term(pattern_edges, self.pat) is M.false_value:
            return M.false_value
        host_edges = self._normalize_store(self._graph_edges(host_graph))
        return self._chain_has_term(host_edges, self.host)

    def __call__(self):
        return self.result


class TestShardConfigure(M.Edge):
    """Select one deterministic round-robin shard of default tests."""

    def __init__(self, graph, shard_index, shard_count):
        graph._test_shard_index = shard_index
        graph._test_shard_count = shard_count
        graph._test_shard_cursor = M.Zero
        self.result = graph
        super().__init__(
            inputs=M.Pair(
                graph,
                M.Pair(shard_index, M.Pair(shard_count, M.EmptyList)),
            ),
            results=M.Pair(graph, M.EmptyList),
        )

    def __call__(self):
        return self.result


class TestShardAccept(M.Edge):
    """Advance the test ordinal and admit it only to the configured shard."""

    def __init__(self, graph):
        registry = M.FromContextGetConstructors(graph)()
        self.result = M.NatEq(
            graph._test_shard_cursor,
            graph._test_shard_index,
            registry,
        )()
        next_pair = M.Succ(graph._test_shard_cursor, registry)()
        next_cursor = M.Head(next_pair)()
        registry = M.Head(M.Tail(next_pair)())()
        if M.NatEq(next_cursor, graph._test_shard_count, registry)() is M.truth_value:
            next_cursor = M.Zero
        graph._test_shard_cursor = next_cursor
        graph._replace_context(constructors=registry)
        super().__init__(inputs=M.Pair(graph, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RunDefaultTestShard(M.Edge):
    """Spawn-safe isolated installation and execution of one test shard."""

    def __init__(self, graph, shard_index, shard_count, result_queue):
        from . import testsuite

        TestShardConfigure(graph, shard_index, shard_count)()
        testsuite.install_default_tests(graph)
        RunTests(graph)()
        self.result = M.FromContextGetTestResults(graph)()
        result_queue.put(self.result)
        super().__init__(
            inputs=M.Pair(
                graph,
                M.Pair(shard_index, M.Pair(shard_count, M.EmptyList)),
            ),
            results=self.result,
        )

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


class RunDefaultTestsParallel(M.Edge):
    """Install and run default tests in isolated shards with Pair reduction."""

    def __init__(self, graph):
        from . import testsuite

        try:
            worker_capacity = multiprocessing.cpu_count()
        except NotImplementedError:
            worker_capacity = 1
        if worker_capacity > 8:
            worker_capacity = 8
        if worker_capacity < 2:
            testsuite.install_default_tests(graph)
            self.result = RunTests(graph)()
            super().__init__(
                inputs=M.Pair(graph, M.EmptyList),
                results=self.result,
            )
            return

        registry = M.FromContextGetConstructors(graph)()
        shard_count = M.Zero
        built_count = 0
        while built_count != worker_capacity:
            count_pair = M.Succ(shard_count, registry)()
            shard_count = M.Head(count_pair)()
            registry = M.Head(M.Tail(count_pair)())()
            built_count = built_count + 1
        graph._replace_context(constructors=registry)

        try:
            mp_context = multiprocessing.get_context("fork")
        except ValueError:
            mp_context = multiprocessing.get_context("spawn")

        workers = M.EmptyList
        shard_index = M.Zero
        slot = 0
        while slot != worker_capacity:
            result_queue = mp_context.Queue()
            process = mp_context.Process(
                target=RunDefaultTestShard,
                args=(graph, shard_index, shard_count, result_queue),
            )
            process.start()
            worker = M.Pair(process, M.Pair(result_queue, M.EmptyList))
            workers = M.Pair(worker, workers)
            next_pair = M.Succ(shard_index, registry)()
            shard_index = M.Head(next_pair)()
            registry = M.Head(M.Tail(next_pair)())()
            slot = slot + 1
        workers = M.Reverse(workers)()

        combined_results = M.EmptyList
        remaining_workers = workers
        while M.IdentityCompare(remaining_workers, M.EmptyList)() is M.false_value:
            worker = M.Head(remaining_workers)()
            process = M.Head(worker)()
            result_queue = M.Head(M.Tail(worker)())()
            process.join()
            if process.exitcode != 0:
                result_queue.close()
                raise RuntimeError("default test shard failed")
            shard_results = result_queue.get()
            result_queue.close()
            reversed_combined = M.Reverse(combined_results)()
            combined_results = shard_results
            while M.IdentityCompare(reversed_combined, M.EmptyList)() is M.false_value:
                combined_results = M.Pair(
                    M.Head(reversed_combined)(),
                    combined_results,
                )
                reversed_combined = M.Tail(reversed_combined)()
            remaining_workers = M.Tail(remaining_workers)()

        graph._replace_context(
            constructors=registry,
            test_results=combined_results,
        )
        graph.default_tests_installed = M.truth_value
        self.result = combined_results
        super().__init__(
            inputs=M.Pair(graph, M.EmptyList),
            results=self.result,
        )

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
