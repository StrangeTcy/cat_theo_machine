"""Indexed tensor regressions for arithmetic, predicates, and three axes."""

from hyge import labels as L
from hyge import machine as M
from hyge import playground as PG
from hyge.runtime import make_fresh_runtime


runtime = make_fresh_runtime()
registry = M.FromContextGetConstructors(runtime.graph)()
operations = M.Head(PG.BuildNatOperationRegister(registry)())()
domain = M.Pair(M.Zero, M.Pair(M.one, M.Pair(M.two, M.EmptyList)))
add = PG.LookupOperationByLabel(L.ExprAddLabel, operations)()
modulo = PG.LookupOperationByLabel(L.NatModEqLabel, operations)()
implies = PG.LookupOperationByLabel(L.ImpliesLabel, operations)()
selected = M.Pair(add, M.Pair(modulo, M.Pair(implies, M.EmptyList)))
built = PG.BuildOperationTensorState(domain, selected, registry, operations)()
tensor = M.Head(built)()
registry = M.Head(M.Tail(built)())()

sum_term = M.Pair(L.ExprAddLabel, M.Pair(M.two, M.Pair(M.two, M.EmptyList)))
value = M.Head(PG.TensorOperationValue(tensor, sum_term, M.EmptyList, registry)())()
assert M.NatEq(value, M.four, registry)() is M.truth_value
modulo_term = M.Pair(L.NatModEqLabel,
    M.Pair(M.two, M.Pair(M.two, M.Pair(M.Zero, M.EmptyList))))
assert M.Head(PG.TensorOperationValue(tensor, modulo_term, M.EmptyList, registry)())() is M.truth_value
false_modulo = M.Pair(L.NatModEqLabel,
    M.Pair(M.two, M.Pair(M.two, M.Pair(M.one, M.EmptyList))))
assert M.Head(PG.TensorOperationValue(tensor, false_modulo, M.EmptyList, registry)())() is M.false_value
undefined_modulo = M.Pair(L.NatModEqLabel,
    M.Pair(M.two, M.Pair(M.Zero, M.Pair(M.Zero, M.EmptyList))))
assert M.Head(PG.TensorOperationValue(tensor, undefined_modulo, M.EmptyList, registry)())() is M.EmptyList

implication = M.Pair(L.ImpliesLabel,
    M.Pair(modulo_term, M.Pair(false_modulo, M.EmptyList)))
assert M.Head(PG.TensorOperationValue(tensor, implication, M.EmptyList, registry)())() is M.false_value
assert M.Head(PG.TensorOperationValue(tensor, M.truth_value, M.EmptyList, registry)())() is M.truth_value
assert M.Head(PG.TensorOperationValue(tensor, M.false_value, M.EmptyList, registry)())() is M.false_value
malformed = M.Pair(L.ExprAddLabel, M.Pair(M.one, M.two))
assert M.Head(PG.TensorOperationValue(tensor, malformed, M.EmptyList, registry)())() is M.EmptyList

# A thousand ternary rows must fit without one Python frame per row.
ten_result = M.NatFromRep(M.GMPRep(10), registry)()
ten = M.Head(ten_result)()
registry = M.Head(M.Tail(ten_result)())()
range_result = PG.BuildNatRange(M.one, ten, registry)()
large_domain = M.Head(range_result)()
registry = M.Head(M.Tail(range_result)())()
large_built = PG.BuildOperationTensorState(
    large_domain, M.Pair(modulo, M.EmptyList), registry, operations,
)()
registry = M.Head(M.Tail(large_built)())()
last_cell = M.Pair(L.NatModEqLabel, M.Pair(ten, M.Pair(ten, M.Pair(ten, M.EmptyList))))
assert M.Head(PG.TensorOperationValue(
    M.Head(large_built)(), last_cell, M.EmptyList, registry,
)())() is M.false_value

print("Discovery tensor regressions passed.")
