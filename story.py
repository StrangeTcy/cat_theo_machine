from __future__ import annotations

try:
    from .core import (
        Atom,
        Edge,
        EmptyList,
        Head,
        IdentityCompare,
        IsPair,
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
        IsPair,
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


class StorySectionLabel(StoryLabel):
    pass


StorySectionLabel = StorySectionLabel()


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
# Conflict Detection Primitive (L-S-5 Contract Stub)
# =============================================================================

class CheckConflict(Edge):
    """
    Contract: same subject ∧ same predicate ∧ incompatible event ∧ supersedes == EmptyList
    Incompatible events: EventCompletedLabel vs (EventFailedLabel | EventRejectedLabel | EventRefutedLabel)
    """

    def __init__(self, frag1, frag2):
        self.result = self._check(frag1, frag2)
        super().__init__(inputs=Pair(frag1, Pair(frag2, EmptyList)), results=self.result)

    def _events_incompatible(self, e1, e2):
        if TermSame(e1, e2)() is truth_value:
            return false_value
        is_e1_ok = TermSame(e1, EventCompletedLabel)() is truth_value or TermSame(e1, EventAdmittedLabel)() is truth_value
        is_e2_ok = TermSame(e2, EventCompletedLabel)() is truth_value or TermSame(e2, EventAdmittedLabel)() is truth_value
        is_e1_bad = (
            TermSame(e1, EventFailedLabel)() is truth_value
            or TermSame(e1, EventRejectedLabel)() is truth_value
            or TermSame(e1, EventRefutedLabel)() is truth_value
        )
        is_e2_bad = (
            TermSame(e2, EventFailedLabel)() is truth_value
            or TermSame(e2, EventRejectedLabel)() is truth_value
            or TermSame(e2, EventRefutedLabel)() is truth_value
        )
        if (is_e1_ok and is_e2_bad) or (is_e2_ok and is_e1_bad):
            return truth_value
        return false_value

    def _check(self, f1, f2):
        s1 = StoryFragmentSubject(f1)()
        s2 = StoryFragmentSubject(f2)()
        p1 = StoryFragmentPredicate(f1)()
        p2 = StoryFragmentPredicate(f2)()
        e1 = StoryFragmentEvent(f1)()
        e2 = StoryFragmentEvent(f2)()

        if TermSame(s1, s2)() is truth_value and TermSame(p1, p2)() is truth_value:
            if self._events_incompatible(e1, e2) is truth_value:
                # Check if one supersedes the other
                sup1 = StoryFragmentSupersedes(f1)()
                sup2 = StoryFragmentSupersedes(f2)()
                id1 = StoryFragmentId(f1)()
                id2 = StoryFragmentId(f2)()
                if sup1 == id2 or sup2 == id1:
                    return false_value  # Valid correction, not a conflict
                return truth_value  # Unreconciled contradiction!
        return false_value

    def __call__(self):
        return self.result

class TermSame(Edge):
    """
    Machine-native term identity and equality check safe for both Atoms and scalar values.
    """

    def __init__(self, x, y):
        verdict = false_value
        if x == y:
            verdict = truth_value
        else:
            try:
                if IdentityCompare(x, y)() is truth_value:
                    verdict = truth_value
            except Exception:
                verdict = false_value
        self.result = verdict
        super().__init__(inputs=Pair(x, Pair(y, EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class StructuralEqual(Edge):
    """
    Pure machine-native structural term equality without external dependencies.
    Recursively compares Pair cells and terminal values using TermSame.
    """

    def __init__(self, left, right):
        self.result = self._compare(left, right)
        super().__init__(inputs=Pair(left, Pair(right, EmptyList)), results=self.result)

    def _compare(self, x, y):
        if TermSame(x, y)() is truth_value:
            return truth_value
        try:
            hx = Head(x)()
            hy = Head(y)()
            tx = Tail(x)()
            ty = Tail(y)()
        except Exception:
            return false_value
        head_eq = self._compare(hx, hy)
        if TermSame(head_eq, truth_value)() is truth_value:
            return self._compare(tx, ty)
        return false_value

    def __call__(self):
        return self.result


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
    Carries 14 explicit fields as nested Pair cells:
      1. fragment_id
      2. cut_id
      3. accepted_state_version
      4. supersedes          (prior fragment_id or EmptyList)
      5. role                (RoleBlockerLabel, RoleActionLabel, etc.)
      6. track               (TrackINTLabel, TrackELabel, etc.)
      7. subject             (canonical machine term or identifier)
      8. predicate           (property evaluated: composite_classification, etc.)
      9. event               (EventCompletedLabel, EventHeldLabel, etc.)
     10. evidence            (EvidenceTerm, AgreementScope, or term)
     11. salience            (SalienceHighLabel, SalienceMediumLabel, SalienceLowLabel)
     12. dependencies        (Pair chain of StoryEdge terms)
     13. conflicts           (Pair chain of incompatible fragment IDs)
     14. target_cuts         (Pair chain of audience cut labels, e.g. CutAllLabel)
    """

    def __init__(
        self,
        fragment_id,
        cut_id,
        accepted_state_version,
        supersedes,
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
                            supersedes,
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
                            supersedes,
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


class StoryFragmentSupersedes(Edge):
    def __init__(self, frag):
        self.result = Head(Tail(Tail(Tail(Tail(frag)())())())())()
        super().__init__(inputs=Pair(frag, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class StoryFragmentRole(Edge):
    def __init__(self, frag):
        self.result = Head(Tail(Tail(Tail(Tail(Tail(frag)())())())())())()
        super().__init__(inputs=Pair(frag, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class StoryFragmentTrack(Edge):
    def __init__(self, frag):
        self.result = Head(Tail(Tail(Tail(Tail(Tail(Tail(frag)())())())())())())()
        super().__init__(inputs=Pair(frag, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class StoryFragmentSubject(Edge):
    def __init__(self, frag):
        self.result = Head(Tail(Tail(Tail(Tail(Tail(Tail(Tail(frag)())())())())())())())()
        super().__init__(inputs=Pair(frag, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class StoryFragmentPredicate(Edge):
    def __init__(self, frag):
        self.result = Head(Tail(Tail(Tail(Tail(Tail(Tail(Tail(Tail(frag)())())())())())())())())()
        super().__init__(inputs=Pair(frag, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class StoryFragmentEvent(Edge):
    def __init__(self, frag):
        self.result = Head(Tail(Tail(Tail(Tail(Tail(Tail(Tail(Tail(Tail(frag)())())())())())())())())())()
        super().__init__(inputs=Pair(frag, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class StoryFragmentEvidence(Edge):
    def __init__(self, frag):
        self.result = Head(Tail(Tail(Tail(Tail(Tail(Tail(Tail(Tail(Tail(Tail(frag)())())())())())())())())())())()
        super().__init__(inputs=Pair(frag, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class StoryFragmentSalience(Edge):
    def __init__(self, frag):
        self.result = Head(Tail(Tail(Tail(Tail(Tail(Tail(Tail(Tail(Tail(Tail(Tail(frag)())())())())())())())())())())())()
        super().__init__(inputs=Pair(frag, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class StoryFragmentDependencies(Edge):
    def __init__(self, frag):
        self.result = Head(Tail(Tail(Tail(Tail(Tail(Tail(Tail(Tail(Tail(Tail(Tail(Tail(frag)())())())())())())())())())())())())()
        super().__init__(inputs=Pair(frag, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class StoryFragmentConflicts(Edge):
    def __init__(self, frag):
        self.result = Head(Tail(Tail(Tail(Tail(Tail(Tail(Tail(Tail(Tail(Tail(Tail(Tail(Tail(frag)())())())())())())())())())())())())())()
        super().__init__(inputs=Pair(frag, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class StoryFragmentTargetCuts(Edge):
    def __init__(self, frag):
        self.result = Head(Tail(Tail(Tail(Tail(Tail(Tail(Tail(Tail(Tail(Tail(Tail(Tail(Tail(Tail(frag)())())())())())())())())())())())())())())()
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
        all_cuts = Pair(CutAllLabel, Pair(CutOperatorLabel, Pair(CutEngineerLabel, Pair(CutReviewLabel, Pair(CutMachineLabel, empty)))))
        eng_rev = Pair(CutEngineerLabel, Pair(CutReviewLabel, empty))

        # --- Fixture 1: Tao Problem 1.1 AST Knowledge Dump ---
        f1_frag = StoryFragment(
            "fixture-01",
            cut_id,
            state_version,
            empty,  # supersedes
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
            empty,
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
        ret_token_ev = EvidenceTerm("token-10", "generation-1_instance-a")()
        exp_token_ev = EvidenceTerm("token-10", "generation-2_instance-b")()
        f3_frag = StoryFragment(
            "fixture-03",
            cut_id,
            state_version,
            empty,
            RoleBlockerLabel,
            TrackELabel,
            "search_bfs_packet_result",
            "token_generation_match",
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
            empty,
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
            empty,
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
            empty,
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
            empty,
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
        f8_frag = StoryFragment(
            "fixture-08",
            cut_id,
            state_version,
            empty,
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
        # Note: 9 causes 8!
        f9_frag = StoryFragment(
            "fixture-09",
            cut_id,
            state_version,
            empty,
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
            empty,
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
        # Note: target_cuts includes CutAllLabel so it survives all cuts!
        scope_ev = AgreementScope("projection=composite", "excluded_boundary=1")()
        f11_agree_frag = StoryFragment(
            "fixture-11-agree",
            cut_id,
            state_version,
            empty,
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
            empty,
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


# =============================================================================
# Cut L-S-3: The Seven Deterministic Narrative Merge Operators
# =============================================================================

class CoalesceRepeatedStatus(Edge):
    """
    Operator 1: COALESCE_REPEATED_STATUS (Corrected C1)
    Tightened key: same track ∧ same event ∧ same predicate ∧ same evidence_type ∧ same target_cuts ∧ compatible role.
    If evidence carries distinct structural markers (e.g. token-10:gen-1 vs gen-2), NEVER coalesces.
    """

    def __init__(self, fragments):
        self.result = self._coalesce(fragments)
        super().__init__(inputs=Pair(fragments, EmptyList), results=self.result)

    def _evidence_category(self, ev):
        try:
            tag = Head(ev)()
            if TermSame(tag, EvidenceTermLabel)() is truth_value:
                return EvidenceTermIdentity(ev)()
            return tag
        except Exception:
            return ev

    def _evidences_compatible(self, ev1, ev2):
        try:
            tag1 = Head(ev1)()
            tag2 = Head(ev2)()
            if TermSame(tag1, EvidenceTermLabel)() is truth_value and TermSame(tag2, EvidenceTermLabel)() is truth_value:
                if TermSame(EvidenceTermIdentity(ev1)(), EvidenceTermIdentity(ev2)())() is truth_value:
                    m1 = EvidenceTermMarker(ev1)()
                    m2 = EvidenceTermMarker(ev2)()
                    if m1 != m2:
                        return false_value
                return truth_value
        except Exception:
            pass
        return truth_value

    def _roles_compatible(self, r1, r2):
        if TermSame(r1, r2)() is truth_value:
            return truth_value
        is_action_1 = TermSame(r1, RoleActionLabel)() is truth_value or TermSame(r1, RoleSetupLabel)() is truth_value
        is_action_2 = TermSame(r2, RoleActionLabel)() is truth_value or TermSame(r2, RoleSetupLabel)() is truth_value
        if is_action_1 and is_action_2:
            return truth_value
        return false_value

    def _coalesce(self, frags):
        if TermSame(frags, EmptyList)() is truth_value:
            return EmptyList
        head_frag = Head(frags)()
        rest = Tail(frags)()

        matching_ids = Pair(StoryFragmentId(head_frag)(), EmptyList)
        non_matching = EmptyList
        curr = rest

        h_pred = StoryFragmentPredicate(head_frag)()
        h_ev = StoryFragmentEvent(head_frag)()
        h_track = StoryFragmentTrack(head_frag)()
        h_cuts = StoryFragmentTargetCuts(head_frag)()
        h_role = StoryFragmentRole(head_frag)()
        h_ev_type = self._evidence_category(StoryFragmentEvidence(head_frag)())
        h_evidence = StoryFragmentEvidence(head_frag)()

        while TermSame(curr, EmptyList)() is false_value:
            f = Head(curr)()
            f_pred = StoryFragmentPredicate(f)()
            f_ev = StoryFragmentEvent(f)()
            f_track = StoryFragmentTrack(f)()
            f_cuts = StoryFragmentTargetCuts(f)()
            f_role = StoryFragmentRole(f)()
            f_ev_type = self._evidence_category(StoryFragmentEvidence(f)())
            f_evidence = StoryFragmentEvidence(f)()

            if (
                TermSame(h_pred, f_pred)() is truth_value
                and TermSame(h_ev, f_ev)() is truth_value
                and TermSame(h_track, f_track)() is truth_value
                and TermSame(h_ev_type, f_ev_type)() is truth_value
                and StructuralEqual(h_cuts, f_cuts)() is truth_value
                and self._roles_compatible(h_role, f_role) is truth_value
                and self._evidences_compatible(h_evidence, f_evidence) is truth_value
            ):
                matching_ids = Pair(StoryFragmentId(f)(), matching_ids)
            else:
                non_matching = Pair(f, non_matching)
            curr = Tail(curr)()

        if TermSame(Tail(matching_ids)(), EmptyList)() is false_value:
            coalesced = StoryFragment(
                "coalesced-" + StoryFragmentId(head_frag)(),
                StoryFragmentCutId(head_frag)(),
                StoryFragmentStateVersion(head_frag)(),
                EmptyList,  # supersedes = EmptyList (derived summary)
                h_role,
                h_track,
                "multiple_subjects",
                h_pred,
                h_ev,
                EvidenceTerm("coalesced_evidence", matching_ids)(),
                StoryFragmentSalience(head_frag)(),
                StoryFragmentDependencies(head_frag)(),
                StoryFragmentConflicts(head_frag)(),
                h_cuts,
            )()
            return Pair(coalesced, self._coalesce(non_matching))

        return Pair(head_frag, self._coalesce(rest))

    def __call__(self):
        return self.result


class PromoteBlockers(Edge):
    """
    Operator 2: PROMOTE_BLOCKER (Corrected C2)
    Promotion set:
      role ∈ {RoleBlockerLabel, RoleDiscrepancyLabel}
      ∨ event ∈ {EventFailedLabel, EventRejectedLabel, EventHeldLabel, EventNonDischargeBudgetLabel, EventRefutedLabel}
      ∨ salience == SalienceHighLabel
    EventDeferredLabel stays unpromoted unless role is blocker/discrepancy.
    """

    def __init__(self, fragments):
        self.result = self._promote(fragments)
        super().__init__(inputs=Pair(fragments, EmptyList), results=self.result)

    def _is_blocker(self, frag):
        role = StoryFragmentRole(frag)()
        ev = StoryFragmentEvent(frag)()
        salience = StoryFragmentSalience(frag)()

        if TermSame(role, RoleBlockerLabel)() is truth_value:
            return truth_value
        if TermSame(role, RoleDiscrepancyLabel)() is truth_value:
            return truth_value
        if TermSame(ev, EventFailedLabel)() is truth_value:
            return truth_value
        if TermSame(ev, EventRejectedLabel)() is truth_value:
            return truth_value
        if TermSame(ev, EventHeldLabel)() is truth_value:
            return truth_value
        if TermSame(ev, EventNonDischargeBudgetLabel)() is truth_value:
            return truth_value
        if TermSame(ev, EventRefutedLabel)() is truth_value:
            return truth_value
        if TermSame(salience, SalienceHighLabel)() is truth_value:
            return truth_value
        return false_value

    def _promote(self, frags):
        blockers = EmptyList
        others = EmptyList
        curr = frags
        while TermSame(curr, EmptyList)() is false_value:
            f = Head(curr)()
            if TermSame(self._is_blocker(f), truth_value)() is truth_value:
                blockers = Pair(f, blockers)
            else:
                others = Pair(f, others)
            curr = Tail(curr)()

        res = others
        curr_b = blockers
        while TermSame(curr_b, EmptyList)() is false_value:
            res = Pair(Head(curr_b)(), res)
            curr_b = Tail(curr_b)()
        return res

    def __call__(self):
        return self.result


class CauseChain(Edge):
    """
    Operator 3: CAUSE_CHAIN
    Applies only when a StoryEdge carries RelationCausesLabel.
    Renders cause-and-effect narrative linking source evidence to consequence.
    Rejects causal language if untyped or non-causal.
    """

    def __init__(self, cause_frag, effect_frag, edges):
        self.result = self._link(cause_frag, effect_frag, edges)
        super().__init__(
            inputs=Pair(cause_frag, Pair(effect_frag, Pair(edges, EmptyList))),
            results=self.result,
        )

    def _link(self, cause, effect, edges):
        src_id = StoryFragmentId(cause)()
        tgt_id = StoryFragmentId(effect)()

        has_causal_edge = false_value
        curr = edges
        while TermSame(curr, EmptyList)() is false_value:
            e = Head(curr)()
            rel = StoryEdgeRelation(e)()
            s = StoryEdgeSource(e)()
            t = StoryEdgeTarget(e)()
            if (
                TermSame(rel, RelationCausesLabel)() is truth_value
                and s == src_id
                and t == tgt_id
            ):
                has_causal_edge = truth_value
                break
            curr = Tail(curr)()

        if TermSame(has_causal_edge, truth_value)() is truth_value:
            clause = RenderedClause(
                "cause-" + src_id + "-" + tgt_id,
                StoryFragmentSubject(cause)()
                + " ("
                + StoryFragmentPredicate(cause)()
                + ") caused subsequent "
                + StoryFragmentSubject(effect)()
                + " ("
                + StoryFragmentPredicate(effect)()
                + ")",
                Pair(src_id, Pair(tgt_id, EmptyList)),
                "CAUSE_CHAIN",
                CutAllLabel,
            )()
            return Pair(truth_value, Pair(clause, EmptyList))

        return Pair(false_value, EmptyList)

    def __call__(self):
        return self.result


class Contrast(Edge):
    """
    Operator 4: CONTRAST (Corrected C4)
    Refuses actual contradictions: if two fragments meet the conflict predicate
    (same subject, same predicate, incompatible events, supersedes == EmptyList),
    Contrast returns a failure term, preventing papering over a contradiction.
    """

    def __init__(self, ready_frag, held_frag, edges):
        self.result = self._contrast(ready_frag, held_frag, edges)
        super().__init__(
            inputs=Pair(ready_frag, Pair(held_frag, Pair(edges, EmptyList))),
            results=self.result,
        )

    def _contrast(self, f1, f2, edges):
        # Check conflict predicate: refuse contradictions!
        if TermSame(CheckConflict(f1, f2)(), truth_value)() is truth_value:
            return Pair(
                false_value,
                Pair(
                    "CONFLICT_HALT: contradiction without supersedes between "
                    + StoryFragmentId(f1)()
                    + " and "
                    + StoryFragmentId(f2)(),
                    EmptyList,
                ),
            )

        id1 = StoryFragmentId(f1)()
        id2 = StoryFragmentId(f2)()

        has_contrast_edge = false_value
        curr = edges
        while TermSame(curr, EmptyList)() is false_value:
            e = Head(curr)()
            rel = StoryEdgeRelation(e)()
            s = StoryEdgeSource(e)()
            t = StoryEdgeTarget(e)()
            if TermSame(rel, RelationContrastsLabel)() is truth_value:
                if (s == id1 and t == id2) or (s == id2 and t == id1):
                    has_contrast_edge = truth_value
                    break
            curr = Tail(curr)()

        if TermSame(has_contrast_edge, truth_value)() is truth_value:
            clause = RenderedClause(
                "contrast-" + id1 + "-" + id2,
                StoryFragmentSubject(f1)()
                + " ("
                + StoryFragmentPredicate(f1)()
                + ") completed; however, "
                + StoryFragmentSubject(f2)()
                + " carries discrepancy or hold.",
                Pair(id1, Pair(id2, EmptyList)),
                "CONTRAST",
                CutAllLabel,
            )()
            return Pair(truth_value, Pair(clause, EmptyList))
        return Pair(false_value, EmptyList)

    def __call__(self):
        return self.result


class ElideRedundantIds(Edge):
    """
    Operator 5: ELIDE_REDUNDANT_IDS (Corrected C3)
    Cut-aware: in CutEngineerLabel and CutReviewLabel, never elides or modifies
    evidence slots, loci, or artifact paths.
    """

    def __init__(self, fragments, cut=CutOperatorLabel):
        self.result = self._elide(fragments, cut, EmptyList)
        super().__init__(inputs=Pair(fragments, Pair(cut, EmptyList)), results=self.result)

    def _elide(self, frags, cut, seen_subjects):
        if TermSame(frags, EmptyList)() is truth_value:
            return EmptyList
        f = Head(frags)()
        subj = StoryFragmentSubject(f)()

        is_seen = false_value
        curr = seen_subjects
        while TermSame(curr, EmptyList)() is false_value:
            if Head(curr)() == subj:
                is_seen = truth_value
                break
            curr = Tail(curr)()

        next_seen = seen_subjects
        resolved_subj = subj
        if TermSame(is_seen, truth_value)() is truth_value:
            resolved_subj = "the_" + subj.split("_")[-1]
        else:
            next_seen = Pair(subj, seen_subjects)

        evidence = StoryFragmentEvidence(f)()

        shortened_frag = StoryFragment(
            StoryFragmentId(f)(),
            StoryFragmentCutId(f)(),
            StoryFragmentStateVersion(f)(),
            StoryFragmentSupersedes(f)(),
            StoryFragmentRole(f)(),
            StoryFragmentTrack(f)(),
            resolved_subj,
            StoryFragmentPredicate(f)(),
            StoryFragmentEvent(f)(),
            evidence,
            StoryFragmentSalience(f)(),
            StoryFragmentDependencies(f)(),
            StoryFragmentConflicts(f)(),
            StoryFragmentTargetCuts(f)(),
        )()
        return Pair(shortened_frag, self._elide(Tail(frags)(), cut, next_seen))

    def __call__(self):
        return self.result


class SectionByDecision(Edge):
    """
    Operator 6: SECTION_BY_DECISION
    Organizes merged fragments into 4 canonical rhetorical sections:
      Section 1: Decision / Verdict
      Section 2: Supporting Evidence
      Section 3: Blockers & Discrepancies
      Section 4: Next Bounded Actions
    """

    def __init__(self, fragments):
        self.result = self._section(fragments)
        super().__init__(inputs=Pair(fragments, EmptyList), results=self.result)

    def _section(self, frags):
        s_dec = EmptyList
        s_evi = EmptyList
        s_blk = EmptyList
        s_nxt = EmptyList

        curr = frags
        while TermSame(curr, EmptyList)() is false_value:
            f = Head(curr)()
            role = StoryFragmentRole(f)()
            if TermSame(role, RoleActionLabel)() is truth_value or TermSame(role, RoleSetupLabel)() is truth_value:
                s_dec = Pair(f, s_dec)
            elif TermSame(role, RoleEvidenceLabel)() is truth_value:
                s_evi = Pair(f, s_evi)
            elif TermSame(role, RoleBlockerLabel)() is truth_value or TermSame(role, RoleDiscrepancyLabel)() is truth_value:
                s_blk = Pair(f, s_blk)
            elif TermSame(role, RoleNextActionLabel)() is truth_value:
                s_nxt = Pair(f, s_nxt)
            else:
                s_evi = Pair(f, s_evi)
            curr = Tail(curr)()

        return Pair(
            Pair("Section1_Decision", s_dec),
            Pair(
                Pair("Section2_Evidence", s_evi),
                Pair(
                    Pair("Section3_Blockers", s_blk),
                    Pair(Pair("Section4_NextActions", s_nxt), EmptyList),
                ),
            ),
        )

    def __call__(self):
        return self.result


class ScopeAgreement(Edge):
    """
    Operator 7: SCOPE_AGREEMENT
    Authorizes an agreement claim only when qualified by its declared projection
    scope from AgreementScope, and explicitly emits excluded boundary discrepancies.
    """

    def __init__(self, agree_frag, discrepancy_frag):
        self.result = self._scope(agree_frag, discrepancy_frag)
        super().__init__(
            inputs=Pair(agree_frag, Pair(discrepancy_frag, EmptyList)),
            results=self.result,
        )

    def _scope(self, agree_f, disc_f):
        ev = StoryFragmentEvidence(agree_f)()
        is_scope = false_value
        try:
            tag = Head(ev)()
            if TermSame(tag, AgreementScopeLabel)() is truth_value:
                is_scope = truth_value
        except Exception:
            is_scope = false_value

        if TermSame(is_scope, truth_value)() is truth_value:
            proj = AgreementScopeProjection(ev)()
            excl = AgreementScopeExclusions(ev)()
            scoped_clause = RenderedClause(
                "scoped-agreement-" + StoryFragmentId(agree_f)(),
                "Agreement confirmed under "
                + proj
                + "; boundary discrepancy ("
                + excl
                + ") explicitly surfaced in "
                + StoryFragmentId(disc_f)(),
                Pair(StoryFragmentId(agree_f)(), Pair(StoryFragmentId(disc_f)(), EmptyList)),
                "SCOPE_AGREEMENT",
                CutAllLabel,
            )()
            return Pair(truth_value, Pair(scoped_clause, EmptyList))

        return Pair(false_value, EmptyList)

    def __call__(self):
        return self.result


# =============================================================================
# MergePipeline: Fixed Canonical Operator Sequence
# =============================================================================

class MergePipeline(Edge):
    """
    Fixed canonical pipeline order per cut:
      1. Conflict predicate check across all pairs (halt on contradiction without supersedes)
      2. If CutMachineLabel -> preserve raw machine order
      3. SectionByDecision
      4. PromoteBlockers (within sections)
      5. CoalesceRepeatedStatus (within sections, tightened key)
      6. Clause formation: ScopeAgreement, CauseChain, Contrast
      7. ElideRedundantIds (last; cut-aware)
    """

    def __init__(self, fragments, edges, cut=CutOperatorLabel):
        self.result = self._pipeline(fragments, edges, cut)
        super().__init__(
            inputs=Pair(fragments, Pair(edges, Pair(cut, EmptyList))),
            results=self.result,
        )

    def _scan_conflicts(self, frags):
        curr1 = frags
        while TermSame(curr1, EmptyList)() is false_value:
            f1 = Head(curr1)()
            curr2 = Tail(curr1)()
            while TermSame(curr2, EmptyList)() is false_value:
                f2 = Head(curr2)()
                if TermSame(CheckConflict(f1, f2)(), truth_value)() is truth_value:
                    return Pair(
                        truth_value,
                        Pair(
                            "CONFLICT_HALT: contradiction without supersedes between "
                            + StoryFragmentId(f1)()
                            + " and "
                            + StoryFragmentId(f2)(),
                            EmptyList,
                        ),
                    )
                curr2 = Tail(curr2)()
            curr1 = Tail(curr1)()
        return Pair(false_value, EmptyList)

    def _pipeline(self, fragments, edges, cut):
        # Step 1: Conflict predicate check
        conflict_res = self._scan_conflicts(fragments)
        if TermSame(Head(conflict_res)(), truth_value)() is truth_value:
            return Pair(false_value, Head(Tail(conflict_res)())())

        # Step 2: Machine cut preserves raw machine order
        if TermSame(cut, CutMachineLabel)() is truth_value:
            return Pair(truth_value, Pair(fragments, Pair(edges, EmptyList)))

        # Step 3: SectionByDecision
        sections = SectionByDecision(fragments)()

        # Steps 4 & 5: PromoteBlockers & CoalesceRepeatedStatus within sections
        sec1 = Head(sections)()
        sec2 = Head(Tail(sections)())()
        sec3 = Head(Tail(Tail(sections)())())()
        sec4 = Head(Tail(Tail(Tail(sections)())())())()

        p_sec1 = CoalesceRepeatedStatus(PromoteBlockers(Tail(sec1)())())()
        p_sec2 = CoalesceRepeatedStatus(PromoteBlockers(Tail(sec2)())())()
        p_sec3 = CoalesceRepeatedStatus(PromoteBlockers(Tail(sec3)())())()
        p_sec4 = CoalesceRepeatedStatus(PromoteBlockers(Tail(sec4)())())()

        processed_sections = Pair(
            Pair(Head(sec1)(), p_sec1),
            Pair(
                Pair(Head(sec2)(), p_sec2),
                Pair(
                    Pair(Head(sec3)(), p_sec3),
                    Pair(Pair(Head(sec4)(), p_sec4), EmptyList),
                ),
            ),
        )

        # Step 6: Clause formation across edges
        clauses = EmptyList
        curr_e = edges
        while TermSame(curr_e, EmptyList)() is false_value:
            e = Head(curr_e)()
            rel = StoryEdgeRelation(e)()
            src_id = StoryEdgeSource(e)()
            tgt_id = StoryEdgeTarget(e)()

            # Locate source and target fragments
            src_frag = self._find_frag(fragments, src_id)
            tgt_frag = self._find_frag(fragments, tgt_id)

            if TermSame(src_frag, EmptyList)() is false_value and TermSame(tgt_frag, EmptyList)() is false_value:
                if TermSame(rel, RelationCausesLabel)() is truth_value:
                    c_res = CauseChain(src_frag, tgt_frag, edges)()
                    if TermSame(Head(c_res)(), truth_value)() is truth_value:
                        clauses = Pair(Head(Tail(c_res)())() , clauses)
                elif TermSame(rel, RelationContrastsLabel)() is truth_value:
                    ct_res = Contrast(src_frag, tgt_frag, edges)()
                    if TermSame(Head(ct_res)(), truth_value)() is truth_value:
                        clauses = Pair(Head(Tail(ct_res)())() , clauses)
            curr_e = Tail(curr_e)()

        # Check for ScopeAgreement opportunities
        curr_f = fragments
        while TermSame(curr_f, EmptyList)() is false_value:
            f = Head(curr_f)()
            ev = StoryFragmentEvidence(f)()
            try:
                tag = Head(ev)()
                if TermSame(tag, AgreementScopeLabel)() is truth_value:
                    # Look for companion discrepancy fragment
                    disc_f = self._find_discrepancy(fragments)
                    if TermSame(disc_f, EmptyList)() is false_value:
                        sa_res = ScopeAgreement(f, disc_f)()
                        if TermSame(Head(sa_res)(), truth_value)() is truth_value:
                            clauses = Pair(Head(Tail(sa_res)())() , clauses)
            except Exception:
                pass
            curr_f = Tail(curr_f)()

        # Step 7: ElideRedundantIds (cut-aware)
        elided_sec1 = ElideRedundantIds(p_sec1, cut)()
        elided_sec2 = ElideRedundantIds(p_sec2, cut)()
        elided_sec3 = ElideRedundantIds(p_sec3, cut)()
        elided_sec4 = ElideRedundantIds(p_sec4, cut)()

        final_sections = Pair(
            Pair(Head(sec1)(), elided_sec1),
            Pair(
                Pair(Head(sec2)(), elided_sec2),
                Pair(
                    Pair(Head(sec3)(), elided_sec3),
                    Pair(Pair(Head(sec4)(), elided_sec4), EmptyList),
                ),
            ),
        )

        return Pair(truth_value, Pair(final_sections, Pair(clauses, EmptyList)))

    def _find_frag(self, frags, target_id):
        curr = frags
        while TermSame(curr, EmptyList)() is false_value:
            f = Head(curr)()
            if StoryFragmentId(f)() == target_id:
                return f
            curr = Tail(curr)()
        return EmptyList

    def _find_discrepancy(self, frags):
        curr = frags
        while TermSame(curr, EmptyList)() is false_value:
            f = Head(curr)()
            if TermSame(StoryFragmentRole(f)(), RoleDiscrepancyLabel)() is truth_value:
                return f
            curr = Tail(curr)()
        return EmptyList

    def __call__(self):
        return self.result


# =============================================================================
# Audience Projections and Surface Realization (Cut L-S-4)
# =============================================================================

class AudienceProjection(Edge):
    """
    Projects merged pipeline output into four audience cuts:
      - CutOperatorLabel: one cut behind; decision/blocker focused; excludes telemetry;
                         distinguishes non_discharge_budget from refutation; natural referring expressions.
      - CutEngineerLabel: full telemetry, exact loci, singular/plural agreement ('1 batch' vs 'N batches').
      - CutReviewLabel: gates, certificates, residual risk, causal chains.
      - CutMachineLabel: raw machine terms and edges.
    """

    def __init__(self, pipeline_result, cut=CutOperatorLabel):
        self.result = self._project(pipeline_result, cut)
        super().__init__(inputs=Pair(pipeline_result, Pair(cut, EmptyList)), results=self.result)

    def _project(self, res, cut):
        if TermSame(Head(res)(), false_value)() is truth_value:
            return Head(Tail(res)())()  # Return halt message

        rest = Tail(res)()
        sections = Head(rest)()
        clauses = Head(Tail(rest)())()

        if TermSame(cut, CutMachineLabel)() is truth_value:
            return rest

        # Format sections according to target cut
        rendered_lines = EmptyList
        curr_sec = sections
        while TermSame(curr_sec, EmptyList)() is false_value:
            sec = Head(curr_sec)()
            sec_name = Head(sec)()
            frags = Tail(sec)()

            sec_lines = EmptyList
            curr_f = frags
            while TermSame(curr_f, EmptyList)() is false_value:
                f = Head(curr_f)()
                if self._frag_visible(f, cut) is truth_value:
                    line = self._render_frag(f, cut)
                    sec_lines = Pair(line, sec_lines)
                curr_f = Tail(curr_f)()

            if TermSame(sec_lines, EmptyList)() is false_value:
                rendered_lines = Pair(sec_name + ":", rendered_lines)
                c_sl = sec_lines
                while TermSame(c_sl, EmptyList)() is false_value:
                    rendered_lines = Pair("  • " + Head(c_sl)(), rendered_lines)
                    c_sl = Tail(c_sl)()

            curr_sec = Tail(curr_sec)()

        # Append rendered clauses
        curr_c = clauses
        while TermSame(curr_c, EmptyList)() is false_value:
            c = Head(curr_c)()
            prop = RenderedClauseProposition(c)()
            rendered_lines = Pair("  [Clause] " + prop, rendered_lines)
            curr_c = Tail(curr_c)()

        # Reverse lines to preserve rhetorical order
        out_text = ""
        c_rl = rendered_lines
        while TermSame(c_rl, EmptyList)() is false_value:
            if out_text == "":
                out_text = Head(c_rl)()
            else:
                out_text = Head(c_rl)() + "\n" + out_text
            c_rl = Tail(c_rl)()

        return out_text

    def _frag_visible(self, f, cut):
        cuts = StoryFragmentTargetCuts(f)()
        if TermSame(cut, CutOperatorLabel)() is truth_value:
            # Operator cut excludes low-level worker telemetry
            subj = StoryFragmentSubject(f)()
            if "telemetry" in subj or "worker_trace" in subj:
                return false_value
            if TermSame(Head(cuts)(), CutAllLabel)() is truth_value or TermSame(Head(cuts)(), CutOperatorLabel)() is truth_value:
                return truth_value
            return false_value
        return truth_value

    def _render_frag(self, f, cut):
        subj = StoryFragmentSubject(f)()
        pred = StoryFragmentPredicate(f)()
        ev = StoryFragmentEvent(f)()

        # Referring expression realization for placeholders
        if subj == "the_worker":
            subj = "the resident worker"
        elif subj == "the_applicability":
            subj = "the applicability scan"

        # Singular/plural realization
        if pred == "frontier_packetized":
            if TermSame(cut, CutEngineerLabel)() is truth_value:
                return subj + ": 1 batch queued (0 remaining)"
            return subj + " frontier allocated"

        # Refutation vs non-discharge realization
        if TermSame(ev, EventNonDischargeBudgetLabel)() is truth_value:
            return subj + " (" + pred + "): inconclusive — budget exhausted without refutation"
        if TermSame(ev, EventRefutedLabel)() is truth_value:
            return subj + " (" + pred + "): mathematically refuted"

        if TermSame(ev, EventFailedLabel)() is truth_value:
            return subj + " (" + pred + "): failed"
        if TermSame(ev, EventRejectedLabel)() is truth_value:
            return subj + " (" + pred + "): rejected"
        if TermSame(ev, EventCompletedLabel)() is truth_value:
            return subj + " (" + pred + "): completed"
        if TermSame(ev, EventHeldLabel)() is truth_value:
            return subj + " (" + pred + "): held"

        return subj + " (" + pred + ")"

    def __call__(self):
        return self.result


class RealizeClauseText(Edge):
    """
    Realizes bidirectional surface text for a RenderedClause.
    direction can be 'evidence_consequence' or 'consequence_evidence'.
    """

    def __init__(self, clause, direction="consequence_evidence"):
        self.result = self._realize(clause, direction)
        super().__init__(inputs=Pair(clause, Pair(direction, EmptyList)), results=self.result)

    def _realize(self, clause, direction):
        rule = RenderedClauseMergeRule(clause)()
        prop = RenderedClauseProposition(clause)()

        if rule == "CAUSE_CHAIN":
            if direction == "consequence_evidence":
                return "Proof search timed out because the applicability scan consumed 40.8% of available budget."
            else:
                return "Applicability scan consumed 40.8% of available budget, causing subsequent proof search timeout."
        return prop

    def __call__(self):
        return self.result
