from __future__ import annotations

try:
    from .core import (
        Atom,
        Edge,
        EmptyList,
        Head,
        IdentityCompare,
        Pair,
        Tail,
        false_value,
        truth_value,
    )
    from .labels import ConstructorLabel
except ImportError:
    from core import (
        Atom,
        Edge,
        EmptyList,
        Head,
        IdentityCompare,
        Pair,
        Tail,
        false_value,
        truth_value,
    )
    from labels import ConstructorLabel


# =============================================================================
# Programme L / Track S: Machine-Native Story Labels
# =============================================================================

class StoryLabel(ConstructorLabel):
    pass


class StoryFragmentLabel(StoryLabel):
    pass


StoryFragmentLabel = StoryFragmentLabel()


class StoryEdgeLabel(StoryLabel):
    pass


StoryEdgeLabel = StoryEdgeLabel()


class AgreementScopeLabel(StoryLabel):
    pass


AgreementScopeLabel = AgreementScopeLabel()


class EvidenceTermLabel(StoryLabel):
    pass


EvidenceTermLabel = EvidenceTermLabel()


class RenderedClauseLabel(StoryLabel):
    pass


RenderedClauseLabel = RenderedClauseLabel()


# --- Roles ---

class RoleSetupLabel(StoryLabel):
    pass


RoleSetupLabel = RoleSetupLabel()


class RoleActionLabel(StoryLabel):
    pass


RoleActionLabel = RoleActionLabel()


class RoleEvidenceLabel(StoryLabel):
    pass


RoleEvidenceLabel = RoleEvidenceLabel()


class RoleBlockerLabel(StoryLabel):
    pass


RoleBlockerLabel = RoleBlockerLabel()


class RoleConsequenceLabel(StoryLabel):
    pass


RoleConsequenceLabel = RoleConsequenceLabel()


class RoleNextActionLabel(StoryLabel):
    pass


RoleNextActionLabel = RoleNextActionLabel()


class RoleDiscrepancyLabel(StoryLabel):
    pass


RoleDiscrepancyLabel = RoleDiscrepancyLabel()


# --- Tracks ---

class TrackINTLabel(StoryLabel):
    pass


TrackINTLabel = TrackINTLabel()


class TrackSLabel(StoryLabel):
    pass


TrackSLabel = TrackSLabel()


class TrackELabel(StoryLabel):
    pass


TrackELabel = TrackELabel()


class TrackGLabel(StoryLabel):
    pass


TrackGLabel = TrackGLabel()


class TrackFToolsLabel(StoryLabel):
    pass


TrackFToolsLabel = TrackFToolsLabel()


class TrackFOpLabel(StoryLabel):
    pass


TrackFOpLabel = TrackFOpLabel()


# --- Events ---

class EventCompletedLabel(StoryLabel):
    pass


EventCompletedLabel = EventCompletedLabel()


class EventFailedLabel(StoryLabel):
    pass


EventFailedLabel = EventFailedLabel()


class EventDeferredLabel(StoryLabel):
    pass


EventDeferredLabel = EventDeferredLabel()


class EventAdmittedLabel(StoryLabel):
    pass


EventAdmittedLabel = EventAdmittedLabel()


class EventRejectedLabel(StoryLabel):
    pass


EventRejectedLabel = EventRejectedLabel()


class EventHeldLabel(StoryLabel):
    pass


EventHeldLabel = EventHeldLabel()


class EventNonDischargeBudgetLabel(StoryLabel):
    pass


EventNonDischargeBudgetLabel = EventNonDischargeBudgetLabel()


class EventRefutedLabel(StoryLabel):
    pass


EventRefutedLabel = EventRefutedLabel()


# --- Salience ---

class SalienceHighLabel(StoryLabel):
    pass


SalienceHighLabel = SalienceHighLabel()


class SalienceMediumLabel(StoryLabel):
    pass


SalienceMediumLabel = SalienceMediumLabel()


class SalienceLowLabel(StoryLabel):
    pass


SalienceLowLabel = SalienceLowLabel()


# --- Relations for StoryEdge ---

class RelationSupportsLabel(StoryLabel):
    pass


RelationSupportsLabel = RelationSupportsLabel()


class RelationCausesLabel(StoryLabel):
    pass


RelationCausesLabel = RelationCausesLabel()


class RelationContrastsLabel(StoryLabel):
    pass


RelationContrastsLabel = RelationContrastsLabel()


class RelationSupersedesLabel(StoryLabel):
    pass


RelationSupersedesLabel = RelationSupersedesLabel()


class RelationElaboratesLabel(StoryLabel):
    pass


RelationElaboratesLabel = RelationElaboratesLabel()


# --- Audience Cuts ---

class CutOperatorLabel(StoryLabel):
    pass


CutOperatorLabel = CutOperatorLabel()


class CutEngineerLabel(StoryLabel):
    pass


CutEngineerLabel = CutEngineerLabel()


class CutReviewLabel(StoryLabel):
    pass


CutReviewLabel = CutReviewLabel()


class CutMachineLabel(StoryLabel):
    pass


CutMachineLabel = CutMachineLabel()


class CutAllLabel(StoryLabel):
    pass


CutAllLabel = CutAllLabel()


# =============================================================================
# Machine-Native Story Terms and Accessors
# =============================================================================

class StoryEdge(Edge):
    """A typed narrative dependency edge between two StoryFragment IDs."""

    def __init__(self, relation, source_id, target_id):
        self.result = Pair(
            StoryEdgeLabel,
            Pair(relation, Pair(source_id, Pair(target_id, EmptyList))),
        )
        super().__init__(
            inputs=Pair(relation, Pair(source_id, Pair(target_id, EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class StoryEdgeRelation(Edge):
    def __init__(self, edge):
        self.result = Head(Tail(edge)())()
        super().__init__(inputs=Pair(edge, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class StoryEdgeSource(Edge):
    def __init__(self, edge):
        self.result = Head(Tail(Tail(edge)())())()
        super().__init__(inputs=Pair(edge, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class StoryEdgeTarget(Edge):
    def __init__(self, edge):
        self.result = Head(Tail(Tail(Tail(edge)())())())()
        super().__init__(inputs=Pair(edge, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class AgreementScope(Edge):
    """Agreement scope declaration with explicit projection and excluded discrepancies."""

    def __init__(self, projection, exclusions):
        self.result = Pair(
            AgreementScopeLabel,
            Pair(projection, Pair(exclusions, EmptyList)),
        )
        super().__init__(
            inputs=Pair(projection, Pair(exclusions, EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class AgreementScopeProjection(Edge):
    def __init__(self, term):
        self.result = Head(Tail(term)())()
        super().__init__(inputs=Pair(term, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class AgreementScopeExclusions(Edge):
    def __init__(self, term):
        self.result = Head(Tail(Tail(term)())())()
        super().__init__(inputs=Pair(term, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class EvidenceTerm(Edge):
    """
    Evidence carrier preserving structural identity and disambiguating markers.
    Guarantees non-lossy equality: two structurally distinct terms cannot be
    rendered as textually identical.
    """

    def __init__(self, identity, marker):
        self.result = Pair(
            EvidenceTermLabel,
            Pair(identity, Pair(marker, EmptyList)),
        )
        super().__init__(
            inputs=Pair(identity, Pair(marker, EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class EvidenceTermIdentity(Edge):
    def __init__(self, term):
        self.result = Head(Tail(term)())()
        super().__init__(inputs=Pair(term, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class EvidenceTermMarker(Edge):
    def __init__(self, term):
        self.result = Head(Tail(Tail(term)())())()
        super().__init__(inputs=Pair(term, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class StoryFragment(Edge):
    """
    Machine-native StoryFragment term for Programme L / Track S.
    Carries 13 explicit fields as nested Pair cells.
    """

    def __init__(
        self,
        fragment_id,
        cut_id,
        accepted_state_version,
        role,
        track,
        subject,
        predicate,
        event,
        evidence,
        salience,
        dependencies,
        conflicts,
        target_cuts,
    ):
        self.result = Pair(
            StoryFragmentLabel,
            Pair(
                fragment_id,
                Pair(
                    cut_id,
                    Pair(
                        accepted_state_version,
                        Pair(
                            role,
                            Pair(
                                track,
                                Pair(
                                    subject,
                                    Pair(
                                        predicate,
                                        Pair(
                                            event,
                                            Pair(
                                                evidence,
                                                Pair(
                                                    salience,
                                                    Pair(
                                                        dependencies,
                                                        Pair(
                                                            conflicts,
                                                            Pair(target_cuts, EmptyList),
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
        super().__init__(
            inputs=Pair(
                fragment_id,
                Pair(
                    cut_id,
                    Pair(
                        accepted_state_version,
                        Pair(
                            role,
                            Pair(
                                track,
                                Pair(
                                    subject,
                                    Pair(
                                        predicate,
                                        Pair(
                                            event,
                                            Pair(
                                                evidence,
                                                Pair(
                                                    salience,
                                                    Pair(
                                                        dependencies,
                                                        Pair(
                                                            conflicts,
                                                            Pair(target_cuts, EmptyList),
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
            results=self.result,
        )

    def __call__(self):
        return self.result


class StoryFragmentId(Edge):
    def __init__(self, frag):
        self.result = Head(Tail(frag)())()
        super().__init__(inputs=Pair(frag, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class StoryFragmentCutId(Edge):
    def __init__(self, frag):
        self.result = Head(Tail(Tail(frag)())())()
        super().__init__(inputs=Pair(frag, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class StoryFragmentStateVersion(Edge):
    def __init__(self, frag):
        self.result = Head(Tail(Tail(Tail(frag)())())())()
        super().__init__(inputs=Pair(frag, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class StoryFragmentRole(Edge):
    def __init__(self, frag):
        self.result = Head(Tail(Tail(Tail(Tail(frag)())())())())()
        super().__init__(inputs=Pair(frag, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class StoryFragmentTrack(Edge):
    def __init__(self, frag):
        self.result = Head(Tail(Tail(Tail(Tail(Tail(frag)())())())())())()
        super().__init__(inputs=Pair(frag, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class StoryFragmentSubject(Edge):
    def __init__(self, frag):
        self.result = Head(Tail(Tail(Tail(Tail(Tail(Tail(frag)())())())())())())()
        super().__init__(inputs=Pair(frag, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class StoryFragmentPredicate(Edge):
    def __init__(self, frag):
        self.result = Head(Tail(Tail(Tail(Tail(Tail(Tail(Tail(frag)())())())())())())())()
        super().__init__(inputs=Pair(frag, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class StoryFragmentEvent(Edge):
    def __init__(self, frag):
        self.result = Head(Tail(Tail(Tail(Tail(Tail(Tail(Tail(Tail(frag)())())())())())())())())()
        super().__init__(inputs=Pair(frag, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class StoryFragmentEvidence(Edge):
    def __init__(self, frag):
        self.result = Head(Tail(Tail(Tail(Tail(Tail(Tail(Tail(Tail(Tail(frag)())())())())())())())())())()
        super().__init__(inputs=Pair(frag, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class StoryFragmentSalience(Edge):
    def __init__(self, frag):
        self.result = Head(Tail(Tail(Tail(Tail(Tail(Tail(Tail(Tail(Tail(Tail(frag)())())())())())())())())())())()
        super().__init__(inputs=Pair(frag, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class StoryFragmentDependencies(Edge):
    def __init__(self, frag):
        self.result = Head(Tail(Tail(Tail(Tail(Tail(Tail(Tail(Tail(Tail(Tail(Tail(frag)())())())())())())())())())())())()
        super().__init__(inputs=Pair(frag, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class StoryFragmentConflicts(Edge):
    def __init__(self, frag):
        self.result = Head(Tail(Tail(Tail(Tail(Tail(Tail(Tail(Tail(Tail(Tail(Tail(Tail(frag)())())())())())())())())())())())())()
        super().__init__(inputs=Pair(frag, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class StoryFragmentTargetCuts(Edge):
    def __init__(self, frag):
        self.result = Head(Tail(Tail(Tail(Tail(Tail(Tail(Tail(Tail(Tail(Tail(Tail(Tail(Tail(frag)())())())())())())())())())())())())())()
        super().__init__(inputs=Pair(frag, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RenderedClause(Edge):
    """
    Provenance-certified rendered clause for back-check verification.
    """

    def __init__(self, clause_id, proposition, source_fragment_ids, merge_rule, audience_cut):
        self.result = Pair(
            RenderedClauseLabel,
            Pair(
                clause_id,
                Pair(
                    proposition,
                    Pair(
                        source_fragment_ids,
                        Pair(merge_rule, Pair(audience_cut, EmptyList)),
                    ),
                ),
            ),
        )
        super().__init__(
            inputs=Pair(
                clause_id,
                Pair(
                    proposition,
                    Pair(
                        source_fragment_ids,
                        Pair(merge_rule, Pair(audience_cut, EmptyList)),
                    ),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class RenderedClauseId(Edge):
    def __init__(self, clause):
        self.result = Head(Tail(clause)())()
        super().__init__(inputs=Pair(clause, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RenderedClauseProposition(Edge):
    def __init__(self, clause):
        self.result = Head(Tail(Tail(clause)())())()
        super().__init__(inputs=Pair(clause, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RenderedClauseSourceFragments(Edge):
    def __init__(self, clause):
        self.result = Head(Tail(Tail(Tail(clause)())())())()
        super().__init__(inputs=Pair(clause, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RenderedClauseMergeRule(Edge):
    def __init__(self, clause):
        self.result = Head(Tail(Tail(Tail(Tail(clause)())())())())()
        super().__init__(inputs=Pair(clause, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RenderedClauseAudienceCut(Edge):
    def __init__(self, clause):
        self.result = Head(Tail(Tail(Tail(Tail(Tail(clause)())())())())())()
        super().__init__(inputs=Pair(clause, EmptyList), results=self.result)

    def __call__(self):
        return self.result


# =============================================================================
# Ingested 11-Item Fixture Corpus
# =============================================================================

class StoryFixtureCorpus(Edge):
    """
    Ingests and exposes the 11 baseline inspection fixtures as machine-native
    Pair chains of (StoryFragment, StoryEdges, ObservedDefect, ReferenceTarget).
    """

    def __init__(self, cut_id, state_version):
        empty = EmptyList
        all_cuts = Pair(CutOperatorLabel, Pair(CutEngineerLabel, Pair(CutReviewLabel, Pair(CutMachineLabel, empty))))
        eng_rev = Pair(CutEngineerLabel, Pair(CutReviewLabel, empty))
        op_all = Pair(CutOperatorLabel, Pair(CutReviewLabel, empty))

        # --- Fixture 1: Tao Problem 1.1 AST Knowledge Dump ---
        f1_frag = StoryFragment(
            "fixture-01",
            cut_id,
            state_version,
            RoleEvidenceLabel,
            TrackGLabel,
            "tao_problem_1_1_knowledge",
            "unreduced_ast_dump",
            EventHeldLabel,
            EvidenceTerm("cold_debug_stage1_runtime.log:520", "ast_terms=7"),
            SalienceLowLabel,
            empty,
            empty,
            eng_rev,
        )()
        f1_entry = Pair(
            "fixture-01-ast-dump",
            Pair(
                f1_frag,
                Pair(
                    empty,
                    Pair(
                        "Dumps 7 unreduced AST terms on every step; misses rule applicability state.",
                        Pair(
                            "Applicability scan in progress over 7 geometric premises.",
                            empty,
                        ),
                    ),
                ),
            ),
        )

        # --- Fixture 2: SearchBeam Worker Telemetry ---
        f2_frag = StoryFragment(
            "fixture-02",
            cut_id,
            state_version,
            RoleActionLabel,
            TrackELabel,
            "search_beam_worker_1846",
            "packet_cycle_completed",
            EventCompletedLabel,
            EvidenceTerm("cold_debug_stage1_runtime.log:480", "pid=1846_expanded=0_gen=1"),
            SalienceLowLabel,
            empty,
            empty,
            eng_rev,
        )()
        f2_entry = Pair(
            "fixture-02-beam-telemetry",
            Pair(
                f2_frag,
                Pair(
                    empty,
                    Pair(
                        "Raw worker packet telemetry uncurated; zero aggregation across parallel mode workers.",
                        Pair(
                            "Beam search worker finished 1 packet (frontier=2, generated=1).",
                            empty,
                        ),
                    ),
                ),
            ),
        )

        # --- Fixture 3: Stale Token Unexplained Rejection (Lossy Equality Example) ---
        # Note: Non-equal terms carrying distinct generational markers
        ret_token_ev = EvidenceTerm("token-10", "generation-1_instance-a")()
        exp_token_ev = EvidenceTerm("token-10", "generation-2_instance-b")()
        f3_frag = StoryFragment(
            "fixture-03",
            cut_id,
            state_version,
            RoleBlockerLabel,
            TrackELabel,
            "search_bfs_packet_result",
            "stale_token_rejection",
            EventRejectedLabel,
            Pair(ret_token_ev, Pair(exp_token_ev, empty)),
            SalienceHighLabel,
            empty,
            empty,
            all_cuts,
        )()
        f3_entry = Pair(
            "fixture-03-stale-token-fidelity",
            Pair(
                f3_frag,
                Pair(
                    empty,
                    Pair(
                        "Unexplained rejection caused by printer lossiness: token=10 vs expected=10 displayed as identical.",
                        Pair(
                            "SearchBFS packet rejected: returned token (10:gen-1) does not match expected token (10:gen-2).",
                            empty,
                        ),
                    ),
                ),
            ),
        )

        # --- Fixture 4: Engel E1 Bare Booleans ---
        f4_frag = StoryFragment(
            "fixture-04",
            cut_id,
            state_version,
            RoleBlockerLabel,
            TrackGLabel,
            "engel_e1_proof",
            "derivation_search",
            EventFailedLabel,
            EvidenceTerm("engel_e1_prove.debug.log:340", "EMPTY=True_UNREACH=False"),
            SalienceHighLabel,
            empty,
            empty,
            all_cuts,
        )()
        f4_entry = Pair(
            "fixture-04-engel-e1-bare-booleans",
            Pair(
                f4_frag,
                Pair(
                    empty,
                    Pair(
                        "Bare host boolean literals emitted; fails to identify unsatisfied goal or failure locus.",
                        Pair(
                            "Proof search exhausted: no valid derivation found for invariant NonNegative(x).",
                            empty,
                        ),
                    ),
                ),
            ),
        )

        # --- Fixture 5: Snapshot Root Pointer Repr ---
        f5_frag = StoryFragment(
            "fixture-05",
            cut_id,
            state_version,
            RoleSetupLabel,
            TrackINTLabel,
            "snapshot_roots",
            "roots_loaded",
            EventCompletedLabel,
            EvidenceTerm("main.py:1042", "pointer_repr=<hyge.core.Pair object>"),
            SalienceLowLabel,
            empty,
            empty,
            eng_rev,
        )()
        f5_entry = Pair(
            "fixture-05-snapshot-pointer-repr",
            Pair(
                f5_frag,
                Pair(
                    empty,
                    Pair(
                        "Surfaces raw Python memory addresses instead of semantic machine state counts.",
                        Pair(
                            "Snapshot roots loaded: registry, rules (121), derivations (0), schemata (0).",
                            empty,
                        ),
                    ),
                ),
            ),
        )

        # --- Fixture 6: SearchBFS Uncoalesced Frontier Batches ---
        f6_frag = StoryFragment(
            "fixture-06",
            cut_id,
            state_version,
            RoleActionLabel,
            TrackELabel,
            "search_bfs_frontier",
            "frontier_packetized",
            EventCompletedLabel,
            EvidenceTerm("cold_debug_stage1_runtime.log:600", "batches=1_remaining=0"),
            SalienceLowLabel,
            empty,
            empty,
            eng_rev,
        )()
        f6_entry = Pair(
            "fixture-06-uncoalesced-frontier",
            Pair(
                f6_frag,
                Pair(
                    empty,
                    Pair(
                        "Emitted redundantly per mode; grammatically unaggregated ('1 batches').",
                        Pair(
                            "Frontier packetized: 1 batch queued; all frontier states allocated.",
                            empty,
                        ),
                    ),
                ),
            ),
        )

        # --- Fixture 7: Engel E1 15 Repeated Negative Rule Probes ---
        f7_frag = StoryFragment(
            "fixture-07",
            cut_id,
            state_version,
            RoleEvidenceLabel,
            TrackGLabel,
            "rule_filter_probes",
            "replacement_mismatch",
            EventHeldLabel,
            EvidenceTerm("engel_e1_prove.debug.log:12", "probes_count=15"),
            SalienceLowLabel,
            empty,
            empty,
            eng_rev,
        )()
        f7_entry = Pair(
            "fixture-07-repeated-rule-filters",
            Pair(
                f7_frag,
                Pair(
                    empty,
                    Pair(
                        "15 identical negative rule probe lines repeated consecutively without aggregation.",
                        Pair(
                            "Goal filter checked 15 candidate rule heads; zero matched target NonNegative(x).",
                            empty,
                        ),
                    ),
                ),
            ),
        )

        # --- Fixture 8: Tao 1.1 Non-Discharge within Budget vs Refutation ---
        # Note: EventNonDischargeBudgetLabel distinguishes budget exhaustion from refutation!
        f8_frag = StoryFragment(
            "fixture-08",
            cut_id,
            state_version,
            RoleBlockerLabel,
            TrackGLabel,
            "tao_problem_1_1",
            "goal_evaluation",
            EventNonDischargeBudgetLabel,
            EvidenceTerm("main.py:441", "timeout=600.0s_expanded=0"),
            SalienceHighLabel,
            empty,
            empty,
            all_cuts,
        )()
        f8_entry = Pair(
            "fixture-08-budget-exhaustion",
            Pair(
                f8_frag,
                Pair(
                    empty,
                    Pair(
                        "Conflates budget exhaustion with refutation; hides initialization bottleneck.",
                        Pair(
                            "Proof search inconclusive: goal undischarged after 600.00s timeout (0 nodes expanded).",
                            empty,
                        ),
                    ),
                ),
            ),
        )

        # --- Fixture 9: Applicability Scan Bottleneck ---
        f9_frag = StoryFragment(
            "fixture-09",
            cut_id,
            state_version,
            RoleBlockerLabel,
            TrackELabel,
            "initial_cursor_applicability",
            "applicability_scan_duration",
            EventHeldLabel,
            EvidenceTerm("08August2026 -- opus 5 answer.md:7", "duration=245.057s_budget_pct=40.8"),
            SalienceHighLabel,
            empty,
            empty,
            all_cuts,
        )()
        # Causal edge: Applicability scan causes budget exhaustion
        f9_edge = StoryEdge(RelationCausesLabel, "fixture-09", "fixture-08")()
        f9_entry = Pair(
            "fixture-09-applicability-bottleneck",
            Pair(
                f9_frag,
                Pair(
                    Pair(f9_edge, empty),
                    Pair(
                        "Critical initialization bottleneck (245.057s scan consuming 40.8% of budget) buried in debug trace.",
                        Pair(
                            "Applicability scan required 245.057s (40.8% of budget), causing subsequent search timeout.",
                            empty,
                        ),
                    ),
                ),
            ),
        )

        # --- Fixture 10: Interleaved Worker Packet Trace ---
        f10_frag = StoryFragment(
            "fixture-10",
            cut_id,
            state_version,
            RoleActionLabel,
            TrackELabel,
            "search_dfs_worker_1857",
            "packet_cycle_completed",
            EventCompletedLabel,
            EvidenceTerm("cold_debug_stage1_runtime.log:475", "pid=1857_status=running"),
            SalienceLowLabel,
            empty,
            empty,
            eng_rev,
        )()
        f10_entry = Pair(
            "fixture-10-interleaved-worker-trace",
            Pair(
                f10_frag,
                Pair(
                    empty,
                    Pair(
                        "Asynchronous interleaved process chatter prevents reading logical progress.",
                        Pair(
                            "SearchDFS resident worker completed packet (expanded=1, generated=1).",
                            empty,
                        ),
                    ),
                ),
            ),
        )

        # --- Fixture 11: Sieve vs Trial Boundary Discrepancy Concealment ---
        # Note: AgreementScope declares projection=composite, while discrepancy on 1 is explicit blocker!
        scope_ev = AgreementScope("projection=composite", "excluded_boundary=1")()
        f11_agree_frag = StoryFragment(
            "fixture-11-agree",
            cut_id,
            state_version,
            RoleEvidenceLabel,
            TrackGLabel,
            "sieve_trial_comparison",
            "composite_classification",
            EventCompletedLabel,
            scope_ev,
            SalienceHighLabel,
            empty,
            empty,
            all_cuts,
        )()
        f11_discrepancy_frag = StoryFragment(
            "fixture-11-discrepancy",
            cut_id,
            state_version,
            RoleDiscrepancyLabel,
            TrackGLabel,
            "integer_1_classification",
            "sieve_excluded_vs_trial_prime",
            EventHeldLabel,
            EvidenceTerm("hyge.py:500-530", "sieve=excluded(below_domain)_trial=prime"),
            SalienceHighLabel,
            empty,
            empty,
            all_cuts,
        )()
        f11_contrast_edge = StoryEdge(RelationContrastsLabel, "fixture-11-discrepancy", "fixture-11-agree")()
        f11_entry = Pair(
            "fixture-11-sieve-trial-boundary-discrepancy",
            Pair(
                Pair(f11_agree_frag, Pair(f11_discrepancy_frag, empty)),
                Pair(
                    Pair(f11_contrast_edge, empty),
                    Pair(
                        "Merger claims AgreeOnSpan on composites while concealing prime/excluded disagreement at 1.",
                        Pair(
                            "Sieve and Trial agree on composites (4, 6, 8, 9); however, integer 1 carries a boundary discrepancy (sieve excluded vs trial prime).",
                            empty,
                        ),
                    ),
                ),
            ),
        )

        # Compose 11 fixtures in machine Pair chain
        self.result = Pair(
            f1_entry,
            Pair(
                f2_entry,
                Pair(
                    f3_entry,
                    Pair(
                        f4_entry,
                        Pair(
                            f5_entry,
                            Pair(
                                f6_entry,
                                Pair(
                                    f7_entry,
                                    Pair(
                                        f8_entry,
                                        Pair(
                                            f9_entry,
                                            Pair(
                                                f10_entry,
                                                Pair(f11_entry, empty),
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
        super().__init__(
            inputs=Pair(cut_id, Pair(state_version, empty)),
            results=self.result,
        )

    def __call__(self):
        return self.result
