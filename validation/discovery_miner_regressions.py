"""Machine-native regression checks for finite operation discovery reuse."""

from hyge import invariant_miner as IM
from hyge import labels as L
from hyge import machine as M
from hyge import playground as PG
from hyge.runtime import make_fresh_runtime


class NamedFindingRecords(M.Edge):
    def __init__(self, findings):
        result = M.EmptyList
        if M.IsPair(findings)() is M.truth_value:
            body = M.Tail(M.Head(findings)())()
            operation = M.Head(body)()
            equation_body = M.Tail(body)()
            equation = M.Head(equation_body)()
            witness_body = M.Tail(M.Tail(equation_body)())()
            witnesses = M.Head(witness_body)()
            scope = M.Head(M.Tail(witness_body)())()
            domain = M.Head(M.Tail(scope)())()
            named = M.Pair(L.NamedRegularityLabel,
                M.Pair(M.Char("recorded observation"), M.Pair(operation,
                    M.Pair(equation, M.Pair(domain, M.Pair(witnesses, M.EmptyList))))))
            result = M.Pair(named, NamedFindingRecords(M.Tail(findings)())())
        super().__init__(inputs=M.Pair(findings, M.EmptyList), results=result)


class FindingForOperation(M.Edge):
    def __init__(self, findings, operation):
        result = M.EmptyList
        if M.IsPair(findings)() is M.truth_value:
            finding = M.Head(findings)()
            if M.Compare(M.Head(M.Tail(finding)())(), operation)() is M.truth_value:
                result = finding
            else:
                result = FindingForOperation(M.Tail(findings)(), operation)()
        super().__init__(inputs=M.Pair(findings, M.Pair(operation, M.EmptyList)), results=result)


runtime = make_fresh_runtime()
registry = M.FromContextGetConstructors(runtime.graph)()
catalog = M.Head(PG.BuildNatOperationRegister(registry)())()
addition = PG.LookupOperationByLabel(L.ExprAddLabel, catalog)()
additions = M.Pair(addition, M.EmptyList)
domain = M.Pair(M.Zero, M.Pair(M.one, M.EmptyList))

mined = IM.MineOperationInvariantsAcrossRegister(domain, registry, additions)()
findings = M.Head(mined)()
registry = M.Head(M.Tail(mined)())()
assert M.IsPair(findings)() is M.truth_value
named = NamedFindingRecords(findings)()

# Fully named candidate sets leave the registry object untouched: no grid rebuild.
repeated = IM.MineOperationInvariantsAcrossRegister(domain, registry, additions, named)()
assert M.Head(repeated)() is M.EmptyList
assert M.Head(M.Tail(repeated)())() is registry

equation = M.Head(M.Tail(M.Tail(M.Head(findings)())())())()
assert IM.NamedOperationEquation(M.Char("add"), equation, domain, named)() is M.truth_value
different_domain = M.Pair(M.one, M.Pair(M.two, M.EmptyList))
assert IM.NamedOperationEquation(M.Char("add"), equation, different_domain, named)() is M.false_value
new_scope = IM.MineOperationInvariantsAcrossRegister(different_domain, registry, additions, named)()
assert M.IsPair(M.Head(new_scope)())() is M.truth_value
registry = M.Head(M.Tail(new_scope)())()

# Unary and ternary descriptions do not break the binary equation grammar.
other_arities = M.Pair(PG.LookupOperationByLabel(L.ExprNegLabel, catalog)(),
    M.Pair(PG.LookupOperationByLabel(L.NatModEqLabel, catalog)(), M.EmptyList))
skipped = IM.MineOperationInvariantsAcrossRegister(domain, registry, other_arities)()
assert M.Head(skipped)() is M.EmptyList
assert M.Head(M.Tail(skipped)())() is registry

# No evidence is produced from an empty finite carrier.
empty_scan = IM.MineOperationInvariantsAcrossRegister(M.EmptyList, registry, additions)()
assert M.Head(empty_scan)() is M.EmptyList

# The actual mixed-operation mining route must propose x|y => x|(y*z).
domain = M.Pair(M.Zero, M.Pair(M.one, M.Pair(M.two, M.EmptyList)))
relational_ops = M.Pair(PG.LookupOperationByLabel(L.DividesLabel, catalog)(),
    M.Pair(PG.LookupOperationByLabel(L.ExprMulLabel, catalog)(),
        M.Pair(PG.LookupOperationByLabel(L.ImpliesLabel, catalog)(), M.EmptyList)))
relational = IM.MineOperationInvariantsAcrossRegister(domain, registry, relational_ops)()
registry = M.Head(M.Tail(relational)())()
propagation = FindingForOperation(M.Head(relational)(), M.Char("divisibility propagation"))()
assert M.IsPair(propagation)() is M.truth_value
propagation_equation = M.Head(M.Tail(M.Tail(propagation)())())()
x = M.Char("x")
y = M.Char("y")
z = M.Char("z")
variables = M.Pair(x, M.Pair(y, M.Pair(z, M.EmptyList)))
antecedent = M.Pair(L.DividesLabel, M.Pair(x, M.Pair(y, M.EmptyList)))
product = M.Pair(L.ExprMulLabel, M.Pair(y, M.Pair(z, M.EmptyList)))
conclusion = M.Pair(L.DividesLabel, M.Pair(x, M.Pair(product, M.EmptyList)))
implication = M.Pair(L.ImpliesLabel, M.Pair(antecedent, M.Pair(conclusion, M.EmptyList)))
expected = M.Pair(L.DiscoveredEquationLabel,
    M.Pair(variables, M.Pair(implication, M.Pair(M.truth_value, M.EmptyList))))
assert M.Compare(propagation_equation, expected)() is M.truth_value

# One three-coordinate law traverses all 1,000 assignments without product-depth recursion.
bound_result = M.NatFromRep(M.GMPRep(10), registry)()
bound = M.Head(bound_result)()
registry = M.Head(M.Tail(bound_result)())()
range_result = PG.BuildNatRange(M.one, bound, registry)()
large_domain = M.Head(range_result)()
registry = M.Head(M.Tail(range_result)())()
left = M.Pair(L.ExprAddLabel,
    M.Pair(M.Pair(L.ExprAddLabel, M.Pair(x, M.Pair(y, M.EmptyList))), M.Pair(z, M.EmptyList)))
right = M.Pair(L.ExprAddLabel,
    M.Pair(x, M.Pair(M.Pair(L.ExprAddLabel, M.Pair(y, M.Pair(z, M.EmptyList))), M.EmptyList)))
associative = M.Pair(L.DiscoveredEquationLabel,
    M.Pair(variables, M.Pair(left, M.Pair(right, M.EmptyList))))
tensor_result = PG.BuildOperationTensorState(large_domain, additions, registry, additions)()
tensor = M.Head(tensor_result)()
registry = M.Head(M.Tail(tensor_result)())()
large_check = IM.CheckOperationEquationDomain(
    associative, variables, variables, large_domain, large_domain, M.EmptyList,
    registry, additions, tensor, M.EmptyList,
)()
assert M.Head(large_check)() is M.truth_value
assert M.IsPair(M.Head(M.Tail(M.Tail(large_check)())())())() is M.truth_value
print("Discovery miner regressions passed.")
