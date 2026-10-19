"""W22: ordinary rewrite paths plus independently replayed grid certificates.

The default symbolic walker still lacks ring normalisation. A separate
explicitly licensed grid inference now certifies the test26 identities.
No FLT theorem is claimed; these are generic polynomial equalities only.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from cat_theo_machine import machine as M, proof as P, labels as L
from cat_theo_machine import playground as PG, invariance as I, checker_b as CB
from cat_theo_machine import rewrite_rules as RR, runtime


def binary(label, a, b):
    return M.Pair(label, M.Pair(a, M.Pair(b, M.EmptyList)))


def chain(*items):
    result = M.EmptyList
    for item in reversed(items):
        result = M.Pair(item, result)
    return result


def field(record, n):
    rest = M.Tail(record)()
    for _ in range(n):
        rest = M.Tail(rest)()
    return M.Head(rest)()


def main():
    rt = runtime.make_fresh_runtime()
    reg = M.FromContextGetConstructors(rt.graph)()
    rules = RR.build_default_rewrite_rule_chain()
    a, b, c = M.Char('a'), M.Char('b'), M.Char('c')
    add = lambda x, y: binary(L.ExprAddLabel, x, y)
    mul = lambda x, y: binary(L.ExprMulLabel, x, y)
    pw = lambda x, y: binary(L.ExprPowLabel, x, y)
    passed = 0

    def check(name, ok):
        nonlocal passed
        assert ok, name
        passed += 1
        print('PASS', name, flush=True)

    def certificate(lhs, rhs, variables, fuel=M.nine):
        nonlocal reg
        result = PG.PolynomialRewriteCertificate(lhs, rhs, variables, rules, reg, fuel)()
        record = M.Head(result)()
        rest = M.Tail(result)()
        success = M.Head(rest)()
        derivation = M.Head(M.Tail(rest)())()
        reg = M.Head(M.Tail(M.Tail(rest)())())()
        return record, success, derivation

    start = mul(c, add(a, b))
    goal = add(mul(c, a), mul(c, b))
    variables = chain(a, b, c)
    record, ok, derivation = certificate(start, goal, variables)
    check('distributivity grid true', field(record, 5) is M.truth_value)
    check('default rules now usable through certificate API', ok is M.truth_value)
    verdict = CB.VerifyDerivation(derivation, start, goal, rules, reg)()
    check('Checker B independently replays root rewrite', M.Head(verdict)() is L.DerivationVerifiedLabel)
    check('withheld trusted rules rejected', M.Head(CB.VerifyDerivation(derivation, start, goal, M.EmptyList, reg)())() is L.UnknownRuleLabel)
    check('changed goal rejected', M.Head(CB.VerifyDerivation(derivation, start, a, rules, reg)())() is L.GoalMismatchLabel)

    nested = mul(a, add(b, mul(c, add(a, b))))
    nested_goal = add(mul(a, b), add(mul(mul(a, c), a), mul(mul(a, c), b)))
    _, ok, derivation = certificate(nested, nested_goal, variables)
    check('multi-step nested path certificate', ok is M.truth_value)
    check('Checker B replays nested paths', M.Head(CB.VerifyDerivation(derivation, nested, nested_goal, rules, reg)())() is L.DerivationVerifiedLabel)
    _, ok, derivation = certificate(start, goal, variables, M.Zero)
    check('zero fuel is a refusal, no certificate', ok is M.false_value and derivation is M.EmptyList)
    _, ok, derivation = certificate(a, a, chain(a), M.Zero)
    check('reflexivity needs no steps', ok is M.truth_value and M.Head(CB.VerifyDerivation(derivation, a, a, rules, reg)())() is L.DerivationVerifiedLabel)

    record, ok, derivation = certificate(add(pw(a, M.two), a), mul(M.two, a), chain(a))
    check('degree trap uses three points', M.NatEq(field(record, 4), M.three, reg)() is M.truth_value)
    check('non-identity refused with witness', field(record, 5) is M.false_value and field(record, 6) is not M.EmptyList and ok is M.false_value and derivation is M.EmptyList)
    for label in (L.ExprNegLabel, L.ExprFracLabel, L.ExprDivLabel):
        term = binary(label, a, b)
        record, ok, derivation = certificate(term, term, chain(a, b))
        check('unsupported constructor refused even reflexively', field(record, 5) is M.EmptyList and ok is M.false_value and derivation is M.EmptyList)

    # One identity test26 labels grid-derived. No supplied rule has a power
    # head: a power-only term has no possible nontrivial default rewrite.
    four_result = M.NatFromRep(M.GMPRep('4'), reg)()
    four = M.Head(four_result)()
    reg = M.Head(M.Tail(four_result)())()
    lhs, rhs = pw(a, four), pw(pw(a, M.two), M.two)
    record, ok, derivation = certificate(lhs, rhs, chain(a))
    check('test26 power identity remains grid true', field(record, 5) is M.truth_value)
    check('precise partial: power expansion unavailable, not a fabricated proof', ok is M.false_value and derivation is M.EmptyList)
    remaining = rules
    while remaining is not M.EmptyList:
        rule = M.Head(remaining)()
        check('default pattern cannot match ExprPow', M.Head(P.RulePattern(rule)())() is not L.ExprPowLabel)
        check('no root rewrite of power expression', M.Compare(P.RewriteHere(rule, lhs)(), lhs)() is M.truth_value)
        remaining = M.Tail(remaining)()
    check('legacy test26 RewriteEquals obstruction unchanged', I.RewriteEquals(lhs, rhs, rules, reg)() is M.false_value)

    trusted_grid = chain(L.PolynomialGridRuleLabel)

    def grid_derivation(left, right, variables):
        nonlocal reg
        result = PG.PolynomialGridDerivation(left, right, variables, reg)()
        reg = M.Head(M.Tail(M.Tail(result)())())()
        return M.Head(result)(), M.Head(M.Tail(result)())()

    def accepted(proof, left, right, trusted=trusted_grid):
        return M.Head(CB.VerifyDerivation(proof, left, right, trusted, reg)())() is L.DerivationVerifiedLabel

    power_record, power_proof = grid_derivation(lhs, rhs, chain(a))
    check('Checker B certifies test26 power identity by full grid replay', accepted(power_proof, lhs, rhs))
    check('grid capability must be explicitly trusted', not accepted(power_proof, lhs, rhs, rules))
    check('grid derivation against wrong goal refused', not accepted(power_proof, lhs, a))
    check('grid derivation against wrong start refused', not accepted(power_proof, a, rhs))
    session = M.Char('grid-certificate-test')
    receipt = M.Pair(L.ProofReceiptLabel, chain(session, lhs, rhs, power_proof))
    policy = M.Pair(L.CheckPolicyLabel, chain(session, lhs, rhs))
    check('grid proof works through receipt verification', M.Head(CB.VerifyProofReceipt(receipt, policy, trusted_grid, reg)())() is L.DerivationVerifiedLabel)
    wrong_policy = M.Pair(L.CheckPolicyLabel, chain(M.Char('wrong-session'), lhs, rhs))
    check('grid receipt keeps session scope guard', M.Head(CB.VerifyProofReceipt(receipt, wrong_policy, trusted_grid, reg)())() is L.CandidateScopeMismatchLabel)


    p, n = M.Char('p'), M.Char('n')
    left = add(pw(p, M.two), mul(mul(four, add(p, pw(n, M.two))), pw(n, M.two)))
    right = pw(add(p, mul(M.two, pw(n, M.two))), M.two)
    pyth_record, pyth_proof = grid_derivation(left, right, chain(p, n))
    fifteen = M.NatFromRep(M.GMPRep('15'), reg)()
    reg = M.Head(M.Tail(fifteen)())()
    check('test26 additive identity uses 15 grid points', M.NatEq(field(pyth_record, 4), M.Head(fifteen)(), reg)() is M.truth_value)
    check('Checker B certifies test26 additive identity by full grid replay', accepted(pyth_proof, left, right))

    def replaced(fields, index, value):
        if index == 0:
            return M.Pair(value, M.Tail(fields)())
        return M.Pair(M.Head(fields)(), replaced(M.Tail(fields)(), index - 1, value))

    def record_change(record, index, value):
        return M.Pair(L.PolynomialIdentityLabel, replaced(M.Tail(record)(), index, value))

    def forged_step(record, left, right, action=None):
        nonlocal reg
        if action is None:
            action = M.Pair(L.PolynomialGridActionLabel, chain(record))
        result = P.Step(left, action, right, reg)()
        reg = M.Head(M.Tail(result)())()
        return M.Head(result)()

    def refused_record(record, left=lhs, right=rhs, action=None):
        step = forged_step(record, left, right, action)
        verdict = CB.VerifyProofStep(step, trusted_grid, chain(left), chain(left), reg)()
        return M.Head(verdict)() is not L.StepVerifiedLabel

    check('tampered degree bound rejected', refused_record(record_change(power_record, 3, chain(M.one))))
    check('tampered grid count rejected', refused_record(record_change(power_record, 4, M.two)))
    check('tampered lhs rejected', refused_record(record_change(power_record, 0, a)))
    check('tampered rhs rejected', refused_record(record_change(power_record, 1, a)))
    check('tampered verdict rejected', refused_record(record_change(power_record, 5, M.false_value)))
    check('nonempty witness on true proof rejected', refused_record(record_change(power_record, 6, chain(M.Zero))))
    check('omitted variables on forged true proof rejected', refused_record(record_change(power_record, 2, M.EmptyList)))
    check('duplicate variables on forged true proof rejected', refused_record(record_change(power_record, 2, chain(a, a))))
    check('truncated record rejected', refused_record(M.Pair(L.PolynomialIdentityLabel, chain(lhs))))
    check('truncated action rejected', refused_record(power_record, action=M.Pair(L.PolynomialGridActionLabel, M.EmptyList)))
    check('extra action payload rejected', refused_record(power_record, action=M.Pair(L.PolynomialGridActionLabel, chain(power_record, a))))

    false_left, false_right = add(pw(a, M.two), a), mul(M.two, a)
    false_record, false_proof = grid_derivation(false_left, false_right, chain(a))
    check('nonidentity produces no grid derivation', false_proof is M.EmptyList and field(false_record, 5) is M.false_value)
    # The false identity agrees on 0,1. Forging its result AND reducing the
    # degree/count must not fool the verifier into checking that smaller grid.
    forged = record_change(record_change(record_change(record_change(false_record,
        5, M.truth_value), 6, M.EmptyList), 3, chain(M.one)), 4, M.two)
    check('degree-trap forgery rejected by recomputing full grid', refused_record(forged, false_left, false_right))

    for term, variables, name in (
        (a, M.EmptyList, 'missing all variables'),
        (add(a, b), chain(a), 'missing one variable'),
        (a, chain(a, a), 'duplicate variables'),
        (a, M.Pair(a, b), 'improper variable chain'),
        (a, chain(M.one), 'numeric variable'),
        (binary(L.ExprNegLabel, a, b), M.EmptyList, 'unsupported term with zero variables'),
        (M.Pair(L.ExprAddLabel, chain(a)), chain(a), 'too few arguments'),
        (M.Pair(L.ExprAddLabel, chain(a, b, a)), chain(a, b), 'extra argument'),
        (M.Pair(L.ExprIntLabel, chain(a)), chain(a), 'nonnumeric constant'),
        (M.Pair(L.ExprIntLabel, chain(M.one, M.two)), M.EmptyList, 'extra constant argument'),
        (pw(a, b), chain(a, b), 'symbolic exponent'),
    ):
        record, proof = grid_derivation(term, term, variables)
        check('grid refuses ' + name, field(record, 5) is M.EmptyList and proof is M.EmptyList)

    record, proof = grid_derivation(M.one, M.two, M.EmptyList)
    check('unequal constants with empty grid tuple are FALSE', field(record, 5) is M.false_value and proof is M.EmptyList)
    forged = record_change(record, 5, M.truth_value)
    check('forged constant equality refused', refused_record(forged, M.one, M.two))
    record, proof = grid_derivation(add(M.one, M.one), M.two, M.EmptyList)
    check('true constant identity checked with zero variables', accepted(proof, add(M.one, M.one), M.two))
    check('constant grid has exactly one empty tuple', M.NatEq(field(record, 4), M.one, reg)() is M.truth_value)

    # Persist the actual proof, registry and endpoints through the existing
    # snapshot codec. No alternative machine-term serialisation is introduced.
    from cat_theo_machine import persistence, main as main_mod
    codec = persistence.SnapshotCodec(main_mod._runtime_namespace())
    snapshot = codec.capture_objects({'proof': power_proof, 'registry': reg,
        'lhs': lhs, 'rhs': rhs, 'trusted': trusted_grid})
    restored = codec.load_snapshot(snapshot)
    roots = restored.roots
    replay = CB.VerifyDerivation(roots['proof'], roots['lhs'], roots['rhs'],
        roots['trusted'], roots['registry'])()
    check('grid proof replays after codec round-trip', M.Head(replay)() is L.DerivationVerifiedLabel)
    check('grid action label snapshot-registered', restored.symbols['PolynomialGridActionLabel'] is L.PolynomialGridActionLabel)
    check('grid rule capability snapshot-registered', restored.symbols['PolynomialGridRuleLabel'] is L.PolynomialGridRuleLabel)
    print('W22: %d checks passed. Recorded grid proofs verified; symbolic normalization remains open.' % passed)


if __name__ == '__main__':
    main()
