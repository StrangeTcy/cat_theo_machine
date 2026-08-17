from __future__ import annotations

import multiprocessing

from . import context as Ctx
from . import machine as M
from . import proof as P
from . import schemata as S
from . import labels as Lmod
from .gmprep import GMPAddText, GMPEqualText, GMPLessText, GMPMulText, GMPRepDigitList, GMPSubText, GMPSuccText
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

    def __init__(
        self,
        graph_version,
        obligation,
        unchecked_obligations,
        ledger=M.EmptyList,
    ):
        name = KObligationName(obligation)()
        updated_unchecked = unchecked_obligations
        if M.Compare(name, M.Char("node-count-max"))() is M.truth_value:
            count_pair = M.Count(GraphNodes(graph_version)(), M.AllConstructors)()
            count = M.Head(count_pair)()
            registry = M.Head(M.Tail(count_pair)())()
            bound = KObligationStructure(obligation)()
            too_many = M.NatLess(bound, count, registry)()
            verdict = M.NotAtom(too_many)()
        elif M.Compare(name, M.Char("edge-count-max"))() is M.truth_value:
            count_pair = M.Count(GraphEdges(graph_version)(), M.AllConstructors)()
            count = M.Head(count_pair)()
            registry = M.Head(M.Tail(count_pair)())()
            bound = KObligationStructure(obligation)()
            too_many = M.NatLess(bound, count, registry)()
            verdict = M.NotAtom(too_many)()
        elif M.Compare(name, M.Char("ledger-length-max"))() is M.truth_value:
            records = M.EmptyList
            registry = M.AllConstructors
            if M.IdentityCompare(ledger, M.EmptyList)() is M.false_value:
                records = ledger.records
                registry = ledger.registry
            count_pair = M.Count(records, registry)()
            count = M.Head(count_pair)()
            registry = M.Head(M.Tail(count_pair)())()
            prospective_pair = M.Succ(count, registry)()
            prospective_count = M.Head(prospective_pair)()
            registry = M.Head(M.Tail(prospective_pair)())()
            bound = KObligationStructure(obligation)()
            too_many = M.NatLess(bound, prospective_count, registry)()
            verdict = M.NotAtom(too_many)()
            if M.IdentityCompare(ledger, M.EmptyList)() is M.false_value:
                ledger.registry = registry
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
                    M.Pair(
                        unchecked_obligations,
                        M.Pair(ledger, M.EmptyList),
                    ),
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


class Handle(M.Edge):
    """Named graph-pattern abbreviation term."""

    def __init__(self, name, pattern_graph):
        self.result = M.Pair(
            Lmod.HandleLabel,
            M.Pair(name, M.Pair(pattern_graph, M.EmptyList)),
        )
        super().__init__(
            inputs=M.Pair(name, M.Pair(pattern_graph, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class HandleName(M.Edge):
    def __init__(self, handle):
        self.result = M.Head(M.Tail(handle)())()
        super().__init__(inputs=M.Pair(handle, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class HandlePattern(M.Edge):
    def __init__(self, handle):
        self.result = M.Head(M.Tail(M.Tail(handle)())())()
        super().__init__(inputs=M.Pair(handle, M.EmptyList), results=self.result)

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


class CompileHandleToLaws(M.Edge):
    """Compile a named pattern abbreviation into ordered fold/unfold Laws."""

    def __init__(self, handle, interface_nodes):
        pattern = HandlePattern(handle)()
        interface = M.Pair(
            M.HypergraphLabel,
            M.Pair(interface_nodes, M.Pair(M.EmptyList, M.EmptyList)),
        )
        connector = M.Pair(
            Lmod.HandleLabel,
            M.Pair(handle, interface_nodes),
        )
        abbreviation = M.Pair(
            M.HypergraphLabel,
            M.Pair(
                M.Pair(handle, interface_nodes),
                M.Pair(M.Pair(connector, M.EmptyList), M.EmptyList),
            ),
        )
        interface_sends = IdentitySendsFor(interface_nodes)()
        pattern_map = Map(interface, pattern, interface_sends)()
        abbreviation_map = Map(interface, abbreviation, interface_sends)()
        fold = Law(
            pattern,
            interface,
            abbreviation,
            pattern_map,
            abbreviation_map,
            M.EmptyList,
        )()
        unfold = Law(
            abbreviation,
            interface,
            pattern,
            abbreviation_map,
            pattern_map,
            M.EmptyList,
        )()
        self.result = M.Pair(fold, M.Pair(unfold, M.EmptyList))
        super().__init__(
            inputs=M.Pair(handle, M.Pair(interface_nodes, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class PositionalSignature(M.Edge):
    """Machine Pair signature: edge label followed by its ordered arity Nat."""

    def __init__(self, edge_term):
        counted = M.Count(EdgeEndpoints(edge_term)(), M.AllConstructors)()
        arity = M.Head(counted)()
        self.registry = M.Head(M.Tail(counted)())()
        self.result = M.Pair(
            M.Head(edge_term)(),
            M.Pair(arity, M.EmptyList),
        )
        super().__init__(inputs=M.Pair(edge_term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SignatureCensus(M.Edge):
    """Deterministic Pair association chain from positional signatures to Nat counts."""

    def __init__(self, graph_version):
        registry = M.AllConstructors
        census = M.EmptyList
        probe = MapExtendOneStep(M.EmptyList, M.EmptyList, M.EmptyList)
        remaining_edges = probe._normalize_store(GraphEdges(graph_version)())
        while M.IdentityCompare(remaining_edges, M.EmptyList)() is M.false_value:
            edge_term = M.Head(remaining_edges)()
            counted = M.Count(EdgeEndpoints(edge_term)(), registry)()
            arity = M.Head(counted)()
            registry = M.Head(M.Tail(counted)())()
            signature = M.Pair(
                M.Head(edge_term)(),
                M.Pair(arity, M.EmptyList),
            )

            remaining_entries = census
            reversed_entries = M.EmptyList
            found = M.false_value
            while M.IdentityCompare(remaining_entries, M.EmptyList)() is M.false_value:
                entry = M.Head(remaining_entries)()
                entry_signature = M.Head(entry)()
                same_signature = M.false_value
                if M.TermEqual(
                    M.Head(entry_signature)(),
                    M.Head(signature)(),
                )() is M.truth_value:
                    if M.NatEq(
                        M.Head(M.Tail(entry_signature)())(),
                        M.Head(M.Tail(signature)())(),
                        registry,
                    )() is M.truth_value:
                        same_signature = M.truth_value
                if same_signature is M.truth_value:
                    incremented = M.Succ(
                        M.Head(M.Tail(entry)())(),
                        registry,
                    )()
                    entry = M.Pair(
                        entry_signature,
                        M.Pair(M.Head(incremented)(), M.EmptyList),
                    )
                    registry = M.Head(M.Tail(incremented)())()
                    found = M.truth_value
                reversed_entries = M.Pair(entry, reversed_entries)
                remaining_entries = M.Tail(remaining_entries)()
            census = M.Reverse(reversed_entries)()
            if found is M.false_value:
                reversed_entries = M.Reverse(census)()
                census = M.Reverse(
                    M.Pair(
                        M.Pair(signature, M.Pair(M.one, M.EmptyList)),
                        reversed_entries,
                    )
                )()
            remaining_edges = M.Tail(remaining_edges)()

        self.registry = registry
        self.result = census
        super().__init__(inputs=M.Pair(graph_version, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class HandleRespectsSignatures(M.Edge):
    """Machine truth when one Handle fold preserves every external signature count."""

    def __init__(self, handle, interface_nodes, graph_version):
        atom_result = M.false_value
        pattern = HandlePattern(handle)()
        compiled = CompileHandleToLaws(handle, interface_nodes)()
        fold = M.Head(compiled)()
        mapping = FirstCompletedMatch(pattern, graph_version)()
        if M.IdentityCompare(mapping, M.EmptyList)() is M.false_value:
            root = M.Head(M.Tail(M.Tail(M.Tail(mapping)())())())()
            probe = MapExtendOneStep(M.EmptyList, M.EmptyList, M.EmptyList)
            remaining_pattern_edges = probe._normalize_store(GraphEdges(pattern)())
            reversed_internal_edges = M.EmptyList
            while M.IdentityCompare(
                remaining_pattern_edges,
                M.EmptyList,
            )() is M.false_value:
                found = MappedHostForPat(
                    root,
                    M.Head(remaining_pattern_edges)(),
                )()
                if M.IdentityCompare(M.Head(found)(), M.truth_value)() is M.truth_value:
                    reversed_internal_edges = M.Pair(
                        M.Tail(found)(),
                        reversed_internal_edges,
                    )
                remaining_pattern_edges = M.Tail(remaining_pattern_edges)()
            internal_edges = M.Reverse(reversed_internal_edges)()
            external_edges = ChainWithout(
                probe._normalize_store(GraphEdges(graph_version)()),
                internal_edges,
            )()
            external_graph = GraphVersion(
                GraphNodes(graph_version)(),
                external_edges,
                GraphVersionInvariants(graph_version)(),
            )()
            before_census = SignatureCensus(external_graph)()

            fired = FireLaw(
                graph_version,
                fold,
                mapping,
                DanglingForbid()(),
            )()
            committed = M.Head(fired)()
            if M.IdentityCompare(committed, M.EmptyList)() is M.false_value:
                after_census = SignatureCensus(committed)()
                atom_result = M.truth_value
                remaining_before = before_census
                while M.IdentityCompare(
                    remaining_before,
                    M.EmptyList,
                )() is M.false_value:
                    before_entry = M.Head(remaining_before)()
                    before_signature = M.Head(before_entry)()
                    remaining_after = after_census
                    matching_count = M.EmptyList
                    while M.IdentityCompare(
                        remaining_after,
                        M.EmptyList,
                    )() is M.false_value:
                        after_entry = M.Head(remaining_after)()
                        after_signature = M.Head(after_entry)()
                        same_signature = M.false_value
                        if M.TermEqual(
                            M.Head(before_signature)(),
                            M.Head(after_signature)(),
                        )() is M.truth_value:
                            if M.NatEq(
                                M.Head(M.Tail(before_signature)())(),
                                M.Head(M.Tail(after_signature)())(),
                                M.AllConstructors,
                            )() is M.truth_value:
                                same_signature = M.truth_value
                        if same_signature is M.truth_value:
                            matching_count = M.Head(M.Tail(after_entry)())()
                            remaining_after = M.EmptyList
                        else:
                            remaining_after = M.Tail(remaining_after)()
                    if M.IdentityCompare(
                        matching_count,
                        M.EmptyList,
                    )() is M.truth_value:
                        atom_result = M.false_value
                        remaining_before = M.EmptyList
                    elif M.NatEq(
                        M.Head(M.Tail(before_entry)())(),
                        matching_count,
                        M.AllConstructors,
                    )() is M.false_value:
                        atom_result = M.false_value
                        remaining_before = M.EmptyList
                    else:
                        remaining_before = M.Tail(remaining_before)()

        self.result = atom_result
        super().__init__(
            inputs=M.Pair(
                handle,
                M.Pair(interface_nodes, M.Pair(graph_version, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


PROMOTION_REPORT_CENSUS_KEY = M.Char("census")
PROMOTION_REPORT_SIGNATURE_KEY = M.Char("signature_ok")
PROMOTION_REPORT_ROUNDTRIP_KEY = M.Char("roundtrip_ok")
PROMOTION_REPORT_SIZE_DELTA_KEY = M.Char("size_delta")


class PromotionReport(M.Edge):
    """Build the ordered machine evidence report for one Handle candidate."""

    def __init__(
        self,
        handle,
        interface_nodes,
        ledger,
        versions,
        match_cap=M.EmptyList,
    ):
        pattern = HandlePattern(handle)()
        if M.IdentityCompare(match_cap, M.EmptyList)() is M.truth_value:
            match_cap = CENSUS_MATCH_CAP
        latest_version = M.EmptyList
        latest_mapping = M.EmptyList
        remaining_versions = versions
        while M.IdentityCompare(remaining_versions, M.EmptyList)() is M.false_value:
            version = M.Head(remaining_versions)()
            mapping = FirstCompletedMatch(pattern, version)()
            if M.IdentityCompare(mapping, M.EmptyList)() is M.false_value:
                latest_version = version
                latest_mapping = mapping
            remaining_versions = M.Tail(remaining_versions)()

        if M.IdentityCompare(latest_version, M.EmptyList)() is M.truth_value:
            self.result = M.EmptyList
        else:
            census = PatternCensus(
                ledger,
                pattern,
                versions,
                match_cap,
            )()
            signature_ok = HandleRespectsSignatures(
                handle,
                interface_nodes,
                latest_version,
            )()
            compiled = CompileHandleToLaws(handle, interface_nodes)()
            fold = M.Head(compiled)()
            unfold = M.Head(M.Tail(compiled)())()
            folded_result = FireLaw(
                latest_version,
                fold,
                latest_mapping,
                DanglingForbid()(),
            )()
            folded = M.Head(folded_result)()
            roundtrip_ok = M.false_value
            size_delta = SignedRational(M.Zero, M.Zero, M.one)()
            if M.IdentityCompare(folded, M.EmptyList)() is M.false_value:
                before_counted = M.Count(
                    GraphNodes(latest_version)(),
                    ledger.registry,
                )()
                nodes_before = M.Head(before_counted)()
                ledger.registry = M.Head(M.Tail(before_counted)())()
                after_counted = M.Count(GraphNodes(folded)(), ledger.registry)()
                nodes_after = M.Head(after_counted)()
                ledger.registry = M.Head(M.Tail(after_counted)())()
                size_delta = SignedRational(
                    nodes_before,
                    nodes_after,
                    M.one,
                )()

                unfold_mapping = FirstCompletedMatch(LawLeft(unfold)(), folded)()
                if M.IdentityCompare(
                    unfold_mapping,
                    M.EmptyList,
                )() is M.false_value:
                    unfolded_result = FireLaw(
                        folded,
                        unfold,
                        unfold_mapping,
                        DanglingForbid()(),
                    )()
                    unfolded = M.Head(unfolded_result)()
                    if M.IdentityCompare(
                        unfolded,
                        M.EmptyList,
                    )() is M.false_value:
                        roundtrip_ok = GraphStoresEqual(
                            unfolded,
                            latest_version,
                        )()

            self.result = M.Pair(
                M.Pair(
                    PROMOTION_REPORT_CENSUS_KEY,
                    M.Pair(census, M.EmptyList),
                ),
                M.Pair(
                    M.Pair(
                        PROMOTION_REPORT_SIGNATURE_KEY,
                        M.Pair(signature_ok, M.EmptyList),
                    ),
                    M.Pair(
                        M.Pair(
                            PROMOTION_REPORT_ROUNDTRIP_KEY,
                            M.Pair(roundtrip_ok, M.EmptyList),
                        ),
                        M.Pair(
                            M.Pair(
                                PROMOTION_REPORT_SIZE_DELTA_KEY,
                                M.Pair(size_delta, M.EmptyList),
                            ),
                            M.EmptyList,
                        ),
                    ),
                ),
            )

        super().__init__(
            inputs=M.Pair(
                handle,
                M.Pair(
                    interface_nodes,
                    M.Pair(
                        ledger,
                        M.Pair(
                            versions,
                            M.Pair(match_cap, M.EmptyList),
                        ),
                    ),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class ProposeHandle(M.Edge):
    """Submit a Handle fold proposal with its machine report as justification."""

    def __init__(self, proposal_store, handle, interface_nodes, report):
        compiled = CompileHandleToLaws(handle, interface_nodes)()
        fold = M.Head(compiled)()
        proposal = Proposal(fold, handle)()
        submitted = ProposalStoreSubmit(proposal_store, proposal)()
        justification = JustifiedBy(proposal, report)()
        self.result = ProposalStoreAttach(
            submitted,
            proposal,
            justification,
        )()
        super().__init__(
            inputs=M.Pair(
                proposal_store,
                M.Pair(
                    handle,
                    M.Pair(
                        interface_nodes,
                        M.Pair(report, M.EmptyList),
                    ),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class ImpactPolicy(M.Edge):
    """The fixed Step-24 impact policy as ordered machine associations."""

    def __init__(self):
        self.result = M.Pair(
            M.Pair(
                M.Char("fold_handle"),
                M.Pair(M.Char("auto"), M.EmptyList),
            ),
            M.Pair(
                M.Pair(
                    M.Char("unfold_handle"),
                    M.Pair(M.Char("auto"), M.EmptyList),
                ),
                M.Pair(
                    M.Pair(
                        M.Char("install_law"),
                        M.Pair(M.Char("human"), M.EmptyList),
                    ),
                    M.Pair(
                        M.Pair(
                            M.Char("meta_rewrite"),
                            M.Pair(M.Char("human"), M.EmptyList),
                        ),
                        M.Pair(
                            M.Pair(
                                M.Char("activation"),
                                M.Pair(M.Char("human"), M.EmptyList),
                            ),
                            M.Pair(
                                M.Pair(
                                    M.Char("tune_preference"),
                                    M.Pair(M.Char("auto"), M.EmptyList),
                                ),
                                M.EmptyList,
                            ),
                        ),
                    ),
                ),
            ),
        )
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class ClassifyProposal(M.Edge):
    """Classify a proposed Law by literal Handle and Law structure."""

    def __init__(self, proposal):
        policy = ImpactPolicy()()
        fold_class = M.Head(M.Head(policy)())()
        policy = M.Tail(policy)()
        unfold_class = M.Head(M.Head(policy)())()
        policy = M.Tail(policy)()
        install_class = M.Head(M.Head(policy)())()
        policy = M.Tail(policy)()
        meta_class = M.Head(M.Head(policy)())()
        policy = M.Tail(policy)()
        policy = M.Tail(policy)()
        preference_class = M.Head(M.Head(policy)())()

        law = ProposalLaw(proposal)()
        left_contains_law = M.false_value
        left_contains_handle = M.false_value
        remaining_left = GraphElements(LawLeft(law)())()
        while M.IdentityCompare(remaining_left, M.EmptyList)() is M.false_value:
            element = M.Head(remaining_left)()
            if M.IsPair(element)() is M.truth_value:
                if M.TermEqual(M.Head(element)(), Lmod.LawLabel)() is M.truth_value:
                    left_contains_law = M.truth_value
                if M.TermEqual(M.Head(element)(), Lmod.HandleLabel)() is M.truth_value:
                    left_contains_handle = M.truth_value
            remaining_left = M.Tail(remaining_left)()

        right_contains_handle = M.false_value
        right_contains_preference = M.false_value
        remaining_right = GraphElements(LawRight(law)())()
        while M.IdentityCompare(remaining_right, M.EmptyList)() is M.false_value:
            element = M.Head(remaining_right)()
            if M.IsPair(element)() is M.truth_value:
                if M.TermEqual(M.Head(element)(), Lmod.HandleLabel)() is M.truth_value:
                    right_contains_handle = M.truth_value
                if M.TermEqual(
                    M.Head(element)(),
                    Lmod.LawPreferenceLabel,
                )() is M.truth_value:
                    right_contains_preference = M.truth_value
            remaining_right = M.Tail(remaining_right)()

        if M.IdentityCompare(left_contains_law, M.truth_value)() is M.truth_value:
            self.result = meta_class
        elif M.IdentityCompare(right_contains_handle, M.truth_value)() is M.truth_value:
            self.result = fold_class
        elif M.IdentityCompare(
            right_contains_preference,
            M.truth_value,
        )() is M.truth_value:
            self.result = preference_class
        elif M.IdentityCompare(left_contains_handle, M.truth_value)() is M.truth_value:
            self.result = unfold_class
        else:
            self.result = install_class

        super().__init__(inputs=M.Pair(proposal, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


AUTONOMY_BUDGET_MAX_FIRINGS_KEY = M.Char("max_firings")
AUTONOMY_BUDGET_MAX_NODES_KEY = M.Char("max_nodes")
AUTONOMY_BUDGET_MAX_ACTIVATIONS_KEY = M.Char("max_activations")
AUTONOMY_REPORT_ACTIVATED_KEY = M.Char("activated")
AUTONOMY_REPORT_SKIPPED_HUMAN_KEY = M.Char("skipped_human")
AUTONOMY_REPORT_FIRINGS_KEY = M.Char("firings")
AUTONOMY_REPORT_STOPPED_REASON_KEY = M.Char("stopped_reason")
AUTONOMY_REPORT_GENERATED_HANDLES_KEY = M.Char("generated_handles")
AUTONOMY_REPORT_GENERATED_COMPOSITIONS_KEY = M.Char("generated_compositions")
AUTONOMY_GENERATE_HANDLES_KEY = M.Char("generate_handles")
AUTONOMY_GENERATE_COMPOSITIONS_KEY = M.Char("generate_compositions")
AUTONOMY_GENERATOR_VERSIONS_KEY = M.Char("versions")
AUTONOMY_GENERATOR_MIN_COUNT_KEY = M.Char("min_count")
AUTONOMY_STOP_EXHAUSTED = M.Char("exhausted")
AUTONOMY_STOP_BUDGET_FIRINGS = M.Char("budget_firings")
AUTONOMY_STOP_BUDGET_NODES = M.Char("budget_nodes")


class AutonomyAuthority(M.Edge):
    """Machine authority recording the exact budget used for auto-approval."""

    def __init__(self, budget_as_term):
        self.result = M.Pair(
            Lmod.AutonomyAuthorityLabel,
            M.Pair(budget_as_term, M.EmptyList),
        )
        super().__init__(
            inputs=M.Pair(budget_as_term, M.EmptyList),
            results=self.result,
        )

    def __call__(self):
        return self.result


class AutonomyCycle(M.Edge):
    """Optionally generate, then approve, activate, and fire within a budget."""

    def __init__(
        self,
        graph_version,
        proposal_store,
        ledger,
        budget,
        generator_config=M.EmptyList,
    ):
        max_firings = M.EmptyList
        max_nodes = M.EmptyList
        max_activations = M.EmptyList
        remaining_budget = budget
        while M.IdentityCompare(remaining_budget, M.EmptyList)() is M.false_value:
            association = M.Head(remaining_budget)()
            key = M.Head(association)()
            value = M.Head(M.Tail(association)())()
            if M.Compare(key, AUTONOMY_BUDGET_MAX_FIRINGS_KEY)() is M.truth_value:
                max_firings = value
            elif M.Compare(key, AUTONOMY_BUDGET_MAX_NODES_KEY)() is M.truth_value:
                max_nodes = value
            elif M.Compare(key, AUTONOMY_BUDGET_MAX_ACTIVATIONS_KEY)() is M.truth_value:
                max_activations = value
            remaining_budget = M.Tail(remaining_budget)()

        generate_handles = M.false_value
        generate_compositions = M.false_value
        generator_versions = M.EmptyList
        generator_min_count = M.one
        remaining_generator_config = generator_config
        while M.IdentityCompare(
            remaining_generator_config,
            M.EmptyList,
        )() is M.false_value:
            association = M.Head(remaining_generator_config)()
            key = M.Head(association)()
            value = M.Head(M.Tail(association)())()
            if M.Compare(key, AUTONOMY_GENERATE_HANDLES_KEY)() is M.truth_value:
                generate_handles = value
            elif M.Compare(
                key,
                AUTONOMY_GENERATE_COMPOSITIONS_KEY,
            )() is M.truth_value:
                generate_compositions = value
            elif M.Compare(
                key,
                AUTONOMY_GENERATOR_VERSIONS_KEY,
            )() is M.truth_value:
                generator_versions = value
            elif M.Compare(
                key,
                AUTONOMY_GENERATOR_MIN_COUNT_KEY,
            )() is M.truth_value:
                generator_min_count = value
            remaining_generator_config = M.Tail(remaining_generator_config)()

        current_version = graph_version
        current_store = proposal_store
        reversed_generation_report = M.EmptyList
        if M.IdentityCompare(generate_handles, M.truth_value)() is M.truth_value:
            generated_handles = GenerateHandleProposals(
                current_store,
                generator_versions,
                ledger,
                generator_min_count,
            )()
            current_store = M.Head(generated_handles)()
            handle_count = M.Head(M.Tail(generated_handles)())()
            handle_skipped = M.Head(M.Tail(M.Tail(generated_handles)())())()
            reversed_generation_report = M.Pair(
                M.Pair(
                    AUTONOMY_REPORT_GENERATED_HANDLES_KEY,
                    M.Pair(
                        M.Pair(
                            handle_count,
                            M.Pair(handle_skipped, M.EmptyList),
                        ),
                        M.EmptyList,
                    ),
                ),
                reversed_generation_report,
            )
        if M.IdentityCompare(
            generate_compositions,
            M.truth_value,
        )() is M.truth_value:
            generated_compositions = GenerateCompositionProposals(
                current_store,
                ledger,
            )()
            current_store = M.Head(generated_compositions)()
            composition_count = M.Head(M.Tail(generated_compositions)())()
            composition_skipped = M.Head(
                M.Tail(M.Tail(generated_compositions)())(),
            )()
            reversed_generation_report = M.Pair(
                M.Pair(
                    AUTONOMY_REPORT_GENERATED_COMPOSITIONS_KEY,
                    M.Pair(
                        M.Pair(
                            composition_count,
                            M.Pair(composition_skipped, M.EmptyList),
                        ),
                        M.EmptyList,
                    ),
                ),
                reversed_generation_report,
            )
        generation_report = M.Reverse(reversed_generation_report)()
        authority = AutonomyAuthority(budget)()
        activation_count = M.Zero
        reversed_activated = M.EmptyList
        reversed_skipped_human = M.EmptyList
        remaining_entries = ProposalStoreEntries(current_store)()
        policy = ImpactPolicy()()

        while M.IdentityCompare(remaining_entries, M.EmptyList)() is M.false_value:
            entry = M.Head(remaining_entries)()
            proposal = ProposalEntryProposal(entry)()
            pending = M.truth_value
            remaining_annotations = ProposalEntryAnnotations(entry)()
            while M.IdentityCompare(
                remaining_annotations,
                M.EmptyList,
            )() is M.false_value:
                annotation = M.Head(remaining_annotations)()
                if M.IsPair(annotation)() is M.truth_value:
                    annotation_label = M.Head(annotation)()
                    if M.TermEqual(
                        annotation_label,
                        Lmod.ApprovedLabel,
                    )() is M.truth_value:
                        pending = M.false_value
                        remaining_annotations = M.EmptyList
                    elif M.TermEqual(
                        annotation_label,
                        Lmod.RejectedLabel,
                    )() is M.truth_value:
                        pending = M.false_value
                        remaining_annotations = M.EmptyList
                    else:
                        remaining_annotations = M.Tail(remaining_annotations)()
                else:
                    remaining_annotations = M.Tail(remaining_annotations)()

            if M.IdentityCompare(pending, M.truth_value)() is M.truth_value:
                impact = ClassifyProposal(proposal)()
                disposition = M.EmptyList
                remaining_policy = policy
                while M.IdentityCompare(
                    remaining_policy,
                    M.EmptyList,
                )() is M.false_value:
                    policy_entry = M.Head(remaining_policy)()
                    if M.Compare(
                        M.Head(policy_entry)(),
                        impact,
                    )() is M.truth_value:
                        disposition = M.Head(M.Tail(policy_entry)())()
                        remaining_policy = M.EmptyList
                    else:
                        remaining_policy = M.Tail(remaining_policy)()

                if M.Compare(disposition, M.Char("human"))() is M.truth_value:
                    reversed_skipped_human = M.Pair(
                        proposal,
                        reversed_skipped_human,
                    )
                elif M.Compare(disposition, M.Char("auto"))() is M.truth_value:
                    if M.NatLess(
                        activation_count,
                        max_activations,
                        ledger.registry,
                    )() is M.truth_value:
                        law = ProposalLaw(proposal)()
                        obligations = LawObligations(law)()
                        has_node_bound = M.false_value
                        remaining_obligations = obligations
                        while M.IdentityCompare(
                            remaining_obligations,
                            M.EmptyList,
                        )() is M.false_value:
                            if M.Compare(
                                KObligationName(M.Head(remaining_obligations)())(),
                                M.Char("node-count-max"),
                            )() is M.truth_value:
                                has_node_bound = M.truth_value
                                remaining_obligations = M.EmptyList
                            else:
                                remaining_obligations = M.Tail(
                                    remaining_obligations,
                                )()
                        if M.IdentityCompare(
                            has_node_bound,
                            M.false_value,
                        )() is M.truth_value:
                            reversed_obligations = M.Reverse(obligations)()
                            obligations = M.Reverse(
                                M.Pair(
                                    KObligation(
                                        M.Char("node-count-max"),
                                        max_nodes,
                                    )(),
                                    reversed_obligations,
                                )
                            )()
                            law = Law(
                                LawLeft(law)(),
                                LawInterface(law)(),
                                LawRight(law)(),
                                LawKToLeft(law)(),
                                LawKToRight(law)(),
                                obligations,
                            )()
                            guarded_proposal = Proposal(
                                law,
                                ProposalOrigin(proposal)(),
                            )()
                            reversed_entries = M.EmptyList
                            current_entries = ProposalStoreEntries(current_store)()
                            while M.IdentityCompare(
                                current_entries,
                                M.EmptyList,
                            )() is M.false_value:
                                current_entry = M.Head(current_entries)()
                                if M.TermEqual(
                                    ProposalEntryProposal(current_entry)(),
                                    proposal,
                                )() is M.truth_value:
                                    reversed_annotations = M.EmptyList
                                    current_annotations = ProposalEntryAnnotations(
                                        current_entry,
                                    )()
                                    while M.IdentityCompare(
                                        current_annotations,
                                        M.EmptyList,
                                    )() is M.false_value:
                                        current_annotation = M.Head(
                                            current_annotations,
                                        )()
                                        if M.IsPair(current_annotation)() is M.truth_value:
                                            if M.TermEqual(
                                                M.Head(current_annotation)(),
                                                Lmod.JustifiedByLabel,
                                            )() is M.truth_value:
                                                if M.TermEqual(
                                                    M.Head(
                                                        M.Tail(current_annotation)(),
                                                    )(),
                                                    proposal,
                                                )() is M.truth_value:
                                                    current_annotation = JustifiedBy(
                                                        guarded_proposal,
                                                        M.Head(
                                                            M.Tail(
                                                                M.Tail(
                                                                    current_annotation,
                                                                )(),
                                                            )(),
                                                        )(),
                                                    )()
                                        reversed_annotations = M.Pair(
                                            current_annotation,
                                            reversed_annotations,
                                        )
                                        current_annotations = M.Tail(
                                            current_annotations,
                                        )()
                                    current_entry = ProposalEntry(
                                        guarded_proposal,
                                        M.Reverse(reversed_annotations)(),
                                    )()
                                reversed_entries = M.Pair(
                                    current_entry,
                                    reversed_entries,
                                )
                                current_entries = M.Tail(current_entries)()
                            current_store = ProposalStore(
                                M.Reverse(reversed_entries)(),
                            )()
                            proposal = guarded_proposal
                        approval = Approved(proposal, authority)()
                        current_store = ProposalStoreAttach(
                            current_store,
                            proposal,
                            approval,
                        )()
                        approved_entry = M.EmptyList
                        updated_entries = ProposalStoreEntries(current_store)()
                        while M.IdentityCompare(
                            updated_entries,
                            M.EmptyList,
                        )() is M.false_value:
                            updated_entry = M.Head(updated_entries)()
                            if M.TermEqual(
                                ProposalEntryProposal(updated_entry)(),
                                proposal,
                            )() is M.truth_value:
                                approved_entry = updated_entry
                                updated_entries = M.EmptyList
                            else:
                                updated_entries = M.Tail(updated_entries)()
                        activated = ActivateProposal(
                            current_version,
                            approved_entry,
                        )()
                        active_version = M.Head(activated)()
                        if M.IdentityCompare(
                            active_version,
                            M.EmptyList,
                        )() is M.false_value:
                            current_version = active_version
                            reversed_activated = M.Pair(
                                proposal,
                                reversed_activated,
                            )
                            next_activation = M.Succ(
                                activation_count,
                                ledger.registry,
                            )()
                            activation_count = M.Head(next_activation)()
                            ledger.registry = M.Head(M.Tail(next_activation)())()
            remaining_entries = M.Tail(remaining_entries)()

        firings = M.Zero
        stopped_reason = AUTONOMY_STOP_EXHAUSTED
        self.last_firing_trace = M.EmptyList
        firing = M.truth_value
        while M.IdentityCompare(firing, M.truth_value)() is M.truth_value:
            if M.NatLess(firings, max_firings, ledger.registry)() is M.false_value:
                stopped_reason = AUTONOMY_STOP_BUDGET_FIRINGS
                firing = M.false_value
            else:
                records_before = ledger.records
                registry_before = ledger.registry
                fired = FireAny(
                    current_version,
                    DanglingForbid()(),
                    ledger,
                )()
                candidate_version = M.Head(fired)()
                self.last_firing_trace = M.Head(M.Tail(fired)())()
                if M.IdentityCompare(
                    candidate_version,
                    M.EmptyList,
                )() is M.truth_value:
                    stopped_reason = AUTONOMY_STOP_EXHAUSTED
                    firing = M.false_value
                else:
                    counted = M.Count(
                        GraphNodes(candidate_version)(),
                        ledger.registry,
                    )()
                    candidate_nodes = M.Head(counted)()
                    ledger.registry = M.Head(M.Tail(counted)())()
                    if M.NatLess(
                        max_nodes,
                        candidate_nodes,
                        ledger.registry,
                    )() is M.truth_value:
                        ledger.records = records_before
                        ledger.results = records_before
                        ledger.registry = registry_before
                        stopped_reason = AUTONOMY_STOP_BUDGET_NODES
                        firing = M.false_value
                    else:
                        current_version = candidate_version
                        next_firings = M.Succ(firings, ledger.registry)()
                        firings = M.Head(next_firings)()
                        ledger.registry = M.Head(M.Tail(next_firings)())()

        report = M.Pair(
            M.Pair(
                AUTONOMY_REPORT_ACTIVATED_KEY,
                M.Pair(M.Reverse(reversed_activated)(), M.EmptyList),
            ),
            M.Pair(
                M.Pair(
                    AUTONOMY_REPORT_SKIPPED_HUMAN_KEY,
                    M.Pair(M.Reverse(reversed_skipped_human)(), M.EmptyList),
                ),
                M.Pair(
                    M.Pair(
                        AUTONOMY_REPORT_FIRINGS_KEY,
                        M.Pair(firings, M.EmptyList),
                    ),
                    M.Pair(
                        M.Pair(
                            AUTONOMY_REPORT_STOPPED_REASON_KEY,
                            M.Pair(stopped_reason, M.EmptyList),
                        ),
                        generation_report,
                    ),
                ),
            ),
        )
        self.result = M.Pair(
            current_version,
            M.Pair(current_store, M.Pair(report, M.EmptyList)),
        )
        super().__init__(
            inputs=M.Pair(
                graph_version,
                M.Pair(
                    proposal_store,
                    M.Pair(
                        ledger,
                        M.Pair(budget, M.Pair(generator_config, M.EmptyList)),
                    ),
                ),
            ),
            results=self.result,
        )

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

    def __init__(self, graph_version, dangling_mode, ledger=M.EmptyList, ordering=M.EmptyList):
        self.result = M.Pair(M.EmptyList, M.Pair(M.EmptyList, M.EmptyList))
        laws = InstalledLaws(graph_version)()
        if M.IdentityCompare(ordering, M.EmptyList)() is M.truth_value:
            ordering = InstalledPreference(graph_version)()
        if M.IdentityCompare(ordering, M.EmptyList)() is M.false_value:
            reversed_ordered = M.Reverse(ordering)()
            remaining_laws = laws
            while M.IdentityCompare(remaining_laws, M.EmptyList)() is M.false_value:
                law = M.Head(remaining_laws)()
                if ChainHasTerm(ordering, law)() is M.false_value:
                    reversed_ordered = M.Pair(law, reversed_ordered)
                remaining_laws = M.Tail(remaining_laws)()
            laws = M.Reverse(reversed_ordered)()
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
                            self.result = fired
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
                M.Pair(
                    dangling_mode,
                    M.Pair(ledger, M.Pair(ordering, M.EmptyList)),
                ),
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


LAW_ORDERING_SCAN_CAP = M.GMPRep("200")


class LawLedgerScore(M.Edge):
    """Success count and exact mean-delta fraction for one law's groups."""

    def __init__(self, law, groups):
        cap_text = M.GMPRepText(LAW_ORDERING_SCAN_CAP)()
        scan_text = "0"
        success_text = "0"
        numerator_text = "0"
        denominator_text = "1"
        remaining_groups = groups
        while M.IdentityCompare(remaining_groups, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                remaining_groups = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                group = M.Head(remaining_groups)()
                if M.TermEqual(M.Head(group)(), law)() is M.truth_value:
                    positive_text = "0"
                    negative_text = "0"
                    record_scan_text = "0"
                    remaining_records = M.Head(M.Tail(group)())()
                    while M.IdentityCompare(
                        remaining_records,
                        M.EmptyList,
                    )() is M.false_value:
                        if GMPEqualText(
                            record_scan_text,
                            cap_text,
                        )() is M.truth_value:
                            remaining_records = M.EmptyList
                        else:
                            record_scan_text = GMPSuccText(record_scan_text)()
                            record = M.Head(remaining_records)()
                            success_text = GMPSuccText(success_text)()
                            positive_text = GMPAddText(
                                positive_text,
                                M.GMPRepText(
                                    M.NatRepOf(
                                        FiringRecordNodesAfter(record)(),
                                        M.AllConstructors,
                                    )()
                                )(),
                            )()
                            negative_text = GMPAddText(
                                negative_text,
                                M.GMPRepText(
                                    M.NatRepOf(
                                        FiringRecordNodesBefore(record)(),
                                        M.AllConstructors,
                                    )()
                                )(),
                            )()
                            remaining_records = M.Tail(remaining_records)()
                    if GMPEqualText(success_text, "0")() is M.false_value:
                        numerator_text = GMPSubText(positive_text, negative_text)()
                        denominator_text = success_text
                    remaining_groups = M.EmptyList
                else:
                    remaining_groups = M.Tail(remaining_groups)()
        self.result = M.Pair(
            success_text,
            M.Pair(numerator_text, M.Pair(denominator_text, M.EmptyList)),
        )
        super().__init__(
            inputs=M.Pair(law, M.Pair(groups, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class LawScorePrecedes(M.Edge):
    """Strict ordering: higher success first, then lower exact mean delta."""

    def __init__(self, left_score, right_score):
        left_success = M.Head(left_score)()
        left_numerator = M.Head(M.Tail(left_score)())()
        left_denominator = M.Head(M.Tail(M.Tail(left_score)())())()
        right_success = M.Head(right_score)()
        right_numerator = M.Head(M.Tail(right_score)())()
        right_denominator = M.Head(M.Tail(M.Tail(right_score)())())()
        if GMPLessText(right_success, left_success)() is M.truth_value:
            self.result = M.truth_value
        elif GMPLessText(left_success, right_success)() is M.truth_value:
            self.result = M.false_value
        else:
            left_cross = GMPMulText(left_numerator, right_denominator)()
            right_cross = GMPMulText(right_numerator, left_denominator)()
            self.result = GMPLessText(left_cross, right_cross)()
        super().__init__(
            inputs=M.Pair(left_score, M.Pair(right_score, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class LawPreference(M.Edge):
    """Preferred-order law list as an installable labeled term."""

    def __init__(self, ordering):
        self.result = M.Pair(
            Lmod.LawPreferenceLabel,
            M.Pair(ordering, M.EmptyList),
        )
        super().__init__(inputs=M.Pair(ordering, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class LawPreferenceOrdering(M.Edge):
    def __init__(self, preference):
        self.result = M.Head(M.Tail(preference)())()
        super().__init__(inputs=M.Pair(preference, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class InstalledPreference(M.Edge):
    """Ordering of the newest installed LawPreference term, or EmptyList."""

    def __init__(self, graph_version):
        cap_text = M.GMPRepText(LAW_ORDERING_SCAN_CAP)()
        scan_text = "0"
        self.result = M.EmptyList
        remaining = GraphVersionInvariants(graph_version)()
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                remaining = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                invariant = M.Head(remaining)()
                if IsInstalledLaw(invariant)() is M.truth_value:
                    law = InstalledLawValue(invariant)()
                    element_scan_text = "0"
                    remaining_elements = GraphNodes(LawRight(law)())()
                    while M.IdentityCompare(
                        remaining_elements,
                        M.EmptyList,
                    )() is M.false_value:
                        if GMPEqualText(
                            element_scan_text,
                            cap_text,
                        )() is M.truth_value:
                            remaining_elements = M.EmptyList
                        else:
                            element_scan_text = GMPSuccText(element_scan_text)()
                            element = M.Head(remaining_elements)()
                            if M.IsPair(element)() is M.truth_value:
                                if M.TermEqual(
                                    M.Head(element)(),
                                    Lmod.LawPreferenceLabel,
                                )() is M.truth_value:
                                    self.result = LawPreferenceOrdering(element)()
                                    remaining_elements = M.EmptyList
                                    remaining = M.EmptyList
                                else:
                                    remaining_elements = M.Tail(remaining_elements)()
                            else:
                                remaining_elements = M.Tail(remaining_elements)()
                if M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
                    remaining = M.Tail(remaining)()
        super().__init__(inputs=M.Pair(graph_version, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class LawOrderingFromLedger(M.Edge):
    """Reorder installed laws by recorded successes, then compression."""

    def __init__(self, ledger, installed):
        cap_text = M.GMPRepText(LAW_ORDERING_SCAN_CAP)()
        groups = FiringLedgerByLaw(ledger.records)()

        ordered = M.EmptyList
        law_scan_text = "0"
        remaining_installed = installed
        while M.IdentityCompare(remaining_installed, M.EmptyList)() is M.false_value:
            if GMPEqualText(law_scan_text, cap_text)() is M.truth_value:
                remaining_installed = M.EmptyList
            else:
                law_scan_text = GMPSuccText(law_scan_text)()
                law = M.Head(remaining_installed)()
                remaining_installed = M.Tail(remaining_installed)()
                score = LawLedgerScore(law, groups)()
                entry = M.Pair(law, M.Pair(score, M.EmptyList))

                reversed_front = M.EmptyList
                placed = M.false_value
                insert_scan_text = "0"
                remaining_ordered = ordered
                while M.IdentityCompare(
                    remaining_ordered,
                    M.EmptyList,
                )() is M.false_value:
                    if GMPEqualText(insert_scan_text, cap_text)() is M.truth_value:
                        reversed_front = M.Pair(
                            M.Head(remaining_ordered)(),
                            reversed_front,
                        )
                        remaining_ordered = M.Tail(remaining_ordered)()
                    else:
                        insert_scan_text = GMPSuccText(insert_scan_text)()
                        existing = M.Head(remaining_ordered)()
                        existing_score = M.Head(M.Tail(existing)())()
                        if M.IdentityCompare(placed, M.false_value)() is M.truth_value:
                            if LawScorePrecedes(score, existing_score)() is M.truth_value:
                                reversed_front = M.Pair(entry, reversed_front)
                                placed = M.truth_value
                        reversed_front = M.Pair(existing, reversed_front)
                        remaining_ordered = M.Tail(remaining_ordered)()
                if M.IdentityCompare(placed, M.false_value)() is M.truth_value:
                    reversed_front = M.Pair(entry, reversed_front)
                ordered = M.Reverse(reversed_front)()

        reversed_laws = M.EmptyList
        remaining_ordered = ordered
        while M.IdentityCompare(remaining_ordered, M.EmptyList)() is M.false_value:
            reversed_laws = M.Pair(
                M.Head(M.Head(remaining_ordered)())(),
                reversed_laws,
            )
            remaining_ordered = M.Tail(remaining_ordered)()
        self.result = M.Reverse(reversed_laws)()
        super().__init__(
            inputs=M.Pair(ledger, M.Pair(installed, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


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


MINE_CANDIDATE_CAP = M.GMPRep("200")


class MineNatFromGMPRep(M.Edge):
    """Convert a GMP machine value to a cached machine Nat."""

    def __init__(self, rep):
        result = M.Atom()
        result.value = rep
        self.result = result
        super().__init__(inputs=M.Pair(rep, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class MineNatSuccessor(M.Edge):
    """Increment a mining Nat without materializing a deep successor key."""

    def __init__(self, number, registry):
        rep = M.NatRepOf(number, registry)()
        next_text = GMPSuccText(M.GMPRepText(rep)())()
        successor = MineNatFromGMPRep(M.GMPRep(next_text))()
        self.result = M.Pair(successor, M.Pair(registry, M.EmptyList))
        super().__init__(
            inputs=M.Pair(number, M.Pair(registry, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class MineNatAdd(M.Edge):
    """Add mining Nats while retaining their bounded cached representation."""

    def __init__(self, left, right, registry):
        left_rep = M.NatRepOf(left, registry)()
        right_rep = M.NatRepOf(right, registry)()
        total_text = GMPAddText(
            M.GMPRepText(left_rep)(),
            M.GMPRepText(right_rep)(),
        )()
        total = MineNatFromGMPRep(M.GMPRep(total_text))()
        self.result = M.Pair(total, M.Pair(registry, M.EmptyList))
        super().__init__(
            inputs=M.Pair(
                left,
                M.Pair(right, M.Pair(registry, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class EnumerateCandidatePatterns(M.Edge):
    """Enumerate bounded closed one-neighborhood GraphVersion candidates."""

    def __init__(self, graph_version, max_size):
        registry = M.Tree(M.EmptyList)
        cap = MineNatFromGMPRep(MINE_CANDIDATE_CAP)()
        inspected = M.Zero
        emitted = M.Zero
        reversed_candidates = M.EmptyList
        remaining_nodes = GraphNodes(graph_version)()

        while M.IdentityCompare(remaining_nodes, M.EmptyList)() is M.false_value:
            if M.NatEq(inspected, cap, registry)() is M.truth_value:
                remaining_nodes = M.EmptyList
            elif M.NatEq(emitted, cap, registry)() is M.truth_value:
                remaining_nodes = M.EmptyList
            else:
                node = M.Head(remaining_nodes)()
                remaining_nodes = M.Tail(remaining_nodes)()
                stepped = MineNatSuccessor(inspected, registry)()
                inspected = M.Head(stepped)()
                registry = M.Head(M.Tail(stepped)())()

                candidate_ok = M.truth_value
                candidate_nodes = M.Pair(node, M.EmptyList)
                reversed_edges = M.EmptyList
                element_count = M.one
                if M.NatLess(max_size, element_count, registry)() is M.truth_value:
                    candidate_ok = M.false_value

                edge_scans = M.Zero
                remaining_edges = GraphEdges(graph_version)()
                while M.IdentityCompare(
                    remaining_edges,
                    M.EmptyList,
                )() is M.false_value:
                    if M.IdentityCompare(candidate_ok, M.false_value)() is M.truth_value:
                        remaining_edges = M.EmptyList
                    elif M.NatEq(edge_scans, cap, registry)() is M.truth_value:
                        candidate_ok = M.false_value
                        remaining_edges = M.EmptyList
                    else:
                        edge = M.Head(remaining_edges)()
                        remaining_edges = M.Tail(remaining_edges)()
                        stepped = MineNatSuccessor(edge_scans, registry)()
                        edge_scans = M.Head(stepped)()
                        registry = M.Head(M.Tail(stepped)())()

                        incident = M.false_value
                        endpoint_scans = M.Zero
                        remaining_endpoints = EdgeEndpoints(edge)()
                        while M.IdentityCompare(
                            remaining_endpoints,
                            M.EmptyList,
                        )() is M.false_value:
                            if M.NatEq(endpoint_scans, cap, registry)() is M.truth_value:
                                candidate_ok = M.false_value
                                remaining_endpoints = M.EmptyList
                            else:
                                endpoint = M.Head(remaining_endpoints)()
                                remaining_endpoints = M.Tail(remaining_endpoints)()
                                stepped = MineNatSuccessor(endpoint_scans, registry)()
                                endpoint_scans = M.Head(stepped)()
                                registry = M.Head(M.Tail(stepped)())()
                                if M.IdentityCompare(endpoint, node)() is M.truth_value:
                                    incident = M.truth_value

                        if M.AndAtom(candidate_ok, incident)() is M.truth_value:
                            reversed_edges = M.Pair(edge, reversed_edges)
                            stepped = MineNatSuccessor(element_count, registry)()
                            element_count = M.Head(stepped)()
                            registry = M.Head(M.Tail(stepped)())()
                            if M.NatLess(max_size, element_count, registry)() is M.truth_value:
                                candidate_ok = M.false_value
                            elif M.NatLess(cap, element_count, registry)() is M.truth_value:
                                candidate_ok = M.false_value

                            endpoint_scans = M.Zero
                            remaining_endpoints = EdgeEndpoints(edge)()
                            while M.IdentityCompare(
                                remaining_endpoints,
                                M.EmptyList,
                            )() is M.false_value:
                                if M.IdentityCompare(
                                    candidate_ok,
                                    M.false_value,
                                )() is M.truth_value:
                                    remaining_endpoints = M.EmptyList
                                elif M.NatEq(
                                    endpoint_scans,
                                    cap,
                                    registry,
                                )() is M.truth_value:
                                    candidate_ok = M.false_value
                                    remaining_endpoints = M.EmptyList
                                else:
                                    endpoint = M.Head(remaining_endpoints)()
                                    remaining_endpoints = M.Tail(remaining_endpoints)()
                                    stepped = MineNatSuccessor(endpoint_scans, registry)()
                                    endpoint_scans = M.Head(stepped)()
                                    registry = M.Head(M.Tail(stepped)())()

                                    present = M.false_value
                                    node_scans = M.Zero
                                    remaining_candidate_nodes = candidate_nodes
                                    while M.IdentityCompare(
                                        remaining_candidate_nodes,
                                        M.EmptyList,
                                    )() is M.false_value:
                                        if M.NatEq(
                                            node_scans,
                                            cap,
                                            registry,
                                        )() is M.truth_value:
                                            candidate_ok = M.false_value
                                            remaining_candidate_nodes = M.EmptyList
                                        else:
                                            candidate_node = M.Head(
                                                remaining_candidate_nodes
                                            )()
                                            remaining_candidate_nodes = M.Tail(
                                                remaining_candidate_nodes
                                            )()
                                            stepped = MineNatSuccessor(node_scans, registry)()
                                            node_scans = M.Head(stepped)()
                                            registry = M.Head(M.Tail(stepped)())()
                                            if M.IdentityCompare(
                                                candidate_node,
                                                endpoint,
                                            )() is M.truth_value:
                                                present = M.truth_value
                                                remaining_candidate_nodes = M.EmptyList

                                    if M.AndAtom(
                                        candidate_ok,
                                        M.IdentityCompare(
                                            present,
                                            M.false_value,
                                        )(),
                                    )() is M.truth_value:
                                        candidate_nodes = M.Reverse(
                                            M.Pair(
                                                endpoint,
                                                M.Reverse(candidate_nodes)(),
                                            )
                                        )()
                                        stepped = MineNatSuccessor(element_count, registry)()
                                        element_count = M.Head(stepped)()
                                        registry = M.Head(M.Tail(stepped)())()
                                        if M.NatLess(
                                            max_size,
                                            element_count,
                                            registry,
                                        )() is M.truth_value:
                                            candidate_ok = M.false_value
                                        elif M.NatLess(
                                            cap,
                                            element_count,
                                            registry,
                                        )() is M.truth_value:
                                            candidate_ok = M.false_value

                if M.IdentityCompare(candidate_ok, M.truth_value)() is M.truth_value:
                    candidate = GraphVersion(
                        candidate_nodes,
                        M.Reverse(reversed_edges)(),
                        M.EmptyList,
                    )()
                    reversed_candidates = M.Pair(candidate, reversed_candidates)
                    stepped = MineNatSuccessor(emitted, registry)()
                    emitted = M.Head(stepped)()
                    registry = M.Head(M.Tail(stepped)())()

        self.result = M.Reverse(reversed_candidates)()
        super().__init__(
            inputs=M.Pair(graph_version, M.Pair(max_size, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class BoundedFirstCompletedMatch(M.Edge):
    """Return the first completed Step-10 match within a machine fuel cap."""

    def __init__(self, pattern, host, match_cap=MINE_CANDIDATE_CAP):
        registry = M.Tree(M.EmptyList)
        cap = MineNatFromGMPRep(match_cap)()
        fuel_used = M.Zero
        pending = GraphElements(pattern)()
        cursor = SearchMatchCursor(M.EmptyList, pattern, host, pending)()
        start = SearchState(M.EmptyList, M.EmptyList, M.EmptyList, M.one, cursor)()
        frontier = M.Pair(start, M.EmptyList)
        result = M.EmptyList

        while M.IdentityCompare(frontier, M.EmptyList)() is M.false_value:
            if M.NatEq(fuel_used, cap, registry)() is M.truth_value:
                frontier = M.EmptyList
            elif M.IdentityCompare(result, M.EmptyList)() is M.false_value:
                frontier = M.EmptyList
            else:
                state = M.Head(frontier)()
                frontier = M.Tail(frontier)()
                stepped = MineNatSuccessor(fuel_used, registry)()
                fuel_used = M.Head(stepped)()
                registry = M.Head(M.Tail(stepped)())()
                cursor = SearchStateCursor(state)()
                if SearchMatchCursorComplete(cursor)() is M.truth_value:
                    mapping = Map(
                        pattern,
                        host,
                        SearchMatchCursorRoot(cursor)(),
                    )()
                    if MapSendsEveryElement(mapping, pattern)() is M.truth_value:
                        result = mapping
                else:
                    pending = SearchMatchCursorPending(cursor)()
                    pat = M.Head(pending)()
                    rest = M.Tail(pending)()
                    mapping = Map(
                        pattern,
                        host,
                        SearchMatchCursorRoot(cursor)(),
                    )()
                    alternatives = MapExtensionAlternatives(mapping, pat, host)()
                    while M.IdentityCompare(
                        alternatives,
                        M.EmptyList,
                    )() is M.false_value:
                        if M.NatEq(fuel_used, cap, registry)() is M.truth_value:
                            alternatives = M.EmptyList
                            frontier = M.EmptyList
                        else:
                            alternative = M.Head(alternatives)()
                            alternatives = M.Tail(alternatives)()
                            stepped = MineNatSuccessor(fuel_used, registry)()
                            fuel_used = M.Head(stepped)()
                            registry = M.Head(M.Tail(stepped)())()
                            root = M.Head(
                                M.Tail(M.Tail(M.Tail(alternative)())())()
                            )()
                            found = MappedHostForPat(root, pat)()
                            if M.IdentityCompare(
                                M.Head(found)(),
                                M.truth_value,
                            )() is M.truth_value:
                                if GraphElementCompatible(
                                    pat,
                                    M.Tail(found)(),
                                )() is M.truth_value:
                                    child_cursor = SearchMatchCursor(
                                        root,
                                        pattern,
                                        host,
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

        self.result = result
        super().__init__(
            inputs=M.Pair(
                pattern,
                M.Pair(host, M.Pair(match_cap, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class MineRecurringPatterns(M.Edge):
    """Mine latest-version candidates by summed bounded census counts."""

    def __init__(self, versions, min_count, max_size):
        registry = M.Tree(M.EmptyList)
        cap = MineNatFromGMPRep(MINE_CANDIDATE_CAP)()

        latest = M.EmptyList
        version_scans = M.Zero
        remaining_versions = versions
        versions_complete = M.truth_value
        while M.IdentityCompare(remaining_versions, M.EmptyList)() is M.false_value:
            if M.NatEq(version_scans, cap, registry)() is M.truth_value:
                versions_complete = M.false_value
                remaining_versions = M.EmptyList
            else:
                latest = M.Head(remaining_versions)()
                remaining_versions = M.Tail(remaining_versions)()
                stepped = MineNatSuccessor(version_scans, registry)()
                version_scans = M.Head(stepped)()
                registry = M.Head(M.Tail(stepped)())()

        candidates = M.EmptyList
        if M.IdentityCompare(versions_complete, M.truth_value)() is M.truth_value:
            if M.IdentityCompare(latest, M.EmptyList)() is M.false_value:
                candidates = EnumerateCandidatePatterns(latest, max_size)()

        reversed_unique_candidates = M.EmptyList
        candidate_dedup_scans = M.Zero
        remaining_candidates = candidates
        while M.IdentityCompare(
            remaining_candidates,
            M.EmptyList,
        )() is M.false_value:
            if M.NatEq(
                candidate_dedup_scans,
                cap,
                registry,
            )() is M.truth_value:
                remaining_candidates = M.EmptyList
            else:
                candidate = M.Head(remaining_candidates)()
                remaining_candidates = M.Tail(remaining_candidates)()
                stepped = MineNatSuccessor(
                    candidate_dedup_scans,
                    registry,
                )()
                candidate_dedup_scans = M.Head(stepped)()
                registry = M.Head(M.Tail(stepped)())()

                duplicate = M.false_value
                unique_scans = M.Zero
                remaining_unique = reversed_unique_candidates
                while M.IdentityCompare(
                    remaining_unique,
                    M.EmptyList,
                )() is M.false_value:
                    if M.NatEq(unique_scans, cap, registry)() is M.truth_value:
                        remaining_unique = M.EmptyList
                    else:
                        prior_candidate = M.Head(remaining_unique)()
                        forward = BoundedFirstCompletedMatch(
                            candidate,
                            prior_candidate,
                        )()
                        reverse = M.EmptyList
                        if M.IdentityCompare(
                            forward,
                            M.EmptyList,
                        )() is M.false_value:
                            reverse = BoundedFirstCompletedMatch(
                                prior_candidate,
                                candidate,
                            )()
                        if M.IdentityCompare(
                            reverse,
                            M.EmptyList,
                        )() is M.false_value:
                            duplicate = M.truth_value
                            remaining_unique = M.EmptyList
                        else:
                            remaining_unique = M.Tail(remaining_unique)()
                            stepped = MineNatSuccessor(unique_scans, registry)()
                            unique_scans = M.Head(stepped)()
                            registry = M.Head(M.Tail(stepped)())()

                if M.IdentityCompare(duplicate, M.false_value)() is M.truth_value:
                    reversed_unique_candidates = M.Pair(
                        candidate,
                        reversed_unique_candidates,
                    )

        candidates = M.Reverse(reversed_unique_candidates)()
        ledger = FiringLedger(registry)
        reversed_mined = M.EmptyList
        candidate_scans = M.Zero
        remaining_candidates = candidates
        while M.IdentityCompare(
            remaining_candidates,
            M.EmptyList,
        )() is M.false_value:
            if M.NatEq(candidate_scans, cap, ledger.registry)() is M.truth_value:
                remaining_candidates = M.EmptyList
            else:
                candidate = M.Head(remaining_candidates)()
                remaining_candidates = M.Tail(remaining_candidates)()
                stepped = MineNatSuccessor(candidate_scans, ledger.registry)()
                candidate_scans = M.Head(stepped)()
                ledger.registry = M.Head(M.Tail(stepped)())()

                counts = PatternCensus(ledger, candidate, versions)()
                total = M.Zero
                count_scans = M.Zero
                counts_complete = M.truth_value
                remaining_counts = counts
                while M.IdentityCompare(
                    remaining_counts,
                    M.EmptyList,
                )() is M.false_value:
                    if M.NatEq(
                        count_scans,
                        cap,
                        ledger.registry,
                    )() is M.truth_value:
                        counts_complete = M.false_value
                        remaining_counts = M.EmptyList
                    else:
                        added = MineNatAdd(
                            total,
                            M.Head(remaining_counts)(),
                            ledger.registry,
                        )()
                        total = M.Head(added)()
                        ledger.registry = M.Head(M.Tail(added)())()
                        remaining_counts = M.Tail(remaining_counts)()
                        stepped = MineNatSuccessor(count_scans, ledger.registry)()
                        count_scans = M.Head(stepped)()
                        ledger.registry = M.Head(M.Tail(stepped)())()

                frequent = M.false_value
                if M.IdentityCompare(counts_complete, M.truth_value)() is M.truth_value:
                    if M.NatLess(
                        total,
                        min_count,
                        ledger.registry,
                    )() is M.false_value:
                        frequent = M.truth_value

                duplicate = M.false_value
                mined_scans = M.Zero
                remaining_mined = reversed_mined
                while M.IdentityCompare(
                    remaining_mined,
                    M.EmptyList,
                )() is M.false_value:
                    if M.IdentityCompare(frequent, M.false_value)() is M.truth_value:
                        remaining_mined = M.EmptyList
                    elif M.NatEq(
                        mined_scans,
                        cap,
                        ledger.registry,
                    )() is M.truth_value:
                        duplicate = M.truth_value
                        remaining_mined = M.EmptyList
                    else:
                        entry = M.Head(remaining_mined)()
                        prior_candidate = M.Head(entry)()
                        forward = BoundedFirstCompletedMatch(
                            candidate,
                            prior_candidate,
                        )()
                        reverse = M.EmptyList
                        if M.IdentityCompare(
                            forward,
                            M.EmptyList,
                        )() is M.false_value:
                            reverse = BoundedFirstCompletedMatch(
                                prior_candidate,
                                candidate,
                            )()
                        if M.IdentityCompare(
                            reverse,
                            M.EmptyList,
                        )() is M.false_value:
                            duplicate = M.truth_value
                            remaining_mined = M.EmptyList
                        else:
                            remaining_mined = M.Tail(remaining_mined)()
                            stepped = MineNatSuccessor(mined_scans, ledger.registry)()
                            mined_scans = M.Head(stepped)()
                            ledger.registry = M.Head(M.Tail(stepped)())()

                if M.AndAtom(
                    frequent,
                    M.IdentityCompare(duplicate, M.false_value)(),
                )() is M.truth_value:
                    entry = M.Pair(
                        candidate,
                        M.Pair(total, M.EmptyList),
                    )
                    reversed_mined = M.Pair(entry, reversed_mined)

        self.result = M.Reverse(reversed_mined)()
        super().__init__(
            inputs=M.Pair(
                versions,
                M.Pair(min_count, M.Pair(max_size, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


HANDLE_PROPOSAL_CAP = M.GMPRep("10")
HANDLE_INTERFACE_SCAN_CAP = M.GMPRep("200")
SKIPPED_HANDLE_CANDIDATES = M.EmptyList


class PatternInterfaceNodes(M.Edge):
    """Return pattern nodes touching host edges outside the pattern."""

    def __init__(self, pattern, host_version):
        registry = M.Tree(M.EmptyList)
        scan_cap = MineNatFromGMPRep(HANDLE_INTERFACE_SCAN_CAP)()
        scanned = MineNatFromGMPRep(M.GMPRep("0"))()
        reversed_interface = M.EmptyList
        remaining_nodes = GraphNodes(pattern)()
        while M.IdentityCompare(remaining_nodes, M.EmptyList)() is M.false_value:
            if M.NatEq(scanned, scan_cap, registry)() is M.truth_value:
                remaining_nodes = M.EmptyList
            else:
                node = M.Head(remaining_nodes)()
                remaining_edges = GraphEdges(host_version)()
                touches_outside = M.false_value
                while M.IdentityCompare(
                    remaining_edges,
                    M.EmptyList,
                )() is M.false_value:
                    if M.NatEq(
                        scanned,
                        scan_cap,
                        registry,
                    )() is M.truth_value:
                        remaining_edges = M.EmptyList
                    else:
                        edge = M.Head(remaining_edges)()
                        if ChainHasTerm(
                            GraphEdges(pattern)(),
                            edge,
                        )() is M.false_value:
                            remaining_endpoints = EdgeEndpoints(edge)()
                            while M.IdentityCompare(
                                remaining_endpoints,
                                M.EmptyList,
                            )() is M.false_value:
                                if M.NatEq(
                                    scanned,
                                    scan_cap,
                                    registry,
                                )() is M.truth_value:
                                    remaining_endpoints = M.EmptyList
                                else:
                                    endpoint = M.Head(remaining_endpoints)()
                                    if M.IdentityCompare(
                                        endpoint,
                                        node,
                                    )() is M.truth_value:
                                        touches_outside = M.truth_value
                                        remaining_endpoints = M.EmptyList
                                        remaining_edges = M.EmptyList
                                    else:
                                        stepped = MineNatSuccessor(scanned, registry)()
                                        scanned = M.Head(stepped)()
                                        registry = M.Head(M.Tail(stepped)())()
                                        remaining_endpoints = M.Tail(
                                            remaining_endpoints
                                        )()
                            if M.IdentityCompare(
                                remaining_edges,
                                M.EmptyList,
                            )() is M.false_value:
                                stepped = MineNatSuccessor(scanned, registry)()
                                scanned = M.Head(stepped)()
                                registry = M.Head(M.Tail(stepped)())()
                                remaining_edges = M.Tail(remaining_edges)()
                        else:
                            stepped = MineNatSuccessor(scanned, registry)()
                            scanned = M.Head(stepped)()
                            registry = M.Head(M.Tail(stepped)())()
                            remaining_edges = M.Tail(remaining_edges)()
                if touches_outside is M.truth_value:
                    reversed_interface = M.Pair(node, reversed_interface)
                stepped = MineNatSuccessor(scanned, registry)()
                scanned = M.Head(stepped)()
                registry = M.Head(M.Tail(stepped)())()
                remaining_nodes = M.Tail(remaining_nodes)()

        self.result = M.Reverse(reversed_interface)()
        super().__init__(
            inputs=M.Pair(pattern, M.Pair(host_version, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class GenerateHandleProposals(M.Edge):
    """Mine witnessed patterns and submit bounded, mechanically checked folds."""

    def __init__(self, proposal_store, versions, ledger, min_count):
        candidate_cap = MineNatFromGMPRep(MINE_CANDIDATE_CAP)()
        proposal_cap = MineNatFromGMPRep(HANDLE_PROPOSAL_CAP)()
        pattern_max_size = MineNatFromGMPRep(MINE_CANDIDATE_CAP)()
        scanned = MineNatFromGMPRep(M.GMPRep("0"))()
        submitted_count = MineNatFromGMPRep(M.GMPRep("0"))()
        candidate_index = MineNatFromGMPRep(M.GMPRep("0"))()
        skipped = SKIPPED_HANDLE_CANDIDATES
        current_store = proposal_store

        latest_version = M.EmptyList
        remaining_versions = versions
        while M.IdentityCompare(remaining_versions, M.EmptyList)() is M.false_value:
            if M.NatEq(scanned, candidate_cap, ledger.registry)() is M.truth_value:
                remaining_versions = M.EmptyList
            else:
                latest_version = M.Head(remaining_versions)()
                stepped = MineNatSuccessor(scanned, ledger.registry)()
                scanned = M.Head(stepped)()
                ledger.registry = M.Head(M.Tail(stepped)())()
                remaining_versions = M.Tail(remaining_versions)()

        candidates = M.EmptyList
        if M.IdentityCompare(latest_version, M.EmptyList)() is M.false_value:
            candidates = MineRecurringPatterns(
                versions,
                min_count,
                pattern_max_size,
            )()

        scanned = MineNatFromGMPRep(M.GMPRep("0"))()
        remaining_candidates = candidates
        while M.IdentityCompare(remaining_candidates, M.EmptyList)() is M.false_value:
            if M.NatEq(submitted_count, proposal_cap, ledger.registry)() is M.truth_value:
                remaining_candidates = M.EmptyList
            elif M.NatEq(scanned, candidate_cap, ledger.registry)() is M.truth_value:
                remaining_candidates = M.EmptyList
            else:
                candidate_entry = M.Head(remaining_candidates)()
                pattern = M.Head(candidate_entry)()
                index_rep = M.NatRepOf(candidate_index, ledger.registry)()
                name = M.Char("mined-" + M.GMPRepText(index_rep)())
                handle = Handle(name, pattern)()
                interface_nodes = PatternInterfaceNodes(
                    pattern,
                    latest_version,
                )()
                report = PromotionReport(
                    handle,
                    interface_nodes,
                    ledger,
                    versions,
                )()
                signature_ok = M.false_value
                roundtrip_ok = M.false_value
                if M.IdentityCompare(report, M.EmptyList)() is M.false_value:
                    signature_entry = M.Head(M.Tail(report)())()
                    roundtrip_entry = M.Head(M.Tail(M.Tail(report)())())()
                    signature_ok = M.Head(M.Tail(signature_entry)())()
                    roundtrip_ok = M.Head(M.Tail(roundtrip_entry)())()

                if M.AndAtom(signature_ok, roundtrip_ok)() is M.truth_value:
                    current_store = ProposeHandle(
                        current_store,
                        handle,
                        interface_nodes,
                        report,
                    )()
                    stepped = MineNatSuccessor(
                        submitted_count,
                        ledger.registry,
                    )()
                    submitted_count = M.Head(stepped)()
                    ledger.registry = M.Head(M.Tail(stepped)())()
                else:
                    skipped = M.Pair(name, skipped)

                stepped = MineNatSuccessor(candidate_index, ledger.registry)()
                candidate_index = M.Head(stepped)()
                ledger.registry = M.Head(M.Tail(stepped)())()
                stepped = MineNatSuccessor(scanned, ledger.registry)()
                scanned = M.Head(stepped)()
                ledger.registry = M.Head(M.Tail(stepped)())()
                remaining_candidates = M.Tail(remaining_candidates)()

        skipped = M.Reverse(skipped)()
        self.result = M.Pair(
            current_store,
            M.Pair(submitted_count, M.Pair(skipped, M.EmptyList)),
        )
        super().__init__(
            inputs=M.Pair(
                proposal_store,
                M.Pair(
                    versions,
                    M.Pair(ledger, M.Pair(min_count, M.EmptyList)),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


COMPOSITION_PROPOSAL_CAP = M.GMPRep("10")
COMPOSITION_ELEMENT_SCAN_CAP = M.GMPRep("200")
SKIPPED_COMPOSITIONS = M.EmptyList


class ComposedFrom(M.Edge):
    """Machine origin evidence for a law composed from two witnessed laws."""

    def __init__(self, law_a, law_b):
        self.result = M.Pair(
            Lmod.ComposedFromLabel,
            M.Pair(law_a, M.Pair(law_b, M.EmptyList)),
        )
        super().__init__(
            inputs=M.Pair(law_a, M.Pair(law_b, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class FiringRecordMapping(M.Edge):
    """Recover the committed match map from a firing record's exact trace."""

    def __init__(self, record):
        prepared = M.Head(FiringRecordTrace(record)())()
        self.result = M.Head(M.Tail(M.Tail(prepared)())())()
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class MapRoot(M.Edge):
    """The immutable Send-root carried by a machine Map term."""

    def __init__(self, mapping):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(mapping)())())())()
        super().__init__(inputs=M.Pair(mapping, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ComposeWitnessedLaws(M.Edge):
    """Mechanically compose an adjacent, chronologically witnessed firing pair."""

    def __init__(self, record_a, record_b):
        law_a = FiringRecordLaw(record_a)()
        law_b = FiringRecordLaw(record_b)()
        registry = M.Tree(M.EmptyList)
        retained_nodes = self._retained(
            GraphNodes(LawInterface(law_a)())(),
            GraphNodes(LawInterface(law_b)())(),
            law_a,
            law_b,
            record_a,
            record_b,
            registry,
        )
        retained_edges = self._retained(
            GraphEdges(LawInterface(law_a)())(),
            GraphEdges(LawInterface(law_b)())(),
            law_a,
            law_b,
            record_a,
            record_b,
            registry,
        )
        obligations = self._obligations(law_a, law_b, registry)

        valid = M.AndAtom(
            M.Head(retained_nodes)(),
            M.AndAtom(
                M.Head(retained_edges)(),
                M.Head(obligations)(),
            )(),
        )()
        self.result = M.EmptyList
        if M.IdentityCompare(valid, M.truth_value)() is M.truth_value:
            node_payload = M.Tail(retained_nodes)()
            edge_payload = M.Tail(retained_edges)()
            interface = GraphVersion(
                M.Head(node_payload)(),
                M.Head(edge_payload)(),
                M.EmptyList,
            )()
            left_sends = M.Head(M.Tail(node_payload)())()
            edge_left_sends = M.Head(M.Tail(edge_payload)())()
            right_sends = M.Head(M.Tail(M.Tail(node_payload)())())()
            edge_right_sends = M.Head(M.Tail(M.Tail(edge_payload)())())()
            left_sends = self._join(left_sends, edge_left_sends)
            right_sends = self._join(right_sends, edge_right_sends)
            composite = Law(
                LawLeft(law_a)(),
                interface,
                LawRight(law_b)(),
                Map(interface, LawLeft(law_a)(), left_sends)(),
                Map(interface, LawRight(law_b)(), right_sends)(),
                M.Head(M.Tail(obligations)())(),
            )()
            if LawMapsComplete(composite)() is M.truth_value:
                self.result = composite

        super().__init__(
            inputs=M.Pair(record_a, M.Pair(record_b, M.EmptyList)),
            results=self.result,
        )

    def _lookup(self, root, source):
        found = MappedHostForPat(root, source)()
        return found

    def _join(self, first, second):
        reversed_first = M.Reverse(first)()
        result = second
        remaining = reversed_first
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            result = M.Pair(M.Head(remaining)(), result)
            remaining = M.Tail(remaining)()
        return result

    def _retained(
        self,
        source_elements,
        target_elements,
        law_a,
        law_b,
        record_a,
        record_b,
        registry,
    ):
        cap = MineNatFromGMPRep(COMPOSITION_ELEMENT_SCAN_CAP)()
        source_scans = MineNatFromGMPRep(M.GMPRep("0"))()
        valid = M.truth_value
        reversed_elements = M.EmptyList
        reversed_left_sends = M.EmptyList
        reversed_right_sends = M.EmptyList
        a_left_root = MapRoot(LawKToLeft(law_a)())()
        b_left_root = MapRoot(LawKToLeft(law_b)())()
        b_right_root = MapRoot(LawKToRight(law_b)())()
        firing_a_root = MapRoot(FiringRecordMapping(record_a)())()
        firing_b_root = MapRoot(FiringRecordMapping(record_b)())()
        remaining_source = source_elements

        while M.IdentityCompare(remaining_source, M.EmptyList)() is M.false_value:
            if M.NatEq(source_scans, cap, registry)() is M.truth_value:
                valid = M.false_value
                remaining_source = M.EmptyList
            else:
                source = M.Head(remaining_source)()
                remaining_source = M.Tail(remaining_source)()
                stepped = MineNatSuccessor(source_scans, registry)()
                source_scans = M.Head(stepped)()
                registry = M.Head(M.Tail(stepped)())()
                left_a = self._lookup(a_left_root, source)
                if M.IdentityCompare(M.Head(left_a)(), M.false_value)() is M.truth_value:
                    valid = M.false_value
                else:
                    actual_a = self._lookup(firing_a_root, M.Tail(left_a)())
                    if M.IdentityCompare(M.Head(actual_a)(), M.false_value)() is M.truth_value:
                        valid = M.false_value
                    else:
                        target_scans = MineNatFromGMPRep(M.GMPRep("0"))()
                        remaining_target = target_elements
                        matched = M.false_value
                        matched_target = M.EmptyList
                        while M.IdentityCompare(
                            remaining_target,
                            M.EmptyList,
                        )() is M.false_value:
                            if M.NatEq(target_scans, cap, registry)() is M.truth_value:
                                valid = M.false_value
                                remaining_target = M.EmptyList
                            elif M.IdentityCompare(
                                matched,
                                M.truth_value,
                            )() is M.truth_value:
                                remaining_target = M.EmptyList
                            else:
                                target = M.Head(remaining_target)()
                                remaining_target = M.Tail(remaining_target)()
                                stepped = MineNatSuccessor(target_scans, registry)()
                                target_scans = M.Head(stepped)()
                                registry = M.Head(M.Tail(stepped)())()
                                left_b = self._lookup(b_left_root, target)
                                if M.IdentityCompare(
                                    M.Head(left_b)(),
                                    M.false_value,
                                )() is M.truth_value:
                                    valid = M.false_value
                                else:
                                    actual_b = self._lookup(
                                        firing_b_root,
                                        M.Tail(left_b)(),
                                    )
                                    if M.IdentityCompare(
                                        M.Head(actual_b)(),
                                        M.false_value,
                                    )() is M.truth_value:
                                        valid = M.false_value
                                    elif M.TermEqual(
                                        M.Tail(actual_a)(),
                                        M.Tail(actual_b)(),
                                    )() is M.truth_value:
                                        matched = M.truth_value
                                        matched_target = target

                        if M.IdentityCompare(
                            matched,
                            M.truth_value,
                        )() is M.truth_value:
                            right_b = self._lookup(
                                b_right_root,
                                matched_target,
                            )
                            if M.IdentityCompare(
                                M.Head(right_b)(),
                                M.false_value,
                            )() is M.truth_value:
                                valid = M.false_value
                            else:
                                reversed_elements = M.Pair(
                                    source,
                                    reversed_elements,
                                )
                                reversed_left_sends = M.Pair(
                                    Send(source, M.Tail(left_a)())(),
                                    reversed_left_sends,
                                )
                                reversed_right_sends = M.Pair(
                                    Send(source, M.Tail(right_b)())(),
                                    reversed_right_sends,
                                )

        return M.Pair(
            valid,
            M.Pair(
                M.Reverse(reversed_elements)(),
                M.Pair(
                    M.Reverse(reversed_left_sends)(),
                    M.Pair(M.Reverse(reversed_right_sends)(), M.EmptyList),
                ),
            ),
        )

    def _obligations(self, law_a, law_b, registry):
        cap = MineNatFromGMPRep(COMPOSITION_ELEMENT_SCAN_CAP)()
        scans = MineNatFromGMPRep(M.GMPRep("0"))()
        valid = M.truth_value
        reversed_obligations = M.EmptyList
        remaining_laws = M.Pair(law_a, M.Pair(law_b, M.EmptyList))
        while M.IdentityCompare(remaining_laws, M.EmptyList)() is M.false_value:
            law = M.Head(remaining_laws)()
            remaining_laws = M.Tail(remaining_laws)()
            remaining = LawObligations(law)()
            while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
                if M.NatEq(scans, cap, registry)() is M.truth_value:
                    valid = M.false_value
                    remaining = M.EmptyList
                    remaining_laws = M.EmptyList
                else:
                    reversed_obligations = M.Pair(
                        M.Head(remaining)(),
                        reversed_obligations,
                    )
                    remaining = M.Tail(remaining)()
                    stepped = MineNatSuccessor(scans, registry)()
                    scans = M.Head(stepped)()
                    registry = M.Head(M.Tail(stepped)())()
        return M.Pair(valid, M.Pair(M.Reverse(reversed_obligations)(), M.EmptyList))

    def __call__(self):
        return self.result


class GenerateCompositionProposals(M.Edge):
    """Submit bounded pending proposals from adjacent witnessed firings."""

    def __init__(self, proposal_store, ledger):
        cap = MineNatFromGMPRep(COMPOSITION_PROPOSAL_CAP)()
        scan_cap = MineNatFromGMPRep(COMPOSITION_ELEMENT_SCAN_CAP)()
        submitted_count = MineNatFromGMPRep(M.GMPRep("0"))()
        record_index = MineNatFromGMPRep(M.GMPRep("0"))()
        scanned = MineNatFromGMPRep(M.GMPRep("0"))()
        skipped = SKIPPED_COMPOSITIONS
        current_store = proposal_store
        remaining = ledger.records
        registry = ledger.registry

        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            next_records = M.Tail(remaining)()
            if M.IdentityCompare(next_records, M.EmptyList)() is M.truth_value:
                remaining = M.EmptyList
            elif M.NatEq(submitted_count, cap, registry)() is M.truth_value:
                remaining = M.EmptyList
            elif M.NatEq(scanned, scan_cap, registry)() is M.truth_value:
                remaining = M.EmptyList
            else:
                record_a = M.Head(remaining)()
                record_b = M.Head(next_records)()
                law_a = FiringRecordLaw(record_a)()
                law_b = FiringRecordLaw(record_b)()
                next_index_step = MineNatSuccessor(record_index, registry)()
                next_index = M.Head(next_index_step)()
                registry = M.Head(M.Tail(next_index_step)())()
                contiguous = M.TermEqual(
                    FiringRecordG1(record_a)(),
                    FiringRecordG0(record_b)(),
                )()
                distinct = M.NotAtom(M.TermEqual(law_a, law_b)())()
                if M.AndAtom(contiguous, distinct)() is M.truth_value:
                    composite = ComposeWitnessedLaws(record_a, record_b)()
                    if M.IdentityCompare(composite, M.EmptyList)() is M.false_value:
                        justification = M.Pair(
                            record_index,
                            M.Pair(next_index, M.EmptyList),
                        )
                        proposal = Proposal(
                            composite,
                            ComposedFrom(law_a, law_b)(),
                        )()
                        current_store = ProposalStoreSubmit(
                            current_store,
                            proposal,
                        )()
                        current_store = ProposalStoreAttach(
                            current_store,
                            proposal,
                            JustifiedBy(proposal, justification)(),
                        )()
                        stepped = MineNatSuccessor(
                            submitted_count,
                            registry,
                        )()
                        submitted_count = M.Head(stepped)()
                        registry = M.Head(M.Tail(stepped)())()
                    else:
                        skipped = M.Pair(
                            M.Pair(
                                M.Head(law_a)(),
                                M.Pair(M.Head(law_b)(), M.EmptyList),
                            ),
                            skipped,
                        )
                stepped = MineNatSuccessor(scanned, registry)()
                scanned = M.Head(stepped)()
                registry = M.Head(M.Tail(stepped)())()
                record_index = next_index
                remaining = next_records

        self.result = M.Pair(
            current_store,
            M.Pair(submitted_count, M.Pair(M.Reverse(skipped)(), M.EmptyList)),
        )
        super().__init__(
            inputs=M.Pair(proposal_store, M.Pair(ledger, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class Surface(M.Edge):
    """A surface form: an ordered Pair chain of symbol atoms."""

    def __init__(self, symbol_chain):
        self.result = M.Pair(
            Lmod.SurfaceLabel,
            M.Pair(symbol_chain, M.EmptyList),
        )
        super().__init__(
            inputs=M.Pair(symbol_chain, M.EmptyList),
            results=self.result,
        )

    def __call__(self):
        return self.result


class Meaning(M.Edge):
    """A structural interpretation wrapped as a labeled term."""

    def __init__(self, graph_term):
        self.result = M.Pair(
            Lmod.MeaningLabel,
            M.Pair(graph_term, M.EmptyList),
        )
        super().__init__(
            inputs=M.Pair(graph_term, M.EmptyList),
            results=self.result,
        )

    def __call__(self):
        return self.result


class Corresponds(M.Edge):
    """A recorded correspondence between one surface and one meaning."""

    def __init__(self, surface_term, meaning_term, law):
        self.result = M.Pair(
            Lmod.CorrespondsLabel,
            M.Pair(
                surface_term,
                M.Pair(meaning_term, M.Pair(law, M.EmptyList)),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                surface_term,
                M.Pair(meaning_term, M.Pair(law, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class CorrespondenceApply(M.Edge):
    """Apply one correspondence law in one direction via the term matcher.

    The law is a compiled Law whose single L node is the source pattern and
    whose single R node is the target template. Returns the instantiated
    target term, or EmptyList when the source does not match.
    """

    def __init__(self, law, source_term):
        self.result = M.EmptyList
        if IsLawTerm(law)() is M.truth_value:
            left_nodes = GraphNodes(LawLeft(law)())()
            right_nodes = GraphNodes(LawRight(law)())()
            if M.IdentityCompare(left_nodes, M.EmptyList)() is M.false_value:
                if M.IdentityCompare(right_nodes, M.EmptyList)() is M.false_value:
                    pattern = M.Head(left_nodes)()
                    template = M.Head(right_nodes)()
                    matched = M.Match(pattern, source_term)()
                    if M.IdentityCompare(
                        M.Head(matched)(),
                        M.truth_value,
                    )() is M.truth_value:
                        self.result = M.Head(
                            M.Instantiate(template, M.Tail(matched)())(),
                        )()
        super().__init__(
            inputs=M.Pair(law, M.Pair(source_term, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


CORRESPONDENCE_SCAN_CAP = M.GMPRep("50")


class CorrespondenceWordEntry(M.Edge):
    """One vocabulary word: its parse law and its render association."""

    def __init__(self, word_symbol, nat):
        parse_law = CompileRuleToLaw(
            P.Rule(Surface(M.Pair(word_symbol, M.EmptyList))(), nat),
        )()
        self.result = M.Pair(
            word_symbol,
            M.Pair(nat, M.Pair(parse_law, M.EmptyList)),
        )
        super().__init__(
            inputs=M.Pair(word_symbol, M.Pair(nat, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class DefaultCorrespondenceVocabulary(M.Edge):
    """Hand-authored correspondence laws for spoken arithmetic sentences.

    Pair(template_law_chain, Pair(word_entry_chain, Pair(digit_word_chain,
    EmptyList))). Every law is compiled through CompileRuleToLaw; nothing
    here parses host strings.
    """

    def __init__(self):
        empty = M.EmptyList
        var_a = M.Pair(M.VarTag, M.Pair(M.Char("?a"), empty))
        var_b = M.Pair(M.VarTag, M.Pair(M.Char("?b"), empty))

        add_meaning = Meaning(
            M.Pair(
                M.ExprAddLabel,
                M.Pair(
                    Surface(M.Pair(var_a, empty))(),
                    M.Pair(Surface(M.Pair(var_b, empty))(), empty),
                ),
            ),
        )()
        mul_meaning = Meaning(
            M.Pair(
                M.ExprMulLabel,
                M.Pair(
                    Surface(M.Pair(var_a, empty))(),
                    M.Pair(Surface(M.Pair(var_b, empty))(), empty),
                ),
            ),
        )()

        sum_sentence = Surface(
            M.Pair(
                M.Char("the"),
                M.Pair(
                    M.Char("sum"),
                    M.Pair(
                        M.Char("of"),
                        M.Pair(
                            var_a,
                            M.Pair(M.Char("and"), M.Pair(var_b, empty)),
                        ),
                    ),
                ),
            ),
        )()
        product_sentence = Surface(
            M.Pair(
                M.Char("the"),
                M.Pair(
                    M.Char("product"),
                    M.Pair(
                        M.Char("of"),
                        M.Pair(
                            var_a,
                            M.Pair(M.Char("and"), M.Pair(var_b, empty)),
                        ),
                    ),
                ),
            ),
        )()
        plus_sentence = Surface(
            M.Pair(var_a, M.Pair(M.Char("plus"), M.Pair(var_b, empty))),
        )()
        times_sentence = Surface(
            M.Pair(var_a, M.Pair(M.Char("times"), M.Pair(var_b, empty))),
        )()

        templates = M.Pair(
            CompileRuleToLaw(P.Rule(sum_sentence, add_meaning))(),
            M.Pair(
                CompileRuleToLaw(P.Rule(product_sentence, mul_meaning))(),
                M.Pair(
                    CompileRuleToLaw(P.Rule(plus_sentence, add_meaning))(),
                    M.Pair(
                        CompileRuleToLaw(P.Rule(times_sentence, mul_meaning))(),
                        empty,
                    ),
                ),
            ),
        )

        words = M.Pair(
            CorrespondenceWordEntry(M.Char("zero"), M.Zero)(),
            M.Pair(
                CorrespondenceWordEntry(M.Char("one"), M.one)(),
                M.Pair(
                    CorrespondenceWordEntry(M.Char("two"), M.two)(),
                    M.Pair(
                        CorrespondenceWordEntry(M.Char("three"), M.three)(),
                        M.Pair(
                            CorrespondenceWordEntry(M.Char("four"), M.four)(),
                            M.Pair(
                                CorrespondenceWordEntry(M.Char("five"), M.five)(),
                                M.Pair(
                                    CorrespondenceWordEntry(M.Char("six"), M.six)(),
                                    M.Pair(
                                        CorrespondenceWordEntry(
                                            M.Char("seven"),
                                            M.seven,
                                        )(),
                                        M.Pair(
                                            CorrespondenceWordEntry(
                                                M.Char("eight"),
                                                M.eight,
                                            )(),
                                            M.Pair(
                                                CorrespondenceWordEntry(
                                                    M.Char("nine"),
                                                    M.nine,
                                                )(),
                                                empty,
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

        digit_words = M.Pair(
            M.Pair(M.Char("0"), M.Pair(M.Char("zero"), empty)),
            M.Pair(
                M.Pair(M.Char("1"), M.Pair(M.Char("one"), empty)),
                M.Pair(
                    M.Pair(M.Char("2"), M.Pair(M.Char("two"), empty)),
                    M.Pair(
                        M.Pair(M.Char("3"), M.Pair(M.Char("three"), empty)),
                        M.Pair(
                            M.Pair(M.Char("4"), M.Pair(M.Char("four"), empty)),
                            M.Pair(
                                M.Pair(M.Char("5"), M.Pair(M.Char("five"), empty)),
                                M.Pair(
                                    M.Pair(M.Char("6"), M.Pair(M.Char("six"), empty)),
                                    M.Pair(
                                        M.Pair(
                                            M.Char("7"),
                                            M.Pair(M.Char("seven"), empty),
                                        ),
                                        M.Pair(
                                            M.Pair(
                                                M.Char("8"),
                                                M.Pair(M.Char("eight"), empty),
                                            ),
                                            M.Pair(
                                                M.Pair(
                                                    M.Char("9"),
                                                    M.Pair(M.Char("nine"), empty),
                                                ),
                                                empty,
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

        self.result = M.Pair(
            templates,
            M.Pair(words, M.Pair(digit_words, empty)),
        )
        super().__init__(inputs=empty, results=self.result)

    def __call__(self):
        return self.result


class CorrespondenceResolveWord(M.Edge):
    """Resolve one Surface word to its Nat through the word parse laws."""

    def __init__(self, word_entries, surface_term):
        cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        scan_text = "0"
        self.result = M.EmptyList
        remaining = word_entries
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                remaining = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                entry = M.Head(remaining)()
                law = M.Head(M.Tail(M.Tail(entry)())())()
                value = CorrespondenceApply(law, surface_term)()
                if M.IdentityCompare(value, M.EmptyList)() is M.false_value:
                    self.result = value
                    remaining = M.EmptyList
                else:
                    remaining = M.Tail(remaining)()
        super().__init__(
            inputs=M.Pair(word_entries, M.Pair(surface_term, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class MeaningEvaluate(M.Edge):
    """Evaluate a parsed Meaning to a Nat through the arithmetic edges."""

    def __init__(self, meaning_term, word_entries, registry):
        self.word_entries = word_entries
        evaluated = self._eval(meaning_term, registry, "0")
        self.result = evaluated
        super().__init__(
            inputs=M.Pair(
                meaning_term,
                M.Pair(word_entries, M.Pair(registry, M.EmptyList)),
            ),
            results=self.result,
        )

    def _eval(self, term, registry, depth_text):
        cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        if GMPEqualText(depth_text, cap_text)() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
        next_depth = GMPSuccText(depth_text)()
        if M.IsPair(term)() is M.truth_value:
            label = M.Head(term)()
            if M.TermEqual(label, Lmod.MeaningLabel)() is M.truth_value:
                return self._eval(M.Head(M.Tail(term)())(), registry, next_depth)
            if M.TermEqual(label, Lmod.SurfaceLabel)() is M.truth_value:
                value = CorrespondenceResolveWord(self.word_entries, term)()
                if M.IdentityCompare(value, M.EmptyList)() is M.truth_value:
                    chain = M.Head(M.Tail(term)())()
                    if M.IdentityCompare(chain, M.EmptyList)() is M.false_value:
                        if M.IdentityCompare(
                            M.Tail(chain)(),
                            M.EmptyList,
                        )() is M.truth_value:
                            element = M.Head(chain)()
                            if M.IsNat(element, registry)() is M.truth_value:
                                value = element
                return M.Pair(value, M.Pair(registry, M.EmptyList))
            arguments = M.Tail(term)()
            is_add = M.TermEqual(label, M.ExprAddLabel)()
            is_mul = M.TermEqual(label, M.ExprMulLabel)()
            if M.OrAtom(is_add, is_mul)() is M.truth_value:
                left_pair = self._eval(M.Head(arguments)(), registry, next_depth)
                left_value = M.Head(left_pair)()
                registry = M.Head(M.Tail(left_pair)())()
                if M.IdentityCompare(left_value, M.EmptyList)() is M.truth_value:
                    return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
                right_pair = self._eval(
                    M.Head(M.Tail(arguments)())(),
                    registry,
                    next_depth,
                )
                right_value = M.Head(right_pair)()
                registry = M.Head(M.Tail(right_pair)())()
                if M.IdentityCompare(right_value, M.EmptyList)() is M.truth_value:
                    return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
                if M.IdentityCompare(is_add, M.truth_value)() is M.truth_value:
                    return M.Add(left_value, right_value, registry)()
                return M.Multiply(left_value, right_value, registry)()
            return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
        if M.IsNat(term, registry)() is M.truth_value:
            return M.Pair(term, M.Pair(registry, M.EmptyList))
        return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))

    def __call__(self):
        return self.result


class RenderNatSurface(M.Edge):
    """Render a Nat as a Surface of number words, one word per digit."""

    def __init__(self, nat, digit_words, registry):
        cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        self.result = M.EmptyList
        rep = M.NatRepOf(nat, registry)()
        if M.IdentityCompare(rep, M.EmptyList)() is M.false_value:
            digits = GMPRepDigitList(rep)()
            reversed_words = M.EmptyList
            complete = M.truth_value
            scan_text = "0"
            remaining_digits = digits
            while M.IdentityCompare(remaining_digits, M.EmptyList)() is M.false_value:
                if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                    complete = M.false_value
                    remaining_digits = M.EmptyList
                else:
                    scan_text = GMPSuccText(scan_text)()
                    digit = M.Head(remaining_digits)()
                    word = M.EmptyList
                    lookup_text = "0"
                    remaining_words = digit_words
                    while M.IdentityCompare(
                        remaining_words,
                        M.EmptyList,
                    )() is M.false_value:
                        if GMPEqualText(lookup_text, cap_text)() is M.truth_value:
                            remaining_words = M.EmptyList
                        else:
                            lookup_text = GMPSuccText(lookup_text)()
                            association = M.Head(remaining_words)()
                            if M.Compare(
                                M.Head(association)(),
                                digit,
                            )() is M.truth_value:
                                word = M.Head(M.Tail(association)())()
                                remaining_words = M.EmptyList
                            else:
                                remaining_words = M.Tail(remaining_words)()
                    if M.IdentityCompare(word, M.EmptyList)() is M.truth_value:
                        complete = M.false_value
                        remaining_digits = M.EmptyList
                    else:
                        reversed_words = M.Pair(word, reversed_words)
                        remaining_digits = M.Tail(remaining_digits)()
            if M.IdentityCompare(complete, M.truth_value)() is M.truth_value:
                self.result = Surface(M.Reverse(reversed_words)())()
        super().__init__(
            inputs=M.Pair(
                nat,
                M.Pair(digit_words, M.Pair(registry, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class ConverseInterpretations(M.Edge):
    """Every structurally distinct Meaning for one group-free Surface chain.

    All template laws run within the scan cap; every distinct Meaning is
    retained as Pair(meaning, Pair(law, EmptyList)). Nothing collapses to
    the first match. Word and spliced-Nat readings apply when no template
    matches.
    """

    def __init__(self, vocabulary, surface_term, registry):
        cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        templates = M.Head(vocabulary)()
        word_entries = M.Head(M.Tail(vocabulary)())()

        reversed_interpretations = M.EmptyList
        scan_text = "0"
        remaining = templates
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                remaining = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                law = M.Head(remaining)()
                candidate = CorrespondenceApply(law, surface_term)()
                if M.IdentityCompare(candidate, M.EmptyList)() is M.false_value:
                    duplicate = M.false_value
                    check_text = "0"
                    checking = reversed_interpretations
                    while M.IdentityCompare(checking, M.EmptyList)() is M.false_value:
                        if GMPEqualText(check_text, cap_text)() is M.truth_value:
                            checking = M.EmptyList
                        else:
                            check_text = GMPSuccText(check_text)()
                            if M.Compare(
                                M.Head(M.Head(checking)())(),
                                candidate,
                            )() is M.truth_value:
                                duplicate = M.truth_value
                                checking = M.EmptyList
                            else:
                                checking = M.Tail(checking)()
                    if M.IdentityCompare(duplicate, M.false_value)() is M.truth_value:
                        reversed_interpretations = M.Pair(
                            M.Pair(candidate, M.Pair(law, M.EmptyList)),
                            reversed_interpretations,
                        )
                remaining = M.Tail(remaining)()

        if M.IdentityCompare(
            reversed_interpretations,
            M.EmptyList,
        )() is M.truth_value:
            direct = CorrespondenceResolveWord(word_entries, surface_term)()
            if M.IdentityCompare(direct, M.EmptyList)() is M.truth_value:
                chain = M.Head(M.Tail(surface_term)())()
                if M.IdentityCompare(chain, M.EmptyList)() is M.false_value:
                    if M.IdentityCompare(
                        M.Tail(chain)(),
                        M.EmptyList,
                    )() is M.truth_value:
                        element = M.Head(chain)()
                        if M.IsNat(element, registry)() is M.truth_value:
                            direct = element
            if M.IdentityCompare(direct, M.EmptyList)() is M.false_value:
                reversed_interpretations = M.Pair(
                    M.Pair(Meaning(direct)(), M.Pair(M.EmptyList, M.EmptyList)),
                    reversed_interpretations,
                )

        self.result = M.Pair(
            M.Reverse(reversed_interpretations)(),
            M.Pair(registry, M.EmptyList),
        )
        super().__init__(
            inputs=M.Pair(
                vocabulary,
                M.Pair(surface_term, M.Pair(registry, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class ConverseValue(M.Edge):
    """Evaluate one group-free Surface chain to its single agreed Nat value.

    Every interpretation is enumerated and evaluated; the value returns
    only when all evaluable interpretations agree. Zero interpretations or
    conflicting values return EmptyList explicitly — never a silent pick.
    """

    def __init__(self, vocabulary, surface_term, registry):
        cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        word_entries = M.Head(M.Tail(vocabulary)())()
        interpreted = ConverseInterpretations(vocabulary, surface_term, registry)()
        interpretations = M.Head(interpreted)()
        registry = M.Head(M.Tail(interpreted)())()

        value = M.EmptyList
        conflicted = M.false_value
        scan_text = "0"
        remaining = interpretations
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                remaining = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                meaning = M.Head(M.Head(remaining)())()
                evaluated = MeaningEvaluate(meaning, word_entries, registry)()
                candidate = M.Head(evaluated)()
                registry = M.Head(M.Tail(evaluated)())()
                if M.IdentityCompare(candidate, M.EmptyList)() is M.false_value:
                    if M.IdentityCompare(value, M.EmptyList)() is M.truth_value:
                        value = candidate
                    elif M.NatEq(value, candidate, registry)() is M.false_value:
                        conflicted = M.truth_value
                        remaining = M.EmptyList
                if M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
                    remaining = M.Tail(remaining)()

        if M.IdentityCompare(conflicted, M.truth_value)() is M.truth_value:
            value = M.EmptyList
        self.result = M.Pair(value, M.Pair(registry, M.EmptyList))
        super().__init__(
            inputs=M.Pair(
                vocabulary,
                M.Pair(surface_term, M.Pair(registry, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SurfaceReduceGroups(M.Edge):
    """Reduce innermost parenthesis groups to their evaluated Nat values.

    Each pass finds one innermost balanced group, evaluates its group-free
    chain through ConverseValue, and splices the Nat back into the sentence.
    Unbalanced or unparseable groups return EmptyList explicitly.
    """

    def __init__(self, vocabulary, surface_term, registry):
        cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        open_symbol = M.Char("(")
        close_symbol = M.Char(")")
        chain = M.Head(M.Tail(surface_term)())()
        failed = M.false_value
        pass_text = "0"
        reducing = M.truth_value
        while M.IdentityCompare(reducing, M.truth_value)() is M.truth_value:
            if GMPEqualText(pass_text, cap_text)() is M.truth_value:
                failed = M.truth_value
                reducing = M.false_value
            else:
                pass_text = GMPSuccText(pass_text)()
                reversed_before = M.EmptyList
                reversed_inner = M.EmptyList
                open_atom = M.EmptyList
                seen_open = M.false_value
                reduced_once = M.false_value
                scan_text = "0"
                remaining = chain
                while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
                    if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                        failed = M.truth_value
                        remaining = M.EmptyList
                    else:
                        scan_text = GMPSuccText(scan_text)()
                        element = M.Head(remaining)()
                        if M.Compare(element, open_symbol)() is M.truth_value:
                            if M.IdentityCompare(
                                seen_open,
                                M.truth_value,
                            )() is M.truth_value:
                                reversed_before = M.Pair(
                                    open_atom,
                                    reversed_before,
                                )
                                flush = M.Reverse(reversed_inner)()
                                while M.IdentityCompare(
                                    flush,
                                    M.EmptyList,
                                )() is M.false_value:
                                    reversed_before = M.Pair(
                                        M.Head(flush)(),
                                        reversed_before,
                                    )
                                    flush = M.Tail(flush)()
                            open_atom = element
                            seen_open = M.truth_value
                            reversed_inner = M.EmptyList
                            remaining = M.Tail(remaining)()
                        elif M.Compare(element, close_symbol)() is M.truth_value:
                            if M.IdentityCompare(
                                seen_open,
                                M.false_value,
                            )() is M.truth_value:
                                failed = M.truth_value
                                remaining = M.EmptyList
                            else:
                                inner_chain = M.Reverse(reversed_inner)()
                                if M.IdentityCompare(
                                    inner_chain,
                                    M.EmptyList,
                                )() is M.truth_value:
                                    failed = M.truth_value
                                    remaining = M.EmptyList
                                else:
                                    valued = ConverseValue(
                                        vocabulary,
                                        Surface(inner_chain)(),
                                        registry,
                                    )()
                                    value = M.Head(valued)()
                                    registry = M.Head(M.Tail(valued)())()
                                    if M.IdentityCompare(
                                        value,
                                        M.EmptyList,
                                    )() is M.truth_value:
                                        failed = M.truth_value
                                        remaining = M.EmptyList
                                    else:
                                        rebuilt = M.Tail(remaining)()
                                        spliced = M.Pair(value, reversed_before)
                                        while M.IdentityCompare(
                                            spliced,
                                            M.EmptyList,
                                        )() is M.false_value:
                                            rebuilt = M.Pair(
                                                M.Head(spliced)(),
                                                rebuilt,
                                            )
                                            spliced = M.Tail(spliced)()
                                        chain = rebuilt
                                        reduced_once = M.truth_value
                                        remaining = M.EmptyList
                        else:
                            if M.IdentityCompare(
                                seen_open,
                                M.truth_value,
                            )() is M.truth_value:
                                reversed_inner = M.Pair(element, reversed_inner)
                            else:
                                reversed_before = M.Pair(element, reversed_before)
                            remaining = M.Tail(remaining)()
                if M.IdentityCompare(failed, M.truth_value)() is M.truth_value:
                    reducing = M.false_value
                elif M.IdentityCompare(reduced_once, M.false_value)() is M.truth_value:
                    if M.IdentityCompare(seen_open, M.truth_value)() is M.truth_value:
                        failed = M.truth_value
                    reducing = M.false_value

        reduced_surface = M.EmptyList
        if M.IdentityCompare(failed, M.false_value)() is M.truth_value:
            reduced_surface = Surface(chain)()
        self.result = M.Pair(reduced_surface, M.Pair(registry, M.EmptyList))
        super().__init__(
            inputs=M.Pair(
                vocabulary,
                M.Pair(surface_term, M.Pair(registry, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class Understood(M.Edge):
    """A successful interpretation: surface, meaning, law, and answer."""

    def __init__(self, surface_term, meaning_term, law, answer_surface):
        self.result = M.Pair(
            Lmod.UnderstoodLabel,
            M.Pair(
                surface_term,
                M.Pair(
                    meaning_term,
                    M.Pair(law, M.Pair(answer_surface, M.EmptyList)),
                ),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                surface_term,
                M.Pair(
                    meaning_term,
                    M.Pair(law, M.Pair(answer_surface, M.EmptyList)),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class NotUnderstood(M.Edge):
    """An explicit interpretation failure carrying its structured reason."""

    def __init__(self, surface_term, reason):
        self.result = M.Pair(
            Lmod.NotUnderstoodLabel,
            M.Pair(surface_term, M.Pair(reason, M.EmptyList)),
        )
        super().__init__(
            inputs=M.Pair(surface_term, M.Pair(reason, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class AmbiguousResult(M.Edge):
    """Distinct disagreeing interpretations retained, none chosen."""

    def __init__(self, surface_term, interpretations):
        self.result = M.Pair(
            Lmod.AmbiguousLabel,
            M.Pair(surface_term, M.Pair(interpretations, M.EmptyList)),
        )
        super().__init__(
            inputs=M.Pair(surface_term, M.Pair(interpretations, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SurfaceUnknownWords(M.Edge):
    """Words of a Surface chain with no entry, template mention, or grouping."""

    def __init__(self, vocabulary, surface_term, registry):
        cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        templates = M.Head(vocabulary)()
        word_entries = M.Head(M.Tail(vocabulary)())()

        reversed_known = M.EmptyList
        entry_scan_text = "0"
        remaining_entries = word_entries
        while M.IdentityCompare(remaining_entries, M.EmptyList)() is M.false_value:
            if GMPEqualText(entry_scan_text, cap_text)() is M.truth_value:
                remaining_entries = M.EmptyList
            else:
                entry_scan_text = GMPSuccText(entry_scan_text)()
                reversed_known = M.Pair(
                    M.Head(M.Head(remaining_entries)())(),
                    reversed_known,
                )
                remaining_entries = M.Tail(remaining_entries)()
        template_scan_text = "0"
        remaining_templates = templates
        while M.IdentityCompare(remaining_templates, M.EmptyList)() is M.false_value:
            if GMPEqualText(template_scan_text, cap_text)() is M.truth_value:
                remaining_templates = M.EmptyList
            else:
                template_scan_text = GMPSuccText(template_scan_text)()
                law = M.Head(remaining_templates)()
                left_nodes = GraphNodes(LawLeft(law)())()
                if M.IdentityCompare(left_nodes, M.EmptyList)() is M.false_value:
                    pattern = M.Head(left_nodes)()
                    if M.IsPair(pattern)() is M.truth_value:
                        chain = M.Head(M.Tail(pattern)())()
                        word_scan_text = "0"
                        while M.IdentityCompare(chain, M.EmptyList)() is M.false_value:
                            if GMPEqualText(
                                word_scan_text,
                                cap_text,
                            )() is M.truth_value:
                                chain = M.EmptyList
                            else:
                                word_scan_text = GMPSuccText(word_scan_text)()
                                element = M.Head(chain)()
                                if P.IsVarPattern(element)() is M.false_value:
                                    reversed_known = M.Pair(element, reversed_known)
                                chain = M.Tail(chain)()
                remaining_templates = M.Tail(remaining_templates)()
        known = M.Pair(
            M.Char("("),
            M.Pair(M.Char(")"), M.Reverse(reversed_known)()),
        )

        reversed_unknown = M.EmptyList
        scan_text = "0"
        remaining = M.Head(M.Tail(surface_term)())()
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                remaining = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                word = M.Head(remaining)()
                if M.IsNat(word, registry)() is M.false_value:
                    found = M.false_value
                    check_text = "0"
                    checking = known
                    while M.IdentityCompare(checking, M.EmptyList)() is M.false_value:
                        if GMPEqualText(check_text, cap_text)() is M.truth_value:
                            checking = M.EmptyList
                        else:
                            check_text = GMPSuccText(check_text)()
                            if M.Compare(M.Head(checking)(), word)() is M.truth_value:
                                found = M.truth_value
                                checking = M.EmptyList
                            else:
                                checking = M.Tail(checking)()
                    if M.IdentityCompare(found, M.false_value)() is M.truth_value:
                        reversed_unknown = M.Pair(word, reversed_unknown)
                remaining = M.Tail(remaining)()
        self.result = M.Reverse(reversed_unknown)()
        super().__init__(
            inputs=M.Pair(
                vocabulary,
                M.Pair(surface_term, M.Pair(registry, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class Converse(M.Edge):
    """Interpret a Surface sentence and return an explicit result term.

    Parenthesis groups reduce innermost-first through the same laws before
    the sentence templates run. Returns Pair(result_term, Pair(registry,
    EmptyList)) where result_term is Understood, NotUnderstood with a
    structured reason, or Ambiguous with every disagreeing interpretation.
    Nothing is guessed and no interpretation is silently discarded.
    """

    def __init__(self, vocabulary, surface_term, registry):
        cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        word_entries = M.Head(M.Tail(vocabulary)())()
        digit_words = M.Head(M.Tail(M.Tail(vocabulary)())())()

        unknown_words = SurfaceUnknownWords(vocabulary, surface_term, registry)()
        outcome = M.EmptyList
        if M.IdentityCompare(unknown_words, M.EmptyList)() is M.false_value:
            outcome = NotUnderstood(
                surface_term,
                M.Pair(
                    Lmod.ReasonUnknownWordLabel,
                    M.Pair(unknown_words, M.EmptyList),
                ),
            )()

        if M.IdentityCompare(outcome, M.EmptyList)() is M.truth_value:
            reduced = SurfaceReduceGroups(vocabulary, surface_term, registry)()
            reduced_surface = M.Head(reduced)()
            registry = M.Head(M.Tail(reduced)())()
            if M.IdentityCompare(reduced_surface, M.EmptyList)() is M.truth_value:
                outcome = NotUnderstood(
                    surface_term,
                    M.Pair(
                        Lmod.ReasonGroupLabel,
                        M.Pair(surface_term, M.EmptyList),
                    ),
                )()
            else:
                interpreted = ConverseInterpretations(
                    vocabulary,
                    reduced_surface,
                    registry,
                )()
                interpretations = M.Head(interpreted)()
                registry = M.Head(M.Tail(interpreted)())()
                if M.IdentityCompare(
                    interpretations,
                    M.EmptyList,
                )() is M.truth_value:
                    outcome = NotUnderstood(
                        surface_term,
                        M.Pair(
                            Lmod.ReasonNoCorrespondenceLabel,
                            M.Pair(reduced_surface, M.EmptyList),
                        ),
                    )()
                else:
                    value = M.EmptyList
                    chosen = M.EmptyList
                    conflicted = M.false_value
                    reversed_valued = M.EmptyList
                    scan_text = "0"
                    remaining = interpretations
                    while M.IdentityCompare(
                        remaining,
                        M.EmptyList,
                    )() is M.false_value:
                        if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                            remaining = M.EmptyList
                        else:
                            scan_text = GMPSuccText(scan_text)()
                            interpretation = M.Head(remaining)()
                            meaning = M.Head(interpretation)()
                            evaluated = MeaningEvaluate(
                                meaning,
                                word_entries,
                                registry,
                            )()
                            candidate = M.Head(evaluated)()
                            registry = M.Head(M.Tail(evaluated)())()
                            if M.IdentityCompare(
                                candidate,
                                M.EmptyList,
                            )() is M.false_value:
                                reversed_valued = M.Pair(
                                    interpretation,
                                    reversed_valued,
                                )
                                if M.IdentityCompare(
                                    value,
                                    M.EmptyList,
                                )() is M.truth_value:
                                    value = candidate
                                    chosen = interpretation
                                elif M.NatEq(
                                    value,
                                    candidate,
                                    registry,
                                )() is M.false_value:
                                    conflicted = M.truth_value
                            remaining = M.Tail(remaining)()
                    if M.IdentityCompare(conflicted, M.truth_value)() is M.truth_value:
                        outcome = AmbiguousResult(
                            surface_term,
                            M.Reverse(reversed_valued)(),
                        )()
                    elif M.IdentityCompare(value, M.EmptyList)() is M.truth_value:
                        outcome = NotUnderstood(
                            surface_term,
                            M.Pair(
                                Lmod.ReasonEvaluationLabel,
                                M.Pair(interpretations, M.EmptyList),
                            ),
                        )()
                    else:
                        answer = RenderNatSurface(value, digit_words, registry)()
                        outcome = Understood(
                            surface_term,
                            M.Head(chosen)(),
                            M.Head(M.Tail(chosen)())(),
                            answer,
                        )()

        self.result = M.Pair(outcome, M.Pair(registry, M.EmptyList))
        super().__init__(
            inputs=M.Pair(
                vocabulary,
                M.Pair(surface_term, M.Pair(registry, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


CORRESPONDENCE_INDUCTION_CAP = M.GMPRep("10")


class CorrespondenceExample(M.Edge):
    """One recorded Surface/Meaning pair with its evidence tag."""

    def __init__(self, surface_term, meaning_term, evidence):
        self.result = M.Pair(
            Lmod.CorrespondenceExampleLabel,
            M.Pair(
                surface_term,
                M.Pair(meaning_term, M.Pair(evidence, M.EmptyList)),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                surface_term,
                M.Pair(meaning_term, M.Pair(evidence, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class CorrespondenceExampleSurface(M.Edge):
    def __init__(self, example):
        self.result = M.Head(M.Tail(example)())()
        super().__init__(inputs=M.Pair(example, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CorrespondenceExampleMeaning(M.Edge):
    def __init__(self, example):
        self.result = M.Head(M.Tail(M.Tail(example)())())()
        super().__init__(inputs=M.Pair(example, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CorrespondenceExampleEvidence(M.Edge):
    def __init__(self, example):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(example)())())())()
        super().__init__(inputs=M.Pair(example, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class AntiUnifyCorrespondence(M.Edge):
    """Bounded structural anti-unification of two correspondence examples.

    Differing aligned surface words become shared variables; differing
    aligned meaning subterms must resolve to the same word differences and
    become Surface holes over the same variables. Returns Pair(parse_law,
    Pair(render_law, EmptyList)) or EmptyList when no lawful shared
    generalization exists. No repair, no guessing.
    """

    def __init__(self, example_a, example_b, word_entries):
        self.word_entries = word_entries
        self.cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        self.result = self._induce(example_a, example_b)
        super().__init__(
            inputs=M.Pair(
                example_a,
                M.Pair(example_b, M.Pair(word_entries, M.EmptyList)),
            ),
            results=self.result,
        )

    def _induce(self, example_a, example_b):
        surface_a = CorrespondenceExampleSurface(example_a)()
        surface_b = CorrespondenceExampleSurface(example_b)()
        chain_a = M.Head(M.Tail(surface_a)())()
        chain_b = M.Head(M.Tail(surface_b)())()

        reversed_general = M.EmptyList
        diffs = M.EmptyList
        var_index_text = "0"
        scan_text = "0"
        while M.IdentityCompare(chain_a, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, self.cap_text)() is M.truth_value:
                return M.EmptyList
            scan_text = GMPSuccText(scan_text)()
            if M.IdentityCompare(chain_b, M.EmptyList)() is M.truth_value:
                return M.EmptyList
            word_a = M.Head(chain_a)()
            word_b = M.Head(chain_b)()
            if M.Compare(word_a, word_b)() is M.truth_value:
                reversed_general = M.Pair(word_a, reversed_general)
            else:
                variable = M.EmptyList
                check_text = "0"
                remaining_diffs = diffs
                while M.IdentityCompare(
                    remaining_diffs,
                    M.EmptyList,
                )() is M.false_value:
                    if GMPEqualText(check_text, self.cap_text)() is M.truth_value:
                        remaining_diffs = M.EmptyList
                    else:
                        check_text = GMPSuccText(check_text)()
                        diff = M.Head(remaining_diffs)()
                        same_a = M.Compare(M.Head(diff)(), word_a)()
                        same_b = M.Compare(M.Head(M.Tail(diff)())(), word_b)()
                        if M.AndAtom(same_a, same_b)() is M.truth_value:
                            variable = M.Head(M.Tail(M.Tail(diff)())())()
                            remaining_diffs = M.EmptyList
                        else:
                            remaining_diffs = M.Tail(remaining_diffs)()
                if M.IdentityCompare(variable, M.EmptyList)() is M.truth_value:
                    variable = M.Pair(
                        M.VarTag,
                        M.Pair(M.Char("?g" + var_index_text), M.EmptyList),
                    )
                    var_index_text = GMPSuccText(var_index_text)()
                    diffs = M.Pair(
                        M.Pair(
                            word_a,
                            M.Pair(word_b, M.Pair(variable, M.EmptyList)),
                        ),
                        diffs,
                    )
                reversed_general = M.Pair(variable, reversed_general)
            chain_a = M.Tail(chain_a)()
            chain_b = M.Tail(chain_b)()
        if M.IdentityCompare(chain_b, M.EmptyList)() is M.false_value:
            return M.EmptyList
        if M.IdentityCompare(diffs, M.EmptyList)() is M.truth_value:
            return M.EmptyList

        meaning_a = CorrespondenceExampleMeaning(example_a)()
        meaning_b = CorrespondenceExampleMeaning(example_b)()
        generalized = self._general(
            M.Head(M.Tail(meaning_a)())(),
            M.Head(M.Tail(meaning_b)())(),
            diffs,
            "0",
        )
        if M.IdentityCompare(M.Head(generalized)(), M.false_value)() is M.truth_value:
            return M.EmptyList

        general_surface = Surface(M.Reverse(reversed_general)())()
        general_meaning = Meaning(M.Tail(generalized)())()
        parse_law = CompileRuleToLaw(P.Rule(general_surface, general_meaning))()
        render_law = CompileRuleToLaw(P.Rule(general_meaning, general_surface))()
        if M.IdentityCompare(parse_law, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        if M.IdentityCompare(render_law, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        return M.Pair(parse_law, M.Pair(render_law, M.EmptyList))

    def _general(self, term_a, term_b, diffs, depth_text):
        if GMPEqualText(depth_text, self.cap_text)() is M.truth_value:
            return M.Pair(M.false_value, M.EmptyList)
        next_depth = GMPSuccText(depth_text)()
        if M.Compare(term_a, term_b)() is M.truth_value:
            return M.Pair(M.truth_value, term_a)

        check_text = "0"
        remaining_diffs = diffs
        while M.IdentityCompare(remaining_diffs, M.EmptyList)() is M.false_value:
            if GMPEqualText(check_text, self.cap_text)() is M.truth_value:
                remaining_diffs = M.EmptyList
            else:
                check_text = GMPSuccText(check_text)()
                diff = M.Head(remaining_diffs)()
                word_a = M.Head(diff)()
                word_b = M.Head(M.Tail(diff)())()
                variable = M.Head(M.Tail(M.Tail(diff)())())()
                if M.AndAtom(
                    self._names(term_a, word_a),
                    self._names(term_b, word_b),
                )() is M.truth_value:
                    return M.Pair(
                        M.truth_value,
                        Surface(M.Pair(variable, M.EmptyList))(),
                    )
                remaining_diffs = M.Tail(remaining_diffs)()

        both_pairs = M.AndAtom(M.IsPair(term_a)(), M.IsPair(term_b)())()
        if M.IdentityCompare(both_pairs, M.truth_value)() is M.truth_value:
            head_general = self._general(
                M.Head(term_a)(),
                M.Head(term_b)(),
                diffs,
                next_depth,
            )
            if M.IdentityCompare(
                M.Head(head_general)(),
                M.false_value,
            )() is M.truth_value:
                return M.Pair(M.false_value, M.EmptyList)
            tail_general = self._general(
                M.Tail(term_a)(),
                M.Tail(term_b)(),
                diffs,
                next_depth,
            )
            if M.IdentityCompare(
                M.Head(tail_general)(),
                M.false_value,
            )() is M.truth_value:
                return M.Pair(M.false_value, M.EmptyList)
            return M.Pair(
                M.truth_value,
                M.Pair(M.Tail(head_general)(), M.Tail(tail_general)()),
            )
        return M.Pair(M.false_value, M.EmptyList)

    def _names(self, meaning_part, word):
        if M.Compare(meaning_part, word)() is M.truth_value:
            return M.truth_value
        if M.Compare(
            meaning_part,
            Surface(M.Pair(word, M.EmptyList))(),
        )() is M.truth_value:
            return M.truth_value
        resolved = CorrespondenceResolveWord(
            self.word_entries,
            Surface(M.Pair(word, M.EmptyList))(),
        )()
        if M.IdentityCompare(resolved, M.EmptyList)() is M.false_value:
            if M.Compare(meaning_part, resolved)() is M.truth_value:
                return M.truth_value
        return M.false_value

    def __call__(self):
        return self.result


class ValidateCorrespondenceLaws(M.Edge):
    """Check induced parse and render laws against every recorded example.

    Accepted examples must parse, agree in evaluated value with the recorded
    meaning, and round-trip through the render law. Rejected examples must
    not match. Returns Pair(verdict, Pair(registry, EmptyList)).
    """

    def __init__(self, parse_law, render_law, examples, word_entries, registry):
        cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        verdict = M.truth_value
        scan_text = "0"
        remaining = examples
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                verdict = M.false_value
                remaining = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                example = M.Head(remaining)()
                surface = CorrespondenceExampleSurface(example)()
                evidence = CorrespondenceExampleEvidence(example)()
                parsed = CorrespondenceApply(parse_law, surface)()
                if M.Compare(evidence, M.Char("rejected"))() is M.truth_value:
                    if M.IdentityCompare(parsed, M.EmptyList)() is M.false_value:
                        verdict = M.false_value
                        remaining = M.EmptyList
                else:
                    if M.IdentityCompare(parsed, M.EmptyList)() is M.truth_value:
                        verdict = M.false_value
                        remaining = M.EmptyList
                    else:
                        parsed_value = MeaningEvaluate(
                            parsed,
                            word_entries,
                            registry,
                        )()
                        left_value = M.Head(parsed_value)()
                        registry = M.Head(M.Tail(parsed_value)())()
                        recorded_value = MeaningEvaluate(
                            CorrespondenceExampleMeaning(example)(),
                            word_entries,
                            registry,
                        )()
                        right_value = M.Head(recorded_value)()
                        registry = M.Head(M.Tail(recorded_value)())()
                        rendered = CorrespondenceApply(render_law, parsed)()
                        if M.IdentityCompare(
                            left_value,
                            M.EmptyList,
                        )() is M.truth_value:
                            verdict = M.false_value
                            remaining = M.EmptyList
                        elif M.IdentityCompare(
                            right_value,
                            M.EmptyList,
                        )() is M.truth_value:
                            verdict = M.false_value
                            remaining = M.EmptyList
                        elif M.NatEq(
                            left_value,
                            right_value,
                            registry,
                        )() is M.false_value:
                            verdict = M.false_value
                            remaining = M.EmptyList
                        elif M.IdentityCompare(
                            rendered,
                            M.EmptyList,
                        )() is M.truth_value:
                            verdict = M.false_value
                            remaining = M.EmptyList
                        elif M.Compare(rendered, surface)() is M.false_value:
                            verdict = M.false_value
                            remaining = M.EmptyList
                if M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
                    remaining = M.Tail(remaining)()
        self.result = M.Pair(verdict, M.Pair(registry, M.EmptyList))
        super().__init__(
            inputs=M.Pair(
                parse_law,
                M.Pair(
                    render_law,
                    M.Pair(
                        examples,
                        M.Pair(word_entries, M.Pair(registry, M.EmptyList)),
                    ),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class GenerateCorrespondenceProposals(M.Edge):
    """Induce, validate, and submit correspondence laws as pending proposals.

    Accepted example pairs are anti-unified within bounded scans; validated
    candidates are submitted with the render law and source examples as
    JustifiedBy evidence. Nothing is approved or activated here.
    """

    def __init__(self, proposal_store, examples, word_entries, registry):
        cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        proposal_cap_text = M.GMPRepText(CORRESPONDENCE_INDUCTION_CAP)()
        current_store = proposal_store
        submitted_text = "0"
        seen_candidates = M.EmptyList

        outer_text = "0"
        remaining_a = examples
        while M.IdentityCompare(remaining_a, M.EmptyList)() is M.false_value:
            if GMPEqualText(outer_text, cap_text)() is M.truth_value:
                remaining_a = M.EmptyList
            elif GMPEqualText(submitted_text, proposal_cap_text)() is M.truth_value:
                remaining_a = M.EmptyList
            else:
                outer_text = GMPSuccText(outer_text)()
                example_a = M.Head(remaining_a)()
                inner_text = "0"
                remaining_b = M.Tail(remaining_a)()
                while M.IdentityCompare(remaining_b, M.EmptyList)() is M.false_value:
                    if GMPEqualText(inner_text, cap_text)() is M.truth_value:
                        remaining_b = M.EmptyList
                    elif GMPEqualText(
                        submitted_text,
                        proposal_cap_text,
                    )() is M.truth_value:
                        remaining_b = M.EmptyList
                    else:
                        inner_text = GMPSuccText(inner_text)()
                        example_b = M.Head(remaining_b)()
                        rejected_a = M.Compare(
                            CorrespondenceExampleEvidence(example_a)(),
                            M.Char("rejected"),
                        )()
                        rejected_b = M.Compare(
                            CorrespondenceExampleEvidence(example_b)(),
                            M.Char("rejected"),
                        )()
                        if M.OrAtom(rejected_a, rejected_b)() is M.false_value:
                            induced = AntiUnifyCorrespondence(
                                example_a,
                                example_b,
                                word_entries,
                            )()
                            if M.IdentityCompare(
                                induced,
                                M.EmptyList,
                            )() is M.false_value:
                                parse_law = M.Head(induced)()
                                render_law = M.Head(M.Tail(induced)())()
                                duplicate = M.false_value
                                check_text = "0"
                                checking = seen_candidates
                                while M.IdentityCompare(
                                    checking,
                                    M.EmptyList,
                                )() is M.false_value:
                                    if GMPEqualText(
                                        check_text,
                                        cap_text,
                                    )() is M.truth_value:
                                        checking = M.EmptyList
                                    else:
                                        check_text = GMPSuccText(check_text)()
                                        if M.Compare(
                                            M.Head(checking)(),
                                            parse_law,
                                        )() is M.truth_value:
                                            duplicate = M.truth_value
                                            checking = M.EmptyList
                                        else:
                                            checking = M.Tail(checking)()
                                if M.IdentityCompare(
                                    duplicate,
                                    M.false_value,
                                )() is M.truth_value:
                                    seen_candidates = M.Pair(
                                        parse_law,
                                        seen_candidates,
                                    )
                                    validated = ValidateCorrespondenceLaws(
                                        parse_law,
                                        render_law,
                                        examples,
                                        word_entries,
                                        registry,
                                    )()
                                    registry = M.Head(M.Tail(validated)())()
                                    if M.IdentityCompare(
                                        M.Head(validated)(),
                                        M.truth_value,
                                    )() is M.truth_value:
                                        proposal = Proposal(
                                            parse_law,
                                            M.Char("induced-correspondence"),
                                        )()
                                        evidence = M.Pair(
                                            render_law,
                                            M.Pair(
                                                example_a,
                                                M.Pair(example_b, M.EmptyList),
                                            ),
                                        )
                                        current_store = ProposalStoreSubmit(
                                            current_store,
                                            proposal,
                                        )()
                                        current_store = ProposalStoreAttach(
                                            current_store,
                                            proposal,
                                            JustifiedBy(proposal, evidence)(),
                                        )()
                                        submitted_text = GMPSuccText(
                                            submitted_text,
                                        )()
                        remaining_b = M.Tail(remaining_b)()
                remaining_a = M.Tail(remaining_a)()

        self.result = M.Pair(
            current_store,
            M.Pair(
                MineNatFromGMPRep(M.GMPRep(submitted_text))(),
                M.Pair(registry, M.EmptyList),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                proposal_store,
                M.Pair(
                    examples,
                    M.Pair(word_entries, M.Pair(registry, M.EmptyList)),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class InstalledCorrespondenceLaws(M.Edge):
    """Installed laws whose left pattern is a Surface term."""

    def __init__(self, graph_version):
        cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        reversed_laws = M.EmptyList
        scan_text = "0"
        remaining = InstalledLaws(graph_version)()
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                remaining = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                law = M.Head(remaining)()
                left_nodes = GraphNodes(LawLeft(law)())()
                if M.IdentityCompare(left_nodes, M.EmptyList)() is M.false_value:
                    pattern = M.Head(left_nodes)()
                    if M.IsPair(pattern)() is M.truth_value:
                        if M.TermEqual(
                            M.Head(pattern)(),
                            Lmod.SurfaceLabel,
                        )() is M.truth_value:
                            reversed_laws = M.Pair(law, reversed_laws)
                remaining = M.Tail(remaining)()
        self.result = M.Reverse(reversed_laws)()
        super().__init__(inputs=M.Pair(graph_version, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class VocabularyWithTemplates(M.Edge):
    """Extend a vocabulary's template chain with additional compiled laws."""

    def __init__(self, vocabulary, extra_laws):
        templates = M.Head(vocabulary)()
        reversed_templates = M.Reverse(templates)()
        remaining = extra_laws
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            reversed_templates = M.Pair(M.Head(remaining)(), reversed_templates)
            remaining = M.Tail(remaining)()
        self.result = M.Pair(
            M.Reverse(reversed_templates)(),
            M.Tail(vocabulary)(),
        )
        super().__init__(
            inputs=M.Pair(vocabulary, M.Pair(extra_laws, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class GeneratePreferenceProposal(M.Edge):
    """Submit the ledger-derived law ordering as one insertion-law proposal."""

    def __init__(self, proposal_store, ledger, graph_version):
        cap_text = M.GMPRepText(LAW_ORDERING_SCAN_CAP)()
        current_store = proposal_store
        submitted_text = "0"
        installed = InstalledLaws(graph_version)()
        if M.IdentityCompare(installed, M.EmptyList)() is M.false_value:
            ordering = LawOrderingFromLedger(ledger, installed)()
            preference = LawPreference(ordering)()
            empty_graph = GraphVersion(M.EmptyList, M.EmptyList, M.EmptyList)()
            preference_graph = GraphVersion(
                M.Pair(preference, M.EmptyList),
                M.EmptyList,
                M.EmptyList,
            )()
            law = Law(
                empty_graph,
                empty_graph,
                preference_graph,
                Map(empty_graph, empty_graph, M.EmptyList)(),
                Map(empty_graph, preference_graph, M.EmptyList)(),
                M.EmptyList,
            )()
            proposal = Proposal(law, M.Char("ledger-preference"))()

            groups = FiringLedgerByLaw(ledger.records)()
            reversed_evidence = M.EmptyList
            scan_text = "0"
            remaining_laws = installed
            while M.IdentityCompare(remaining_laws, M.EmptyList)() is M.false_value:
                if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                    remaining_laws = M.EmptyList
                else:
                    scan_text = GMPSuccText(scan_text)()
                    scored_law = M.Head(remaining_laws)()
                    score = LawLedgerScore(scored_law, groups)()
                    reversed_evidence = M.Pair(
                        M.Pair(
                            scored_law,
                            M.Pair(
                                MineNatFromGMPRep(
                                    M.GMPRep(M.Head(score)()),
                                )(),
                                M.EmptyList,
                            ),
                        ),
                        reversed_evidence,
                    )
                    remaining_laws = M.Tail(remaining_laws)()
            evidence = M.Reverse(reversed_evidence)()

            current_store = ProposalStoreSubmit(current_store, proposal)()
            current_store = ProposalStoreAttach(
                current_store,
                proposal,
                JustifiedBy(proposal, evidence)(),
            )()
            submitted_text = "1"

        self.result = M.Pair(
            current_store,
            M.Pair(
                MineNatFromGMPRep(M.GMPRep(submitted_text))(),
                M.EmptyList,
            ),
        )
        super().__init__(
            inputs=M.Pair(
                proposal_store,
                M.Pair(ledger, M.Pair(graph_version, M.EmptyList)),
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
            checked = CheckObligation(
                committed,
                obligation,
                unchecked,
                ledger,
            )()
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
