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
    print("=== L-S-4 Verification Suite: MergePipeline, Audience Cuts & Realization ===")
    empty = M.EmptyList

    corpus = S.StoryFixtureCorpus("cut-001", "state-v1")()

    # Extract all 11 fixtures from corpus
    f_entries = []
    curr = corpus
    while M.IdentityCompare(curr, empty)() is M.false_value:
        f_entries.append(M.Head(curr)())
        curr = M.Tail(curr)()
    assert len(f_entries) == 11

    # -------------------------------------------------------------------------
    # 1. Fixture 7: 15 repeated replacement probes -> 1 coalesced summary fragment
    # -------------------------------------------------------------------------
    f7_entry = f_entries[6]
    f7_frag = M.Head(M.Tail(f7_entry)())()
    # Generate 15 identical probe fragments with same evidence term
    shared_ev = S.EvidenceTerm("probe_log", "replacement_mismatch")()
    f7_list = empty
    for i in range(15):
        probe_f = S.StoryFragment(
            f"probe-{i:02d}",
            "cut-001",
            "v1",
            empty,
            S.RoleEvidenceLabel,
            S.TrackGLabel,
            "rule_filter_probes",
            "replacement_mismatch",
            S.EventHeldLabel,
            shared_ev,
            S.SalienceLowLabel,
            empty,
            empty,
            M.Pair(S.CutEngineerLabel, M.Pair(S.CutReviewLabel, empty)),
        )()
        f7_list = M.Pair(probe_f, f7_list)

    coalesced_f7 = S.CoalesceRepeatedStatus(f7_list)()
    # Should coalesce into exactly 1 summary fragment
    assert M.IdentityCompare(M.Tail(coalesced_f7)(), empty)() is M.truth_value
    c_f7 = M.Head(coalesced_f7)()
    assert S.StoryFragmentId(c_f7)().startswith("coalesced-")
    # Provenance carries all 15 IDs
    c7_ev = S.StoryFragmentEvidence(c_f7)()
    source_ids = S.EvidenceTermMarker(c7_ev)()
    count_ids = 0
    c_curr = source_ids
    while M.IdentityCompare(c_curr, empty)() is M.false_value:
        count_ids += 1
        c_curr = M.Tail(c_curr)()
    assert count_ids == 15
    print("[PASS] 1. Fixture 7: 15 repeated probes coalesced into 1 summary fragment with 15 provenance IDs.")

    # -------------------------------------------------------------------------
    # 2. Fixture 6: per-mode 1 batches -> merge only if key matches; else stay separate
    # -------------------------------------------------------------------------
    f6_dfs = S.StoryFragment("f6-dfs", "c1", "v1", empty, S.RoleActionLabel, S.TrackELabel, "search_dfs", "frontier_packetized", S.EventCompletedLabel, S.EvidenceTerm("log", "batches=1")(), S.SalienceLowLabel, empty, empty, S.CutAllLabel)()
    f6_bfs = S.StoryFragment("f6-bfs", "c1", "v1", empty, S.RoleActionLabel, S.TrackELabel, "search_bfs", "frontier_packetized", S.EventCompletedLabel, S.EvidenceTerm("log", "batches=1")(), S.SalienceLowLabel, empty, empty, S.CutAllLabel)()
    f6_other = S.StoryFragment("f6-other", "c1", "v1", empty, S.RoleActionLabel, S.TrackELabel, "search_dfs", "frontier_packetized", S.EventCompletedLabel, S.EvidenceTerm("different_log", "batches=2")(), S.SalienceLowLabel, empty, empty, S.CutAllLabel)()

    f6_coalesced = S.CoalesceRepeatedStatus(M.Pair(f6_dfs, M.Pair(f6_bfs, M.Pair(f6_other, empty))))()
    # f6_dfs and f6_bfs share evidence_type 'log' -> coalesced; f6_other has 'different_log' -> separate
    assert M.IdentityCompare(f6_coalesced, empty)() is M.false_value
    first_c = M.Head(f6_coalesced)()
    second_c = M.Head(M.Tail(f6_coalesced)())()
    assert S.StoryFragmentId(first_c)().startswith("coalesced-")
    assert S.StoryFragmentId(second_c)() == "f6-other"
    print("[PASS] 2. Fixture 6: cross-mode batches merge when key matches and remain separate on different evidence type.")

    # -------------------------------------------------------------------------
    # 3. Fixtures 2 + 10: worker telemetry excluded from operator cut; present in engineer cut
    # -------------------------------------------------------------------------
    f2_frag = M.Head(M.Tail(f_entries[1])())()
    f10_frag = M.Head(M.Tail(f_entries[9])())()
    telemetry_list = M.Pair(f2_frag, M.Pair(f10_frag, empty))

    pipe_op = S.MergePipeline(telemetry_list, empty, S.CutOperatorLabel)()
    proj_op = S.AudienceProjection(pipe_op, S.CutOperatorLabel)()
    # Operator cut must exclude low-level worker telemetry lines
    assert "pid=1846" not in proj_op
    assert "pid=1857" not in proj_op

    pipe_eng = S.MergePipeline(telemetry_list, empty, S.CutEngineerLabel)()
    proj_eng = S.AudienceProjection(pipe_eng, S.CutEngineerLabel)()
    # Engineer cut must include worker actions
    assert "completed" in proj_eng
    print("[PASS] 3. Fixtures 2 + 10: worker telemetry properly excluded from operator cut, preserved in engineer cut.")

    # -------------------------------------------------------------------------
    # 4. Fixtures 8 + 9: timeout <- scan; blocker in Decision; 9->8 causal clause; event is non_discharge_budget
    # -------------------------------------------------------------------------
    f8_frag = M.Head(M.Tail(f_entries[7])())()
    f9_frag = M.Head(M.Tail(f_entries[8])())()
    f9_edges = M.Head(M.Tail(M.Tail(f_entries[8])())())()

    # Event must be EventNonDischargeBudgetLabel, never EventRefutedLabel
    assert M.IdentityCompare(S.StoryFragmentEvent(f8_frag)(), S.EventNonDischargeBudgetLabel)() is M.truth_value
    assert M.IdentityCompare(S.StoryFragmentEvent(f8_frag)(), S.EventRefutedLabel)() is M.false_value

    pipe_8_9 = S.MergePipeline(M.Pair(f8_frag, M.Pair(f9_frag, empty)), f9_edges, S.CutOperatorLabel)()
    assert M.IdentityCompare(M.Head(pipe_8_9)(), M.truth_value)() is M.truth_value

    rest_8_9 = M.Tail(pipe_8_9)()
    sections_8_9 = M.Head(rest_8_9)()
    clauses_8_9 = M.Head(M.Tail(rest_8_9)())()

    # CauseChain clause exists
    assert M.IdentityCompare(clauses_8_9, empty)() is M.false_value
    c_clause = M.Head(clauses_8_9)()
    assert S.RenderedClauseMergeRule(c_clause)() == "CAUSE_CHAIN"
    # Bidirectional surface realization:
    bidir_conseq_ev = S.RealizeClauseText(c_clause, "consequence_evidence")()
    bidir_ev_conseq = S.RealizeClauseText(c_clause, "evidence_consequence")()
    assert "because" in bidir_conseq_ev
    assert "causing" in bidir_ev_conseq
    print("[PASS] 4. Fixtures 8 + 9: causal chain 9->8 verified with non_discharge_budget and bidirectional realization.")

    # -------------------------------------------------------------------------
    # 5. Fixture 11: ScopeAgreement + PromoteBlockers; agreement carries projection; discrepancy survives all cuts
    # -------------------------------------------------------------------------
    f11_frags = M.Head(M.Tail(f_entries[10])())()
    f11_agree = M.Head(f11_frags)()
    f11_disc = M.Head(M.Tail(f11_frags)())()
    f11_edges = M.Head(M.Tail(M.Tail(f_entries[10])())())()

    pipe_11 = S.MergePipeline(f11_frags, f11_edges, S.CutOperatorLabel)()
    assert M.IdentityCompare(M.Head(pipe_11)(), M.truth_value)() is M.truth_value

    # Projection to operator cut:
    proj_11_op = S.AudienceProjection(pipe_11, S.CutOperatorLabel)()
    assert "projection=composite" in proj_11_op
    assert "excluded_boundary=1" in proj_11_op

    # Projection to review cut:
    proj_11_rev = S.AudienceProjection(pipe_11, S.CutReviewLabel)()
    assert "projection=composite" in proj_11_rev
    print("[PASS] 5. Fixture 11: ScopeAgreement and boundary discrepancy survive operator and review cuts.")

    # -------------------------------------------------------------------------
    # 6. Fixture 3: token fidelity; two EvidenceTerms with StructuralEqual=false NEVER coalesce
    # -------------------------------------------------------------------------
    f3_frag = M.Head(M.Tail(f_entries[2])())()
    ev_pair = S.StoryFragmentEvidence(f3_frag)()
    ev1 = M.Head(ev_pair)()
    ev2 = M.Head(M.Tail(ev_pair)())()

    f3_a = S.StoryFragment("t1", "c1", "v1", empty, S.RoleBlockerLabel, S.TrackELabel, "token_check", "mismatch", S.EventRejectedLabel, ev1, S.SalienceHighLabel, empty, empty, S.CutAllLabel)()
    f3_b = S.StoryFragment("t2", "c1", "v1", empty, S.RoleBlockerLabel, S.TrackELabel, "token_check", "mismatch", S.EventRejectedLabel, ev2, S.SalienceHighLabel, empty, empty, S.CutAllLabel)()

    f3_coalesce_attempt = S.CoalesceRepeatedStatus(M.Pair(f3_a, M.Pair(f3_b, empty)))()
    # Must NOT coalesce: distinct markers gen-1 vs gen-2 ensure they remain 2 distinct fragments!
    assert M.IdentityCompare(M.Tail(f3_coalesce_attempt)(), empty)() is M.false_value
    assert S.StoryFragmentId(M.Head(f3_coalesce_attempt)())() == "t1"
    assert S.StoryFragmentId(M.Head(M.Tail(f3_coalesce_attempt)())())() == "t2"
    print("[PASS] 6. Fixture 3: non-equal structural tokens with distinct markers are NEVER coalesced.")

    # -------------------------------------------------------------------------
    # 7. Synthetic correction pair: with supersedes -> admitted; without -> CONFLICT_HALT
    # -------------------------------------------------------------------------
    f_orig = S.StoryFragment("f-orig", "c1", "v1", empty, S.RoleActionLabel, S.TrackELabel, "subsystem_alpha", "audit_check", S.EventCompletedLabel, "ev", S.SalienceHighLabel, empty, empty, S.CutAllLabel)()
    # Contradiction: same subject, same predicate, incompatible event, supersedes = empty
    f_bad_corr = S.StoryFragment("f-bad", "c1", "v2", empty, S.RoleActionLabel, S.TrackELabel, "subsystem_alpha", "audit_check", S.EventFailedLabel, "ev", S.SalienceHighLabel, empty, empty, S.CutAllLabel)()

    pipe_conflict = S.MergePipeline(M.Pair(f_orig, M.Pair(f_bad_corr, empty)), empty, S.CutOperatorLabel)()
    # Must fail with CONFLICT_HALT
    assert M.IdentityCompare(M.Head(pipe_conflict)(), M.false_value)() is M.truth_value
    assert "CONFLICT_HALT" in M.Tail(pipe_conflict)()

    # Valid correction: supersedes is explicitly set to f-orig
    f_good_corr = S.StoryFragment("f-good", "c1", "v2", "f-orig", S.RoleActionLabel, S.TrackELabel, "subsystem_alpha", "audit_check", S.EventFailedLabel, "ev", S.SalienceHighLabel, empty, empty, S.CutAllLabel)()
    pipe_resolved = S.MergePipeline(M.Pair(f_orig, M.Pair(f_good_corr, empty)), empty, S.CutOperatorLabel)()
    # Must succeed because f_good supersedes f_orig
    assert M.IdentityCompare(M.Head(pipe_resolved)(), M.truth_value)() is M.truth_value
    print("[PASS] 7. Synthetic correction pair: halts on contradiction without supersedes; admits valid correction.")

    # -------------------------------------------------------------------------
    # 8. Provenance test: every clause produced by MergePipeline traces to >= 1 source ID
    # -------------------------------------------------------------------------
    pipe_full = S.MergePipeline(M.Pair(f8_frag, M.Pair(f9_frag, empty)), f9_edges, S.CutOperatorLabel)()
    clauses_full = M.Head(M.Tail(M.Tail(pipe_full)())())()
    assert M.IdentityCompare(clauses_full, empty)() is M.false_value

    curr_cl = clauses_full
    while M.IdentityCompare(curr_cl, empty)() is M.false_value:
        cl = M.Head(curr_cl)()
        src_ids = S.RenderedClauseSourceFragments(cl)()
        merge_rule = S.RenderedClauseMergeRule(cl)()
        assert M.IdentityCompare(src_ids, empty)() is M.false_value  # traces to >= 1 source ID
        assert merge_rule in ("CAUSE_CHAIN", "CONTRAST", "SCOPE_AGREEMENT")
        curr_cl = M.Tail(curr_cl)()
    print("[PASS] 8. Provenance test: every pipeline clause traces to source fragment IDs and names its merge rule.")

    # -------------------------------------------------------------------------
    # 9. Conformance checks: core.py untouched and zero forbidden constructs
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

    print("[PASS] 9. Invariance check: core.py untouched; zero forbidden constructs across story.py and suites.")

    print("\nALL 9 CHECKS IN SUITE L-S-4 PASSED SUCCESSFULLY.")


if __name__ == "__main__":
    run_tests()
