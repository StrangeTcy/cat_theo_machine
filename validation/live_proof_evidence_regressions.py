"""Live proof explanations come from retained scope and recorded evidence."""

import os
import tempfile

from hyge import checker_b as CB
from hyge import discovered_laws as DL
from hyge import labels as L
from hyge import live_proof as LP
from hyge import machine as M
from hyge import persistence
from hyge import playground as PG
from hyge import runtime
from hyge import search as S


class CheckScopedProofEvidence(M.Edge):
    def __init__(self, graph, request):
        outcome = LP.RetryLiveProofRequest(graph, request)()
        registry = M.FromContextGetConstructors(graph)()
        assert LP.LiveProofOutcomeStatus(outcome)() is L.PendingLabel
        assert LP.LiveProofOutcomeSearchJob(outcome)() is M.EmptyList
        assert LP.LiveProofOutcomeReceipt(outcome)() is M.EmptyList
        assert LP.LiveProofOutcomeVerification(outcome)() is M.EmptyList
        spec = LP.LiveProofRequestSpec(request)()
        admission = LP.LiveProofOutcomeReason(outcome)()
        assert PG.ExactArity(admission, M.four, registry)() is M.truth_value
        assert M.Compare(M.Head(admission)(), M.Char("live-equality-scope-admission-v1"))() is M.truth_value
        expected = M.Pair(M.false_value, M.Pair(M.EmptyList, M.Pair(M.EmptyList,
            M.Pair(M.false_value, M.EmptyList))))
        recorded_expected = M.Head(M.Tail(admission)())()
        recorded_actual = M.Head(M.Tail(M.Tail(admission)())())()
        recorded_verdict = M.Head(M.Tail(M.Tail(M.Tail(admission)())())())()
        actual = M.Pair(PG.GoalSpecNoSolutions(spec)(), M.Pair(PG.GoalSpecExpVars(spec)(),
            M.Pair(PG.GoalSpecParamConstraints(spec)(), M.Pair(PG.GoalSpecPositiveOnly(spec)(), M.EmptyList))))
        assert M.Compare(recorded_expected, expected)() is M.truth_value
        assert M.Compare(recorded_actual, actual)() is M.truth_value
        assert recorded_verdict is M.false_value
        assert M.Compare(admission, LP.LiveEqualityScopeAdmission(spec)())() is M.truth_value
        evidence = LP.FormatLiveProofEvidence(outcome, registry)()
        assert M.Compare(M.Char(evidence.replace("Search job: none recorded.", "")), M.Char(evidence))() is M.false_value
        assert M.Compare(M.Char(evidence.replace("Proof receipt: none recorded.", "")), M.Char(evidence))() is M.false_value
        assert M.Compare(M.Char(evidence.replace("Checker result: none recorded.", "")), M.Char(evidence))() is M.false_value
        rendered = LP.FormatLiveProofOutcome(outcome, registry)()
        assert M.Compare(M.Char(rendered.replace("descent", "")), M.Char(rendered))() is M.truth_value
        assert M.Compare(M.Char(rendered.replace("Required proof:", "")), M.Char(rendered))() is M.truth_value
        super().__init__(inputs=M.Pair(request, registry), results=outcome)


if __name__ == "__main__":
    rt = runtime.make_fresh_runtime()
    arbitrary_text = M.Char("there are no solutions x+2=y+3")
    arbitrary = LP.RecordLiveProofRequest(rt.graph, arbitrary_text)()
    arbitrary_outcome = CheckScopedProofEvidence(rt.graph, arbitrary)()
    flt_text = M.Char("prove that for n>2 there are no positive integers x,y,z with x^n+y^n=z^n")
    flt = LP.RecordLiveProofRequest(rt.graph, flt_text)()
    flt_outcome = CheckScopedProofEvidence(rt.graph, flt)()
    spec = LP.LiveProofRequestSpec(flt)()
    assert PG.GoalSpecNoSolutions(spec)() is M.truth_value
    assert PG.GoalSpecPositiveOnly(spec)() is M.truth_value
    assert M.IsPair(PG.GoalSpecExpVars(spec)())() is M.truth_value
    assert M.IsPair(PG.GoalSpecParamConstraints(spec)())() is M.truth_value
    assert M.Compare(LP.LiveProofRequestText(flt)(), flt_text)() is M.truth_value
    print("PASS arbitrary exclusion claims and the full exponent-family request retain scope and report absent search, receipt, and checker evidence")

    request = LP.RecordLiveProofRequest(rt.graph, M.Char("prove x+y=y+x"))()
    no_rules = LP.RetryLiveProofRequest(rt.graph, request)()
    assert LP.LiveProofOutcomeStatus(no_rules)() is L.PendingLabel
    assert LP.LiveProofOutcomeSearchJob(no_rules)() is M.EmptyList
    blank = LP.RecordLiveProofRequest(rt.graph, M.Char(""))()
    blank_outcome = LP.RetryLiveProofRequest(rt.graph, blank)()
    zero_outcome = LP.RetryLiveProofRequest(rt.graph, request, M.Zero)()
    assert LP.LiveProofOutcomeStatus(blank_outcome)() is L.PendingLabel
    assert LP.LiveProofOutcomeStatus(zero_outcome)() is L.PendingLabel
    assert LP.LiveProofOutcomeSearchJob(blank_outcome)() is M.EmptyList
    assert LP.LiveProofOutcomeSearchJob(zero_outcome)() is M.EmptyList
    registry = M.FromContextGetConstructors(rt.graph)()
    base_spec = LP.LiveProofRequestSpec(request)()
    broken_scope = M.Pair(PG.GoalSpecLhs(base_spec)(), M.Pair(PG.GoalSpecRhs(base_spec)(),
        M.Pair(PG.GoalSpecBaseVars(base_spec)(), M.Pair(M.EmptyList, M.Pair(M.EmptyList,
            M.Pair(M.EmptyList, M.Pair(M.false_value, M.Pair(registry, M.EmptyList))))))))
    malformed = LP.RecordLiveProofRequest(rt.graph, LP.LiveProofRequestText(request)(), broken_scope)()
    CheckScopedProofEvidence(rt.graph, malformed)()
    broken_positive = M.Pair(PG.GoalSpecLhs(base_spec)(), M.Pair(PG.GoalSpecRhs(base_spec)(),
        M.Pair(PG.GoalSpecBaseVars(base_spec)(), M.Pair(M.EmptyList, M.Pair(M.EmptyList,
            M.Pair(M.false_value, M.Pair(M.Zero, M.Pair(registry, M.EmptyList))))))))
    malformed = LP.RecordLiveProofRequest(rt.graph, LP.LiveProofRequestText(request)(), broken_positive)()
    CheckScopedProofEvidence(rt.graph, malformed)()
    print("PASS blank requests, zero search budgets, and malformed scope flags remain pending without starting search")

    x = M.Char("x")
    y = M.Char("y")
    variables = M.Pair(x, M.Pair(y, M.EmptyList))
    lhs = M.Pair(L.ExprAddLabel, M.Pair(x, M.Pair(y, M.EmptyList)))
    rhs = M.Pair(L.ExprAddLabel, M.Pair(y, M.Pair(x, M.EmptyList)))
    equation = M.Pair(L.DiscoveredEquationLabel, M.Pair(variables, M.Pair(lhs, M.Pair(rhs, M.EmptyList))))
    named = M.Pair(L.NamedRegularityLabel, M.Pair(M.Char("addition commutes for evidence checks"),
        M.Pair(M.Char("add"), M.Pair(equation, M.Pair(M.Pair(M.one, M.EmptyList), M.Pair(M.EmptyList, M.EmptyList))))))
    recorded = DL.RecordNamedDiscoveredLaw(rt, named, M.Pair(L.PolynomialGridRuleLabel, M.EmptyList))()
    rule = M.Head(recorded)()
    assert rule is not M.EmptyList
    proved = LP.RetryLiveProofRequest(rt.graph, request)()
    registry = M.FromContextGetConstructors(rt.graph)()
    assert LP.LiveProofOutcomeStatus(proved)() is L.ProvedLabel
    receipt = LP.LiveProofOutcomeReceipt(proved)()
    assert M.IsPair(receipt)() is M.truth_value
    assert M.Head(LP.LiveProofOutcomeVerification(proved)())() is L.DerivationVerifiedLabel
    checked = CB.VerifyDerivation(LP.LiveProofRecordField(receipt, M.four)(),
        PG.GoalSpecLhs(base_spec)(), PG.GoalSpecRhs(base_spec)(), M.Pair(rule, M.EmptyList), registry)()
    assert M.Head(checked)() is L.DerivationVerifiedLabel
    evidence = LP.FormatLiveProofEvidence(proved, registry)()
    assert M.Compare(M.Char(evidence.replace("Proof receipt: recorded.", "")), M.Char(evidence))() is M.false_value
    assert M.Compare(M.Char(evidence.replace("Checker result: verified.", "")), M.Char(evidence))() is M.false_value
    scoped_same = LP.RecordLiveProofRequest(rt.graph, M.Char("there are no solutions x+y=y+x"))()
    CheckScopedProofEvidence(rt.graph, scoped_same)()
    CheckScopedProofEvidence(rt.graph, flt)()
    print("PASS a learned addition law proves its bare equality with checked evidence and cannot prove the exclusion claim containing that equality")

    unfinished_request = LP.RecordLiveProofRequest(rt.graph, M.Char("x+y=x*y"))()
    bounded = LP.RetryLiveProofRequest(rt.graph, unfinished_request, M.one)()
    registry = M.FromContextGetConstructors(rt.graph)()
    assert LP.LiveProofOutcomeStatus(bounded)() is L.PendingLabel
    job = LP.LiveProofOutcomeSearchJob(bounded)()
    assert M.IsPair(job)() is M.truth_value
    assert M.NatEq(S.SearchJobExpanded(job)(), M.one, registry)() is M.truth_value
    evidence = LP.FormatLiveProofEvidence(bounded, registry)()
    assert M.Compare(M.Char(evidence.replace("Search job: none recorded.", "")), M.Char(evidence))() is M.truth_value
    assert M.Compare(M.Char(evidence.replace("expanded", "")), M.Char(evidence))() is M.false_value
    assert M.Compare(M.Char(evidence.replace("generated", "")), M.Char(evidence))() is M.false_value
    assert M.Compare(M.Char(evidence), M.Char(LP.FormatLiveProofEvidence(no_rules, registry)()))() is M.false_value
    assert LP.LiveProofOutcomeReceipt(bounded)() is M.EmptyList
    assert LP.LiveProofOutcomeVerification(bounded)() is M.EmptyList
    print("PASS a recorded bounded search renders its counters instead of claiming that no search ran")

    legacy_advice = M.Char("Legacy advice: use the imaginary spiral proof technique.")
    legacy = M.Pair(M.Char("live-proof-outcome-v1"), M.Pair(flt, M.Pair(L.PendingLabel,
        M.Pair(legacy_advice, M.Pair(M.EmptyList, M.Pair(M.EmptyList,
            M.Pair(registry, M.Pair(M.EmptyList, M.EmptyList))))))))
    rendered = LP.FormatLiveProofOutcome(legacy, registry)()
    assert M.Compare(M.Char(rendered.replace(legacy_advice(), "")), M.Char(rendered))() is M.truth_value
    assert M.Compare(M.Char(rendered.replace("Search job: none recorded.", "")), M.Char(rendered))() is M.false_value
    rt.graph.add_node(legacy)
    restored_target = LP.RecordLiveProofRequest(rt.graph, flt_text)()
    structured_outcome = CheckScopedProofEvidence(rt.graph, restored_target)()
    registry = M.FromContextGetConstructors(rt.graph)()
    expected_output = LP.FormatLiveProofOutcome(structured_outcome, registry)()
    snapshot_scope = M.Pair(M.Char("live-evidence-snapshot-check"), M.Pair(legacy,
        M.Pair(structured_outcome, M.EmptyList)))
    rt.graph.add_node(snapshot_scope)
    codec = persistence.SnapshotCodec(persistence._runtime_namespace_for_restore())
    with tempfile.TemporaryDirectory(prefix="hyge-live-evidence-") as snapshot_directory:
        snapshot_path = os.path.join(snapshot_directory, "recorded-evidence.json")
        codec.save(rt.graph, snapshot_path)
        restored = codec.load(snapshot_path)
        resumed = runtime.make_fresh_runtime()
        codec.activate(restored, resumed.graph)
    restored_scope = M.Head(M.FromContextGetNodes(resumed.graph)())()
    restored_legacy = M.Head(M.Tail(restored_scope)())()
    restored_outcome = M.Head(M.Tail(M.Tail(restored_scope)())())()
    restored_registry = M.FromContextGetConstructors(resumed.graph)()
    assert M.IsPair(LP.LiveProofOutcomeReason(restored_outcome)())() is M.truth_value
    assert M.Compare(M.Char(LP.FormatLiveProofOutcome(restored_outcome, restored_registry)()),
        M.Char(expected_output))() is M.truth_value
    restored_legacy_output = LP.FormatLiveProofOutcome(restored_legacy, restored_registry)()
    assert M.Compare(M.Char(restored_legacy_output.replace(legacy_advice(), "")), M.Char(restored_legacy_output))() is M.truth_value
    assert M.Compare(M.Char(restored_legacy_output.replace("Checker result: none recorded.", "")),
        M.Char(restored_legacy_output))() is M.false_value
    print("PASS legacy canned advice is not rendered; structured scope admissions and factual evidence survive file-backed restoration")
    print("Live proof evidence regressions passed.")
