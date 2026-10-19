"""W23: partial/signed subtraction, gcd cofactors and schema-derived NatLess.

Arithmetic edges compute inputs; ordinary Peano schemas derive order facts.
Checker B checks the derivation conditional on the explicitly computed input
facts, not a new arithmetic action. No FTA, Eisenstein UFD or FLT is derived.
"""
import os
import sys
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from cat_theo_machine import machine as M, labels as L, proof as P
from cat_theo_machine import runtime, main as main_mod, checker_b as CB
from cat_theo_machine import graph_task as GT, dialogue as D, persistence
from cat_theo_machine.math import arithmetic as A

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def chain(*items):
    out = M.EmptyList
    for item in reversed(items):
        out = M.Pair(item, out)
    return out


def fact(label, *args):
    return M.Pair(label, chain(*args))


def field(record, index):
    cursor = M.Tail(record)()
    for _ in range(index):
        cursor = M.Tail(cursor)()
    return M.Head(cursor)()


def main():
    t0 = time.monotonic()
    rt = runtime.make_fresh_runtime()
    pack = rt.load_pack(os.path.join(REPO, 'packs', 'nat-order.pack.yaml'), main_mod._runtime_namespace())
    reg = M.FromContextGetConstructors(rt.graph)()
    count = 0

    def check(name, ok):
        nonlocal count
        assert ok, name
        count += 1
        print('PASS', name, flush=True)

    def take(result):
        nonlocal reg
        reg = M.Head(M.Tail(result)())()
        return M.Head(result)()

    def nat(n):
        return take(M.NatFromRep(M.GMPRep(str(n)), reg)())

    def equal(a, b):
        return M.NatEq(a, b, reg)() is M.truth_value

    def whole(n):
        magnitude = nat(abs(n))
        return take(A.WholeFromSignedNat(M.one if n < 0 else M.Zero, magnitude, reg)())

    for x, y, expected in ((9, 4, 5), (4, 4, 0), (0, 0, 0), (1001, 1, 1000), (9, 0, 9)):
        a, b, answer = nat(x), nat(y), nat(expected)
        result = take(A.NatSubtract(a, b, reg)())
        check('natural subtraction %d-%d' % (x, y), equal(result, answer))
        restored = take(A.Add(result, b, reg)())
        check('difference reconstructs minuend', equal(restored, a))
    check('natural underflow is refused, not clamped to zero', take(A.NatSubtract(nat(2), nat(3), reg)()) is M.EmptyList)
    bad = M.Thingy()
    for left, right in ((bad, M.one), (M.one, bad)):
        original = reg
        check('natural subtraction refuses invalid sort', take(A.NatSubtract(left, right, reg)()) is M.EmptyList)
        check('refusal threads the unchanged registry', reg is original)
    for x, y, expected in ((3, 8, -5), (-3, 8, -11), (3, -8, 11), (-3, -8, 5), (0, 0, 0), (-4, -4, 0)):
        left, right, answer = whole(x), whole(y), whole(expected)
        result = take(A.WholeSubtract(left, right, reg)())
        check('signed subtraction %d-(%d)' % (x, y), A.WholeEqual(result, answer, reg)() is M.truth_value)
    for left, right in ((M.one, whole(1)), (whole(1), bad)):
        check('signed subtraction refuses non-Whole', take(A.WholeSubtract(left, right, reg)()) is M.EmptyList)

    for a, b, expected in ((12, 3, 4), (0, 5, 0), (1, 1, 1), (1000, 10, 100)):
        numerator, divisor, answer = nat(a), nat(b), nat(expected)
        quotient = take(A.ExactNatQuotient(numerator, divisor, reg)())
        check('exact quotient %d/%d' % (a, b), equal(quotient, answer))
        product = take(A.Multiply(quotient, divisor, reg)())
        check('quotient reconstructs numerator', equal(product, numerator))
    for a, b in ((nat(5), nat(2)), (M.Zero, M.Zero), (M.one, M.Zero), (bad, M.one), (M.one, bad)):
        check('inexact/zero-divisor/invalid quotient refused', take(A.ExactNatQuotient(a, b, reg)()) is M.EmptyList)

    cofactor_record = M.EmptyList
    for a, b, g, u, v in ((18, 30, 6, 3, 5), (35, 64, 1, 35, 64), (2, 8, 2, 1, 4),
                          (0, 7, 7, 0, 1), (7, 0, 7, 1, 0), (9, 9, 9, 1, 1)):
        left, right = nat(a), nat(b)
        expected_g, expected_u, expected_v = nat(g), nat(u), nat(v)
        record = take(A.CoprimeCofactors(left, right, reg)())
        check('cofactor record has native label', M.Head(record)() is L.CoprimeCofactorsLabel)
        actual_g, actual_u, actual_v = field(record, 2), field(record, 3), field(record, 4)
        check('gcd/cofactors for (%d,%d)' % (a, b), equal(actual_g, expected_g) and equal(actual_u, expected_u) and equal(actual_v, expected_v))
        reconstructed_left = take(A.Multiply(actual_g, actual_u, reg)())
        reconstructed_right = take(A.Multiply(actual_g, actual_v, reg)())
        check('both inputs reconstruct from gcd and cofactors', equal(reconstructed_left, left) and equal(reconstructed_right, right))
        check('reduced cofactors are coprime', A.IsCoprime(actual_u, actual_v, reg)() is M.truth_value)
        if a == 2 and b == 8:
            check('decoy (2,8) is NOT originally coprime', A.IsCoprime(left, right, reg)() is M.false_value)
            check('decoy retains nonunit gcd rather than discarding hypothesis', not equal(actual_g, M.one))
        cofactor_record = record
    for left, right in ((M.Zero, M.Zero), (bad, M.one), (M.one, bad)):
        check('undefined/invalid cofactor pair refused', take(A.CoprimeCofactors(left, right, reg)()) is M.EmptyList)

    rules = pack.rule_chain
    check('pack contains only two generic order schemas', len(pack.rule_map) == 2)
    check('pack is registered without a problem agenda', os.path.join(REPO, 'packs', 'nat-order.pack.yaml') in main_mod.PACK_PATHS)
    saved_start = saved_goal = saved_proof = M.EmptyList
    for n in (1, 2, 7, 1000):
        upper = nat(n)
        expected_lower = nat(n - 1)
        computed = take(A.NatPredecessorFact(upper, reg)())
        check('positive natural produces a successor computation fact', M.Head(computed)() is L.NatSuccessorLabel)
        lower = field(computed, 0)
        check('fact agrees with machine predecessor/successor', equal(lower, expected_lower) and equal(field(computed, 1), upper))
        start = P.Knowledge(chain(computed))()
        goal = P.Knowledge(chain(fact(L.NatLessLabel, lower, upper)))()
        closure = GT.ForwardDeriveFacts(chain(computed), rules, M.two, reg)()
        check('forward schema derives NatLess', P.FactsCover(P.KnowledgeFacts(goal)(), closure)() is M.truth_value)
        proof = take(D.SearchKnowledgeDerivation(start, goal, rules, M.two, reg)())
        check('search finds an ordinary knowledge derivation', proof is not M.EmptyList)
        check('Checker B verifies schema-derived NatLess', M.Head(CB.VerifyDerivation(proof, start, goal, rules, reg)())() is L.DerivationVerifiedLabel)
        swapped = P.Knowledge(chain(fact(L.NatLessLabel, upper, lower)))()
        check('same proof against swapped pair is refused', M.Head(CB.VerifyDerivation(proof, start, swapped, rules, reg)())() is L.GoalMismatchLabel)
        check('same proof with withheld rule is refused', M.Head(CB.VerifyDerivation(proof, start, goal, M.EmptyList, reg)())() is L.UnknownRuleLabel)
        check('swapped inequality is not derivable', take(D.SearchKnowledgeDerivation(start, swapped, rules, M.two, reg)()) is M.EmptyList)
        saved_start, saved_goal, saved_proof = start, goal, proof
    for value in (M.Zero, bad, whole(-1)):
        check('zero or wrong sort emits no predecessor fact', take(A.NatPredecessorFact(value, reg)()) is M.EmptyList)
    empty_start = P.Knowledge(M.EmptyList)()
    check('no computed premise means no order proof', take(D.SearchKnowledgeDerivation(empty_start, saved_goal, rules, M.two, reg)()) is M.EmptyList)
    zero_goal = P.Knowledge(chain(fact(L.NatLessLabel, M.Zero, M.Zero)))()
    check('zero does not acquire a strict self inequality', take(D.SearchKnowledgeDerivation(empty_start, zero_goal, rules, M.two, reg)()) is M.EmptyList)
    lower_record = take(A.NatPredecessorFact(nat(6), reg)())
    middle = field(lower_record, 0)
    bottom_record = take(A.NatPredecessorFact(middle, reg)())
    bottom = field(bottom_record, 0)
    top = field(lower_record, 1)
    start = P.Knowledge(chain(lower_record, bottom_record))()
    goal = P.Knowledge(chain(fact(L.NatLessLabel, bottom, top)))()
    proof = take(D.SearchKnowledgeDerivation(start, goal, rules, M.three, reg)())
    check('transitive decrease uses both computed predecessor facts', proof is not M.EmptyList)
    check('multi-step transitive order proof verified', M.Head(CB.VerifyDerivation(proof, start, goal, rules, reg)())() is L.DerivationVerifiedLabel)

    codec = persistence.SnapshotCodec(main_mod._runtime_namespace())
    state = codec.load_snapshot(codec.capture_objects({'registry': reg, 'start': saved_start,
        'goal': saved_goal, 'proof': saved_proof, 'rules': rules, 'cofactors': cofactor_record}))
    roots = state.roots
    check('arithmetic/order vocabulary snapshot-registered', state.symbols['NatSuccessorLabel'] is L.NatSuccessorLabel and state.symbols['CoprimeCofactorsLabel'] is L.CoprimeCofactorsLabel)
    check('ordinary order derivation re-verifies after codec round-trip', M.Head(CB.VerifyDerivation(roots['proof'], roots['start'], roots['goal'], roots['rules'], roots['registry'])())() is L.DerivationVerifiedLabel)
    record = roots['cofactors']
    check('cofactor record survives codec round-trip', M.Head(record)() is L.CoprimeCofactorsLabel and A.IsCoprime(field(record, 3), field(record, 4), roots['registry'])() is M.truth_value)
    print('TEST 35: %d/%d checks passed (%.1fs).' % (count, count, time.monotonic() - t0))
    print('Not derived: FTA, coprime-square-factors, Eisenstein UFD, FLT or EveryStateMoves.')
    print('Trust boundary: computed successor facts are explicit premises; Checker B replays the Peano schema, not arithmetic provenance.')


if __name__ == '__main__':
    main()
