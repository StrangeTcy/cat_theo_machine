"""Witness replay retains subset semantics while following matching order."""

import time

from hyge import invariant_miner as IM
from hyge import labels as L
from hyge import machine as M
from hyge import observed_structures as OS
from hyge import playground as PG
from hyge import runtime
from hyge import template_matching as TM


if __name__ == "__main__":
    empty = M.EmptyList
    first = M.Pair(M.Pair(M.one, empty), M.Pair(M.two, M.Pair(M.two, empty)))
    second = M.Pair(M.Pair(M.two, empty), M.Pair(M.three, M.Pair(M.three, empty)))
    third = M.Pair(M.Pair(M.three, empty), M.Pair(M.four, M.Pair(M.four, empty)))
    replayed = M.Pair(first, M.Pair(second, M.Pair(third, empty)))
    first_copy = M.Pair(M.Pair(M.one, empty), M.Pair(M.two, M.Pair(M.two, empty)))
    assert OS.ObservedWitnessSubset(M.Pair(first_copy, M.Tail(replayed)()), replayed)() is M.truth_value
    assert OS.ObservedWitnessSubset(M.Pair(third, M.Pair(second, empty)), replayed)() is M.truth_value
    assert OS.ObservedWitnessSubset(M.Pair(second, M.Pair(first, M.Pair(second,
        M.Pair(third, M.Pair(first, empty))))), replayed)() is M.truth_value
    assert OS.ObservedWitnessSubset(M.Pair(first, M.Pair(second,
        M.Pair(third, M.Pair(first, empty)))), replayed)() is M.truth_value
    assert OS.ObservedWitnessSubset(empty, replayed)() is M.truth_value
    assert OS.ObservedWitnessSubset(M.Pair(first, empty), empty)() is M.false_value
    assert OS.ObservedWitnessSubset(M.Pair(first, M.Atom()), replayed)() is M.false_value
    missing = M.Pair(M.Pair(M.four, empty), M.Pair(M.five, M.Pair(M.five, empty)))
    assert OS.ObservedWitnessSubset(M.Pair(first, M.Pair(missing, empty)), replayed)() is M.false_value
    forged = M.Pair(M.Pair(M.one, empty), M.Pair(M.three, M.Pair(M.three, empty)))
    assert OS.ObservedWitnessSubset(M.Pair(forged, empty), replayed)() is M.false_value
    print("PASS ordered, reordered, duplicate, exhausted-cursor and partial witness sets retain membership semantics")
    print("PASS missing, altered, empty-replay and malformed evidence is refused")

    rt = runtime.make_fresh_runtime()
    registry = M.FromContextGetConstructors(rt.graph)()
    operations = M.Head(PG.BuildNatOperationRegister(registry)())()
    assert M.Head(OS.ObservedExecutableOperations(operations, registry)())() is M.truth_value
    bound_result = M.NatFromRep(M.GMPRep("10"), registry)()
    bound = M.Head(bound_result)()
    registry = M.Head(M.Tail(bound_result)())()
    built_domain = PG.BuildNatRange(M.one, bound, registry)()
    domain = M.Head(built_domain)()
    registry = M.Head(M.Tail(built_domain)())()
    assert TM.FiniteNatChain(domain, registry)() is M.truth_value
    mined = IM.MineOperationInvariantsAcrossRegister(
        domain, registry, operations, stop_after_first=M.truth_value,
    )()
    findings = M.Head(mined)()
    registry = M.Head(M.Tail(mined)())()
    assert M.IsPair(findings)() is M.truth_value
    finding = M.Head(findings)()
    equation = M.Head(M.Tail(M.Tail(finding)())())()
    lhs = M.Head(M.Tail(M.Tail(equation)())())()
    assert M.Head(lhs)() is L.ExprAddLabel
    assert TM.FiniteNatChain(domain, registry)() is M.truth_value
    executable = OS.ObservedExecutableOperations(operations, registry)()
    started = time.perf_counter()
    checked = OS.ReplayObservedFindings(findings, domain, operations,
        M.Head(M.Tail(executable)())(), registry)()
    assert M.Head(checked)() is M.truth_value
    print("Replay seconds:", time.perf_counter() - started)
    started = time.perf_counter()
    built = OS.BuildObservedStructureBundle(findings, domain, operations, registry)()
    bundle = M.Head(built)()
    registry = M.Head(M.Tail(built)())()
    assert M.IsPair(bundle)() is M.truth_value
    print("Bundle seconds:", time.perf_counter() - started)
    assert M.Head(OS.VerifyObservedStructureBundle(bundle, findings, domain,
        operations, registry)())() is M.truth_value
    print("PASS the real miner's add commutativity on {1..10} builds and verifies a full-catalog bundle")
    print("Observed witness regressions passed.")
