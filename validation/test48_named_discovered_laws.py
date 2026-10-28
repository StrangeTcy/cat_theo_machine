"""Machine-native checks of named-law certification, bindings, and reuse."""

import os
import tempfile

from hyge import checker_b as CB
from hyge import discovered_laws as DL
from hyge import labels as L
from hyge import machine as M
from hyge import main as Main
from hyge import persistence
from hyge import playground as PG
from hyge import proof as P
from hyge import runtime


if __name__ == "__main__":
    rt = runtime.make_fresh_runtime()
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
    domain = M.Pair(M.one, M.EmptyList)
    named = M.Pair(
        L.NamedRegularityLabel,
        M.Pair(
            M.Char("addition commutes"),
            M.Pair(
                M.Char("add"),
                M.Pair(equation, M.Pair(domain, M.Pair(M.EmptyList, M.EmptyList))),
            ),
        ),
    )
    assert M.IdentityCompare(rt.ordered_rules(), M.EmptyList)() is M.truth_value
    recorded = DL.RecordNamedDiscoveredLaw(rt, named, authority)()
    rule = M.Head(recorded)()
    receipt = M.Head(M.Tail(recorded)())()
    verification = M.Head(M.Tail(M.Tail(recorded)())())()
    reg = M.Head(M.Tail(M.Tail(M.Tail(recorded)())())())()
    assert M.IdentityCompare(rule, M.EmptyList)() is M.false_value
    assert M.IdentityCompare(M.Head(verification)(), L.DerivationVerifiedLabel)() is M.truth_value
    assert M.IdentityCompare(rt.ordered_rules(), M.EmptyList)() is M.false_value
    assert M.IdentityCompare(rt.graph.lookup_derivation(lhs, rhs), M.EmptyList)() is M.false_value
    assert M.IdentityCompare(M.Head(M.FromContextGetNodes(rt.graph)())(), receipt)() is M.truth_value
    print("PASS named polynomial law is certified, linked to its proof, and enters the compiled rule chain")

    target = M.Pair(L.ExprAddLabel, M.Pair(M.two, M.Pair(M.three, M.EmptyList)))
    expected = M.Pair(L.ExprAddLabel, M.Pair(M.three, M.Pair(M.two, M.EmptyList)))
    assert M.Compare(P.RewriteHere(rule, target)(), expected)() is M.truth_value
    assert P.ContainsVar(P.RewriteHere(rule, target)())() is M.false_value
    plan = M.Pair(P.RewriteAction(rule, M.EmptyList)(), M.EmptyList)
    rewritten = P.BuildRewriteDerivation(target, plan, reg)()
    proof = M.Head(rewritten)()
    reg = M.Head(M.Tail(rewritten)())()
    checked = CB.VerifyDerivation(proof, target, expected, M.Pair(rule, M.EmptyList), reg)()
    assert M.IdentityCompare(M.Head(checked)(), L.DerivationVerifiedLabel)() is M.truth_value
    print("PASS named rule rewrites outside the sampled domain with shared variable bindings and replayable proof")

    rt.graph._replace_context(constructors=reg)
    codec = persistence.SnapshotCodec(Main._runtime_namespace())
    with tempfile.TemporaryDirectory(prefix="hyge-named-discovery-") as snapshot_dir:
        snapshot_path = os.path.join(snapshot_dir, "named-law.json")
        codec.save(rt.graph, snapshot_path)
        restored = codec.load(snapshot_path)
        resumed = runtime.make_fresh_runtime()
        codec.activate(restored, resumed.graph)
    reg = M.FromContextGetConstructors(resumed.graph)()
    restored_rule = M.Head(M.FromContextGetRuleOrder(resumed.graph)())()
    target = M.Pair(L.ExprAddLabel, M.Pair(M.two, M.Pair(M.three, M.EmptyList)))
    expected = M.Pair(L.ExprAddLabel, M.Pair(M.three, M.Pair(M.two, M.EmptyList)))
    assert M.Compare(P.RewriteHere(restored_rule, target)(), expected)() is M.truth_value
    restored_receipt = M.Head(M.FromContextGetNodes(resumed.graph)())()
    receipt_fields = M.Tail(restored_receipt)()
    restored_lhs = M.Head(M.Tail(receipt_fields)())()
    restored_rhs = M.Head(M.Tail(M.Tail(receipt_fields)())())()
    restored_proof = M.Head(M.Tail(M.Tail(M.Tail(receipt_fields)())())())()
    checked = CB.VerifyDerivation(restored_proof, restored_lhs, restored_rhs, authority, reg)()
    assert M.IdentityCompare(M.Head(checked)(), L.DerivationVerifiedLabel)() is M.truth_value
    print("PASS snapshot round trip preserves shared rule identities and the independently replayable named proof")

    repeated = M.Pair(L.ExprAddLabel, M.Pair(x, M.Pair(x, M.EmptyList)))
    doubled = M.Pair(L.ExprMulLabel, M.Pair(M.two, M.Pair(x, M.EmptyList)))
    repeat_equation = M.Pair(
        L.DiscoveredEquationLabel,
        M.Pair(M.Pair(x, M.EmptyList), M.Pair(repeated, M.Pair(doubled, M.EmptyList))),
    )
    certified = DL.CertifyDiscoveredEquation(repeat_equation, authority, reg)()
    repeat_rule = M.Head(certified)()
    reg = M.Head(M.Tail(M.Tail(M.Tail(certified)())())())()
    mismatch = M.Pair(L.ExprAddLabel, M.Pair(M.one, M.Pair(M.two, M.EmptyList)))
    assert M.IdentityCompare(M.Head(M.Match(P.RulePattern(repeat_rule)(), mismatch)())(), M.false_value)() is M.truth_value
    target = M.Pair(L.ExprAddLabel, M.Pair(M.three, M.Pair(M.three, M.EmptyList)))
    expected = M.Pair(L.ExprMulLabel, M.Pair(M.two, M.Pair(M.three, M.EmptyList)))
    assert M.Compare(P.RewriteHere(repeat_rule, target)(), expected)() is M.truth_value
    print("PASS repeated occurrences enforce one binding and instantiate the replacement")

    unlicensed = DL.CertifyDiscoveredEquation(equation, M.EmptyList, reg)()
    assert M.IdentityCompare(M.Head(unlicensed)(), M.EmptyList)() is M.truth_value
    unlicensed_verification = M.Head(M.Tail(M.Tail(unlicensed)())())()
    assert M.IdentityCompare(M.Head(unlicensed_verification)(), L.UnknownRuleLabel)() is M.truth_value
    reg = M.Head(M.Tail(M.Tail(M.Tail(unlicensed)())())())()
    print("PASS universal promotion requires explicit polynomial decision authority")

    singleton_lhs = M.Pair(L.ExprMulLabel, M.Pair(x, M.Pair(y, M.EmptyList)))
    singleton_equation = M.Pair(
        L.DiscoveredEquationLabel,
        M.Pair(variables, M.Pair(singleton_lhs, M.Pair(x, M.EmptyList))),
    )
    singleton_named = M.Pair(
        L.NamedRegularityLabel,
        M.Pair(
            M.Char("singleton multiplication"),
            M.Pair(
                M.Char("mul"),
                M.Pair(singleton_equation, M.Pair(domain, M.Pair(M.EmptyList, M.EmptyList))),
            ),
        ),
    )
    resumed.graph._replace_context(constructors=reg)
    prior_rules = M.FromContextGetRuleOrder(resumed.graph)()
    recorded = DL.RecordNamedDiscoveredLaw(resumed, singleton_named, authority)()
    assert M.IdentityCompare(M.Head(recorded)(), M.EmptyList)() is M.truth_value
    assert M.IdentityCompare(M.FromContextGetRuleOrder(resumed.graph)(), prior_rules)() is M.truth_value
    assert M.IdentityCompare(M.Head(M.FromContextGetNodes(resumed.graph)())(), singleton_named)() is M.truth_value
    reg = M.FromContextGetConstructors(resumed.graph)()
    print("PASS finite singleton agreement stays recorded without an unrestricted rule")

    gcd_lhs = M.Pair(L.ExprGcdLabel, M.Pair(x, M.Pair(y, M.EmptyList)))
    gcd_rhs = M.Pair(L.ExprGcdLabel, M.Pair(y, M.Pair(x, M.EmptyList)))
    gcd_equation = M.Pair(
        L.DiscoveredEquationLabel,
        M.Pair(variables, M.Pair(gcd_lhs, M.Pair(gcd_rhs, M.EmptyList))),
    )
    unsupported = DL.CertifyDiscoveredEquation(gcd_equation, authority, reg)()
    assert M.IdentityCompare(M.Head(unsupported)(), M.EmptyList)() is M.truth_value
    assert M.IdentityCompare(M.Head(M.Tail(unsupported)())(), M.EmptyList)() is M.truth_value
    assert M.IdentityCompare(M.Head(DL.CertifyDiscoveredEquation(M.EmptyList, authority, reg)())(), M.EmptyList)() is M.truth_value
    print("PASS unsupported and malformed equations cannot enter the active rule chain")
