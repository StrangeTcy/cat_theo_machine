"""Live requests retain scope and close only with replayed active-rule proofs."""

import os
import tempfile

from hyge import checker_b as CB
from hyge import discovered_laws as DL
from hyge import labels as L
from hyge import live_proof as LP
from hyge import machine as M
from hyge import main as Main
from hyge import persistence
from hyge import playground as PG
from hyge import proof as P
from hyge import runtime
from hyge import search as S


if __name__ == "__main__":
    rt = runtime.make_fresh_runtime()
    request = LP.RecordLiveProofRequest(rt.graph, M.Char("prove x+y=y+x"))()
    result = LP.RetryLiveProofRequest(rt.graph, request)()
    assert LP.LiveProofOutcomeStatus(result)() is L.PendingLabel
    assert LP.LiveProofOutcomeReceipt(result)() is M.EmptyList
    assert M.Compare(LP.LiveProofRequestText(request)(), M.Char("prove x+y=y+x"))() is M.truth_value
    print("PASS a live equality stays pending without an active law")

    reg = M.FromContextGetConstructors(rt.graph)()
    authority = M.Pair(L.PolynomialGridRuleLabel, M.EmptyList)
    x = M.Char("x")
    y = M.Char("y")
    variables = M.Pair(x, M.Pair(y, M.EmptyList))
    lhs = M.Pair(L.ExprAddLabel, M.Pair(x, M.Pair(y, M.EmptyList)))
    rhs = M.Pair(L.ExprAddLabel, M.Pair(y, M.Pair(x, M.EmptyList)))
    equation = M.Pair(
        L.DiscoveredEquationLabel,
        M.Pair(variables, M.Pair(lhs, M.Pair(rhs, M.EmptyList))),
    )
    named = M.Pair(
        L.NamedRegularityLabel,
        M.Pair(
            M.Char("addition commutes"),
            M.Pair(
                M.Char("add"),
                M.Pair(equation, M.Pair(M.Pair(M.one, M.EmptyList), M.Pair(M.EmptyList, M.EmptyList))),
            ),
        ),
    )
    recorded = DL.RecordNamedDiscoveredLaw(rt, named, authority)()
    rule = M.Head(recorded)()
    assert M.IdentityCompare(rule, M.EmptyList)() is M.false_value
    result = LP.RetryLiveProofRequest(rt.graph, request)()
    assert LP.LiveProofOutcomeStatus(result)() is L.ProvedLabel
    receipt = LP.LiveProofOutcomeReceipt(result)()
    assert M.IdentityCompare(M.Head(receipt)(), L.ProofReceiptLabel)() is M.truth_value
    assert M.Compare(LP.LiveProofRecordField(receipt, M.one)(), LP.LiveProofRequestText(request)())() is M.truth_value
    derivation = LP.LiveProofRecordField(receipt, M.four)()
    reg = M.FromContextGetConstructors(rt.graph)()
    spec = LP.LiveProofRequestSpec(request)()
    checked = CB.VerifyDerivation(
        derivation, PG.GoalSpecLhs(spec)(), PG.GoalSpecRhs(spec)(), M.Pair(rule, M.EmptyList), reg
    )()
    assert M.Head(checked)() is L.DerivationVerifiedLabel
    assert P.ContainsVar(P.DerivationEnd(derivation, reg)())() is M.false_value
    assert M.Compare(LP.LatestLiveProofRequest(M.FromContextGetNodes(rt.graph)())(), request)() is M.truth_value
    assert M.Compare(LP.LatestLiveProofOutcome(M.FromContextGetNodes(rt.graph)(), request)(), result)() is M.truth_value
    print("PASS the same request closes after learning a law and Checker B independently replays its receipt")
    print(LP.FormatLiveProofOutcome(result, reg)())

    nested = LP.RecordLiveProofRequest(rt.graph, M.Char("(x+y)*2=(y+x)*2"))()
    result = LP.RetryLiveProofRequest(rt.graph, nested, M.eight)()
    assert LP.LiveProofOutcomeStatus(result)() is L.ProvedLabel
    receipt = LP.LiveProofOutcomeReceipt(result)()
    derivation = LP.LiveProofRecordField(receipt, M.four)()
    reg = M.FromContextGetConstructors(rt.graph)()
    steps = P.DerivationSteps(derivation, reg)()
    first_action = P.StepAction(M.Head(steps)(), reg)()
    assert M.IdentityCompare(P.ActionPath(first_action)(), M.EmptyList)() is M.false_value
    print("PASS an active learned law rewrites a nested subterm with a checked path")

    expanded = M.Pair(L.ExprAddLabel, M.Pair(x, M.Pair(x, M.EmptyList)))
    doubled = M.Pair(L.ExprMulLabel, M.Pair(M.two, M.Pair(x, M.EmptyList)))
    doubling_equation = M.Pair(
        L.DiscoveredEquationLabel,
        M.Pair(M.Pair(x, M.EmptyList), M.Pair(expanded, M.Pair(doubled, M.EmptyList))),
    )
    doubling_named = M.Pair(
        L.NamedRegularityLabel,
        M.Pair(
            M.Char("double a sum"),
            M.Pair(
                M.Char("add"),
                M.Pair(doubling_equation, M.Pair(M.Pair(M.one, M.EmptyList), M.Pair(M.EmptyList, M.EmptyList))),
            ),
        ),
    )
    recorded = DL.RecordNamedDiscoveredLaw(rt, doubling_named, authority)()
    assert M.IdentityCompare(M.Head(recorded)(), M.EmptyList)() is M.false_value
    multiple = LP.RecordLiveProofRequest(rt.graph, M.Char("(x+x)+y=y+2*x"))()
    limited = LP.RetryLiveProofRequest(rt.graph, multiple, M.one)()
    assert LP.LiveProofOutcomeStatus(limited)() is L.PendingLabel
    assert LP.LiveProofOutcomeReceipt(limited)() is M.EmptyList
    assert M.NatEq(
        S.SearchJobExpanded(LP.LiveProofOutcomeSearchJob(limited)())(), M.one,
        M.FromContextGetConstructors(rt.graph)(),
    )() is M.truth_value
    result = LP.RetryLiveProofRequest(rt.graph, multiple, M.eight)()
    assert LP.LiveProofOutcomeStatus(result)() is L.ProvedLabel
    receipt = LP.LiveProofOutcomeReceipt(result)()
    derivation = LP.LiveProofRecordField(receipt, M.four)()
    reg = M.FromContextGetConstructors(rt.graph)()
    steps = P.DerivationSteps(derivation, reg)()
    assert M.IsPair(M.Tail(steps)())() is M.truth_value
    checked = CB.VerifyDerivation(
        derivation, LP.LiveProofRecordField(receipt, M.two)(), LP.LiveProofRecordField(receipt, M.three)(),
        PG.ChainReverse(M.FromContextGetRuleOrder(rt.graph)())(), reg,
    )()
    assert M.Head(checked)() is L.DerivationVerifiedLabel
    print("PASS a multistep proof combines learned laws and remains independently replayable")

    flt_text = M.Char("prove that for n>2 there are no positive integers x,y,z with x^n+y^n=z^n")
    flt = LP.RecordLiveProofRequest(rt.graph, flt_text)()
    result = LP.RetryLiveProofRequest(rt.graph, flt)()
    assert LP.LiveProofOutcomeStatus(result)() is L.PendingLabel
    assert LP.LiveProofOutcomeReceipt(result)() is M.EmptyList
    spec = LP.LiveProofRequestSpec(flt)()
    assert PG.GoalSpecNoSolutions(spec)() is M.truth_value
    assert PG.GoalSpecPositiveOnly(spec)() is M.truth_value
    assert M.IsPair(PG.GoalSpecExpVars(spec)())() is M.truth_value
    assert M.IsPair(PG.GoalSpecParamConstraints(spec)())() is M.truth_value
    assert M.Compare(LP.LiveProofRequestText(flt)(), flt_text)() is M.truth_value
    print("PASS FLT retains no-solutions, positivity, exponent family, constraints, and original text")

    no_solutions = LP.RecordLiveProofRequest(rt.graph, M.Char("there are no solutions x=x"))()
    positive = LP.RecordLiveProofRequest(rt.graph, M.Char("prove x=x for positive x"))()
    constrained = LP.RecordLiveProofRequest(rt.graph, M.Char("for x>2 prove x=x"))()
    family = LP.RecordLiveProofRequest(rt.graph, M.Char("x^n=x^n"))()
    suffix = LP.RecordLiveProofRequest(rt.graph, M.Char("x=x assuming x is prime"))()
    comma = LP.RecordLiveProofRequest(rt.graph, M.Char("x=x, y=0"))()
    malformed = LP.RecordLiveProofRequest(rt.graph, M.Char("x=x+"))()
    unparsed = LP.RecordLiveProofRequest(rt.graph, M.Char("prove Fermat's Last Theorem"))()
    assert LP.LiveProofOutcomeStatus(LP.RetryLiveProofRequest(rt.graph, no_solutions)())() is L.PendingLabel
    assert LP.LiveProofOutcomeStatus(LP.RetryLiveProofRequest(rt.graph, positive)())() is L.PendingLabel
    assert LP.LiveProofOutcomeStatus(LP.RetryLiveProofRequest(rt.graph, constrained)())() is L.PendingLabel
    assert LP.LiveProofOutcomeStatus(LP.RetryLiveProofRequest(rt.graph, family)())() is L.PendingLabel
    assert LP.LiveProofOutcomeStatus(LP.RetryLiveProofRequest(rt.graph, suffix)())() is L.PendingLabel
    assert LP.LiveProofOutcomeStatus(LP.RetryLiveProofRequest(rt.graph, comma)())() is L.PendingLabel
    assert LP.LiveProofOutcomeStatus(LP.RetryLiveProofRequest(rt.graph, malformed)())() is L.PendingLabel
    assert LP.LiveProofOutcomeStatus(LP.RetryLiveProofRequest(rt.graph, unparsed)())() is L.PendingLabel
    print("PASS scoped, prose, malformed, and unsupported goals cannot become reflexive equality proofs")

    invalid_record = M.Pair(M.Char("live-proof-request-v1"), M.Pair(M.Char("x=x"), M.EmptyList))
    assert LP.LiveProofOutcomeStatus(LP.RetryLiveProofRequest(rt.graph, invalid_record)())() is L.PendingLabel
    malformed_spec = LP.RecordLiveProofRequest(rt.graph, M.Char("x=x"), M.Char("invalid-spec"))()
    assert LP.LiveProofOutcomeStatus(LP.RetryLiveProofRequest(rt.graph, malformed_spec)())() is L.PendingLabel
    broken_registry = M.Pair(
        x,
        M.Pair(
            x,
            M.Pair(
                M.Pair(x, M.EmptyList),
                M.Pair(
                    M.EmptyList,
                    M.Pair(
                        M.EmptyList,
                        M.Pair(M.false_value, M.Pair(M.false_value, M.Pair(M.Char("invalid registry"), M.EmptyList))),
                    ),
                ),
            ),
        ),
    )
    invalid_registry = LP.RecordLiveProofRequest(rt.graph, M.Char("x=x"), broken_registry)()
    assert LP.LiveProofOutcomeStatus(LP.RetryLiveProofRequest(rt.graph, invalid_registry)())() is L.PendingLabel
    assert M.IsNat(M.one, M.FromContextGetConstructors(rt.graph)())() is M.truth_value
    mismatch_spec = LP.LiveProofRequestSpec(request)()
    mismatch = LP.RecordLiveProofRequest(rt.graph, M.Char("x=y"), mismatch_spec)()
    assert LP.LiveProofOutcomeStatus(LP.RetryLiveProofRequest(rt.graph, mismatch)())() is L.PendingLabel
    zero = LP.RetryLiveProofRequest(rt.graph, request, M.Zero)()
    invalid_budget = LP.RetryLiveProofRequest(rt.graph, request, M.Char("forever"))()
    assert LP.LiveProofOutcomeStatus(zero)() is L.PendingLabel
    assert LP.LiveProofOutcomeStatus(invalid_budget)() is L.PendingLabel
    print("PASS malformed records, mismatched supplied specs, and invalid or zero budgets stay pending")

    reflexive = LP.RecordLiveProofRequest(rt.graph, M.Char("x=x"))()
    result = LP.RetryLiveProofRequest(rt.graph, reflexive)()
    assert LP.LiveProofOutcomeStatus(result)() is L.ProvedLabel
    assert M.Head(LP.LiveProofOutcomeVerification(result)())() is L.DerivationVerifiedLabel
    assert M.IsPair(LP.LiveProofOutcomeReceipt(result)())() is M.truth_value
    print("PASS reflexivity still requires a saved derivation and independent verification")

    restored_target = LP.RecordLiveProofRequest(rt.graph, flt_text)()
    pending = LP.RetryLiveProofRequest(rt.graph, restored_target)()
    rt.graph.add_node(M.Char("unrelated note"))
    codec = persistence.SnapshotCodec(Main._runtime_namespace())
    with tempfile.TemporaryDirectory(prefix="hyge-live-proof-") as snapshot_dir:
        snapshot_path = os.path.join(snapshot_dir, "live-goal.json")
        codec.save(rt.graph, snapshot_path)
        restored = codec.load(snapshot_path)
        resumed = runtime.make_fresh_runtime()
        codec.activate(restored, resumed.graph)
    restored_request = LP.LatestLiveProofRequest(M.FromContextGetNodes(resumed.graph)())()
    restored_outcome = LP.LatestLiveProofOutcome(M.FromContextGetNodes(resumed.graph)(), restored_request)()
    assert M.Compare(LP.LiveProofRequestText(restored_request)(), flt_text)() is M.truth_value
    assert LP.LiveProofOutcomeStatus(restored_outcome)() is L.PendingLabel
    spec = LP.LiveProofRequestSpec(restored_request)()
    assert PG.GoalSpecNoSolutions(spec)() is M.truth_value
    assert PG.GoalSpecPositiveOnly(spec)() is M.truth_value
    assert M.IsPair(PG.GoalSpecExpVars(spec)())() is M.truth_value
    assert M.IsPair(PG.GoalSpecParamConstraints(spec)())() is M.truth_value
    assert LP.LiveProofOutcomeStatus(LP.RetryLiveProofRequest(resumed.graph)())() is L.PendingLabel
    recovered_equality = LP.RecordLiveProofRequest(resumed.graph, M.Char("x+y=y+x"))()
    result = LP.RetryLiveProofRequest(resumed.graph, recovered_equality)()
    assert LP.LiveProofOutcomeStatus(result)() is L.ProvedLabel
    assert M.Head(LP.LiveProofOutcomeVerification(result)())() is L.DerivationVerifiedLabel
    print("PASS snapshot restore retains scope, current request, outcome history, and checked learned-rule reuse")
