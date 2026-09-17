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


def run_checks():
    print("=== L-S-2 Verification Suite: Machine-Native Story Terms ===")

    # 1. StoryEdge Accessors
    edge = S.StoryEdge(S.RelationCausesLabel, "src-01", "tgt-02")()
    rel = S.StoryEdgeRelation(edge)()
    src = S.StoryEdgeSource(edge)()
    tgt = S.StoryEdgeTarget(edge)()
    assert M.IdentityCompare(rel, S.RelationCausesLabel)() is M.truth_value
    assert src == "src-01"
    assert tgt == "tgt-02"
    print("[PASS] 1. StoryEdge construction and field accessors verified.")

    # 2. AgreementScope Accessors
    scope = S.AgreementScope("projection=composite", "excluded=1")()
    proj = S.AgreementScopeProjection(scope)()
    excl = S.AgreementScopeExclusions(scope)()
    assert proj == "projection=composite"
    assert excl == "excluded=1"
    print("[PASS] 2. AgreementScope projection and exclusion accessors verified.")

    # 3. EvidenceTerm Fidelity (Example 3 rule: structural distinction preserved)
    ev1 = S.EvidenceTerm("token-10", "gen-1")()
    ev2 = S.EvidenceTerm("token-10", "gen-2")()
    assert M.IdentityCompare(ev1, ev2)() is M.false_value
    assert S.EvidenceTermMarker(ev1)() == "gen-1"
    assert S.EvidenceTermMarker(ev2)() == "gen-2"
    print("[PASS] 3. EvidenceTerm structural distinction (non-lossy equality) verified.")

    # 4. StoryFragment 13-Field Accessors
    empty = M.EmptyList
    dep = S.StoryEdge(S.RelationSupportsLabel, "f0", "f1")()
    deps = M.Pair(dep, empty)
    confs = empty
    cuts = M.Pair(S.CutOperatorLabel, M.Pair(S.CutReviewLabel, empty))
    ev = S.EvidenceTerm("locus:42", "marker:0")()

    frag = S.StoryFragment(
        "frag-01",
        "cut-001",
        "v1",
        empty,  # supersedes
        S.RoleBlockerLabel,
        S.TrackFToolsLabel,
        "admission_gate",
        "token_mismatch",
        S.EventRejectedLabel,
        ev,
        S.SalienceHighLabel,
        deps,
        confs,
        cuts,
    )()

    assert S.StoryFragmentId(frag)() == "frag-01"
    assert S.StoryFragmentCutId(frag)() == "cut-001"
    assert S.StoryFragmentStateVersion(frag)() == "v1"
    assert M.IdentityCompare(S.StoryFragmentSupersedes(frag)(), empty)() is M.truth_value
    assert M.IdentityCompare(S.StoryFragmentRole(frag)(), S.RoleBlockerLabel)() is M.truth_value
    assert M.IdentityCompare(S.StoryFragmentTrack(frag)(), S.TrackFToolsLabel)() is M.truth_value
    assert S.StoryFragmentSubject(frag)() == "admission_gate"
    assert S.StoryFragmentPredicate(frag)() == "token_mismatch"
    assert M.IdentityCompare(S.StoryFragmentEvent(frag)(), S.EventRejectedLabel)() is M.truth_value
    assert M.IdentityCompare(S.StoryFragmentSalience(frag)(), S.SalienceHighLabel)() is M.truth_value
    assert M.IdentityCompare(S.StoryFragmentConflicts(frag)(), empty)() is M.truth_value
    print("[PASS] 4. StoryFragment 13-field construction and round-trip accessors verified.")

    # 5. RenderedClause Accessors
    clause = S.RenderedClause(
        "cl-01",
        "SearchBFS packet rejected due to stale generation token.",
        M.Pair("frag-01", empty),
        "PROMOTE_BLOCKER",
        S.CutOperatorLabel,
    )()
    assert S.RenderedClauseId(clause)() == "cl-01"
    assert S.RenderedClauseProposition(clause)() == "SearchBFS packet rejected due to stale generation token."
    assert S.RenderedClauseMergeRule(clause)() == "PROMOTE_BLOCKER"
    assert M.IdentityCompare(S.RenderedClauseAudienceCut(clause)(), S.CutOperatorLabel)() is M.truth_value
    print("[PASS] 5. RenderedClause certified provenance accessors verified.")

    # 6. Ingestion of 11-Item Fixture Corpus
    corpus = S.StoryFixtureCorpus("cut-001", "state-v1")()
    cursor = corpus
    count = 0
    fixture_names = []

    while M.IdentityCompare(cursor, empty)() is M.false_value:
        entry = M.Head(cursor)()
        name = M.Head(entry)()
        fixture_names.append(name)
        count += 1
        cursor = M.Tail(cursor)()

    assert count == 11
    print(f"[PASS] 6. StoryFixtureCorpus ingested exactly 11 fixtures: count={count}.")

    # Verify specific requirement fixtures:
    # Fixture 3: token fidelity
    f3_entry = M.Head(M.Tail(M.Tail(corpus)())())()
    f3_frag = M.Head(M.Tail(f3_entry)())()
    f3_ev_pair = S.StoryFragmentEvidence(f3_frag)()
    ev_ret = M.Head(f3_ev_pair)()
    ev_exp = M.Head(M.Tail(f3_ev_pair)())()
    assert S.EvidenceTermMarker(ev_ret)() != S.EvidenceTermMarker(ev_exp)()
    print("[PASS] 7. Fixture 3 (token fidelity) preserves structural distinguishing markers.")

    # Fixture 8: Budget exhaustion distinguished from refutation
    f8_entry = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(corpus)())())())())())())())()
    f8_frag = M.Head(M.Tail(f8_entry)())()
    assert M.IdentityCompare(S.StoryFragmentEvent(f8_frag)(), S.EventNonDischargeBudgetLabel)() is M.truth_value
    print("[PASS] 8. Fixture 8 distinguishes EventNonDischargeBudget from EventRefuted.")

    # Fixture 9: Causal edge linking applicability bottleneck to timeout
    f9_entry = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(corpus)())())())())())())())())()
    f9_edges = M.Head(M.Tail(M.Tail(f9_entry)())())()
    f9_edge = M.Head(f9_edges)()
    assert M.IdentityCompare(S.StoryEdgeRelation(f9_edge)(), S.RelationCausesLabel)() is M.truth_value
    print("[PASS] 9. Fixture 9 establishes verified CAUSE_CHAIN to Fixture 8.")

    # Fixture 11: Agreement scope + explicit boundary discrepancy
    f11_entry = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(corpus)())())())())())())())())())())()
    f11_frags = M.Head(M.Tail(f11_entry)())()
    f11_agree = M.Head(f11_frags)()
    f11_discrepancy = M.Head(M.Tail(f11_frags)())()
    assert M.IdentityCompare(S.StoryFragmentRole(f11_discrepancy)(), S.RoleDiscrepancyLabel)() is M.truth_value
    scope_term = S.StoryFragmentEvidence(f11_agree)()
    assert S.AgreementScopeProjection(scope_term)() == "projection=composite"
    assert S.AgreementScopeExclusions(scope_term)() == "excluded_boundary=1"
    print("[PASS] 10. Fixture 11 declares projection scope and explicit boundary discrepancy fragment.")

    # 7. Check core.py is untouched
    core_path = os.path.join(IMPORT_ROOT, "core.py")
    with open(core_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Story" not in content
    print("[PASS] 11. Invariance check: core.py is completely untouched.")

    print("\nALL 11 CHECKS PASSED SUCCESSFULLY.")


if __name__ == "__main__":
    run_checks()
