from __future__ import annotations

from . import machine as M
from . import proof as Pmod
from .gmprep import GMPSuccText, GMPPredText, GMPExactQuotientText, GMPQuadraticPSDText
from .graph import *

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



class MiningDurableTermEqual(M.Edge):
    def __init__(self, left, right, registry=M.EmptyList):
        if M.IdentityCompare(registry, M.EmptyList)() is M.truth_value:
            registry = M.AllConstructors
        if M.IdentityCompare(left, right)() is M.truth_value:
            self.result = M.truth_value
        elif M.AndAtom(M.IsPair(left)(), M.IsPair(right)())() is M.truth_value:
            self.result = M.AndAtom(
                MiningDurableTermEqual(
                    M.Head(left)(), M.Head(right)(), registry,
                )(),
                MiningDurableTermEqual(
                    M.Tail(left)(), M.Tail(right)(), registry,
                )(),
            )()
        elif M.OrAtom(M.IsPair(left)(), M.IsPair(right)())() is M.truth_value:
            self.result = M.false_value
        else:
            left_rep = M.NatRepOf(left, registry)()
            right_rep = M.NatRepOf(right, registry)()
            if M.IdentityCompare(left_rep, M.EmptyList)() is M.false_value:
                if M.IdentityCompare(right_rep, M.EmptyList)() is M.false_value:
                    self.result = GMPEqualText(
                        M.GMPRepText(left_rep)(),
                        M.GMPRepText(right_rep)(),
                    )()
                else:
                    self.result = M.false_value
            else:
                self.result = M.Compare(left, right)()
        super().__init__(
            inputs=M.Pair(left, M.Pair(right, M.Pair(registry, M.EmptyList))),
            results=self.result,
        )

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
                                if MiningDurableTermEqual(
                                    RobustnessLaw(element)(),
                                    law,
                                    M.AllConstructors,
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
                if MiningDurableTermEqual(
                    FiringRecordLaw(record)(), law, registry,
                )() is M.truth_value:
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



class MiningIsTaughtDerivationSchema(M.Edge):
    def __init__(self, term):
        self.result = M.false_value
        if M.IsPair(term)() is M.truth_value:
            if M.Compare(
                M.Head(term)(), M.Char("taught-derivation-schema"),
            )() is M.truth_value:
                self.result = M.truth_value
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result



class MiningSchemaPatternsEqual(M.Edge):
    def __init__(self, left, right):
        left_start = M.Head(M.Tail(left)())()
        right_start = M.Head(M.Tail(right)())()
        left_goal = M.Head(M.Tail(M.Tail(left)())())()
        right_goal = M.Head(M.Tail(M.Tail(right)())())()
        self.result = M.AndAtom(
            M.Compare(left_start, right_start)(),
            M.Compare(left_goal, right_goal)(),
        )()
        super().__init__(inputs=M.Pair(left, M.Pair(right, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result
class MiningSchemaReuseCount(M.Edge):
    def __init__(self, records, schema, count_text="0", scan_text="0"):
        if M.IdentityCompare(records, M.EmptyList)() is M.truth_value:
            self.result = MineNatFromGMPRep(M.GMPRep(count_text))()
        elif GMPEqualText(
            scan_text, M.GMPRepText(METRIC_RECORD_SCAN_CAP)(),
        )() is M.truth_value:
            self.result = MineNatFromGMPRep(M.GMPRep(count_text))()
        else:
            next_text = count_text
            recorded_schema = FiringRecordLaw(M.Head(records)())()
            if MiningIsTaughtDerivationSchema(
                recorded_schema,
            )() is M.truth_value:
                if MiningSchemaPatternsEqual(
                    recorded_schema, schema,
                )() is M.truth_value:
                    next_text = GMPSuccText(count_text)()
            self.result = MiningSchemaReuseCount(
                M.Tail(records)(),
                schema,
                next_text,
                GMPSuccText(scan_text)(),
            )()
        super().__init__(inputs=M.Pair(records, M.Pair(schema, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result
class MeasureReuse(M.Edge):
    """Census count of one handle's pattern across a version history.

    Delegates to the Step-20 PatternCensus rather than re-counting, then
    sums its per-version counts into a single Nat.
    """

    def __init__(self, ledger, handle, versions):
        if MiningIsTaughtDerivationSchema(handle)() is M.truth_value:
            self.result = MiningSchemaReuseCount(
                ledger.records, handle,
            )()
        else:
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






class PolynomialVariableKnown(M.Edge):
    def __init__(self, variable, variables):
        if M.IdentityCompare(variables, M.EmptyList)() is M.truth_value:
            self.result = M.false_value
        elif M.Compare(
            M.Tail(variable)(), M.Tail(M.Head(variables)())(),
        )() is M.truth_value:
            self.result = M.truth_value
        else:
            self.result = PolynomialVariableKnown(
                variable, M.Tail(variables)(),
            )()
        super().__init__(inputs=M.Pair(variable, M.Pair(variables, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class PolynomialVariableAppend(M.Edge):
    def __init__(self, variables, variable):
        if M.IdentityCompare(variables, M.EmptyList)() is M.truth_value:
            self.result = M.Pair(variable, M.EmptyList)
        else:
            self.result = M.Pair(
                M.Head(variables)(),
                PolynomialVariableAppend(
                    M.Tail(variables)(), variable,
                )(),
            )
        super().__init__(inputs=M.Pair(variables, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class PolynomialVariables(M.Edge):
    def __init__(self, term, variables=M.EmptyList):
        if Pmod.IsVarPattern(term)() is M.truth_value:
            if PolynomialVariableKnown(term, variables)() is M.truth_value:
                self.result = variables
            else:
                self.result = PolynomialVariableAppend(
                    variables, term,
                )()
        elif M.IsPair(term)() is M.truth_value:
            after_head = PolynomialVariables(M.Head(term)(), variables)()
            self.result = PolynomialVariables(M.Tail(term)(), after_head)()
        else:
            self.result = variables
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CanonicalPower(M.Edge):
    def __init__(self, variable, exponent_text):
        self.result = M.Pair(
            variable, M.Pair(M.Char(exponent_text), M.EmptyList),
        )
        super().__init__(inputs=M.Pair(variable, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CanonicalPowerVariable(M.Edge):
    def __init__(self, power):
        self.result = M.Head(power)()
        super().__init__(inputs=M.Pair(power, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CanonicalPowerExponent(M.Edge):
    def __init__(self, power):
        self.result = M.Head(M.Tail(power)())()()
        super().__init__(inputs=M.Pair(power, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CanonicalMonomial(M.Edge):
    """Signed coefficient and a sparse variable/exponent chain."""

    def __init__(self, coefficient_text, powers):
        self.result = M.Pair(
            M.Char("canonical-monomial"),
            M.Pair(M.Char(coefficient_text), M.Pair(powers, M.EmptyList)),
        )
        super().__init__(inputs=M.Pair(powers, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CanonicalMonomialCoefficient(M.Edge):
    def __init__(self, monomial):
        self.result = M.Head(M.Tail(monomial)())()()
        super().__init__(inputs=M.Pair(monomial, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CanonicalMonomialPowers(M.Edge):
    def __init__(self, monomial):
        self.result = M.Head(M.Tail(M.Tail(monomial)())())()
        super().__init__(inputs=M.Pair(monomial, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class BoundedPolynomialVariables(M.Edge):
    def __init__(self, expression, bound_text="6"):
        self.result = self._take(PolynomialVariables(expression)(), bound_text)
        super().__init__(inputs=M.Pair(expression, M.EmptyList), results=self.result)

    def _take(self, variables, remaining_text):
        if M.IdentityCompare(variables, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        if GMPEqualText(remaining_text, "0")() is M.truth_value:
            return M.EmptyList
        return M.Pair(
            M.Head(variables)(),
            self._take(M.Tail(variables)(), GMPPredText(remaining_text)()),
        )

    def __call__(self):
        return self.result


class CanonicalPowerExponentFor(M.Edge):
    def __init__(self, powers, variable):
        if M.IdentityCompare(powers, M.EmptyList)() is M.truth_value:
            self.result = "0"
        elif M.Compare(
            M.Tail(CanonicalPowerVariable(M.Head(powers)())())(),
            M.Tail(variable)(),
        )() is M.truth_value:
            self.result = CanonicalPowerExponent(M.Head(powers)())()
        else:
            self.result = CanonicalPowerExponentFor(
                M.Tail(powers)(), variable,
            )()
        super().__init__(inputs=M.Pair(powers, M.Pair(variable, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class CanonicalVariablePowers(M.Edge):
    def __init__(self, variables, selected):
        if M.IdentityCompare(variables, M.EmptyList)() is M.truth_value:
            self.result = M.EmptyList
        else:
            variable = M.Head(variables)()
            rest = CanonicalVariablePowers(M.Tail(variables)(), selected)()
            if M.Compare(M.Tail(variable)(), M.Tail(selected)())() is M.truth_value:
                self.result = M.Pair(CanonicalPower(variable, "1")(), rest)
            else:
                self.result = rest
        super().__init__(inputs=M.Pair(variables, M.Pair(selected, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class CanonicalMergePowers(M.Edge):
    def __init__(self, variables, left, right):
        if M.IdentityCompare(variables, M.EmptyList)() is M.truth_value:
            self.result = M.EmptyList
        else:
            variable = M.Head(variables)()
            exponent = GMPAddText(
                CanonicalPowerExponentFor(left, variable)(),
                CanonicalPowerExponentFor(right, variable)(),
            )()
            rest = CanonicalMergePowers(
                M.Tail(variables)(), left, right,
            )()
            if GMPEqualText(exponent, "0")() is M.truth_value:
                self.result = rest
            else:
                self.result = M.Pair(
                    CanonicalPower(variable, exponent)(), rest,
                )
        super().__init__(inputs=M.Pair(variables, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CanonicalPowersEqual(M.Edge):
    def __init__(self, left, right):
        if M.IdentityCompare(left, M.EmptyList)() is M.truth_value:
            self.result = M.IdentityCompare(right, M.EmptyList)()
        elif M.IdentityCompare(right, M.EmptyList)() is M.truth_value:
            self.result = M.false_value
        else:
            left_power = M.Head(left)()
            right_power = M.Head(right)()
            same_variable = M.Compare(
                M.Tail(CanonicalPowerVariable(left_power)())(),
                M.Tail(CanonicalPowerVariable(right_power)())(),
            )()
            same_exponent = GMPEqualText(
                CanonicalPowerExponent(left_power)(),
                CanonicalPowerExponent(right_power)(),
            )()
            self.result = M.AndAtom(
                M.AndAtom(same_variable, same_exponent)(),
                CanonicalPowersEqual(M.Tail(left)(), M.Tail(right)())(),
            )()
        super().__init__(inputs=M.Pair(left, M.Pair(right, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class CanonicalPowersPrefer(M.Edge):
    """Lexicographic descending exponent-vector order."""

    def __init__(self, left, right, variables):
        if M.IdentityCompare(variables, M.EmptyList)() is M.truth_value:
            self.result = M.false_value
        else:
            variable = M.Head(variables)()
            left_exponent = CanonicalPowerExponentFor(left, variable)()
            right_exponent = CanonicalPowerExponentFor(right, variable)()
            if GMPEqualText(left_exponent, right_exponent)() is M.truth_value:
                self.result = CanonicalPowersPrefer(
                    left, right, M.Tail(variables)(),
                )()
            else:
                self.result = GMPLessText(right_exponent, left_exponent)()
        super().__init__(inputs=M.Pair(left, M.Pair(right, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class CanonicalPolynomialInsert(M.Edge):
    def __init__(self, polynomial, monomial, variables):
        coefficient = CanonicalMonomialCoefficient(monomial)()
        if GMPEqualText(coefficient, "0")() is M.truth_value:
            self.result = polynomial
        elif M.IdentityCompare(polynomial, M.EmptyList)() is M.truth_value:
            self.result = M.Pair(monomial, M.EmptyList)
        else:
            head = M.Head(polynomial)()
            same = CanonicalPowersEqual(
                CanonicalMonomialPowers(head)(),
                CanonicalMonomialPowers(monomial)(),
            )()
            if same is M.truth_value:
                combined = GMPAddText(
                    CanonicalMonomialCoefficient(head)(), coefficient,
                )()
                if GMPEqualText(combined, "0")() is M.truth_value:
                    self.result = M.Tail(polynomial)()
                else:
                    self.result = M.Pair(
                        CanonicalMonomial(
                            combined, CanonicalMonomialPowers(head)(),
                        )(),
                        M.Tail(polynomial)(),
                    )
            elif CanonicalPowersPrefer(
                CanonicalMonomialPowers(monomial)(),
                CanonicalMonomialPowers(head)(),
                variables,
            )() is M.truth_value:
                self.result = M.Pair(monomial, polynomial)
            else:
                self.result = M.Pair(
                    head,
                    CanonicalPolynomialInsert(
                        M.Tail(polynomial)(), monomial, variables,
                    )(),
                )
        super().__init__(inputs=M.Pair(polynomial, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CanonicalPolynomialMerge(M.Edge):
    def __init__(self, left, right, variables):
        if M.IdentityCompare(right, M.EmptyList)() is M.truth_value:
            self.result = left
        else:
            self.result = CanonicalPolynomialMerge(
                CanonicalPolynomialInsert(left, M.Head(right)(), variables)(),
                M.Tail(right)(),
                variables,
            )()
        super().__init__(inputs=M.Pair(left, M.Pair(right, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class CanonicalPolynomialNegate(M.Edge):
    def __init__(self, polynomial):
        if M.IdentityCompare(polynomial, M.EmptyList)() is M.truth_value:
            self.result = M.EmptyList
        else:
            head = M.Head(polynomial)()
            self.result = M.Pair(
                CanonicalMonomial(
                    GMPSubText("0", CanonicalMonomialCoefficient(head)())(),
                    CanonicalMonomialPowers(head)(),
                )(),
                CanonicalPolynomialNegate(M.Tail(polynomial)())(),
            )
        super().__init__(inputs=M.Pair(polynomial, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CanonicalPolynomialMultiplyMonomial(M.Edge):
    def __init__(self, polynomial, monomial, variables):
        if M.IdentityCompare(polynomial, M.EmptyList)() is M.truth_value:
            self.result = M.EmptyList
        else:
            head = M.Head(polynomial)()
            product = CanonicalMonomial(
                GMPMulText(
                    CanonicalMonomialCoefficient(head)(),
                    CanonicalMonomialCoefficient(monomial)(),
                )(),
                CanonicalMergePowers(
                    variables,
                    CanonicalMonomialPowers(head)(),
                    CanonicalMonomialPowers(monomial)(),
                )(),
            )()
            rest = CanonicalPolynomialMultiplyMonomial(
                M.Tail(polynomial)(), monomial, variables,
            )()
            self.result = CanonicalPolynomialInsert(rest, product, variables)()
        super().__init__(inputs=M.Pair(polynomial, M.Pair(monomial, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class CanonicalPolynomialMultiply(M.Edge):
    def __init__(self, left, right, variables):
        if M.IdentityCompare(right, M.EmptyList)() is M.truth_value:
            self.result = M.EmptyList
        else:
            products = CanonicalPolynomialMultiplyMonomial(
                left, M.Head(right)(), variables,
            )()
            self.result = CanonicalPolynomialMerge(
                products,
                CanonicalPolynomialMultiply(
                    left, M.Tail(right)(), variables,
                )(),
                variables,
            )()
        super().__init__(inputs=M.Pair(left, M.Pair(right, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class CanonicalPolynomialPower(M.Edge):
    def __init__(self, polynomial, exponent_text, variables):
        if GMPEqualText(exponent_text, "0")() is M.truth_value:
            self.result = M.Pair(CanonicalMonomial("1", M.EmptyList)(), M.EmptyList)
        else:
            self.result = CanonicalPolynomialMultiply(
                polynomial,
                CanonicalPolynomialPower(
                    polynomial, GMPPredText(exponent_text)(), variables,
                )(),
                variables,
            )()
        super().__init__(inputs=M.Pair(polynomial, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class NormalizeCanonicalPolynomial(M.Edge):
    """Normalize a bounded expression over an arbitrary variable chain."""

    def __init__(self, expression, variables, registry):
        self.result = M.EmptyList
        if Pmod.IsVarPattern(expression)() is M.truth_value:
            self.result = M.Pair(
                CanonicalMonomial(
                    "1", CanonicalVariablePowers(variables, expression)(),
                )(),
                M.EmptyList,
            )
        elif M.IsPair(expression)() is M.truth_value:
            label = M.Head(expression)()
            arguments = M.Tail(expression)()
            if M.IdentityCompare(label, M.ExprIntLabel)() is M.truth_value:
                rep = M.NatRepOf(M.Head(arguments)(), registry)()
                if M.IdentityCompare(rep, M.EmptyList)() is M.false_value:
                    self.result = M.Pair(
                        CanonicalMonomial(M.GMPRepText(rep)(), M.EmptyList)(),
                        M.EmptyList,
                    )
            elif M.IdentityCompare(label, M.ExprNegLabel)() is M.truth_value:
                self.result = CanonicalPolynomialNegate(
                    NormalizeCanonicalPolynomial(
                        M.Head(arguments)(), variables, registry,
                    )(),
                )()
            elif M.IdentityCompare(label, M.ExprAddLabel)() is M.truth_value:
                self.result = CanonicalPolynomialMerge(
                    NormalizeCanonicalPolynomial(
                        M.Head(arguments)(), variables, registry,
                    )(),
                    NormalizeCanonicalPolynomial(
                        M.Head(M.Tail(arguments)())(), variables, registry,
                    )(),
                    variables,
                )()
            elif M.IdentityCompare(label, M.ExprMulLabel)() is M.truth_value:
                self.result = CanonicalPolynomialMultiply(
                    NormalizeCanonicalPolynomial(
                        M.Head(arguments)(), variables, registry,
                    )(),
                    NormalizeCanonicalPolynomial(
                        M.Head(M.Tail(arguments)())(), variables, registry,
                    )(),
                    variables,
                )()
            elif M.IdentityCompare(label, M.ExprPowLabel)() is M.truth_value:
                exponent_term = M.Head(M.Tail(arguments)())()
                if M.IsPair(exponent_term)() is M.truth_value:
                    if M.IdentityCompare(M.Head(exponent_term)(), M.ExprIntLabel)() is M.truth_value:
                        exponent_rep = M.NatRepOf(
                            M.Head(M.Tail(exponent_term)())(), registry,
                        )()
                        if M.IdentityCompare(exponent_rep, M.EmptyList)() is M.false_value:
                            self.result = CanonicalPolynomialPower(
                                NormalizeCanonicalPolynomial(
                                    M.Head(arguments)(), variables, registry,
                                )(),
                                M.GMPRepText(exponent_rep)(),
                                variables,
                            )()
        super().__init__(inputs=M.Pair(expression, M.Pair(variables, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class CanonicalPolynomialEqual(M.Edge):
    def __init__(self, left, right):
        if M.IdentityCompare(left, M.EmptyList)() is M.truth_value:
            self.result = M.IdentityCompare(right, M.EmptyList)()
        elif M.IdentityCompare(right, M.EmptyList)() is M.truth_value:
            self.result = M.false_value
        else:
            left_head = M.Head(left)()
            right_head = M.Head(right)()
            coefficients = GMPEqualText(
                CanonicalMonomialCoefficient(left_head)(),
                CanonicalMonomialCoefficient(right_head)(),
            )()
            powers = CanonicalPowersEqual(
                CanonicalMonomialPowers(left_head)(),
                CanonicalMonomialPowers(right_head)(),
            )()
            self.result = M.AndAtom(
                M.AndAtom(coefficients, powers)(),
                CanonicalPolynomialEqual(M.Tail(left)(), M.Tail(right)())(),
            )()
        super().__init__(inputs=M.Pair(left, M.Pair(right, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class PolynomialMonomial(M.Edge):
    def __init__(self, coefficient_text, first_exponent_text, second_exponent_text):
        self.result = M.Pair(
            M.Char("polynomial-monomial"),
            M.Pair(
                M.Char(coefficient_text),
                M.Pair(
                    M.Char(first_exponent_text),
                    M.Pair(M.Char(second_exponent_text), M.EmptyList),
                ),
            ),
        )
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class PolynomialMonomialCoefficient(M.Edge):
    def __init__(self, monomial):
        self.result = M.Head(M.Tail(monomial)())()()
        super().__init__(inputs=M.Pair(monomial, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class PolynomialMonomialFirstExponent(M.Edge):
    def __init__(self, monomial):
        self.result = M.Head(M.Tail(M.Tail(monomial)())())()()
        super().__init__(inputs=M.Pair(monomial, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class PolynomialMonomialSecondExponent(M.Edge):
    def __init__(self, monomial):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(monomial)())())())()()
        super().__init__(inputs=M.Pair(monomial, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class PolynomialInsert(M.Edge):
    def __init__(self, polynomial, monomial):
        coefficient = PolynomialMonomialCoefficient(monomial)()
        if GMPEqualText(coefficient, "0")() is M.truth_value:
            self.result = polynomial
        elif M.IdentityCompare(polynomial, M.EmptyList)() is M.truth_value:
            self.result = M.Pair(monomial, M.EmptyList)
        else:
            head = M.Head(polynomial)()
            head_first = PolynomialMonomialFirstExponent(head)()
            head_second = PolynomialMonomialSecondExponent(head)()
            new_first = PolynomialMonomialFirstExponent(monomial)()
            new_second = PolynomialMonomialSecondExponent(monomial)()
            if GMPEqualText(head_first, new_first)() is M.truth_value:
                if GMPEqualText(head_second, new_second)() is M.truth_value:
                    combined_text = GMPAddText(
                        PolynomialMonomialCoefficient(head)(), coefficient,
                    )()
                    if GMPEqualText(combined_text, "0")() is M.truth_value:
                        self.result = M.Tail(polynomial)()
                    else:
                        self.result = M.Pair(
                            PolynomialMonomial(
                                combined_text, new_first, new_second,
                            )(),
                            M.Tail(polynomial)(),
                        )
                elif GMPLessText(head_second, new_second)() is M.truth_value:
                    self.result = M.Pair(monomial, polynomial)
                else:
                    self.result = M.Pair(
                        head,
                        PolynomialInsert(M.Tail(polynomial)(), monomial)(),
                    )
            elif GMPLessText(head_first, new_first)() is M.truth_value:
                self.result = M.Pair(monomial, polynomial)
            else:
                self.result = M.Pair(
                    head,
                    PolynomialInsert(M.Tail(polynomial)(), monomial)(),
                )
        super().__init__(inputs=M.Pair(polynomial, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class PolynomialMerge(M.Edge):
    def __init__(self, source, target):
        if M.IdentityCompare(source, M.EmptyList)() is M.truth_value:
            self.result = target
        else:
            inserted = PolynomialInsert(target, M.Head(source)())()
            self.result = PolynomialMerge(M.Tail(source)(), inserted)()
        super().__init__(inputs=M.Pair(source, M.Pair(target, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class PolynomialNegate(M.Edge):
    def __init__(self, polynomial):
        if M.IdentityCompare(polynomial, M.EmptyList)() is M.truth_value:
            self.result = M.EmptyList
        else:
            monomial = M.Head(polynomial)()
            self.result = M.Pair(
                PolynomialMonomial(
                    GMPSubText(
                        "0", PolynomialMonomialCoefficient(monomial)(),
                    )(),
                    PolynomialMonomialFirstExponent(monomial)(),
                    PolynomialMonomialSecondExponent(monomial)(),
                )(),
                PolynomialNegate(M.Tail(polynomial)())(),
            )
        super().__init__(inputs=M.Pair(polynomial, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class PolynomialMultiplyByMonomial(M.Edge):
    def __init__(self, polynomial, multiplier):
        if M.IdentityCompare(polynomial, M.EmptyList)() is M.truth_value:
            self.result = M.EmptyList
        else:
            monomial = M.Head(polynomial)()
            product = PolynomialMonomial(
                GMPMulText(
                    PolynomialMonomialCoefficient(monomial)(),
                    PolynomialMonomialCoefficient(multiplier)(),
                )(),
                GMPAddText(
                    PolynomialMonomialFirstExponent(monomial)(),
                    PolynomialMonomialFirstExponent(multiplier)(),
                )(),
                GMPAddText(
                    PolynomialMonomialSecondExponent(monomial)(),
                    PolynomialMonomialSecondExponent(multiplier)(),
                )(),
            )()
            rest = PolynomialMultiplyByMonomial(
                M.Tail(polynomial)(), multiplier,
            )()
            self.result = PolynomialInsert(rest, product)()
        super().__init__(inputs=M.Pair(polynomial, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class PolynomialMultiply(M.Edge):
    def __init__(self, left, right):
        if M.IdentityCompare(left, M.EmptyList)() is M.truth_value:
            self.result = M.EmptyList
        else:
            products = PolynomialMultiplyByMonomial(
                right, M.Head(left)(),
            )()
            rest = PolynomialMultiply(M.Tail(left)(), right)()
            self.result = PolynomialMerge(products, rest)()
        super().__init__(inputs=M.Pair(left, M.Pair(right, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class PolynomialPower(M.Edge):
    def __init__(self, polynomial, exponent_text):
        if GMPEqualText(exponent_text, "0")() is M.truth_value:
            self.result = M.Pair(
                PolynomialMonomial("1", "0", "0")(), M.EmptyList,
            )
        else:
            self.result = PolynomialMultiply(
                polynomial,
                PolynomialPower(
                    polynomial, GMPPredText(exponent_text)(),
                )(),
            )()
        super().__init__(inputs=M.Pair(polynomial, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class NormalizePolynomial(M.Edge):
    def __init__(self, expression, first, second, registry):
        self.result = M.EmptyList
        if Pmod.IsVarPattern(expression)() is M.truth_value:
            if M.Compare(
                M.Tail(expression)(), M.Tail(first)(),
            )() is M.truth_value:
                self.result = M.Pair(
                    PolynomialMonomial("1", "1", "0")(), M.EmptyList,
                )
            elif M.Compare(
                M.Tail(expression)(), M.Tail(second)(),
            )() is M.truth_value:
                self.result = M.Pair(
                    PolynomialMonomial("1", "0", "1")(), M.EmptyList,
                )
        elif M.IsPair(expression)() is M.truth_value:
            label = M.Head(expression)()
            arguments = M.Tail(expression)()
            if M.IdentityCompare(label, M.ExprIntLabel)() is M.truth_value:
                value = M.Head(arguments)()
                rep = M.NatRepOf(value, registry)()
                if M.IdentityCompare(rep, M.EmptyList)() is M.false_value:
                    self.result = M.Pair(
                        PolynomialMonomial(
                            M.GMPRepText(rep)(), "0", "0",
                        )(),
                        M.EmptyList,
                    )
            elif M.IdentityCompare(label, M.ExprNegLabel)() is M.truth_value:
                self.result = PolynomialNegate(
                    NormalizePolynomial(
                        M.Head(arguments)(), first, second, registry,
                    )(),
                )()
            elif M.IdentityCompare(label, M.ExprAddLabel)() is M.truth_value:
                left = NormalizePolynomial(
                    M.Head(arguments)(), first, second, registry,
                )()
                right = NormalizePolynomial(
                    M.Head(M.Tail(arguments)())(), first, second, registry,
                )()
                self.result = PolynomialMerge(left, right)()
            elif M.IdentityCompare(label, M.ExprMulLabel)() is M.truth_value:
                left = NormalizePolynomial(
                    M.Head(arguments)(), first, second, registry,
                )()
                right = NormalizePolynomial(
                    M.Head(M.Tail(arguments)())(), first, second, registry,
                )()
                self.result = PolynomialMultiply(left, right)()
            elif M.IdentityCompare(label, M.ExprPowLabel)() is M.truth_value:
                base = NormalizePolynomial(
                    M.Head(arguments)(), first, second, registry,
                )()
                exponent_term = M.Head(M.Tail(arguments)())()
                exponent = M.EmptyList
                if M.IsPair(exponent_term)() is M.truth_value:
                    if M.IdentityCompare(
                        M.Head(exponent_term)(), M.ExprIntLabel,
                    )() is M.truth_value:
                        exponent = M.Head(M.Tail(exponent_term)())()
                if M.IdentityCompare(exponent, M.EmptyList)() is M.false_value:
                    exponent_rep = M.NatRepOf(exponent, registry)()
                    if M.IdentityCompare(
                        exponent_rep, M.EmptyList,
                    )() is M.false_value:
                        self.result = PolynomialPower(
                            base, M.GMPRepText(exponent_rep)(),
                        )()
        super().__init__(inputs=M.Pair(expression, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class PolynomialEqual(M.Edge):
    def __init__(self, left, right):
        if M.IdentityCompare(left, M.EmptyList)() is M.truth_value:
            if M.IdentityCompare(right, M.EmptyList)() is M.truth_value:
                self.result = M.truth_value
            else:
                self.result = M.false_value
        elif M.IdentityCompare(right, M.EmptyList)() is M.truth_value:
            self.result = M.false_value
        else:
            left_monomial = M.Head(left)()
            right_monomial = M.Head(right)()
            same_coefficient = GMPEqualText(
                PolynomialMonomialCoefficient(left_monomial)(),
                PolynomialMonomialCoefficient(right_monomial)(),
            )()
            same_first = GMPEqualText(
                PolynomialMonomialFirstExponent(left_monomial)(),
                PolynomialMonomialFirstExponent(right_monomial)(),
            )()
            same_second = GMPEqualText(
                PolynomialMonomialSecondExponent(left_monomial)(),
                PolynomialMonomialSecondExponent(right_monomial)(),
            )()
            self.result = M.AndAtom(
                M.AndAtom(same_coefficient, same_first)(),
                M.AndAtom(
                    same_second,
                    PolynomialEqual(M.Tail(left)(), M.Tail(right)())(),
                )(),
            )()
        super().__init__(inputs=M.Pair(left, M.Pair(right, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class PolynomialSwapVariables(M.Edge):
    def __init__(self, polynomial):
        if M.IdentityCompare(polynomial, M.EmptyList)() is M.truth_value:
            self.result = M.EmptyList
        else:
            monomial = M.Head(polynomial)()
            swapped = PolynomialMonomial(
                PolynomialMonomialCoefficient(monomial)(),
                PolynomialMonomialSecondExponent(monomial)(),
                PolynomialMonomialFirstExponent(monomial)(),
            )()
            self.result = PolynomialInsert(
                PolynomialSwapVariables(M.Tail(polynomial)())(), swapped,
            )()
        super().__init__(inputs=M.Pair(polynomial, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class PolynomialAtEqualVariables(M.Edge):
    def __init__(self, polynomial):
        if M.IdentityCompare(polynomial, M.EmptyList)() is M.truth_value:
            self.result = M.EmptyList
        else:
            monomial = M.Head(polynomial)()
            substituted = PolynomialMonomial(
                PolynomialMonomialCoefficient(monomial)(),
                "0",
                GMPAddText(
                    PolynomialMonomialFirstExponent(monomial)(),
                    PolynomialMonomialSecondExponent(monomial)(),
                )(),
            )()
            self.result = PolynomialInsert(
                PolynomialAtEqualVariables(M.Tail(polynomial)())(),
                substituted,
            )()
        super().__init__(inputs=M.Pair(polynomial, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class PolynomialDivisionResult(M.Edge):
    def __init__(self, quotient, remainder, trace, status):
        self.result = M.Pair(
            M.Char("polynomial-division-result"),
            M.Pair(
                quotient,
                M.Pair(
                    remainder,
                    M.Pair(trace, M.Pair(status, M.EmptyList)),
                ),
            ),
        )
        super().__init__(inputs=M.Pair(quotient, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class PolynomialDivisionQuotient(M.Edge):
    def __init__(self, result):
        self.result = M.Head(M.Tail(result)())()
        super().__init__(inputs=M.Pair(result, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class PolynomialDivisionRemainder(M.Edge):
    def __init__(self, result):
        self.result = M.Head(M.Tail(M.Tail(result)())())()
        super().__init__(inputs=M.Pair(result, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class PolynomialDivisionTrace(M.Edge):
    def __init__(self, result):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(result)())())())()
        super().__init__(inputs=M.Pair(result, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class PolynomialDivisionStatus(M.Edge):
    def __init__(self, result):
        self.result = M.Head(
            M.Tail(M.Tail(M.Tail(M.Tail(result)())())())(),
        )()
        super().__init__(inputs=M.Pair(result, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class PolynomialExactDivideStep(M.Edge):
    def __init__(self, dividend, divisor, quotient, trace,
                 remaining_text="100"):
        if GMPEqualText(remaining_text, "0")() is M.truth_value:
            self.result = PolynomialDivisionResult(
                quotient, dividend, M.Reverse(trace)(), M.Char("fuel-stopped"),
            )()
        elif M.IdentityCompare(dividend, M.EmptyList)() is M.truth_value:
            self.result = PolynomialDivisionResult(
                quotient, M.EmptyList, M.Reverse(trace)(), M.Char("exact"),
            )()
        elif M.IdentityCompare(divisor, M.EmptyList)() is M.truth_value:
            self.result = PolynomialDivisionResult(
                quotient, dividend, M.Reverse(trace)(), M.Char("zero-divisor"),
            )()
        else:
            dividend_lead = M.Head(dividend)()
            divisor_lead = M.Head(divisor)()
            dividend_first = PolynomialMonomialFirstExponent(dividend_lead)()
            dividend_second = PolynomialMonomialSecondExponent(dividend_lead)()
            divisor_first = PolynomialMonomialFirstExponent(divisor_lead)()
            divisor_second = PolynomialMonomialSecondExponent(divisor_lead)()
            first_too_small = GMPLessText(dividend_first, divisor_first)()
            second_too_small = GMPLessText(dividend_second, divisor_second)()
            coefficient = GMPExactQuotientText(
                PolynomialMonomialCoefficient(dividend_lead)(),
                PolynomialMonomialCoefficient(divisor_lead)(),
            )()
            if M.OrAtom(first_too_small, second_too_small)() is M.truth_value:
                self.result = PolynomialDivisionResult(
                    quotient, dividend, M.Reverse(trace)(), M.Char("non-exact"),
                )()
            elif M.Compare(
                M.Char(coefficient), M.Char(""),
            )() is M.truth_value:
                self.result = PolynomialDivisionResult(
                    quotient, dividend, M.Reverse(trace)(), M.Char("non-exact"),
                )()
            else:
                quotient_term = PolynomialMonomial(
                    coefficient,
                    GMPSubText(dividend_first, divisor_first)(),
                    GMPSubText(dividend_second, divisor_second)(),
                )()
                subtracted = PolynomialMultiplyByMonomial(
                    divisor, quotient_term,
                )()
                next_dividend = PolynomialMerge(
                    dividend, PolynomialNegate(subtracted)(),
                )()
                next_quotient = PolynomialInsert(quotient, quotient_term)()
                step = M.Pair(
                    M.Char("polynomial-division-step"),
                    M.Pair(
                        quotient_term,
                        M.Pair(subtracted, M.Pair(next_dividend, M.EmptyList)),
                    ),
                )
                self.result = PolynomialExactDivideStep(
                    next_dividend,
                    divisor,
                    next_quotient,
                    M.Pair(step, trace),
                    GMPPredText(remaining_text)(),
                )()
        super().__init__(
            inputs=M.Pair(dividend, M.Pair(divisor, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class PolynomialExactDivide(M.Edge):
    def __init__(self, dividend, divisor, remaining_text="100"):
        trial = PolynomialExactDivideStep(
            dividend, divisor, M.EmptyList, M.EmptyList, remaining_text,
        )()
        if M.Compare(
            PolynomialDivisionStatus(trial)(), M.Char("exact"),
        )() is M.truth_value:
            reconstructed = PolynomialMultiply(
                divisor, PolynomialDivisionQuotient(trial)(),
            )()
            if PolynomialEqual(reconstructed, dividend)() is M.truth_value:
                self.result = trial
            else:
                self.result = PolynomialDivisionResult(
                    PolynomialDivisionQuotient(trial)(),
                    dividend,
                    PolynomialDivisionTrace(trial)(),
                    M.Char("reconstruction-failed"),
                )()
        else:
            self.result = trial
        super().__init__(
            inputs=M.Pair(dividend, M.Pair(divisor, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class PolynomialDifferenceFactor(M.Edge):
    def __init__(self):
        self.result = M.Pair(
            PolynomialMonomial("1", "1", "0")(),
            M.Pair(
                PolynomialMonomial("-1", "0", "1")(),
                M.EmptyList,
            ),
        )
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class PolynomialPowerExpression(M.Edge):
    def __init__(self, variable, exponent_text):
        if GMPEqualText(exponent_text, "0")() is M.truth_value:
            self.result = M.Pair(M.ExprIntLabel, M.Pair(M.one, M.EmptyList))
        elif GMPEqualText(exponent_text, "1")() is M.truth_value:
            self.result = variable
        else:
            exponent = MineNatFromGMPRep(M.GMPRep(exponent_text))()
            self.result = M.Pair(
                M.ExprPowLabel,
                M.Pair(
                    variable,
                    M.Pair(
                        M.Pair(M.ExprIntLabel, M.Pair(exponent, M.EmptyList)),
                        M.EmptyList,
                    ),
                ),
            )
        super().__init__(inputs=M.Pair(variable, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class PolynomialMonomialExpression(M.Edge):
    def __init__(self, monomial, first, second):
        coefficient_text = PolynomialMonomialCoefficient(monomial)()
        negative = GMPLessText(coefficient_text, "0")()
        magnitude_text = coefficient_text
        if M.IdentityCompare(negative, M.truth_value)() is M.truth_value:
            magnitude_text = GMPSubText("0", coefficient_text)()
        first_factor = PolynomialPowerExpression(
            first, PolynomialMonomialFirstExponent(monomial)(),
        )()
        second_factor = PolynomialPowerExpression(
            second, PolynomialMonomialSecondExponent(monomial)(),
        )()
        first_zero = GMPEqualText(
            PolynomialMonomialFirstExponent(monomial)(), "0",
        )()
        second_zero = GMPEqualText(
            PolynomialMonomialSecondExponent(monomial)(), "0",
        )()
        if M.AndAtom(first_zero, second_zero)() is M.truth_value:
            magnitude = MineNatFromGMPRep(M.GMPRep(magnitude_text))()
            expression = M.Pair(
                M.ExprIntLabel, M.Pair(magnitude, M.EmptyList),
            )
        elif M.IdentityCompare(first_zero, M.truth_value)() is M.truth_value:
            expression = second_factor
        elif M.IdentityCompare(second_zero, M.truth_value)() is M.truth_value:
            expression = first_factor
        else:
            expression = M.Pair(
                M.ExprMulLabel,
                M.Pair(first_factor, M.Pair(second_factor, M.EmptyList)),
            )
        if GMPEqualText(magnitude_text, "1")() is M.false_value:
            magnitude = MineNatFromGMPRep(M.GMPRep(magnitude_text))()
            expression = M.Pair(
                M.ExprMulLabel,
                M.Pair(
                    M.Pair(M.ExprIntLabel, M.Pair(magnitude, M.EmptyList)),
                    M.Pair(expression, M.EmptyList),
                ),
            )
        if M.IdentityCompare(negative, M.truth_value)() is M.truth_value:
            expression = M.Pair(
                M.ExprNegLabel, M.Pair(expression, M.EmptyList),
            )
        self.result = expression
        super().__init__(inputs=M.Pair(monomial, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class PolynomialExpression(M.Edge):
    def __init__(self, polynomial, first, second):
        if M.IdentityCompare(polynomial, M.EmptyList)() is M.truth_value:
            self.result = M.Pair(
                M.ExprIntLabel, M.Pair(M.Zero, M.EmptyList),
            )
        else:
            first_term = PolynomialMonomialExpression(
                M.Head(polynomial)(), first, second,
            )()
            if M.IdentityCompare(
                M.Tail(polynomial)(), M.EmptyList,
            )() is M.truth_value:
                self.result = first_term
            else:
                self.result = M.Pair(
                    M.ExprAddLabel,
                    M.Pair(
                        first_term,
                        M.Pair(
                            PolynomialExpression(
                                M.Tail(polynomial)(), first, second,
                            )(),
                            M.EmptyList,
                        ),
                    ),
                )
        super().__init__(inputs=M.Pair(polynomial, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class PolynomialLinearFactor(M.Edge):
    def __init__(self, first_coefficient, second_coefficient):
        polynomial = M.EmptyList
        if GMPEqualText(second_coefficient, "0")() is M.false_value:
            polynomial = PolynomialInsert(
                polynomial,
                PolynomialMonomial(second_coefficient, "0", "1")(),
            )()
        if GMPEqualText(first_coefficient, "0")() is M.false_value:
            polynomial = PolynomialInsert(
                polynomial,
                PolynomialMonomial(first_coefficient, "1", "0")(),
            )()
        self.result = polynomial
        super().__init__(
            inputs=M.Pair(first_coefficient, M.Pair(second_coefficient, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class PolynomialFactorHypotheses(M.Edge):
    """Bounded structural factors, ordered with symmetry as a bias."""

    def __init__(self):
        self.result = M.Pair(
            PolynomialLinearFactor("1", "-1")(),
            M.Pair(
                PolynomialLinearFactor("1", "1")(),
                M.Pair(
                    PolynomialLinearFactor("1", "0")(),
                    M.Pair(
                        PolynomialLinearFactor("0", "1")(),
                        M.Pair(
                            PolynomialLinearFactor("2", "-1")(),
                            M.Pair(
                                PolynomialLinearFactor("2", "1")(),
                                M.Pair(
                                    PolynomialLinearFactor("1", "-2")(),
                                    M.Pair(
                                        PolynomialLinearFactor("1", "2")(),
                                        M.EmptyList,
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


class PolynomialFactorizationResult(M.Edge):
    def __init__(self, factors, cofactor, traces):
        self.result = M.Pair(
            M.Char("polynomial-factorization"),
            M.Pair(factors, M.Pair(cofactor, M.Pair(traces, M.EmptyList))),
        )
        super().__init__(
            inputs=M.Pair(factors, M.Pair(cofactor, M.Pair(traces, M.EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class PolynomialFactorizationFactors(M.Edge):
    def __init__(self, result):
        self.result = M.Head(M.Tail(result)())()
        super().__init__(inputs=M.Pair(result, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class PolynomialFactorizationCofactor(M.Edge):
    def __init__(self, result):
        self.result = M.Head(M.Tail(M.Tail(result)())())()
        super().__init__(inputs=M.Pair(result, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class PolynomialFactorizationTraces(M.Edge):
    def __init__(self, result):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(result)())())())()
        super().__init__(inputs=M.Pair(result, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class PolynomialExtractStructuralFactors(M.Edge):
    """Retry exact division on each quotient, then advance hypotheses."""

    def __init__(self, polynomial, hypotheses=None, fuel_text="12"):
        if hypotheses is None:
            hypotheses = PolynomialFactorHypotheses()()
        self.result = self._extract(
            polynomial, hypotheses, fuel_text, M.EmptyList, M.EmptyList,
        )
        super().__init__(
            inputs=M.Pair(polynomial, M.Pair(hypotheses, M.EmptyList)),
            results=self.result,
        )

    def _extract(self, polynomial, hypotheses, fuel_text, factors, traces):
        if GMPEqualText(fuel_text, "0")() is M.truth_value:
            return PolynomialFactorizationResult(
                M.Reverse(factors)(), polynomial, M.Reverse(traces)(),
            )()
        if M.IdentityCompare(hypotheses, M.EmptyList)() is M.truth_value:
            return PolynomialFactorizationResult(
                M.Reverse(factors)(), polynomial, M.Reverse(traces)(),
            )()
        divisor = M.Head(hypotheses)()
        division = PolynomialExactDivide(polynomial, divisor)()
        if M.Compare(
            PolynomialDivisionStatus(division)(), M.Char("exact"),
        )() is M.truth_value:
            quotient = PolynomialDivisionQuotient(division)()
            if M.IdentityCompare(quotient, M.EmptyList)() is M.false_value:
                return self._extract(
                    quotient,
                    hypotheses,
                    GMPPredText(fuel_text)(),
                    M.Pair(divisor, factors),
                    M.Pair(PolynomialDivisionTrace(division)(), traces),
                )
        return self._extract(
            polynomial, M.Tail(hypotheses)(), fuel_text, factors, traces,
        )

    def __call__(self):
        return self.result


class PolynomialFactorProduct(M.Edge):
    def __init__(self, factors, cofactor):
        if M.IdentityCompare(factors, M.EmptyList)() is M.truth_value:
            self.result = cofactor
        else:
            self.result = PolynomialMultiply(
                M.Head(factors)(),
                PolynomialFactorProduct(M.Tail(factors)(), cofactor)(),
            )()
        super().__init__(
            inputs=M.Pair(factors, M.Pair(cofactor, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class PolynomialFactoredExpression(M.Edge):
    def __init__(self, factors, cofactor, first, second):
        if M.IdentityCompare(factors, M.EmptyList)() is M.truth_value:
            self.result = PolynomialExpression(cofactor, first, second)()
        else:
            factor_expression = PolynomialExpression(
                M.Head(factors)(), first, second,
            )()
            rest_expression = PolynomialFactoredExpression(
                M.Tail(factors)(), cofactor, first, second,
            )()
            self.result = M.Pair(
                M.ExprMulLabel,
                M.Pair(factor_expression, M.Pair(rest_expression, M.EmptyList)),
            )
        super().__init__(
            inputs=M.Pair(
                factors,
                M.Pair(cofactor, M.Pair(first, M.Pair(second, M.EmptyList))),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class NormalizedDifferenceCandidate(M.Edge):
    """Discover a bounded exact factorization of a polynomial residual."""

    def __init__(self, goal, registry=M.EmptyList):
        if M.IdentityCompare(registry, M.EmptyList)() is M.truth_value:
            registry = M.AllConstructors
        self.result = M.EmptyList
        if M.IsPair(goal)() is M.truth_value:
            if M.IdentityCompare(M.Head(goal)(), M.ExprLeLabel)() is M.truth_value:
                variables = PolynomialVariables(goal)()
                if M.IdentityCompare(variables, M.EmptyList)() is M.false_value:
                    if M.IdentityCompare(M.Tail(variables)(), M.EmptyList)() is M.false_value:
                        first = M.Head(variables)()
                        second = M.Head(M.Tail(variables)())()
                        lesser = M.Head(M.Tail(goal)())()
                        greater = M.Head(M.Tail(M.Tail(goal)())())()
                        difference_expression = M.Pair(
                            M.ExprAddLabel,
                            M.Pair(
                                greater,
                                M.Pair(
                                    M.Pair(
                                        M.ExprNegLabel,
                                        M.Pair(lesser, M.EmptyList),
                                    ),
                                    M.EmptyList,
                                ),
                            ),
                        )
                        difference = NormalizePolynomial(
                            difference_expression, first, second, registry,
                        )()
                        factorization = PolynomialExtractStructuralFactors(
                            difference,
                        )()
                        factors = PolynomialFactorizationFactors(factorization)()
                        if M.IdentityCompare(factors, M.EmptyList)() is M.false_value:
                            cofactor = PolynomialFactorizationCofactor(factorization)()
                            reconstructed = PolynomialFactorProduct(
                                factors, cofactor,
                            )()
                            if PolynomialEqual(difference, reconstructed)() is M.truth_value:
                                factored = PolynomialFactoredExpression(
                                    factors, cofactor, first, second,
                                )()
                                proposition = M.Pair(
                                    M.ExprEqLabel,
                                    M.Pair(
                                        difference_expression,
                                        M.Pair(factored, M.EmptyList),
                                    ),
                                )
                                certificate = M.Pair(
                                    M.Char("bounded-structural-exact-division"),
                                    M.Pair(
                                        difference,
                                        M.Pair(
                                            factors,
                                            M.Pair(
                                                cofactor,
                                                M.Pair(
                                                    PolynomialFactorizationTraces(factorization)(),
                                                    M.Pair(reconstructed, M.EmptyList),
                                                ),
                                            ),
                                        ),
                                    ),
                                )
                                self.result = M.Pair(
                                    proposition,
                                    M.Pair(
                                        M.Char("goal-structural"),
                                        M.Pair(
                                            M.Char("verified-identity"),
                                            M.Pair(certificate, M.EmptyList),
                                        ),
                                    ),
                                )
        super().__init__(inputs=M.Pair(goal, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class QuadraticCoefficientResult(M.Edge):
    def __init__(self, a_text, b_text, c_text, status):
        self.result = M.Pair(
            M.Char("quadratic-coefficients"),
            M.Pair(
                M.Char(a_text),
                M.Pair(M.Char(b_text), M.Pair(M.Char(c_text), M.Pair(status, M.EmptyList))),
            ),
        )
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class HomogeneousQuadraticCoefficients(M.Edge):
    def __init__(self, polynomial, a_text="0", b_text="0", c_text="0"):
        if M.IdentityCompare(polynomial, M.EmptyList)() is M.truth_value:
            self.result = QuadraticCoefficientResult(
                a_text, b_text, c_text, M.truth_value,
            )()
        else:
            monomial = M.Head(polynomial)()
            coefficient = PolynomialMonomialCoefficient(monomial)()
            first = PolynomialMonomialFirstExponent(monomial)()
            second = PolynomialMonomialSecondExponent(monomial)()
            if GMPEqualText(first, "2")() is M.truth_value:
                if GMPEqualText(second, "0")() is M.truth_value:
                    self.result = HomogeneousQuadraticCoefficients(
                        M.Tail(polynomial)(), coefficient, b_text, c_text,
                    )()
                else:
                    self.result = QuadraticCoefficientResult(a_text, b_text, c_text, M.false_value)()
            elif GMPEqualText(first, "1")() is M.truth_value:
                if GMPEqualText(second, "1")() is M.truth_value:
                    self.result = HomogeneousQuadraticCoefficients(
                        M.Tail(polynomial)(), a_text, coefficient, c_text,
                    )()
                else:
                    self.result = QuadraticCoefficientResult(a_text, b_text, c_text, M.false_value)()
            elif GMPEqualText(first, "0")() is M.truth_value:
                if GMPEqualText(second, "2")() is M.truth_value:
                    self.result = HomogeneousQuadraticCoefficients(
                        M.Tail(polynomial)(), a_text, b_text, coefficient,
                    )()
                else:
                    self.result = QuadraticCoefficientResult(a_text, b_text, c_text, M.false_value)()
            else:
                self.result = QuadraticCoefficientResult(a_text, b_text, c_text, M.false_value)()
        super().__init__(inputs=M.Pair(polynomial, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class QuadraticCoefficientA(M.Edge):
    def __init__(self, result):
        self.result = M.Head(M.Tail(result)())()()
        super().__init__(inputs=M.Pair(result, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class QuadraticCoefficientB(M.Edge):
    def __init__(self, result):
        self.result = M.Head(M.Tail(M.Tail(result)())())()()
        super().__init__(inputs=M.Pair(result, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class QuadraticCoefficientC(M.Edge):
    def __init__(self, result):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(result)())())())()()
        super().__init__(inputs=M.Pair(result, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class QuadraticCoefficientStatus(M.Edge):
    def __init__(self, result):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(result)())())())())()
        super().__init__(inputs=M.Pair(result, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class PairedFactorsNonnegative(M.Edge):
    def __init__(self, factors):
        if M.IdentityCompare(factors, M.EmptyList)() is M.truth_value:
            self.result = M.truth_value
        elif M.IdentityCompare(M.Tail(factors)(), M.EmptyList)() is M.truth_value:
            self.result = M.false_value
        elif PolynomialEqual(
            M.Head(factors)(), M.Head(M.Tail(factors)())(),
        )() is M.false_value:
            self.result = M.false_value
        else:
            self.result = PairedFactorsNonnegative(
                M.Tail(M.Tail(factors)())(),
            )()
        super().__init__(inputs=M.Pair(factors, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class InequalityDifferenceStep(M.Edge):
    def __init__(self, goal, difference_expression, difference):
        zero = M.Pair(M.ExprIntLabel, M.Pair(M.Zero, M.EmptyList))
        difference_goal = M.Pair(
            M.ExprLeLabel, M.Pair(zero, M.Pair(difference_expression, M.EmptyList)),
        )
        self.result = M.Pair(
            M.Char("inequality-difference-step"),
            M.Pair(goal, M.Pair(difference_goal, M.Pair(difference, M.EmptyList))),
        )
        super().__init__(inputs=M.Pair(goal, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ReplayInventedLemmaOnGoal(M.Edge):
    """Revalidate identity, paired factors, and a positive semidefinite cofactor."""

    def __init__(self, goal, invented_lemma, registry=M.EmptyList):
        self.result = M.EmptyList
        if M.IsPair(goal)() is M.truth_value:
            if M.IdentityCompare(M.Head(goal)(), M.ExprLeLabel)() is M.truth_value:
                proposition = M.Head(M.Tail(invented_lemma)())()
                certificate = M.Head(
                    M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(invented_lemma)())())())())())(),
                )()
                if M.Compare(M.Head(certificate)(), M.Char("invention-evidence"))() is M.truth_value:
                    structural = M.Head(M.Tail(certificate)())()
                    validation = M.Head(M.Tail(M.Tail(M.Tail(certificate)())())())()
                    validation_status = CandidateValidationStatus(validation)()
                    if M.Compare(validation_status, M.Char("proved"))() is M.truth_value:
                        stored_difference = M.Head(M.Tail(structural)())()
                        factors = M.Head(M.Tail(M.Tail(structural)())())()
                        cofactor = M.Head(M.Tail(M.Tail(M.Tail(structural)())())())()
                        variables = PolynomialVariables(goal)()
                        if M.IdentityCompare(variables, M.EmptyList)() is M.false_value:
                            if M.IdentityCompare(M.Tail(variables)(), M.EmptyList)() is M.false_value:
                                first = M.Head(variables)()
                                second = M.Head(M.Tail(variables)())()
                                lesser = M.Head(M.Tail(goal)())()
                                greater = M.Head(M.Tail(M.Tail(goal)())())()
                                difference_expression = M.Pair(
                                    M.ExprAddLabel,
                                    M.Pair(
                                        greater,
                                        M.Pair(
                                            M.Pair(M.ExprNegLabel, M.Pair(lesser, M.EmptyList)),
                                            M.EmptyList,
                                        ),
                                    ),
                                )
                                difference = NormalizePolynomial(
                                    difference_expression, first, second, registry,
                                )()
                                same_residual = PolynomialEqual(difference, stored_difference)()
                                paired = PairedFactorsNonnegative(factors)()
                                coefficients = HomogeneousQuadraticCoefficients(cofactor)()
                                quadratic = M.false_value
                                if QuadraticCoefficientStatus(coefficients)() is M.truth_value:
                                    quadratic = GMPQuadraticPSDText(
                                        QuadraticCoefficientA(coefficients)(),
                                        QuadraticCoefficientB(coefficients)(),
                                        QuadraticCoefficientC(coefficients)(),
                                    )()
                                if M.AndAtom(same_residual, M.AndAtom(paired, quadratic)())() is M.truth_value:
                                    identity_step = M.Pair(
                                        M.Char("verified-identity-rewrite"),
                                        M.Pair(proposition, M.EmptyList),
                                    )
                                    positivity = M.Pair(
                                        M.Char("proved-positive"),
                                        M.Pair(factors, M.Pair(cofactor, M.Pair(coefficients, M.EmptyList))),
                                    )
                                    self.result = M.Pair(
                                        M.Char("invented-lemma-replay-derivation"),
                                        M.Pair(
                                            goal,
                                            M.Pair(
                                                invented_lemma,
                                                M.Pair(
                                                    InequalityDifferenceStep(goal, difference_expression, difference)(),
                                                    M.Pair(
                                                        identity_step,
                                                        M.Pair(
                                                            positivity,
                                                            M.Pair(M.Char("proved"), M.EmptyList),
                                                        ),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    )
        super().__init__(
            inputs=M.Pair(goal, M.Pair(invented_lemma, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class ReplayInventedLemma(M.Edge):
    def __init__(self, graph_version, goal, registry, nodes=M.EmptyList, started=M.false_value):
        if M.IdentityCompare(started, M.false_value)() is M.truth_value:
            nodes = GraphVersionNodes(graph_version)()
        if M.IdentityCompare(nodes, M.EmptyList)() is M.truth_value:
            self.result = M.EmptyList
        else:
            node = M.Head(nodes)()
            replay = M.EmptyList
            if M.IsPair(node)() is M.truth_value:
                if M.Compare(M.Head(node)(), M.Char("invented-lemma"))() is M.truth_value:
                    replay = ReplayInventedLemmaOnGoal(goal, node, registry)()
            if M.IdentityCompare(replay, M.EmptyList)() is M.false_value:
                self.result = M.Pair(replay, M.Pair(node, M.EmptyList))
            else:
                self.result = ReplayInventedLemma(
                    graph_version, goal, registry, M.Tail(nodes)(), M.truth_value,
                )()
        super().__init__(
            inputs=M.Pair(graph_version, M.Pair(goal, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class CandidateValidation(M.Edge):
    """Validate a candidate without using the stalled start or rule chain."""

    def __init__(self, proposition, registry=M.EmptyList):
        status = M.Char("unknown")
        if M.IsPair(proposition)() is M.truth_value:
            if M.IdentityCompare(M.Head(proposition)(), M.ExprEqLabel)() is M.truth_value:
                variables = PolynomialVariables(proposition)()
                if M.IdentityCompare(variables, M.EmptyList)() is M.false_value:
                    if M.IdentityCompare(M.Tail(variables)(), M.EmptyList)() is M.false_value:
                        first = M.Head(variables)()
                        second = M.Head(M.Tail(variables)())()
                        left = M.Head(M.Tail(proposition)())()
                        right = M.Head(M.Tail(M.Tail(proposition)())())()
                        left_polynomial = NormalizePolynomial(
                            left, first, second, registry,
                        )()
                        right_polynomial = NormalizePolynomial(
                            right, first, second, registry,
                        )()
                        if PolynomialEqual(left_polynomial, right_polynomial)() is M.truth_value:
                            status = M.Char("proved")
                        else:
                            status = M.Char("refuted")
        self.result = M.Pair(
            M.Char("candidate-validation"),
            M.Pair(status, M.Pair(proposition, M.EmptyList)),
        )
        super().__init__(inputs=M.Pair(proposition, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CandidateValidationStatus(M.Edge):
    def __init__(self, validation):
        self.result = M.Head(M.Tail(validation)())()
        super().__init__(inputs=M.Pair(validation, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CandidateTrial(M.Edge):
    """Pair-only evidence for the effect of adding one candidate fact.

    Both arms use the exact start and existing compiled rule chain captured by
    the failed search.  A candidate is an improvement here only when an
    existing rule becomes applicable; no candidate-to-goal rule is created.
    """

    def __init__(self, candidate, start, rules, registry):
        proposition = M.Head(candidate)()
        baseline = Pmod.FilterApplicableRules(rules, start, registry)()
        augmented = baseline
        if Pmod.IsKnowledge(start)() is M.truth_value:
            augmented_start = Pmod.Knowledge(
                M.Pair(proposition, Pmod.KnowledgeFacts(start)()),
            )()
            augmented = Pmod.FilterApplicableRules(
                rules, augmented_start, registry,
            )()
        baseline_count = M.GMPRepText(M.CountRep(baseline)())()
        augmented_count = M.GMPRepText(M.CountRep(augmented)())()
        improvement = GMPLessText(baseline_count, augmented_count)()
        self.result = M.Pair(
            M.Char("candidate-trial"),
            M.Pair(
                candidate,
                M.Pair(
                    baseline,
                    M.Pair(
                        augmented,
                        M.Pair(
                            improvement,
                            M.Pair(
                                M.Char("newly-applicable-existing-rule"),
                                M.EmptyList,
                            ),
                        ),
                    ),
                ),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                candidate,
                M.Pair(start, M.Pair(rules, M.Pair(registry, M.EmptyList))),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class CandidateTrialImproved(M.Edge):
    def __init__(self, trial):
        self.result = M.Head(
            M.Tail(M.Tail(M.Tail(M.Tail(trial)())())())(),
        )()
        super().__init__(inputs=M.Pair(trial, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CandidateWithSource(M.Edge):
    def __init__(self, candidate, source):
        self.result = M.Pair(
            M.Head(candidate)(),
            M.Pair(
                source,
                M.Pair(
                    M.Head(M.Tail(M.Tail(candidate)())())(),
                    M.Pair(
                        M.Head(M.Tail(M.Tail(M.Tail(candidate)())())())(),
                        M.EmptyList,
                    ),
                ),
            ),
        )
        super().__init__(
            inputs=M.Pair(candidate, M.Pair(source, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class CandidateFromResidualFacts(M.Edge):
    def __init__(self, facts, registry):
        if M.IdentityCompare(facts, M.EmptyList)() is M.truth_value:
            self.result = M.EmptyList
        else:
            candidate = NormalizedDifferenceCandidate(
                M.Head(facts)(), registry,
            )()
            if M.IdentityCompare(candidate, M.EmptyList)() is M.false_value:
                self.result = CandidateWithSource(
                    candidate, M.Char("frontier-residual"),
                )()
            else:
                self.result = CandidateFromResidualFacts(
                    M.Tail(facts)(), registry,
                )()
        super().__init__(inputs=M.Pair(facts, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CandidateFromFrontier(M.Edge):
    def __init__(self, frontier, registry):
        if M.IdentityCompare(frontier, M.EmptyList)() is M.truth_value:
            self.result = M.EmptyList
        else:
            state = M.Head(frontier)()
            current = M.Head(M.Tail(state)())()
            if Pmod.IsKnowledge(current)() is M.truth_value:
                candidate = CandidateFromResidualFacts(
                    Pmod.KnowledgeFacts(current)(), registry,
                )()
            else:
                candidate = NormalizedDifferenceCandidate(
                    current, registry,
                )()
                if M.IdentityCompare(candidate, M.EmptyList)() is M.false_value:
                    candidate = CandidateWithSource(
                        candidate, M.Char("frontier-residual"),
                    )()
            if M.IdentityCompare(candidate, M.EmptyList)() is M.false_value:
                self.result = candidate
            else:
                self.result = CandidateFromFrontier(
                    M.Tail(frontier)(), registry,
                )()
        super().__init__(inputs=M.Pair(frontier, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class InventFromStall(M.Edge):
    def __init__(self, stall, registry=M.EmptyList):
        fields = M.Tail(stall)()
        goal = M.Head(fields)()
        candidate = NormalizedDifferenceCandidate(goal, registry)()
        if M.IdentityCompare(candidate, M.EmptyList)() is M.truth_value:
            candidate = CandidateFromFrontier(
                M.Head(M.Tail(fields)())(), registry,
            )()
        if M.IdentityCompare(candidate, M.EmptyList)() is M.truth_value:
            self.result = M.EmptyList
        else:
            stall_start = M.Head(
                M.Tail(M.Tail(M.Tail(M.Tail(fields)())())())(),
            )()
            stall_rules = M.Head(
                M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(fields)())())())())(),
            )()
            trial = CandidateTrial(
                candidate,
                stall_start,
                stall_rules,
                registry,
            )()
            validation = CandidateValidation(M.Head(candidate)(), registry)()
            candidate_with_trial = M.Pair(
                M.Head(candidate)(),
                M.Pair(
                    M.Head(M.Tail(candidate)())(),
                    M.Pair(
                        M.Head(M.Tail(M.Tail(candidate)())())(),
                        M.Pair(
                            M.Head(M.Tail(M.Tail(M.Tail(candidate)())())())(),
                            M.Pair(trial, M.Pair(validation, M.EmptyList)),
                        ),
                    ),
                ),
            )
            self.result = M.Pair(candidate_with_trial, M.EmptyList)
        super().__init__(inputs=M.Pair(stall, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result
