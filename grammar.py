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
from . import firing
from . import ledger
from . import language

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
