from __future__ import annotations

from . import labels as Lmod
from . import machine as M
from .graph import *

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


