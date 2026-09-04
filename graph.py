from __future__ import annotations

import io
import multiprocessing

from . import context as Ctx
from . import machine as M
from . import proof as P
from . import schemata as S
from . import labels as Lmod
from . import trees as Tmod
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
        self._search_installed_heuristic_version = M.EmptyList
        self._search_installed_heuristic_resolved = M.EmptyList
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


class Retired(M.Edge):
    """Step 33: an append-only invariant mark demoting one installed Law."""

    def __init__(self, law):
        self.result = M.Pair(Lmod.RetiredLabel, M.Pair(law, M.EmptyList))
        super().__init__(inputs=M.Pair(law, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class IsRetired(M.Edge):
    def __init__(self, term):
        self.result = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if M.TermEqual(M.Head(term)(), Lmod.RetiredLabel)() is M.truth_value:
                self.result = M.truth_value
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RetiredLaw(M.Edge):
    def __init__(self, retired):
        self.result = M.Head(M.Tail(retired)())()
        super().__init__(inputs=M.Pair(retired, M.EmptyList), results=self.result)

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


class ApprovedAuthority(M.Edge):
    def __init__(self, approved):
        self.result = M.Head(M.Tail(M.Tail(approved)())())()
        super().__init__(inputs=M.Pair(approved, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class Countersigned(M.Edge):
    """Step 37: a second, independent authority endorsing a policy change."""

    def __init__(self, proposal, authority):
        self.result = M.Pair(
            Lmod.CountersignedLabel,
            M.Pair(proposal, M.Pair(authority, M.EmptyList)),
        )
        super().__init__(
            inputs=M.Pair(proposal, M.Pair(authority, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class IsCountersigned(M.Edge):
    def __init__(self, term):
        self.result = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if M.TermEqual(
                M.Head(term)(),
                Lmod.CountersignedLabel,
            )() is M.truth_value:
                self.result = M.truth_value
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CountersignedProposal(M.Edge):
    def __init__(self, countersigned):
        self.result = M.Head(M.Tail(countersigned)())()
        super().__init__(
            inputs=M.Pair(countersigned, M.EmptyList),
            results=self.result,
        )

    def __call__(self):
        return self.result


class CountersignedAuthority(M.Edge):
    def __init__(self, countersigned):
        self.result = M.Head(M.Tail(M.Tail(countersigned)())())()
        super().__init__(
            inputs=M.Pair(countersigned, M.EmptyList),
            results=self.result,
        )

    def __call__(self):
        return self.result


class IsAutonomyAuthorityTerm(M.Edge):
    def __init__(self, term):
        self.result = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if M.TermEqual(
                M.Head(term)(),
                Lmod.AutonomyAuthorityLabel,
            )() is M.truth_value:
                self.result = M.truth_value
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ReasonUncountersigned(M.Edge):
    def __init__(self, proposal):
        self.result = M.Pair(
            Lmod.ReasonUncountersignedLabel,
            M.Pair(proposal, M.EmptyList),
        )
        super().__init__(inputs=M.Pair(proposal, M.EmptyList), results=self.result)

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


BOOT_STORE_CAP = M.GMPRep("100000")
BOOT_DEPTH_CAP = M.GMPRep("50000")
BOOT_PENDING_CAP = M.GMPRep("1000")
SAFETY_SCAN_CAP = M.GMPRep("200")

# Step 49: the three recognized measures, as label singletons compared by
# identity. Adding a fourth measure is a code change, deliberately: the
# floor's vocabulary is not machine-extensible.
SAFETY_MEASURE_STORE_SIZE = M.Char("store-size")
SAFETY_MEASURE_PROVENANCE_DEPTH = M.Char("provenance-depth")
SAFETY_MEASURE_PENDING_PROPOSALS = M.Char("pending-proposals")


class SafetyInvariant(M.Edge):
    """Step 49: a named bound on one recognized measure."""

    def __init__(self, name, bound, measure):
        self.result = M.Pair(
            Lmod.SafetyInvariantLabel,
            M.Pair(name, M.Pair(bound, M.Pair(measure, M.EmptyList))),
        )
        super().__init__(
            inputs=M.Pair(name, M.Pair(bound, M.Pair(measure, M.EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class IsSafetyInvariant(M.Edge):
    def __init__(self, term):
        self.result = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if M.TermEqual(
                M.Head(term)(),
                Lmod.SafetyInvariantLabel,
            )() is M.truth_value:
                self.result = M.truth_value
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SafetyInvariantName(M.Edge):
    def __init__(self, term):
        self.result = M.Head(M.Tail(term)())()
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SafetyInvariantBound(M.Edge):
    def __init__(self, term):
        self.result = M.Head(M.Tail(M.Tail(term)())())()
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SafetyInvariantMeasure(M.Edge):
    def __init__(self, term):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(term)())())())()
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ReasonSafety(M.Edge):
    """Refusal reason carrying the violated invariant and the proposal."""

    def __init__(self, invariant, proposal):
        self.result = M.Pair(
            Lmod.ReasonSafetyLabel,
            M.Pair(invariant, M.Pair(proposal, M.EmptyList)),
        )
        super().__init__(
            inputs=M.Pair(invariant, M.Pair(proposal, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class MeasureStoreSize(M.Edge):
    """Element count of one graph version: nodes plus edges."""

    def __init__(self, graph_version):
        total_text = "0"
        remaining = GraphNodes(graph_version)()
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            total_text = GMPSuccText(total_text)()
            remaining = M.Tail(remaining)()
        remaining = GraphEdges(graph_version)()
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            total_text = GMPSuccText(total_text)()
            remaining = M.Tail(remaining)()
        self.result = M.GMPRep(total_text)
        super().__init__(
            inputs=M.Pair(graph_version, M.EmptyList),
            results=self.result,
        )

    def __call__(self):
        return self.result


class MeasureProvenanceDepth(M.Edge):
    """Length of the Next chain reachable from one version."""

    def __init__(self, graph_version):
        cap_text = M.GMPRepText(SAFETY_SCAN_CAP)()
        depth_text = "0"
        current = graph_version
        walking = M.truth_value
        while M.IdentityCompare(walking, M.truth_value)() is M.truth_value:
            walking = M.false_value
            if GMPEqualText(depth_text, cap_text)() is M.false_value:
                if M.IsPair(current)() is M.truth_value:
                    if M.TermEqual(
                        M.Head(current)(),
                        Lmod.NextLabel,
                    )() is M.truth_value:
                        depth_text = GMPSuccText(depth_text)()
                        current = M.Head(M.Tail(current)())()
                        walking = M.truth_value
        self.result = M.GMPRep(depth_text)
        super().__init__(
            inputs=M.Pair(graph_version, M.EmptyList),
            results=self.result,
        )

    def __call__(self):
        return self.result


class MeasurePendingProposals(M.Edge):
    """Count of unapproved entries in a proposal store."""

    def __init__(self, proposal_store):
        total_text = "0"
        remaining = M.EmptyList
        if M.IdentityCompare(proposal_store, M.EmptyList)() is M.false_value:
            remaining = ProposalStoreEntries(proposal_store)()
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            entry = M.Head(remaining)()
            if ProposalEntryIsApproved(entry)() is M.false_value:
                total_text = GMPSuccText(total_text)()
            remaining = M.Tail(remaining)()
        self.result = M.GMPRep(total_text)
        super().__init__(
            inputs=M.Pair(proposal_store, M.EmptyList),
            results=self.result,
        )

    def __call__(self):
        return self.result


class InstalledSafetyInvariants(M.Edge):
    """Every SafetyInvariant term in the invariant store, in store order."""

    def __init__(self, graph_version):
        cap_text = M.GMPRepText(SAFETY_SCAN_CAP)()
        scan_text = "0"
        reversed_found = M.EmptyList
        remaining = GraphVersionInvariants(graph_version)()
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                remaining = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                invariant = M.Head(remaining)()
                if IsSafetyInvariant(invariant)() is M.truth_value:
                    reversed_found = M.Pair(invariant, reversed_found)
                remaining = M.Tail(remaining)()
        self.result = Reverse(reversed_found)()
        super().__init__(
            inputs=M.Pair(graph_version, M.EmptyList),
            results=self.result,
        )

    def __call__(self):
        return self.result


class CheckSafety(M.Edge):
    """Step 49: the first violated installed invariant, or EmptyList.

    A measure exceeds its bound when bound < measured. Unrecognized
    measures are ignored rather than treated as violations: the floor
    refuses on evidence, never on confusion.
    """

    def __init__(self, graph_version, proposal_store=M.EmptyList):
        self.result = M.EmptyList
        remaining = InstalledSafetyInvariants(graph_version)()
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            invariant = M.Head(remaining)()
            measure = SafetyInvariantMeasure(invariant)()
            measured = M.EmptyList
            if M.Compare(measure, SAFETY_MEASURE_STORE_SIZE)() is M.truth_value:
                measured = MeasureStoreSize(graph_version)()
            elif M.Compare(
                measure,
                SAFETY_MEASURE_PROVENANCE_DEPTH,
            )() is M.truth_value:
                measured = MeasureProvenanceDepth(graph_version)()
            elif M.Compare(
                measure,
                SAFETY_MEASURE_PENDING_PROPOSALS,
            )() is M.truth_value:
                measured = MeasurePendingProposals(proposal_store)()
            if M.IdentityCompare(measured, M.EmptyList)() is M.false_value:
                bound_text = M.GMPRepText(SafetyInvariantBound(invariant)())()
                if GMPLessText(
                    bound_text,
                    M.GMPRepText(measured)(),
                )() is M.truth_value:
                    self.result = invariant
                    remaining = M.EmptyList
            if M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
                remaining = M.Tail(remaining)()
        super().__init__(
            inputs=M.Pair(graph_version, M.Pair(proposal_store, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class BootstrapSafetyInvariants(M.Edge):
    """The three floor invariants, installed by host code at startup.

    This is the one permitted non-proposal installation, mirroring
    IMPACT_POLICY-as-bootstrap. Changing any of these bounds afterwards is
    a policy_change proposal and goes through Step 37's gate.
    """

    def __init__(self, graph_version):
        added = M.Pair(
            SafetyInvariant(
                M.Char("boot-store-size"),
                BOOT_STORE_CAP,
                SAFETY_MEASURE_STORE_SIZE,
            )(),
            M.Pair(
                SafetyInvariant(
                    M.Char("boot-provenance-depth"),
                    BOOT_DEPTH_CAP,
                    SAFETY_MEASURE_PROVENANCE_DEPTH,
                )(),
                M.Pair(
                    SafetyInvariant(
                        M.Char("boot-pending-proposals"),
                        BOOT_PENDING_CAP,
                        SAFETY_MEASURE_PENDING_PROPOSALS,
                    )(),
                    M.EmptyList,
                ),
            ),
        )
        self.result = GraphVersion(
            GraphNodes(graph_version)(),
            GraphEdges(graph_version)(),
            ChainAddMissing(GraphVersionInvariants(graph_version)(), added)(),
        )()
        super().__init__(
            inputs=M.Pair(graph_version, M.EmptyList),
            results=self.result,
        )

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
    """Install an approved proposal and return its recorded Next splice.

    Step 37: a `policy_change` proposal that loosens any class from "human"
    to "auto" (relative to InstalledPolicy at activation time) additionally
    requires a Countersigned annotation whose authority is structurally
    distinct from the approving authority; neither authority may be an
    AutonomyAuthority term. Tightening needs only the normal approval.
    """

    def __init__(self, graph_version, proposal_entry, proposal_store=M.EmptyList):
        proposal = ProposalEntryProposal(proposal_entry)()
        # Step 49: the safety floor is evaluated before any gate logic, so a
        # violation refuses even an approved, countersigned proposal.
        safety_violation = CheckSafety(graph_version, proposal_store)()
        countersign_ok = M.truth_value
        if M.Compare(
            ClassifyProposal(proposal)(),
            M.Char("policy_change"),
        )() is M.truth_value:
            loosening = M.false_value
            effective_policy = InstalledPolicy(graph_version)()
            remaining_elements = GraphNodes(
                LawRight(ProposalLaw(proposal)())(),
            )()
            while M.IdentityCompare(
                remaining_elements,
                M.EmptyList,
            )() is M.false_value:
                element = M.Head(remaining_elements)()
                if IsPolicyEntry(element)() is M.truth_value:
                    class_name = PolicyEntryClassName(element)()
                    new_gate = PolicyEntryGate(element)()
                    current_gate = M.EmptyList
                    remaining_policy = effective_policy
                    while M.IdentityCompare(
                        remaining_policy,
                        M.EmptyList,
                    )() is M.false_value:
                        policy_entry = M.Head(remaining_policy)()
                        if M.Compare(
                            M.Head(policy_entry)(),
                            class_name,
                        )() is M.truth_value:
                            current_gate = M.Head(M.Tail(policy_entry)())()
                            remaining_policy = M.EmptyList
                        else:
                            remaining_policy = M.Tail(remaining_policy)()
                    if M.Compare(current_gate, M.Char("human"))() is M.truth_value:
                        if M.Compare(new_gate, M.Char("auto"))() is M.truth_value:
                            loosening = M.truth_value
                remaining_elements = M.Tail(remaining_elements)()

            if M.IdentityCompare(loosening, M.truth_value)() is M.truth_value:
                countersign_ok = M.false_value
                approving_authority = M.EmptyList
                remaining_annotations = ProposalEntryAnnotations(proposal_entry)()
                while M.IdentityCompare(
                    remaining_annotations,
                    M.EmptyList,
                )() is M.false_value:
                    annotation = M.Head(remaining_annotations)()
                    if IsApproved(annotation)() is M.truth_value:
                        if M.TermEqual(
                            ApprovedProposal(annotation)(),
                            proposal,
                        )() is M.truth_value:
                            approving_authority = ApprovedAuthority(annotation)()
                            remaining_annotations = M.EmptyList
                        else:
                            remaining_annotations = M.Tail(remaining_annotations)()
                    else:
                        remaining_annotations = M.Tail(remaining_annotations)()
                if M.IdentityCompare(
                    approving_authority,
                    M.EmptyList,
                )() is M.false_value:
                    if IsAutonomyAuthorityTerm(
                        approving_authority,
                    )() is M.false_value:
                        remaining_annotations = ProposalEntryAnnotations(
                            proposal_entry,
                        )()
                        while M.IdentityCompare(
                            remaining_annotations,
                            M.EmptyList,
                        )() is M.false_value:
                            annotation = M.Head(remaining_annotations)()
                            if IsCountersigned(annotation)() is M.truth_value:
                                if M.TermEqual(
                                    CountersignedProposal(annotation)(),
                                    proposal,
                                )() is M.truth_value:
                                    countersigner = CountersignedAuthority(
                                        annotation,
                                    )()
                                    if IsAutonomyAuthorityTerm(
                                        countersigner,
                                    )() is M.false_value:
                                        if M.TermEqual(
                                            countersigner,
                                            approving_authority,
                                        )() is M.false_value:
                                            countersign_ok = M.truth_value
                                            remaining_annotations = M.EmptyList
                            if M.IdentityCompare(
                                remaining_annotations,
                                M.EmptyList,
                            )() is M.false_value:
                                remaining_annotations = M.Tail(
                                    remaining_annotations,
                                )()

        if M.IdentityCompare(safety_violation, M.EmptyList)() is M.false_value:
            self.result = M.Pair(
                M.EmptyList,
                M.Pair(ReasonSafety(safety_violation, proposal)(), M.EmptyList),
            )
        elif ProposalEntryIsApproved(proposal_entry)() is M.false_value:
            self.result = M.Pair(
                M.EmptyList,
                M.Pair(ReasonUnapproved(proposal)(), M.EmptyList),
            )
        elif M.IdentityCompare(countersign_ok, M.false_value)() is M.truth_value:
            self.result = M.Pair(
                M.EmptyList,
                M.Pair(ReasonUncountersigned(proposal)(), M.EmptyList),
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
    """Pair(truth_value, host) when the mapping already sends pat, else Pair(false_value, EmptyList).

    This is the innermost question of the matcher -- asked once per
    candidate per frontier state -- and it used to answer it by walking
    two terms structurally. A pattern element is the same object every
    time it is asked about: it comes out of the pattern graph, and a
    Send was built around that very object. So identity settles nearly
    every case, and TermEqual is only reached for the elements identity
    misses, which keeps the answer exactly what it was.

    IsSend was likewise a whole Edge -- an allocation carrying a UUID --
    per item scanned, to compare one head against one label singleton.
    """

    def __init__(self, root, pat):
        self.result = self._lookup(root, pat)
        super().__init__(inputs=M.Pair(root, M.Pair(pat, M.EmptyList)), results=self.result)

    def _lookup(self, root, pat):
        remaining = root
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            item = M.Head(remaining)()
            if M.IsPair(item)() is M.truth_value:
                if M.IdentityCompare(
                    M.Head(item)(), Lmod.SendLabel,
                )() is M.truth_value:
                    sent = SendPat(item)()
                    if M.IdentityCompare(sent, pat)() is M.truth_value:
                        return M.Pair(M.truth_value, SendHost(item)())
                    if M.TermEqual(sent, pat)() is M.truth_value:
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


CONTRACT_SCAN_CAP = M.GMPRep("500")


class Contract(M.Edge):
    """Step 39: machine-checkable interface promise for a promoted handle."""

    def __init__(self, handle, ports, forbidden):
        self.result = M.Pair(
            Lmod.ContractLabel,
            M.Pair(handle, M.Pair(ports, M.Pair(forbidden, M.EmptyList))),
        )
        super().__init__(
            inputs=M.Pair(handle, M.Pair(ports, M.Pair(forbidden, M.EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class IsContract(M.Edge):
    def __init__(self, term):
        self.result = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if M.TermEqual(M.Head(term)(), Lmod.ContractLabel)() is M.truth_value:
                self.result = M.truth_value
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ContractHandle(M.Edge):
    def __init__(self, contract):
        self.result = M.Head(M.Tail(contract)())()
        super().__init__(inputs=M.Pair(contract, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ContractPorts(M.Edge):
    def __init__(self, contract):
        self.result = M.Head(M.Tail(M.Tail(contract)())())()
        super().__init__(inputs=M.Pair(contract, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ContractForbidden(M.Edge):
    def __init__(self, contract):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(contract)())())())()
        super().__init__(inputs=M.Pair(contract, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class DefaultContractForbidden(M.Edge):
    """The fixed initial alteration kinds a contract rules out."""

    def __init__(self):
        self.result = M.Pair(
            M.Char("delete-port"),
            M.Pair(M.Char("merge-port"), M.EmptyList),
        )
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class InstalledContracts(M.Edge):
    """Contract terms carried by installed laws (newest first, capped)."""

    def __init__(self, graph_version):
        cap_text = M.GMPRepText(CONTRACT_SCAN_CAP)()
        scan_text = "0"
        reversed_contracts = M.EmptyList
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
                            if IsContract(element)() is M.truth_value:
                                reversed_contracts = M.Pair(
                                    element,
                                    reversed_contracts,
                                )
                            remaining_elements = M.Tail(remaining_elements)()
                remaining = M.Tail(remaining)()
        self.result = Reverse(reversed_contracts)()
        super().__init__(
            inputs=M.Pair(graph_version, M.EmptyList),
            results=self.result,
        )

    def __call__(self):
        return self.result


class ContractViolation(M.Edge):
    """First contract whose port a deletion set touches, or EmptyList."""

    def __init__(self, contracts, deleted_nodes):
        cap_text = M.GMPRepText(CONTRACT_SCAN_CAP)()
        scan_text = "0"
        self.result = M.EmptyList
        remaining_contracts = contracts
        while M.IdentityCompare(
            remaining_contracts,
            M.EmptyList,
        )() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                remaining_contracts = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                contract = M.Head(remaining_contracts)()
                remaining_ports = ContractPorts(contract)()
                while M.IdentityCompare(
                    remaining_ports,
                    M.EmptyList,
                )() is M.false_value:
                    port = M.Head(remaining_ports)()
                    if ChainHasTerm(deleted_nodes, port)() is M.truth_value:
                        self.result = contract
                        remaining_ports = M.EmptyList
                        remaining_contracts = M.EmptyList
                    else:
                        remaining_ports = M.Tail(remaining_ports)()
                if M.IdentityCompare(
                    remaining_contracts,
                    M.EmptyList,
                )() is M.false_value:
                    remaining_contracts = M.Tail(remaining_contracts)()
        super().__init__(
            inputs=M.Pair(contracts, M.Pair(deleted_nodes, M.EmptyList)),
            results=self.result,
        )

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
    """Submit a Handle fold proposal with its machine report as justification.

    Step 39: when `contract` is provided, the fold law's R graph gains the
    Contract term as one extra node, so activation installs the contract and
    firing the fold inserts it alongside the handle.
    """

    def __init__(self, proposal_store, handle, interface_nodes, report, contract=M.EmptyList):
        compiled = CompileHandleToLaws(handle, interface_nodes)()
        fold = M.Head(compiled)()
        if M.IdentityCompare(contract, M.EmptyList)() is M.false_value:
            right = LawRight(fold)()
            contracted_right = M.Pair(
                M.HypergraphLabel,
                M.Pair(
                    M.Pair(contract, GraphNodes(right)()),
                    M.Pair(GraphEdges(right)(), M.EmptyList),
                ),
            )
            interface = LawInterface(fold)()
            old_map = LawKToRight(fold)()
            contracted_map = Map(
                interface,
                contracted_right,
                M.Head(M.Tail(M.Tail(M.Tail(old_map)())())())(),
            )()
            fold = Law(
                LawLeft(fold)(),
                interface,
                contracted_right,
                LawKToLeft(fold)(),
                contracted_map,
                LawObligations(fold)(),
            )()
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
                                M.Pair(
                                    M.Pair(
                                        M.Char("retire_law"),
                                        M.Pair(M.Char("human"), M.EmptyList),
                                    ),
                                    M.Pair(
                                        M.Pair(
                                            M.Char("tune_scheduler"),
                                            M.Pair(M.Char("human"), M.EmptyList),
                                        ),
                                        M.Pair(
                                            M.Pair(
                                                M.Char("annotate"),
                                                M.Pair(M.Char("auto"), M.EmptyList),
                                            ),
                                            M.EmptyList,
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        )
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class PolicyEntry(M.Edge):
    """Step 36: one installable policy association, class name to gate."""

    def __init__(self, class_name, gate):
        self.result = M.Pair(
            Lmod.PolicyEntryLabel,
            M.Pair(class_name, M.Pair(gate, M.EmptyList)),
        )
        super().__init__(
            inputs=M.Pair(class_name, M.Pair(gate, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class IsPolicyEntry(M.Edge):
    def __init__(self, term):
        self.result = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if M.TermEqual(M.Head(term)(), Lmod.PolicyEntryLabel)() is M.truth_value:
                self.result = M.truth_value
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class PolicyEntryClassName(M.Edge):
    def __init__(self, entry):
        self.result = M.Head(M.Tail(entry)())()
        super().__init__(inputs=M.Pair(entry, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class PolicyEntryGate(M.Edge):
    def __init__(self, entry):
        self.result = M.Head(M.Tail(M.Tail(entry)())())()
        super().__init__(inputs=M.Pair(entry, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class InstalledPolicy(M.Edge):
    """Step 36: effective policy — newest PolicyEntry per class, else bootstrap.

    Walks installed laws (newest first) collecting the newest PolicyEntry per
    class name, then appends the ImpactPolicy bootstrap defaults for classes
    without an entry. Returns the same association-chain shape as ImpactPolicy.
    """

    def __init__(self, graph_version):
        cap_text = M.GMPRepText(LAW_ORDERING_SCAN_CAP)()
        scan_text = "0"
        overrides = M.EmptyList
        if M.IdentityCompare(graph_version, M.EmptyList)() is M.false_value:
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
                                if IsPolicyEntry(element)() is M.truth_value:
                                    class_name = PolicyEntryClassName(element)()
                                    known = M.false_value
                                    remaining_overrides = overrides
                                    while M.IdentityCompare(
                                        remaining_overrides,
                                        M.EmptyList,
                                    )() is M.false_value:
                                        if M.Compare(
                                            M.Head(M.Head(remaining_overrides)())(),
                                            class_name,
                                        )() is M.truth_value:
                                            known = M.truth_value
                                            remaining_overrides = M.EmptyList
                                        else:
                                            remaining_overrides = M.Tail(
                                                remaining_overrides,
                                            )()
                                    if M.IdentityCompare(
                                        known,
                                        M.false_value,
                                    )() is M.truth_value:
                                        overrides = M.Pair(
                                            M.Pair(
                                                class_name,
                                                M.Pair(
                                                    PolicyEntryGate(element)(),
                                                    M.EmptyList,
                                                ),
                                            ),
                                            overrides,
                                        )
                                remaining_elements = M.Tail(remaining_elements)()
                    remaining = M.Tail(remaining)()
            overrides = Reverse(overrides)()

        reversed_effective = M.EmptyList
        remaining_defaults = ImpactPolicy()()
        while M.IdentityCompare(remaining_defaults, M.EmptyList)() is M.false_value:
            default_entry = M.Head(remaining_defaults)()
            class_name = M.Head(default_entry)()
            effective_entry = default_entry
            remaining_overrides = overrides
            while M.IdentityCompare(
                remaining_overrides,
                M.EmptyList,
            )() is M.false_value:
                override = M.Head(remaining_overrides)()
                if M.Compare(M.Head(override)(), class_name)() is M.truth_value:
                    effective_entry = override
                    remaining_overrides = M.EmptyList
                else:
                    remaining_overrides = M.Tail(remaining_overrides)()
            reversed_effective = M.Pair(effective_entry, reversed_effective)
            remaining_defaults = M.Tail(remaining_defaults)()
        self.result = Reverse(reversed_effective)()
        super().__init__(
            inputs=M.Pair(graph_version, M.EmptyList),
            results=self.result,
        )

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
        policy = M.Tail(policy)()
        retire_class = M.Head(M.Head(policy)())()
        policy = M.Tail(policy)()
        scheduler_class = M.Head(M.Head(policy)())()
        policy = M.Tail(policy)()
        annotate_class = M.Head(M.Head(policy)())()

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
        right_contains_retired = M.false_value
        right_contains_heuristic = M.false_value
        right_contains_policy_entry = M.false_value
        right_contains_robustness = M.false_value
        right_contains_migration = M.false_value
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
                if M.TermEqual(
                    M.Head(element)(),
                    Lmod.RetiredLabel,
                )() is M.truth_value:
                    right_contains_retired = M.truth_value
                if IsHeuristicTerm(element)() is M.truth_value:
                    right_contains_heuristic = M.truth_value
                if IsPolicyEntry(element)() is M.truth_value:
                    right_contains_policy_entry = M.truth_value
                if IsMigration(element)() is M.truth_value:
                    right_contains_migration = M.truth_value
                if M.TermEqual(
                    M.Head(element)(),
                    Lmod.RobustnessLabel,
                )() is M.truth_value:
                    right_contains_robustness = M.truth_value
            remaining_right = M.Tail(remaining_right)()

        if M.IdentityCompare(
            right_contains_policy_entry,
            M.truth_value,
        )() is M.truth_value:
            self.result = M.Char("policy_change")
        elif M.IdentityCompare(left_contains_law, M.truth_value)() is M.truth_value:
            self.result = meta_class
        elif M.IdentityCompare(
            right_contains_robustness,
            M.truth_value,
        )() is M.truth_value:
            self.result = annotate_class
        elif M.IdentityCompare(
            right_contains_migration,
            M.truth_value,
        )() is M.truth_value:
            self.result = install_class
        elif M.IdentityCompare(
            right_contains_retired,
            M.truth_value,
        )() is M.truth_value:
            self.result = retire_class
        elif M.IdentityCompare(
            right_contains_heuristic,
            M.truth_value,
        )() is M.truth_value:
            self.result = scheduler_class
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
AUTONOMY_BUDGET_ACTIVATE_APPROVED_KEY = M.Char("activate_approved")
AUTONOMY_BUDGET_REQUIRE_ROBUSTNESS_KEY = M.Char("require_robustness")
AUTONOMY_REPORT_SKIPPED_FRAGILE_KEY = M.Char("skipped_fragile")
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
AUTONOMY_GENERATOR_SLICE_INDEX_KEY = M.Char("slice_index")
AUTONOMY_GENERATOR_SLICE_COUNT_KEY = M.Char("slice_count")
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
        activate_approved = M.false_value
        require_robustness = M.EmptyList
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
            elif M.Compare(
                key,
                AUTONOMY_BUDGET_ACTIVATE_APPROVED_KEY,
            )() is M.truth_value:
                activate_approved = value
            elif M.Compare(
                key,
                AUTONOMY_BUDGET_REQUIRE_ROBUSTNESS_KEY,
            )() is M.truth_value:
                require_robustness = value
            remaining_budget = M.Tail(remaining_budget)()

        generate_handles = M.false_value
        generate_compositions = M.false_value
        generator_versions = M.EmptyList
        generator_min_count = M.one
        generator_slice_index = M.EmptyList
        generator_slice_count = M.EmptyList
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
            elif M.Compare(
                key,
                AUTONOMY_GENERATOR_SLICE_INDEX_KEY,
            )() is M.truth_value:
                generator_slice_index = value
            elif M.Compare(
                key,
                AUTONOMY_GENERATOR_SLICE_COUNT_KEY,
            )() is M.truth_value:
                generator_slice_count = value
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
                generator_slice_index,
                generator_slice_count,
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
        reversed_skipped_fragile = M.EmptyList
        remaining_entries = ProposalStoreEntries(current_store)()
        policy = InstalledPolicy(current_version)()

        while M.IdentityCompare(remaining_entries, M.EmptyList)() is M.false_value:
            entry = M.Head(remaining_entries)()
            proposal = ProposalEntryProposal(entry)()
            pending = M.truth_value
            has_approved = M.false_value
            has_rejected = M.false_value
            has_activation_mark = M.false_value
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
                        has_approved = M.truth_value
                    elif M.TermEqual(
                        annotation_label,
                        Lmod.RejectedLabel,
                    )() is M.truth_value:
                        pending = M.false_value
                        has_rejected = M.truth_value
                    elif M.TermEqual(
                        annotation_label,
                        Lmod.ActivationLabel,
                    )() is M.truth_value:
                        has_activation_mark = M.truth_value
                remaining_annotations = M.Tail(remaining_annotations)()

            if M.IdentityCompare(pending, M.truth_value)() is M.truth_value:
                impact = ClassifyProposal(proposal)()
                disposition = M.EmptyList
                if M.Compare(impact, M.Char("policy_change"))() is M.truth_value:
                    disposition = M.Char("human")
                remaining_policy = policy
                while M.IdentityCompare(
                    remaining_policy,
                    M.EmptyList,
                )() is M.false_value:
                    policy_entry = M.Head(remaining_policy)()
                    if M.IdentityCompare(
                        disposition,
                        M.EmptyList,
                    )() is M.false_value:
                        remaining_policy = M.EmptyList
                    elif M.Compare(
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
                    fragile = M.false_value
                    if M.IdentityCompare(
                        require_robustness,
                        M.EmptyList,
                    )() is M.false_value:
                        robustness_term = InstalledRobustness(
                            current_version,
                            ProposalLaw(proposal)(),
                        )()
                        if M.IdentityCompare(
                            robustness_term,
                            M.EmptyList,
                        )() is M.truth_value:
                            fragile = M.truth_value
                        elif M.NatLess(
                            RobustnessPassed(robustness_term)(),
                            require_robustness,
                            ledger.registry,
                        )() is M.truth_value:
                            fragile = M.truth_value
                    if M.IdentityCompare(fragile, M.truth_value)() is M.truth_value:
                        reversed_skipped_fragile = M.Pair(
                            proposal,
                            reversed_skipped_fragile,
                        )
                    elif M.NatLess(
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
            elif M.IdentityCompare(
                activate_approved,
                M.truth_value,
            )() is M.truth_value:
                if M.IdentityCompare(has_approved, M.truth_value)() is M.truth_value:
                    if M.IdentityCompare(
                        has_rejected,
                        M.false_value,
                    )() is M.truth_value:
                        if M.IdentityCompare(
                            has_activation_mark,
                            M.false_value,
                        )() is M.truth_value:
                            fragile = M.false_value
                            if M.IdentityCompare(
                                require_robustness,
                                M.EmptyList,
                            )() is M.false_value:
                                robustness_term = InstalledRobustness(
                                    current_version,
                                    ProposalLaw(proposal)(),
                                )()
                                if M.IdentityCompare(
                                    robustness_term,
                                    M.EmptyList,
                                )() is M.truth_value:
                                    fragile = M.truth_value
                                elif M.NatLess(
                                    RobustnessPassed(robustness_term)(),
                                    require_robustness,
                                    ledger.registry,
                                )() is M.truth_value:
                                    fragile = M.truth_value
                            if M.IdentityCompare(
                                fragile,
                                M.truth_value,
                            )() is M.truth_value:
                                reversed_skipped_fragile = M.Pair(
                                    proposal,
                                    reversed_skipped_fragile,
                                )
                            elif M.NatLess(
                                activation_count,
                                max_activations,
                                ledger.registry,
                            )() is M.truth_value:
                                activated = ActivateProposal(
                                    current_version,
                                    entry,
                                )()
                                active_version = M.Head(activated)()
                                if M.IdentityCompare(
                                    active_version,
                                    M.EmptyList,
                                )() is M.false_value:
                                    current_version = active_version
                                    current_store = ProposalStoreAttach(
                                        current_store,
                                        proposal,
                                        Activation(proposal)(),
                                    )()
                                    reversed_activated = M.Pair(
                                        proposal,
                                        reversed_activated,
                                    )
                                    next_activation = M.Succ(
                                        activation_count,
                                        ledger.registry,
                                    )()
                                    activation_count = M.Head(next_activation)()
                                    ledger.registry = M.Head(
                                        M.Tail(next_activation)(),
                                    )()
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

        tail_report = generation_report
        if M.IdentityCompare(
            require_robustness,
            M.EmptyList,
        )() is M.false_value:
            tail_report = M.Reverse(
                M.Pair(
                    M.Pair(
                        AUTONOMY_REPORT_SKIPPED_FRAGILE_KEY,
                        M.Pair(
                            M.Reverse(reversed_skipped_fragile)(),
                            M.EmptyList,
                        ),
                    ),
                    M.Reverse(generation_report)(),
                )
            )()
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
                        tail_report,
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


class EncodePremisesAsGraph(M.Edge):
    """One graph holding every premise of a multi-premise rule.

    EncodeTermAsGraph turns a single term into Hypergraph(subterms, edges).
    A conjunction of premises is the union of those: every premise's
    subterms are nodes of the one L-side, every premise's applications are
    its edges, and a variable occurring in two premises is one node in the
    union because subterm occurrences are compared structurally. That
    sharing is what makes the conjunction mean "the same shape" rather
    than "some shape each" -- Polygon(?s) and Edges(?s, three) constrain
    one ?s precisely because ?s appears once in the merged node store.
    """

    def __init__(self, premises):
        nodes = M.EmptyList
        edges = M.EmptyList
        remaining = premises
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            encoded = EncodeTermAsGraph(M.Head(remaining)())()
            nodes = ChainAddMissing(nodes, GraphNodes(encoded)())()
            edges = ChainAddMissing(edges, GraphEdges(encoded)())()
            remaining = M.Tail(remaining)()
        self.result = M.Pair(
            M.HypergraphLabel,
            M.Pair(nodes, M.Pair(edges, M.EmptyList)),
        )
        super().__init__(
            inputs=M.Pair(premises, M.EmptyList),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SharedSubtermsAcross(M.Edge):
    """Subterms shared between a premise chain and one replacement term.

    The interface K of a multi-premise law: what the premises and the
    conclusion have in common, which is what must be preserved when the
    law fires. Collected in premise order, duplicates dropped, so the K
    of a single-premise rule is exactly what SharedSubterms already gives.
    """

    def __init__(self, premises, replacement):
        right_subterms = TermSubterms(replacement)()
        reversed_shared = M.EmptyList
        remaining = premises
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            candidates = TermSubterms(M.Head(remaining)())()
            while M.IdentityCompare(
                candidates, M.EmptyList,
            )() is M.false_value:
                candidate = M.Head(candidates)()
                if ChainHasTerm(right_subterms, candidate)() is M.truth_value:
                    if ChainHasTerm(
                        reversed_shared, candidate,
                    )() is M.false_value:
                        reversed_shared = M.Pair(candidate, reversed_shared)
                candidates = M.Tail(candidates)()
            remaining = M.Tail(remaining)()
        self.result = M.Reverse(reversed_shared)()
        super().__init__(
            inputs=M.Pair(premises, M.Pair(replacement, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class CompileMultiRuleToLaw(M.Edge):
    """A multi-premise rule becomes a Law whose L-side is a conjunction.

    CompileRuleToLaw refuses anything with more than one premise, because
    its L is EncodeTermAsGraph of a single term. The refusal is not a
    principle -- the L/K/R shape has room for a conjunction, since L is
    already a node-and-edge store rather than a term. Building it needs
    three things and nothing more:

      L  the union of the premise encodings (EncodePremisesAsGraph)
      K  the subterms the premises share with the conclusion
      R  the conclusion's own encoding, unchanged

    The K-maps stay identity Sends into each side, exactly as the single
    premise case, because K is a subset of both stores by construction.
    """

    def __init__(self, rule):
        self.result = self._compile(rule)
        super().__init__(inputs=M.Pair(rule, M.EmptyList), results=self.result)

    def _compile(self, rule):
        premises = P.RulePremises(rule)()
        if M.IdentityCompare(premises, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        replacement = P.RuleReplacement(rule)()
        if M.IdentityCompare(replacement, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        left = EncodePremisesAsGraph(premises)()
        right = EncodeTermAsGraph(replacement)()
        shared = SharedSubtermsAcross(premises, replacement)()
        interface = M.Pair(
            M.HypergraphLabel,
            M.Pair(shared, M.Pair(M.EmptyList, M.EmptyList)),
        )
        sends = IdentitySendsFor(shared)()
        k_to_left = Map(interface, left, sends)()
        k_to_right = Map(interface, right, sends)()
        return Law(
            left, interface, right, k_to_left, k_to_right, M.EmptyList,
        )()

    def __call__(self):
        return self.result


class CompileDeductionToLaw(M.Edge):
    """A monotone rule: the premises stay, the conclusion is added.

    CompileMultiRuleToLaw sets K to the subterms the premises share with
    the conclusion, so firing deletes every premise element the
    conclusion does not mention. That is exactly right for a rewrite --
    the redex is consumed -- and exactly wrong for a deduction. A parse
    rule compiled that way eats its own daughters, and a fact derived
    once could never be used twice.

    Here K is the whole of L and R is L together with the conclusion.
    Nothing is deleted, one fact is added, and the K-maps are identity
    Sends over every element of L rather than over the shared subterms
    only. Everything else -- the ledger, the obligations, the firing
    record, the proposal lifecycle -- is the ordinary law machinery,
    because this is an ordinary Law.
    """

    def __init__(self, rule):
        self.result = self._compile(rule)
        super().__init__(inputs=M.Pair(rule, M.EmptyList), results=self.result)

    def _compile(self, rule):
        premises = P.RulePremises(rule)()
        if M.IdentityCompare(premises, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        replacement = P.RuleReplacement(rule)()
        if M.IdentityCompare(replacement, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        left = EncodePremisesAsGraph(premises)()
        conclusion = EncodeTermAsGraph(replacement)()
        right = M.Pair(
            M.HypergraphLabel,
            M.Pair(
                ChainAddMissing(GraphNodes(left)(), GraphNodes(conclusion)())(),
                M.Pair(
                    ChainAddMissing(
                        GraphEdges(left)(), GraphEdges(conclusion)(),
                    )(),
                    M.EmptyList,
                ),
            ),
        )
        interface = M.Pair(
            M.HypergraphLabel,
            M.Pair(
                GraphNodes(left)(),
                M.Pair(GraphEdges(left)(), M.EmptyList),
            ),
        )
        sends = IdentitySendsFor(GraphElements(interface)())()
        k_to_left = Map(interface, left, sends)()
        k_to_right = Map(interface, right, sends)()
        return Law(
            left, interface, right, k_to_left, k_to_right, M.EmptyList,
        )()

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


class RetireLaw(M.Edge):
    """Step 33: append a Retired mark; nodes, edges, and history untouched."""

    def __init__(self, graph_version, law):
        invariants = M.Pair(
            Retired(law)(),
            GraphVersionInvariants(graph_version)(),
        )
        self.result = GraphVersion(
            GraphNodes(graph_version)(),
            GraphEdges(graph_version)(),
            invariants,
        )()
        super().__init__(
            inputs=M.Pair(graph_version, M.Pair(law, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class UnretireLaw(M.Edge):
    """Step 33 reversal: append a fresh InstalledLaw mark restoring the law."""

    def __init__(self, graph_version, law):
        invariants = M.Pair(
            InstalledLaw(law)(),
            GraphVersionInvariants(graph_version)(),
        )
        self.result = GraphVersion(
            GraphNodes(graph_version)(),
            GraphEdges(graph_version)(),
            invariants,
        )()
        super().__init__(
            inputs=M.Pair(graph_version, M.Pair(law, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class InstalledLaws(M.Edge):
    """Active installed Laws: the newest status mark per law must be install."""

    def __init__(self, graph_version):
        reversed_laws = M.EmptyList
        seen = M.EmptyList
        remaining = GraphVersionInvariants(graph_version)()
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            invariant = M.Head(remaining)()
            law = M.EmptyList
            active = M.false_value
            if IsInstalledLaw(invariant)() is M.truth_value:
                law = InstalledLawValue(invariant)()
                active = M.truth_value
            elif IsRetired(invariant)() is M.truth_value:
                law = RetiredLaw(invariant)()
            if M.IdentityCompare(law, M.EmptyList)() is M.false_value:
                already = M.false_value
                remaining_seen = seen
                while M.IdentityCompare(
                    remaining_seen,
                    M.EmptyList,
                )() is M.false_value:
                    if M.TermEqual(M.Head(remaining_seen)(), law)() is M.truth_value:
                        already = M.truth_value
                        remaining_seen = M.EmptyList
                    else:
                        remaining_seen = M.Tail(remaining_seen)()
                if M.IdentityCompare(already, M.false_value)() is M.truth_value:
                    seen = M.Pair(law, seen)
                    if M.IdentityCompare(active, M.truth_value)() is M.truth_value:
                        reversed_laws = M.Pair(law, reversed_laws)
            remaining = M.Tail(remaining)()
        self.result = Reverse(reversed_laws)()
        super().__init__(inputs=M.Pair(graph_version, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class AllLawsWithStatus(M.Edge):
    """Every law ever installed paired with its current status Char."""

    def __init__(self, graph_version):
        reversed_entries = M.EmptyList
        seen = M.EmptyList
        remaining = GraphVersionInvariants(graph_version)()
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            invariant = M.Head(remaining)()
            law = M.EmptyList
            status = M.Char("retired")
            if IsInstalledLaw(invariant)() is M.truth_value:
                law = InstalledLawValue(invariant)()
                status = M.Char("active")
            elif IsRetired(invariant)() is M.truth_value:
                law = RetiredLaw(invariant)()
            if M.IdentityCompare(law, M.EmptyList)() is M.false_value:
                already = M.false_value
                remaining_seen = seen
                while M.IdentityCompare(
                    remaining_seen,
                    M.EmptyList,
                )() is M.false_value:
                    if M.TermEqual(M.Head(remaining_seen)(), law)() is M.truth_value:
                        already = M.truth_value
                        remaining_seen = M.EmptyList
                    else:
                        remaining_seen = M.Tail(remaining_seen)()
                if M.IdentityCompare(already, M.false_value)() is M.truth_value:
                    seen = M.Pair(law, seen)
                    reversed_entries = M.Pair(
                        M.Pair(law, M.Pair(status, M.EmptyList)),
                        reversed_entries,
                    )
            remaining = M.Tail(remaining)()
        self.result = Reverse(reversed_entries)()
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
        contracts = InstalledContracts(graph_version)()
        contract_probe = M.EmptyList
        if M.IdentityCompare(contracts, M.EmptyList)() is M.false_value:
            contract_probe = MapExtendOneStep(M.EmptyList, M.EmptyList, M.EmptyList)
        laws = InstalledLaws(graph_version)()
        # Step 47 ordering resolution, highest precedence first:
        # explicit argument, then SchedulePolicy-derived, then LawPreference,
        # then installed-store order.
        if M.IdentityCompare(ordering, M.EmptyList)() is M.truth_value:
            ordering = ScheduleOrdering(graph_version, ledger)()
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
                        violation = M.EmptyList
                        if M.IdentityCompare(
                            contracts,
                            M.EmptyList,
                        )() is M.false_value:
                            root = M.Head(
                                M.Tail(M.Tail(M.Tail(mapping)())())(),
                            )()
                            kept_left = InterfacePreimages(
                                LawInterface(active_law)(),
                                LawKToLeft(active_law)(),
                            )()
                            deleted_nodes = MappedImages(
                                root,
                                contract_probe._normalize_store(
                                    GraphNodes(LawLeft(active_law)())(),
                                ),
                                kept_left,
                            )()
                            violation = ContractViolation(
                                contracts,
                                deleted_nodes,
                            )()
                        if M.IdentityCompare(
                            violation,
                            M.EmptyList,
                        )() is M.false_value:
                            reason = M.Pair(
                                Lmod.ReasonContractLabel,
                                M.Pair(violation, M.EmptyList),
                            )
                            if M.IdentityCompare(
                                ledger,
                                M.EmptyList,
                            )() is M.false_value:
                                ledger.record_miss(law, reason)
                            self.result = M.Pair(
                                M.EmptyList,
                                M.Pair(
                                    M.Pair(
                                        Miss(active_law, reason)(),
                                        M.EmptyList,
                                    ),
                                    M.EmptyList,
                                ),
                            )
                            remaining = M.Tail(remaining)()
                        else:
                            fired = FireLaw(
                                graph_version,
                                active_law,
                                mapping,
                                dangling_mode,
                                ledger,
                            )()
                            if M.IdentityCompare(
                                M.Head(fired)(),
                                M.EmptyList,
                            )() is M.false_value:
                                self.result = fired
                                remaining = M.EmptyList
                            else:
                                if M.IdentityCompare(
                                    ledger,
                                    M.EmptyList,
                                )() is M.false_value:
                                    ledger.record_miss(law, M.Char("refused"))
                                self.result = fired
                                remaining = M.Tail(remaining)()
                    else:
                        if M.IdentityCompare(ledger, M.EmptyList)() is M.false_value:
                            ledger.record_miss(law, M.Char("no-match"))
                        remaining = M.Tail(remaining)()
                else:
                    if M.IdentityCompare(ledger, M.EmptyList)() is M.false_value:
                        ledger.record_miss(law, M.Char("no-bindings"))
                    remaining = M.Tail(remaining)()
            else:
                if M.IdentityCompare(ledger, M.EmptyList)() is M.false_value:
                    ledger.record_miss(law, M.Char("no-match"))
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


LAW_SATURATION_PASS_CAP = M.GMPRep("50")
LAW_MATCH_CAP = M.GMPRep("2000")


class CompletedMatches(M.Edge):
    """Every completed match of a pattern graph in a host version.

    FirstCompletedMatch stops at the first, which is what a rewrite
    wants: fire it, and the next call sees a changed graph. A deduction
    wants all of them, because every match is a fact waiting to be
    derived and none of them invalidates the others. Same frontier, same
    MapExtensionAlternatives, no early return.
    """

    def __init__(self, pattern, host, cap_text):
        pending = GraphElements(pattern)()
        cursor = SearchMatchCursor(M.EmptyList, pattern, host, pending)()
        start = SearchState(M.EmptyList, M.EmptyList, M.EmptyList, M.one, cursor)()
        reversed_matches = M.EmptyList
        scan_text = "0"
        frontier = M.Pair(start, M.EmptyList)
        while M.IdentityCompare(frontier, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                frontier = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                state = M.Head(frontier)()
                frontier = M.Tail(frontier)()
                cursor = SearchStateCursor(state)()
                if SearchMatchCursorComplete(cursor)() is M.truth_value:
                    mapping = Map(pattern, host, SearchMatchCursorRoot(cursor)())()
                    if MapSendsEveryElement(mapping, pattern)() is M.truth_value:
                        reversed_matches = M.Pair(mapping, reversed_matches)
                else:
                    pending = SearchMatchCursorPending(cursor)()
                    pat = M.Head(pending)()
                    rest = M.Tail(pending)()
                    mapping = Map(pattern, host, SearchMatchCursorRoot(cursor)())()
                    alternatives = MapExtensionAlternatives(mapping, pat, host)()
                    while M.IdentityCompare(
                        alternatives, M.EmptyList,
                    )() is M.false_value:
                        alternative = M.Head(alternatives)()
                        root = M.Head(
                            M.Tail(M.Tail(M.Tail(alternative)())())(),
                        )()
                        found = MappedHostForPat(root, pat)()
                        if M.IdentityCompare(
                            M.Head(found)(), M.truth_value,
                        )() is M.truth_value:
                            if GraphElementCompatible(
                                pat, M.Tail(found)(),
                            )() is M.truth_value:
                                child_cursor = SearchMatchCursor(
                                    root, pattern, host, rest,
                                )()
                                frontier = M.Pair(
                                    SearchState(
                                        M.EmptyList,
                                        M.EmptyList,
                                        M.EmptyList,
                                        M.one,
                                        child_cursor,
                                    )(),
                                    frontier,
                                )
                        alternatives = M.Tail(alternatives)()
        self.result = M.Reverse(reversed_matches)()
        super().__init__(
            inputs=M.Pair(pattern, M.Pair(host, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SaturateLaws(M.Edge):
    """Fire every law at every match until nothing new is derived.

    FireAny fires the first law with a completed match and hands back a
    version; in a loop that is a rewrite engine. It never reaches a
    fixed point on monotone laws, for two reasons visible in FireLaw:
    the insertion stage appends the R elements unconditionally, so the
    same conclusion is added again on every firing, and the first match
    stays the first match, so no other law is ever reached. Saturation
    is a different discipline over the same firings -- every match of
    every law, each fired once, and a firing whose conclusion is already
    in the store is not a firing at all.

    Laws are passed in rather than read from the version. InstallLaw
    puts a law's own L, K and R elements into the node store, so a
    pattern sitting in the same version its facts live in would match
    other patterns and derive facts about them. Facts live in the
    version; laws live in the store they were installed in.

    `saturated` is truth only when a pass fired nothing before the pass
    cap ran out.
    """

    def __init__(self, version, laws, ledger, dangling_mode):
        pass_cap_text = M.GMPRepText(LAW_SATURATION_PASS_CAP)()
        match_cap_text = M.GMPRepText(LAW_MATCH_CAP)()
        scan_cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        self.saturated = M.false_value
        current = version
        pass_text = "0"
        growing = M.truth_value
        while M.IdentityCompare(growing, M.truth_value)() is M.truth_value:
            if GMPEqualText(pass_text, pass_cap_text)() is M.truth_value:
                growing = M.false_value
            else:
                pass_text = GMPSuccText(pass_text)()
                growing = M.false_value
                law_scan_text = "0"
                remaining_laws = laws
                while M.IdentityCompare(
                    remaining_laws, M.EmptyList,
                )() is M.false_value:
                    if GMPEqualText(
                        law_scan_text, scan_cap_text,
                    )() is M.truth_value:
                        remaining_laws = M.EmptyList
                    else:
                        law_scan_text = GMPSuccText(law_scan_text)()
                        law = M.Head(remaining_laws)()
                        match_scan_text = "0"
                        remaining_matches = CompletedMatches(
                            LawLeft(law)(), current, match_cap_text,
                        )()
                        while M.IdentityCompare(
                            remaining_matches, M.EmptyList,
                        )() is M.false_value:
                            if GMPEqualText(
                                match_scan_text, scan_cap_text,
                            )() is M.truth_value:
                                remaining_matches = M.EmptyList
                            else:
                                match_scan_text = GMPSuccText(match_scan_text)()
                                bindings = LawMatchBindings(
                                    law, M.Head(remaining_matches)(),
                                )()
                                active = law
                                if M.IdentityCompare(
                                    bindings, M.EmptyList,
                                )() is M.false_value:
                                    active = InstantiateLaw(law, bindings)()
                                if M.IdentityCompare(
                                    active, M.EmptyList,
                                )() is M.false_value:
                                    missing = ChainWithout(
                                        GraphNodes(LawRight(active)())(),
                                        GraphNodes(current)(),
                                    )()
                                    if M.IdentityCompare(
                                        missing, M.EmptyList,
                                    )() is M.false_value:
                                        fresh = FirstCompletedMatch(
                                            LawLeft(active)(), current,
                                        )()
                                        if M.IdentityCompare(
                                            fresh, M.EmptyList,
                                        )() is M.false_value:
                                            fired = FireLaw(
                                                current,
                                                active,
                                                fresh,
                                                dangling_mode,
                                                ledger,
                                            )()
                                            committed = M.Head(fired)()
                                            if M.IdentityCompare(
                                                committed, M.EmptyList,
                                            )() is M.false_value:
                                                current = committed
                                                growing = M.truth_value
                                remaining_matches = M.Tail(remaining_matches)()
                        remaining_laws = M.Tail(remaining_laws)()
                if M.IdentityCompare(growing, M.false_value)() is M.truth_value:
                    self.saturated = M.truth_value
        self.result = current
        super().__init__(
            inputs=M.Pair(version, M.Pair(laws, M.EmptyList)),
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
        self.misses = M.EmptyList
        self.registry = registry
        super().__init__(inputs=M.Pair(registry, M.EmptyList), results=self.records)

    def append(self, record):
        reversed_records = M.Reverse(self.records)()
        self.records = M.Reverse(M.Pair(record, reversed_records))()
        self.results = self.records
        return self.records

    def record_miss(self, law, reason):
        reversed_misses = M.Reverse(self.misses)()
        self.misses = M.Reverse(
            M.Pair(M.Pair(law, M.Pair(reason, M.EmptyList)), reversed_misses)
        )()
        return self.misses

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


class IsHeuristicTerm(M.Edge):
    """Step 34: a term whose head is one of the five search-mode labels."""

    def __init__(self, term):
        self.result = M.false_value
        if M.IsPair(term)() is M.truth_value:
            head = M.Head(term)()
            if M.TermEqual(head, Lmod.DFSLabel)() is M.truth_value:
                self.result = M.truth_value
            elif M.TermEqual(head, Lmod.BFSLabel)() is M.truth_value:
                self.result = M.truth_value
            elif M.TermEqual(head, Lmod.BeamLabel)() is M.truth_value:
                self.result = M.truth_value
            elif M.TermEqual(head, Lmod.AStarLabel)() is M.truth_value:
                self.result = M.truth_value
            elif M.TermEqual(head, Lmod.RewriteDFSLabel)() is M.truth_value:
                self.result = M.truth_value
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class InstalledHeuristic(M.Edge):
    """Newest installed Heuristic-family term, or EmptyList (mirrors InstalledPreference)."""

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
                            if IsHeuristicTerm(element)() is M.truth_value:
                                self.result = element
                                remaining_elements = M.EmptyList
                                remaining = M.EmptyList
                            else:
                                remaining_elements = M.Tail(remaining_elements)()
                if M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
                    remaining = M.Tail(remaining)()
        super().__init__(inputs=M.Pair(graph_version, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SchedulePolicy(M.Edge):
    """Step 47: the two scheduler weights as an installable labeled term."""

    def __init__(self, exploit_weight, explore_weight):
        self.result = M.Pair(
            Lmod.SchedulePolicyLabel,
            M.Pair(exploit_weight, M.Pair(explore_weight, M.EmptyList)),
        )
        super().__init__(
            inputs=M.Pair(
                exploit_weight,
                M.Pair(explore_weight, M.EmptyList),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class IsSchedulePolicy(M.Edge):
    def __init__(self, term):
        self.result = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if M.TermEqual(
                M.Head(term)(),
                Lmod.SchedulePolicyLabel,
            )() is M.truth_value:
                self.result = M.truth_value
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SchedulePolicyExploit(M.Edge):
    def __init__(self, term):
        self.result = M.Head(M.Tail(term)())()
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SchedulePolicyExplore(M.Edge):
    def __init__(self, term):
        self.result = M.Head(M.Tail(M.Tail(term)())())()
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class InstalledSchedulePolicy(M.Edge):
    """Newest installed SchedulePolicy term, or EmptyList.

    Mirrors InstalledPreference and InstalledHeuristic exactly: scan the
    invariant store, newest installation wins.
    """

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
                            if IsSchedulePolicy(element)() is M.truth_value:
                                self.result = element
                                remaining_elements = M.EmptyList
                                remaining = M.EmptyList
                            else:
                                remaining_elements = M.Tail(remaining_elements)()
                if M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
                    remaining = M.Tail(remaining)()
        super().__init__(
            inputs=M.Pair(graph_version, M.EmptyList),
            results=self.result,
        )

    def __call__(self):
        return self.result


class ScheduleOrdering(M.Edge):
    """Step 47: order installed laws by the SchedulePolicy score, descending.

    score(law) = exploit_weight * cost_savings(law)
               + explore_weight * novelty(law-left-pattern)

    The formula is host code and fixed; only the two Nat weights are
    machine-visible and machine-changeable, through a tune_scheduler
    proposal. If the machine ever needs a different formula, that is
    ladder 13 territory and goes through Step 37's countersigned gate as a
    policy change, not through a weight edit.

    Nat arithmetic throughout, via GMP count texts. Selection sort by
    descending score keeps the comparison structural and the order total:
    ties keep installed-store order, so the result stays deterministic.
    """

    def __init__(self, graph_version, ledger, policy=M.EmptyList):
        if M.IdentityCompare(policy, M.EmptyList)() is M.truth_value:
            policy = InstalledSchedulePolicy(graph_version)()
        self.result = M.EmptyList
        if M.IdentityCompare(policy, M.EmptyList)() is M.false_value:
            registry = M.AllConstructors
            if M.IdentityCompare(ledger, M.EmptyList)() is M.false_value:
                registry = ledger.registry
            exploit_text = M.GMPRepText(
                M.NatRepOf(SchedulePolicyExploit(policy)(), registry)(),
            )()
            explore_text = M.GMPRepText(
                M.NatRepOf(SchedulePolicyExplore(policy)(), registry)(),
            )()
            records = M.EmptyList
            if M.IdentityCompare(ledger, M.EmptyList)() is M.false_value:
                records = ledger.records
            cap_text = M.GMPRepText(LAW_ORDERING_SCAN_CAP)()
            scan_text = "0"
            scored = M.EmptyList
            remaining = InstalledLaws(graph_version)()
            while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
                if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                    remaining = M.EmptyList
                else:
                    scan_text = GMPSuccText(scan_text)()
                    law = M.Head(remaining)()
                    saved_text = M.GMPRepText(
                        M.NatRepOf(
                            MeasureCostSavings(records, law, registry)(),
                            registry,
                        )(),
                    )()
                    novel_text = M.GMPRepText(
                        M.NatRepOf(
                            MeasureNovelty(graph_version, LawLeft(law)())(),
                            registry,
                        )(),
                    )()
                    score_text = GMPAddText(
                        GMPMulText(exploit_text, saved_text)(),
                        GMPMulText(explore_text, novel_text)(),
                    )()
                    scored = M.Pair(
                        M.Pair(law, M.Pair(M.GMPRep(score_text), M.EmptyList)),
                        scored,
                    )
                    remaining = M.Tail(remaining)()
            scored = Reverse(scored)()
            ordered = M.EmptyList
            while M.IdentityCompare(scored, M.EmptyList)() is M.false_value:
                best = M.Head(scored)()
                best_text = M.GMPRepText(M.Head(M.Tail(best)())())()
                probe = M.Tail(scored)()
                while M.IdentityCompare(probe, M.EmptyList)() is M.false_value:
                    entry = M.Head(probe)()
                    entry_text = M.GMPRepText(M.Head(M.Tail(entry)())())()
                    if GMPLessText(best_text, entry_text)() is M.truth_value:
                        best = entry
                        best_text = entry_text
                    probe = M.Tail(probe)()
                ordered = M.Pair(M.Head(best)(), ordered)
                remainder = M.EmptyList
                probe = scored
                dropped = M.false_value
                while M.IdentityCompare(probe, M.EmptyList)() is M.false_value:
                    entry = M.Head(probe)()
                    if M.IdentityCompare(entry, best)() is M.truth_value:
                        if M.IdentityCompare(dropped, M.false_value)() is M.truth_value:
                            dropped = M.truth_value
                        else:
                            remainder = M.Pair(entry, remainder)
                    else:
                        remainder = M.Pair(entry, remainder)
                    probe = M.Tail(probe)()
                scored = Reverse(remainder)()
            self.result = Reverse(ordered)()
        super().__init__(
            inputs=M.Pair(graph_version, M.EmptyList),
            results=self.result,
        )

    def __call__(self):
        return self.result


HEURISTIC_TRIAL_FIXTURE_CAP = M.GMPRep("10")


class HeuristicTrial(M.Edge):
    """Step 35: run every fixture under both heuristics; observe costs only.

    `fixtures` is an M-list of Pair(start, Pair(goal, Pair(rules, EmptyList))).
    Returns an M-list of Pair(cost_a, Pair(cost_b, EmptyList)) in fixture
    order. Nothing is installed; both runs are purely observational.
    """

    def __init__(self, graph, heuristic_a, heuristic_b, fixtures, registry):
        from .search import api as SearchApi

        cap_text = M.GMPRepText(HEURISTIC_TRIAL_FIXTURE_CAP)()
        scan_text = "0"
        reversed_results = M.EmptyList
        remaining = fixtures
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                remaining = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                fixture = M.Head(remaining)()
                start = M.Head(fixture)()
                goal = M.Head(M.Tail(fixture)())()
                rules = M.Head(M.Tail(M.Tail(fixture)())())()
                pair_a = SearchApi.Search(
                    graph,
                    start,
                    goal,
                    rules,
                    heuristic_a,
                    registry,
                )()
                cost_a = M.Head(M.Tail(pair_a)())()
                pair_b = SearchApi.Search(
                    graph,
                    start,
                    goal,
                    rules,
                    heuristic_b,
                    registry,
                )()
                cost_b = M.Head(M.Tail(pair_b)())()
                reversed_results = M.Pair(
                    M.Pair(cost_a, M.Pair(cost_b, M.EmptyList)),
                    reversed_results,
                )
                remaining = M.Tail(remaining)()
        self.result = Reverse(reversed_results)()
        super().__init__(
            inputs=M.Pair(
                heuristic_a,
                M.Pair(heuristic_b, M.Pair(fixtures, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class GenerateHeuristicProposal(M.Edge):
    """Step 35: submit heuristic_b only under strict per-fixture dominance."""

    def __init__(self, proposal_store, trial_result, heuristic_b, registry):
        from .search.model import SearchCostValue

        cap_text = M.GMPRepText(HEURISTIC_TRIAL_FIXTURE_CAP)()
        scan_text = "0"
        dominant = M.truth_value
        if M.IdentityCompare(trial_result, M.EmptyList)() is M.truth_value:
            dominant = M.false_value
        remaining = trial_result
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                remaining = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                entry = M.Head(remaining)()
                value_a = SearchCostValue(M.Head(entry)())()
                value_b = SearchCostValue(M.Head(M.Tail(entry)())())()
                if M.NatLess(value_b, value_a, registry)() is M.false_value:
                    dominant = M.false_value
                    remaining = M.EmptyList
                else:
                    remaining = M.Tail(remaining)()

        current_store = proposal_store
        submitted_text = "0"
        if M.IdentityCompare(dominant, M.truth_value)() is M.truth_value:
            empty_graph = GraphVersion(M.EmptyList, M.EmptyList, M.EmptyList)()
            heuristic_graph = GraphVersion(
                M.Pair(heuristic_b, M.EmptyList),
                M.EmptyList,
                M.EmptyList,
            )()
            law = Law(
                empty_graph,
                empty_graph,
                heuristic_graph,
                Map(empty_graph, empty_graph, M.EmptyList)(),
                Map(empty_graph, heuristic_graph, M.EmptyList)(),
                M.EmptyList,
            )()
            proposal = Proposal(law, M.Char("heuristic-trial"))()
            current_store = ProposalStoreSubmit(current_store, proposal)()
            current_store = ProposalStoreAttach(
                current_store,
                proposal,
                JustifiedBy(proposal, trial_result)(),
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
                M.Pair(trial_result, M.Pair(heuristic_b, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


PERTURB_SCAN_CAP = M.GMPRep("200")
PERTURB_NODE_CHAR = M.Char("perturb-node")
PERTURB_EDGE_CHAR = M.Char("perturb-edge")


class PerturbVersion(M.Edge):
    """Step 40: one deterministic perturbation chosen by seed mod 3.

    `seed_atom` is a Char whose symbol is the decimal seed. The added node
    and edge embed the module singleton label atoms plus the caller's seed
    atom, so perturbing twice with the same seed atom yields structurally
    equal additions (TermEqual is identity on atoms).

    seed mod 3 == 0: add one fresh isolated node.
    seed mod 3 == 1: add one fresh edge between the two lowest-index nodes.
    seed mod 3 == 2: retire-mark the lowest-index installed law that is not
    `protected_law`. No other menu items exist; no randomness.
    """

    def __init__(self, graph_version, seed_atom, protected_law=M.EmptyList):
        remainder = seed_atom()
        while GMPLessText(remainder, "3")() is M.false_value:
            remainder = GMPSubText(remainder, "3")()
        nodes = GraphNodes(graph_version)()
        edges = GraphEdges(graph_version)()
        invariants = GraphVersionInvariants(graph_version)()
        if GMPEqualText(remainder, "0")() is M.truth_value:
            fresh = M.Pair(
                PERTURB_NODE_CHAR,
                M.Pair(seed_atom, M.EmptyList),
            )
            nodes = M.Pair(fresh, nodes)
        elif GMPEqualText(remainder, "1")() is M.truth_value:
            first = M.EmptyList
            second = M.EmptyList
            remaining = nodes
            while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
                if M.IdentityCompare(first, M.EmptyList)() is M.truth_value:
                    first = M.Head(remaining)()
                elif M.IdentityCompare(second, M.EmptyList)() is M.truth_value:
                    second = M.Head(remaining)()
                    remaining = M.EmptyList
                if M.IdentityCompare(
                    remaining,
                    M.EmptyList,
                )() is M.false_value:
                    remaining = M.Tail(remaining)()
            if M.IdentityCompare(second, M.EmptyList)() is M.false_value:
                fresh_edge = M.Pair(
                    PERTURB_EDGE_CHAR,
                    M.Pair(first, M.Pair(second, M.EmptyList)),
                )
                edges = M.Pair(fresh_edge, edges)
        else:
            victim = M.EmptyList
            remaining = Reverse(InstalledLaws(graph_version)())()
            while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
                law = M.Head(remaining)()
                if M.TermEqual(law, protected_law)() is M.false_value:
                    victim = law
                remaining = M.Tail(remaining)()
            if M.IdentityCompare(victim, M.EmptyList)() is M.false_value:
                invariants = M.Pair(Retired(victim)(), invariants)
        self.result = GraphVersion(nodes, edges, invariants)()
        super().__init__(
            inputs=M.Pair(graph_version, M.Pair(protected_law, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class RobustnessReport(M.Edge):
    """Step 40: per-seed commutation evidence for one law; observational only.

    For each fixture and seed: fire the law on the fixture, fire it on the
    perturbed fixture, then compare the perturbed result against the
    perturbation of the unperturbed result (firing commutes with the
    perturbation). Returns an M-list of
    Pair(seed_text_char, Pair(fired, Pair(commutes, EmptyList))).
    """

    def __init__(self, law, fixtures, seed_texts):
        cap_text = M.GMPRepText(PERTURB_SCAN_CAP)()
        scan_text = "0"
        reversed_rows = M.EmptyList
        remaining_fixtures = fixtures
        while M.IdentityCompare(
            remaining_fixtures,
            M.EmptyList,
        )() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                remaining_fixtures = M.EmptyList
            else:
                fixture = M.Head(remaining_fixtures)()
                remaining_seeds = seed_texts
                while M.IdentityCompare(
                    remaining_seeds,
                    M.EmptyList,
                )() is M.false_value:
                    if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                        remaining_seeds = M.EmptyList
                    else:
                        scan_text = GMPSuccText(scan_text)()
                        seed = M.Head(remaining_seeds)()
                        base_mapping = FirstCompletedMatch(
                            LawLeft(law)(),
                            fixture,
                        )()
                        base_result = M.EmptyList
                        if M.IdentityCompare(
                            base_mapping,
                            M.EmptyList,
                        )() is M.false_value:
                            base_fired = FireLaw(
                                fixture,
                                law,
                                base_mapping,
                                DanglingForbid()(),
                            )()
                            base_result = M.Head(base_fired)()
                        perturbed = PerturbVersion(fixture, seed, law)()
                        mapping = FirstCompletedMatch(
                            LawLeft(law)(),
                            perturbed,
                        )()
                        fired_flag = M.false_value
                        commutes = M.false_value
                        if M.IdentityCompare(
                            mapping,
                            M.EmptyList,
                        )() is M.false_value:
                            fired = FireLaw(
                                perturbed,
                                law,
                                mapping,
                                DanglingForbid()(),
                            )()
                            fired_version = M.Head(fired)()
                            if M.IdentityCompare(
                                fired_version,
                                M.EmptyList,
                            )() is M.false_value:
                                fired_flag = M.truth_value
                                if M.IdentityCompare(
                                    base_result,
                                    M.EmptyList,
                                )() is M.false_value:
                                    expected = PerturbVersion(
                                        base_result,
                                        seed,
                                        law,
                                    )()
                                    forward = BoundedFirstCompletedMatch(
                                        fired_version,
                                        expected,
                                    )()
                                    reverse = M.EmptyList
                                    if M.IdentityCompare(
                                        forward,
                                        M.EmptyList,
                                    )() is M.false_value:
                                        reverse = BoundedFirstCompletedMatch(
                                            expected,
                                            fired_version,
                                        )()
                                    if M.IdentityCompare(
                                        reverse,
                                        M.EmptyList,
                                    )() is M.false_value:
                                        commutes = M.truth_value
                        reversed_rows = M.Pair(
                            M.Pair(
                                seed,
                                M.Pair(
                                    fired_flag,
                                    M.Pair(commutes, M.EmptyList),
                                ),
                            ),
                            reversed_rows,
                        )
                        remaining_seeds = M.Tail(remaining_seeds)()
                remaining_fixtures = M.Tail(remaining_fixtures)()
        self.result = Reverse(reversed_rows)()
        super().__init__(
            inputs=M.Pair(law, M.Pair(fixtures, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class Robustness(M.Edge):
    """Step 40: recorded stress evidence for one law as a labeled term."""

    def __init__(self, law, passed, total):
        self.result = M.Pair(
            Lmod.RobustnessLabel,
            M.Pair(law, M.Pair(passed, M.Pair(total, M.EmptyList))),
        )
        super().__init__(
            inputs=M.Pair(law, M.Pair(passed, M.Pair(total, M.EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class IsRobustness(M.Edge):
    def __init__(self, term):
        self.result = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if M.TermEqual(M.Head(term)(), Lmod.RobustnessLabel)() is M.truth_value:
                self.result = M.truth_value
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RobustnessLaw(M.Edge):
    def __init__(self, term):
        self.result = M.Head(M.Tail(term)())()
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RobustnessPassed(M.Edge):
    def __init__(self, term):
        self.result = M.Head(M.Tail(M.Tail(term)())())()
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class InstalledRobustness(M.Edge):
    """Newest installed Robustness term for a law, or EmptyList."""

    def __init__(self, graph_version, law):
        cap_text = M.GMPRepText(PERTURB_SCAN_CAP)()
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
                    carrier = InstalledLawValue(invariant)()
                    element_scan_text = "0"
                    remaining_elements = GraphNodes(LawRight(carrier)())()
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
                            if IsRobustness(element)() is M.truth_value:
                                if M.TermEqual(
                                    RobustnessLaw(element)(),
                                    law,
                                )() is M.truth_value:
                                    self.result = element
                                    remaining_elements = M.EmptyList
                                    remaining = M.EmptyList
                            if M.IdentityCompare(
                                remaining_elements,
                                M.EmptyList,
                            )() is M.false_value:
                                remaining_elements = M.Tail(remaining_elements)()
                if M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
                    remaining = M.Tail(remaining)()
        super().__init__(
            inputs=M.Pair(graph_version, M.Pair(law, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class GenerateRobustnessAnnotation(M.Edge):
    """Step 40: submit one insertion-law proposal carrying a Robustness term."""

    def __init__(self, proposal_store, law, report):
        passed_text = "0"
        total_text = "0"
        remaining_rows = report
        while M.IdentityCompare(remaining_rows, M.EmptyList)() is M.false_value:
            row = M.Head(remaining_rows)()
            total_text = GMPSuccText(total_text)()
            fired_flag = M.Head(M.Tail(row)())()
            commutes = M.Head(M.Tail(M.Tail(row)())())()
            if M.IdentityCompare(fired_flag, M.truth_value)() is M.truth_value:
                if M.IdentityCompare(commutes, M.truth_value)() is M.truth_value:
                    passed_text = GMPSuccText(passed_text)()
            remaining_rows = M.Tail(remaining_rows)()
        robustness = Robustness(
            law,
            MineNatFromGMPRep(M.GMPRep(passed_text))(),
            MineNatFromGMPRep(M.GMPRep(total_text))(),
        )()
        empty_graph = GraphVersion(M.EmptyList, M.EmptyList, M.EmptyList)()
        robustness_graph = GraphVersion(
            M.Pair(robustness, M.EmptyList),
            M.EmptyList,
            M.EmptyList,
        )()
        annotation_law = Law(
            empty_graph,
            empty_graph,
            robustness_graph,
            Map(empty_graph, empty_graph, M.EmptyList)(),
            Map(empty_graph, robustness_graph, M.EmptyList)(),
            M.EmptyList,
        )()
        proposal = Proposal(annotation_law, M.Char("robustness-harness"))()
        current_store = ProposalStoreSubmit(proposal_store, proposal)()
        current_store = ProposalStoreAttach(
            current_store,
            proposal,
            JustifiedBy(proposal, report)(),
        )()
        self.result = M.Pair(current_store, M.Pair(robustness, M.EmptyList))
        super().__init__(
            inputs=M.Pair(
                proposal_store,
                M.Pair(law, M.Pair(report, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


METRIC_RECORD_SCAN_CAP = M.GMPRep("200")
NOVELTY_SCAN_CAP = M.GMPRep("50")


class CostSavings(M.Edge):
    """Step 46: recorded node-count savings for one law as a labeled term."""

    def __init__(self, law, saved):
        self.result = M.Pair(
            Lmod.CostSavingsLabel,
            M.Pair(law, M.Pair(saved, M.EmptyList)),
        )
        super().__init__(
            inputs=M.Pair(law, M.Pair(saved, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class IsCostSavings(M.Edge):
    def __init__(self, term):
        self.result = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if M.TermEqual(
                M.Head(term)(),
                Lmod.CostSavingsLabel,
            )() is M.truth_value:
                self.result = M.truth_value
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CostSavingsLaw(M.Edge):
    def __init__(self, term):
        self.result = M.Head(M.Tail(term)())()
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CostSavingsSaved(M.Edge):
    def __init__(self, term):
        self.result = M.Head(M.Tail(M.Tail(term)())())()
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class Reuse(M.Edge):
    """Step 46: census reuse count for one handle as a labeled term."""

    def __init__(self, handle, count):
        self.result = M.Pair(
            Lmod.ReuseLabel,
            M.Pair(handle, M.Pair(count, M.EmptyList)),
        )
        super().__init__(
            inputs=M.Pair(handle, M.Pair(count, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class IsReuse(M.Edge):
    def __init__(self, term):
        self.result = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if M.TermEqual(M.Head(term)(), Lmod.ReuseLabel)() is M.truth_value:
                self.result = M.truth_value
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ReuseHandle(M.Edge):
    def __init__(self, term):
        self.result = M.Head(M.Tail(term)())()
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ReuseCount(M.Edge):
    def __init__(self, term):
        self.result = M.Head(M.Tail(M.Tail(term)())())()
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class Novelty(M.Edge):
    """Step 46: count of installed handles a pattern does not match into."""

    def __init__(self, pattern_graph, count):
        self.result = M.Pair(
            Lmod.NoveltyLabel,
            M.Pair(pattern_graph, M.Pair(count, M.EmptyList)),
        )
        super().__init__(
            inputs=M.Pair(pattern_graph, M.Pair(count, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class IsNovelty(M.Edge):
    def __init__(self, term):
        self.result = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if M.TermEqual(M.Head(term)(), Lmod.NoveltyLabel)() is M.truth_value:
                self.result = M.truth_value
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class NoveltyPattern(M.Edge):
    def __init__(self, term):
        self.result = M.Head(M.Tail(term)())()
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class NoveltyCount(M.Edge):
    def __init__(self, term):
        self.result = M.Head(M.Tail(M.Tail(term)())())()
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class MeasureCostSavings(M.Edge):
    """Sum of node-count reductions over one law's committed records.

    Reuses the ledger records written by FireLaw: a record whose nodes_after
    is below its nodes_before saved the difference. Growth contributes
    nothing rather than a negative, keeping the measure Nat-valued.
    """

    def __init__(self, records, law, registry=M.EmptyList):
        if M.IdentityCompare(registry, M.EmptyList)() is M.truth_value:
            registry = M.AllConstructors
        cap_text = M.GMPRepText(METRIC_RECORD_SCAN_CAP)()
        scan_text = "0"
        saved_text = "0"
        remaining = records
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                remaining = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                record = M.Head(remaining)()
                if M.TermEqual(FiringRecordLaw(record)(), law)() is M.truth_value:
                    before_text = M.GMPRepText(
                        M.NatRepOf(FiringRecordNodesBefore(record)(), registry)(),
                    )()
                    after_text = M.GMPRepText(
                        M.NatRepOf(FiringRecordNodesAfter(record)(), registry)(),
                    )()
                    if GMPLessText(after_text, before_text)() is M.truth_value:
                        saved_text = GMPAddText(
                            saved_text,
                            GMPSubText(before_text, after_text)(),
                        )()
                remaining = M.Tail(remaining)()
        self.result = MineNatFromGMPRep(M.GMPRep(saved_text))()
        super().__init__(
            inputs=M.Pair(records, M.Pair(law, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class MeasureReuse(M.Edge):
    """Census count of one handle's pattern across a version history.

    Delegates to the Step-20 PatternCensus rather than re-counting, then
    sums its per-version counts into a single Nat.
    """

    def __init__(self, ledger, handle, versions):
        counts = PatternCensus(ledger, HandlePattern(handle)(), versions)()
        total_text = "0"
        remaining = counts
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            count = M.Head(remaining)()
            total_text = GMPAddText(
                total_text,
                M.GMPRepText(M.NatRepOf(count, ledger.registry)())(),
            )()
            remaining = M.Tail(remaining)()
        self.result = MineNatFromGMPRep(M.GMPRep(total_text))()
        super().__init__(
            inputs=M.Pair(handle, M.Pair(versions, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class MeasureNovelty(M.Edge):
    """Count installed handles whose pattern the candidate does not match.

    Bounded by NOVELTY_SCAN_CAP. Matching reuses FirstCompletedMatch, so a
    candidate is 'known' exactly when the ordinary matcher relates it to an
    installed handle's pattern.
    """

    def __init__(self, graph_version, pattern_graph):
        cap_text = M.GMPRepText(NOVELTY_SCAN_CAP)()
        scan_text = "0"
        unmatched_text = "0"
        remaining = GraphVersionInvariants(graph_version)()
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                remaining = M.EmptyList
            else:
                invariant = M.Head(remaining)()
                if M.IsPair(invariant)() is M.truth_value:
                    if M.TermEqual(
                        M.Head(invariant)(),
                        Lmod.HandleLabel,
                    )() is M.truth_value:
                        scan_text = GMPSuccText(scan_text)()
                        installed_pattern = HandlePattern(invariant)()
                        mapping = FirstCompletedMatch(
                            pattern_graph,
                            installed_pattern,
                        )()
                        if M.IdentityCompare(
                            mapping,
                            M.EmptyList,
                        )() is M.truth_value:
                            unmatched_text = GMPSuccText(unmatched_text)()
                remaining = M.Tail(remaining)()
        self.result = MineNatFromGMPRep(M.GMPRep(unmatched_text))()
        super().__init__(
            inputs=M.Pair(graph_version, M.Pair(pattern_graph, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


META_WINDOW_CAP = M.GMPRep("100")

# Step 48 quotation vocabulary: machine label singletons, compared by
# identity, never reason text.
META_OUTCOME_FIRED = M.Char("fired")
META_OUTCOME_MISSED = M.Char("missed")
META_DELTA_SHRANK = M.Char("shrank")
META_DELTA_GREW = M.Char("grew")
META_DELTA_FLAT = M.Char("flat")
META_CLASS_UNKNOWN = M.Char("unknown-class")


class QuoteLedgerRecord(M.Edge):
    """Step 48: render one ledger record as an ordinary small GraphVersion.

    The quoted structure encodes four facts about the record -- its law,
    its outcome, the sign of its size delta, and its proposal class -- as
    an ordinary term, then hands that term to the Step-8 encoder. No new
    quotation machinery: EncodeTermAsGraph does the work, so the miner,
    matcher and census run over the result unchanged.

    Outcome and delta-sign are machine label singletons, not text, so the
    miner compares them structurally like any other constructor.
    """

    def __init__(self, record, outcome, proposal_class, registry=M.EmptyList):
        if M.IdentityCompare(registry, M.EmptyList)() is M.truth_value:
            registry = M.AllConstructors
        before_text = M.GMPRepText(
            M.NatRepOf(FiringRecordNodesBefore(record)(), registry)(),
        )()
        after_text = M.GMPRepText(
            M.NatRepOf(FiringRecordNodesAfter(record)(), registry)(),
        )()
        delta_sign = META_DELTA_FLAT
        if GMPLessText(after_text, before_text)() is M.truth_value:
            delta_sign = META_DELTA_SHRANK
        elif GMPLessText(before_text, after_text)() is M.truth_value:
            delta_sign = META_DELTA_GREW
        quoted_term = M.Pair(
            Lmod.MetaRecordLabel,
            M.Pair(
                FiringRecordLaw(record)(),
                M.Pair(
                    outcome,
                    M.Pair(delta_sign, M.Pair(proposal_class, M.EmptyList)),
                ),
            ),
        )
        self.result = EncodeTermAsGraph(quoted_term)()
        super().__init__(
            inputs=M.Pair(record, M.EmptyList),
            results=self.result,
        )

    def __call__(self):
        return self.result


class MineMetaPatterns(M.Edge):
    """Step 48: mine the machine's own outcome history.

    Quote the last META_WINDOW_CAP ledger records, then run the ordinary
    Step-27 miner over the quoted versions. Recurring patterns here are
    patterns-of-outcomes rather than patterns-of-terms, but nothing about
    the miner changes: the quoted records are just graphs.

    Misses are quoted too, so a law that keeps failing is as visible to
    the miner as one that keeps succeeding. This edge interprets nothing;
    it returns candidates for the ordinary handle path to name.
    """

    def __init__(self, ledger, min_count, max_size):
        registry = ledger.registry
        cap_text = M.GMPRepText(META_WINDOW_CAP)()
        scan_text = "0"
        reversed_quoted = M.EmptyList
        remaining = ledger.records
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                remaining = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                reversed_quoted = M.Pair(
                    QuoteLedgerRecord(
                        M.Head(remaining)(),
                        META_OUTCOME_FIRED,
                        META_CLASS_UNKNOWN,
                        registry,
                    )(),
                    reversed_quoted,
                )
                remaining = M.Tail(remaining)()
        remaining_misses = ledger.misses
        while M.IdentityCompare(remaining_misses, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                remaining_misses = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                miss = M.Head(remaining_misses)()
                miss_term = M.Pair(
                    Lmod.MetaRecordLabel,
                    M.Pair(
                        M.Head(miss)(),
                        M.Pair(
                            META_OUTCOME_MISSED,
                            M.Pair(
                                META_DELTA_FLAT,
                                M.Pair(META_CLASS_UNKNOWN, M.EmptyList),
                            ),
                        ),
                    ),
                )
                reversed_quoted = M.Pair(
                    EncodeTermAsGraph(miss_term)(),
                    reversed_quoted,
                )
                remaining_misses = M.Tail(remaining_misses)()
        quoted = Reverse(reversed_quoted)()
        self.result = M.EmptyList
        if M.IdentityCompare(quoted, M.EmptyList)() is M.false_value:
            self.result = MineRecurringPatterns(quoted, min_count, max_size)()
        super().__init__(
            inputs=M.Pair(min_count, M.Pair(max_size, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class OrderByPriors(M.Edge):
    """Step 48: stable-partition a candidate list by meta-handle priors.

    Candidates whose pattern matches a prior meta-handle come first, in
    their original relative order; everything else follows, also in its
    original relative order. This is order only: every input candidate
    appears in the output exactly once, so the set is unchanged and no cap
    is widened. Passing priors at all is a coordinator decision.
    """

    def __init__(self, candidates, prior_handles):
        self.result = candidates
        if M.IdentityCompare(prior_handles, M.EmptyList)() is M.false_value:
            cap_text = M.GMPRepText(MINE_CANDIDATE_CAP)()
            scan_text = "0"
            reversed_leading = M.EmptyList
            reversed_trailing = M.EmptyList
            remaining = candidates
            while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
                if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                    remaining = M.EmptyList
                else:
                    scan_text = GMPSuccText(scan_text)()
                    entry = M.Head(remaining)()
                    # A miner entry is Pair(pattern, Pair(count, ...)); a bare
                    # graph is also a Pair, headed by HypergraphLabel. Unwrap
                    # only the former, or the pattern becomes the label itself.
                    pattern = entry
                    if M.IsPair(entry)() is M.truth_value:
                        if M.TermEqual(
                            M.Head(entry)(),
                            M.HypergraphLabel,
                        )() is M.false_value:
                            pattern = M.Head(entry)()
                    favoured = M.false_value
                    remaining_priors = prior_handles
                    while M.IdentityCompare(
                        remaining_priors,
                        M.EmptyList,
                    )() is M.false_value:
                        prior = M.Head(remaining_priors)()
                        prior_pattern = prior
                        if M.IsPair(prior)() is M.truth_value:
                            if M.TermEqual(
                                M.Head(prior)(),
                                Lmod.HandleLabel,
                            )() is M.truth_value:
                                prior_pattern = HandlePattern(prior)()
                        mapping = FirstCompletedMatch(
                            prior_pattern,
                            pattern,
                        )()
                        if M.IdentityCompare(
                            mapping,
                            M.EmptyList,
                        )() is M.false_value:
                            favoured = M.truth_value
                            remaining_priors = M.EmptyList
                        else:
                            remaining_priors = M.Tail(remaining_priors)()
                    if M.IdentityCompare(favoured, M.truth_value)() is M.truth_value:
                        reversed_leading = M.Pair(entry, reversed_leading)
                    else:
                        reversed_trailing = M.Pair(entry, reversed_trailing)
                    remaining = M.Tail(remaining)()
            ordered = Reverse(reversed_trailing)()
            remaining_leading = reversed_leading
            while M.IdentityCompare(
                remaining_leading,
                M.EmptyList,
            )() is M.false_value:
                ordered = M.Pair(M.Head(remaining_leading)(), ordered)
                remaining_leading = M.Tail(remaining_leading)()
            self.result = ordered
        super().__init__(
            inputs=M.Pair(candidates, M.Pair(prior_handles, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


MIGRATION_PROPOSAL_CAP = M.GMPRep("10")
MIGRATION_SCAN_CAP = M.GMPRep("200")
CONFLICT_SCAN_CAP = M.GMPRep("200")


class FireTraceElements(M.Edge):
    """Step 44: the host elements one committed FiringRecord touched.

    The touched set is the record's mapped host nodes (Send targets in the
    Fire mapping root) together with the host edges of g0 absent from g1
    and the edges of g1 absent from g0 — everything the surgery consumed or
    produced. Returned as one Pair chain, order deterministic: mapped nodes
    in mapping order, then deleted edges in g0 store order, then inserted
    edges in g1 store order."""

    def __init__(self, record):
        elements = M.EmptyList
        trace = FiringRecordTrace(record)()
        fire = M.EmptyList
        remaining_trace = trace
        while M.IdentityCompare(remaining_trace, M.EmptyList)() is M.false_value:
            entry = M.Head(remaining_trace)()
            if M.IsPair(entry)() is M.truth_value:
                if M.TermEqual(M.Head(entry)(), Lmod.NextLabel)() is M.truth_value:
                    fire = M.Head(M.Tail(M.Tail(entry)())())()
            remaining_trace = M.Tail(remaining_trace)()
        reversed_elements = M.EmptyList
        if M.IdentityCompare(fire, M.EmptyList)() is M.false_value:
            mapping = M.Head(M.Tail(M.Tail(fire)())())()
            if M.IsPair(mapping)() is M.truth_value:
                if M.TermEqual(M.Head(mapping)(), Lmod.MapLabel)() is M.truth_value:
                    root = M.Head(M.Tail(M.Tail(M.Tail(mapping)())())())()
                    remaining_root = root
                    while M.IdentityCompare(
                        remaining_root,
                        M.EmptyList,
                    )() is M.false_value:
                        item = M.Head(remaining_root)()
                        if IsSend(item)() is M.truth_value:
                            reversed_elements = M.Pair(
                                SendHost(item)(),
                                reversed_elements,
                            )
                        remaining_root = M.Tail(remaining_root)()
        g0 = FiringRecordG0(record)()
        g1 = FiringRecordG1(record)()
        g0_edges = GraphEdges(g0)()
        g1_edges = GraphEdges(g1)()
        remaining_edges = g0_edges
        while M.IdentityCompare(remaining_edges, M.EmptyList)() is M.false_value:
            edge = M.Head(remaining_edges)()
            if ChainHasTerm(g1_edges, edge)() is M.false_value:
                reversed_elements = M.Pair(edge, reversed_elements)
            remaining_edges = M.Tail(remaining_edges)()
        remaining_edges = g1_edges
        while M.IdentityCompare(remaining_edges, M.EmptyList)() is M.false_value:
            edge = M.Head(remaining_edges)()
            if ChainHasTerm(g0_edges, edge)() is M.false_value:
                reversed_elements = M.Pair(edge, reversed_elements)
            remaining_edges = M.Tail(remaining_edges)()
        self.result = M.Reverse(reversed_elements)()
        super().__init__(
            inputs=M.Pair(record, M.EmptyList),
            results=self.result,
        )

    def __call__(self):
        return self.result


class Conflict(M.Edge):
    """Step 44: provenance term naming two firings that touched shared
    elements, with the shared elements and the canonical winner recorded."""

    def __init__(self, first_record, second_record, shared_elements, winner):
        self.result = M.Pair(
            Lmod.ConflictLabel,
            M.Pair(
                first_record,
                M.Pair(
                    second_record,
                    M.Pair(shared_elements, M.Pair(winner, M.EmptyList)),
                ),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                first_record,
                M.Pair(
                    second_record,
                    M.Pair(shared_elements, M.Pair(winner, M.EmptyList)),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class IsConflict(M.Edge):
    def __init__(self, term):
        self.result = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if M.TermEqual(M.Head(term)(), Lmod.ConflictLabel)() is M.truth_value:
                self.result = M.truth_value
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class DetectConflicts(M.Edge):
    """Step 44: pairwise overlap scan over one chronological record chain.

    Two records conflict when their Fire-trace element sets share at least
    one element by identity. The winner is always the record earlier in the
    chain (first-by-canonical-order: chronological ledger order, which for
    merged worker chains is worker order then per-worker order). Conflict
    terms are recorded, never discarded, and never mutate any version.
    Scans at most CONFLICT_SCAN_CAP records. Returns the Conflict chain in
    detection order."""

    def __init__(self, records, registry=M.EmptyList):
        if M.IdentityCompare(registry, M.EmptyList)() is M.truth_value:
            registry = M.AllConstructors
        scan_cap_text = M.GMPRepText(CONFLICT_SCAN_CAP)()
        scanned_text = "0"
        reversed_conflicts = M.EmptyList
        annotated = M.EmptyList
        remaining_records = records
        while M.IdentityCompare(remaining_records, M.EmptyList)() is M.false_value:
            if GMPEqualText(scanned_text, scan_cap_text)() is M.truth_value:
                remaining_records = M.EmptyList
            else:
                record = M.Head(remaining_records)()
                elements = FireTraceElements(record)()
                remaining_prior = annotated
                while M.IdentityCompare(
                    remaining_prior,
                    M.EmptyList,
                )() is M.false_value:
                    prior = M.Head(remaining_prior)()
                    prior_record = M.Head(prior)()
                    prior_elements = M.Head(M.Tail(prior)())()
                    reversed_shared = M.EmptyList
                    remaining_elements = elements
                    while M.IdentityCompare(
                        remaining_elements,
                        M.EmptyList,
                    )() is M.false_value:
                        element = M.Head(remaining_elements)()
                        if ChainHasTerm(
                            prior_elements,
                            element,
                        )() is M.truth_value:
                            reversed_shared = M.Pair(element, reversed_shared)
                        remaining_elements = M.Tail(remaining_elements)()
                    if M.IdentityCompare(
                        reversed_shared,
                        M.EmptyList,
                    )() is M.false_value:
                        reversed_conflicts = M.Pair(
                            Conflict(
                                prior_record,
                                record,
                                M.Reverse(reversed_shared)(),
                                prior_record,
                            )(),
                            reversed_conflicts,
                        )
                    remaining_prior = M.Tail(remaining_prior)()
                annotated = M.Pair(
                    M.Pair(record, M.Pair(elements, M.EmptyList)),
                    annotated,
                )
                scanned_text = GMPSuccText(scanned_text)()
                remaining_records = M.Tail(remaining_records)()
        self.result = M.Reverse(reversed_conflicts)()
        super().__init__(
            inputs=M.Pair(records, M.EmptyList),
            results=self.result,
        )

    def __call__(self):
        return self.result


class ConflictWinner(M.Edge):
    def __init__(self, conflict):
        self.result = M.Head(
            M.Tail(M.Tail(M.Tail(M.Tail(conflict)())())())(),
        )()
        super().__init__(
            inputs=M.Pair(conflict, M.EmptyList),
            results=self.result,
        )

    def __call__(self):
        return self.result


class Migration(M.Edge):
    """Step 41: provenance term naming an old-to-new handle replacement."""

    def __init__(self, old_handle, new_handle, bridge_law):
        self.result = M.Pair(
            Lmod.MigrationLabel,
            M.Pair(
                old_handle,
                M.Pair(new_handle, M.Pair(bridge_law, M.EmptyList)),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                old_handle,
                M.Pair(new_handle, M.Pair(bridge_law, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class IsMigration(M.Edge):
    def __init__(self, term):
        self.result = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if M.TermEqual(M.Head(term)(), Lmod.MigrationLabel)() is M.truth_value:
                self.result = M.truth_value
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class GenerateMigrationProposals(M.Edge):
    """Step 41: bridge retired handles onto matching active replacements.

    For each retired fold law whose handle-pattern completes a bounded match
    into an active fold law's handle-pattern (and whose interfaces are
    structurally equal), submit ONE proposal whose law rewrites the folded
    old abbreviation into the folded new abbreviation plus a Migration
    marker. No match, no proposal: bridges are never synthesized.
    """

    def __init__(self, proposal_store, graph_version):
        scan_cap_text = M.GMPRepText(MIGRATION_SCAN_CAP)()
        proposal_cap_text = M.GMPRepText(MIGRATION_PROPOSAL_CAP)()
        current_store = proposal_store
        submitted_text = "0"

        retired_folds = M.EmptyList
        active_folds = M.EmptyList
        scan_text = "0"
        remaining_statuses = AllLawsWithStatus(graph_version)()
        while M.IdentityCompare(
            remaining_statuses,
            M.EmptyList,
        )() is M.false_value:
            if GMPEqualText(scan_text, scan_cap_text)() is M.truth_value:
                remaining_statuses = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                status_entry = M.Head(remaining_statuses)()
                law = M.Head(status_entry)()
                status = M.Head(M.Tail(status_entry)())()
                handle = M.EmptyList
                element_scan_text = "0"
                remaining_elements = GraphNodes(LawRight(law)())()
                while M.IdentityCompare(
                    remaining_elements,
                    M.EmptyList,
                )() is M.false_value:
                    if GMPEqualText(
                        element_scan_text,
                        scan_cap_text,
                    )() is M.truth_value:
                        remaining_elements = M.EmptyList
                    else:
                        element_scan_text = GMPSuccText(element_scan_text)()
                        element = M.Head(remaining_elements)()
                        if M.IsPair(element)() is M.truth_value:
                            if M.TermEqual(
                                M.Head(element)(),
                                Lmod.HandleLabel,
                            )() is M.truth_value:
                                handle = element
                                remaining_elements = M.EmptyList
                        if M.IdentityCompare(
                            remaining_elements,
                            M.EmptyList,
                        )() is M.false_value:
                            remaining_elements = M.Tail(remaining_elements)()
                if M.IdentityCompare(handle, M.EmptyList)() is M.false_value:
                    entry = M.Pair(handle, M.Pair(law, M.EmptyList))
                    if M.Compare(status, M.Char("retired"))() is M.truth_value:
                        retired_folds = M.Pair(entry, retired_folds)
                    elif M.Compare(status, M.Char("active"))() is M.truth_value:
                        active_folds = M.Pair(entry, active_folds)
                remaining_statuses = M.Tail(remaining_statuses)()
        retired_folds = Reverse(retired_folds)()
        active_folds = Reverse(active_folds)()

        remaining_retired = retired_folds
        while M.IdentityCompare(
            remaining_retired,
            M.EmptyList,
        )() is M.false_value:
            if GMPEqualText(
                submitted_text,
                proposal_cap_text,
            )() is M.truth_value:
                remaining_retired = M.EmptyList
            else:
                retired_entry = M.Head(remaining_retired)()
                old_handle = M.Head(retired_entry)()
                old_fold = M.Head(M.Tail(retired_entry)())()
                remaining_active = active_folds
                while M.IdentityCompare(
                    remaining_active,
                    M.EmptyList,
                )() is M.false_value:
                    active_entry = M.Head(remaining_active)()
                    new_handle = M.Head(active_entry)()
                    new_fold = M.Head(M.Tail(active_entry)())()
                    compatible = M.TermEqual(
                        LawInterface(old_fold)(),
                        LawInterface(new_fold)(),
                    )()
                    mapping = M.EmptyList
                    if M.IdentityCompare(
                        compatible,
                        M.truth_value,
                    )() is M.truth_value:
                        mapping = BoundedFirstCompletedMatch(
                            HandlePattern(old_handle)(),
                            HandlePattern(new_handle)(),
                        )()
                    if M.IdentityCompare(mapping, M.EmptyList)() is M.false_value:
                        abbrev_old = LawRight(old_fold)()
                        abbrev_new = LawRight(new_fold)()
                        marker = Migration(
                            old_handle,
                            new_handle,
                            M.EmptyList,
                        )()
                        bridged_right = M.Pair(
                            M.HypergraphLabel,
                            M.Pair(
                                M.Pair(marker, GraphNodes(abbrev_new)()),
                                M.Pair(GraphEdges(abbrev_new)(), M.EmptyList),
                            ),
                        )
                        new_map = LawKToRight(new_fold)()
                        bridge = Law(
                            abbrev_old,
                            LawInterface(old_fold)(),
                            bridged_right,
                            LawKToRight(old_fold)(),
                            Map(
                                LawInterface(old_fold)(),
                                bridged_right,
                                M.Head(
                                    M.Tail(M.Tail(M.Tail(new_map)())())(),
                                )(),
                            )(),
                            M.EmptyList,
                        )()
                        proposal = Proposal(
                            bridge,
                            M.Char("handle-migration"),
                        )()
                        current_store = ProposalStoreSubmit(
                            current_store,
                            proposal,
                        )()
                        current_store = ProposalStoreAttach(
                            current_store,
                            proposal,
                            JustifiedBy(proposal, mapping)(),
                        )()
                        submitted_text = GMPSuccText(submitted_text)()
                        remaining_active = M.EmptyList
                    else:
                        remaining_active = M.Tail(remaining_active)()
                remaining_retired = M.Tail(remaining_retired)()

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
                M.Pair(graph_version, M.EmptyList),
            ),
            results=self.result,
        )

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
        # The cap is a loop bound, never a term under study: it is only ever
        # handed to NatEq below, never decomposed, matched, or TermEqual'd.
        # NatFromRep would materialize it as a Succ chain -- one allocation
        # per unit, superquadratic in the bound -- so a cap of 100 costs ~50s
        # to build before a single match is attempted. The cached atom denotes
        # the same number and NatEq compares the two representations alike.
        # Numerals the machine reasons about still get the Succ chain; this
        # one it only counts with.
        cap = MineNatFromGMPRep(match_cap)()
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
    """Mine witnessed patterns and submit bounded, mechanically checked folds.

    Step 43: optional `slice_index`/`slice_count` (GMPRep atoms) select a
    deterministic round-robin slice of the candidate list by candidate
    ordinal; `candidate_index` (and so mined names) advance over every
    candidate regardless of slice, so the union over all slices is
    byte-identical to an unsliced run.
    """

    def __init__(
        self,
        proposal_store,
        versions,
        ledger,
        min_count,
        slice_index=M.EmptyList,
        slice_count=M.EmptyList,
    ):
        candidate_cap = MineNatFromGMPRep(MINE_CANDIDATE_CAP)()
        proposal_cap = MineNatFromGMPRep(HANDLE_PROPOSAL_CAP)()
        pattern_max_size = MineNatFromGMPRep(MINE_CANDIDATE_CAP)()
        scanned = MineNatFromGMPRep(M.GMPRep("0"))()
        submitted_count = MineNatFromGMPRep(M.GMPRep("0"))()
        candidate_index = MineNatFromGMPRep(M.GMPRep("0"))()
        sliced = M.false_value
        slice_cursor_text = "0"
        slice_index_text = "0"
        slice_count_text = "0"
        if M.IdentityCompare(slice_index, M.EmptyList)() is M.false_value:
            if M.IdentityCompare(slice_count, M.EmptyList)() is M.false_value:
                sliced = M.truth_value
                slice_index_text = M.GMPRepText(slice_index)()
                slice_count_text = M.GMPRepText(slice_count)()
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
                mine_here = M.truth_value
                if M.IdentityCompare(sliced, M.truth_value)() is M.truth_value:
                    if GMPEqualText(
                        slice_cursor_text,
                        slice_index_text,
                    )() is M.false_value:
                        mine_here = M.false_value
                    slice_cursor_text = GMPSuccText(slice_cursor_text)()
                    if GMPEqualText(
                        slice_cursor_text,
                        slice_count_text,
                    )() is M.truth_value:
                        slice_cursor_text = "0"
                signature_ok = M.false_value
                roundtrip_ok = M.false_value
                handle = M.EmptyList
                interface_nodes = M.EmptyList
                report = M.EmptyList
                if M.IdentityCompare(mine_here, M.truth_value)() is M.truth_value:
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
                        Contract(
                            handle,
                            interface_nodes,
                            DefaultContractForbidden()(),
                        )(),
                    )()
                    stepped = MineNatSuccessor(
                        submitted_count,
                        ledger.registry,
                    )()
                    submitted_count = M.Head(stepped)()
                    ledger.registry = M.Head(M.Tail(stepped)())()
                elif M.IdentityCompare(mine_here, M.truth_value)() is M.truth_value:
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


class ObservedSymbolStep(M.Edge):
    """One symbol observed between two cursors.

    Pair(ObservedSymbolStepLabel, Pair(utterance, Pair(before,
    Pair(symbol, Pair(after, EmptyList))))). The client emits one of
    these per symbol as it arrives. It establishes no words, guesses no
    boundaries, normalises nothing and discards nothing -- it records
    what was observed, in order.
    """

    def __init__(self, utterance, before, symbol, after):
        self.result = M.Pair(
            Lmod.ObservedSymbolStepLabel,
            M.Pair(
                utterance,
                M.Pair(before, M.Pair(symbol, M.Pair(after, M.EmptyList))),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                utterance,
                M.Pair(before, M.Pair(symbol, M.Pair(after, M.EmptyList))),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class ObservedStepBefore(M.Edge):
    def __init__(self, step):
        self.result = M.Head(M.Tail(M.Tail(step)())())()
        super().__init__(inputs=M.Pair(step, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ObservedStepSymbol(M.Edge):
    def __init__(self, step):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(step)())())())()
        super().__init__(inputs=M.Pair(step, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ObservedStepAfter(M.Edge):
    def __init__(self, step):
        self.result = M.Head(
            M.Tail(M.Tail(M.Tail(M.Tail(step)())())())(),
        )()
        super().__init__(inputs=M.Pair(step, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FormArc(M.Edge):
    """One step of a shared form trie: state, symbol, next state."""

    def __init__(self, state, symbol, next_state):
        self.result = M.Pair(
            Lmod.FormArcLabel,
            M.Pair(state, M.Pair(symbol, M.Pair(next_state, M.EmptyList))),
        )
        super().__init__(
            inputs=M.Pair(
                state, M.Pair(symbol, M.Pair(next_state, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class FormSense(M.Edge):
    """A form state that spells something: its category and its meaning."""

    def __init__(self, state, category, meaning):
        self.result = M.Pair(
            Lmod.FormSenseLabel,
            M.Pair(state, M.Pair(category, M.Pair(meaning, M.EmptyList))),
        )
        super().__init__(
            inputs=M.Pair(
                state, M.Pair(category, M.Pair(meaning, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class FormScan(M.Edge):
    """A recognition in progress: trie state, where it began, where it is."""

    def __init__(self, state, start, cursor):
        self.result = M.Pair(
            Lmod.FormScanLabel,
            M.Pair(state, M.Pair(start, M.Pair(cursor, M.EmptyList))),
        )
        super().__init__(
            inputs=M.Pair(state, M.Pair(start, M.Pair(cursor, M.EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class Reading(M.Edge):
    """A meaning found over an interval of the observed input."""

    def __init__(self, category, start, end, meaning):
        self.result = M.Pair(
            Lmod.ReadingLabel,
            M.Pair(
                category, M.Pair(start, M.Pair(end, M.Pair(meaning, M.EmptyList))),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                category, M.Pair(start, M.Pair(end, M.Pair(meaning, M.EmptyList))),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class ObservedStepUtterance(M.Edge):
    def __init__(self, step):
        self.result = M.Head(M.Tail(step)())()
        super().__init__(inputs=M.Pair(step, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ObservedBy(M.Edge):
    """Provenance: which event stream the observations came from.

    Pair(ObservedByLabel, Pair(utterance, Pair(stream, EmptyList))). The
    client states where its ObservedSymbolStep facts came from; the
    machine stores the claim and derives nothing from it.
    """

    def __init__(self, utterance, stream):
        self.result = M.Pair(
            Lmod.ObservedByLabel,
            M.Pair(utterance, M.Pair(stream, M.EmptyList)),
        )
        super().__init__(
            inputs=M.Pair(utterance, M.Pair(stream, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class LexiconRoot(M.Edge):
    """The one shared trie root a language's forms hang from."""

    def __init__(self, language, root):
        self.result = M.Pair(
            Lmod.LexiconRootLabel,
            M.Pair(language, M.Pair(root, M.EmptyList)),
        )
        super().__init__(
            inputs=M.Pair(language, M.Pair(root, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class IndexSpec(M.Edge):
    """A declared index: a relation and the argument chain keying it.

    Pair(IndexSpecLabel, Pair(relation, Pair(keys, EmptyList))). The
    engine builds exactly the indexes it declares here and answers every
    premise from one; a spec without a root behind it would be a claim,
    so none is recorded that is not kept.
    """

    def __init__(self, relation, keys):
        self.result = M.Pair(
            Lmod.IndexSpecLabel,
            M.Pair(relation, M.Pair(keys, M.EmptyList)),
        )
        super().__init__(
            inputs=M.Pair(relation, M.Pair(keys, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class DeductionPlan(M.Edge):
    """The execution certificate for one trigger position of a law.

    Pair(DeductionPlanLabel, Pair(law, Pair(trigger, Pair(lookups,
    Pair(conclusion, EmptyList))))). The law stays the authoritative
    statement; the plan says which premise the delta arrives on, which
    declared indexes the other premises are answered from, and what
    relation the conclusion carries. One plan exists per premise
    position the engine executes; PlansByTriggerRelation holds them by
    trigger label.
    """

    def __init__(self, law, trigger, lookups, conclusion):
        self.result = M.Pair(
            Lmod.DeductionPlanLabel,
            M.Pair(
                law,
                M.Pair(trigger, M.Pair(lookups, M.Pair(conclusion, M.EmptyList))),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                law,
                M.Pair(trigger, M.Pair(lookups, M.Pair(conclusion, M.EmptyList))),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class DeltaAgenda(M.Edge):
    """The pending delta facts. Empty is quiescence."""

    def __init__(self, facts):
        self.result = M.Pair(Lmod.DeltaAgendaLabel, M.Pair(facts, M.EmptyList))
        super().__init__(inputs=M.Pair(facts, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class IndexedFiring(M.Edge):
    """One firing of a law by index: its premises and its conclusion.

    Pair(IndexedFiringLabel, Pair(law, Pair(premises, Pair(bindings,
    Pair(conclusion, EmptyList))))). The bindings slot stays empty until
    templates carry variables; every join here is by identity, so there
    is nothing else to record yet.
    """

    def __init__(self, law, premises, bindings, conclusion):
        self.result = M.Pair(
            Lmod.IndexedFiringLabel,
            M.Pair(
                law,
                M.Pair(
                    premises,
                    M.Pair(bindings, M.Pair(conclusion, M.EmptyList)),
                ),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                law,
                M.Pair(
                    premises,
                    M.Pair(bindings, M.Pair(conclusion, M.EmptyList)),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class BinaryProduction(M.Edge):
    """One binary grammar production: categories and a meaning template.

    Pair(BinaryProductionLabel, Pair(left, Pair(right, Pair(result,
    Pair(template, EmptyList))))). The template's variables bind the
    daughter meanings in order of first appearance: the first distinct
    variable takes the left daughter's meaning, the second the right
    daughter's, and one variable appearing twice shares one meaning in
    both places. A template that must keep the right daughter alone --
    a determiner or a command word dropped from the meaning -- cannot
    say so with a bare variable, since one variable binds to the left
    daughter; it says so with Pair(ProjectRightLabel,
    Pair(inner_template, EmptyList)), under which the first distinct
    variable of the inner template takes the right daughter's meaning.
    Every firing runs the template through FreshenTemplate before
    anything binds, so two applications of one production never share
    a variable.
    """

    def __init__(self, left, right, result, template):
        self.result = M.Pair(
            Lmod.BinaryProductionLabel,
            M.Pair(
                left,
                M.Pair(
                    right,
                    M.Pair(result, M.Pair(template, M.EmptyList)),
                ),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                left,
                M.Pair(
                    right,
                    M.Pair(result, M.Pair(template, M.EmptyList)),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class Freshened(M.Edge):
    """The record of one freshening: template, scope, bindings, result."""

    def __init__(self, template, scope, bindings, instantiated):
        self.result = M.Pair(
            Lmod.FreshenedLabel,
            M.Pair(
                template,
                M.Pair(
                    scope,
                    M.Pair(
                        bindings, M.Pair(instantiated, M.EmptyList),
                    ),
                ),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                template,
                M.Pair(
                    scope,
                    M.Pair(
                        bindings, M.Pair(instantiated, M.EmptyList),
                    ),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class FreshenTemplate(M.Edge):
    """Allocate fresh variables for one application of a template.

    The walk collects each distinct variable of the template by
    identity, in order of first appearance; allocates one new variable
    per distinct variable -- Pair(VarTag, Pair(scope, Pair(old,
    EmptyList))), so the recognised VarTag shape is kept and the scope
    tells applications apart -- builds the old-to-new binding chain,
    and rebuilds the template through it. Two occurrences of one old
    variable receive the same new variable; two applications receive
    different ones, whatever the scope atoms are.
    """

    def __init__(self, template, scope):
        empty = M.EmptyList

        distinct = empty
        stack = M.Pair(template, empty)
        while M.IdentityCompare(stack, empty)() is M.false_value:
            node = M.Head(stack)()
            stack = M.Tail(stack)()
            if M.IsPair(node)() is M.truth_value:
                if M.IdentityCompare(M.Head(node)(), M.VarTag)() is M.truth_value:
                    present = M.false_value
                    walker = distinct
                    while M.IdentityCompare(walker, empty)() is M.false_value:
                        if M.IdentityCompare(
                            M.Head(walker)(), node,
                        )() is M.truth_value:
                            present = M.truth_value
                            walker = empty
                        else:
                            walker = M.Tail(walker)()
                    if present is M.false_value:
                        distinct = M.Pair(node, distinct)
                else:
                    stack = M.Pair(M.Tail(node)(), stack)
                    stack = M.Pair(M.Head(node)(), stack)

        bindings = empty
        walker = distinct
        while M.IdentityCompare(walker, empty)() is M.false_value:
            old_variable = M.Head(walker)()
            fresh_variable = M.Pair(
                M.VarTag, M.Pair(scope, M.Pair(old_variable, empty)),
            )
            bindings = M.Pair(M.Pair(old_variable, fresh_variable), bindings)
            walker = M.Tail(walker)()

        self.bindings_chain = bindings
        self.instantiated = self._rebuild(template, bindings)
        self.result = Freshened(
            template, scope, bindings, self.instantiated,
        )()
        super().__init__(
            inputs=M.Pair(template, M.Pair(scope, empty)),
            results=self.result,
        )

    def _rebuild(self, node, bindings):
        if M.IsPair(node)() is M.truth_value:
            if M.IdentityCompare(M.Head(node)(), M.VarTag)() is M.truth_value:
                walker = bindings
                while M.IdentityCompare(walker, M.EmptyList)() is M.false_value:
                    entry = M.Head(walker)()
                    if M.IdentityCompare(
                        M.Head(entry)(), node,
                    )() is M.truth_value:
                        return M.Tail(entry)()
                    walker = M.Tail(walker)()
                return node
            return M.Pair(
                self._rebuild(M.Head(node)(), bindings),
                self._rebuild(M.Tail(node)(), bindings),
            )
        return node

    def __call__(self):
        return self.result


class ResolveReflexives(M.Edge):
    """Replace every reflexive marker in a term with one variable.

    Pair(ReflexiveLabel, ...) anywhere in the term becomes the given
    variable -- the same object at every site, which is the sharing a
    definition's self needs: "one and itself" must read as [one, self]
    with the self in the application and the self in the restriction
    being one variable. Every other structure is preserved and leaves
    are untouched.
    """

    def __init__(self, term, variable):
        self.result = self._resolve(term, variable)
        super().__init__(
            inputs=M.Pair(term, M.Pair(variable, M.EmptyList)),
            results=self.result,
        )

    def _resolve(self, node, variable):
        if M.IsPair(node)() is M.truth_value:
            if M.IdentityCompare(
                M.Head(node)(), Lmod.ReflexiveLabel,
            )() is M.truth_value:
                return variable
            return M.Pair(
                self._resolve(M.Head(node)(), variable),
                self._resolve(M.Tail(node)(), variable),
            )
        return node

    def __call__(self):
        return self.result


class PredicateHoles(M.Edge):
    """Keep undefined predicates as holes inside a formed chain.

    Pair(conditions, defined_labels) -> Pair(conditions_with_holes,
    Pair(hole_predicates, EmptyList)). A condition is holed when its
    label is installed nowhere and it is not the structural
    ExactFillers, which is scope rather than a predicate. The
    arguments move inside the hole unchanged and the reason is
    NoDefinitionInstalled; the predicate labels chain, in condition
    order with duplicates dropped, is the open-dependency report. A
    hole is the difference between lexical ignorance and a formed
    graph with a named gap: the graph exists, the gap is in it.
    """

    def __init__(self, conditions, defined_labels):
        empty = M.EmptyList
        reversed_conditions = empty
        reversed_holes = empty
        walker = conditions
        while M.IdentityCompare(walker, empty)() is M.false_value:
            condition = M.Head(walker)()
            label = M.Head(condition)()
            keep = M.false_value
            if M.IdentityCompare(
                label, Lmod.ExactFillersLabel,
            )() is M.truth_value:
                keep = M.truth_value
            else:
                defined_walker = defined_labels
                while M.IdentityCompare(
                    defined_walker, empty,
                )() is M.false_value:
                    if M.IdentityCompare(
                        label, M.Head(defined_walker)(),
                    )() is M.truth_value:
                        keep = M.truth_value
                        defined_walker = empty
                    else:
                        defined_walker = M.Tail(defined_walker)()
            if keep is M.truth_value:
                reversed_conditions = M.Pair(condition, reversed_conditions)
            else:
                holed = M.Pair(
                    Lmod.HoleLabel,
                    M.Pair(
                        label,
                        M.Pair(
                            M.Tail(condition)(),
                            M.Pair(
                                Lmod.NoDefinitionInstalledLabel, empty,
                            ),
                        ),
                    ),
                )
                reversed_conditions = M.Pair(holed, reversed_conditions)
                present = M.false_value
                hole_walker = reversed_holes
                while M.IdentityCompare(
                    hole_walker, empty,
                )() is M.false_value:
                    if M.IdentityCompare(
                        label, M.Head(hole_walker)(),
                    )() is M.truth_value:
                        present = M.truth_value
                        hole_walker = empty
                    else:
                        hole_walker = M.Tail(hole_walker)()
                if present is M.false_value:
                    reversed_holes = M.Pair(label, reversed_holes)
            walker = M.Tail(walker)()
        self.result = M.Pair(
            M.Reverse(reversed_conditions)(),
            M.Pair(M.Reverse(reversed_holes)(), empty),
        )
        super().__init__(
            inputs=M.Pair(conditions, M.Pair(defined_labels, empty)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class DefinitionNodeOpenDependencies(M.Edge):
    """The open dependencies of a formed definition graph, read off it.

    Walks the conditions; a Hole's predicate is an open dependency.
    Order follows the conditions; duplicates drop. This is the report
    that replaces asking about unknown words: the graph was formed, and
    these are the predicates it still needs definitions for.
    """

    def __init__(self, node):
        empty = M.EmptyList
        reversed_dependencies = empty
        walker = DefinitionNodeConditions(node)()
        while M.IdentityCompare(walker, empty)() is M.false_value:
            condition = M.Head(walker)()
            if M.IdentityCompare(
                M.Head(condition)(), Lmod.HoleLabel,
            )() is M.truth_value:
                predicate = M.Head(M.Tail(condition)())()
                present = M.false_value
                dependency_walker = reversed_dependencies
                while M.IdentityCompare(
                    dependency_walker, empty,
                )() is M.false_value:
                    if M.IdentityCompare(
                        predicate, M.Head(dependency_walker)(),
                    )() is M.truth_value:
                        present = M.truth_value
                        dependency_walker = empty
                    else:
                        dependency_walker = M.Tail(dependency_walker)()
                if present is M.false_value:
                    reversed_dependencies = M.Pair(
                        predicate, reversed_dependencies,
                    )
            walker = M.Tail(walker)()
        self.result = M.Reverse(reversed_dependencies)()
        super().__init__(
            inputs=M.Pair(node, M.EmptyList), results=self.result,
        )

    def __call__(self):
        return self.result


class SpanningDefinitionReading(M.Edge):
    """The definition reading that spans exactly the given cursors."""

    def __init__(self, readings, category, start, end):
        empty = M.EmptyList
        self.result = empty
        walker = readings
        while M.IdentityCompare(walker, empty)() is M.false_value:
            reading = M.Head(walker)()
            if M.IdentityCompare(
                M.Head(M.Tail(reading)())(), category,
            )() is M.truth_value:
                if M.IdentityCompare(
                    M.Head(M.Tail(M.Tail(reading)())())(), start,
                )() is M.truth_value:
                    if M.IdentityCompare(
                        M.Head(M.Tail(M.Tail(M.Tail(reading)())())())(), end,
                    )() is M.truth_value:
                        self.result = M.Head(
                            M.Tail(M.Tail(M.Tail(M.Tail(reading)())())())(),
                        )()
                        walker = empty
                    else:
                        walker = M.Tail(walker)()
                else:
                    walker = M.Tail(walker)()
            else:
                walker = M.Tail(walker)()
        super().__init__(
            inputs=M.Pair(
                readings,
                M.Pair(category, M.Pair(start, M.Pair(end, empty))),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class DefinitionFragment(M.Edge):
    """The definition fragment's lexicon and grammar, as facts.

    Thirteen forms: the command word, the colon, the space, the
    article, the adjective, the category noun carrying its category
    and its NonNegative presupposition, the copula, the relation
    adjective naming Divides, the restriction, the role preposition
    naming the divisor, the numeral, the conjunction, the reflexive.
    Thirty-seven binary productions compose them -- glue that eats the
    spaces and the colon, the adjective over the noun into a lexical
    noun phrase, coordination in either order, the restriction, and
    two definition shapes -- the head-noun order ("a prime number is
    divisible...") and the predicate-nominal order ("a prime is a
    number divisible..."), where the category rides after the copula.
    The fragment carries no entry for either shape's definiendum: a
    word that is not a form is a gap, and the gap is filled by the
    loop, not by hand. The trie states
    are found through nested red-black trees, the same shape the
    engine indexes arcs by.

    Returns Pair(arcs, Pair(senses, Pair(productions, Pair(root,
    Pair(def_category, Pair(one, Pair(prime, Pair(nat,
    Pair(divisor, Pair(alphabet, EmptyList))))))))) -- the atoms
    callers assert against ride after the facts, and the alphabet is
    the fragment's canonical symbols: an observed step only matches
    the trie if the client emits these atoms, because index keys are
    identities, not texts.
    """

    def __init__(self):
        empty = M.EmptyList

        sym_a = M.Char("a")
        sym_b = M.Char("b")
        sym_d = M.Char("d")
        sym_e = M.Char("e")
        sym_f = M.Char("f")
        sym_i = M.Char("i")
        sym_l = M.Char("l")
        sym_m = M.Char("m")
        sym_n = M.Char("n")
        sym_o = M.Char("o")
        sym_p = M.Char("p")
        sym_r = M.Char("r")
        sym_s = M.Char("s")
        sym_t = M.Char("t")
        sym_u = M.Char("u")
        sym_v = M.Char("v")
        sym_y = M.Char("y")
        # Letters no fragment word uses, carried so the gap loop can
        # OBSERVE unknown words that contain them ("six", "eight",
        # "twenty"): a word the lexicon lacks is a gap to learn, but a
        # letter the alphabet lacks kills the whole line unread.
        sym_c = M.Char("c")
        sym_g = M.Char("g")
        sym_h = M.Char("h")
        sym_j = M.Char("j")
        sym_k = M.Char("k")
        sym_q = M.Char("q")
        sym_w = M.Char("w")
        sym_x = M.Char("x")
        sym_z = M.Char("z")
        sym_colon = M.Char(":")
        sym_space = M.Char(" ")
        sym_open = M.Char("(")
        sym_close = M.Char(")")

        word_definition = M.Pair(sym_d, M.Pair(sym_e, M.Pair(sym_f, M.Pair(sym_i, M.Pair(sym_n, M.Pair(sym_i, M.Pair(sym_t, M.Pair(sym_i, M.Pair(sym_o, M.Pair(sym_n, empty))))))))))

        word_colon = M.Pair(sym_colon, empty)

        word_space = M.Pair(sym_space, empty)

        word_a = M.Pair(sym_a, empty)


        word_number = M.Pair(sym_n, M.Pair(sym_u, M.Pair(sym_m, M.Pair(sym_b, M.Pair(sym_e, M.Pair(sym_r, empty))))))

        word_is = M.Pair(sym_i, M.Pair(sym_s, empty))

        word_divisible = M.Pair(sym_d, M.Pair(sym_i, M.Pair(sym_v, M.Pair(sym_i, M.Pair(sym_s, M.Pair(sym_i, M.Pair(sym_b, M.Pair(sym_l, M.Pair(sym_e, empty)))))))))

        word_only = M.Pair(sym_o, M.Pair(sym_n, M.Pair(sym_l, M.Pair(sym_y, empty))))

        word_by = M.Pair(sym_b, M.Pair(sym_y, empty))

        word_one = M.Pair(sym_o, M.Pair(sym_n, M.Pair(sym_e, empty)))

        word_and = M.Pair(sym_a, M.Pair(sym_n, M.Pair(sym_d, empty)))

        word_itself = M.Pair(sym_i, M.Pair(sym_t, M.Pair(sym_s, M.Pair(sym_e, M.Pair(sym_l, M.Pair(sym_f, empty))))))

        word_natural = M.Pair(sym_n, M.Pair(sym_a, M.Pair(sym_t, M.Pair(sym_u, M.Pair(sym_r, M.Pair(sym_a, M.Pair(sym_l, empty)))))))

        word_that = M.Pair(sym_t, M.Pair(sym_h, M.Pair(sym_a, M.Pair(sym_t, empty))))

        word_not = M.Pair(sym_n, M.Pair(sym_o, M.Pair(sym_t, empty)))

        one = M.Char("one")
        prime = M.Char("prime")
        nat = M.Char("nat")
        divisor = M.Char("divisor")
        number_chunk = M.Pair(
            CategoryTerm(nat)(),
            M.Pair(M.Pair(Lmod.NonNegativeLabel, empty), empty),
        )

        cat_cw = M.Char("CW")
        cat_col = M.Char("COL")
        cat_spc = M.Char("SPC")
        cat_det = M.Char("DET")
        cat_adj = M.Char("ADJ")
        cat_cn = M.Char("CN")
        cat_cop = M.Char("COP")
        cat_radj = M.Char("RADJ")
        cat_rop = M.Char("ROP")
        cat_p = M.Char("P")
        cat_num = M.Char("NUM")
        cat_conj = M.Char("CONJ")
        cat_rpron = M.Char("RPRON")
        cat_adjg = M.Char("ADJG")
        cat_detg = M.Char("DETG")
        cat_cwg = M.Char("CWG")
        cat_cwgg = M.Char("CWGG")
        cat_np = M.Char("NP")
        cat_npg = M.Char("NPG")
        cat_sbj = M.Char("SBJ")
        cat_copg = M.Char("COPG")
        cat_numg = M.Char("NUMG")
        cat_conjg = M.Char("CONJG")
        cat_cjpron = M.Char("CJPRON")
        cat_coord = M.Char("COORD")
        cat_pg = M.Char("PG")
        cat_pp = M.Char("PP")
        cat_ropg = M.Char("ROPG")
        cat_rpred = M.Char("RPRED")
        cat_radg = M.Char("RADJG")
        cat_pred = M.Char("PRED")
        cat_def = M.Char("DEF")
        cat_sbare = M.Char("SBARE")
        cat_sbareg = M.Char("SBAREG")
        cat_sbare2 = M.Char("SBARE2")
        cat_sbare2g = M.Char("SBARE2G")
        cat_rprong = M.Char("RPRONG")
        cat_cjnum = M.Char("CJNUM")
        cat_ncat = M.Char("NCAT")
        cat_ncatg = M.Char("NCATG")
        cat_prednom = M.Char("PREDNOM")
        cat_relpron = M.Char("RELPRON")
        cat_neg = M.Char("NEG")
        cat_relprong = M.Char("RELPRONG")
        cat_negg = M.Char("NEGG")
        cat_negpred = M.Char("NEGPRED")
        cat_negpredg = M.Char("NEGPREDG")
        cat_relpred = M.Char("RELPRED")
        cat_qsubj = M.Char("QSUBJ")
        cat_question = M.Char("QUESTION")


        entries = M.Pair(M.Pair(word_definition, M.Pair(cat_cw, M.Char("definition"))), M.Pair(M.Pair(word_colon, M.Pair(cat_col, M.Char(":"))), M.Pair(M.Pair(word_space, M.Pair(cat_spc, M.Char(" "))), M.Pair(M.Pair(word_a, M.Pair(cat_det, M.Char("a"))), M.Pair(M.Pair(word_number, M.Pair(cat_cn, number_chunk)), M.Pair(M.Pair(word_is, M.Pair(cat_cop, M.Char("is"))), M.Pair(M.Pair(word_divisible, M.Pair(cat_radj, Lmod.DividesLabel)), M.Pair(M.Pair(word_only, M.Pair(cat_rop, M.Char("only"))), M.Pair(M.Pair(word_by, M.Pair(cat_p, divisor)), M.Pair(M.Pair(word_one, M.Pair(cat_num, one)), M.Pair(M.Pair(word_and, M.Pair(cat_conj, M.Char("and"))), M.Pair(M.Pair(word_itself, M.Pair(cat_rpron, M.Pair(Lmod.ReflexiveLabel, empty))), M.Pair(M.Pair(word_natural, M.Pair(cat_adj, M.Char("natural"))), M.Pair(M.Pair(word_that, M.Pair(cat_relpron, M.Char("that"))), M.Pair(M.Pair(word_not, M.Pair(cat_neg, Lmod.NotLabel)), empty)))))))))))))))

        root = M.Char("frag-root")
        self._state_counter_text = "0"
        tree = empty
        arcs_reversed = empty
        senses_reversed = empty
        walker = entries
        while M.IdentityCompare(walker, empty)() is M.false_value:
            entry = M.Head(walker)()
            outcome = self._extend_trie(
                tree, arcs_reversed, root, M.Head(entry)(),
            )
            tree = M.Head(outcome)()
            arcs_reversed = M.Head(M.Tail(outcome)())()
            final_state = M.Head(M.Tail(M.Tail(outcome)())())()
            senses_reversed = M.Pair(
                FormSense(
                    final_state,
                    M.Head(M.Tail(entry)())(),
                    M.Tail(M.Tail(entry)())(),
                )(),
                senses_reversed,
            )
            walker = M.Tail(walker)()
        arcs = M.Reverse(arcs_reversed)()
        senses = M.Reverse(senses_reversed)()

        kind_left = M.Char("kind-left")
        kind_project = M.Char("kind-project")
        kind_pair = M.Char("kind-pair")
        kind_np = M.Char("kind-np")
        kind_restriction = M.Char("kind-restriction")
        kind_definition = M.Char("kind-definition")
        specs = M.Pair(M.Pair(cat_adj, M.Pair(cat_spc, M.Pair(cat_adjg, M.Pair(kind_left, empty)))), M.Pair(M.Pair(cat_adjg, M.Pair(cat_cn, M.Pair(cat_np, M.Pair(kind_np, empty)))), M.Pair(M.Pair(cat_det, M.Pair(cat_spc, M.Pair(cat_detg, M.Pair(kind_left, empty)))), M.Pair(M.Pair(cat_detg, M.Pair(cat_adj, M.Pair(cat_sbare, M.Pair(kind_project, empty)))), M.Pair(M.Pair(cat_detg, M.Pair(cat_np, M.Pair(cat_np, M.Pair(kind_project, empty)))), M.Pair(M.Pair(cat_cw, M.Pair(cat_col, M.Pair(cat_cwg, M.Pair(kind_left, empty)))), M.Pair(M.Pair(cat_cwg, M.Pair(cat_spc, M.Pair(cat_cwgg, M.Pair(kind_left, empty)))), M.Pair(M.Pair(cat_cwgg, M.Pair(cat_np, M.Pair(cat_np, M.Pair(kind_project, empty)))), M.Pair(M.Pair(cat_cwgg, M.Pair(cat_sbare, M.Pair(cat_sbare, M.Pair(kind_project, empty)))), M.Pair(M.Pair(cat_np, M.Pair(cat_spc, M.Pair(cat_npg, M.Pair(kind_left, empty)))), M.Pair(M.Pair(cat_cop, M.Pair(cat_spc, M.Pair(cat_copg, M.Pair(kind_left, empty)))), M.Pair(M.Pair(cat_copg, M.Pair(cat_numg, M.Pair(cat_qsubj, M.Pair(kind_project, empty)))), M.Pair(M.Pair(cat_npg, M.Pair(cat_copg, M.Pair(cat_sbj, M.Pair(kind_left, empty)))), M.Pair(M.Pair(cat_qsubj, M.Pair(cat_npg, M.Pair(cat_question, M.Pair(kind_left, empty)))), M.Pair(M.Pair(cat_qsubj, M.Pair(cat_np, M.Pair(cat_question, M.Pair(kind_left, empty)))), M.Pair(M.Pair(cat_num, M.Pair(cat_spc, M.Pair(cat_numg, M.Pair(kind_left, empty)))), M.Pair(M.Pair(cat_conj, M.Pair(cat_spc, M.Pair(cat_conjg, M.Pair(kind_left, empty)))), M.Pair(M.Pair(cat_conjg, M.Pair(cat_rpron, M.Pair(cat_cjpron, M.Pair(kind_project, empty)))), M.Pair(M.Pair(cat_numg, M.Pair(cat_cjpron, M.Pair(cat_coord, M.Pair(kind_pair, empty)))), M.Pair(M.Pair(cat_p, M.Pair(cat_spc, M.Pair(cat_pg, M.Pair(kind_left, empty)))), M.Pair(M.Pair(cat_pg, M.Pair(cat_coord, M.Pair(cat_pp, M.Pair(kind_restriction, empty)))), M.Pair(M.Pair(cat_rop, M.Pair(cat_spc, M.Pair(cat_ropg, M.Pair(kind_left, empty)))), M.Pair(M.Pair(cat_ropg, M.Pair(cat_pp, M.Pair(cat_rpred, M.Pair(kind_project, empty)))), M.Pair(M.Pair(cat_radj, M.Pair(cat_spc, M.Pair(cat_radg, M.Pair(kind_left, empty)))), M.Pair(M.Pair(cat_radg, M.Pair(cat_rpred, M.Pair(cat_pred, M.Pair(kind_pair, empty)))), M.Pair(M.Pair(cat_sbj, M.Pair(cat_pred, M.Pair(cat_def, M.Pair(kind_definition, empty)))), M.Pair(M.Pair(cat_sbare, M.Pair(cat_spc, M.Pair(cat_sbareg, M.Pair(kind_left, empty)))), M.Pair(M.Pair(cat_sbareg, M.Pair(cat_copg, M.Pair(cat_sbare2, M.Pair(kind_left, empty)))), M.Pair(M.Pair(cat_sbare2, M.Pair(cat_spc, M.Pair(cat_sbare2g, M.Pair(kind_left, empty)))), M.Pair(M.Pair(cat_sbare2, M.Pair(cat_prednom, M.Pair(cat_def, M.Pair(kind_definition, empty)))), M.Pair(M.Pair(cat_sbare2g, M.Pair(cat_prednom, M.Pair(cat_def, M.Pair(kind_definition, empty)))), M.Pair(M.Pair(cat_rpron, M.Pair(cat_spc, M.Pair(cat_rprong, M.Pair(kind_left, empty)))), M.Pair(M.Pair(cat_conjg, M.Pair(cat_num, M.Pair(cat_cjnum, M.Pair(kind_project, empty)))), M.Pair(M.Pair(cat_rprong, M.Pair(cat_cjnum, M.Pair(cat_coord, M.Pair(kind_pair, empty)))), M.Pair(M.Pair(cat_detg, M.Pair(cat_cn, M.Pair(cat_ncat, M.Pair(kind_project, empty)))), M.Pair(M.Pair(cat_ncat, M.Pair(cat_spc, M.Pair(cat_ncatg, M.Pair(kind_left, empty)))), M.Pair(M.Pair(cat_ncatg, M.Pair(cat_pred, M.Pair(cat_prednom, M.Pair(kind_pair, empty)))), M.Pair(M.Pair(cat_qsubj, M.Pair(cat_adj, M.Pair(cat_question, M.Pair(kind_left, empty)))), M.Pair(M.Pair(cat_qsubj, M.Pair(cat_sbare, M.Pair(cat_question, M.Pair(kind_left, empty)))), M.Pair(M.Pair(cat_np, M.Pair(cat_spc, M.Pair(cat_npg, M.Pair(kind_left, empty)))), M.Pair(M.Pair(cat_relpron, M.Pair(cat_spc, M.Pair(cat_relprong, M.Pair(kind_left, empty)))), M.Pair(M.Pair(cat_relprong, M.Pair(cat_copg, M.Pair(cat_negg, M.Pair(kind_left, empty)))), M.Pair(M.Pair(cat_negg, M.Pair(cat_neg, M.Pair(cat_negpred, M.Pair(kind_project, empty)))), M.Pair(M.Pair(cat_negpred, M.Pair(cat_spc, M.Pair(cat_negpredg, M.Pair(kind_left, empty)))), M.Pair(M.Pair(cat_negpredg, M.Pair(cat_adj, M.Pair(cat_relpred, M.Pair(kind_pair, empty)))), M.Pair(M.Pair(cat_npg, M.Pair(cat_relpred, M.Pair(cat_prednom, M.Pair(kind_pair, empty)))), M.Pair(M.Pair(cat_sbj, M.Pair(cat_prednom, M.Pair(cat_def, M.Pair(kind_definition, empty)))), empty)))))))))))))))))))))))))))))))))))))))))))))))

        self._production_counter_text = "0"
        productions_reversed = empty
        walker = specs
        while M.IdentityCompare(walker, empty)() is M.false_value:
            spec = M.Head(walker)()
            kind = M.Head(M.Tail(M.Tail(M.Tail(spec)())())())()
            first = M.Pair(
                M.VarTag,
                M.Pair(
                    M.Char("?frag" + self._production_counter_text + "a"), empty,
                ),
            )
            second = M.Pair(
                M.VarTag,
                M.Pair(
                    M.Char("?frag" + self._production_counter_text + "b"), empty,
                ),
            )
            if M.IdentityCompare(kind, kind_left)() is M.truth_value:
                built = first
            elif M.IdentityCompare(kind, kind_project)() is M.truth_value:
                built = M.Pair(Lmod.ProjectRightLabel, M.Pair(second, empty))
            elif M.IdentityCompare(kind, kind_pair)() is M.truth_value:
                built = M.Pair(first, M.Pair(second, empty))
            elif M.IdentityCompare(kind, kind_np)() is M.truth_value:
                built = M.Pair(
                    Lmod.LexicalNpLabel, M.Pair(first, M.Pair(second, empty)),
                )
            elif M.IdentityCompare(kind, kind_restriction)() is M.truth_value:
                built = M.Pair(
                    Lmod.RestrictionLabel,
                    M.Pair(first, M.Pair(second, empty)),
                )
            else:
                built = M.Pair(
                    Lmod.DefinitionMeaningLabel,
                    M.Pair(first, M.Pair(second, empty)),
                )
            productions_reversed = M.Pair(
                BinaryProduction(
                    M.Head(spec)(),
                    M.Head(M.Tail(spec)())(),
                    M.Head(M.Tail(M.Tail(spec)())())(),
                    built,
                )(),
                productions_reversed,
            )
            self._production_counter_text = GMPSuccText(
                self._production_counter_text,
            )()
            walker = M.Tail(walker)()
        productions = M.Reverse(productions_reversed)()

        alphabet = M.Pair(sym_a, M.Pair(sym_b, M.Pair(sym_c, M.Pair(sym_d, M.Pair(sym_e, M.Pair(sym_f, M.Pair(sym_g, M.Pair(sym_h, M.Pair(sym_i, M.Pair(sym_j, M.Pair(sym_k, M.Pair(sym_l, M.Pair(sym_m, M.Pair(sym_n, M.Pair(sym_o, M.Pair(sym_p, M.Pair(sym_q, M.Pair(sym_r, M.Pair(sym_s, M.Pair(sym_t, M.Pair(sym_u, M.Pair(sym_v, M.Pair(sym_w, M.Pair(sym_x, M.Pair(sym_y, M.Pair(sym_z, M.Pair(sym_colon, M.Pair(sym_space, M.Pair(sym_open, M.Pair(sym_close, empty))))))))))))))))))))))))))))))
        self.result = M.Pair(
            arcs,
            M.Pair(
                senses,
                M.Pair(
                    productions,
                    M.Pair(
                        root,
                        M.Pair(
                            cat_def,
                            M.Pair(
                                one,
                                M.Pair(
                                    prime,
                                    M.Pair(
                                        nat,
                                        M.Pair(
                                            divisor,
                                            M.Pair(
                                                alphabet,
                                                M.Pair(
                                                    cat_spc,
                                                    M.Pair(cat_adj, empty),
                                                ),
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
        super().__init__(inputs=empty, results=self.result)

    def _extend_trie(self, tree, arcs_reversed, state, word_chain):
        empty = M.EmptyList
        if M.IdentityCompare(word_chain, empty)() is M.truth_value:
            return M.Pair(
                tree, M.Pair(arcs_reversed, M.Pair(state, empty)),
            )
        symbol = M.Head(word_chain)()
        by_symbol = Tmod.IdentityRedBlackLookupValue(tree, state)()
        if M.IdentityCompare(by_symbol, empty)() is M.truth_value:
            by_symbol = M.EmptyList
        next_state = Tmod.IdentityRedBlackLookupValue(by_symbol, symbol)()
        if M.IdentityCompare(next_state, empty)() is M.truth_value:
            next_state = M.Char("frag-st-" + self._state_counter_text)
            self._state_counter_text = GMPSuccText(self._state_counter_text)()
            arcs_reversed = M.Pair(
                FormArc(state, symbol, next_state)(), arcs_reversed,
            )
            tree = Tmod.IdentityRedBlackInsert(
                tree,
                state,
                Tmod.IdentityRedBlackInsert(by_symbol, symbol, next_state)(),
            )()
        return self._extend_trie(
            tree, arcs_reversed, next_state, M.Tail(word_chain)(),
        )

    def __call__(self):
        return self.result


class LexicalGap(M.Edge):
    """The word-shaped hole between readings, and the category the grammar asks to fill it.

    Pair(readings, Pair(productions, Pair(spc_category, EmptyList))) ->
    Pair(start, Pair(end, Pair(category, EmptyList))), or EmptyList.

    A gap is a run between two space readings that no reading covers;
    spaces are observed events, so the run between two of them is a
    word-shaped hole, not a tokenized word. The category is read
    backwards through the grammar: the reading that starts where the
    right space ends anchors a production's right daughter; the left
    daughter then wants to end where the right space begins; and the
    glue production (word, space, left-daughter) says which
    word-category spans the gap. One backward step and one hop of
    glue -- what the grammar says at the boundary, no more.
    """

    def __init__(self, readings, productions, spc_category,
                 line_end=M.EmptyList):
        empty = M.EmptyList
        self.result = empty

        spaces_reversed = empty
        walker = readings
        while M.IdentityCompare(walker, empty)() is M.false_value:
            reading = M.Head(walker)()
            if M.IdentityCompare(
                M.Head(M.Tail(reading)())(), spc_category,
            )() is M.truth_value:
                spaces_reversed = M.Pair(reading, spaces_reversed)
            walker = M.Tail(walker)()
        spaces = M.Reverse(spaces_reversed)()

        outer = spaces
        while M.IdentityCompare(outer, empty)() is M.false_value:
            if M.IdentityCompare(self.result, empty)() is M.false_value:
                outer = empty
            else:
                space_a = M.Head(outer)()
                gap_start = M.Head(M.Tail(M.Tail(M.Tail(space_a)())())())()
                inner = spaces
                while M.IdentityCompare(inner, empty)() is M.false_value:
                    if M.IdentityCompare(self.result, empty)() is M.false_value:
                        inner = empty
                    else:
                        space_b = M.Head(inner)()
                        gap_end = M.Head(M.Tail(M.Tail(space_b)())())()
                        forward = GMPLessText(
                            M.GMPRepText(gap_start)(),
                            M.GMPRepText(gap_end)(),
                        )()
                        if forward is M.truth_value:
                            uncovered = M.truth_value
                            check = readings
                            while M.IdentityCompare(check, empty)() is M.false_value:
                                other = M.Head(check)()
                                other_start = M.Head(M.Tail(M.Tail(other)())())()
                                other_end = M.Head(M.Tail(M.Tail(M.Tail(other)())())())()
                                starts_before_end = GMPLessText(
                                    M.GMPRepText(other_start)(),
                                    M.GMPRepText(gap_end)(),
                                )()
                                ends_after_start = GMPLessText(
                                    M.GMPRepText(gap_start)(),
                                    M.GMPRepText(other_end)(),
                                )()
                                if starts_before_end is M.truth_value:
                                    if ends_after_start is M.truth_value:
                                        uncovered = M.false_value
                                check = M.Tail(check)()
                            if uncovered is M.truth_value:
                                # The left context first: what has already
                                # been parsed up to the hole is the
                                # incremental reading order, and anchoring
                                # on the right reading first proposed a
                                # category the left context cannot use
                                # ("is seven prime": the right-anchored
                                # read saw ADJ and proposed DET for
                                # "seven"; the COPG on the left wants
                                # NUM). Right anchor stays as fallback.
                                self._infer_category_from_left(
                                    readings, productions, spc_category,
                                    gap_start, gap_end,
                                )
                                if M.IdentityCompare(
                                    self.result, empty,
                                )() is M.truth_value:
                                    self._infer_category(
                                        readings, productions, space_b,
                                        gap_start, gap_end,
                                    )
                        inner = M.Tail(inner)()
                outer = M.Tail(outer)()

        if M.IdentityCompare(self.result, empty)() is M.truth_value:
            # A word that ENDS the line has a left space but no right
            # space, so the two-space scan above never sees it. The
            # readings cannot say where the line ends -- an uncovered
            # final word leaves no reading over itself -- so the caller
            # passes the line's final cursor. A run from a space to
            # that cursor that no reading covers is the same
            # word-shaped hole, read leftward for its category.
            if M.IdentityCompare(line_end, empty)() is M.false_value:
                outer = spaces
                while M.IdentityCompare(outer, empty)() is M.false_value:
                    if M.IdentityCompare(
                        self.result, empty,
                    )() is M.false_value:
                        outer = empty
                    else:
                        space_a = M.Head(outer)()
                        gap_start = M.Head(
                            M.Tail(M.Tail(M.Tail(space_a)())())(),
                        )()
                        forward = GMPLessText(
                            M.GMPRepText(gap_start)(),
                            M.GMPRepText(line_end)(),
                        )()
                        if forward is M.truth_value:
                            uncovered = M.truth_value
                            check = readings
                            while M.IdentityCompare(
                                check, empty,
                            )() is M.false_value:
                                other = M.Head(check)()
                                other_start = M.Head(
                                    M.Tail(M.Tail(other)())(),
                                )()
                                other_end = M.Head(
                                    M.Tail(M.Tail(M.Tail(other)())())(),
                                )()
                                starts_before_end = GMPLessText(
                                    M.GMPRepText(other_start)(),
                                    M.GMPRepText(line_end)(),
                                )()
                                ends_after_start = GMPLessText(
                                    M.GMPRepText(gap_start)(),
                                    M.GMPRepText(other_end)(),
                                )()
                                if starts_before_end is M.truth_value:
                                    if ends_after_start is M.truth_value:
                                        uncovered = M.false_value
                                check = M.Tail(check)()
                            if uncovered is M.truth_value:
                                self._infer_category_from_left(
                                    readings, productions, spc_category,
                                    gap_start, line_end,
                                )
                        outer = M.Tail(outer)()

        super().__init__(
            inputs=M.Pair(
                readings,
                M.Pair(productions, M.Pair(spc_category, empty)),
            ),
            results=self.result,
        )

    def _infer_category(self, readings, productions, space_b, gap_start, gap_end):
        empty = M.EmptyList
        anchor_start = M.Head(M.Tail(M.Tail(M.Tail(space_b)())())())()
        walker = readings
        anchor_category = empty
        while M.IdentityCompare(walker, empty)() is M.false_value:
            reading = M.Head(walker)()
            if M.IdentityCompare(
                M.Head(M.Tail(M.Tail(reading)())())(), anchor_start,
            )() is M.truth_value:
                anchor_category = M.Head(M.Tail(reading)())()
                walker = empty
            else:
                walker = M.Tail(walker)()
        if M.IdentityCompare(anchor_category, empty)() is M.truth_value:
            return
        outer = productions
        while M.IdentityCompare(outer, empty)() is M.false_value:
            production = M.Head(outer)()
            right_category = M.Head(M.Tail(M.Tail(production)())())()
            if M.IdentityCompare(right_category, anchor_category)() is M.truth_value:
                left_category = M.Head(M.Tail(production)())()
                inner = productions
                while M.IdentityCompare(inner, empty)() is M.false_value:
                    glue = M.Head(inner)()
                    glue_left = M.Head(M.Tail(glue)())()
                    glue_result = M.Head(M.Tail(M.Tail(M.Tail(glue)())())())()
                    if M.IdentityCompare(glue_result, left_category)() is M.truth_value:
                        self.result = M.Pair(
                            gap_start,
                            M.Pair(gap_end, M.Pair(glue_left, empty)),
                        )
                        inner = empty
                        outer = empty
                    else:
                        inner = M.Tail(inner)()
            else:
                outer = M.Tail(outer)()

    def _infer_category_from_left(
        self, readings, productions, spc_category, gap_start, gap_end,
    ):
        """The other half of the boundary read.

        The right-anchored half asks what the reading after the hole
        wants to its left; this half asks what the reading that ends
        where the hole begins wants to its right. A production whose
        left daughter is that category names the wanted category as
        its right daughter, and the wanted one must be a word
        category -- one that glues with a space to its right.
        Production order is the grammar's precedence when two
        productions want different things at the same boundary; the
        chart, not the inference, has the final word.
        """
        empty = M.EmptyList
        walker = readings
        anchor_category = empty
        while M.IdentityCompare(walker, empty)() is M.false_value:
            reading = M.Head(walker)()
            if M.IdentityCompare(
                M.Head(M.Tail(reading)())(), spc_category,
            )() is M.truth_value:
                walker = M.Tail(walker)()
            elif M.IdentityCompare(
                M.Head(M.Tail(M.Tail(M.Tail(reading)())())())(), gap_start,
            )() is M.truth_value:
                anchor_category = M.Head(M.Tail(reading)())()
                walker = empty
            else:
                walker = M.Tail(walker)()
        if M.IdentityCompare(anchor_category, empty)() is M.truth_value:
            return
        outer = productions
        while M.IdentityCompare(outer, empty)() is M.false_value:
            production = M.Head(outer)()
            if M.IdentityCompare(
                M.Head(M.Tail(production)())(), anchor_category,
            )() is M.truth_value:
                wanted = M.Head(M.Tail(M.Tail(production)())())()
                inner = productions
                while M.IdentityCompare(inner, empty)() is M.false_value:
                    glue = M.Head(inner)()
                    glue_left = M.Head(M.Tail(glue)())()
                    glue_right = M.Head(M.Tail(M.Tail(glue)())())()
                    glue_result = M.Head(M.Tail(M.Tail(M.Tail(glue)())())())()
                    glue_is_space = M.IdentityCompare(
                        glue_right, spc_category,
                    )() is M.truth_value
                    word_direct = M.IdentityCompare(
                        glue_left, wanted,
                    )() is M.truth_value and glue_is_space
                    word_glued = M.IdentityCompare(
                        glue_result, wanted,
                    )() is M.truth_value and glue_is_space
                    if word_direct:
                        self.result = M.Pair(
                            gap_start,
                            M.Pair(gap_end, M.Pair(wanted, empty)),
                        )
                        inner = empty
                        outer = empty
                    elif word_glued:
                        self.result = M.Pair(
                            gap_start,
                            M.Pair(gap_end, M.Pair(glue_left, empty)),
                        )
                        inner = empty
                        outer = empty
                    else:
                        inner = M.Tail(inner)()
            else:
                outer = M.Tail(outer)()

    def __call__(self):
        return self.result


class ProvisionalWord(M.Edge):
    """A gap becomes lexicon: arcs for its symbols, and a sense with a hole.

    Pair(root, Pair(symbols, Pair(category, Pair(word, EmptyList)))) ->
    Pair(arcs, Pair(sense, Pair(final_state, EmptyList))). The states
    are fresh, the arcs spell the gap's symbols from the root, and the
    sense's meaning is Hole(word, EmptyList, NoDefinitionInstalled):
    the category came from the grammar, the meaning is not known yet,
    and the definition the word appears in is what will supply it.
    Learn the arcs and the sense into the running engine and drain;
    the chart completes without anything re-observing.
    """

    def __init__(self, root, symbols, category, word):
        empty = M.EmptyList
        arcs_reversed = empty
        state = root
        counter_text = "0"
        walker = symbols
        while M.IdentityCompare(walker, empty)() is M.false_value:
            next_state = M.Char("gap-st-" + counter_text)
            counter_text = GMPSuccText(counter_text)()
            arcs_reversed = M.Pair(
                FormArc(state, M.Head(walker)(), next_state)(),
                arcs_reversed,
            )
            state = next_state
            walker = M.Tail(walker)()
        sense = FormSense(
            state, category, Hole(word, empty, Lmod.NoDefinitionInstalledLabel)(),
        )()
        self.result = M.Pair(
            M.Reverse(arcs_reversed)(),
            M.Pair(sense, M.Pair(state, empty)),
        )
        super().__init__(
            inputs=M.Pair(
                root,
                M.Pair(
                    symbols,
                    M.Pair(category, M.Pair(word, empty)),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class RecogniseForms(M.Edge):
    """The reader's deduction, run by index and delta instead of by search.

    Three ordinary monotone laws, compiled by CompileDeductionToLaw and
    left whole:

        FormScan(?f, ?start, ?cur),
        ObservedSymbolStep(?u, ?cur, ?sym, ?next),
        FormArc(?f, ?sym, ?f2)
            ->  FormScan(?f2, ?start, ?next)

        FormScan(?f, ?start, ?cur),
        FormSense(?f, ?cat, ?mean)
            ->  Reading(?cat, ?start, ?cur, ?mean)

        Reading(?a, ?start, ?mid, ?ma),
        BinaryProduction(?a, ?b, ?c, ?t),
        Reading(?b, ?mid, ?end, ?mb)
            ->  Reading(?c, ?start, ?end, composed)

    The laws stay authoritative; the engine never reads them back to
    run. Each is executed through the DeductionPlan records keyed by
    trigger relation in PlansByTriggerRelation: a plan names its
    trigger premise, one lookup step per remaining premise -- an
    IndexSpec together with that premise's variable pattern -- and the
    conclusion template. The interpreter binds the trigger's arguments,
    resolves each lookup's key positions from those bindings, walks the
    index chains, checks the remaining bound arguments by identity,
    instantiates the conclusion, and inserts it. One plan exists per
    premise position of the first two laws, so facts arrive in any
    order: a late arc finds the scans waiting for it, a late sense the
    scans at its state. Composition is triggered by either daughter.
    The one position not executed is a production arriving after
    readings exist.

    Every fact enters through one insert that deduplicates on the
    relation's first declared index -- a lookup by the declared keys
    and a value comparison along the small chain it returns --
    maintains every declared index, and queues itself on the
    DeltaAgenda. The loop pops until the agenda is empty, which is
    quiescence; no pass ever rereads the store, and nothing asks the
    generic matcher anything. The indexes are red-black trees keyed on
    atoms, the one structure here with sublinear fan-out. All observed
    steps must belong to one utterance, and composition refuses a
    daughter of zero width: readings over an empty span would compose
    with themselves forever.
    """

    def __init__(self, steps, arcs, senses, root, productions):
        empty = M.EmptyList

        self.facts_inserted_text = "0"
        self.delta_popped_text = "0"
        self.index_lookups_text = "0"
        self.facts_returned_text = "0"
        self.conclusions_attempted_text = "0"
        self.new_conclusions_text = "0"
        self.full_store_enumerations_text = "0"
        self.freshen_count_text = "0"
        self.definition_count_text = "0"

        var_f = M.Pair(M.VarTag, M.Pair(M.Char("?f"), empty))
        var_start = M.Pair(M.VarTag, M.Pair(M.Char("?start"), empty))
        var_cur = M.Pair(M.VarTag, M.Pair(M.Char("?cur"), empty))
        var_u = M.Pair(M.VarTag, M.Pair(M.Char("?u"), empty))
        var_sym = M.Pair(M.VarTag, M.Pair(M.Char("?sym"), empty))
        var_next = M.Pair(M.VarTag, M.Pair(M.Char("?next"), empty))
        var_f2 = M.Pair(M.VarTag, M.Pair(M.Char("?f2"), empty))
        var_g = M.Pair(M.VarTag, M.Pair(M.Char("?g"), empty))
        var_s2 = M.Pair(M.VarTag, M.Pair(M.Char("?s2"), empty))
        var_c2 = M.Pair(M.VarTag, M.Pair(M.Char("?c2"), empty))
        var_cat = M.Pair(M.VarTag, M.Pair(M.Char("?cat"), empty))
        var_mean = M.Pair(M.VarTag, M.Pair(M.Char("?mean"), empty))
        var_ra = M.Pair(M.VarTag, M.Pair(M.Char("?ra"), empty))
        var_rb = M.Pair(M.VarTag, M.Pair(M.Char("?rb"), empty))
        var_rc = M.Pair(M.VarTag, M.Pair(M.Char("?rc"), empty))
        var_rs = M.Pair(M.VarTag, M.Pair(M.Char("?rs"), empty))
        var_re = M.Pair(M.VarTag, M.Pair(M.Char("?re"), empty))
        var_rmid = M.Pair(M.VarTag, M.Pair(M.Char("?rmid"), empty))
        var_rma = M.Pair(M.VarTag, M.Pair(M.Char("?rma"), empty))
        var_rmb = M.Pair(M.VarTag, M.Pair(M.Char("?rmb"), empty))
        var_rt = M.Pair(M.VarTag, M.Pair(M.Char("?rt"), empty))
        self._compose_start_var = var_rs
        self._compose_mid_var = var_rmid
        self._compose_end_var = var_re

        self.scan_law = CompileDeductionToLaw(
            P.MultiRule(
                M.Pair(
                    M.Pair(
                        Lmod.FormScanLabel,
                        M.Pair(var_f, M.Pair(var_start, M.Pair(var_cur, empty))),
                    ),
                    M.Pair(
                        M.Pair(
                            Lmod.ObservedSymbolStepLabel,
                            M.Pair(
                                var_u,
                                M.Pair(
                                    var_cur,
                                    M.Pair(var_sym, M.Pair(var_next, empty)),
                                ),
                            ),
                        ),
                        M.Pair(
                            M.Pair(
                                Lmod.FormArcLabel,
                                M.Pair(
                                    var_f,
                                    M.Pair(var_sym, M.Pair(var_f2, empty)),
                                ),
                            ),
                            empty,
                        ),
                    ),
                ),
                M.Pair(
                    Lmod.FormScanLabel,
                    M.Pair(var_f2, M.Pair(var_start, M.Pair(var_next, empty))),
                ),
            ),
        )()
        self.sense_law = CompileDeductionToLaw(
            P.MultiRule(
                M.Pair(
                    M.Pair(
                        Lmod.FormScanLabel,
                        M.Pair(var_g, M.Pair(var_s2, M.Pair(var_c2, empty))),
                    ),
                    M.Pair(
                        M.Pair(
                            Lmod.FormSenseLabel,
                            M.Pair(
                                var_g,
                                M.Pair(var_cat, M.Pair(var_mean, empty)),
                            ),
                        ),
                        empty,
                    ),
                ),
                M.Pair(
                    Lmod.ReadingLabel,
                    M.Pair(
                        var_cat,
                        M.Pair(
                            var_s2,
                            M.Pair(var_c2, M.Pair(var_mean, empty)),
                        ),
                    ),
                ),
            ),
        )()
        self.compose_law = CompileDeductionToLaw(
            P.MultiRule(
                M.Pair(
                    M.Pair(
                        Lmod.ReadingLabel,
                        M.Pair(
                            var_ra,
                            M.Pair(
                                var_rs,
                                M.Pair(var_rmid, M.Pair(var_rma, empty)),
                            ),
                        ),
                    ),
                    M.Pair(
                        M.Pair(
                            Lmod.BinaryProductionLabel,
                            M.Pair(
                                var_ra,
                                M.Pair(
                                    var_rb,
                                    M.Pair(var_rc, M.Pair(var_rt, empty)),
                                ),
                            ),
                        ),
                        M.Pair(
                            M.Pair(
                                Lmod.ReadingLabel,
                                M.Pair(
                                    var_rb,
                                    M.Pair(
                                        var_rmid,
                                        M.Pair(var_re, M.Pair(var_rmb, empty)),
                                    ),
                                ),
                            ),
                            empty,
                        ),
                    ),
                ),
                M.Pair(
                    Lmod.ReadingLabel,
                    M.Pair(
                        var_rc,
                        M.Pair(
                            var_rs,
                            M.Pair(
                                var_re,
                                M.Pair(
                                    M.Pair(
                                        Lmod.ComposeMeaningLabel,
                                        M.Pair(
                                            var_rt,
                                            M.Pair(
                                                var_rma,
                                                M.Pair(var_rmb, empty),
                                            ),
                                        ),
                                    ),
                                    empty,
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        )()

        self.step_index_spec = IndexSpec(
            Lmod.ObservedSymbolStepLabel, M.Pair(M.GMPRep("1"), empty),
        )()
        self.arc_index_spec = IndexSpec(
            Lmod.FormArcLabel,
            M.Pair(M.GMPRep("0"), M.Pair(M.GMPRep("1"), empty)),
        )()
        self.sense_index_spec = IndexSpec(
            Lmod.FormSenseLabel, M.Pair(M.GMPRep("0"), empty),
        )()
        self.scan_cursor_index_spec = IndexSpec(
            Lmod.FormScanLabel, M.Pair(M.GMPRep("2"), empty),
        )()
        self.scan_state_index_spec = IndexSpec(
            Lmod.FormScanLabel, M.Pair(M.GMPRep("0"), empty),
        )()
        self.reading_start_index_spec = IndexSpec(
            Lmod.ReadingLabel,
            M.Pair(M.GMPRep("0"), M.Pair(M.GMPRep("1"), empty)),
        )()
        self.reading_end_index_spec = IndexSpec(
            Lmod.ReadingLabel,
            M.Pair(M.GMPRep("0"), M.Pair(M.GMPRep("2"), empty)),
        )()
        self.production_left_index_spec = IndexSpec(
            Lmod.BinaryProductionLabel, M.Pair(M.GMPRep("0"), empty),
        )()
        self.production_right_index_spec = IndexSpec(
            Lmod.BinaryProductionLabel, M.Pair(M.GMPRep("1"), empty),
        )()
        self.index_specs = M.Pair(
            self.step_index_spec,
            M.Pair(
                self.arc_index_spec,
                M.Pair(
                    self.sense_index_spec,
                    M.Pair(
                        self.scan_cursor_index_spec,
                        M.Pair(
                            self.scan_state_index_spec,
                            M.Pair(
                                self.reading_start_index_spec,
                                M.Pair(
                                    self.reading_end_index_spec,
                                    M.Pair(
                                        self.production_left_index_spec,
                                        M.Pair(
                                            self.production_right_index_spec,
                                            empty,
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        )

        scan_pattern = M.Pair(
            Lmod.FormScanLabel,
            M.Pair(var_f, M.Pair(var_start, M.Pair(var_cur, empty))),
        )
        step_pattern = M.Pair(
            Lmod.ObservedSymbolStepLabel,
            M.Pair(
                var_u,
                M.Pair(var_cur, M.Pair(var_sym, M.Pair(var_next, empty))),
            ),
        )
        arc_pattern = M.Pair(
            Lmod.FormArcLabel,
            M.Pair(var_f, M.Pair(var_sym, M.Pair(var_f2, empty))),
        )
        sense_pattern = M.Pair(
            Lmod.FormSenseLabel,
            M.Pair(var_f, M.Pair(var_cat, M.Pair(var_mean, empty))),
        )
        reading_a_pattern = M.Pair(
            Lmod.ReadingLabel,
            M.Pair(
                var_ra,
                M.Pair(var_rs, M.Pair(var_rmid, M.Pair(var_rma, empty))),
            ),
        )
        production_pattern = M.Pair(
            Lmod.BinaryProductionLabel,
            M.Pair(
                var_ra,
                M.Pair(var_rb, M.Pair(var_rc, M.Pair(var_rt, empty))),
            ),
        )
        reading_b_pattern = M.Pair(
            Lmod.ReadingLabel,
            M.Pair(
                var_rb,
                M.Pair(var_rmid, M.Pair(var_re, M.Pair(var_rmb, empty))),
            ),
        )
        scan_conclusion = M.Pair(
            Lmod.FormScanLabel,
            M.Pair(var_f2, M.Pair(var_start, M.Pair(var_next, empty))),
        )
        reading_conclusion = M.Pair(
            Lmod.ReadingLabel,
            M.Pair(
                var_cat,
                M.Pair(var_start, M.Pair(var_cur, M.Pair(var_mean, empty))),
            ),
        )
        compose_conclusion = M.Pair(
            Lmod.ReadingLabel,
            M.Pair(
                var_rc,
                M.Pair(
                    var_rs,
                    M.Pair(
                        var_re,
                        M.Pair(
                            M.Pair(
                                Lmod.ComposeMeaningLabel,
                                M.Pair(
                                    var_rt,
                                    M.Pair(var_rma, M.Pair(var_rmb, empty)),
                                ),
                            ),
                            empty,
                        ),
                    ),
                ),
            ),
        )

        self.plan_from_scan = DeductionPlan(
            self.scan_law,
            scan_pattern,
            M.Pair(
                M.Pair(
                    self.step_index_spec, M.Pair(step_pattern, empty),
                ),
                M.Pair(
                    M.Pair(self.arc_index_spec, M.Pair(arc_pattern, empty)),
                    empty,
                ),
            ),
            scan_conclusion,
        )()
        self.plan_from_step = DeductionPlan(
            self.scan_law,
            step_pattern,
            M.Pair(
                M.Pair(
                    self.scan_cursor_index_spec,
                    M.Pair(scan_pattern, empty),
                ),
                M.Pair(
                    M.Pair(self.arc_index_spec, M.Pair(arc_pattern, empty)),
                    empty,
                ),
            ),
            scan_conclusion,
        )()
        self.plan_from_arc = DeductionPlan(
            self.scan_law,
            arc_pattern,
            M.Pair(
                M.Pair(
                    self.scan_state_index_spec, M.Pair(scan_pattern, empty),
                ),
                M.Pair(
                    M.Pair(self.step_index_spec, M.Pair(step_pattern, empty)),
                    empty,
                ),
            ),
            scan_conclusion,
        )()
        self.plan_sense_from_scan = DeductionPlan(
            self.sense_law,
            scan_pattern,
            M.Pair(
                M.Pair(self.sense_index_spec, M.Pair(sense_pattern, empty)),
                empty,
            ),
            reading_conclusion,
        )()
        self.plan_sense_from_sense = DeductionPlan(
            self.sense_law,
            sense_pattern,
            M.Pair(
                M.Pair(
                    self.scan_state_index_spec, M.Pair(scan_pattern, empty),
                ),
                empty,
            ),
            reading_conclusion,
        )()
        self.plan_from_left_daughter = DeductionPlan(
            self.compose_law,
            reading_a_pattern,
            M.Pair(
                M.Pair(
                    self.production_left_index_spec,
                    M.Pair(production_pattern, empty),
                ),
                M.Pair(
                    M.Pair(
                        self.reading_start_index_spec,
                        M.Pair(reading_b_pattern, empty),
                    ),
                    empty,
                ),
            ),
            compose_conclusion,
        )()
        self.plan_from_right_daughter = DeductionPlan(
            self.compose_law,
            reading_b_pattern,
            M.Pair(
                M.Pair(
                    self.production_right_index_spec,
                    M.Pair(production_pattern, empty),
                ),
                M.Pair(
                    M.Pair(
                        self.reading_end_index_spec,
                        M.Pair(reading_a_pattern, empty),
                    ),
                    empty,
                ),
            ),
            compose_conclusion,
        )()
        self.plans = M.Pair(
            self.plan_from_scan,
            M.Pair(
                self.plan_from_step,
                M.Pair(
                    self.plan_from_arc,
                    M.Pair(
                        self.plan_sense_from_scan,
                        M.Pair(
                            self.plan_sense_from_sense,
                            M.Pair(
                                self.plan_from_left_daughter,
                                M.Pair(self.plan_from_right_daughter, empty),
                            ),
                        ),
                    ),
                ),
            ),
        )

        plans_by_trigger = empty
        plans_by_trigger = Tmod.IdentityRedBlackInsert(
            plans_by_trigger,
            Lmod.FormScanLabel,
            M.Pair(
                self.plan_from_scan,
                M.Pair(self.plan_sense_from_scan, empty),
            ),
        )()
        plans_by_trigger = Tmod.IdentityRedBlackInsert(
            plans_by_trigger,
            Lmod.ObservedSymbolStepLabel,
            M.Pair(self.plan_from_step, empty),
        )()
        plans_by_trigger = Tmod.IdentityRedBlackInsert(
            plans_by_trigger,
            Lmod.FormArcLabel,
            M.Pair(self.plan_from_arc, empty),
        )()
        plans_by_trigger = Tmod.IdentityRedBlackInsert(
            plans_by_trigger,
            Lmod.FormSenseLabel,
            M.Pair(self.plan_sense_from_sense, empty),
        )()
        self._plans_by_trigger = Tmod.IdentityRedBlackInsert(
            plans_by_trigger,
            Lmod.ReadingLabel,
            M.Pair(
                self.plan_from_left_daughter,
                M.Pair(self.plan_from_right_daughter, empty),
            ),
        )()

        registry = empty
        specs_walker = self.index_specs
        while M.IdentityCompare(specs_walker, empty)() is M.false_value:
            spec = M.Head(specs_walker)()
            registry = M.Pair(M.Pair(spec, M.Pair(empty, empty)), registry)
            specs_walker = M.Tail(specs_walker)()
        self._index_registry = M.Reverse(registry)()

        self._agenda = empty
        self._firings_reversed = empty
        self._readings_reversed = empty
        self._root_state = root

        remaining = steps
        while M.IdentityCompare(remaining, empty)() is M.false_value:
            self._insert(M.Head(remaining)())
            remaining = M.Tail(remaining)()
        remaining = arcs
        while M.IdentityCompare(remaining, empty)() is M.false_value:
            self._insert(M.Head(remaining)())
            remaining = M.Tail(remaining)()
        remaining = senses
        while M.IdentityCompare(remaining, empty)() is M.false_value:
            self._insert(M.Head(remaining)())
            remaining = M.Tail(remaining)()
        remaining = productions
        while M.IdentityCompare(remaining, empty)() is M.false_value:
            self._insert(M.Head(remaining)())
            remaining = M.Tail(remaining)()
        remaining = steps
        while M.IdentityCompare(remaining, empty)() is M.false_value:
            cursor = ObservedStepBefore(M.Head(remaining)())()
            self._insert(FormScan(root, cursor, cursor)())
            remaining = M.Tail(remaining)()

        self._steps_index_root = self._root_for(self.step_index_spec)
        self._arcs_index_root = self._root_for(self.arc_index_spec)
        self._senses_index_root = self._root_for(self.sense_index_spec)

        self._drain_agenda()
        self._assemble_result()
        super().__init__(
            inputs=M.Pair(
                steps,
                M.Pair(
                    arcs,
                    M.Pair(
                        senses, M.Pair(root, M.Pair(productions, empty)),
                    ),
                ),
            ),
            results=self.result,
        )

    def _drain_agenda(self):
        empty = M.EmptyList
        while M.IdentityCompare(self._agenda, empty)() is M.false_value:
            fact = M.Head(self._agenda)()
            self._agenda = M.Tail(self._agenda)()
            self.delta_popped_text = GMPSuccText(self.delta_popped_text)()
            label = M.Head(fact)()
            held_plans = self._lookup(self._plans_by_trigger, label)
            walker = held_plans
            while M.IdentityCompare(walker, empty)() is M.false_value:
                self._execute_plan(M.Head(walker)(), fact)
                walker = M.Tail(walker)()

    def _assemble_result(self):
        self._steps_index_root = self._root_for(self.step_index_spec)
        self._arcs_index_root = self._root_for(self.arc_index_spec)
        self._senses_index_root = self._root_for(self.sense_index_spec)
        self.result = M.Pair(
            M.Reverse(self._readings_reversed)(),
            M.Pair(
                M.Reverse(self._firings_reversed)(),
                M.Pair(DeltaAgenda(self._agenda)(), M.EmptyList),
            ),
        )

    def Observe(self, utterance, before, symbol, after):
        """One observed symbol event, and the root scan it seeds.

        The client's whole contract: report each symbol as it arrives.
        The step enters through the same insert as every fact, and the
        cursor's scan is seeded whether or not one was there -- the
        dedupe decides. Drain afterwards to run the delta.
        """
        self._insert(ObservedSymbolStep(utterance, before, symbol, after)())
        return self._insert(FormScan(self._root_state, before, before)())

    def Drain(self):
        """Run the delta agenda to quiescence; the readings so far are
        the result. A conversation keeps arriving; this is how it does
        so without repaying the parse.
        """
        self._drain_agenda()
        self._assemble_result()
        return self.result

    def Learn(self, arcs, senses):
        """Teach lexicon facts mid-conversation.

        Arcs and senses enter through the same insert as every fact,
        the delta agenda carries them, and the drain completes the
        chart -- nothing re-observes, nothing restarts, and the
        counters show only the new work.
        """
        arcs_walker = arcs
        while M.IdentityCompare(arcs_walker, M.EmptyList)() is M.false_value:
            self._insert(M.Head(arcs_walker)())
            arcs_walker = M.Tail(arcs_walker)()
        senses_walker = senses
        while M.IdentityCompare(senses_walker, M.EmptyList)() is M.false_value:
            self._insert(M.Head(senses_walker)())
            senses_walker = M.Tail(senses_walker)()
        return self.Drain()

    def _lookup(self, tree, key):
        self.index_lookups_text = GMPSuccText(self.index_lookups_text)()
        return Tmod.IdentityRedBlackLookupValue(tree, key)()

    def _root_for(self, spec):
        walker = self._index_registry
        while M.IdentityCompare(walker, M.EmptyList)() is M.false_value:
            entry = M.Head(walker)()
            if M.IdentityCompare(M.Head(entry)(), spec)() is M.truth_value:
                return M.Head(M.Tail(entry)())()
            walker = M.Tail(walker)()
        return M.EmptyList

    def _arg_at(self, args, position_text):
        counter = "0"
        walker = args
        while M.IdentityCompare(walker, M.EmptyList)() is M.false_value:
            if GMPEqualText(counter, position_text)() is M.truth_value:
                return M.Head(walker)()
            counter = GMPSuccText(counter)()
            walker = M.Tail(walker)()
        return M.EmptyList

    def _binding(self, bindings, variable):
        walker = bindings
        while M.IdentityCompare(walker, M.EmptyList)() is M.false_value:
            entry = M.Head(walker)()
            if M.IdentityCompare(
                M.Head(entry)(), variable,
            )() is M.truth_value:
                return M.Tail(entry)()
            walker = M.Tail(walker)()
        return M.false_value

    def _keys_from_fact(self, spec, fact):
        keys_reversed = M.EmptyList
        walker = M.Head(M.Tail(M.Tail(spec)())())()
        while M.IdentityCompare(walker, M.EmptyList)() is M.false_value:
            keys_reversed = M.Pair(
                self._arg_at(
                    M.Tail(fact)(), M.GMPRepText(M.Head(walker)())(),
                ),
                keys_reversed,
            )
            walker = M.Tail(walker)()
        return M.Reverse(keys_reversed)()

    def _keys_from_pattern(self, spec, pattern, bindings):
        keys_reversed = M.EmptyList
        walker = M.Head(M.Tail(M.Tail(spec)())())()
        while M.IdentityCompare(walker, M.EmptyList)() is M.false_value:
            variable = self._arg_at(
                M.Tail(pattern)(), M.GMPRepText(M.Head(walker)())(),
            )
            value = self._binding(bindings, variable)
            if value is M.false_value:
                return M.false_value
            keys_reversed = M.Pair(value, keys_reversed)
            walker = M.Tail(walker)()
        return M.Reverse(keys_reversed)()

    def _index_lookup(self, spec, keys):
        tree = self._root_for(spec)
        walker = keys
        while M.IdentityCompare(walker, M.EmptyList)() is M.false_value:
            if M.IdentityCompare(tree, M.EmptyList)() is M.truth_value:
                return M.EmptyList
            tree = self._lookup(tree, M.Head(walker)())
            walker = M.Tail(walker)()
        return tree

    def _index_insert(self, tree, keys, fact):
        key = M.Head(keys)()
        rest = M.Tail(keys)()
        if M.IdentityCompare(rest, M.EmptyList)() is M.truth_value:
            held = self._lookup(tree, key)
            if M.IdentityCompare(held, M.EmptyList)() is M.truth_value:
                held = M.EmptyList
            return Tmod.IdentityRedBlackInsert(
                tree, key, M.Pair(fact, held),
            )()
        subtree = self._lookup(tree, key)
        if M.IdentityCompare(subtree, M.EmptyList)() is M.truth_value:
            subtree = M.EmptyList
        return Tmod.IdentityRedBlackInsert(
            tree, key, self._index_insert(subtree, rest, fact),
        )()

    def _insert(self, fact):
        label = M.Head(fact)()

        walker = self._index_registry
        while M.IdentityCompare(walker, M.EmptyList)() is M.false_value:
            entry = M.Head(walker)()
            spec = M.Head(entry)()
            if M.IdentityCompare(
                M.Head(M.Tail(spec)())(), label,
            )() is M.truth_value:
                keys = self._keys_from_fact(spec, fact)
                held = self._index_lookup(spec, keys)
                seen_walker = held
                while M.IdentityCompare(
                    seen_walker, M.EmptyList,
                )() is M.false_value:
                    if M.TermEqual(M.Head(seen_walker)(), fact)() is M.truth_value:
                        return M.false_value
                    seen_walker = M.Tail(seen_walker)()
                walker = M.EmptyList
            else:
                walker = M.Tail(walker)()

        updated = M.EmptyList
        walker = self._index_registry
        while M.IdentityCompare(walker, M.EmptyList)() is M.false_value:
            entry = M.Head(walker)()
            spec = M.Head(entry)()
            root = M.Head(M.Tail(entry)())()
            if M.IdentityCompare(
                M.Head(M.Tail(spec)())(), label,
            )() is M.truth_value:
                root = self._index_insert(
                    root, self._keys_from_fact(spec, fact), fact,
                )
            updated = M.Pair(
                M.Pair(spec, M.Pair(root, M.EmptyList)), updated,
            )
            walker = M.Tail(walker)()
        self._index_registry = M.Reverse(updated)()

        if M.IdentityCompare(label, Lmod.ReadingLabel)() is M.truth_value:
            self._readings_reversed = M.Pair(fact, self._readings_reversed)

        self.facts_inserted_text = GMPSuccText(self.facts_inserted_text)()
        self._agenda = M.Pair(fact, self._agenda)
        return M.truth_value

    def _match_pattern(self, pattern, fact, bindings):
        pattern_args = M.Tail(pattern)()
        fact_args = M.Tail(fact)()
        extended = bindings
        while M.IdentityCompare(pattern_args, M.EmptyList)() is M.false_value:
            if M.IdentityCompare(fact_args, M.EmptyList)() is M.truth_value:
                return M.false_value
            pattern_arg = M.Head(pattern_args)()
            fact_arg = M.Head(fact_args)()
            if M.IsPair(pattern_arg)() is M.truth_value:
                if M.IdentityCompare(
                    M.Head(pattern_arg)(), M.VarTag,
                )() is M.truth_value:
                    bound = self._binding(extended, pattern_arg)
                    if bound is M.false_value:
                        extended = M.Pair(
                            M.Pair(pattern_arg, fact_arg), extended,
                        )
                    else:
                        if M.IdentityCompare(
                            bound, fact_arg,
                        )() is M.false_value:
                            return M.false_value
                else:
                    if M.IdentityCompare(
                        pattern_arg, fact_arg,
                    )() is M.false_value:
                        return M.false_value
            else:
                if M.IdentityCompare(
                    pattern_arg, fact_arg,
                )() is M.false_value:
                    return M.false_value
            pattern_args = M.Tail(pattern_args)()
            fact_args = M.Tail(fact_args)()
        if M.IdentityCompare(fact_args, M.EmptyList)() is M.false_value:
            return M.false_value
        return extended

    def _execute_plan(self, plan, fact):
        law = M.Head(M.Tail(plan)())()
        trigger = M.Head(M.Tail(M.Tail(plan)())())()
        bindings = self._match_pattern(trigger, fact, M.EmptyList)
        if bindings is M.false_value:
            return
        steps = M.Head(M.Tail(M.Tail(M.Tail(plan)())())())()
        conclusion = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(plan)())())())())()
        self._run_steps(
            steps, bindings, M.Pair(fact, M.EmptyList), conclusion, law,
        )

    def _run_steps(self, steps, bindings, premises, conclusion, law):
        if M.IdentityCompare(steps, M.EmptyList)() is M.truth_value:
            self._conclude(conclusion, bindings, premises, law)
            return
        step = M.Head(steps)()
        spec = M.Head(step)()
        pattern = M.Head(M.Tail(step)())()
        keys = self._keys_from_pattern(spec, pattern, bindings)
        if keys is M.false_value:
            return
        held = self._index_lookup(spec, keys)
        walker = held
        while M.IdentityCompare(walker, M.EmptyList)() is M.false_value:
            candidate = M.Head(walker)()
            self.facts_returned_text = GMPSuccText(self.facts_returned_text)()
            extended = self._match_pattern(pattern, candidate, bindings)
            if extended is not M.false_value:
                self._run_steps(
                    M.Tail(steps)(),
                    extended,
                    M.Pair(candidate, premises),
                    conclusion,
                    law,
                )
            walker = M.Tail(walker)()

    def _conclude(self, conclusion, bindings, premises, law):
        args_reversed = M.EmptyList
        walker = M.Tail(conclusion)()
        while M.IdentityCompare(walker, M.EmptyList)() is M.false_value:
            built = self._build_arg(M.Head(walker)(), bindings)
            if built is M.false_value:
                return
            args_reversed = M.Pair(built, args_reversed)
            walker = M.Tail(walker)()
        fact = M.Pair(M.Head(conclusion)(), M.Reverse(args_reversed)())
        self.conclusions_attempted_text = GMPSuccText(
            self.conclusions_attempted_text,
        )()
        if self._insert(fact) is M.truth_value:
            self.new_conclusions_text = GMPSuccText(self.new_conclusions_text)()
            self._firings_reversed = M.Pair(
                IndexedFiring(law, premises, bindings, fact)(),
                self._firings_reversed,
            )

    def _build_arg(self, arg, bindings):
        if M.IsPair(arg)() is M.truth_value:
            if M.IdentityCompare(M.Head(arg)(), M.VarTag)() is M.truth_value:
                value = self._binding(bindings, arg)
                if value is M.false_value:
                    return M.false_value
                return value
            if M.IdentityCompare(
                M.Head(arg)(), Lmod.ComposeMeaningLabel,
            )() is M.truth_value:
                meaning = self._compose_meaning(arg, bindings)
                if meaning is M.false_value:
                    return M.false_value
                return self._build_arg(meaning, bindings)
            if M.IdentityCompare(
                M.Head(arg)(), Lmod.DefinitionMeaningLabel,
            )() is M.truth_value:
                return self._definition_meaning(arg)
            head_built = self._build_arg(M.Head(arg)(), bindings)
            if head_built is M.false_value:
                return M.false_value
            tail_built = self._build_arg(M.Tail(arg)(), bindings)
            if tail_built is M.false_value:
                return M.false_value
            return M.Pair(head_built, tail_built)
        return arg

    def _compose_meaning(self, marker, bindings):
        start = self._binding(bindings, self._compose_start_var)
        middle = self._binding(bindings, self._compose_mid_var)
        end = self._binding(bindings, self._compose_end_var)
        if start is M.false_value or middle is M.false_value:
            return M.false_value
        if end is M.false_value:
            return M.false_value
        if M.IdentityCompare(start, middle)() is M.truth_value:
            return M.false_value
        if M.IdentityCompare(middle, end)() is M.truth_value:
            return M.false_value
        template_var = M.Head(M.Tail(marker)())()
        left_var = M.Head(M.Tail(M.Tail(marker)())())()
        right_var = M.Head(M.Tail(M.Tail(M.Tail(marker)())())())()
        template = self._binding(bindings, template_var)
        left_meaning = self._binding(bindings, left_var)
        right_meaning = self._binding(bindings, right_var)
        if template is M.false_value:
            return M.false_value
        if left_meaning is M.false_value:
            return M.false_value
        if right_meaning is M.false_value:
            return M.false_value
        inner_template = template
        right_first = M.false_value
        if M.IsPair(template)() is M.truth_value:
            if M.IdentityCompare(
                M.Head(template)(), Lmod.ProjectRightLabel,
            )() is M.truth_value:
                inner_template = M.Head(M.Tail(template)())()
                right_first = M.truth_value
        scope = M.GMPRep(self.freshen_count_text)
        self.freshen_count_text = GMPSuccText(self.freshen_count_text)()
        fresh = FreshenTemplate(inner_template, scope)
        fresh_bindings = M.EmptyList
        walker = fresh.bindings_chain
        slot = "0"
        while M.IdentityCompare(walker, M.EmptyList)() is M.false_value:
            entry = M.Head(walker)()
            fresh_variable = M.Tail(entry)()
            if GMPEqualText(slot, "0")() is M.truth_value:
                if right_first is M.truth_value:
                    fresh_bindings = M.Pair(
                        M.Pair(fresh_variable, right_meaning), fresh_bindings,
                    )
                else:
                    fresh_bindings = M.Pair(
                        M.Pair(fresh_variable, left_meaning), fresh_bindings,
                    )
            else:
                if right_first is M.truth_value:
                    fresh_bindings = M.Pair(
                        M.Pair(fresh_variable, left_meaning), fresh_bindings,
                    )
                else:
                    fresh_bindings = M.Pair(
                        M.Pair(fresh_variable, right_meaning), fresh_bindings,
                    )
            slot = GMPSuccText(slot)()
            walker = M.Tail(walker)()
        return self._instantiate(fresh.instantiated, fresh_bindings)

    def _definition_meaning(self, marker):
        """The definition production: one scope, one self, and the graph.

        The grammar hands over one of two shapes. With the head-noun
        order -- "a prime number is divisible..." -- the left daughter
        is LexicalNp(concept, Pair(category, Pair(presuppositions,
        EmptyList))) and the right is the predicate chain. With the
        predicate-nominal order -- "a prime is a number divisible..."
        -- the left daughter is the bare concept and the right is
        Pair(chunk, predicate-chain), the category riding after the
        copula. This side allocates what no template can: the scope and
        the fresh self. The noun's presuppositions become conditions
        over that self; the reflexives among the fillers resolve to it,
        so "one and itself" and "itself and one" both read with one
        variable object in the application and the restriction alike --
        and the sample application pairs the self with the filler that
        is not itself, whichever order was spoken. The restriction
        becomes ExactFillers(relation, self, role, fillers) rather than
        a quantifier, because the parser records what was said and
        normalization is a law's job.
        """
        left = M.Head(M.Tail(marker)())()
        right = M.Head(M.Tail(M.Tail(marker)())())()
        if M.IdentityCompare(
            M.Tail(M.Tail(M.Tail(marker)())())(), M.EmptyList,
        )() is M.false_value:
            return M.false_value
        predicate_chain = M.EmptyList
        if M.IsPair(left)() is M.truth_value:
            if M.IdentityCompare(
                M.Head(left)(), Lmod.HoleLabel,
            )() is M.truth_value:
                concept = left
                if M.IsPair(right)() is M.false_value:
                    return M.false_value
                chunk = M.Head(right)()
                predicate_chain = M.Head(M.Tail(right)())()
                if M.IdentityCompare(
                    M.Tail(M.Tail(right)())(), M.EmptyList,
                )() is M.false_value:
                    return M.false_value
            elif M.IdentityCompare(
                M.Head(left)(), Lmod.LexicalNpLabel,
            )() is M.false_value:
                return M.false_value
            else:
                concept = M.Head(M.Tail(left)())()
                chunk = M.Head(M.Tail(M.Tail(left)())())()
                predicate_chain = right
        else:
            concept = left
            if M.IsPair(right)() is M.false_value:
                return M.false_value
            chunk = M.Head(right)()
            predicate_chain = M.Head(M.Tail(right)())()
            if M.IdentityCompare(
                M.Tail(M.Tail(right)())(), M.EmptyList,
            )() is M.false_value:
                return M.false_value
        if M.IsPair(chunk)() is M.false_value:
            return M.false_value
        category = M.Head(chunk)()
        presuppositions = M.Tail(chunk)()
        if M.IdentityCompare(predicate_chain, M.EmptyList)() is M.truth_value:
            return M.false_value
        relation = M.Head(predicate_chain)()
        rest = M.Tail(predicate_chain)()
        if M.IdentityCompare(rest, M.EmptyList)() is M.truth_value:
            return M.false_value
        restriction = M.Head(rest)()
        if M.IdentityCompare(M.Tail(rest)(), M.EmptyList)() is M.false_value:
            return M.false_value
        if M.IsPair(restriction)() is M.false_value:
            return M.false_value
        if M.IdentityCompare(
            M.Head(restriction)(), Lmod.RestrictionLabel,
        )() is M.false_value:
            return M.false_value
        role = M.Head(M.Tail(restriction)())()
        fillers = M.Head(M.Tail(M.Tail(restriction)())())()
        if M.IdentityCompare(fillers, M.EmptyList)() is M.truth_value:
            return M.false_value

        scope = M.GMPRep(self.definition_count_text)
        self.definition_count_text = GMPSuccText(self.definition_count_text)()
        self_variable = M.Pair(
            M.VarTag, M.Pair(scope, M.Pair(M.Char("?self"), M.EmptyList)),
        )
        resolved_fillers = ResolveReflexives(fillers, self_variable)()
        chosen_filler = M.EmptyList
        filler_walker = resolved_fillers
        while M.IdentityCompare(filler_walker, M.EmptyList)() is M.false_value:
            candidate_filler = M.Head(filler_walker)()
            if M.IdentityCompare(
                candidate_filler, self_variable,
            )() is M.false_value:
                chosen_filler = candidate_filler
                filler_walker = M.EmptyList
            else:
                filler_walker = M.Tail(filler_walker)()
        if M.IdentityCompare(chosen_filler, M.EmptyList)() is M.truth_value:
            chosen_filler = M.Head(resolved_fillers)()

        conditions_reversed = M.Pair(
            M.Pair(
                Lmod.ExactFillersLabel,
                M.Pair(
                    relation,
                    M.Pair(
                        self_variable,
                        M.Pair(role, M.Pair(resolved_fillers, M.EmptyList)),
                    ),
                ),
            ),
            M.EmptyList,
        )
        conditions_reversed = M.Pair(
            M.Pair(
                relation,
                M.Pair(
                    chosen_filler,
                    M.Pair(self_variable, M.EmptyList),
                ),
            ),
            conditions_reversed,
        )
        walker = presuppositions
        while M.IdentityCompare(walker, M.EmptyList)() is M.false_value:
            condition_marker = M.Head(walker)()
            conditions_reversed = M.Pair(
                M.Pair(
                    M.Head(condition_marker)(),
                    M.Pair(self_variable, M.EmptyList),
                ),
                conditions_reversed,
            )
            walker = M.Tail(walker)()
        conditions = conditions_reversed

        definiendum = M.Pair(
            Lmod.DefiniendumLabel,
            M.Pair(concept, M.Pair(category, M.EmptyList)),
        )
        return DefinitionNode(
            definiendum, Binder(scope, self_variable)(), conditions,
        )()

    def _instantiate(self, term, bindings):
        if M.IsPair(term)() is M.truth_value:
            if M.IdentityCompare(M.Head(term)(), M.VarTag)() is M.truth_value:
                value = self._binding(bindings, term)
                if value is M.false_value:
                    return term
                return value
            return M.Pair(
                self._instantiate(M.Head(term)(), bindings),
                self._instantiate(M.Tail(term)(), bindings),
            )
        return term

    def __call__(self):
        return self.result


class ReadingPolicy(M.Edge):
    """What counts as a word, stated as data rather than as string surgery.

    Pair(ReadingPolicyLabel, Pair(separators, Pair(discarded,
    Pair(standalone, Pair(foldings, EmptyList))))).

    Reading a typed line used to be a chain of host replaces: lowercase
    the line, blank out the sentence punctuation, pad the brackets and
    the comma with spaces, split on whitespace, spell out any word that
    is all digits. Six decisions about what a word is, made in Python
    before the machine saw anything, and none of them stateable,
    retirable or learnable. A pack that wanted a semicolon for a
    separator would have had to edit the reader.

    Each of those decisions is a chain here. Separators end a word.
    Discarded characters end a word and are dropped. Standalone
    characters end a word and are one themselves -- which is the whole
    of why a comma is a word. Foldings say which character stands for
    which, so case is a correspondence rather than a method call.
    """

    def __init__(self, separators, discarded, standalone, foldings):
        self.result = M.Pair(
            Lmod.ReadingPolicyLabel,
            M.Pair(
                separators,
                M.Pair(discarded, M.Pair(standalone, M.Pair(foldings, M.EmptyList))),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                separators,
                M.Pair(discarded, M.Pair(standalone, M.Pair(foldings, M.EmptyList))),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class ReadingPolicySeparators(M.Edge):
    def __init__(self, policy):
        self.result = M.Head(M.Tail(policy)())()
        super().__init__(inputs=M.Pair(policy, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ReadingPolicyDiscarded(M.Edge):
    def __init__(self, policy):
        self.result = M.Head(M.Tail(M.Tail(policy)())())()
        super().__init__(inputs=M.Pair(policy, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ReadingPolicyStandalone(M.Edge):
    def __init__(self, policy):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(policy)())())())()
        super().__init__(inputs=M.Pair(policy, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ReadingPolicyFoldings(M.Edge):
    def __init__(self, policy):
        self.result = M.Head(
            M.Tail(M.Tail(M.Tail(M.Tail(policy)())())())(),
        )()
        super().__init__(inputs=M.Pair(policy, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class DefaultReadingPolicy(M.Edge):
    """The reader's own decisions, as the chains a pack could replace.

    These reproduce exactly what the host replaces used to do: space,
    tab and newline break a word; a full stop, question mark and
    exclamation mark break one and vanish; a bracket or a comma is a
    word standing alone; and each capital stands for its small letter.
    """

    def __init__(self):
        empty = M.EmptyList
        separators = M.Pair(
            M.Char(" "),
            M.Pair(M.Char("\t"), M.Pair(M.Char("\n"), M.Pair(M.Char("\r"), empty))),
        )
        discarded = M.Pair(
            M.Char("."),
            M.Pair(M.Char("?"), M.Pair(M.Char("!"), empty)),
        )
        standalone = M.Pair(
            M.Char("("),
            M.Pair(M.Char(")"), M.Pair(M.Char(","), empty)),
        )
        foldings = empty
        foldings = M.Pair(M.Pair(M.Char("Z"), M.Pair(M.Char("z"), empty)), foldings)
        foldings = M.Pair(M.Pair(M.Char("Y"), M.Pair(M.Char("y"), empty)), foldings)
        foldings = M.Pair(M.Pair(M.Char("X"), M.Pair(M.Char("x"), empty)), foldings)
        foldings = M.Pair(M.Pair(M.Char("W"), M.Pair(M.Char("w"), empty)), foldings)
        foldings = M.Pair(M.Pair(M.Char("V"), M.Pair(M.Char("v"), empty)), foldings)
        foldings = M.Pair(M.Pair(M.Char("U"), M.Pair(M.Char("u"), empty)), foldings)
        foldings = M.Pair(M.Pair(M.Char("T"), M.Pair(M.Char("t"), empty)), foldings)
        foldings = M.Pair(M.Pair(M.Char("S"), M.Pair(M.Char("s"), empty)), foldings)
        foldings = M.Pair(M.Pair(M.Char("R"), M.Pair(M.Char("r"), empty)), foldings)
        foldings = M.Pair(M.Pair(M.Char("Q"), M.Pair(M.Char("q"), empty)), foldings)
        foldings = M.Pair(M.Pair(M.Char("P"), M.Pair(M.Char("p"), empty)), foldings)
        foldings = M.Pair(M.Pair(M.Char("O"), M.Pair(M.Char("o"), empty)), foldings)
        foldings = M.Pair(M.Pair(M.Char("N"), M.Pair(M.Char("n"), empty)), foldings)
        foldings = M.Pair(M.Pair(M.Char("M"), M.Pair(M.Char("m"), empty)), foldings)
        foldings = M.Pair(M.Pair(M.Char("L"), M.Pair(M.Char("l"), empty)), foldings)
        foldings = M.Pair(M.Pair(M.Char("K"), M.Pair(M.Char("k"), empty)), foldings)
        foldings = M.Pair(M.Pair(M.Char("J"), M.Pair(M.Char("j"), empty)), foldings)
        foldings = M.Pair(M.Pair(M.Char("I"), M.Pair(M.Char("i"), empty)), foldings)
        foldings = M.Pair(M.Pair(M.Char("H"), M.Pair(M.Char("h"), empty)), foldings)
        foldings = M.Pair(M.Pair(M.Char("G"), M.Pair(M.Char("g"), empty)), foldings)
        foldings = M.Pair(M.Pair(M.Char("F"), M.Pair(M.Char("f"), empty)), foldings)
        foldings = M.Pair(M.Pair(M.Char("E"), M.Pair(M.Char("e"), empty)), foldings)
        foldings = M.Pair(M.Pair(M.Char("D"), M.Pair(M.Char("d"), empty)), foldings)
        foldings = M.Pair(M.Pair(M.Char("C"), M.Pair(M.Char("c"), empty)), foldings)
        foldings = M.Pair(M.Pair(M.Char("B"), M.Pair(M.Char("b"), empty)), foldings)
        foldings = M.Pair(M.Pair(M.Char("A"), M.Pair(M.Char("a"), empty)), foldings)
        self.result = ReadingPolicy(separators, discarded, standalone, foldings)()
        super().__init__(inputs=empty, results=self.result)

    def __call__(self):
        return self.result


class FoldCharacter(M.Edge):
    """The character this one stands for, or itself when nothing says."""

    def __init__(self, character, foldings):
        cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        self.result = character
        scan_text = "0"
        remaining = foldings
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                remaining = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                entry = M.Head(remaining)()
                if M.Compare(M.Head(entry)(), character)() is M.truth_value:
                    self.result = M.Head(M.Tail(entry)())()
                    remaining = M.EmptyList
                else:
                    remaining = M.Tail(remaining)()
        super().__init__(
            inputs=M.Pair(character, M.Pair(foldings, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class WordForDigitCharacter(M.Edge):
    """The number word a digit character names, or EmptyList.

    The inverse of SurfaceDigitOfWord, over the same chain, so the
    reader and the printer agree by construction about which digit is
    which word.
    """

    def __init__(self, character, digit_words):
        cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        self.result = M.EmptyList
        scan_text = "0"
        remaining = digit_words
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                remaining = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                entry = M.Head(remaining)()
                if M.Compare(M.Head(entry)(), character)() is M.truth_value:
                    self.result = M.Head(M.Tail(entry)())()
                    remaining = M.EmptyList
                else:
                    remaining = M.Tail(remaining)()
        super().__init__(
            inputs=M.Pair(character, M.Pair(digit_words, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class WordsOfStream(M.Edge):
    """A stream of characters as words, by the policy and nothing else.

    The host boundary and the word rule in one place, because splitting
    a line into one-character atoms and then concatenating them back
    into a word is ceremony: it allocates a Char and three identities
    per character to arrive at the string it started from. What the
    policy decides is data -- these chains -- and what the host does is
    read.

    Characters arrive one at a time from the stream, so no host
    container is walked. Each is folded through the policy, then asked
    of the policy's chains: a separator ends the run, a discarded
    character ends it and is gone, a standalone character ends it and
    is a word itself, which is the whole of why a comma is a word. A
    finished run that is entirely digits becomes one number word per
    digit through the same chain RenderNatSurface prints with, so
    reader and printer agree by construction; a run that is not stays
    whole, so e2 and sqrt2 survive.
    """

    def __init__(self, stream, policy, digit_words):
        separators = ReadingPolicySeparators(policy)()
        discarded = ReadingPolicyDiscarded(policy)()
        standalone = ReadingPolicyStandalone(policy)()
        foldings = ReadingPolicyFoldings(policy)()
        reversed_words = M.EmptyList
        run_text = ""
        run_digits = M.EmptyList
        all_digits = M.truth_value
        reading = M.truth_value
        while M.IdentityCompare(reading, M.truth_value)() is M.truth_value:
            symbol = stream.read(1)
            if symbol == "":
                reading = M.false_value
                character = M.Head(separators)()
            else:
                character = FoldCharacter(M.Char(symbol), foldings)()
            ends_run = M.false_value
            stands_alone = M.false_value
            if SurfaceChainHasWord(separators, character)() is M.truth_value:
                ends_run = M.truth_value
            elif SurfaceChainHasWord(discarded, character)() is M.truth_value:
                ends_run = M.truth_value
            elif SurfaceChainHasWord(standalone, character)() is M.truth_value:
                ends_run = M.truth_value
                stands_alone = M.truth_value
            if M.IdentityCompare(ends_run, M.false_value)() is M.truth_value:
                digit_word = WordForDigitCharacter(character, digit_words)()
                if M.IdentityCompare(digit_word, M.EmptyList)() is M.truth_value:
                    all_digits = M.false_value
                else:
                    run_digits = M.Pair(digit_word, run_digits)
                run_text = run_text + character()
            else:
                if run_text != "":
                    if M.IdentityCompare(all_digits, M.truth_value)() is M.truth_value:
                        spelled = M.Reverse(run_digits)()
                        while M.IdentityCompare(
                            spelled, M.EmptyList,
                        )() is M.false_value:
                            reversed_words = M.Pair(
                                M.Head(spelled)(), reversed_words,
                            )
                            spelled = M.Tail(spelled)()
                    else:
                        reversed_words = M.Pair(M.Char(run_text), reversed_words)
                run_text = ""
                run_digits = M.EmptyList
                all_digits = M.truth_value
                if M.IdentityCompare(stands_alone, M.truth_value)() is M.truth_value:
                    reversed_words = M.Pair(character, reversed_words)
        self.result = M.Reverse(reversed_words)()
        super().__init__(
            inputs=M.Pair(policy, M.Pair(digit_words, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class WordsOfText(M.Edge):
    """Host text as words: the one place a stream is made of a string."""

    def __init__(self, text, policy, digit_words):
        self.result = WordsOfStream(io.StringIO(text), policy, digit_words)()
        super().__init__(
            inputs=M.Pair(policy, M.Pair(digit_words, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class WordChainWithout(M.Edge):
    """The words of a chain that are not in `unwanted`."""

    def __init__(self, words, unwanted):
        reversed_kept = M.EmptyList
        remaining = words
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            word = M.Head(remaining)()
            if SurfaceChainHasWord(unwanted, word)() is M.false_value:
                reversed_kept = M.Pair(word, reversed_kept)
            remaining = M.Tail(remaining)()
        self.result = M.Reverse(reversed_kept)()
        super().__init__(
            inputs=M.Pair(words, M.Pair(unwanted, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SoleWord(M.Edge):
    """The one word of a chain, or EmptyList when there is not exactly one.

    "what is a triangle" asks about one term. Reading that used to be a
    host comprehension over a host list and a length check; the question
    it answers is about a chain, and this is that question.
    """

    def __init__(self, words):
        self.result = M.EmptyList
        if M.IdentityCompare(words, M.EmptyList)() is M.false_value:
            if M.IdentityCompare(M.Tail(words)(), M.EmptyList)() is M.truth_value:
                self.result = M.Head(words)()
        super().__init__(
            inputs=M.Pair(words, M.EmptyList), results=self.result,
        )

    def __call__(self):
        return self.result


class DefinitionTermAndBody(M.Edge):
    """Split "a triangle is a polygon ..." into its term and its body.

    Leading articles are skipped, the next word is the term being
    defined, a copula after it is dropped, and what remains is the body.
    Returns Pair(term, Pair(body, EmptyList)), or EmptyList when there
    is no term or no body left to define it with.

    The console did this by walking an index over a host list and
    slicing it, then building the very chain it had just taken apart.
    The articles and the copulas are chains here, so a reader that says
    "one triangle is ..." is a longer chain rather than a longer tuple
    in Python.
    """

    def __init__(self, words, articles, copulas):
        self.result = M.EmptyList
        remaining = words
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if SurfaceChainHasWord(articles, M.Head(remaining)())() is M.truth_value:
                remaining = M.Tail(remaining)()
            else:
                term = M.Head(remaining)()
                body = M.Tail(remaining)()
                if M.IdentityCompare(body, M.EmptyList)() is M.false_value:
                    if SurfaceChainHasWord(
                        copulas, M.Head(body)(),
                    )() is M.truth_value:
                        body = M.Tail(body)()
                if M.IdentityCompare(body, M.EmptyList)() is M.false_value:
                    self.result = M.Pair(term, M.Pair(body, M.EmptyList))
                remaining = M.EmptyList
        super().__init__(
            inputs=M.Pair(
                words, M.Pair(articles, M.Pair(copulas, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SurfaceOfText(M.Edge):
    """A typed line as a Surface, through the policy."""

    def __init__(self, text, policy, digit_words):
        self.words = WordsOfText(text, policy, digit_words)()
        self.result = Surface(self.words)()
        super().__init__(
            inputs=M.Pair(policy, M.Pair(digit_words, M.EmptyList)),
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


CORRESPONDENCE_SCAN_CAP = M.GMPRep("200")


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
        var_c = M.Pair(M.VarTag, M.Pair(M.Char("?c"), empty))

        # A definition body is a sentence, so it is read the way every
        # other sentence is read: by correspondence templates that are
        # themselves laws. The relation words were a host list and the
        # parse a hand-written state machine; each shape below is one law
        # instead, so a new phrasing is a new template rather than a new
        # branch, and induction can learn one from examples.
        genus_meaning = Meaning(
            M.Pair(
                M.DefinitionGenusLabel,
                M.Pair(Surface(M.Pair(var_a, empty))(), empty),
            ),
        )()
        counted_meaning = Meaning(
            M.Pair(
                M.DefinitionCountedLabel,
                M.Pair(
                    Surface(M.Pair(var_a, empty))(),
                    M.Pair(
                        Surface(M.Pair(var_b, empty))(),
                        M.Pair(Surface(M.Pair(var_c, empty))(), empty),
                    ),
                ),
            ),
        )()
        genus_body = Surface(M.Pair(M.Char("a"), M.Pair(var_a, empty)))()
        genus_body_bare = Surface(M.Pair(var_a, empty))()
        with_body = Surface(
            M.Pair(
                M.Char("a"),
                M.Pair(
                    var_a,
                    M.Pair(
                        M.Char("with"),
                        M.Pair(var_b, M.Pair(var_c, empty)),
                    ),
                ),
            ),
        )()
        having_body = Surface(
            M.Pair(
                M.Char("a"),
                M.Pair(
                    var_a,
                    M.Pair(
                        M.Char("having"),
                        M.Pair(var_b, M.Pair(var_c, empty)),
                    ),
                ),
            ),
        )()
        has_body = Surface(
            M.Pair(
                M.Char("a"),
                M.Pair(
                    var_a,
                    M.Pair(
                        M.Char("has"),
                        M.Pair(var_b, M.Pair(var_c, empty)),
                    ),
                ),
            ),
        )()
        whose_body = Surface(
            M.Pair(
                M.Char("a"),
                M.Pair(
                    var_a,
                    M.Pair(
                        M.Char("whose"),
                        M.Pair(var_b, M.Pair(var_c, empty)),
                    ),
                ),
            ),
        )()

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
        formal_mul_sentence = Surface(
            M.Pair(
                M.Char("mul"),
                M.Pair(
                    M.Char("("),
                    M.Pair(
                        var_a,
                        M.Pair(
                            M.Char(","),
                            M.Pair(var_b, M.Pair(M.Char(")"), empty)),
                        ),
                    ),
                ),
            ),
        )()
        formal_add_sentence = Surface(
            M.Pair(
                M.Char("add"),
                M.Pair(
                    M.Char("("),
                    M.Pair(
                        var_a,
                        M.Pair(
                            M.Char(","),
                            M.Pair(var_b, M.Pair(M.Char(")"), empty)),
                        ),
                    ),
                ),
            ),
        )()
        equal_meaning = Meaning(
            M.Pair(
                Lmod.EqualLabel,
                M.Pair(
                    Surface(M.Pair(var_a, empty))(),
                    M.Pair(Surface(M.Pair(var_b, empty))(), empty),
                ),
            ),
        )()
        real_meaning = Meaning(
            M.Pair(
                M.IsRealLabel,
                M.Pair(
                    M.Pair(
                        M.SqrtLabel,
                        M.Pair(Surface(M.Pair(var_a, empty))(), empty),
                    ),
                    empty,
                ),
            ),
        )()
        # A radicand may itself be a root. "sqrt ( X )" on its own is not a
        # sentence and has no value, so the group reducer had nothing to
        # splice and the whole sentence failed. As a phrase it does have a
        # meaning -- the Sqrt term -- which is exactly what the surrounding
        # slot wants.
        sqrt_phrase = Surface(
            M.Pair(
                M.Char("sqrt"),
                M.Pair(
                    M.Char("("),
                    M.Pair(var_a, M.Pair(M.Char(")"), empty)),
                ),
            ),
        )()
        # Once the inner group has reduced, the radicand is a spliced term and
        # the brackets are gone: the phrase reaching the reducer is "sqrt X",
        # not "sqrt ( X )". Both forms mean the same root.
        sqrt_bare_phrase = Surface(
            M.Pair(M.Char("sqrt"), M.Pair(var_a, empty)),
        )()
        sqrt_phrase_meaning = Meaning(
            M.Pair(
                M.SqrtLabel,
                M.Pair(Surface(M.Pair(var_a, empty))(), empty),
            ),
        )()
        equal_sentence = Surface(
            M.Pair(
                M.Char("is"),
                M.Pair(
                    var_a,
                    M.Pair(
                        M.Char("equal"),
                        M.Pair(M.Char("to"), M.Pair(var_b, empty)),
                    ),
                ),
            ),
        )()
        # An expression can sit in the equality's subject slot: "is two
        # plus two equal to four". The template matcher binds one word per
        # variable, so the composed phrasing is its own template, the same
        # rule the bracket-group reducer follows for primality subjects.
        # The meaning nests the sum inside the equality; evaluation runs
        # MeaningEvaluate recursively, so both sides reach Nats and NatEq
        # answers yes or no. D2, 2026-09-05.
        plus_equal_sentence = Surface(
            M.Pair(
                M.Char("is"),
                M.Pair(
                    var_a,
                    M.Pair(
                        M.Char("plus"),
                        M.Pair(
                            var_b,
                            M.Pair(
                                M.Char("equal"),
                                M.Pair(M.Char("to"), M.Pair(var_c, empty)),
                            ),
                        ),
                    ),
                ),
            ),
        )()
        plus_equal_meaning = Meaning(
            M.Pair(
                Lmod.EqualLabel,
                M.Pair(
                    M.Pair(
                        M.ExprAddLabel,
                        M.Pair(
                            Surface(M.Pair(var_a, empty))(),
                            M.Pair(Surface(M.Pair(var_b, empty))(), empty),
                        ),
                    ),
                    M.Pair(Surface(M.Pair(var_c, empty))(), empty),
                ),
            ),
        )()
        real_sentence = Surface(
            M.Pair(
                M.Char("is"),
                M.Pair(
                    M.Char("sqrt"),
                    M.Pair(
                        M.Char("("),
                        M.Pair(
                            var_a,
                            M.Pair(M.Char(")"), M.Pair(M.Char("real"), empty)),
                        ),
                    ),
                ),
            ),
        )()

        # The reducer strips the brackets it consumes, so a sentence whose
        # radicand was a group arrives as "is sqrt X real". The bracketed
        # form above still matches what the reader typed; this matches what
        # reduction leaves behind.
        real_bare_sentence = Surface(
            M.Pair(
                M.Char("is"),
                M.Pair(
                    M.Char("sqrt"),
                    M.Pair(var_a, M.Pair(M.Char("real"), empty)),
                ),
            ),
        )()

        even_meaning = Meaning(
            M.Pair(
                Lmod.EvenPropLabel,
                M.Pair(Surface(M.Pair(var_a, empty))(), empty),
            ),
        )()
        odd_meaning = Meaning(
            M.Pair(
                Lmod.OddPropLabel,
                M.Pair(Surface(M.Pair(var_a, empty))(), empty),
            ),
        )()
        even_sentence = Surface(
            M.Pair(
                M.Char("is"),
                M.Pair(var_a, M.Pair(M.Char("even"), empty)),
            ),
        )()
        odd_sentence = Surface(
            M.Pair(
                M.Char("is"),
                M.Pair(var_a, M.Pair(M.Char("odd"), empty)),
            ),
        )()

        def _task_meaning(task_name):
            return Meaning(
                M.Pair(Lmod.TaskLabel, M.Pair(M.Char(task_name), empty)),
            )()

        def _task_law(task_meaning_term, *symbols):
            chain = empty
            index = len(symbols)
            while index != 0:
                index = index - 1
                chain = M.Pair(M.Char(symbols[index]), chain)
            return CompileRuleToLaw(P.Rule(Surface(chain)(), task_meaning_term))()

        diagnostics_meaning = _task_meaning("self-diagnostics")
        tao_meaning = _task_meaning("tao")
        e1_meaning = _task_meaning("e1")
        e2_meaning = _task_meaning("e2")
        coins_meaning = _task_meaning("coins")
        sqrt_meaning = _task_meaning("sqrt")

        templates = M.Pair(
            CompileRuleToLaw(P.Rule(with_body, counted_meaning))(),
            M.Pair(
            CompileRuleToLaw(P.Rule(having_body, counted_meaning))(),
            M.Pair(
            CompileRuleToLaw(P.Rule(has_body, counted_meaning))(),
            M.Pair(
            CompileRuleToLaw(P.Rule(whose_body, counted_meaning))(),
            M.Pair(
            CompileRuleToLaw(P.Rule(genus_body, genus_meaning))(),
            M.Pair(
            CompileRuleToLaw(P.Rule(genus_body_bare, genus_meaning))(),
            M.Pair(
            CompileRuleToLaw(P.Rule(equal_sentence, equal_meaning))(),
            M.Pair(
                CompileRuleToLaw(
                    P.Rule(plus_equal_sentence, plus_equal_meaning),
                )(),
            M.Pair(
                CompileRuleToLaw(P.Rule(even_sentence, even_meaning))(),
            M.Pair(
                CompileRuleToLaw(P.Rule(odd_sentence, odd_meaning))(),
            M.Pair(
                CompileRuleToLaw(P.Rule(real_sentence, real_meaning))(),
                M.Pair(
                    CompileRuleToLaw(
                        P.Rule(sqrt_phrase, sqrt_phrase_meaning),
                    )(),
                M.Pair(
                    CompileRuleToLaw(
                        P.Rule(sqrt_bare_phrase, sqrt_phrase_meaning),
                    )(),
                M.Pair(
                    CompileRuleToLaw(
                        P.Rule(real_bare_sentence, real_meaning),
                    )(),
                M.Pair(
                    CompileRuleToLaw(P.Rule(sum_sentence, add_meaning))(),
                    M.Pair(
                        CompileRuleToLaw(P.Rule(product_sentence, mul_meaning))(),
                        M.Pair(
                            CompileRuleToLaw(P.Rule(plus_sentence, add_meaning))(),
                            M.Pair(
                                CompileRuleToLaw(
                                    P.Rule(times_sentence, mul_meaning),
                                )(),
                                M.Pair(
                                    CompileRuleToLaw(
                                        P.Rule(formal_mul_sentence, mul_meaning),
                                    )(),
                                    M.Pair(
                                        CompileRuleToLaw(
                                            P.Rule(formal_add_sentence, add_meaning),
                                        )(),
                                        M.Pair(
                                            _task_law(
                                                diagnostics_meaning,
                                                "run", "self-diagnostics",
                                            ),
                                            M.Pair(
                                                _task_law(
                                                    diagnostics_meaning,
                                                    "run", "the", "tests",
                                                ),
                                                M.Pair(
                                                    _task_law(
                                                        tao_meaning,
                                                        "solve", "the", "tao",
                                                        "triangle", "problem",
                                                    ),
                                                    M.Pair(
                                                        _task_law(
                                                            tao_meaning,
                                                            "solve", "tao",
                                                        ),
                                                        M.Pair(
                                                            _task_law(
                                                                e2_meaning,
                                                                "solve", "engel", "e2",
                                                            ),
                                                            M.Pair(
                                                                _task_law(
                                                                    e1_meaning,
                                                                    "solve", "engel", "e1",
                                                                ),
                                                                M.Pair(
                                                                    _task_law(
                                                                        coins_meaning,
                                                                        "solve", "the",
                                                                        "coin", "problem",
                                                                    ),
                                                                    M.Pair(
                                                                        _task_law(
                                                                            sqrt_meaning,
                                                                            "prove", "square",
                                                                            "roots", "are",
                                                                            "real",
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
                                ),
                            ),
                        ),
                    ),
                ),
            ),
            ),
            ),
            ),
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
                            else:
                                # Group reduction splices whole terms into the
                                # chain, so a one-element Surface may hold a
                                # Sqrt rather than a number word. Evaluate it
                                # as the term it is.
                                if M.IsPair(element)() is M.truth_value:
                                    return self._eval(
                                        element,
                                        registry,
                                        next_depth,
                                    )
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
                left_nat = M.IsNat(left_value, registry)()
                right_nat = M.IsNat(right_value, registry)()
                if M.AndAtom(left_nat, right_nat)() is M.false_value:
                    # A root has no Nat value and neither does a product
                    # or sum built on one. The operands are still perfectly
                    # good terms, so the expression is too: hand back the
                    # symbolic term, exactly as the Sqrt case below does.
                    return M.Pair(
                        M.Pair(
                            label,
                            M.Pair(
                                left_value,
                                M.Pair(right_value, M.EmptyList),
                            ),
                        ),
                        M.Pair(registry, M.EmptyList),
                    )
                if M.IdentityCompare(is_add, M.truth_value)() is M.truth_value:
                    return M.Add(left_value, right_value, registry)()
                return M.Multiply(left_value, right_value, registry)()
            if M.TermEqual(label, M.SqrtLabel)() is M.truth_value:
                # A root has no Nat value, but it is a perfectly good term and
                # the prover takes it as one. Evaluate the radicand so a
                # nested root loses its Surface wrappers at every depth, then
                # hand back the Sqrt term itself.
                inner_pair = self._eval(
                    M.Head(arguments)(),
                    registry,
                    next_depth,
                )
                inner_value = M.Head(inner_pair)()
                registry = M.Head(M.Tail(inner_pair)())()
                if M.IdentityCompare(
                    inner_value,
                    M.EmptyList,
                )() is M.truth_value:
                    return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
                return M.Pair(
                    M.Pair(
                        M.SqrtLabel,
                        M.Pair(inner_value, M.EmptyList),
                    ),
                    M.Pair(registry, M.EmptyList),
                )
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


class ConstructorSignature(M.Edge):
    """A constructor, the word that names it, and how many arguments it takes.

    Pair(SignatureLabel, Pair(word, Pair(constructor, Pair(arity, Empty)))).

    The formal notation "mul ( a , b )" was one hand-written template per
    constructor, so a constructor the packs knew about had no formal form
    until someone added a branch. A signature is that form as data:
    FormalProductions below turns it into a production of the grammar, so
    every constructor a pack emits is writable the moment it is loaded and
    nothing in the parser mentions it.
    """

    def __init__(self, word, constructor, arity):
        self.result = M.Pair(
            Lmod.SignatureLabel,
            M.Pair(
                word,
                M.Pair(constructor, M.Pair(arity, M.EmptyList)),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                word,
                M.Pair(constructor, M.Pair(arity, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SignatureWord(M.Edge):
    def __init__(self, signature):
        self.result = M.Head(M.Tail(signature)())()
        super().__init__(
            inputs=M.Pair(signature, M.EmptyList), results=self.result,
        )

    def __call__(self):
        return self.result


class SignatureConstructor(M.Edge):
    def __init__(self, signature):
        self.result = M.Head(M.Tail(M.Tail(signature)())())()
        super().__init__(
            inputs=M.Pair(signature, M.EmptyList), results=self.result,
        )

    def __call__(self):
        return self.result


class SignatureArity(M.Edge):
    def __init__(self, signature):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(signature)())())())()
        super().__init__(
            inputs=M.Pair(signature, M.EmptyList), results=self.result,
        )

    def __call__(self):
        return self.result


# The chart's own limits. A pass that adds nothing is the fixed point;
# CHART_PASS_CAP is what stops a grammar whose productions keep feeding
# each other, so a cycle in the productions is a bounded failure rather
# than a host recursion error.
CHART_PASS_CAP = M.GMPRep("50")

# The category the formal notation is written in. An argument is the
# same category as the whole application, which is the entire reason
# nesting needs no machinery.
CHART_TERM_CATEGORY = M.Char("term")

# The notation's function words. These carry no meaning of their own and
# no branch of their own: they appear in productions exactly the way
# "mul" does, as words to be matched in order.
FORMAL_OPEN_WORD = M.Char("(")
FORMAL_CLOSE_WORD = M.Char(")")
FORMAL_SEPARATOR_WORD = M.Char(",")


class WordSymbol(M.Edge):
    """A production symbol matching one literal word of the input.

    Pair(WordSymbolLabel, Pair(word, EmptyList)).
    """

    def __init__(self, word):
        self.result = M.Pair(
            Lmod.WordSymbolLabel,
            M.Pair(word, M.EmptyList),
        )
        super().__init__(
            inputs=M.Pair(word, M.EmptyList), results=self.result,
        )

    def __call__(self):
        return self.result


class CategorySymbol(M.Edge):
    """A production symbol matching a constituent of one category.

    Pair(CategorySymbolLabel, Pair(category, Pair(variable, EmptyList))).
    The variable is the slot the matched constituent's term binds to, so
    the production's template can name what the symbol found.
    """

    def __init__(self, category, variable):
        self.result = M.Pair(
            Lmod.CategorySymbolLabel,
            M.Pair(category, M.Pair(variable, M.EmptyList)),
        )
        super().__init__(
            inputs=M.Pair(category, M.Pair(variable, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class Production(M.Edge):
    """One grammar rule: a category, a symbol sequence, and a template.

    Pair(ProductionLabel, Pair(category, Pair(symbols, Pair(template,
    EmptyList)))). The symbols say what stands next to what; the
    template says what the result term is, built by the same Instantiate
    every law's right-hand side is built by. A grammar is a chain of
    these and nothing else -- there is no production that is a branch in
    the parser instead.
    """

    def __init__(self, category, symbols, template):
        self.result = M.Pair(
            Lmod.ProductionLabel,
            M.Pair(
                category,
                M.Pair(symbols, M.Pair(template, M.EmptyList)),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                category,
                M.Pair(symbols, M.Pair(template, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class ProductionCategory(M.Edge):
    def __init__(self, production):
        self.result = M.Head(M.Tail(production)())()
        super().__init__(
            inputs=M.Pair(production, M.EmptyList), results=self.result,
        )

    def __call__(self):
        return self.result


class ProductionSymbols(M.Edge):
    def __init__(self, production):
        self.result = M.Head(M.Tail(M.Tail(production)())())()
        super().__init__(
            inputs=M.Pair(production, M.EmptyList), results=self.result,
        )

    def __call__(self):
        return self.result


class ProductionTemplate(M.Edge):
    def __init__(self, production):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(production)())())())()
        super().__init__(
            inputs=M.Pair(production, M.EmptyList), results=self.result,
        )

    def __call__(self):
        return self.result


class Constituent(M.Edge):
    """One reading of one span: a category, a term, and the two cells.

    Pair(ConstituentLabel, Pair(category, Pair(term, Pair(start,
    Pair(after, EmptyList))))). `start` is the cell it begins at and
    `after` the cell it ends before, so a constituent is a fact about a
    span rather than about a position in a scan.
    """

    def __init__(self, category, term, start, after):
        self.result = M.Pair(
            Lmod.ConstituentLabel,
            M.Pair(
                category,
                M.Pair(term, M.Pair(start, M.Pair(after, M.EmptyList))),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                category,
                M.Pair(term, M.Pair(start, M.Pair(after, M.EmptyList))),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class ConstituentCategory(M.Edge):
    def __init__(self, constituent):
        self.result = M.Head(M.Tail(constituent)())()
        super().__init__(
            inputs=M.Pair(constituent, M.EmptyList), results=self.result,
        )

    def __call__(self):
        return self.result


class ConstituentTerm(M.Edge):
    def __init__(self, constituent):
        self.result = M.Head(M.Tail(M.Tail(constituent)())())()
        super().__init__(
            inputs=M.Pair(constituent, M.EmptyList), results=self.result,
        )

    def __call__(self):
        return self.result


class ConstituentStart(M.Edge):
    def __init__(self, constituent):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(constituent)())())())()
        super().__init__(
            inputs=M.Pair(constituent, M.EmptyList), results=self.result,
        )

    def __call__(self):
        return self.result


class ConstituentAfter(M.Edge):
    def __init__(self, constituent):
        self.result = M.Head(
            M.Tail(M.Tail(M.Tail(M.Tail(constituent)())())())(),
        )()
        super().__init__(
            inputs=M.Pair(constituent, M.EmptyList), results=self.result,
        )

    def __call__(self):
        return self.result


class ChartCells(M.Edge):
    """The cells of a word chain: every position a span may start or end at.

    A cell is a position, named by the suffix of the chain that begins
    there -- the chain itself is the first cell and EmptyList the cell
    past the last word. Two spans are the same span exactly when their
    cells are the same objects, so nothing counts positions and nothing
    compares counts.
    """

    def __init__(self, chain):
        cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        reversed_cells = M.EmptyList
        scan_text = "0"
        remaining = chain
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                remaining = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                reversed_cells = M.Pair(remaining, reversed_cells)
                remaining = M.Tail(remaining)()
        self.result = M.Reverse(M.Pair(M.EmptyList, reversed_cells))()
        super().__init__(
            inputs=M.Pair(chain, M.EmptyList), results=self.result,
        )

    def __call__(self):
        return self.result


class ChartSymbolMatches(M.Edge):
    """Every way one symbol sequence can be matched starting at one cell.

    Returns a chain of Pair(bindings, Pair(after, EmptyList)): the
    bindings the category symbols made and the cell the match ended
    before. Every way, not the first way -- two readings of the same
    words are two matches here, and choosing between them is not this
    edge's business.

    A word symbol consumes one input word; a category symbol consumes a
    constituent already in the chart and hands its term to the template
    through the symbol's variable. The recursion is over the symbol
    chain, which shrinks at every step, so it ends when the symbols run
    out.
    """

    def __init__(self, symbols, cell, constituents):
        cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        self.result = M.EmptyList
        if M.IdentityCompare(symbols, M.EmptyList)() is M.truth_value:
            self.result = M.Pair(
                M.Pair(M.EmptyList, M.Pair(cell, M.EmptyList)),
                M.EmptyList,
            )
        else:
            symbol = M.Head(symbols)()
            rest_symbols = M.Tail(symbols)()
            if M.TermEqual(
                M.Head(symbol)(),
                Lmod.WordSymbolLabel,
            )() is M.truth_value:
                if M.IdentityCompare(cell, M.EmptyList)() is M.false_value:
                    if M.Compare(
                        M.Head(cell)(),
                        M.Head(M.Tail(symbol)())(),
                    )() is M.truth_value:
                        self.result = ChartSymbolMatches(
                            rest_symbols,
                            M.Tail(cell)(),
                            constituents,
                        )()
            elif M.TermEqual(
                M.Head(symbol)(),
                Lmod.CategorySymbolLabel,
            )() is M.truth_value:
                category = M.Head(M.Tail(symbol)())()
                variable = M.Head(M.Tail(M.Tail(symbol)())())()
                reversed_matches = M.EmptyList
                scan_text = "0"
                remaining = constituents
                while M.IdentityCompare(
                    remaining, M.EmptyList,
                )() is M.false_value:
                    if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                        remaining = M.EmptyList
                    else:
                        scan_text = GMPSuccText(scan_text)()
                        constituent = M.Head(remaining)()
                        if M.IdentityCompare(
                            ConstituentStart(constituent)(), cell,
                        )() is M.truth_value:
                            if M.Compare(
                                ConstituentCategory(constituent)(), category,
                            )() is M.truth_value:
                                tail_matches = ChartSymbolMatches(
                                    rest_symbols,
                                    ConstituentAfter(constituent)(),
                                    constituents,
                                )()
                                tail_scan_text = "0"
                                remaining_tail = tail_matches
                                while M.IdentityCompare(
                                    remaining_tail, M.EmptyList,
                                )() is M.false_value:
                                    if GMPEqualText(
                                        tail_scan_text, cap_text,
                                    )() is M.truth_value:
                                        remaining_tail = M.EmptyList
                                    else:
                                        tail_scan_text = GMPSuccText(
                                            tail_scan_text,
                                        )()
                                        tail_match = M.Head(remaining_tail)()
                                        reversed_matches = M.Pair(
                                            M.Pair(
                                                M.Pair(
                                                    M.Pair(
                                                        variable,
                                                        M.Pair(
                                                            ConstituentTerm(
                                                                constituent,
                                                            )(),
                                                            M.EmptyList,
                                                        ),
                                                    ),
                                                    M.Head(tail_match)(),
                                                ),
                                                M.Tail(tail_match)(),
                                            ),
                                            reversed_matches,
                                        )
                                        remaining_tail = M.Tail(
                                            remaining_tail,
                                        )()
                        remaining = M.Tail(remaining)()
                self.result = M.Reverse(reversed_matches)()
        super().__init__(
            inputs=M.Pair(
                symbols,
                M.Pair(cell, M.Pair(constituents, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class ChartAddConstituent(M.Edge):
    """Add a constituent unless one exactly like it is already present.

    Two constituents are the same when they are the same category over
    the same two cells carrying structurally equal terms. Two readings
    of one span with different terms are both kept: ambiguity is a fact
    about the sentence, and collapsing it here would be the parser
    choosing on the reader's behalf.

    Returns Pair(constituents, Pair(added, EmptyList)).
    """

    def __init__(self, constituents, constituent):
        cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        category = ConstituentCategory(constituent)()
        term = ConstituentTerm(constituent)()
        start = ConstituentStart(constituent)()
        after = ConstituentAfter(constituent)()
        self.capped = M.false_value
        present = M.false_value
        scan_text = "0"
        remaining = constituents
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                self.capped = M.truth_value
                present = M.truth_value
                remaining = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                other = M.Head(remaining)()
                if M.IdentityCompare(
                    ConstituentStart(other)(), start,
                )() is M.truth_value:
                    if M.IdentityCompare(
                        ConstituentAfter(other)(), after,
                    )() is M.truth_value:
                        if M.Compare(
                            ConstituentCategory(other)(), category,
                        )() is M.truth_value:
                            if M.TermEqual(
                                ConstituentTerm(other)(), term,
                            )() is M.truth_value:
                                present = M.truth_value
                if M.IdentityCompare(present, M.truth_value)() is M.truth_value:
                    remaining = M.EmptyList
                else:
                    remaining = M.Tail(remaining)()
        self.added = M.false_value
        grown = constituents
        if M.IdentityCompare(present, M.false_value)() is M.truth_value:
            grown = M.Pair(constituent, constituents)
            self.added = M.truth_value
        self.result = M.Pair(grown, M.Pair(self.added, M.EmptyList))
        super().__init__(
            inputs=M.Pair(constituents, M.Pair(constituent, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class ChartSaturate(M.Edge):
    """Close a set of constituents under a set of productions.

    One pass tries every production at every cell against every
    constituent the chart already holds; a pass that adds nothing is the
    fixed point. This loop knows nothing about what any production says.
    Brackets, separators, argument order and arity live in the
    productions; the loop is the same loop whatever they are, which is
    the whole difference between a grammar and a parser written by hand.

    `saturated` is truth only when a pass added nothing before the pass
    cap ran out and no addition hit the chart's own size cap, so an
    unfinished parse is visible rather than silently partial.
    """

    def __init__(self, productions, seeds, cells):
        cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        pass_cap_text = M.GMPRepText(CHART_PASS_CAP)()
        constituents = seeds
        self.saturated = M.false_value
        self.capped = M.false_value
        pass_text = "0"
        growing = M.truth_value
        while M.IdentityCompare(growing, M.truth_value)() is M.truth_value:
            if GMPEqualText(pass_text, pass_cap_text)() is M.truth_value:
                growing = M.false_value
            else:
                pass_text = GMPSuccText(pass_text)()
                growing = M.false_value
                production_scan_text = "0"
                remaining_productions = productions
                while M.IdentityCompare(
                    remaining_productions, M.EmptyList,
                )() is M.false_value:
                    if GMPEqualText(
                        production_scan_text, cap_text,
                    )() is M.truth_value:
                        remaining_productions = M.EmptyList
                    else:
                        production_scan_text = GMPSuccText(
                            production_scan_text,
                        )()
                        production = M.Head(remaining_productions)()
                        category = ProductionCategory(production)()
                        symbols = ProductionSymbols(production)()
                        template = ProductionTemplate(production)()
                        cell_scan_text = "0"
                        remaining_cells = cells
                        while M.IdentityCompare(
                            remaining_cells, M.EmptyList,
                        )() is M.false_value:
                            if GMPEqualText(
                                cell_scan_text, cap_text,
                            )() is M.truth_value:
                                remaining_cells = M.EmptyList
                            else:
                                cell_scan_text = GMPSuccText(cell_scan_text)()
                                cell = M.Head(remaining_cells)()
                                matches = ChartSymbolMatches(
                                    symbols, cell, constituents,
                                )()
                                match_scan_text = "0"
                                remaining_matches = matches
                                while M.IdentityCompare(
                                    remaining_matches, M.EmptyList,
                                )() is M.false_value:
                                    if GMPEqualText(
                                        match_scan_text, cap_text,
                                    )() is M.truth_value:
                                        remaining_matches = M.EmptyList
                                    else:
                                        match_scan_text = GMPSuccText(
                                            match_scan_text,
                                        )()
                                        match = M.Head(remaining_matches)()
                                        after = M.Head(M.Tail(match)())()
                                        if M.IdentityCompare(
                                            after, cell,
                                        )() is M.false_value:
                                            addition = ChartAddConstituent(
                                                constituents,
                                                Constituent(
                                                    category,
                                                    M.Head(
                                                        M.Instantiate(
                                                            template,
                                                            M.Head(match)(),
                                                        )(),
                                                    )(),
                                                    cell,
                                                    after,
                                                )(),
                                            )
                                            constituents = M.Head(addition())()
                                            if M.IdentityCompare(
                                                addition.added,
                                                M.truth_value,
                                            )() is M.truth_value:
                                                growing = M.truth_value
                                            if M.IdentityCompare(
                                                addition.capped,
                                                M.truth_value,
                                            )() is M.truth_value:
                                                self.capped = M.truth_value
                                        remaining_matches = M.Tail(
                                            remaining_matches,
                                        )()
                                remaining_cells = M.Tail(remaining_cells)()
                        remaining_productions = M.Tail(remaining_productions)()
                if M.IdentityCompare(growing, M.false_value)() is M.truth_value:
                    if M.IdentityCompare(
                        self.capped, M.false_value,
                    )() is M.truth_value:
                        self.saturated = M.truth_value
        self.result = constituents
        super().__init__(
            inputs=M.Pair(
                productions,
                M.Pair(seeds, M.Pair(cells, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class ChartSpanningTerms(M.Edge):
    """Every term of one category whose constituent covers the whole chain."""

    def __init__(self, constituents, category, chain):
        cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        reversed_terms = M.EmptyList
        scan_text = "0"
        remaining = constituents
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                remaining = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                constituent = M.Head(remaining)()
                if M.IdentityCompare(
                    ConstituentStart(constituent)(), chain,
                )() is M.truth_value:
                    if M.IdentityCompare(
                        ConstituentAfter(constituent)(), M.EmptyList,
                    )() is M.truth_value:
                        if M.Compare(
                            ConstituentCategory(constituent)(), category,
                        )() is M.truth_value:
                            reversed_terms = M.Pair(
                                ConstituentTerm(constituent)(),
                                reversed_terms,
                            )
                remaining = M.Tail(remaining)()
        self.result = M.Reverse(reversed_terms)()
        super().__init__(
            inputs=M.Pair(
                constituents,
                M.Pair(category, M.Pair(chain, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class ChartSeedConstituents(M.Edge):
    """What the words of a chain mean standing on their own.

    One constituent per word the vocabulary resolves, and one per run of
    adjacent digit words, since "six four" is one number spanning two
    cells and no production says so. This is the only place a word's own
    meaning is consulted; everything above it is productions.
    """

    def __init__(self, word_entries, digit_words, category, chain):
        cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        reversed_seeds = M.EmptyList
        scan_text = "0"
        remaining = chain
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                remaining = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                word = M.Head(remaining)()
                value = CorrespondenceResolveWord(
                    word_entries,
                    Surface(M.Pair(word, M.EmptyList))(),
                )()
                if M.IdentityCompare(value, M.EmptyList)() is M.false_value:
                    reversed_seeds = M.Pair(
                        Constituent(
                            category, value, remaining, M.Tail(remaining)(),
                        )(),
                        reversed_seeds,
                    )
                reversed_run = M.EmptyList
                run_scan_text = "0"
                run_remaining = remaining
                while M.IdentityCompare(
                    run_remaining, M.EmptyList,
                )() is M.false_value:
                    if GMPEqualText(
                        run_scan_text, cap_text,
                    )() is M.truth_value:
                        run_remaining = M.EmptyList
                    else:
                        run_scan_text = GMPSuccText(run_scan_text)()
                        digit = SurfaceDigitOfWord(
                            M.Head(run_remaining)(), digit_words,
                        )()
                        if M.IdentityCompare(
                            digit, M.EmptyList,
                        )() is M.truth_value:
                            run_remaining = M.EmptyList
                        else:
                            reversed_run = M.Pair(
                                M.Head(run_remaining)(), reversed_run,
                            )
                            run_remaining = M.Tail(run_remaining)()
                            run_value = SurfaceDigitRunValue(
                                M.Reverse(reversed_run)(), digit_words,
                            )()
                            if M.IdentityCompare(
                                run_value, M.EmptyList,
                            )() is M.false_value:
                                reversed_seeds = M.Pair(
                                    Constituent(
                                        category,
                                        run_value,
                                        remaining,
                                        run_remaining,
                                    )(),
                                    reversed_seeds,
                                )
                remaining = M.Tail(remaining)()
        self.result = M.Reverse(reversed_seeds)()
        super().__init__(
            inputs=M.Pair(
                word_entries,
                M.Pair(
                    digit_words,
                    M.Pair(category, M.Pair(chain, M.EmptyList)),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class FormalProductions(M.Edge):
    """The formal notation as productions, generated from the signatures.

    "mul ( a , b )" used to be a scan for an open bracket, a depth
    counter, a split on commas at depth zero and an arity check after
    the fact -- one grammar written as control flow. A signature is now
    one production: the word, an open bracket, an argument category per
    argument with separators between them, a close bracket, and a
    template putting the matched arguments under the constructor.

    Arity is not checked, it is matched: a production with two argument
    slots does not match one argument. Nesting is not implemented at
    all: an argument is the same category the whole application is, so
    the chart has already read the inner application by the time the
    outer one asks for it. Brackets and commas are words in a
    production, the same as "mul" is.

    Returns Pair(productions, Pair(registry, EmptyList)).
    """

    def __init__(self, signatures, category, registry):
        cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        reversed_productions = M.EmptyList
        scan_text = "0"
        remaining = signatures
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                remaining = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                signature = M.Head(remaining)()
                reversed_symbols = M.Pair(
                    WordSymbol(FORMAL_OPEN_WORD)(),
                    M.Pair(
                        WordSymbol(SignatureWord(signature)())(),
                        M.EmptyList,
                    ),
                )
                reversed_variables = M.EmptyList
                separated = M.false_value
                arity_scan_text = "0"
                remaining_arity = SignatureArity(signature)()
                while M.NatEq(
                    remaining_arity, M.Zero, registry,
                )() is M.false_value:
                    if GMPEqualText(
                        arity_scan_text, cap_text,
                    )() is M.truth_value:
                        remaining_arity = M.Zero
                    else:
                        arity_scan_text = GMPSuccText(arity_scan_text)()
                        if M.IdentityCompare(
                            separated, M.truth_value,
                        )() is M.truth_value:
                            reversed_symbols = M.Pair(
                                WordSymbol(FORMAL_SEPARATOR_WORD)(),
                                reversed_symbols,
                            )
                        variable = M.Pair(
                            M.VarTag, M.Pair(M.Atom(), M.EmptyList),
                        )
                        reversed_symbols = M.Pair(
                            CategorySymbol(category, variable)(),
                            reversed_symbols,
                        )
                        reversed_variables = M.Pair(
                            variable, reversed_variables,
                        )
                        separated = M.truth_value
                        stepped = M.NatPred(remaining_arity, registry)()
                        remaining_arity = M.Head(stepped)()
                        registry = M.Head(M.Tail(stepped)())()
                reversed_symbols = M.Pair(
                    WordSymbol(FORMAL_CLOSE_WORD)(), reversed_symbols,
                )
                reversed_productions = M.Pair(
                    Production(
                        category,
                        M.Reverse(reversed_symbols)(),
                        M.Pair(
                            SignatureConstructor(signature)(),
                            M.Reverse(reversed_variables)(),
                        ),
                    )(),
                    reversed_productions,
                )
                remaining = M.Tail(remaining)()
        self.result = M.Pair(
            M.Reverse(reversed_productions)(),
            M.Pair(registry, M.EmptyList),
        )
        super().__init__(
            inputs=M.Pair(
                signatures,
                M.Pair(category, M.Pair(registry, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class FormalTermReadings(M.Edge):
    """Read "name ( arg , arg )" by chart, as the first client of the chart.

    The formal notation gets no reader of its own. Its signatures become
    productions, the vocabulary seeds the words, and the same saturation
    that any other grammar runs through produces the terms. Takes a
    Surface, as every other reader in this file does, and returns every
    term spanning the whole of it, so an ambiguous notation reports both
    readings instead of one of them.

    Returns Pair(terms, Pair(registry, EmptyList)). An empty chain of
    terms means the words do not spell an application: a word with no
    signature, a wrong count of arguments and a missing bracket are all
    the same answer here, which is that no production spans the input.
    """

    def __init__(self, signatures, vocabulary, surface_term, registry):
        word_entries = M.Head(M.Tail(vocabulary)())()
        digit_words = M.Head(M.Tail(M.Tail(vocabulary)())())()
        chain = M.Head(M.Tail(surface_term)())()
        generated = FormalProductions(
            signatures, CHART_TERM_CATEGORY, registry,
        )()
        registry = M.Head(M.Tail(generated)())()
        chart = ChartSaturate(
            M.Head(generated)(),
            ChartSeedConstituents(
                word_entries, digit_words, CHART_TERM_CATEGORY, chain,
            )(),
            ChartCells(chain)(),
        )
        self.saturated = chart.saturated
        self.result = M.Pair(
            ChartSpanningTerms(chart(), CHART_TERM_CATEGORY, chain)(),
            M.Pair(registry, M.EmptyList),
        )
        super().__init__(
            inputs=M.Pair(
                signatures,
                M.Pair(
                    vocabulary,
                    M.Pair(surface_term, M.Pair(registry, M.EmptyList)),
                ),
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


class SurfaceOperatorWords(M.Edge):
    """The infix words the vocabulary's binary templates are keyed on."""

    def __init__(self, vocabulary):
        self.result = M.Pair(
            M.Char("plus"),
            M.Pair(
                M.Char("times"),
                M.Pair(M.Char("minus"), M.EmptyList),
            ),
        )
        super().__init__(
            inputs=M.Pair(vocabulary, M.EmptyList),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SurfaceChainHasWord(M.Edge):
    """Membership by word value rather than object identity."""

    def __init__(self, chain, word):
        self.result = M.false_value
        remaining = chain
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if M.Compare(M.Head(remaining)(), word)() is M.truth_value:
                self.result = M.truth_value
                remaining = M.EmptyList
            else:
                remaining = M.Tail(remaining)()
        super().__init__(
            inputs=M.Pair(chain, M.Pair(word, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SurfaceFoldChainedOperator(M.Edge):
    """Rewrite `a OP b OP c` as `( a OP b ) OP c`, left-associating.

    The correspondence laws are strictly binary: "two times two" has one
    interpretation and "two times two times two" has none, which surfaced
    as "no correspondence law for that shape" -- true, but only because
    nothing had grouped the chain. Parenthesising by hand already worked,
    so this supplies the grouping the reader would otherwise have to type.

    One fold per call, leftmost first; the caller re-reduces, so a longer
    chain folds one step at a time. A chain with fewer than two operators
    is returned unchanged, and the operator words must be the same one --
    mixing "plus" and "times" would impose a precedence this has no
    grounds to choose.
    """

    def __init__(self, chain, operator_words):
        cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        first_index_text = ""
        second_index_text = ""
        first_word = M.EmptyList
        seen_text = "0"
        scan_text = "0"
        remaining = chain
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                remaining = M.EmptyList
            else:
                word = M.Head(remaining)()
                # Compare, not ChainHasTerm: M.Char does not intern, so a
                # word read from a sentence is a different object from the
                # same word in the operator list, and identity would miss it.
                if SurfaceChainHasWord(operator_words, word)() is M.truth_value:
                    if M.IdentityCompare(first_word, M.EmptyList)() is M.truth_value:
                        first_word = word
                        first_index_text = scan_text
                    elif M.Compare(word, first_word)() is M.truth_value:
                        if GMPEqualText(second_index_text, "")() is M.truth_value:
                            second_index_text = scan_text
                scan_text = GMPSuccText(scan_text)()
                remaining = M.Tail(remaining)()
        self.result = chain
        if GMPEqualText(second_index_text, "")() is M.false_value:
            # The group opens at the operand immediately before the first
            # operator, not at the start of the sentence: "is two times two
            # times two" must fold to "is ( two times two ) times two", or
            # the leading words are swallowed into a group that cannot be
            # evaluated -- which is how a question became a group failure.
            open_index_text = "0"
            if GMPLessText("0", first_index_text)() is M.truth_value:
                open_index_text = GMPSubText(first_index_text, "1")()
            reversed_output = M.EmptyList
            cursor_text = "0"
            remaining = chain
            while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
                if GMPEqualText(cursor_text, open_index_text)() is M.truth_value:
                    reversed_output = M.Pair(M.Char("("), reversed_output)
                if GMPEqualText(cursor_text, second_index_text)() is M.truth_value:
                    reversed_output = M.Pair(M.Char(")"), reversed_output)
                    while M.IdentityCompare(
                        remaining,
                        M.EmptyList,
                    )() is M.false_value:
                        reversed_output = M.Pair(M.Head(remaining)(), reversed_output)
                        remaining = M.Tail(remaining)()
                else:
                    reversed_output = M.Pair(M.Head(remaining)(), reversed_output)
                    cursor_text = GMPSuccText(cursor_text)()
                    remaining = M.Tail(remaining)()
            self.result = Reverse(reversed_output)()
        super().__init__(
            inputs=M.Pair(chain, M.Pair(operator_words, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SurfaceDigitRunValue(M.Edge):
    """A chain that is entirely digit words, read as one Nat.

    Only a chain of two or more digit words qualifies: a single word is
    already handled by the ordinary correspondence laws, and any non-digit
    word means this is a sentence rather than a numeral.
    """

    def __init__(self, chain, digit_words):
        cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        digits_text = ""
        counted_text = "0"
        all_digits = M.truth_value
        scan_text = "0"
        remaining = chain
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                all_digits = M.false_value
                remaining = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                digit = SurfaceDigitOfWord(M.Head(remaining)(), digit_words)()
                if M.IdentityCompare(digit, M.EmptyList)() is M.truth_value:
                    all_digits = M.false_value
                    remaining = M.EmptyList
                else:
                    digits_text = digits_text + digit()
                    counted_text = GMPSuccText(counted_text)()
                    remaining = M.Tail(remaining)()
        self.result = M.EmptyList
        if M.IdentityCompare(all_digits, M.truth_value)() is M.truth_value:
            if GMPLessText("1", counted_text)() is M.truth_value:
                self.result = MineNatFromGMPRep(M.GMPRep(digits_text))()
        super().__init__(
            inputs=M.Pair(chain, M.Pair(digit_words, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SurfaceJoinDigitWords(M.Edge):
    """Fold runs of adjacent digit words into single multi-digit numerals.

    The tokenizer rewrites each digit of a numeral separately, so "64"
    arrives as "six four". No correspondence law relates two number words
    standing side by side, so every multi-digit numeral was unevaluable --
    "sqrt(64)" and "(64)" alike -- and the failure was reported as
    unbalanced parentheses. This is the inverse of RenderNatSurface, which
    already turns a Nat into a chain of digit words.

    A run of one word is left exactly as it was, so single digits and every
    documented spelled-out form are untouched. Only runs of two or more are
    joined, and the join is the concatenation of their digit characters.
    """

    def __init__(self, chain, digit_words):
        cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        reversed_output = M.EmptyList
        pending_text = ""
        pending_words = M.EmptyList
        scan_text = "0"
        remaining = chain
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                remaining = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                word = M.Head(remaining)()
                digit = SurfaceDigitOfWord(word, digit_words)()
                if M.IdentityCompare(digit, M.EmptyList)() is M.false_value:
                    pending_text = pending_text + digit()
                    pending_words = M.Pair(word, pending_words)
                else:
                    reversed_output = SurfaceFlushDigits(
                        reversed_output,
                        pending_text,
                        pending_words,
                    )()
                    pending_text = ""
                    pending_words = M.EmptyList
                    reversed_output = M.Pair(word, reversed_output)
                remaining = M.Tail(remaining)()
        reversed_output = SurfaceFlushDigits(
            reversed_output,
            pending_text,
            pending_words,
        )()
        self.result = Reverse(reversed_output)()
        super().__init__(
            inputs=M.Pair(chain, M.Pair(digit_words, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SurfaceDigitOfWord(M.Edge):
    """The digit character a number word names, or EmptyList."""

    def __init__(self, word, digit_words):
        cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        self.result = M.EmptyList
        scan_text = "0"
        remaining = digit_words
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                remaining = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                entry = M.Head(remaining)()
                if M.Compare(M.Head(M.Tail(entry)())(), word)() is M.truth_value:
                    self.result = M.Head(entry)()
                    remaining = M.EmptyList
                else:
                    remaining = M.Tail(remaining)()
        super().__init__(
            inputs=M.Pair(word, M.Pair(digit_words, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SurfaceFlushDigits(M.Edge):
    """Emit a pending digit run: joined when several, verbatim when one."""

    def __init__(self, reversed_output, pending_text, pending_words):
        self.result = reversed_output
        if M.IdentityCompare(pending_words, M.EmptyList)() is M.false_value:
            single = M.IdentityCompare(M.Tail(pending_words)(), M.EmptyList)()
            if M.IdentityCompare(single, M.truth_value)() is M.truth_value:
                self.result = M.Pair(M.Head(pending_words)(), reversed_output)
            else:
                self.result = M.Pair(M.Char(pending_text), reversed_output)
        super().__init__(
            inputs=M.Pair(reversed_output, M.Pair(pending_words, M.EmptyList)),
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
        self.unevaluated = M.EmptyList
        cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        open_symbol = M.Char("(")
        close_symbol = M.Char(")")
        chain = M.Head(M.Tail(surface_term)())()
        # The correspondence laws are binary, so an unparenthesized chain
        # like "two times two times two" has no interpretation at all.
        # Left-associate it into the grouping the reader would otherwise
        # have to type; the loop below then reduces those groups normally.
        operator_words = SurfaceOperatorWords(vocabulary)()
        fold_text = "0"
        folding = M.truth_value
        while M.IdentityCompare(folding, M.truth_value)() is M.truth_value:
            folding = M.false_value
            if GMPLessText(fold_text, cap_text)() is M.truth_value:
                fold_text = GMPSuccText(fold_text)()
                folded = SurfaceFoldChainedOperator(chain, operator_words)()
                if M.TermEqual(folded, chain)() is M.false_value:
                    chain = folded
                    folding = M.truth_value
        failed = M.false_value
        # Distinguish a bracket-matching failure from a group whose contents
        # simply could not be evaluated. Both used to surface as "your
        # parentheses do not balance", which is false whenever the brackets
        # are fine and merely their contents are not understood.
        value_failed = M.false_value
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
                                has_comma = M.false_value
                                comma_scan = inner_chain
                                while M.IdentityCompare(
                                    comma_scan,
                                    M.EmptyList,
                                )() is M.false_value:
                                    if M.Compare(
                                        M.Head(comma_scan)(),
                                        M.Char(","),
                                    )() is M.truth_value:
                                        has_comma = M.truth_value
                                        comma_scan = M.EmptyList
                                    else:
                                        comma_scan = M.Tail(comma_scan)()
                                if M.IdentityCompare(
                                    has_comma,
                                    M.truth_value,
                                )() is M.truth_value:
                                    # A comma marks an argument list, not a
                                    # grouping: "( three , sqrt seven )" is
                                    # the tail of "mul ( ... )" and only
                                    # means anything WITH its function word
                                    # and brackets. Reducing the whole group
                                    # destroyed the shape the formal
                                    # template matches. Instead, reduce each
                                    # comma-separated ARGUMENT to a single
                                    # term and keep the brackets and commas,
                                    # so "mul ( three , sqrt seven )"
                                    # becomes "mul ( three , <Sqrt(7)> )"
                                    # and the binary template binds cleanly.
                                    changed = M.false_value
                                    arg_failed = M.false_value
                                    reversed_args = M.EmptyList
                                    reversed_segment = M.EmptyList
                                    seg_scan = inner_chain
                                    while M.IdentityCompare(
                                        seg_scan,
                                        M.EmptyList,
                                    )() is M.false_value:
                                        piece = M.Head(seg_scan)()
                                        if M.Compare(
                                            piece,
                                            M.Char(","),
                                        )() is M.truth_value:
                                            reversed_args = M.Pair(
                                                M.Reverse(reversed_segment)(),
                                                reversed_args,
                                            )
                                            reversed_segment = M.EmptyList
                                        else:
                                            reversed_segment = M.Pair(
                                                piece,
                                                reversed_segment,
                                            )
                                        seg_scan = M.Tail(seg_scan)()
                                    reversed_args = M.Pair(
                                        M.Reverse(reversed_segment)(),
                                        reversed_args,
                                    )
                                    segments = M.Reverse(reversed_args)()
                                    reversed_rebuilt_args = M.EmptyList
                                    seg_walk = segments
                                    while M.IdentityCompare(
                                        seg_walk,
                                        M.EmptyList,
                                    )() is M.false_value:
                                        segment = M.Head(seg_walk)()
                                        single = M.false_value
                                        if M.IdentityCompare(
                                            segment,
                                            M.EmptyList,
                                        )() is M.false_value:
                                            if M.IdentityCompare(
                                                M.Tail(segment)(),
                                                M.EmptyList,
                                            )() is M.truth_value:
                                                single = M.truth_value
                                        if M.IdentityCompare(
                                            single,
                                            M.truth_value,
                                        )() is M.truth_value:
                                            reversed_rebuilt_args = M.Pair(
                                                segment,
                                                reversed_rebuilt_args,
                                            )
                                        else:
                                            valued = ConverseValue(
                                                vocabulary,
                                                Surface(segment)(),
                                                registry,
                                            )()
                                            seg_value = M.Head(valued)()
                                            registry = M.Head(
                                                M.Tail(valued)(),
                                            )()
                                            if M.IdentityCompare(
                                                seg_value,
                                                M.EmptyList,
                                            )() is M.truth_value:
                                                seg_readings = ConverseInterpretations(
                                                    vocabulary,
                                                    Surface(segment)(),
                                                    registry,
                                                )()
                                                seg_list = M.Head(
                                                    seg_readings,
                                                )()
                                                registry = M.Head(
                                                    M.Tail(seg_readings)(),
                                                )()
                                                if M.IdentityCompare(
                                                    seg_list,
                                                    M.EmptyList,
                                                )() is M.false_value:
                                                    if M.IdentityCompare(
                                                        M.Tail(seg_list)(),
                                                        M.EmptyList,
                                                    )() is M.truth_value:
                                                        seg_meaning = M.Head(
                                                            M.Head(
                                                                seg_list,
                                                            )(),
                                                        )()
                                                        seg_value = M.Head(
                                                            M.Tail(
                                                                seg_meaning,
                                                            )(),
                                                        )()
                                            if M.IdentityCompare(
                                                seg_value,
                                                M.EmptyList,
                                            )() is M.truth_value:
                                                arg_failed = M.truth_value
                                            else:
                                                reversed_rebuilt_args = M.Pair(
                                                    M.Pair(
                                                        seg_value,
                                                        M.EmptyList,
                                                    ),
                                                    reversed_rebuilt_args,
                                                )
                                                changed = M.truth_value
                                        seg_walk = M.Tail(seg_walk)()
                                    if M.IdentityCompare(
                                        arg_failed,
                                        M.false_value,
                                    )() is M.truth_value:
                                        if M.IdentityCompare(
                                            changed,
                                            M.truth_value,
                                        )() is M.truth_value:
                                            rebuilt_args = M.Reverse(
                                                reversed_rebuilt_args,
                                            )()
                                            rebuilt = M.Tail(remaining)()
                                            rebuilt = M.Pair(element, rebuilt)
                                            reversed_group = M.EmptyList
                                            arg_walk = rebuilt_args
                                            first_arg = M.truth_value
                                            while M.IdentityCompare(
                                                arg_walk,
                                                M.EmptyList,
                                            )() is M.false_value:
                                                if M.IdentityCompare(
                                                    first_arg,
                                                    M.false_value,
                                                )() is M.truth_value:
                                                    reversed_group = M.Pair(
                                                        M.Char(","),
                                                        reversed_group,
                                                    )
                                                first_arg = M.false_value
                                                seg_flush = M.Head(arg_walk)()
                                                while M.IdentityCompare(
                                                    seg_flush,
                                                    M.EmptyList,
                                                )() is M.false_value:
                                                    reversed_group = M.Pair(
                                                        M.Head(seg_flush)(),
                                                        reversed_group,
                                                    )
                                                    seg_flush = M.Tail(
                                                        seg_flush,
                                                    )()
                                                arg_walk = M.Tail(arg_walk)()
                                            group_walk = reversed_group
                                            while M.IdentityCompare(
                                                group_walk,
                                                M.EmptyList,
                                            )() is M.false_value:
                                                rebuilt = M.Pair(
                                                    M.Head(group_walk)(),
                                                    rebuilt,
                                                )
                                                group_walk = M.Tail(
                                                    group_walk,
                                                )()
                                            rebuilt = M.Pair(
                                                open_atom,
                                                rebuilt,
                                            )
                                            spliced = reversed_before
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
                                            # All arguments already single:
                                            # nothing to do here. Flush the
                                            # group into 'before' untouched
                                            # so the scan can continue past
                                            # it without reporting failure.
                                            reversed_before = M.Pair(
                                                open_atom,
                                                reversed_before,
                                            )
                                            flush = inner_chain
                                            while M.IdentityCompare(
                                                flush,
                                                M.EmptyList,
                                            )() is M.false_value:
                                                reversed_before = M.Pair(
                                                    M.Head(flush)(),
                                                    reversed_before,
                                                )
                                                flush = M.Tail(flush)()
                                            reversed_before = M.Pair(
                                                element,
                                                reversed_before,
                                            )
                                            seen_open = M.false_value
                                            reversed_inner = M.EmptyList
                                            remaining = M.Tail(remaining)()
                                    else:
                                        failed = M.truth_value
                                        value_failed = M.truth_value
                                        self.unevaluated = Surface(
                                            inner_chain,
                                        )()
                                        remaining = M.EmptyList
                                elif M.IdentityCompare(
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
                                        # "64" reaches here as "six four":
                                        # the tokenizer splits every digit and
                                        # no law relates two number words side
                                        # by side. A run of digit words has a
                                        # direct reading as one numeral.
                                        value = SurfaceDigitRunValue(
                                            inner_chain,
                                            M.Head(
                                                M.Tail(M.Tail(vocabulary)())(),
                                            )(),
                                        )()
                                    if M.IdentityCompare(
                                        value,
                                        M.EmptyList,
                                    )() is M.truth_value:
                                        # A group need not denote a number.
                                        # "sqrt ( three )" has no value, but it
                                        # does have a meaning, and the sentence
                                        # around it wants a term in that slot.
                                        # Splice the term so nesting reads the
                                        # same as any other radicand.
                                        inner_readings = ConverseInterpretations(
                                            vocabulary,
                                            Surface(inner_chain)(),
                                            registry,
                                        )()
                                        inner_list = M.Head(inner_readings)()
                                        registry = M.Head(
                                            M.Tail(inner_readings)(),
                                        )()
                                        if M.IdentityCompare(
                                            inner_list,
                                            M.EmptyList,
                                        )() is M.false_value:
                                            if M.IdentityCompare(
                                                M.Tail(inner_list)(),
                                                M.EmptyList,
                                            )() is M.truth_value:
                                                only = M.Head(inner_list)()
                                                reading = M.Head(only)()
                                                value = M.Head(
                                                    M.Tail(reading)(),
                                                )()
                                    if M.IdentityCompare(
                                        value,
                                        M.EmptyList,
                                    )() is M.truth_value:
                                        failed = M.truth_value
                                        value_failed = M.truth_value
                                        self.unevaluated = Surface(inner_chain)()
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
        self.value_failed = value_failed
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
            direct = ConverseInterpretations(vocabulary, surface_term, registry)()
            direct_interpretations = M.Head(direct)()
            registry = M.Head(M.Tail(direct)())()
            reduced_surface = surface_term
            group_value_failed = M.false_value
            unevaluated_group = M.EmptyList
            if M.IdentityCompare(
                direct_interpretations,
                M.EmptyList,
            )() is M.truth_value:
                reducer = SurfaceReduceGroups(
                    vocabulary,
                    surface_term,
                    registry,
                )
                reduced = reducer()
                reduced_surface = M.Head(reduced)()
                registry = M.Head(M.Tail(reduced)())()
                group_value_failed = reducer.value_failed
                unevaluated_group = reducer.unevaluated
            if M.IdentityCompare(reduced_surface, M.EmptyList)() is M.truth_value:
                # Balanced brackets whose contents did not evaluate are a
                # different failure from brackets that do not match, and
                # saying the wrong one sends the reader hunting a typo that
                # is not there.
                group_reason = M.Pair(
                    Lmod.ReasonGroupLabel,
                    M.Pair(surface_term, M.EmptyList),
                )
                if M.IdentityCompare(
                    group_value_failed,
                    M.truth_value,
                )() is M.truth_value:
                    group_reason = M.Pair(
                        Lmod.ReasonGroupValueLabel,
                        M.Pair(unevaluated_group, M.EmptyList),
                    )
                outcome = NotUnderstood(surface_term, group_reason)()
            else:
                interpretations = direct_interpretations
                if M.IdentityCompare(
                    interpretations,
                    M.EmptyList,
                )() is M.truth_value:
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
                    proposition = ConversePropositionInterpretations(
                        vocabulary,
                        reduced_surface,
                        registry,
                    )()
                    interpretations = M.Head(proposition)()
                    registry = M.Head(M.Tail(proposition)())()
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
                if M.IdentityCompare(outcome, M.EmptyList)() is M.truth_value:
                    task_scan_text = "0"
                    remaining_tasks = interpretations
                    while M.IdentityCompare(
                        remaining_tasks,
                        M.EmptyList,
                    )() is M.false_value:
                        if GMPEqualText(
                            task_scan_text,
                            cap_text,
                        )() is M.truth_value:
                            remaining_tasks = M.EmptyList
                        else:
                            task_scan_text = GMPSuccText(task_scan_text)()
                            interpretation = M.Head(remaining_tasks)()
                            meaning = M.Head(interpretation)()
                            body = M.Head(M.Tail(meaning)())()
                            if M.IsPair(body)() is M.truth_value:
                                if M.TermEqual(
                                    M.Head(body)(),
                                    Lmod.TaskLabel,
                                )() is M.truth_value:
                                    outcome = Understood(
                                        surface_term,
                                        meaning,
                                        M.Head(M.Tail(interpretation)())(),
                                        M.EmptyList,
                                    )()
                                    remaining_tasks = M.EmptyList
                                elif M.TermEqual(
                                    M.Head(body)(),
                                    M.IsRealLabel,
                                )() is M.truth_value:
                                    outcome = Understood(
                                        surface_term,
                                        meaning,
                                        M.Head(M.Tail(interpretation)())(),
                                        M.EmptyList,
                                    )()
                                    remaining_tasks = M.EmptyList
                            if M.IdentityCompare(
                                remaining_tasks,
                                M.EmptyList,
                            )() is M.false_value:
                                remaining_tasks = M.Tail(remaining_tasks)()
                if M.IdentityCompare(outcome, M.EmptyList)() is M.truth_value:
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
                            evaluated = PropositionEvaluate(
                                meaning,
                                word_entries,
                                registry,
                            )()
                            candidate = M.Head(evaluated)()
                            registry = M.Head(M.Tail(evaluated)())()
                            if M.IdentityCompare(
                                candidate,
                                M.EmptyList,
                            )() is M.truth_value:
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
                                elif M.IdentityCompare(
                                    value,
                                    M.truth_value,
                                )() is M.truth_value:
                                    if M.IdentityCompare(
                                        value,
                                        candidate,
                                    )() is M.false_value:
                                        conflicted = M.truth_value
                                elif M.IdentityCompare(
                                    value,
                                    M.false_value,
                                )() is M.truth_value:
                                    if M.IdentityCompare(
                                        value,
                                        candidate,
                                    )() is M.false_value:
                                        conflicted = M.truth_value
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
                        answer = M.EmptyList
                        if M.IdentityCompare(
                            value,
                            M.truth_value,
                        )() is M.truth_value:
                            answer = RenderPropositionSurface(value)()
                        elif M.IdentityCompare(
                            value,
                            M.false_value,
                        )() is M.truth_value:
                            answer = RenderPropositionSurface(value)()
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


class SurfaceEqualSplit(M.Edge):
    """Split a Surface chain at its first `equal to` marker."""

    def __init__(self, chain):
        self.result = M.EmptyList
        if M.IdentityCompare(chain, M.EmptyList)() is M.false_value:
            element = M.Head(chain)()
            remaining = M.Tail(chain)()
            if M.Compare(element, M.Char("equal"))() is M.truth_value:
                if M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
                    if M.Compare(M.Head(remaining)(), M.Char("to"))() is M.truth_value:
                        right = M.Tail(remaining)()
                        if M.IdentityCompare(right, M.EmptyList)() is M.false_value:
                            self.result = M.Pair(
                                M.EmptyList,
                                M.Pair(right, M.EmptyList),
                            )
            else:
                split = SurfaceEqualSplit(remaining)()
                if M.IdentityCompare(split, M.EmptyList)() is M.false_value:
                    left = M.Head(split)()
                    right = M.Head(M.Tail(split)())()
                    self.result = M.Pair(
                        M.Pair(element, left),
                        M.Pair(right, M.EmptyList),
                    )
        super().__init__(inputs=M.Pair(chain, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ConversePropositionInterpretations(M.Edge):
    """Interpret an equality question with independently parsed clauses."""

    def __init__(self, vocabulary, surface_term, registry):
        self.result = M.EmptyList
        chain = M.Head(M.Tail(surface_term)())()
        if M.IdentityCompare(chain, M.EmptyList)() is M.false_value:
            if M.Compare(M.Head(chain)(), M.Char("is"))() is M.truth_value:
                split = SurfaceEqualSplit(M.Tail(chain)())()
                if M.IdentityCompare(split, M.EmptyList)() is M.false_value:
                    left_chain = M.Head(split)()
                    right_chain = M.Head(M.Tail(split)())()
                    left = Converse(
                        vocabulary,
                        Surface(left_chain)(),
                        registry,
                    )()
                    left_outcome = M.Head(left)()
                    registry = M.Head(M.Tail(left)())()
                    right = Converse(
                        vocabulary,
                        Surface(right_chain)(),
                        registry,
                    )()
                    right_outcome = M.Head(right)()
                    registry = M.Head(M.Tail(right)())()
                    if M.IdentityCompare(
                        M.Head(left_outcome)(),
                        Lmod.UnderstoodLabel,
                    )() is M.truth_value:
                        if M.IdentityCompare(
                            M.Head(right_outcome)(),
                            Lmod.UnderstoodLabel,
                        )() is M.truth_value:
                            left_meaning = M.Head(
                                M.Tail(M.Tail(left_outcome)())(),
                            )()
                            right_meaning = M.Head(
                                M.Tail(M.Tail(right_outcome)())(),
                            )()
                            meaning = Meaning(
                                M.Pair(
                                    Lmod.EqualLabel,
                                    M.Pair(
                                        left_meaning,
                                        M.Pair(right_meaning, M.EmptyList),
                                    ),
                                ),
                            )()
                            self.result = M.Pair(
                                M.Pair(
                                    meaning,
                                    M.Pair(M.EmptyList, M.EmptyList),
                                ),
                                M.EmptyList,
                            )
        self.registry = registry
        super().__init__(
            inputs=M.Pair(
                vocabulary,
                M.Pair(surface_term, M.Pair(registry, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return M.Pair(self.result, M.Pair(self.registry, M.EmptyList))


class PropositionEvaluate(M.Edge):
    """Evaluate a proposition Meaning to the machine truth atoms.

    Even/Odd propositions evaluate through WitnessSearchEven: the verdict
    arrives with first-class evidence (Confirmed with a Witness, or
    Refuted with a reason), retained on self.evidence for the caller."""

    def __init__(self, meaning_term, word_entries, registry):
        value = M.EmptyList
        self.evidence = M.EmptyList
        body = meaning_term
        if M.IsPair(body)() is M.truth_value:
            if M.TermEqual(M.Head(body)(), Lmod.MeaningLabel)() is M.truth_value:
                body = M.Head(M.Tail(body)())()
        if M.IsPair(body)() is M.truth_value:
            is_even_prop = M.TermEqual(M.Head(body)(), Lmod.EvenPropLabel)()
            is_odd_prop = M.TermEqual(M.Head(body)(), Lmod.OddPropLabel)()
            if M.OrAtom(is_even_prop, is_odd_prop)() is M.truth_value:
                evaluated = MeaningEvaluate(
                    M.Head(M.Tail(body)())(),
                    word_entries,
                    registry,
                )()
                subject = M.Head(evaluated)()
                registry = M.Head(M.Tail(evaluated)())()
                if M.IdentityCompare(subject, M.EmptyList)() is M.false_value:
                    searched = WitnessSearchEven(
                        body,
                        subject,
                        registry,
                        odd=is_odd_prop,
                    )()
                    value = M.Head(searched)()
                    self.evidence = M.Head(M.Tail(searched)())()
                    registry = M.Head(M.Tail(M.Tail(searched)())())()
                self.result = M.Pair(value, M.Pair(registry, M.EmptyList))
                super().__init__(
                    inputs=M.Pair(
                        meaning_term,
                        M.Pair(word_entries, M.Pair(registry, M.EmptyList)),
                    ),
                    results=self.result,
                )
                return
            if M.TermEqual(M.Head(body)(), Lmod.EqualLabel)() is M.truth_value:
                arguments = M.Tail(body)()
                left = MeaningEvaluate(
                    M.Head(arguments)(),
                    word_entries,
                    registry,
                )()
                left_value = M.Head(left)()
                registry = M.Head(M.Tail(left)())()
                right = MeaningEvaluate(
                    M.Head(M.Tail(arguments)())(),
                    word_entries,
                    registry,
                )()
                right_value = M.Head(right)()
                registry = M.Head(M.Tail(right)())()
                if M.IdentityCompare(left_value, M.EmptyList)() is M.false_value:
                    if M.IdentityCompare(right_value, M.EmptyList)() is M.false_value:
                        value = M.NatEq(left_value, right_value, registry)()
        self.result = M.Pair(value, M.Pair(registry, M.EmptyList))
        super().__init__(
            inputs=M.Pair(
                meaning_term,
                M.Pair(word_entries, M.Pair(registry, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class RenderPropositionSurface(M.Edge):
    """Render a machine truth atom as the answer Surface `yes` or `no`."""

    def __init__(self, value):
        self.result = M.EmptyList
        if M.IdentityCompare(value, M.truth_value)() is M.truth_value:
            self.result = Surface(M.Pair(M.Char("yes"), M.EmptyList))()
        elif M.IdentityCompare(value, M.false_value)() is M.truth_value:
            self.result = Surface(M.Pair(M.Char("no"), M.EmptyList))()
        super().__init__(inputs=M.Pair(value, M.EmptyList), results=self.result)

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

    Accepted examples the parse law matches must agree in evaluated value
    with their recorded meaning and round-trip through the render law;
    accepted examples it does not match are evidence for other
    constructions and are skipped. The law must cover at least two
    accepted examples. Rejected examples must never match. Returns
    Pair(verdict, Pair(registry, EmptyList)).
    """

    def __init__(self, parse_law, render_law, examples, word_entries, registry):
        cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        verdict = M.truth_value
        covered_text = "0"
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
                        pass
                    else:
                        covered_text = GMPSuccText(covered_text)()
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
                        elif self._values_agree(
                            left_value,
                            right_value,
                            registry,
                        ) is M.false_value:
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
        if GMPLessText(covered_text, "2")() is M.truth_value:
            verdict = M.false_value
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

    def _values_agree(self, left_value, right_value, registry):
        # Nats compare by NatEq; symbolic values (Sqrt(7), Mul(three,
        # Sqrt(7))) have no Nat reading and compare structurally. Mixed
        # kinds disagree.
        left_nat = M.IsNat(left_value, registry)()
        right_nat = M.IsNat(right_value, registry)()
        if M.AndAtom(left_nat, right_nat)() is M.truth_value:
            return M.NatEq(left_value, right_value, registry)()
        if M.OrAtom(left_nat, right_nat)() is M.truth_value:
            return M.false_value
        return M.Compare(left_value, right_value)()

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


WITNESS_SEARCH_CAP = M.GMPRep("50")


class WitnessSearchDivides(M.Edge):
    """Bounded witness search for Divides(d, n): find k with d*k = n.

    Returns Pair(verdict, Pair(evidence, Pair(registry, EmptyList))),
    the WitnessSearchEven contract exactly: verdict truth/false/Empty,
    evidence Confirmed(prop, Witness(k)) or Refuted(prop, no-witness),
    refutation exact (candidates d*k grow monotonically past n), a cap
    hit answering EmptyList because absence of search is not absence
    of witness. d = 0 answers only when n = 0 (witness 0); the
    candidate never grows, so the walk is capped rather than watched.
    """

    def __init__(self, prop_term, divisor, n, registry):
        cap_text = M.GMPRepText(WITNESS_SEARCH_CAP)()
        d_rep = M.NatRepOf(divisor, registry)()
        n_rep = M.NatRepOf(n, registry)()
        verdict = M.EmptyList
        evidence = M.EmptyList
        if M.IdentityCompare(d_rep, M.EmptyList)() is M.false_value:
            if M.IdentityCompare(n_rep, M.EmptyList)() is M.false_value:
                d_text = M.GMPRepText(d_rep)()
                n_text = M.GMPRepText(n_rep)()
                k_text = "0"
                candidate_text = "0"
                searching = M.truth_value
                while M.IdentityCompare(
                    searching, M.truth_value,
                )() is M.truth_value:
                    searching = M.false_value
                    if GMPEqualText(k_text, cap_text)() is M.truth_value:
                        pass
                    elif GMPEqualText(candidate_text, n_text)() is M.truth_value:
                        witness_pair = M.NatFromRep(
                            M.GMPRep(k_text), registry,
                        )()
                        witness_nat = M.Head(witness_pair)()
                        registry = M.Head(M.Tail(witness_pair)())()
                        verdict = M.truth_value
                        evidence = M.Pair(
                            Lmod.ConfirmedLabel,
                            M.Pair(
                                prop_term,
                                M.Pair(
                                    M.Pair(
                                        Lmod.WitnessLabel,
                                        M.Pair(witness_nat, M.EmptyList),
                                    ),
                                    M.EmptyList,
                                ),
                            ),
                        )
                    elif GMPLessText(n_text, candidate_text)() is M.truth_value:
                        verdict = M.false_value
                        evidence = M.Pair(
                            Lmod.RefutedLabel,
                            M.Pair(
                                prop_term,
                                M.Pair(M.Char("no-witness"), M.EmptyList),
                            ),
                        )
                    elif GMPEqualText(d_text, "0")() is M.truth_value:
                        # 0*k never grows: n != 0 is refuted now, not
                        # at the cap.
                        verdict = M.false_value
                        evidence = M.Pair(
                            Lmod.RefutedLabel,
                            M.Pair(
                                prop_term,
                                M.Pair(M.Char("no-witness"), M.EmptyList),
                            ),
                        )
                    else:
                        k_text = GMPSuccText(k_text)()
                        candidate_text = GMPAddText(candidate_text, d_text)()
                        searching = M.truth_value
        self.result = M.Pair(
            verdict,
            M.Pair(evidence, M.Pair(registry, M.EmptyList)),
        )
        super().__init__(
            inputs=M.Pair(
                prop_term,
                M.Pair(divisor, M.Pair(n, M.Pair(registry, M.EmptyList))),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class ExactDivisorRestriction(M.Edge):
    """Check every divisor of n lies in the allowed chain.

    The primality shape, spoken generally: the parsed definition says
    'Divides restricted to exactly these fillers', and this edge asks
    whether n satisfies it. Walks d = 1..n under WITNESS_SEARCH_CAP;
    d divides n is decided by the same monotone multiple-walk as
    WitnessSearchDivides; a divisor outside `allowed_nats` refutes with
    that divisor as witness -- the counterexample is evidence, not a
    silent false. All divisors allowed confirms. n's rep missing or
    the cap reached before n answers EmptyList: not knowing is not no.

    Returns Pair(verdict, Pair(evidence, Pair(registry, EmptyList))).
    """

    def __init__(self, prop_term, n, allowed_nats, registry):
        cap_text = M.GMPRepText(WITNESS_SEARCH_CAP)()
        n_rep = M.NatRepOf(n, registry)()
        verdict = M.EmptyList
        evidence = M.EmptyList
        if M.IdentityCompare(n_rep, M.EmptyList)() is M.false_value:
            n_text = M.GMPRepText(n_rep)()
            allowed_texts = M.EmptyList
            allowed_walker = allowed_nats
            while M.IdentityCompare(
                allowed_walker, M.EmptyList,
            )() is M.false_value:
                allowed_rep = M.NatRepOf(M.Head(allowed_walker)(), registry)()
                if M.IdentityCompare(allowed_rep, M.EmptyList)() is M.false_value:
                    allowed_texts = M.Pair(
                        M.Char(M.GMPRepText(allowed_rep)()), allowed_texts,
                    )
                allowed_walker = M.Tail(allowed_walker)()
            d_text = "1"
            counterexample_text = ""
            complete = M.false_value
            walking = M.truth_value
            while M.IdentityCompare(walking, M.truth_value)() is M.truth_value:
                walking = M.false_value
                if GMPEqualText(d_text, cap_text)() is M.truth_value:
                    pass
                elif GMPLessText(n_text, d_text)() is M.truth_value:
                    complete = M.truth_value
                else:
                    multiple_text = d_text
                    divides = M.false_value
                    stepping = M.truth_value
                    while M.IdentityCompare(
                        stepping, M.truth_value,
                    )() is M.truth_value:
                        stepping = M.false_value
                        if GMPEqualText(multiple_text, n_text)() is M.truth_value:
                            divides = M.truth_value
                        elif GMPLessText(multiple_text, n_text)() is M.truth_value:
                            multiple_text = GMPAddText(multiple_text, d_text)()
                            stepping = M.truth_value
                    if M.IdentityCompare(divides, M.truth_value)() is M.truth_value:
                        allowed_here = M.false_value
                        allowed_probe = allowed_texts
                        while M.IdentityCompare(
                            allowed_probe, M.EmptyList,
                        )() is M.false_value:
                            if M.Compare(
                                M.Head(allowed_probe)(), M.Char(d_text),
                            )() is M.truth_value:
                                allowed_here = M.truth_value
                                allowed_probe = M.EmptyList
                            else:
                                allowed_probe = M.Tail(allowed_probe)()
                        if M.IdentityCompare(
                            allowed_here, M.false_value,
                        )() is M.truth_value:
                            counterexample_text = d_text
                    if counterexample_text == "":
                        d_text = GMPSuccText(d_text)()
                        walking = M.truth_value
            if counterexample_text != "":
                witness_pair = M.NatFromRep(
                    M.GMPRep(counterexample_text), registry,
                )()
                witness_nat = M.Head(witness_pair)()
                registry = M.Head(M.Tail(witness_pair)())()
                verdict = M.false_value
                evidence = M.Pair(
                    Lmod.RefutedLabel,
                    M.Pair(
                        prop_term,
                        M.Pair(
                            M.Pair(
                                Lmod.WitnessLabel,
                                M.Pair(witness_nat, M.EmptyList),
                            ),
                            M.EmptyList,
                        ),
                    ),
                )
            elif M.IdentityCompare(complete, M.truth_value)() is M.truth_value:
                verdict = M.truth_value
                evidence = M.Pair(
                    Lmod.ConfirmedLabel,
                    M.Pair(
                        prop_term,
                        M.Pair(M.Char("all-divisors-allowed"), M.EmptyList),
                    ),
                )
        self.result = M.Pair(
            verdict,
            M.Pair(evidence, M.Pair(registry, M.EmptyList)),
        )
        super().__init__(
            inputs=M.Pair(
                prop_term,
                M.Pair(n, M.Pair(allowed_nats, M.Pair(registry, M.EmptyList))),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class WitnessSearchEven(M.Edge):
    """Bounded witness search for Even(n): find k with k+k = n.

    Returns Pair(verdict, Pair(evidence, Pair(registry, EmptyList))).
    verdict is truth/false; evidence is Confirmed(prop, Witness(k)) or
    Refuted(prop, no-witness) -- first-class terms, not silent absences.
    The search walks k = 0,1,2,... under WITNESS_SEARCH_CAP; a cap hit
    refutes nothing and returns EmptyList verdict (the machine does not
    know), because absence of search is not absence of witness.
    """

    def __init__(self, prop_term, n, registry, odd=M.false_value):
        cap_text = M.GMPRepText(WITNESS_SEARCH_CAP)()
        n_rep = M.NatRepOf(n, registry)()
        verdict = M.EmptyList
        evidence = M.EmptyList
        if M.IdentityCompare(n_rep, M.EmptyList)() is M.false_value:
            n_text = M.GMPRepText(n_rep)()
            k_text = "0"
            searching = M.truth_value
            while M.IdentityCompare(searching, M.truth_value)() is M.truth_value:
                searching = M.false_value
                if GMPEqualText(k_text, cap_text)() is M.truth_value:
                    pass
                else:
                    double_text = GMPAddText(k_text, k_text)()
                    candidate_text = double_text
                    if M.IdentityCompare(odd, M.truth_value)() is M.truth_value:
                        candidate_text = GMPSuccText(double_text)()
                    if GMPEqualText(candidate_text, n_text)() is M.truth_value:
                        witness_pair = M.NatFromRep(
                            M.GMPRep(k_text),
                            registry,
                        )()
                        witness_nat = M.Head(witness_pair)()
                        registry = M.Head(M.Tail(witness_pair)())()
                        verdict = M.truth_value
                        evidence = M.Pair(
                            Lmod.ConfirmedLabel,
                            M.Pair(
                                prop_term,
                                M.Pair(
                                    M.Pair(
                                        Lmod.WitnessLabel,
                                        M.Pair(witness_nat, M.EmptyList),
                                    ),
                                    M.EmptyList,
                                ),
                            ),
                        )
                    elif GMPLessText(n_text, candidate_text)() is M.truth_value:
                        # Candidates grow monotonically; passing n proves
                        # no witness exists. This refutation is exact, not
                        # a cap artifact.
                        verdict = M.false_value
                        evidence = M.Pair(
                            Lmod.RefutedLabel,
                            M.Pair(
                                prop_term,
                                M.Pair(M.Char("no-witness"), M.EmptyList),
                            ),
                        )
                    else:
                        k_text = GMPSuccText(k_text)()
                        searching = M.truth_value
        self.result = M.Pair(
            verdict,
            M.Pair(evidence, M.Pair(registry, M.EmptyList)),
        )
        super().__init__(
            inputs=M.Pair(
                prop_term,
                M.Pair(n, M.Pair(registry, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class Definition(M.Edge):
    """A taught definition: one term names a surface phrase built of words.

    Pair(DefinitionLabel, Pair(term_word, Pair(body_surface, EmptyList))).
    The body is an ordinary Surface chain; its words are the definition's
    dependencies, and each dependency is either defined (a word entry, a
    template mention, or another Definition) or an open hole the machine
    should ask about. Definitions live as nodes in the learned version, so
    they persist through the same checkpoint as every learned law.
    """

    def __init__(self, term_word, body_surface):
        self.result = M.Pair(
            Lmod.DefinitionLabel,
            M.Pair(term_word, M.Pair(body_surface, M.EmptyList)),
        )
        super().__init__(
            inputs=M.Pair(term_word, M.Pair(body_surface, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class IsDefinition(M.Edge):
    def __init__(self, term):
        self.result = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if M.TermEqual(
                M.Head(term)(),
                Lmod.DefinitionLabel,
            )() is M.truth_value:
                self.result = M.truth_value
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class DefinitionTerm(M.Edge):
    def __init__(self, definition):
        self.result = M.Head(M.Tail(definition)())()
        super().__init__(
            inputs=M.Pair(definition, M.EmptyList),
            results=self.result,
        )

    def __call__(self):
        return self.result


class DefinitionBody(M.Edge):
    def __init__(self, definition):
        self.result = M.Head(M.Tail(M.Tail(definition)())())()
        super().__init__(
            inputs=M.Pair(definition, M.EmptyList),
            results=self.result,
        )

    def __call__(self):
        return self.result


class DefinitionNode(M.Edge):
    """A definition as a graph: what is defined, under which self, on what terms.

    Pair(DefinitionNodeLabel, Pair(definiendum, Pair(binder,
    Pair(conditions, EmptyList)))). The definiendum is a typed term,
    Definiendum(concept, Category(atom)), not a word; the binder holds
    one scope and one fresh variable that every reflexive in the
    conditions resolves to; the conditions are a chain of predicate
    terms, in which an undefined predicate stays as a Hole rather than
    disappearing. The shape is declared with a ConstructorSignature, so
    the formal reader writes and reads it like any constructor. This is
    what a definition Reading's meaning is: the graph is the output of
    parsing, not a byproduct of it.
    """

    def __init__(self, definiendum, binder, conditions):
        self.result = M.Pair(
            Lmod.DefinitionNodeLabel,
            M.Pair(
                definiendum, M.Pair(binder, M.Pair(conditions, M.EmptyList)),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                definiendum, M.Pair(binder, M.Pair(conditions, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class DefinitionNodeDefiniendum(M.Edge):
    def __init__(self, node):
        self.result = M.Head(M.Tail(node)())()
        super().__init__(inputs=M.Pair(node, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class DefinitionNodeBinder(M.Edge):
    def __init__(self, node):
        self.result = M.Head(M.Tail(M.Tail(node)())())()
        super().__init__(inputs=M.Pair(node, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class DefinitionNodeConditions(M.Edge):
    def __init__(self, node):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(node)())())())()
        super().__init__(inputs=M.Pair(node, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class Definiendum(M.Edge):
    """The thing defined: a concept over a category, not a word."""

    def __init__(self, concept, category):
        self.result = M.Pair(
            Lmod.DefiniendumLabel,
            M.Pair(concept, M.Pair(category, M.EmptyList)),
        )
        super().__init__(
            inputs=M.Pair(concept, M.Pair(category, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class CategoryTerm(M.Edge):
    """Category(atom): the sort a definiendum is over."""

    def __init__(self, category):
        self.result = M.Pair(
            Lmod.CategoryLabel, M.Pair(category, M.EmptyList),
        )
        super().__init__(
            inputs=M.Pair(category, M.EmptyList), results=self.result,
        )

    def __call__(self):
        return self.result


class Binder(M.Edge):
    """One scope and the fresh self every reflexive resolves to.

    Pair(BinderLabel, Pair(scope, Pair(self, EmptyList))). The self is
    one variable object shared by every condition that mentions it;
    the scope tells this definition's applications apart from the next.
    """

    def __init__(self, scope, self_variable):
        self.result = M.Pair(
            Lmod.BinderLabel,
            M.Pair(scope, M.Pair(self_variable, M.EmptyList)),
        )
        super().__init__(
            inputs=M.Pair(scope, M.Pair(self_variable, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class BinderScope(M.Edge):
    def __init__(self, binder):
        self.result = M.Head(M.Tail(binder)())()
        super().__init__(inputs=M.Pair(binder, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class BinderSelf(M.Edge):
    def __init__(self, binder):
        self.result = M.Head(M.Tail(M.Tail(binder)())())()
        super().__init__(inputs=M.Pair(binder, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class Divides(M.Edge):
    """Divides(divisor, number): the divisibility predicate."""

    def __init__(self, divisor, number):
        self.result = M.Pair(
            Lmod.DividesLabel,
            M.Pair(divisor, M.Pair(number, M.EmptyList)),
        )
        super().__init__(
            inputs=M.Pair(divisor, M.Pair(number, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class Hole(M.Edge):
    """An undefined predicate kept as a named gap in a formed graph.

    Pair(HoleLabel, Pair(predicate, Pair(arguments, Pair(reason,
    EmptyList)))). The predicate is its label, the arguments are the
    chain it would take, and the reason says why it is open. A hole is
    what lets the graph exist before every word in it is defined; the
    dependency question is then read off the hole, not off the words.
    """

    def __init__(self, predicate, arguments, reason):
        self.result = M.Pair(
            Lmod.HoleLabel,
            M.Pair(
                predicate, M.Pair(arguments, M.Pair(reason, M.EmptyList)),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                predicate, M.Pair(arguments, M.Pair(reason, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class HolePredicate(M.Edge):
    def __init__(self, hole):
        self.result = M.Head(M.Tail(hole)())()
        super().__init__(inputs=M.Pair(hole, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class HoleArguments(M.Edge):
    def __init__(self, hole):
        self.result = M.Head(M.Tail(M.Tail(hole)())())()
        super().__init__(inputs=M.Pair(hole, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ExactFillers(M.Edge):
    """A restriction kept as scope, not flattened to a quantifier.

    "only" becomes one of these rather than a ForAll, so the parse
    records what was said and a normalization law can expand it later.

    Pair(ExactFillersLabel, Pair(relation, Pair(fixed, Pair(role,
    Pair(allowed, EmptyList))))). Of the relation, the fixed argument
    stays, the role named is the one being restricted, and the allowed
    chain holds everything that may fill it. The parser records what
    was said; expanding this into a quantifier is a normalization law's
    job, checked on its own.
    """

    def __init__(self, relation, fixed, role, allowed):
        self.result = M.Pair(
            Lmod.ExactFillersLabel,
            M.Pair(
                relation,
                M.Pair(fixed, M.Pair(role, M.Pair(allowed, M.EmptyList))),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                relation,
                M.Pair(fixed, M.Pair(role, M.Pair(allowed, M.EmptyList))),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class DefinitionNodeWellFormed(M.Edge):
    """One certificate: this term is a well-formed definition graph.

    The checks are the shape itself: the label; three slots exactly; a
    definiendum of two slots whose second is a Category term; a binder
    of two slots whose second slot is a variable; conditions that are a
    chain of terms. Nothing here knows any predicate -- a hole is as
    well-formed as a defined condition, because a hole is the point.
    """

    def __init__(self, node):
        self.result = M.false_value
        if M.IsPair(node)() is M.truth_value:
            if M.IdentityCompare(
                M.Head(node)(), Lmod.DefinitionNodeLabel,
            )() is M.truth_value:
                slots = M.Tail(node)()
                if M.IdentityCompare(slots, M.EmptyList)() is M.false_value:
                    rest_one = M.Tail(slots)()
                    if M.IdentityCompare(
                        rest_one, M.EmptyList,
                    )() is M.false_value:
                        rest_two = M.Tail(rest_one)()
                        if M.IdentityCompare(
                            rest_two, M.EmptyList,
                        )() is M.false_value:
                            if M.IdentityCompare(
                                M.Tail(rest_two)(), M.EmptyList,
                            )() is M.truth_value:
                                definiendum = M.Head(slots)()
                                binder = M.Head(rest_one)()
                                conditions = M.Head(rest_two)()
                                if self._definiendum_ok(definiendum) is M.truth_value:
                                    if self._binder_ok(binder) is M.truth_value:
                                        if self._conditions_ok(conditions) is M.truth_value:
                                            self.result = M.truth_value
        super().__init__(
            inputs=M.Pair(node, M.EmptyList), results=self.result,
        )

    def _definiendum_ok(self, definiendum):
        if M.IsPair(definiendum)() is M.false_value:
            return M.false_value
        if M.IdentityCompare(
            M.Head(definiendum)(), Lmod.DefiniendumLabel,
        )() is M.false_value:
            return M.false_value
        slots = M.Tail(definiendum)()
        if M.IdentityCompare(slots, M.EmptyList)() is M.truth_value:
            return M.false_value
        rest = M.Tail(slots)()
        if M.IdentityCompare(rest, M.EmptyList)() is M.truth_value:
            return M.false_value
        if M.IdentityCompare(M.Tail(rest)(), M.EmptyList)() is M.false_value:
            return M.false_value
        category = M.Head(rest)()
        if M.IsPair(category)() is M.false_value:
            return M.false_value
        if M.IdentityCompare(
            M.Head(category)(), Lmod.CategoryLabel,
        )() is M.false_value:
            return M.false_value
        category_slots = M.Tail(category)()
        if M.IdentityCompare(
            category_slots, M.EmptyList,
        )() is M.truth_value:
            return M.false_value
        if M.IdentityCompare(
            M.Tail(category_slots)(), M.EmptyList,
        )() is M.false_value:
            return M.false_value
        return M.truth_value

    def _binder_ok(self, binder):
        if M.IsPair(binder)() is M.false_value:
            return M.false_value
        if M.IdentityCompare(
            M.Head(binder)(), Lmod.BinderLabel,
        )() is M.false_value:
            return M.false_value
        slots = M.Tail(binder)()
        if M.IdentityCompare(slots, M.EmptyList)() is M.truth_value:
            return M.false_value
        rest = M.Tail(slots)()
        if M.IdentityCompare(rest, M.EmptyList)() is M.truth_value:
            return M.false_value
        if M.IdentityCompare(M.Tail(rest)(), M.EmptyList)() is M.false_value:
            return M.false_value
        self_variable = M.Head(rest)()
        if M.IsPair(self_variable)() is M.false_value:
            return M.false_value
        if M.IdentityCompare(
            M.Head(self_variable)(), M.VarTag,
        )() is M.false_value:
            return M.false_value
        return M.truth_value

    def _conditions_ok(self, conditions):
        walker = conditions
        while M.IdentityCompare(walker, M.EmptyList)() is M.false_value:
            if M.IsPair(M.Head(walker)())() is M.false_value:
                return M.false_value
            walker = M.Tail(walker)()
        return M.truth_value

    def __call__(self):
        return self.result


class InstalledDefinitions(M.Edge):
    """Every Definition node in a version, in store order."""

    def __init__(self, graph_version):
        cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        reversed_definitions = M.EmptyList
        scan_text = "0"
        remaining = GraphNodes(graph_version)()
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                remaining = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                node = M.Head(remaining)()
                if IsDefinition(node)() is M.truth_value:
                    reversed_definitions = M.Pair(node, reversed_definitions)
                remaining = M.Tail(remaining)()
        self.result = M.Reverse(reversed_definitions)()
        super().__init__(
            inputs=M.Pair(graph_version, M.EmptyList),
            results=self.result,
        )

    def __call__(self):
        return self.result


class DefinitionFor(M.Edge):
    """The Definition whose term is `word`, or EmptyList."""

    def __init__(self, graph_version, word):
        cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        self.result = M.EmptyList
        scan_text = "0"
        remaining = InstalledDefinitions(graph_version)()
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                remaining = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                definition = M.Head(remaining)()
                if M.Compare(DefinitionTerm(definition)(), word)() is M.truth_value:
                    self.result = definition
                    remaining = M.EmptyList
                else:
                    remaining = M.Tail(remaining)()
        super().__init__(
            inputs=M.Pair(graph_version, M.Pair(word, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


DEFINITION_STOP_WORDS = M.Pair(
    M.Char("a"),
    M.Pair(
        M.Char("an"),
        M.Pair(
            M.Char("the"),
            M.Pair(
                M.Char("is"),
                M.Pair(
                    M.Char("are"),
                    M.Pair(
                        M.Char("with"),
                        M.Pair(
                            M.Char("of"),
                            M.Pair(
                                M.Char("and"),
                                M.Pair(
                                    M.Char("that"),
                                    M.Pair(
                                        M.Char("which"),
                                        M.Pair(
                                            M.Char("has"),
                                            M.Pair(
                                                M.Char("have"),
                                                M.EmptyList,
                                            ),
                                        ),
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


class DefinitionOpenDependencies(M.Edge):
    """Body words that are neither vocabulary, stop words, numbers, the
    defined term itself, nor covered by another installed Definition.

    These are the holes: the words the machine should ask about next.
    Order follows the body; duplicates collapse to first appearance.
    """

    def __init__(self, graph_version, definition, vocabulary, registry):
        cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        term_word = DefinitionTerm(definition)()
        body = DefinitionBody(definition)()
        reversed_open = M.EmptyList
        scan_text = "0"
        chain = M.Head(M.Tail(body)())()
        while M.IdentityCompare(chain, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                chain = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                word = M.Head(chain)()
                known = M.false_value
                if M.Compare(word, term_word)() is M.truth_value:
                    known = M.truth_value
                if M.IdentityCompare(known, M.false_value)() is M.truth_value:
                    if ChainHasWordStructural(
                        DEFINITION_STOP_WORDS,
                        word,
                    )() is M.truth_value:
                        known = M.truth_value
                if M.IdentityCompare(known, M.false_value)() is M.truth_value:
                    single = Surface(M.Pair(word, M.EmptyList))()
                    unknown = SurfaceUnknownWords(
                        vocabulary,
                        single,
                        registry,
                    )()
                    if M.IdentityCompare(unknown, M.EmptyList)() is M.truth_value:
                        known = M.truth_value
                if M.IdentityCompare(known, M.false_value)() is M.truth_value:
                    defined = DefinitionFor(graph_version, word)()
                    if M.IdentityCompare(defined, M.EmptyList)() is M.false_value:
                        known = M.truth_value
                if M.IdentityCompare(known, M.false_value)() is M.truth_value:
                    # 'three sides' depends on the concept 'side': a plural
                    # surface form is grounded by its singular definition.
                    singular = WordSingular(word)()
                    if M.IdentityCompare(singular, M.EmptyList)() is M.false_value:
                        defined = DefinitionFor(graph_version, singular)()
                        if M.IdentityCompare(
                            defined, M.EmptyList,
                        )() is M.false_value:
                            known = M.truth_value
                if M.IdentityCompare(known, M.false_value)() is M.truth_value:
                    if ChainHasWordStructural(
                        M.Reverse(reversed_open)(),
                        word,
                    )() is M.false_value:
                        reversed_open = M.Pair(word, reversed_open)
                chain = M.Tail(chain)()
        self.result = M.Reverse(reversed_open)()
        super().__init__(
            inputs=M.Pair(
                graph_version,
                M.Pair(
                    definition,
                    M.Pair(vocabulary, M.Pair(registry, M.EmptyList)),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class WordSingular(M.Edge):
    """The singular Char for a plural word atom, or EmptyList.

    Chars carry their symbol at the host boundary by construction; this
    reads that boundary the same way the tokenizer wrote it. Only the
    plain '-s' form is folded -- irregular plurals stay open holes, which
    is the machine asking rather than guessing.
    """

    def __init__(self, word):
        self.result = M.EmptyList
        symbol = getattr(word, "symbol", None)
        if symbol is not None:
            if len(symbol) > 2 and symbol.endswith("s") and not symbol.endswith("ss"):
                self.result = M.Char(symbol[:-1])
        super().__init__(inputs=M.Pair(word, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ChainHasWordStructural(M.Edge):
    """Structural membership for word atoms (Compare, not identity)."""

    def __init__(self, chain, word):
        cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        self.result = M.false_value
        scan_text = "0"
        remaining = chain
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                remaining = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                if M.Compare(M.Head(remaining)(), word)() is M.truth_value:
                    self.result = M.truth_value
                    remaining = M.EmptyList
                else:
                    remaining = M.Tail(remaining)()
        super().__init__(
            inputs=M.Pair(chain, M.Pair(word, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class BridgeFor(M.Edge):
    """The Corresponds node linking `word` to a constructor, or EmptyList.

    A bridge is Pair(CorrespondsLabel, Pair(Surface([word]),
    Pair(label, Pair(EmptyList, EmptyList)))) spliced into the learned
    version: the word's meaning IS the pack constructor, recorded as a
    version node so it persists through the same checkpoint as every
    definition and law.
    """

    def __init__(self, graph_version, word):
        cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        self.result = M.EmptyList
        scan_text = "0"
        remaining = GraphNodes(graph_version)()
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                remaining = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                node = M.Head(remaining)()
                if M.IsPair(node)() is M.truth_value:
                    if M.TermEqual(
                        M.Head(node)(),
                        Lmod.CorrespondsLabel,
                    )() is M.truth_value:
                        node_surface = M.Head(M.Tail(node)())()
                        chain = M.Head(M.Tail(node_surface)())()
                        if M.IdentityCompare(
                            chain, M.EmptyList,
                        )() is M.false_value:
                            if M.Compare(
                                M.Head(chain)(), word,
                            )() is M.truth_value:
                                self.result = node
                                remaining = M.EmptyList
                if M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
                    remaining = M.Tail(remaining)()
        super().__init__(
            inputs=M.Pair(graph_version, M.Pair(word, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class BridgeConstructor(M.Edge):
    """The constructor label a bridge node points at."""

    def __init__(self, bridge):
        self.result = M.Head(M.Tail(M.Tail(bridge)())())()
        super().__init__(
            inputs=M.Pair(bridge, M.EmptyList),
            results=self.result,
        )

    def __call__(self):
        return self.result


class InstallBridge(M.Edge):
    """Splice a word-to-constructor Corresponds node into the version.

    Returns Pair(new_version, EmptyList), or the unchanged version with
    the existing bridge at the tail when the word is already linked.
    """

    def __init__(self, graph_version, word, constructor_label):
        existing = BridgeFor(graph_version, word)()
        if M.IdentityCompare(existing, M.EmptyList)() is M.false_value:
            self.result = M.Pair(graph_version, M.Pair(existing, M.EmptyList))
        else:
            bridge = Corresponds(
                Surface(M.Pair(word, M.EmptyList))(),
                constructor_label,
                M.EmptyList,
            )()
            next_version = GraphVersion(
                M.Pair(bridge, GraphNodes(graph_version)()),
                GraphEdges(graph_version)(),
                GraphVersionInvariants(graph_version)(),
            )()
            self.result = M.Pair(next_version, M.EmptyList)
        super().__init__(
            inputs=M.Pair(
                graph_version,
                M.Pair(word, M.Pair(constructor_label, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


ONTOLOGY_FACT_CAP = M.GMPRep("200")


class OntologyFactsFor(M.Edge):
    """Replacement heads of every installed rule whose pattern names `label`.

    The pack ontology is a rule graph: TriangleLabel(shape) rewrites to
    PolygonLabel(shape), EdgesLabel(shape), and so on. Those replacement
    heads ARE the constructor's ontology facts -- what a triangle is and
    has, exactly as the packs authored it. Walks the rule tree entries
    under ONTOLOGY_FACT_CAP; duplicate heads collapse to first appearance.
    """

    def __init__(self, rules_tree, label, registry):
        cap_text = M.GMPRepText(ONTOLOGY_FACT_CAP)()
        reversed_facts = M.EmptyList
        scan_text = "0"
        entries = M.TreeEntries(rules_tree)()
        while M.IdentityCompare(entries, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                entries = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                rule = M.Head(M.Tail(M.Head(entries)())())()
                pattern = M.Head(M.Head(rule.inputs)())()
                if M.IsPair(pattern)() is M.truth_value:
                    if M.IdentityCompare(
                        M.Head(pattern)(), label,
                    )() is M.truth_value:
                        # Head() of the replacement term unwraps straight
                        # to the constructor label atom: the fact itself.
                        fact_head = M.Head(
                            M.Head(M.Tail(rule.inputs)())(),
                        )()
                        if M.IdentityCompare(
                            fact_head, M.EmptyList,
                        )() is M.false_value:
                            if ChainHasTerm(
                                M.Reverse(reversed_facts)(),
                                fact_head,
                            )() is M.false_value:
                                reversed_facts = M.Pair(
                                    fact_head,
                                    reversed_facts,
                                )
                entries = M.Tail(entries)()
        self.result = M.Reverse(reversed_facts)()
        super().__init__(
            inputs=M.Pair(
                rules_tree,
                M.Pair(label, M.Pair(registry, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class RulePatternHeads(M.Edge):
    """Every constructor atom heading an installed rule's pattern.

    Walks the loaded rule tree under ONTOLOGY_FACT_CAP; duplicates
    collapse by identity. This is the machine's own answer to 'which
    constructors do rules fire on' -- the filter the bridge noticing
    uses, read from loaded structure rather than re-parsed sources.
    """

    def __init__(self, rules_tree, registry):
        cap_text = M.GMPRepText(ONTOLOGY_FACT_CAP)()
        reversed_heads = M.EmptyList
        scan_text = "0"
        entries = M.TreeEntries(rules_tree)()
        while M.IdentityCompare(entries, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                entries = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                rule = M.Head(M.Tail(M.Head(entries)())())()
                pattern = M.Head(M.Head(rule.inputs)())()
                if M.IsPair(pattern)() is M.truth_value:
                    head = M.Head(pattern)()
                    if ChainHasTerm(
                        M.Reverse(reversed_heads)(),
                        head,
                    )() is M.false_value:
                        reversed_heads = M.Pair(head, reversed_heads)
                entries = M.Tail(entries)()
        self.result = M.Reverse(reversed_heads)()
        super().__init__(
            inputs=M.Pair(rules_tree, M.Pair(registry, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class DefinitionBodyReading(M.Edge):
    """The Meaning a definition body parses to, through the ordinary templates.

    The body is a sentence and is read like one: ConverseInterpretations
    runs the correspondence templates against it, and the definition-body
    templates in the vocabulary turn "a polygon with three sides" into
    DefinitionCounted(polygon, three, sides) and "a shape" into
    DefinitionGenus(shape). A body with no reading, or with disagreeing
    readings, yields EmptyList -- the machine does not pick one for the
    trainer.

    This replaces a host-side word list and a hand-written state machine.
    A new phrasing is now a new template law, not a new branch.
    """

    def __init__(self, definition, vocabulary, registry):
        self.result = M.EmptyList
        body = DefinitionBody(definition)()
        readings = M.Head(
            ConverseInterpretations(vocabulary, body, registry)(),
        )()
        if M.IdentityCompare(readings, M.EmptyList)() is M.false_value:
            if M.IdentityCompare(
                M.Tail(readings)(), M.EmptyList,
            )() is M.truth_value:
                self.result = M.Head(M.Head(readings)())()
        super().__init__(
            inputs=M.Pair(
                definition,
                M.Pair(vocabulary, M.Pair(registry, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class ReadingWordConstructor(M.Edge):
    """The constructor a slot of a parsed reading names, or EmptyList.

    A template slot holds a Surface of one word. The word denotes pack
    structure when a bridge links it -- directly, or through its singular,
    so "sides" grounds on "side".
    """

    def __init__(self, graph_version, slot):
        self.result = M.EmptyList
        chain = M.Head(M.Tail(slot)())()
        if M.IdentityCompare(chain, M.EmptyList)() is M.false_value:
            word = M.Head(chain)()
            bridge = BridgeFor(graph_version, word)()
            if M.IdentityCompare(bridge, M.EmptyList)() is M.truth_value:
                singular = WordSingular(word)()
                if M.IdentityCompare(
                    singular, M.EmptyList,
                )() is M.false_value:
                    bridge = BridgeFor(graph_version, singular)()
            if M.IdentityCompare(bridge, M.EmptyList)() is M.false_value:
                self.result = BridgeConstructor(bridge)()
        super().__init__(
            inputs=M.Pair(graph_version, M.Pair(slot, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class ReadingWordNat(M.Edge):
    """The Nat a slot of a parsed reading names, or EmptyList."""

    def __init__(self, slot, word_entries):
        self.result = CorrespondenceResolveWord(word_entries, slot)()
        super().__init__(
            inputs=M.Pair(slot, M.Pair(word_entries, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class CompileDefinitionToLaws(M.Edge):
    """A taught definition becomes the same rule shape the packs author.

    "a triangle is a figure with three sides" is not prose to be recited.
    Its subject bridges to TriangleLabel and its body names constructors
    through their own bridges, so the definition asserts that whatever is
    a triangle is also each of those things. That is exactly the pack
    ontology's own form:

        pattern      Triangle(?shape)
        replacement  Polygon(?shape)

    One rule per named body constructor, each compiled through the same
    CompileRuleToLaw the packs go through, so a taught concept enters the
    rule graph as structure rather than as a sentence. Returns EmptyList
    when the subject has no bridge or the body names nothing: a definition
    the machine cannot ground stays a definition and is not guessed at.
    """

    def __init__(self, graph_version, definition,
                 vocabulary=M.EmptyList, registry=M.EmptyList):
        word_entries = M.EmptyList
        if M.IdentityCompare(vocabulary, M.EmptyList)() is M.false_value:
            word_entries = M.Head(M.Tail(vocabulary)())()
        self.result = M.EmptyList
        subject_bridge = BridgeFor(
            graph_version,
            DefinitionTerm(definition)(),
        )()
        if M.IdentityCompare(
            subject_bridge, M.EmptyList,
        )() is M.false_value:
            subject = BridgeConstructor(subject_bridge)()
            shape = M.Pair(
                M.VarTag,
                M.Pair(M.Char("shape"), M.EmptyList),
            )
            pattern = M.Pair(subject, M.Pair(shape, M.EmptyList))
            reversed_laws = M.EmptyList
            reversed_premises = M.EmptyList
            # The body is read by the ordinary correspondence templates,
            # so what arrives here is a Meaning term -- a graph -- not a
            # chain of words to scan. DefinitionGenus(x) says the subject
            # IS an x; DefinitionCounted(x, n, y) says it is an x with n
            # y's. Each becomes a forward rule over a shared ?shape.
            reading = DefinitionBodyReading(
                definition,
                vocabulary,
                registry,
            )()
            if M.IdentityCompare(reading, M.EmptyList)() is M.false_value:
                body_term = M.Head(M.Tail(reading)())()
                reading_head = M.Head(body_term)()
                genus_slot = M.Head(M.Tail(body_term)())()
                genus = ReadingWordConstructor(graph_version, genus_slot)()
                if M.IdentityCompare(genus, M.EmptyList)() is M.false_value:
                    replacement = M.Pair(genus, M.Pair(shape, M.EmptyList))
                    reversed_premises = M.Pair(
                        replacement, reversed_premises,
                    )
                    rule = P.Rule(pattern, replacement)
                    law = CompileRuleToLaw(rule)()
                    if M.IdentityCompare(
                        law, M.EmptyList,
                    )() is M.false_value:
                        # Carry the rule beside its law: a version stores
                        # laws and a runtime fires rules, and nothing
                        # decompiles one into the other.
                        reversed_laws = M.Pair(
                            M.Pair(law, M.Pair(rule, M.EmptyList)),
                            reversed_laws,
                        )
                if M.IdentityCompare(
                    reading_head, M.DefinitionCountedLabel,
                )() is M.truth_value:
                    rest = M.Tail(M.Tail(body_term)())()
                    count_slot = M.Head(rest)()
                    noun_slot = M.Head(M.Tail(rest)())()
                    counted = ReadingWordNat(count_slot, word_entries)()
                    noun = ReadingWordConstructor(graph_version, noun_slot)()
                    if M.IdentityCompare(
                        counted, M.EmptyList,
                    )() is M.false_value:
                        if M.IdentityCompare(
                            noun, M.EmptyList,
                        )() is M.false_value:
                            replacement = M.Pair(
                                noun,
                                M.Pair(
                                    shape,
                                    M.Pair(counted, M.EmptyList),
                                ),
                            )
                            reversed_premises = M.Pair(
                                replacement, reversed_premises,
                            )
                            rule = P.Rule(pattern, replacement)
                            law = CompileRuleToLaw(rule)()
                            if M.IdentityCompare(
                                law, M.EmptyList,
                            )() is M.false_value:
                                reversed_laws = M.Pair(
                                    M.Pair(law, M.Pair(rule, M.EmptyList)),
                                    reversed_laws,
                                )
            # A definition is a biconditional. The forward arrows above say
            # what a triangle is; this is the arrow back -- from a polygon
            # that has three edges, conclude a triangle. It is genuinely
            # multi-premise, which is why the conjunctive compiler exists.
            premises = M.Reverse(reversed_premises)()
            if M.IdentityCompare(premises, M.EmptyList)() is M.false_value:
                if M.IdentityCompare(
                    M.Tail(premises)(), M.EmptyList,
                )() is M.false_value:
                    converse = P.MultiRule(premises, pattern)
                    converse_law = CompileMultiRuleToLaw(converse)()
                    if M.IdentityCompare(
                        converse_law, M.EmptyList,
                    )() is M.false_value:
                        reversed_laws = M.Pair(
                            M.Pair(
                                converse_law,
                                M.Pair(converse, M.EmptyList),
                            ),
                            reversed_laws,
                        )
            self.result = M.Reverse(reversed_laws)()
        super().__init__(
            inputs=M.Pair(graph_version, M.Pair(definition, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class InstallDefinitionLaws(M.Edge):
    """Install every law a definition compiles to; return the new version.

    The version is threaded through InstallLaw one law at a time, so a
    taught concept lands in the same place pack laws land and the search
    considers it on the same terms. A definition that compiles to nothing
    leaves the version untouched.
    """

    def __init__(self, graph_version, definition,
                 vocabulary=M.EmptyList, registry=M.EmptyList):
        current = graph_version
        installed_count = M.Zero
        remaining = CompileDefinitionToLaws(
            graph_version, definition, vocabulary, registry,
        )()
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            current = InstallLaw(current, M.Head(M.Head(remaining)())())()
            stepped = M.Succ(installed_count, M.AllConstructors)()
            installed_count = M.Head(stepped)()
            remaining = M.Tail(remaining)()
        self.result = M.Pair(current, M.Pair(installed_count, M.EmptyList))
        super().__init__(
            inputs=M.Pair(graph_version, M.Pair(definition, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class DefinitionRulesFor(M.Edge):
    """The rewrite rules a definition compiles to, without installing them.

    A version stores laws; a proof runtime fires rules. Both come from the
    same compilation, so this hands the rule side to whoever needs to
    teach a runtime what the trainer taught the conversation.
    """

    def __init__(self, graph_version, definition,
                 vocabulary=M.EmptyList, registry=M.EmptyList):
        reversed_rules = M.EmptyList
        remaining = CompileDefinitionToLaws(
            graph_version, definition, vocabulary, registry,
        )()
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            pair = M.Head(remaining)()
            reversed_rules = M.Pair(M.Head(M.Tail(pair)())(), reversed_rules)
            remaining = M.Tail(remaining)()
        self.result = M.Reverse(reversed_rules)()
        super().__init__(
            inputs=M.Pair(graph_version, M.Pair(definition, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class TaughtDefinitionRules(M.Edge):
    """Every rule every installed Definition in a version compiles to.

    The conversation and the prover kept two rule sets: laws taught here
    never reached the pack-booted runtime that answers 'solve the tao
    triangle problem', so a taught concept could not participate in a
    proof. This is the whole taught ontology in the form a runtime
    accepts, so the two sets can be made one.
    """

    def __init__(self, graph_version,
                 vocabulary=M.EmptyList, registry=M.EmptyList):
        reversed_rules = M.EmptyList
        remaining = InstalledDefinitions(graph_version)()
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            definition = M.Head(remaining)()
            rules = DefinitionRulesFor(
                graph_version, definition, vocabulary, registry,
            )()
            while M.IdentityCompare(rules, M.EmptyList)() is M.false_value:
                reversed_rules = M.Pair(M.Head(rules)(), reversed_rules)
                rules = M.Tail(rules)()
            remaining = M.Tail(remaining)()
        self.result = M.Reverse(reversed_rules)()
        super().__init__(
            inputs=M.Pair(graph_version, M.EmptyList),
            results=self.result,
        )

    def __call__(self):
        return self.result


class InstallDefinition(M.Edge):
    """Splice a Definition node into the version; append-only Next history.

    Returns Pair(new_version, EmptyList). A definition for an
    already-defined term returns the version unchanged and the existing
    Definition at the head of the tail for the caller to report.
    """

    def __init__(self, graph_version, definition):
        existing = DefinitionFor(
            graph_version,
            DefinitionTerm(definition)(),
        )()
        if M.IdentityCompare(existing, M.EmptyList)() is M.false_value:
            self.result = M.Pair(graph_version, M.Pair(existing, M.EmptyList))
        else:
            next_version = GraphVersion(
                M.Pair(definition, GraphNodes(graph_version)()),
                GraphEdges(graph_version)(),
                GraphVersionInvariants(graph_version)(),
            )()
            self.result = M.Pair(next_version, M.EmptyList)
        super().__init__(
            inputs=M.Pair(graph_version, M.Pair(definition, M.EmptyList)),
            results=self.result,
        )

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


RETIREMENT_PROPOSAL_CAP = M.GMPRep("10")


class GenerateRetirementProposals(M.Edge):
    """Step 33: propose retiring installed laws that only miss in the ledger."""

    def __init__(self, proposal_store, ledger, graph_version):
        cap_text = M.GMPRepText(RETIREMENT_PROPOSAL_CAP)()
        current_store = proposal_store
        submitted_text = "0"
        empty_graph = GraphVersion(M.EmptyList, M.EmptyList, M.EmptyList)()
        remaining_laws = InstalledLaws(graph_version)()
        while M.IdentityCompare(remaining_laws, M.EmptyList)() is M.false_value:
            if GMPEqualText(submitted_text, cap_text)() is M.truth_value:
                remaining_laws = M.EmptyList
            else:
                law = M.Head(remaining_laws)()
                miss_text = "0"
                remaining_misses = ledger.misses
                while M.IdentityCompare(
                    remaining_misses,
                    M.EmptyList,
                )() is M.false_value:
                    miss = M.Head(remaining_misses)()
                    if M.TermEqual(M.Head(miss)(), law)() is M.truth_value:
                        miss_text = GMPSuccText(miss_text)()
                    remaining_misses = M.Tail(remaining_misses)()
                success_text = "0"
                remaining_records = ledger.records
                while M.IdentityCompare(
                    remaining_records,
                    M.EmptyList,
                )() is M.false_value:
                    record = M.Head(remaining_records)()
                    if M.TermEqual(
                        FiringRecordLaw(record)(),
                        law,
                    )() is M.truth_value:
                        success_text = GMPSuccText(success_text)()
                    remaining_records = M.Tail(remaining_records)()
                if GMPEqualText(miss_text, "0")() is M.false_value:
                    if GMPEqualText(success_text, "0")() is M.truth_value:
                        retired_graph = GraphVersion(
                            M.Pair(Retired(law)(), M.EmptyList),
                            M.EmptyList,
                            M.EmptyList,
                        )()
                        retire_law = Law(
                            empty_graph,
                            empty_graph,
                            retired_graph,
                            Map(empty_graph, empty_graph, M.EmptyList)(),
                            Map(empty_graph, retired_graph, M.EmptyList)(),
                            M.EmptyList,
                        )()
                        proposal = Proposal(
                            retire_law,
                            M.Char("ledger-retirement"),
                        )()
                        evidence = M.Pair(
                            law,
                            M.Pair(
                                MineNatFromGMPRep(M.GMPRep(miss_text))(),
                                M.EmptyList,
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
                        submitted_text = GMPSuccText(submitted_text)()
                remaining_laws = M.Tail(remaining_laws)()

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


CURATOR_REPORT_SCAN_CAP = M.GMPRep("200")


class SelfModelVersion(M.Edge):
    """Step 50: the machine's own state rendered in its own substrate.

    One GraphVersion built by quotation: installed laws with their
    Robustness and metric annotations, contracts, the effective policy,
    the schedule policy, safety invariants, and the last META_WINDOW_CAP
    ledger records. Everything is an ordinary term, so the ordinary miner,
    matcher and census run over the result unchanged.

    SelfModelLabel marks the root and is the only label this step adds.
    Nothing here interprets the state; it only renders it.
    """

    def __init__(self, graph_version, proposal_store, ledger):
        registry = M.AllConstructors
        if M.IdentityCompare(ledger, M.EmptyList)() is M.false_value:
            registry = ledger.registry
        cap_text = M.GMPRepText(SAFETY_SCAN_CAP)()

        # Installed laws, each paired with its recorded metrics so that a
        # law with no successes is structurally visible as such.
        scan_text = "0"
        reversed_laws = M.EmptyList
        records = M.EmptyList
        if M.IdentityCompare(ledger, M.EmptyList)() is M.false_value:
            records = ledger.records
        remaining = InstalledLaws(graph_version)()
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                remaining = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                law = M.Head(remaining)()
                fired_text = "0"
                remaining_records = records
                while M.IdentityCompare(
                    remaining_records,
                    M.EmptyList,
                )() is M.false_value:
                    if M.TermEqual(
                        FiringRecordLaw(M.Head(remaining_records)())(),
                        law,
                    )() is M.truth_value:
                        fired_text = GMPSuccText(fired_text)()
                    remaining_records = M.Tail(remaining_records)()
                reversed_laws = M.Pair(
                    M.Pair(
                        law,
                        M.Pair(
                            MeasureCostSavings(records, law, registry)(),
                            M.Pair(
                                MineNatFromGMPRep(M.GMPRep(fired_text))(),
                                M.EmptyList,
                            ),
                        ),
                    ),
                    reversed_laws,
                )
                remaining = M.Tail(remaining)()

        # The last META_WINDOW_CAP records, quoted by the Step-48 edge.
        window_text = M.GMPRepText(META_WINDOW_CAP)()
        scan_text = "0"
        reversed_quoted = M.EmptyList
        remaining = records
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, window_text)() is M.truth_value:
                remaining = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                reversed_quoted = M.Pair(
                    QuoteLedgerRecord(
                        M.Head(remaining)(),
                        META_OUTCOME_FIRED,
                        META_CLASS_UNKNOWN,
                        registry,
                    )(),
                    reversed_quoted,
                )
                remaining = M.Tail(remaining)()

        pending_count = M.EmptyList
        if M.IdentityCompare(proposal_store, M.EmptyList)() is M.false_value:
            pending_count = MeasurePendingProposals(proposal_store)()

        model_term = M.Pair(
            Lmod.SelfModelLabel,
            M.Pair(
                Reverse(reversed_laws)(),
                M.Pair(
                    InstalledContracts(graph_version)(),
                    M.Pair(
                        InstalledPolicy(graph_version)(),
                        M.Pair(
                            InstalledSchedulePolicy(graph_version)(),
                            M.Pair(
                                InstalledSafetyInvariants(graph_version)(),
                                M.Pair(
                                    Reverse(reversed_quoted)(),
                                    M.Pair(pending_count, M.EmptyList),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        )
        self.result = EncodeTermAsGraph(model_term)()
        super().__init__(
            inputs=M.Pair(graph_version, M.EmptyList),
            results=self.result,
        )

    def __call__(self):
        return self.result


class CuratorReport(M.Edge):
    """Step 38: the machine's self-description for the deciding human.

    Returns an association chain (sorted by class name at render time):
      per proposal class: Pair(class, Pair(Pair(submitted, Pair(approved,
        Pair(rejected, Pair(pending, EmptyList)))), EmptyList))
    followed by entries for retired-law count, the effective policy, and the
    recorded skip lists. Read-only: no store, ledger, or version is written.
    """

    def __init__(self, proposal_store, ledger, graph_version):
        cap_text = M.GMPRepText(CURATOR_REPORT_SCAN_CAP)()
        class_rows = M.EmptyList
        scan_text = "0"
        remaining_entries = ProposalStoreEntries(proposal_store)()
        while M.IdentityCompare(remaining_entries, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                remaining_entries = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                entry = M.Head(remaining_entries)()
                proposal = ProposalEntryProposal(entry)()
                impact = ClassifyProposal(proposal)()
                approved = M.false_value
                rejected = M.false_value
                remaining_annotations = ProposalEntryAnnotations(entry)()
                while M.IdentityCompare(
                    remaining_annotations,
                    M.EmptyList,
                )() is M.false_value:
                    annotation = M.Head(remaining_annotations)()
                    if M.IsPair(annotation)() is M.truth_value:
                        if M.TermEqual(
                            M.Head(annotation)(),
                            Lmod.ApprovedLabel,
                        )() is M.truth_value:
                            approved = M.truth_value
                        if M.TermEqual(
                            M.Head(annotation)(),
                            Lmod.RejectedLabel,
                        )() is M.truth_value:
                            rejected = M.truth_value
                    remaining_annotations = M.Tail(remaining_annotations)()

                row = M.EmptyList
                reversed_rows = M.EmptyList
                remaining_rows = class_rows
                while M.IdentityCompare(
                    remaining_rows,
                    M.EmptyList,
                )() is M.false_value:
                    candidate = M.Head(remaining_rows)()
                    if M.Compare(M.Head(candidate)(), impact)() is M.truth_value:
                        row = candidate
                    else:
                        reversed_rows = M.Pair(candidate, reversed_rows)
                    remaining_rows = M.Tail(remaining_rows)()
                if M.IdentityCompare(row, M.EmptyList)() is M.truth_value:
                    counts = M.Pair(
                        "0",
                        M.Pair("0", M.Pair("0", M.Pair("0", M.EmptyList))),
                    )
                else:
                    counts = M.Head(M.Tail(row)())()
                submitted_text = GMPSuccText(M.Head(counts)())()
                approved_text = M.Head(M.Tail(counts)())()
                rejected_text = M.Head(M.Tail(M.Tail(counts)())())()
                pending_text = M.Head(M.Tail(M.Tail(M.Tail(counts)())())())()
                if M.IdentityCompare(approved, M.truth_value)() is M.truth_value:
                    approved_text = GMPSuccText(approved_text)()
                elif M.IdentityCompare(rejected, M.truth_value)() is M.truth_value:
                    rejected_text = GMPSuccText(rejected_text)()
                else:
                    pending_text = GMPSuccText(pending_text)()
                row = M.Pair(
                    impact,
                    M.Pair(
                        M.Pair(
                            submitted_text,
                            M.Pair(
                                approved_text,
                                M.Pair(
                                    rejected_text,
                                    M.Pair(pending_text, M.EmptyList),
                                ),
                            ),
                        ),
                        M.EmptyList,
                    ),
                )
                class_rows = Reverse(M.Pair(row, reversed_rows))()
                remaining_entries = M.Tail(remaining_entries)()

        retired_text = "0"
        scan_text = "0"
        remaining_statuses = AllLawsWithStatus(graph_version)()
        while M.IdentityCompare(remaining_statuses, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                remaining_statuses = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                status_entry = M.Head(remaining_statuses)()
                if M.Compare(
                    M.Head(M.Tail(status_entry)())(),
                    M.Char("retired"),
                )() is M.truth_value:
                    retired_text = GMPSuccText(retired_text)()
                remaining_statuses = M.Tail(remaining_statuses)()

        fired_text = "0"
        scan_text = "0"
        remaining_records = ledger.records
        while M.IdentityCompare(remaining_records, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                remaining_records = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                fired_text = GMPSuccText(fired_text)()
                remaining_records = M.Tail(remaining_records)()

        miss_text = "0"
        scan_text = "0"
        remaining_misses = ledger.misses
        while M.IdentityCompare(remaining_misses, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                remaining_misses = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                miss_text = GMPSuccText(miss_text)()
                remaining_misses = M.Tail(remaining_misses)()

        self.result = M.Pair(
            M.Pair(M.Char("classes"), M.Pair(class_rows, M.EmptyList)),
            M.Pair(
                M.Pair(
                    M.Char("retired_laws"),
                    M.Pair(retired_text, M.EmptyList),
                ),
                M.Pair(
                    M.Pair(
                        M.Char("ledger_firings"),
                        M.Pair(fired_text, M.EmptyList),
                    ),
                    M.Pair(
                        M.Pair(
                            M.Char("ledger_misses"),
                            M.Pair(miss_text, M.EmptyList),
                        ),
                        M.Pair(
                            M.Pair(
                                M.Char("effective_policy"),
                                M.Pair(
                                    InstalledPolicy(graph_version)(),
                                    M.EmptyList,
                                ),
                            ),
                            M.Pair(
                                M.Pair(
                                    M.Char("skipped_handle_candidates"),
                                    M.Pair(
                                        SKIPPED_HANDLE_CANDIDATES,
                                        M.EmptyList,
                                    ),
                                ),
                                M.Pair(
                                    M.Pair(
                                        M.Char("skipped_compositions"),
                                        M.Pair(
                                            SKIPPED_COMPOSITIONS,
                                            M.EmptyList,
                                        ),
                                    ),
                                    M.Pair(
                                        M.Pair(
                                            M.Char("unchecked_obligations"),
                                            M.Pair(
                                                UncheckedObligations()(),
                                                M.EmptyList,
                                            ),
                                        ),
                                        M.Pair(
                                            M.Pair(
                                                M.Char("self_model"),
                                                M.Pair(
                                                    SelfModelVersion(
                                                        graph_version,
                                                        proposal_store,
                                                        ledger,
                                                    )(),
                                                    M.EmptyList,
                                                ),
                                            ),
                                            M.EmptyList,
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
                proposal_store,
                M.Pair(ledger, M.Pair(graph_version, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class RenderCuratorReport(M.Edge):
    """Step 38: deterministic plain-text rendering; output only, no writes."""

    def __init__(self, report):
        class_rows = M.Head(M.Tail(M.Head(report)())())()
        row_texts = M.EmptyList
        remaining_rows = class_rows
        while M.IdentityCompare(remaining_rows, M.EmptyList)() is M.false_value:
            row = M.Head(remaining_rows)()
            counts = M.Head(M.Tail(row)())()
            line = (
                "class "
                + M.Head(row)()()
                + ": submitted="
                + M.Head(counts)()
                + " approved="
                + M.Head(M.Tail(counts)())()
                + " rejected="
                + M.Head(M.Tail(M.Tail(counts)())())()
                + " pending="
                + M.Head(M.Tail(M.Tail(M.Tail(counts)())())())()
            )
            inserted = M.false_value
            reversed_sorted = M.EmptyList
            remaining_texts = row_texts
            while M.IdentityCompare(
                remaining_texts,
                M.EmptyList,
            )() is M.false_value:
                existing = M.Head(remaining_texts)()
                if M.IdentityCompare(inserted, M.false_value)() is M.truth_value:
                    if line < existing:
                        reversed_sorted = M.Pair(existing, M.Pair(line, reversed_sorted))
                        inserted = M.truth_value
                    else:
                        reversed_sorted = M.Pair(existing, reversed_sorted)
                else:
                    reversed_sorted = M.Pair(existing, reversed_sorted)
                remaining_texts = M.Tail(remaining_texts)()
            if M.IdentityCompare(inserted, M.false_value)() is M.truth_value:
                reversed_sorted = M.Pair(line, reversed_sorted)
            row_texts = Reverse(reversed_sorted)()
            remaining_rows = M.Tail(remaining_rows)()

        rendered = "curator report"
        remaining_texts = row_texts
        while M.IdentityCompare(remaining_texts, M.EmptyList)() is M.false_value:
            rendered = rendered + "\n" + M.Head(remaining_texts)()
            remaining_texts = M.Tail(remaining_texts)()

        remaining_sections = M.Tail(report)()
        while M.IdentityCompare(
            remaining_sections,
            M.EmptyList,
        )() is M.false_value:
            section = M.Head(remaining_sections)()
            key = M.Head(section)()()
            value = M.Head(M.Tail(section)())()
            if key == "effective_policy":
                policy_text = ""
                remaining_policy = value
                while M.IdentityCompare(
                    remaining_policy,
                    M.EmptyList,
                )() is M.false_value:
                    policy_entry = M.Head(remaining_policy)()
                    policy_text = (
                        policy_text
                        + " "
                        + M.Head(policy_entry)()()
                        + "="
                        + M.Head(M.Tail(policy_entry)())()()
                    )
                    remaining_policy = M.Tail(remaining_policy)()
                rendered = rendered + "\n" + key + ":" + policy_text
            elif key == "retired_laws" or key == "ledger_firings" or key == "ledger_misses":
                rendered = rendered + "\n" + key + "=" + value
            else:
                count_text = "0"
                remaining_items = value
                while M.IdentityCompare(
                    remaining_items,
                    M.EmptyList,
                )() is M.false_value:
                    count_text = GMPSuccText(count_text)()
                    remaining_items = M.Tail(remaining_items)()
                rendered = rendered + "\n" + key + " count=" + count_text
            remaining_sections = M.Tail(remaining_sections)()

        self.result = rendered
        super().__init__(inputs=M.Pair(report, M.EmptyList), results=M.EmptyList)

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
        # Nodes and edges are two views of one store: EncodeTermAsGraph
        # puts every application in both, so a fact appeared twice in
        # this chain and every match through it was found twice over.
        # Four completed mappings for one join, on a pattern with two
        # applications, is 2^2 -- and the duplicates cost the same as
        # the real ones to explore.
        reversed_collected = M.EmptyList
        remaining = probe._normalize_store(GraphNodes(source)())
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            candidate = M.Head(remaining)()
            if self._already_collected(reversed_collected, candidate) is M.false_value:
                reversed_collected = M.Pair(candidate, reversed_collected)
            remaining = M.Tail(remaining)()
        remaining = probe._normalize_store(GraphEdges(source)())
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            candidate = M.Head(remaining)()
            if self._already_collected(reversed_collected, candidate) is M.false_value:
                reversed_collected = M.Pair(candidate, reversed_collected)
            remaining = M.Tail(remaining)()
        collected = M.EmptyList
        while M.IdentityCompare(reversed_collected, M.EmptyList)() is M.false_value:
            collected = M.Pair(M.Head(reversed_collected)(), collected)
            reversed_collected = M.Tail(reversed_collected)()
        return collected

    def _already_collected(self, collected, candidate):
        remaining = collected
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if M.IdentityCompare(M.Head(remaining)(), candidate)() is M.truth_value:
                return M.truth_value
            remaining = M.Tail(remaining)()
        return M.false_value

    def _alternatives(self, mapping, pat, host_graph):
        # Shape first, but only where shape is decisive. Every candidate
        # used to be put through the whole of MapExtendOneStep -- graph
        # membership scans, apart checks, positional agreement -- when a
        # mismatched constructor label settles it immediately.
        #
        # The filter is deliberately narrower than GraphElementCompatible,
        # which rejects a bare unlabelled pattern node against everything
        # -- Compare on two value-less atoms is false -- while
        # MapExtendOneStep admits it and the pattern census counts on
        # that. Two applications with different labels cannot be sent to
        # one another whatever else is true, and that is the case worth
        # excluding; everything else still goes to MapExtendOneStep to
        # decide, exactly as before.
        reversed_hits = M.EmptyList
        remaining = self._candidates(mapping, host_graph)
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            candidate = M.Head(remaining)()
            if self._labels_permit(pat, candidate) is M.truth_value:
                extended = MapExtendOneStep(mapping, pat, candidate)()
                if M.IsPair(extended)() is M.truth_value:
                    if M.IdentityCompare(
                        M.Head(extended)(), Lmod.MapLabel,
                    )() is M.truth_value:
                        reversed_hits = M.Pair(extended, reversed_hits)
            remaining = M.Tail(remaining)()
        ordered = M.EmptyList
        while M.IdentityCompare(reversed_hits, M.EmptyList)() is M.false_value:
            ordered = M.Pair(M.Head(reversed_hits)(), ordered)
            reversed_hits = M.Tail(reversed_hits)()
        return ordered

    def _labels_permit(self, pat, candidate):
        if P.IsVarPattern(pat)() is M.truth_value:
            return M.truth_value
        if M.IsPair(pat)() is M.false_value:
            return M.truth_value
        if M.IsPair(candidate)() is M.false_value:
            return M.truth_value
        pat_head = M.Head(pat)()
        candidate_head = M.Head(candidate)()
        if M.IdentityCompare(pat_head, candidate_head)() is M.truth_value:
            return M.truth_value
        return M.TermEqual(pat_head, candidate_head)()

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
        # Identity first. This is asked most often about an element that
        # came out of the very store being searched -- a pattern element
        # against the pattern graph, a host element against the host --
        # so the answer is nearly always the same object, and walking two
        # terms structurally to discover that was the matcher's single
        # largest cost. TermEqual still decides everything identity
        # misses, so the answer is unchanged.
        remaining = chain
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            candidate = M.Head(remaining)()
            if M.IdentityCompare(candidate, term)() is M.truth_value:
                return M.truth_value
            if M.TermEqual(candidate, term)() is M.truth_value:
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
        # IsSend is an Edge, so asking it allocates an atom and an
        # identity per item scanned, to compare one head against one
        # label singleton.
        if M.IsPair(term)() is M.false_value:
            return M.false_value
        return M.IdentityCompare(M.Head(term)(), Lmod.SendLabel)()

    def _is_apart(self, term):
        if M.IsPair(term)() is M.false_value:
            return M.false_value
        if M.IdentityCompare(M.Head(term)(), Lmod.ApartLabel)() is M.truth_value:
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
                if M.IdentityCompare(other_host, host)() is M.truth_value:
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
                if M.IdentityCompare(other_host, host)() is M.truth_value:
                    if self._has_apart_commitment(root, pat, other_pat) is M.truth_value:
                        return Apart(pat, other_pat)()
                    if self._has_apart_commitment(root, other_pat, pat) is M.truth_value:
                        return Apart(other_pat, pat)()
            remaining = M.Tail(remaining)()
        return M.EmptyList

    def _step(self):
        if M.IsPair(self.mapping)() is M.false_value:
            return Miss(self.pat, ReasonShape(self.mapping)())()
        if M.IdentityCompare(M.Head(self.mapping)(), Lmod.MapLabel)() is M.false_value:
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


class ReasonStale(M.Edge):
    """Step 45: a worker claim that no longer replays on the merged version.

    Carries the law whose replay was refused and the worker record that
    claimed it, so a stale claim is recorded rather than silently dropped.
    """

    def __init__(self, law, claimed_record):
        self.result = M.Pair(
            Lmod.ReasonStaleLabel,
            M.Pair(law, M.Pair(claimed_record, M.EmptyList)),
        )
        super().__init__(
            inputs=M.Pair(law, M.Pair(claimed_record, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class MergeFrontiers(M.Edge):
    """Step 45: fold worker frontier claims into one coordinator version.

    Coordinator-only: workers never activate, and their frontier versions are
    never transplanted. Each worker record is re-derived against the growing
    coordinator version by replaying its law through the ordinary firing
    path; a claim whose law no longer has a completed match is refused and
    recorded as a Miss carrying ReasonStale. Worker order then per-worker
    chronological order is the canonical order, so the fold is deterministic
    and the earlier claim wins any overlap, matching DetectConflicts.

    Returns Pair(merged_version, Pair(conflicts, EmptyList)); the ledger is
    mutated in place with the replayed records and any stale misses.
    """

    def __init__(self, base_version, worker_records, ledger, dangling_mode=M.EmptyList):
        if M.IdentityCompare(dangling_mode, M.EmptyList)() is M.truth_value:
            dangling_mode = DanglingForbid()()
        current_version = base_version
        remaining_workers = worker_records
        while M.IdentityCompare(remaining_workers, M.EmptyList)() is M.false_value:
            records = M.Head(remaining_workers)()
            remaining_records = records
            while M.IdentityCompare(
                remaining_records,
                M.EmptyList,
            )() is M.false_value:
                claimed = M.Head(remaining_records)()
                law = FiringRecordLaw(claimed)()
                mapping = FirstCompletedMatch(LawLeft(law)(), current_version)()
                if M.IdentityCompare(mapping, M.EmptyList)() is M.truth_value:
                    ledger.record_miss(law, ReasonStale(law, claimed)())
                else:
                    replayed = FireLaw(
                        current_version,
                        law,
                        mapping,
                        dangling_mode,
                        ledger,
                    )()
                    committed = M.Head(replayed)()
                    if M.IdentityCompare(
                        committed,
                        M.EmptyList,
                    )() is M.truth_value:
                        ledger.record_miss(law, ReasonStale(law, claimed)())
                    else:
                        current_version = committed
                remaining_records = M.Tail(remaining_records)()
            remaining_workers = M.Tail(remaining_workers)()
        conflicts = DetectConflicts(ledger.records, ledger.registry)()
        self.result = M.Pair(current_version, M.Pair(conflicts, M.EmptyList))
        super().__init__(
            inputs=M.Pair(base_version, M.Pair(worker_records, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


__all__ = [name for name in globals() if not name.startswith("_")]
