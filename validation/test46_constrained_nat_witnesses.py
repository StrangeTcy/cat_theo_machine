"""Bounded numeric witnesses: independently re-evaluated, never FLT receipts.

Finite search is not universal existence or a parametrisation theorem. A search
record is not a Checker-B derivation. Inputs/expected counts are host fixtures;
all machine construction, enumeration, matching and arithmetic use native edges.
"""
import os
import sys
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from cat_theo_machine import machine as M, labels as L, playground as PG
from cat_theo_machine import runtime, main as Main, persistence, checker_b as CB, proof as P
from cat_theo_machine.math import arithmetic as A


def chain(*items):
    out = M.EmptyList
    for item in reversed(items):
        out = M.Pair(item, out)
    return out


def expr(label, *args):
    return M.Pair(label, chain(*args))


def field(record, index):
    cursor = M.Tail(record)()
    for _ in range(index):
        cursor = M.Tail(cursor)()
    return M.Head(cursor)()


def main():
    t0 = time.monotonic()
    rt = runtime.make_fresh_runtime()
    reg = M.FromContextGetConstructors(rt.graph)()
    checks = 0

    def check(name, ok):
        nonlocal checks
        assert ok, name
        checks += 1
        print('PASS', name, flush=True)

    def take(result):
        nonlocal reg
        reg = M.Head(M.Tail(result)())()
        return M.Head(result)()

    def nat(value):
        return take(M.NatFromRep(M.GMPRep(str(value)), reg)())

    def equal(left, right):
        return M.NatEq(left, right, reg)() is M.truth_value

    def search(constraints, variables, bound, budget, status, examined):
        record = take(PG.FindNatWitness(constraints, variables, bound, budget, reg)())
        check('record vocabulary is explicit', M.Head(record)() is L.NatWitnessSearchLabel)
        check('exact problem and limits recorded', M.Compare(field(record, 0), constraints)() is M.truth_value
              and M.Compare(field(record, 1), variables)() is M.truth_value
              and M.IdentityCompare(field(record, 2), bound)() is M.truth_value
              and M.IdentityCompare(field(record, 3), budget)() is M.truth_value)
        check('search status is scoped', field(record, 4) is status)
        check('candidate count is exact', equal(field(record, 6), nat(examined)))
        if status is not L.NatWitnessFoundLabel:
            check('non-found record carries no assignment', field(record, 5) is M.EmptyList)
        else:
            check('independent assignment replay succeeds', take(PG.VerifyNatWitness(
                constraints, variables, bound, field(record, 5), reg)()) is M.truth_value)
        return record

    x, y, z = M.Char('numeric-x'), M.Char('numeric-y'), M.Char('numeric-z')
    variables = chain(x, y)
    eq = lambda left, right: expr(L.ExprEqLabel, left, right)
    lt = lambda left, right: expr(L.ExprLtLabel, left, right)
    add = lambda left, right: expr(L.ExprAddLabel, left, right)
    mul = lambda left, right: expr(L.ExprMulLabel, left, right)
    pw = lambda left, right: expr(L.ExprPowLabel, left, right)
    constraints = chain(eq(add(x, y), M.three), eq(mul(x, y), M.two), lt(x, y))
    record = search(constraints, variables, nat(4), nat(16), L.NatWitnessFoundLabel, 10)
    environment = field(record, 5)
    check('first numeric witness is (1,2)', equal(M.Head(M.Tail(M.Head(environment)())())(), M.one)
          and equal(M.Head(M.Tail(M.Head(M.Tail(environment)())())())(), M.two))
    check('numeric witness can enter arithmetic', equal(take(PG.EvaluateNatExpr(mul(x, y), environment, reg)()), M.two))
    check('changed equation rejected on replay', take(PG.VerifyNatWitness(chain(eq(add(x, y), M.two)), variables,
          nat(4), environment, reg)()) is M.false_value)
    check('search record cannot certify universal movement', M.Head(CB.VerifyDerivation(
        record, P.Knowledge(M.EmptyList)(), P.Knowledge(chain(expr(L.EveryStateMovesLabel, x)))(),
        M.EmptyList, reg)())() is not L.DerivationVerifiedLabel)

    # Stream carries, including the very last tuple, rather than a diagonal or
    # a materialised Cartesian product. First coordinate changes fastest.
    for a, b, examined in ((0, 0, 1), (1, 0, 2), (0, 1, 4), (2, 2, 9)):
        search(chain(eq(x, nat(a)), eq(y, nat(b))), variables, M.three, M.nine,
               L.NatWitnessFoundLabel, examined)
    three = chain(x, y, z)
    last = chain(eq(x, M.one), eq(y, M.one), eq(z, M.one))
    search(last, three, M.two, M.seven, L.NatWitnessBudgetLabel, 7)
    search(last, three, M.two, M.eight, L.NatWitnessFoundLabel, 8)
    search(constraints, variables, nat(4), M.nine, L.NatWitnessBudgetLabel, 9)
    search(constraints, variables, nat(4), M.Zero, L.NatWitnessBudgetLabel, 0)
    search(chain(eq(pw(x, M.two), M.two)), chain(x), M.three, M.three,
           L.NatWitnessExhaustedLabel, 3)
    # Exhausting [0,3) says nothing about a solution at 3.
    root = chain(eq(pw(x, M.two), M.nine))
    search(root, chain(x), M.three, M.three, L.NatWitnessExhaustedLabel, 3)
    root_record = search(root, chain(x), nat(4), nat(4), L.NatWitnessFoundLabel, 4)
    check('found root reuses the natural index', M.IdentityCompare(
        M.Head(M.Tail(M.Head(field(root_record, 5))())())(), nat(3))() is M.truth_value)
    search(root, chain(x), M.Zero, M.Zero, L.NatWitnessExhaustedLabel, 0)
    search(M.EmptyList, M.EmptyList, M.Zero, M.one, L.NatWitnessFoundLabel, 1)
    search(chain(eq(M.one, M.two)), M.EmptyList, M.Zero, M.one, L.NatWitnessExhaustedLabel, 1)
    search(chain(eq(M.one, M.one)), M.EmptyList, M.Zero, M.Zero, L.NatWitnessBudgetLabel, 0)
    search(M.EmptyList, variables, M.two, M.one, L.NatWitnessFoundLabel, 1)

    opaque_variable = M.Thingy()
    opaque_record = search(chain(eq(opaque_variable, M.two)), chain(opaque_variable),
                           M.three, M.three, L.NatWitnessFoundLabel, 3)
    check('binding an opaque variable does not change its sort', A.IsNat(opaque_variable, reg)() is M.false_value)
    check('opaque-variable assignment contains a real Nat value', A.IsNat(
        M.Head(M.Tail(M.Head(field(opaque_record, 5))())())(), reg)() is M.truth_value)
    search(chain(eq(expr(L.ExprIntLabel, M.one), M.one)), M.EmptyList, M.Zero,
           M.one, L.NatWitnessFoundLabel, 1)

    bad = M.Thingy()
    for malformed, vars_ in (
        (chain(eq(x, M.one)), chain(x, x)),
        (chain(eq(x, M.one)), chain(M.one)),
        (chain(eq(x, y)), chain(x)),
        (chain(expr(L.ExprEqLabel, x)), chain(x)),
        (chain(expr(L.ExprEqLabel, x, M.one, M.two)), chain(x)),
        (chain(eq(expr(L.ExprDivLabel, x, M.two), M.one)), chain(x)),
        (chain(eq(expr(L.ExprPowLabel, x, y), M.one)), variables),
        (chain(eq(expr(L.ExprIntLabel, x), M.one)), chain(x)),
        (chain(expr(L.EveryStateMovesLabel, x)), chain(x)),
        (M.Pair(eq(x, M.one), bad), chain(x)),
        (chain(eq(x, M.one)), M.Pair(x, bad)),
        # Validate the whole request; a false prefix must not hide bad syntax.
        (chain(eq(M.one, M.two), eq(expr(L.ExprDivLabel, x, M.two), M.one)), chain(x)),
    ):
        search(malformed, vars_, M.two, M.two, L.NatWitnessInvalidLabel, 0)
    for bound, budget in ((bad, M.one), (M.two, bad)):
        search(constraints, variables, bound, budget, L.NatWitnessInvalidLabel, 0)
    for malformed_env in (
        M.EmptyList,
        chain(chain(x, M.one)),
        chain(chain(y, M.two), chain(x, M.one)),
        chain(chain(x, M.one), chain(x, M.two)),
        chain(chain(x, M.one), chain(y, M.two), chain(z, M.Zero)),
        chain(chain(x, bad), chain(y, M.two)),
        chain(chain(x, M.one, M.Zero), chain(y, M.two)),
        M.Pair(chain(x, M.one), bad),
    ):
        check('malformed assignment refused by independent replay', take(PG.VerifyNatWitness(
            constraints, variables, nat(4), malformed_env, reg)()) is M.EmptyList)
    check('out-of-bound otherwise correct assignment refused', take(PG.VerifyNatWitness(
        root, chain(x), M.three, field(root_record, 5), reg)()) is M.EmptyList)
    check('bad bound refused on replay', take(PG.VerifyNatWitness(
        root, chain(x), bad, field(root_record, 5), reg)()) is M.EmptyList)
    check('unsupported constraints refused on replay', take(PG.VerifyNatWitness(
        chain(expr(L.EveryStateMovesLabel, x)), chain(x), nat(4), field(root_record, 5), reg)()) is M.EmptyList)

    codec = persistence.SnapshotCodec(Main._runtime_namespace())
    restored = codec.load_snapshot(codec.capture_objects({'record': record, 'registry': reg}))
    saved = restored.roots['record']
    saved_reg = restored.roots['registry']
    check('witness labels snapshot-registered', restored.symbols['NatWitnessFoundLabel'] is L.NatWitnessFoundLabel
          and M.Head(saved)() is L.NatWitnessSearchLabel)
    replay = PG.VerifyNatWitness(field(saved, 0), field(saved, 1), field(saved, 2), field(saved, 5), saved_reg)()
    check('numeric assignment re-evaluates after codec round-trip', M.Head(replay)() is M.truth_value)
    print('TEST 46: %d/%d checks passed (%.1fs).' % (checks, checks, time.monotonic() - t0))
    print('Bounded arithmetic search only; no universal witness theorem, parametrisation, FLT or ledger receipt.')


if __name__ == '__main__':
    main()
