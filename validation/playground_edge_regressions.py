"""Machine-native regressions for playground admission and reporting."""

from hyge import labels as L
from hyge import machine as M
from hyge import playground as PG
from hyge.runtime import make_fresh_runtime


runtime = make_fresh_runtime()
registry = M.FromContextGetConstructors(runtime.graph)()
x = M.Char("x")
y = M.Char("y")
n = M.Char("n")
x_variables = M.Pair(x, M.EmptyList)
y_variables = M.Pair(y, M.EmptyList)
one_tuple = M.Pair(M.one, M.EmptyList)
one_domain = M.Pair(one_tuple, M.EmptyList)
x_environment = PG.ZipEnvironment(x_variables, one_tuple)()

# Both operations in the constraint chain must be available to quantifiers.
x_plus_zero = M.Pair(L.ExprAddLabel, M.Pair(x, M.Pair(M.Zero, M.EmptyList)))
x_times_one = M.Pair(L.ExprMulLabel, M.Pair(x, M.Pair(M.one, M.EmptyList)))
addition_identity = M.Pair(L.ExprEqLabel, M.Pair(x_plus_zero, M.Pair(x, M.EmptyList)))
multiplication_identity = M.Pair(L.ExprEqLabel, M.Pair(x_times_one, M.Pair(x, M.EmptyList)))
mixed_constraints = M.Pair(addition_identity, M.Pair(multiplication_identity, M.EmptyList))
assert M.Head(PG.EvaluateNatConstraints(mixed_constraints, x_environment, registry)())() is M.truth_value
assert M.Head(PG.UniversalQuantify(one_domain, x_variables, mixed_constraints, registry)())() is M.truth_value
assert M.Head(PG.ExistentialQuantify(one_domain, x_variables, mixed_constraints, registry)())() is M.truth_value

# Instantiate returns one result field; the quantifiers retain their registry.
fact = M.Char("present")
derivation_relation = M.Pair(
    L.DerivationRelationLabel,
    M.Pair(M.EmptyList, M.Pair(M.Pair(fact, M.EmptyList),
        M.Pair(fact, M.Pair(M.one, M.Pair(M.false_value, M.EmptyList))))),
)
empty_assignment_domain = M.Pair(M.EmptyList, M.EmptyList)
universal_derivation = PG.UniversalQuantify(
    empty_assignment_domain, M.EmptyList, derivation_relation, registry,
)()
existential_derivation = PG.ExistentialQuantify(
    empty_assignment_domain, M.EmptyList, derivation_relation, registry,
)()
assert M.Head(universal_derivation)() is M.truth_value
assert M.Head(existential_derivation)() is M.truth_value
assert M.Head(M.Tail(universal_derivation)())() is registry
assert M.Head(M.Tail(existential_derivation)())() is registry

# Failed evaluations must not match one another; numeric zero still matches.
zero_tuple = M.Pair(M.Zero, M.EmptyList)
undefined_entry = M.Pair(L.EvaluationEntryLabel, M.Pair(zero_tuple, M.Pair(M.EmptyList, M.EmptyList)))
undefined_tensor = M.Pair(L.EvaluationTensorLabel,
    M.Pair(M.Char("undefined"), M.Pair(M.Pair(undefined_entry, M.EmptyList), M.EmptyList)))
assert M.Head(PG.FindTensorEqualityWitness(
    undefined_tensor, undefined_tensor, x_variables, y_variables, M.false_value, registry,
)())() is M.EmptyList
zero_entry = M.Pair(L.EvaluationEntryLabel, M.Pair(zero_tuple, M.Pair(M.Zero, M.EmptyList)))
zero_tensor = M.Pair(L.EvaluationTensorLabel,
    M.Pair(M.Char("zero"), M.Pair(M.Pair(zero_entry, M.EmptyList), M.EmptyList)))
zero_witness = M.Head(PG.FindTensorEqualityWitness(
    zero_tensor, zero_tensor, x_variables, y_variables, M.false_value, registry,
)())()
assert M.IsPair(zero_witness)() is M.truth_value
assert M.NatEq(PG.EnvLookup(zero_witness, x)(), M.Zero, registry)() is M.truth_value
assert M.NatEq(PG.EnvLookup(zero_witness, y)(), M.Zero, registry)() is M.truth_value
assert M.Head(PG.FindTensorEqualityWitness(
    undefined_tensor, zero_tensor, x_variables, y_variables, M.false_value, registry,
)())() is M.EmptyList

# Surface punctuation and grouping preserve the submitted proposition.
unequal_spec = PG.ParseSurfaceGoalSpec(M.Char("x != x"), registry)()
assert M.IsPair(unequal_spec)() is M.truth_value
assert PG.GoalSpecNoSolutions(unequal_spec)() is M.truth_value
equal_spec = PG.ParseSurfaceGoalSpec(M.Char("x = x"), registry)()
assert PG.GoalSpecNoSolutions(equal_spec)() is M.false_value
grouped_spec = PG.ParseSurfaceGoalSpec(M.Char("(x + y) = z"), registry)()
assert M.IsPair(grouped_spec)() is M.truth_value
registry = PG.GoalSpecRegistry(grouped_spec)()
assert M.Compare(M.Char(PG.RenderNatExpr(PG.GoalSpecLhs(grouped_spec)(), registry)()), M.Char("x + y"))() is M.truth_value
compound_exponent = M.Pair(L.ExprAddLabel, M.Pair(y, M.Pair(M.one, M.EmptyList)))
power = M.Pair(L.ExprPowLabel, M.Pair(x, M.Pair(compound_exponent, M.EmptyList)))
assert M.Compare(M.Char(PG.RenderNatExpr(power, registry)()), M.Char("x^(y + 1)"))() is M.truth_value

# Improper argument chains and constraint tails are refused before traversal.
malformed_expression = M.Pair(L.ExprAddLabel, M.Pair(x, y))
identity_result = PG.PolynomialIdentityByGrid(malformed_expression, x, x_variables, registry)()
identity_record = M.Head(identity_result)()
registry = M.Head(M.Tail(identity_result)())()
assert M.Head(PG.TupleElementAt(M.Tail(identity_record)(), M.five, registry)())() is M.EmptyList
assert M.Head(PG.EvaluateNatExpr(malformed_expression, x_environment, registry)())() is M.EmptyList
malformed_constant = M.Pair(L.ExprIntLabel, M.EmptyList)
assert M.Head(PG.EvaluateNatExpr(malformed_constant, x_environment, registry)())() is M.EmptyList
assert M.Compare(M.Char(PG.RenderNatExpr(malformed_constant, registry)()), M.Char("?"))() is M.truth_value
malformed_constraints = M.Pair(addition_identity, x)
malformed_search = PG.FindNatWitness(malformed_constraints, x_variables, M.two, M.two, registry)()
malformed_record = M.Head(malformed_search)()
assert M.Head(PG.TupleElementAt(M.Tail(malformed_record)(), M.four, registry)())() is L.NatWitnessInvalidLabel
assert M.Head(PG.EvaluateNatConstraints(malformed_constraints, x_environment, registry)())() is M.EmptyList
assert PG.ValidNatConstraints(M.Pair(x, M.EmptyList), x_variables, registry)() is M.false_value
short_constraint = M.Pair(L.ExprEqLabel, M.Pair(x, M.EmptyList))
assert M.Head(PG.EvaluateNatConstraints(M.Pair(short_constraint, M.EmptyList), x_environment, registry)())() is M.EmptyList

# Modulo zero refuses both direct verification and bounded witness search.
modulo_zero = M.Pair(L.NatModEqLabel, M.Pair(M.one, M.Pair(M.Zero, M.Pair(M.Zero, M.EmptyList))))
modulo_constraints = M.Pair(modulo_zero, M.EmptyList)
assert M.Head(PG.EvaluateNatConstraints(modulo_constraints, M.EmptyList, registry)())() is M.EmptyList
assert M.Head(PG.VerifyNatWitness(modulo_constraints, M.EmptyList, M.one, M.EmptyList, registry)())() is M.EmptyList
modulo_search = PG.FindNatWitness(modulo_constraints, M.EmptyList, M.one, M.one, registry)()
modulo_record = M.Head(modulo_search)()
registry = M.Head(M.Tail(modulo_search)())()
assert M.Head(PG.TupleElementAt(M.Tail(modulo_record)(), M.four, registry)())() is L.NatWitnessInvalidLabel

# A rejected parameter domain stays empty instead of inserting rejected values.
n_above_nine = M.Pair(L.ExprLtLabel, M.Pair(M.nine, M.Pair(n, M.EmptyList)))
rejected_parameters = PG.FilterCandidateParameters(n, M.Pair(n_above_nine, M.EmptyList), registry)()
assert M.Head(rejected_parameters)() is M.EmptyList
registry = M.Head(M.Tail(rejected_parameters)())()
n_above_two = M.Pair(L.ExprLtLabel, M.Pair(M.two, M.Pair(n, M.EmptyList)))
accepted_parameters = PG.FilterCandidateParameters(n, M.Pair(n_above_two, M.EmptyList), registry)()
registry = M.Head(M.Tail(accepted_parameters)())()
assert M.Compare(M.Char(PG.FormatSetChain(M.Head(accepted_parameters)(), registry)()), M.Char("{3, 4}"))() is M.truth_value

# Both report formats distinguish a found assignment from an empty search.
moduli = M.Pair(M.two, M.EmptyList)
domain = M.Pair(M.Zero, M.Pair(M.one, M.EmptyList))
empty_domain_report = PG.FormatDiscoveriesReport(
    x, x, M.EmptyList, moduli, M.two, M.EmptyList, M.false_value, registry,
    domain_chain=domain,
)()
assert M.Compare(M.Char(empty_domain_report), M.Char(
    "  - Ground Tensor Witness Search (domain {0, 1}): 0 solutions in ground tensor; sweeping moduli {2}."
    "\n  - across moduli {2}: no proper residue restriction found."
))() is M.truth_value
found_domain_report = PG.FormatDiscoveriesReport(
    x, x, M.EmptyList, moduli, M.two, x_environment, M.false_value, registry,
    domain_chain=domain,
)()
assert M.Compare(M.Char(found_domain_report), M.Char(
    "  - Ground Tensor Witness (domain {0, 1}): Counterexample solution found at (x = 1) where x = x."
    "\n  - across moduli {2}: no proper residue restriction found."
))() is M.truth_value
empty_range_report = PG.FormatDiscoveriesReport(
    x, x, M.EmptyList, moduli, M.two, M.EmptyList, M.false_value, registry,
)()
assert M.Compare(M.Char(empty_range_report), M.Char(
    "  - Ground Tensor Witness Search (domain 0..1): 0 solutions in ground tensor; sweeping moduli {2}."
    "\n  - across moduli {2}: no proper residue restriction found."
))() is M.truth_value
found_range_report = PG.FormatDiscoveriesReport(
    x, x, M.EmptyList, moduli, M.two, x_environment, M.false_value, registry,
)()
assert M.Compare(M.Char(found_range_report), M.Char(
    "  - Ground Tensor Witness (0..1): Counterexample solution found at (x = 1) where x = x."
    "\n  - across moduli {2}: no proper residue restriction found."
))() is M.truth_value

print("Playground edge regressions passed.")
