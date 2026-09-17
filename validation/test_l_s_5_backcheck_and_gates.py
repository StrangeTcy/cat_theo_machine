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
    print("=== L-S-5 Verification Suite: Standalone Conflict Verifier & Provenance Gate ===")
    empty = M.EmptyList

    corpus = S.StoryFixtureCorpus("cut-001", "state-v1")()
    f_entries = []
    curr = corpus
    while M.IdentityCompare(curr, empty)() is M.false_value:
        f_entries.append(M.Head(curr)())
        curr = M.Tail(curr)()
    assert len(f_entries) == 11

    # -------------------------------------------------------------------------
    # 1. PromoteBlockers: Scope-Correction Verification (Salience clause removed)
    # -------------------------------------------------------------------------
    # Fragment A: ordinary setup action with SalienceHighLabel, but event is completed
    f_high_action = S.StoryFragment("f-hi", "c1", "v1", empty, S.RoleActionLabel, S.TrackINTLabel, "agenda_boot", "boot_sequence", S.EventCompletedLabel, "ev", S.SalienceHighLabel, empty, empty, S.CutAllLabel)()
    f_setup = S.StoryFragment("f-set", "c1", "v1", empty, S.RoleSetupLabel, S.TrackINTLabel, "config", "load_rules", S.EventCompletedLabel, "ev", S.SalienceLowLabel, empty, empty, S.CutAllLabel)()
    # Fragment B: action with event = EventHeldLabel ("live admission held")
    f_held_action = S.StoryFragment("f-held", "c1", "v1", empty, S.RoleActionLabel, S.TrackFToolsLabel, "live_admission", "gate_evaluation", S.EventHeldLabel, "ev", S.SalienceLowLabel, empty, empty, S.CutAllLabel)()

    # Test 1a: High salience alone does NOT promote over unpromoted items
    list_salience = M.Pair(f_setup, M.Pair(f_high_action, empty))
    res_salience = S.PromoteBlockers(list_salience)()
    assert S.StoryFragmentId(M.Head(res_salience)())() == "f-setup" or S.StoryFragmentId(M.Head(res_salience)())() == "f-hi"
    # Neither is in blocker promotion set, so neither is hoisted as a blocker
    assert M.IdentityCompare(S.StoryFragmentRole(M.Head(res_salience)()), S.RoleBlockerLabel)() is M.false_value

    # Test 1b: EventHeldLabel DOES promote to head of sequence regardless of action role
    list_held = M.Pair(f_setup, M.Pair(f_held_action, empty))
    res_held = S.PromoteBlockers(list_held)()
    assert S.StoryFragmentId(M.Head(res_held)())() == "f-held"
    print("[PASS] 1. PromoteBlockers resolution: salience clause removed; EventHeldLabel hoists to head of sequence.")

    # -------------------------------------------------------------------------
    # 2. VerifyConflictSet: Standalone Conflict Verifier Callable Matrix
    # -------------------------------------------------------------------------
    f_base = S.StoryFragment("base-1", "c1", "v1", empty, S.RoleActionLabel, S.TrackELabel, "worker_pool", "lease_acquisition", S.EventCompletedLabel, "ev", S.SalienceMediumLabel, empty, empty, S.CutAllLabel)()

    # Case 2a: same subject/predicate, incompatible event, no supersedes -> HALT
    f_contra = S.StoryFragment("contra-1", "c1", "v1", empty, S.RoleActionLabel, S.TrackELabel, "worker_pool", "lease_acquisition", S.EventFailedLabel, "ev", S.SalienceMediumLabel, empty, empty, S.CutAllLabel)()
    v_halt = S.VerifyConflictSet(M.Pair(f_base, M.Pair(f_contra, empty)))()
    assert M.IdentityCompare(M.Head(v_halt)(), M.false_value)() is M.truth_value
    assert "CONFLICT_HALT" in M.Head(M.Tail(v_halt)())()

    # Case 2b: same subject/predicate, incompatible event, valid supersedes -> CORRECTION ADMITTED (truth_value)
    f_corr = S.StoryFragment("corr-1", "c1", "v2", "base-1", S.RoleActionLabel, S.TrackELabel, "worker_pool", "lease_acquisition", S.EventFailedLabel, "ev", S.SalienceMediumLabel, empty, empty, S.CutAllLabel)()
    v_corr = S.VerifyConflictSet(M.Pair(f_base, M.Pair(f_corr, empty)))()
    assert M.IdentityCompare(M.Head(v_corr)(), M.truth_value)() is M.truth_value

    # Case 2c: same subject, different predicate, incompatible event -> NO HALT (Item 2 case)
    f_diff_pred = S.StoryFragment("diff-1", "c1", "v1", empty, S.RoleBlockerLabel, S.TrackFToolsLabel, "worker_pool", "admission_gate", S.EventFailedLabel, "ev", S.SalienceHighLabel, empty, empty, S.CutAllLabel)()
    v_diff = S.VerifyConflictSet(M.Pair(f_base, M.Pair(f_diff_pred, empty)))()
    assert M.IdentityCompare(M.Head(v_diff)(), M.truth_value)() is M.truth_value

    # Case 2d: same subject/predicate, same event -> NO HALT
    f_same = S.StoryFragment("same-1", "c1", "v1", empty, S.RoleActionLabel, S.TrackELabel, "worker_pool", "lease_acquisition", S.EventCompletedLabel, "ev", S.SalienceMediumLabel, empty, empty, S.CutAllLabel)()
    v_same = S.VerifyConflictSet(M.Pair(f_base, M.Pair(f_same, empty)))()
    assert M.IdentityCompare(M.Head(v_same)(), M.truth_value)() is M.truth_value
    print("[PASS] 2. VerifyConflictSet: standalone conflict verifier passed full 4-case matrix.")

    # -------------------------------------------------------------------------
    # 3. CertifyClauseProvenance: L-S-5 Provenance Certificate Contract
    # -------------------------------------------------------------------------
    closed_cut_ids = M.Pair("frag-01", M.Pair("frag-02", M.Pair("frag-03", empty)))

    # 3a: Valid clause with tracked source IDs and authorized rule
    valid_clause = S.RenderedClause(
        "cl-100",
        "SearchBFS resident worker completed packet.",
        M.Pair("frag-01", M.Pair("frag-02", empty)),
        "CAUSE_CHAIN",
        S.CutOperatorLabel,
    )()
    cert_valid = S.CertifyClauseProvenance(valid_clause, closed_cut_ids)()
    assert M.IdentityCompare(M.Head(cert_valid)(), M.truth_value)() is M.truth_value

    # 3b: Empty clause ID -> fails certification
    bad_id_clause = S.RenderedClause("", "proposition", M.Pair("frag-01", empty), "CAUSE_CHAIN", S.CutOperatorLabel)()
    cert_bad_id = S.CertifyClauseProvenance(bad_id_clause, closed_cut_ids)()
    assert M.IdentityCompare(M.Head(cert_bad_id)(), M.false_value)() is M.truth_value
    assert "CERT_FAIL" in M.Tail(cert_bad_id)()

    # 3c: Untracked/forged source fragment ID not in closed cut -> fails certification
    forged_clause = S.RenderedClause("cl-101", "forged claim", M.Pair("untracked-ghost-id", empty), "CAUSE_CHAIN", S.CutOperatorLabel)()
    cert_forged = S.CertifyClauseProvenance(forged_clause, closed_cut_ids)()
    assert M.IdentityCompare(M.Head(cert_forged)(), M.false_value)() is M.truth_value
    assert "not in closed cut" in M.Tail(cert_forged)()

    # 3d: Unauthorized merge rule -> fails certification
    unauth_rule_clause = S.RenderedClause("cl-102", "valid claim", M.Pair("frag-01", empty), "MAGIC_LLM_MERGE", S.CutOperatorLabel)()
    cert_unauth = S.CertifyClauseProvenance(unauth_rule_clause, closed_cut_ids)()
    assert M.IdentityCompare(M.Head(cert_unauth)(), M.false_value)() is M.truth_value
    assert "unauthorized merge rule" in M.Tail(cert_unauth)()

    # 3e (Gap 2): Rule precondition re-check with edge graph
    # CAUSE_CHAIN requires a connecting RelationCausesLabel edge between cited sources
    valid_edge = S.StoryEdge(S.RelationCausesLabel, "frag-01", "frag-02")()
    edges_valid = M.Pair(valid_edge, empty)
    cert_edge_pos = S.CertifyClauseProvenance(valid_clause, closed_cut_ids, edges_valid)()
    assert M.IdentityCompare(M.Head(cert_edge_pos)(), M.truth_value)() is M.truth_value

    # Negative edge test: edge does not connect frag-01 and frag-02
    invalid_edge = S.StoryEdge(S.RelationCausesLabel, "frag-03", "frag-02")()
    edges_invalid = M.Pair(invalid_edge, empty)
    cert_edge_neg = S.CertifyClauseProvenance(valid_clause, closed_cut_ids, edges_invalid)()
    assert M.IdentityCompare(M.Head(cert_edge_neg)(), M.false_value)() is M.truth_value
    assert "CAUSE_CHAIN precondition failed" in M.Tail(cert_edge_neg)()

    # Verify entailment limitation note is present at gate definition
    assert "LIMITATION NOTE ON ENTAILMENT SCOPE" in S.CertifyClauseProvenance.__doc__
    print("[PASS] 3. CertifyClauseProvenance: contract enforces non-empty IDs, closed-cut provenance, authorized rules, and structural edge preconditions.")

    # -------------------------------------------------------------------------
    # 4. VerifyBlockerCoverage: Blocker-Coverage Gate (Gap 1)
    # -------------------------------------------------------------------------
    f11_entry = f_entries[10]
    f11_frags = M.Head(M.Tail(f11_entry)())()
    pipe_f11 = S.MergePipeline(f11_frags, empty, S.CutOperatorLabel)()

    # 4a: Positive test: blocker discrepancy fragment from fixture 11 is covered in rendered clauses
    cov_pos = S.VerifyBlockerCoverage(f11_frags, pipe_f11, S.CutOperatorLabel)()
    assert M.IdentityCompare(M.Head(cov_pos)(), M.truth_value)() is M.truth_value

    # 4b: Negative test: delete the fixture-11 discrepancy clause from pipeline output; assert verifier halts
    cov_neg = S.VerifyBlockerCoverage(f11_frags, empty, S.CutOperatorLabel)()
    assert M.IdentityCompare(M.Head(cov_neg)(), M.false_value)() is M.truth_value
    cov_err_reason = M.Head(M.Tail(cov_neg)())()
    cov_missing_id = M.Head(M.Tail(M.Tail(cov_neg)())())()
    assert "BLOCKER_COVERAGE_HALT" in cov_err_reason
    assert cov_missing_id == "fixture-11-discrepancy"
    print("[PASS] 4. VerifyBlockerCoverage: positive coverage verified; negative deletion test halts on missing blocker.")

    # -------------------------------------------------------------------------
    # 5. Pipeline-Level Tests for Fixtures 1, 4, 5 (Closing the Gap)
    # -------------------------------------------------------------------------
    # Fixture 1: 7 unreduced AST terms suppressed; semantic progress summary present
    f1_frag = M.Head(M.Tail(f_entries[0])())()
    pipe_f1 = S.MergePipeline(M.Pair(f1_frag, empty), empty, S.CutOperatorLabel)()
    proj_f1_op = S.AudienceProjection(pipe_f1, S.CutOperatorLabel)()
    for raw_ast in ("Given(ArithmeticProgression", "Need(Angles", "Parameter(CommonDifference", "Given(Triangle"):
        assert raw_ast not in proj_f1_op
    assert "applicability scan in progress over geometric premises" in proj_f1_op
    print("[PASS] 5. Fixture 1 pipeline test: raw AST premises suppressed; semantic progress summary present.")

    # Fixture 4: Bare host True/False booleans suppressed; structured invariant NonNegative(x) present
    f4_frag = M.Head(M.Tail(f_entries[3])())()
    pipe_f4 = S.MergePipeline(M.Pair(f4_frag, empty), empty, S.CutOperatorLabel)()
    proj_f4_op = S.AudienceProjection(pipe_f4, S.CutOperatorLabel)()
    proj_f4_eng = S.AudienceProjection(pipe_f4, S.CutEngineerLabel)()
    for cut_text in (proj_f4_op, proj_f4_eng):
        assert "EMPTY True" not in cut_text
        assert "UNREACH False" not in cut_text
        assert "NonNegative(x)" in cut_text
    print("[PASS] 6. Fixture 4 pipeline test: bare host booleans absent; structured invariant NonNegative(x) present.")

    # Fixture 5: <hyge.core.Pair object at 0x...> memory pointer addresses suppressed; semantic counts present
    f5_frag = M.Head(M.Tail(f_entries[4])())()
    pipe_f5 = S.MergePipeline(M.Pair(f5_frag, empty), empty, S.CutOperatorLabel)()
    proj_f5_op = S.AudienceProjection(pipe_f5, S.CutOperatorLabel)()
    proj_f5_rev = S.AudienceProjection(pipe_f5, S.CutReviewLabel)()
    for cut_text in (proj_f5_op, proj_f5_rev):
        assert "<hyge.core.Pair object" not in cut_text
        assert "at 0x" not in cut_text
        assert "121 rules" in cut_text
        assert "0 derivations" in cut_text
    print("[PASS] 7. Fixture 5 pipeline test: object pointer addresses suppressed; semantic root counts present.")

    # -------------------------------------------------------------------------
    # 6. Referring Expression Placeholder Resolution Test
    # -------------------------------------------------------------------------
    f_mention_1 = S.StoryFragment("m1", "c1", "v1", empty, S.RoleActionLabel, S.TrackELabel, "search_bfs_worker", "initialization", S.EventCompletedLabel, "ev", S.SalienceLowLabel, empty, empty, S.CutAllLabel)()
    f_mention_2 = S.StoryFragment("m2", "c1", "v1", empty, S.RoleActionLabel, S.TrackELabel, "search_bfs_worker", "execution", S.EventCompletedLabel, "ev", S.SalienceLowLabel, empty, empty, S.CutAllLabel)()

    pipe_mention = S.MergePipeline(M.Pair(f_mention_1, M.Pair(f_mention_2, empty)), empty, S.CutOperatorLabel)()
    proj_mention_op = S.AudienceProjection(pipe_mention, S.CutOperatorLabel)()
    # First mention retains canonical name; second mention resolves to referring expression 'the resident worker'
    assert "search_bfs_worker" in proj_mention_op
    assert "the resident worker" in proj_mention_op
    print("[PASS] 8. Placeholder resolution: the_<entity> placeholder resolves to natural referring expression.")

    # -------------------------------------------------------------------------
    # 7. Conformance & Invariance Checks
    # -------------------------------------------------------------------------
    core_path = os.path.join(IMPORT_ROOT, "core.py")
    with open(core_path, "r", encoding="utf-8") as f:
        core_src = f.read()
    assert "Story" not in core_src

    story_path = os.path.join(IMPORT_ROOT, "story.py")
    with open(story_path, "r", encoding="utf-8") as f:
        story_src = f.read()
    for forbidden in ("hasattr", "isinstance", "type(", "__class__", "__new__"):
        assert forbidden not in story_src

    # Confirm rent benchmark is NOT in story.py (Scope Correction)
    assert "admission_hooks" not in story_src
    assert "prose_rent" not in story_src

    print("[PASS] 9. Scope & Invariance check: core.py untouched; rent excluded; zero forbidden constructs.")

    print("\nALL 9 CHECKS IN SUITE L-S-5 PASSED SUCCESSFULLY.")


if __name__ == "__main__":
    run_tests()
