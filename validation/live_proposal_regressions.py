"""Live proposals stop at one complete unrecorded finite observation."""

from hyge import invariant_miner as IM
from hyge import labels as L
from hyge import machine as M
from hyge import playground as PG
from hyge.runtime import make_fresh_runtime


runtime = make_fresh_runtime()
registry = M.FromContextGetConstructors(runtime.graph)()
catalog = M.Head(PG.BuildNatOperationRegister(registry)())()
addition = PG.LookupOperationByLabel(L.ExprAddLabel, catalog)()
power = PG.LookupOperationByLabel(L.ExprPowLabel, catalog)()
additions = M.Pair(addition, M.EmptyList)
powers = M.Pair(power, M.EmptyList)
domain = M.Pair(M.one, M.Pair(M.two, M.EmptyList))
x = M.Char("x")
y = M.Char("y")
z = M.Char("z")
variables = M.Pair(x, M.Pair(y, M.EmptyList))
commutative = M.Pair(L.DiscoveredEquationLabel,
    M.Pair(variables,
        M.Pair(M.Pair(L.ExprAddLabel, M.Pair(x, M.Pair(y, M.EmptyList))),
            M.Pair(M.Pair(L.ExprAddLabel, M.Pair(y, M.Pair(x, M.EmptyList))), M.EmptyList))))

# A later register sentinel has no operation fields. Returning a law before
# touching it proves that the live path does not continue its batch scan.
proposal = IM.ProposeNextRegularityOrStructure(
    M.Pair(addition, M.Pair(M.EmptyList, M.EmptyList)), domain, M.EmptyList, registry,
)()
assert M.Head(proposal)() is L.ObservedRegularityLabel
finding = M.Head(M.Tail(proposal)())()
registry = M.Head(M.Tail(M.Tail(proposal)())())()
body = M.Tail(finding)()
equation_body = M.Tail(body)()
equation = M.Head(equation_body)()
assert M.Compare(equation, commutative)() is M.truth_value
witness_body = M.Tail(M.Tail(equation_body)())()
witnesses = M.Head(witness_body)()
counted = PG.ChainLength(witnesses, registry)()
registry = M.Head(M.Tail(counted)())()
assert M.NatEq(M.Head(counted)(), M.four, registry)() is M.truth_value
assert M.Compare(M.Head(M.Tail(M.Head(M.Tail(witness_body)())())())(), domain)() is M.truth_value

# Naming the first law removes it before tensor evaluation. The next proposal
# is a three-variable association law, checked at all eight assignments.
named = M.Pair(L.NamedRegularityLabel,
    M.Pair(M.Char("exchange"), M.Pair(M.Head(body)(),
        M.Pair(equation, M.Pair(domain, M.Pair(witnesses, M.EmptyList))))))
proposal = IM.ProposeNextRegularityOrStructure(
    additions, domain, M.Pair(named, M.EmptyList), registry,
)()
assert M.Head(proposal)() is L.ObservedRegularityLabel
second = M.Head(M.Tail(proposal)())()
registry = M.Head(M.Tail(M.Tail(proposal)())())()
second_equation_body = M.Tail(M.Tail(second)())()
second_equation = M.Head(second_equation_body)()
associative = M.Pair(L.DiscoveredEquationLabel,
    M.Pair(M.Pair(x, M.Pair(y, M.Pair(z, M.EmptyList))),
        M.Pair(M.Pair(L.ExprAddLabel,
            M.Pair(x, M.Pair(M.Pair(L.ExprAddLabel, M.Pair(y, M.Pair(z, M.EmptyList))), M.EmptyList))),
            M.Pair(M.Pair(L.ExprAddLabel,
                M.Pair(M.Pair(L.ExprAddLabel, M.Pair(x, M.Pair(y, M.EmptyList))), M.Pair(z, M.EmptyList))),
                M.EmptyList))))
assert M.Compare(second_equation, associative)() is M.truth_value
second_witnesses = M.Head(M.Tail(M.Tail(second_equation_body)())())()
counted = PG.ChainLength(second_witnesses, registry)()
registry = M.Head(M.Tail(counted)())()
assert M.NatEq(M.Head(counted)(), M.eight, registry)() is M.truth_value

# A named structural sentinel has no equation fields. Removing it before the
# checker reaches the chain demonstrates skip-before-evaluation directly.
sentinel = M.Atom()
sentinel_record = M.Pair(L.NamedRegularityLabel,
    M.Pair(M.Char("already recorded"), M.Pair(M.Char("add"),
        M.Pair(sentinel, M.Pair(domain, M.Pair(M.EmptyList, M.EmptyList))))))
unnamed = IM.UnnamedOperationEquations(
    M.Char("add"), M.Pair(sentinel, M.Pair(commutative, M.EmptyList)), domain,
    M.Pair(sentinel_record, M.EmptyList),
)()
assert M.Compare(unnamed, M.Pair(commutative, M.EmptyList))() is M.truth_value
built = PG.BuildOperationTensorState(domain, additions, registry, additions)()
tensor = M.Head(built)()
registry = M.Head(M.Tail(built)())()
checked = IM.CheckOperationEquationCandidates(
    M.Char("add"), unnamed, variables, domain, registry, additions, tensor,
    M.EmptyList, M.truth_value,
)()
assert M.IsPair(M.Head(checked)())() is M.truth_value
registry = M.Head(M.Tail(checked)())()

# The candidate checker also stops before an unrecorded sentinel after its
# first completed law. This checks the inner recursion independently.
checked = IM.CheckOperationEquationCandidates(
    M.Char("add"), M.Pair(commutative, M.Pair(sentinel, M.EmptyList)), variables,
    domain, registry, additions, tensor, M.EmptyList, M.truth_value,
)()
assert M.IsPair(M.Head(checked)())() is M.truth_value
assert M.Tail(M.Head(checked)())() is M.EmptyList
registry = M.Head(M.Tail(checked)())()

# Empty carriers and refuted candidate sets do not become observed laws.
proposal = IM.ProposeNextRegularityOrStructure(powers, M.EmptyList, M.EmptyList, registry)()
assert M.Head(proposal)() is M.EmptyList
assert M.Head(M.Tail(proposal)())() is M.EmptyList
assert M.Head(M.Tail(M.Tail(proposal)())())() is registry
proposal = IM.ProposeNextRegularityOrStructure(powers, domain, M.EmptyList, registry)()
assert M.Head(proposal)() is M.EmptyList
assert M.Head(M.Tail(proposal)())() is M.EmptyList
registry = M.Head(M.Tail(M.Tail(proposal)())())()

# Exhausting the unrecorded laws still reaches structure synthesis. A fully
# named candidate set does not rebuild the tensor or change its registry.
singleton = M.Pair(M.one, M.EmptyList)
proposal = IM.ProposeNextRegularityOrStructure(powers, singleton, M.EmptyList, registry)()
assert M.Head(proposal)() is L.ObservedRegularityLabel
power_finding = M.Head(M.Tail(proposal)())()
registry = M.Head(M.Tail(M.Tail(proposal)())())()
power_body = M.Tail(power_finding)()
power_equation_body = M.Tail(power_body)()
power_witnesses = M.Head(M.Tail(M.Tail(power_equation_body)())())()
named_power = M.Pair(L.NamedRegularityLabel,
    M.Pair(M.Char("singleton power exchange"), M.Pair(M.Head(power_body)(),
        M.Pair(M.Head(power_equation_body)(), M.Pair(singleton, M.Pair(power_witnesses, M.EmptyList))))))
proposal = IM.ProposeNextRegularityOrStructure(
    powers, singleton, M.Pair(named_power, M.EmptyList), registry,
)()
assert M.Head(proposal)() is L.AlgebraicTemplateLabel
assert M.Head(M.Tail(M.Tail(proposal)())())() is registry
template = M.Head(M.Tail(proposal)())()
named_structure = M.Pair(L.NamedStructureLabel,
    M.Pair(M.Char("singleton structure"), M.Pair(template, M.EmptyList)))
proposal = IM.ProposeNextRegularityOrStructure(
    powers, singleton, M.Pair(named_structure, M.Pair(named_power, M.EmptyList)), registry,
)()
assert M.Head(proposal)() is M.EmptyList
assert M.Head(M.Tail(M.Tail(proposal)())())() is registry

# A tiny supplied corpus bounds both operation profiles to two variables.
# Default and explicit batch modes retain both findings, in register order;
# the optional first mode yields only the first member of that same corpus.
bounded_addition = M.Pair(M.Char("add"),
    M.Pair(variables, M.Pair(M.Pair(L.ExprAddLabel, variables),
        M.Pair(M.Char(" + "), M.Pair(M.two, M.Pair(M.truth_value,
            M.Pair(M.Char("max"), M.Pair(M.Char("expensive"), M.EmptyList))))))))
bounded_multiplication = M.Pair(M.Char("mul"),
    M.Pair(variables, M.Pair(M.Pair(L.ExprMulLabel, variables),
        M.Pair(M.Char("*"), M.Pair(M.three, M.Pair(M.truth_value,
            M.Pair(M.Char("sum"), M.Pair(M.Char("expensive"), M.EmptyList))))))))
corpus = M.Pair(bounded_addition, M.Pair(bounded_multiplication, M.EmptyList))
batch = IM.MineOperationInvariantsAcrossRegister(singleton, registry, corpus)()
batch_findings = M.Head(batch)()
registry = M.Head(M.Tail(batch)())()
assert M.IsPair(batch_findings)() is M.truth_value
assert M.IsPair(M.Tail(batch_findings)())() is M.truth_value
assert M.Tail(M.Tail(batch_findings)())() is M.EmptyList
assert M.Compare(M.Head(M.Tail(M.Head(batch_findings)())())(), M.Char("add"))() is M.truth_value
assert M.Compare(M.Head(M.Tail(M.Head(M.Tail(batch_findings)())())())(), M.Char("mul"))() is M.truth_value
explicit_batch = IM.MineOperationInvariantsAcrossRegister(
    singleton, registry, corpus, M.EmptyList, M.false_value,
)()
assert M.Compare(M.Head(explicit_batch)(), batch_findings)() is M.truth_value
registry = M.Head(M.Tail(explicit_batch)())()
first = IM.MineOperationInvariantsAcrossRegister(
    singleton, registry, corpus, M.EmptyList, M.truth_value,
)()
assert M.Compare(M.Head(first)(), M.Pair(M.Head(batch_findings)(), M.EmptyList))() is M.truth_value

print("Live proposal regressions passed: complete first law, named skipping, short-circuit sentinels, safe exhaustion, and unchanged batch findings.")
