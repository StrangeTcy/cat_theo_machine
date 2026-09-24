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





# Late bindings: the class bodies above forward-reference firing/ledger
# machinery defined in the downstream modules (legal at call time, as in
# the original monolith). Import them here, after every class definition,
# so the module-level cycle graph -> firing -> graph resolves and the
# names are present in this module's globals when methods execute.
from .firing import (  # noqa: E402
    FireAny,
    FireLaw,
    FirstCompletedMatch,
    GraphElements,
    InstallLaw,
    MapExtendOneStep,
)
from .ledger import (  # noqa: E402
    CENSUS_MATCH_CAP,
    ChainAddMissing,
    GenerateCompositionProposals,
    GenerateHandleProposals,
    GraphStoresEqual,
    InstalledRobustness,
    IsHeuristicTerm,
    IsMigration,
    LAW_ORDERING_SCAN_CAP,
    PatternCensus,
    RobustnessPassed,
    SignedRational,
)
__all__ = [name for name in globals() if not name.startswith("_")]
