"""Compare stored tensor cells with direct evaluation, including refusals."""

from hyge import labels as L
from hyge import invariant_miner as IM
from hyge import machine as M
from hyge import playground as PG
from hyge.math import arithmetic as A
from hyge.runtime import make_fresh_runtime


class VerifyTensorAxes(M.Edge):
    def __init__(self, tensor, label, variables, domain, remaining, point, registry, operations):
        if M.IdentityCompare(variables, M.EmptyList)() is M.truth_value:
            term = M.Pair(label, point)
            cached = PG.TensorOperationValue(tensor, term, M.EmptyList, registry)()
            direct = PG.EvaluateNatExpr(term, M.EmptyList, registry, operations)()
            registry = M.Head(M.Tail(direct)())()
            expected = M.Head(direct)()
            if A.IsNat(expected, registry)() is M.truth_value:
                assert M.NatEq(M.Head(cached)(), expected, registry)() is M.truth_value
            else:
                assert M.Head(cached)() is expected
        elif M.IsPair(remaining)() is M.truth_value:
            registry = VerifyTensorAxes(
                tensor, label, M.Tail(variables)(), domain, domain,
                PG.ChainAppendEnd(point, M.Head(remaining)())(), registry, operations,
            )()
            registry = VerifyTensorAxes(
                tensor, label, variables, domain, M.Tail(remaining)(), point, registry, operations,
            )()
        super().__init__(inputs=M.Pair(tensor, M.Pair(label, point)), results=registry)


class VerifyTensorOperations(M.Edge):
    def __init__(self, tensor, remaining, domain, registry, operations):
        if M.IsPair(remaining)() is M.truth_value:
            entry = M.Head(remaining)()
            variables = M.Head(M.Tail(entry)())()
            label = M.Head(M.Head(M.Tail(M.Tail(entry)())())())()
            axis_domain = domain
            if M.IdentityCompare(label, L.ImpliesLabel)() is M.truth_value:
                axis_domain = M.Pair(M.false_value, M.Pair(M.truth_value, M.EmptyList))
            registry = VerifyTensorAxes(
                tensor, label, variables, axis_domain, axis_domain, M.EmptyList, registry, operations,
            )()
            registry = VerifyTensorOperations(
                tensor, M.Tail(remaining)(), domain, registry, operations,
            )()
        super().__init__(inputs=M.Pair(tensor, remaining), results=registry)


runtime = make_fresh_runtime()
registry = M.FromContextGetConstructors(runtime.graph)()
operations = M.Head(PG.BuildNatOperationRegister(registry)())()
domain = M.Pair(M.Zero, M.Pair(M.one, M.Pair(M.two, M.EmptyList)))
selected = M.Pair(PG.LookupOperationByLabel(L.ExprNegLabel, operations)(),
    M.Pair(PG.LookupOperationByLabel(L.ExprAddLabel, operations)(),
        M.Pair(PG.LookupOperationByLabel(L.NatModEqLabel, operations)(),
            M.Pair(PG.LookupOperationByLabel(L.DividesLabel, operations)(),
                M.Pair(PG.LookupOperationByLabel(L.ImpliesLabel, operations)(), M.EmptyList)))))
built = PG.BuildOperationTensorState(domain, selected, registry, operations)()
tensor = M.Head(built)()
registry = M.Head(M.Tail(built)())()
registry = VerifyTensorOperations(tensor, selected, domain, registry, operations)()
print("PASS all 52 unary, binary, ternary and implication cells agree with direct evaluation")

# Equal naturals may be distinct atoms, including after construction or restore.
alias = M.ConstructedBy(M.Atom(), L.SuccLabel, M.Pair(M.one, M.EmptyList), registry)()
alias_two = M.Head(alias)()
registry = M.Head(M.Tail(alias)())()
assert alias_two is not M.two
term = M.Pair(L.ExprAddLabel, M.Pair(alias_two, M.Pair(M.two, M.EmptyList)))
assert M.NatEq(M.Head(PG.TensorOperationValue(tensor, term, M.EmptyList, registry)())(), M.four, registry)() is M.truth_value
x = M.Char("x")
environment = PG.ZipEnvironment(M.Pair(x, M.EmptyList), M.Pair(alias_two, M.EmptyList))()
term = M.Pair(L.ExprAddLabel, M.Pair(x, M.Pair(M.two, M.EmptyList)))
assert M.NatEq(M.Head(PG.TensorOperationValue(tensor, term, environment, registry)())(), M.four, registry)() is M.truth_value
inner = M.Pair(L.ExprAddLabel, M.Pair(M.one, M.Pair(M.one, M.EmptyList)))
term = M.Pair(L.ExprAddLabel, M.Pair(inner, M.Pair(M.Zero, M.EmptyList)))
assert M.NatEq(M.Head(PG.TensorOperationValue(tensor, term, M.EmptyList, registry)())(), M.two, registry)() is M.truth_value
print("PASS natural aliases, variable bindings and nested cached operations")

# No axis prefix, extra coordinate, missing coordinate, or missing operation is a cell.
short = M.Pair(L.ExprAddLabel, M.Pair(M.one, M.EmptyList))
long = M.Pair(L.ExprAddLabel, M.Pair(M.one, M.Pair(M.one, M.Pair(M.one, M.EmptyList))))
improper = M.Pair(L.ExprAddLabel, M.Pair(M.one, M.two))
outside = M.Pair(L.ExprAddLabel, M.Pair(M.three, M.Pair(M.one, M.EmptyList)))
missing = M.Pair(L.ExprGcdLabel, M.Pair(M.one, M.Pair(M.one, M.EmptyList)))
assert M.Head(PG.TensorOperationValue(tensor, short, M.EmptyList, registry)())() is M.EmptyList
assert M.Head(PG.TensorOperationValue(tensor, long, M.EmptyList, registry)())() is M.EmptyList
assert M.Head(PG.TensorOperationValue(tensor, improper, M.EmptyList, registry)())() is M.EmptyList
assert M.Head(PG.TensorOperationValue(tensor, outside, M.EmptyList, registry)())() is M.EmptyList
assert M.Head(PG.TensorOperationValue(tensor, missing, M.EmptyList, registry)())() is M.EmptyList
empty = PG.BuildOperationTensorState(M.EmptyList, selected, registry, operations)()
term = M.Pair(L.ExprAddLabel, M.Pair(M.one, M.Pair(M.one, M.EmptyList)))
assert M.Head(PG.TensorOperationValue(M.Head(empty)(), term, M.EmptyList, registry)())() is M.EmptyList
print("PASS malformed, missing and out-of-domain cells are refused")

# A rejected arithmetic argument must not become a false predicate result.
bad_divides = M.Pair(L.DividesLabel, M.Pair(M.one, M.Pair(M.truth_value, M.EmptyList)))
bad_less = M.Pair(L.ExprLtLabel, M.Pair(M.false_value, M.Pair(M.one, M.EmptyList)))
bad_modulo = M.Pair(L.NatModEqLabel,
    M.Pair(M.one, M.Pair(M.two, M.Pair(M.truth_value, M.EmptyList))))
bad_implication = M.Pair(L.ImpliesLabel, M.Pair(M.one, M.Pair(M.two, M.EmptyList)))
assert M.Head(PG.EvaluateNatExpr(bad_divides, M.EmptyList, registry, operations)())() is M.EmptyList
assert M.Head(PG.EvaluateNatExpr(bad_less, M.EmptyList, registry, operations)())() is M.EmptyList
assert M.Head(PG.EvaluateNatExpr(bad_modulo, M.EmptyList, registry, operations)())() is M.EmptyList
assert M.Head(PG.EvaluateNatExpr(bad_implication, M.EmptyList, registry, operations)())() is M.EmptyList
assert M.Head(PG.TensorOperationValue(tensor, bad_divides, M.EmptyList, registry)())() is M.EmptyList
assert M.Head(PG.TensorOperationValue(tensor, bad_implication, M.EmptyList, registry)())() is M.EmptyList
invalid_equation = M.Pair(L.DiscoveredEquationLabel,
    M.Pair(M.EmptyList, M.Pair(bad_divides, M.Pair(bad_divides, M.EmptyList))))
invalid_check = IM.CheckOperationEquationPoint(
    invalid_equation, M.EmptyList, M.EmptyList, registry, operations, tensor, M.EmptyList,
)()
assert M.Head(invalid_check)() is M.false_value
assert M.Head(M.Tail(M.Tail(invalid_check)())())() is M.EmptyList
print("PASS invalid predicate arguments cannot supply evidence of an equation")
print("Discovery tensor axes regressions passed.")
