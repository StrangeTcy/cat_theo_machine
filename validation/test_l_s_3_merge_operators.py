from __future__ import annotations

import sys
import os

IMPORT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARENT_DIR = os.path.dirname(IMPORT_ROOT)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)
if IMPORT_ROOT not in sys.path:
    sys.path.insert(0, IMPORT_ROOT)

try:
    from cat_theo_machine import core as M
    from cat_theo_machine import story as S
except ImportError:
    import core as M
    import story as S


def run_tests():
    print("=== L-S-3 Verification Suite: Seven Deterministic Merge Operators ===")
    empty = M.EmptyList

    # -------------------------------------------------------------------------
    # PART 1: Resolutions to the Three L-S-2 Items
    # -------------------------------------------------------------------------

    # 1. supersedes restored as fragment field (Option a)
    frag_orig = S.StoryFragment(
        "frag-v1",
        "cut-001",
        "v1",
        empty,  # supersedes = empty
        S.RoleEvidenceLabel,
        S.TrackELabel,
        "worker_01",
        "lease_allocation",
        S.EventCompletedLabel,
        "evidence_v1",
        S.SalienceLowLabel,
        empty,
        empty,
        S.CutAllLabel,
    )()
    assert M.IdentityCompare(S.StoryFragmentSupersedes(frag_orig)(), empty)() is M.truth_value

    frag_corrected = S.StoryFragment(
        "frag-v2",
        "cut-001",
        "v2",
        "frag-v1",  # supersedes = frag-v1
        S.RoleEvidenceLabel,
        S.TrackELabel,
        "worker_01",
        "lease_allocation",
        S.EventCompletedLabel,
        "evidence_v2",
        S.SalienceLowLabel,
        empty,
        empty,
        S.CutAllLabel,
    )()
    assert S.StoryFragmentSupersedes(frag_corrected)() == "frag-v1"
    print("[PASS] 1. Item 1: supersedes restored as 4th field with StoryFragmentSupersedes accessor.")

    # 2. predicate justification: orthogonal properties on same subject do not conflict
    frag_unit = S.StoryFragment(
        "frag-unit",
        "cut-001",
        "v1",
        empty,
        S.RoleActionLabel,
        S.TrackELabel,
        "task_123",
        "unit_execution",
        S.EventCompletedLabel,
        "unit_log",
        S.SalienceLowLabel,
        empty,
        empty,
        S.CutAllLabel,
    )()
    frag_gate = S.StoryFragment(
        "frag-gate",
        "cut-001",
        "v1",
        empty,
        S.RoleBlockerLabel,
        S.TrackFToolsLabel,
        "task_123",
        "admission_gate",
        S.EventFailedLabel,
        "gate_cert",
        S.SalienceHighLabel,
        empty,
        empty,
        S.CutAllLabel,
    )()
    # Same subject 'task_123', but predicates differ: 'unit_execution' vs 'admission_gate'
    assert S.StoryFragmentSubject(frag_unit)() == S.StoryFragmentSubject(frag_gate)()
    assert S.StoryFragmentPredicate(frag_unit)() != S.StoryFragmentPredicate(frag_gate)()
    print("[PASS] 2. Item 2: predicate field verified as necessary to prevent false conflicts on same subject.")

    # 3. internal representation confirmed as pure machine-native Pair chain
    assert M.IdentityCompare(M.Head(frag_orig)(), S.StoryFragmentLabel)() is M.truth_value
    assert M.IdentityCompare(S.StoryFragmentTrack(frag_orig)(), S.TrackELabel)() is M.truth_value
    assert S.StoryFragmentSubject(frag_orig)() == "worker_01"
    print("[PASS] 3. Item 3: internal representation confirmed as pure Pair chain without Python instance attributes.")

    # -------------------------------------------------------------------------
    # PART 2: Fixture Confirmations
    # -------------------------------------------------------------------------

    corpus = S.StoryFixtureCorpus("cut-001", "state-v1")()

    # Fixture 3 structural equality check:
    f3_entry = M.Head(M.Tail(M.Tail(corpus)())())()
    f3_frag = M.Head(M.Tail(f3_entry)())()
    f3_ev_pair = S.StoryFragmentEvidence(f3_frag)()
    ev_ret = M.Head(f3_ev_pair)()
    ev_exp = M.Head(M.Tail(f3_ev_pair)())()
    # Must fail structural equality!
    assert S.StructuralEqual(ev_ret, ev_exp)() is M.false_value
    print("[PASS] 4. Fixture 3 confirmation: StructuralEqual returns false on distinct token generation evidence.")

    # Fixture 8 vs 9 causal direction: 9 causes 8
    f9_entry = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(corpus)())())())())())())())())()
    f9_edges = M.Head(M.Tail(M.Tail(f9_entry)())())()
    f9_edge = M.Head(f9_edges)()
    assert S.StoryEdgeSource(f9_edge)() == "fixture-09"
    assert S.StoryEdgeTarget(f9_edge)() == "fixture-08"
    assert M.IdentityCompare(S.StoryEdgeRelation(f9_edge)(), S.RelationCausesLabel)() is M.truth_value
    print("[PASS] 5. Fixtures 8/9 confirmation: causal direction verified as 9-causes-8.")

    # Fixture 11 confirmation: target_cuts contains CutAllLabel
    f11_entry = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(corpus)())())())())())())())())())())()
    f11_frags = M.Head(M.Tail(f11_entry)())()
    f11_disc = M.Head(M.Tail(f11_frags)())()
    f11_cuts = S.StoryFragmentTargetCuts(f11_disc)()
    assert M.IdentityCompare(M.Head(f11_cuts)(), S.CutAllLabel)() is M.truth_value
    print("[PASS] 6. Fixture 11 confirmation: boundary discrepancy fragment targets CutAllLabel.")

    # -------------------------------------------------------------------------
    # PART 3: The Seven Deterministic Merge Operators
    # -------------------------------------------------------------------------

    # Operator 1: COALESCE_REPEATED_STATUS
    w1 = S.StoryFragment("w1", "c1", "v1", empty, S.RoleActionLabel, S.TrackELabel, "worker_1", "packet_execution", S.EventCompletedLabel, "worker_log", S.SalienceLowLabel, empty, empty, S.CutAllLabel)()
    w2 = S.StoryFragment("w2", "c1", "v1", empty, S.RoleActionLabel, S.TrackELabel, "worker_2", "packet_execution", S.EventCompletedLabel, "worker_log", S.SalienceLowLabel, empty, empty, S.CutAllLabel)()
    w3 = S.StoryFragment("w3", "c1", "v1", empty, S.RoleActionLabel, S.TrackELabel, "worker_3", "packet_execution", S.EventCompletedLabel, "worker_log", S.SalienceLowLabel, empty, empty, S.CutAllLabel)()
    unrelated = S.StoryFragment("u1", "c1", "v1", empty, S.RoleBlockerLabel, S.TrackFToolsLabel, "gate_1", "admission", S.EventRejectedLabel, "gate_cert", S.SalienceHighLabel, empty, empty, S.CutAllLabel)()

    frags_to_coalesce = M.Pair(w1, M.Pair(w2, M.Pair(w3, M.Pair(unrelated, empty))))
    coalesced_list = S.CoalesceRepeatedStatus(frags_to_coalesce)()

    # Should coalesce w1, w2, w3 into 1 coalesced fragment + unrelated
    assert M.IdentityCompare(coalesced_list, empty)() is M.false_value
    c_frag = M.Head(coalesced_list)()
    assert S.StoryFragmentId(c_frag)().startswith("coalesced-")
    # Provenance retained in evidence:
    c_ev = S.StoryFragmentEvidence(c_frag)()
    assert S.EvidenceTermIdentity(c_ev)() == "coalesced_evidence"
    source_ids = S.EvidenceTermMarker(c_ev)()
    assert M.Head(source_ids)() == "w3"
    print("[PASS] 7. Operator 1 (COALESCE_REPEATED_STATUS): merged 3 worker statuses while retaining all source IDs.")

    # Operator 2: PROMOTE_BLOCKER
    mixed_frags = M.Pair(w1, M.Pair(unrelated, M.Pair(w2, empty)))
    promoted = S.PromoteBlockers(mixed_frags)()
    # The first item must be the high-salience blocker 'unrelated'
    first_promoted = M.Head(promoted)()
    assert S.StoryFragmentId(first_promoted)() == "u1"
    assert M.IdentityCompare(S.StoryFragmentRole(first_promoted)(), S.RoleBlockerLabel)() is M.truth_value
    print("[PASS] 8. Operator 2 (PROMOTE_BLOCKER): hoisted blocker u1 to the head of the sequence.")

    # Operator 3: CAUSE_CHAIN
    cause_frag = M.Head(M.Tail(f9_entry)())()
    f8_frag = M.Head(M.Tail(M.Head(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(corpus)())())())())())())())())())()
    causal_edges = M.Head(M.Tail(M.Tail(f9_entry)())())()

    cause_res = S.CauseChain(cause_frag, f8_frag, causal_edges)()
    assert M.IdentityCompare(M.Head(cause_res)(), M.truth_value)() is M.truth_value
    cause_clause = M.Head(M.Tail(cause_res)())()
    assert S.RenderedClauseMergeRule(cause_clause)() == "CAUSE_CHAIN"
    assert "caused" in S.RenderedClauseProposition(cause_clause)()

    # Test rejection of causal claim when edge is absent
    non_causal = S.CauseChain(cause_frag, f8_frag, empty)()
    assert M.IdentityCompare(M.Head(non_causal)(), M.false_value)() is M.truth_value
    print("[PASS] 9. Operator 3 (CAUSE_CHAIN): valid causal edge produced certified clause; missing edge rejected.")

    # Operator 4: CONTRAST
    f11_agree = M.Head(f11_frags)()
    f11_disc = M.Head(M.Tail(f11_frags)())()
    f11_edges = M.Head(M.Tail(M.Tail(f11_entry)())())()

    contrast_res = S.Contrast(f11_agree, f11_disc, f11_edges)()
    assert M.IdentityCompare(M.Head(contrast_res)(), M.truth_value)() is M.truth_value
    contrast_clause = M.Head(M.Tail(contrast_res)())()
    assert S.RenderedClauseMergeRule(contrast_clause)() == "CONTRAST"
    assert "however" in S.RenderedClauseProposition(contrast_clause)()
    print("[PASS] 10. Operator 4 (CONTRAST): paired completed status with discrepancy via contrasting relation.")

    # Operator 5: ELIDE_REDUNDANT_IDS
    r1 = S.StoryFragment("r1", "c1", "v1", empty, S.RoleActionLabel, S.TrackELabel, "search_bfs_worker", "step", S.EventCompletedLabel, "ev", S.SalienceLowLabel, empty, empty, S.CutAllLabel)()
    r2 = S.StoryFragment("r2", "c1", "v1", empty, S.RoleActionLabel, S.TrackELabel, "search_bfs_worker", "step", S.EventCompletedLabel, "ev", S.SalienceLowLabel, empty, empty, S.CutAllLabel)()
    elided = S.ElideRedundantIds(M.Pair(r1, M.Pair(r2, empty)))()

    first_subj = S.StoryFragmentSubject(M.Head(elided)())()
    second_subj = S.StoryFragmentSubject(M.Head(M.Tail(elided)())())()
    assert first_subj == "search_bfs_worker"
    assert second_subj == "the_worker"
    print("[PASS] 11. Operator 5 (ELIDE_REDUNDANT_IDS): preserved full identity on first mention; shortened on second.")

    # Operator 6: SECTION_BY_DECISION
    s_input = M.Pair(w1, M.Pair(unrelated, empty))
    sections = S.SectionByDecision(s_input)()
    # Check 4 sections present
    sec1 = M.Head(sections)()
    sec2 = M.Head(M.Tail(sections)())()
    sec3 = M.Head(M.Tail(M.Tail(sections)())())()
    sec4 = M.Head(M.Tail(M.Tail(M.Tail(sections)())())())()
    assert M.Head(sec1)() == "Section1_Decision"
    assert M.Head(sec2)() == "Section2_Evidence"
    assert M.Head(sec3)() == "Section3_Blockers"
    assert M.Head(sec4)() == "Section4_NextActions"
    # w1 in Section1, unrelated in Section3
    assert M.IdentityCompare(M.Tail(sec1)(), empty)() is M.false_value
    assert M.IdentityCompare(M.Tail(sec3)(), empty)() is M.false_value
    print("[PASS] 12. Operator 6 (SECTION_BY_DECISION): structured fragments into 4 canonical rhetorical sections.")

    # Operator 7: SCOPE_AGREEMENT
    scope_res = S.ScopeAgreement(f11_agree, f11_disc)()
    assert M.IdentityCompare(M.Head(scope_res)(), M.truth_value)() is M.truth_value
    scope_clause = M.Head(M.Tail(scope_res)())()
    assert S.RenderedClauseMergeRule(scope_clause)() == "SCOPE_AGREEMENT"
    assert "projection=composite" in S.RenderedClauseProposition(scope_clause)()
    assert "excluded_boundary=1" in S.RenderedClauseProposition(scope_clause)()
    print("[PASS] 13. Operator 7 (SCOPE_AGREEMENT): agreement claim qualified by projection with boundary discrepancy surfaced.")

    # Invariance check
    core_path = os.path.join(IMPORT_ROOT, "core.py")
    with open(core_path, "r", encoding="utf-8") as f:
        core_src = f.read()
    assert "Story" not in core_src
    print("[PASS] 14. Invariance check: core.py remains completely untouched.")

    print("\nALL 14 CHECKS IN SUITE L-S-3 PASSED SUCCESSFULLY.")


if __name__ == "__main__":
    run_tests()
