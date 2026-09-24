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
from . import graph

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





# Late bindings: method bodies above forward-reference ledger machinery
# (as in the original monolith). Import after every class definition so
# the names are present in this module's globals when methods execute.
from .ledger import (  # noqa: E402
    FiringRecord,
    InstalledPreference,
    ScheduleOrdering,
)
__all__ = [name for name in globals() if not name.startswith("_")]
