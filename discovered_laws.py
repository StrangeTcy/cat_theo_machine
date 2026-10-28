"""Certify named polynomial observations before admitting rewrite rules."""

from . import checker_b as CB
from . import labels as L
from . import machine as M
from . import playground as PG
from . import proof as P


class CertifyDiscoveredEquation(M.Edge):
    """Return rule, derivation, verification, and registry as a machine chain.

    A sampled identity is admitted only when the polynomial decision
    procedure proves it universally and Checker B independently replays that
    proof under the caller's explicit decision-procedure authority.
    Unsupported or refuted equations return no active rule.
    """

    def __init__(self, equation, trusted_rules, registry):
        input_registry = registry
        rule = M.EmptyList
        derivation = M.EmptyList
        verification = M.EmptyList
        if M.IsPair(equation)() is M.truth_value:
            if M.IdentityCompare(
                M.Head(equation)(), L.DiscoveredEquationLabel
            )() is M.truth_value:
                fields = M.Tail(equation)()
                if PG.ExactArity(fields, M.three, registry)() is M.truth_value:
                    variables = M.Head(fields)()
                    lhs = M.Head(M.Tail(fields)())()
                    rhs = M.Head(M.Tail(M.Tail(fields)())())()
                    certified = PG.PolynomialGridDerivation(
                        lhs, rhs, variables, registry
                    )()
                    derivation = M.Head(M.Tail(certified)())()
                    registry = M.Head(M.Tail(M.Tail(certified)())())()
                    if M.IdentityCompare(
                        derivation, M.EmptyList
                    )() is M.false_value:
                        verification = CB.VerifyDerivation(
                            derivation, lhs, rhs, trusted_rules, registry
                        )()
                        if M.IdentityCompare(
                            M.Head(verification)(), L.DerivationVerifiedLabel
                        )() is M.truth_value:
                            sides = PG.VariableizeDiscoveredTerm(
                                M.Pair(lhs, M.Pair(rhs, M.EmptyList)), variables
                            )()
                            rule = P.Rule(
                                M.Head(sides)(), M.Head(M.Tail(sides)())()
                            )()
        self.result = M.Pair(
            rule,
            M.Pair(
                derivation,
                M.Pair(verification, M.Pair(registry, M.EmptyList)),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                equation, M.Pair(trusted_rules, M.Pair(input_registry, M.EmptyList))
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class RecordNamedDiscoveredLaw(M.Edge):
    """Persist the observation and activate only an independently checked law."""

    def __init__(self, runtime, named_record, trusted_rules):
        registry = M.FromContextGetConstructors(runtime.graph)()
        fields = M.Tail(named_record)()
        name = M.Head(fields)()
        equation = M.Head(M.Tail(M.Tail(fields)())())()
        certified = CertifyDiscoveredEquation(equation, trusted_rules, registry)()
        rule = M.Head(certified)()
        derivation = M.Head(M.Tail(certified)())()
        verification = M.Head(M.Tail(M.Tail(certified)())())()
        registry = M.Head(M.Tail(M.Tail(M.Tail(certified)())())())()
        runtime.graph._replace_context(constructors=registry)
        runtime.graph.add_node(named_record)
        receipt = M.EmptyList
        if M.IdentityCompare(rule, M.EmptyList)() is M.false_value:
            sides = M.Tail(M.Tail(equation)())()
            lhs = M.Head(sides)()
            rhs = M.Head(M.Tail(sides)())()
            runtime.graph.add_rule(rule)
            runtime._compiled_ordered_rules = None
            registry = M.FromContextGetConstructors(runtime.graph)()
            runtime.graph.add_derivation(lhs, rhs, derivation)
            receipt = M.Pair(
                L.ProofReceiptLabel,
                M.Pair(
                    name,
                    M.Pair(
                        lhs,
                        M.Pair(
                            rhs,
                            M.Pair(
                                derivation,
                                M.Pair(
                                    registry,
                                    M.Pair(
                                        rule,
                                        M.Pair(named_record, M.Pair(verification, M.EmptyList)),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            )
            runtime.graph.add_node(receipt)
        self.result = M.Pair(
            rule,
            M.Pair(receipt, M.Pair(verification, M.Pair(registry, M.EmptyList))),
        )
        super().__init__(
            inputs=M.Pair(named_record, M.Pair(trusted_rules, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result
