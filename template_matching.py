"""Replayable finite matching of explicit one-operation equation templates.

This checker admits only exact binary catalogue calls as candidate bodies.
Source observations select equation obligations; their flags and witnesses do
not establish those obligations for the candidate. Closure and every equation
are evaluated again on the bound finite Nat carrier. No theorem or rule is
created, and no claim extends beyond that carrier.
"""

from . import labels as L
from . import machine as M
from . import operation_catalog as OC
from . import playground as PG
from .math import arithmetic as A


class FiniteNatChain(M.Edge):
    """Validate a proper chain of distinct nonnegative Nat values."""

    def __init__(self, chain, registry, seen=M.EmptyList):
        verdict = M.false_value
        if M.IdentityCompare(chain, M.EmptyList)() is M.truth_value:
            verdict = M.truth_value
        elif M.IsPair(chain)() is M.truth_value:
            value = M.Head(chain)()
            if A.IsNat(value, registry)() is M.truth_value:
                if M.NatLess(value, M.Zero, registry)() is M.false_value:
                    if PG.ChainContains(seen, value, registry)() is M.false_value:
                        verdict = FiniteNatChain(M.Tail(chain)(), registry, M.Pair(value, seen))()
        super().__init__(inputs=M.Pair(chain, M.Pair(registry, M.Pair(seen, M.EmptyList))), results=verdict)


class FiniteVariableChain(M.Edge):
    """Validate distinct atomic indeterminates without numeric or truth values."""

    def __init__(self, chain, registry, seen=M.EmptyList):
        verdict = M.false_value
        if M.IdentityCompare(chain, M.EmptyList)() is M.truth_value:
            verdict = M.truth_value
        elif M.IsPair(chain)() is M.truth_value:
            variable = M.Head(chain)()
            if M.IsPair(variable)() is M.false_value:
                if M.IdentityCompare(variable, M.EmptyList)() is M.false_value:
                    if A.IsNat(variable, registry)() is M.false_value:
                        if M.IsWhole(variable, registry)() is M.false_value:
                            if M.OrAtom(M.IdentityCompare(variable, M.truth_value)(), M.IdentityCompare(variable, M.false_value)())() is M.false_value:
                                if PG.ChainHasTerm(seen, variable)() is M.false_value:
                                    verdict = FiniteVariableChain(M.Tail(chain)(), registry, M.Pair(variable, seen))()
        super().__init__(inputs=M.Pair(chain, M.Pair(registry, M.Pair(seen, M.EmptyList))), results=verdict)


class FiniteTemplateScope(M.Edge):
    """Admit one synthesized template and the exact supplied binary candidate."""

    def __init__(self, template, variables, operation, carrier, registry):
        result = M.EmptyList
        admitted = M.false_value
        try:
            admitted = M.AndAtom(M.IsPair(carrier)(), FiniteNatChain(carrier, registry)())()
            admitted = M.AndAtom(admitted,
                M.AndAtom(PG.ExactArity(variables, M.two, registry)(), FiniteVariableChain(variables, registry)())())()
            if admitted is M.truth_value:
                admitted = M.IsPair(operation)()
            if admitted is M.truth_value:
                candidate_label = M.Head(operation)()
                admitted = M.Compare(M.Tail(operation)(), variables)()
            if admitted is M.truth_value:
                candidate_entry = OC.NatOperationDescription(candidate_label)()
                admitted = M.IsPair(candidate_entry)()
            if admitted is M.truth_value:
                candidate_formals = M.Head(M.Tail(candidate_entry)())()
                admitted = PG.ExactArity(candidate_formals, M.two, registry)()
            if admitted is M.truth_value:
                admitted = M.IsPair(template)()
            if admitted is M.truth_value:
                admitted = M.IdentityCompare(M.Head(template)(), L.AlgebraicTemplateLabel)()
            if admitted is M.truth_value:
                fields = M.Tail(template)()
                admitted = PG.ExactArity(fields, M.three, registry)()
            if admitted is M.truth_value:
                source_carrier = M.Head(fields)()
                source_operations = M.Head(M.Tail(fields)())()
                requirements = M.Head(M.Tail(M.Tail(fields)())())()
                admitted = M.AndAtom(M.IsPair(source_carrier)(), FiniteNatChain(source_carrier, registry)())()
                admitted = M.AndAtom(admitted, PG.ExactArity(source_operations, M.one, registry)())()
                admitted = M.AndAtom(admitted, M.IsPair(requirements)())()
            if admitted is M.truth_value:
                source_entry = M.Head(source_operations)()
                admitted = PG.ExactArity(source_entry, M.eight, registry)()
            if admitted is M.truth_value:
                source_name = M.Head(source_entry)()
                source_formals = M.Head(M.Tail(source_entry)())()
                source_operation = M.Head(M.Tail(M.Tail(source_entry)())())()
                admitted = M.AndAtom(PG.ExactArity(source_formals, M.two, registry)(), M.IsPair(source_operation)())()
            if admitted is M.truth_value:
                source_label = M.Head(source_operation)()
                canonical_source = OC.NatOperationDescription(source_label)()
                admitted = M.Compare(source_entry, canonical_source)()
            if admitted is M.truth_value:
                result = M.Pair(source_name, M.Pair(source_carrier, M.Pair(source_label,
                    M.Pair(candidate_label, M.Pair(requirements,
                        M.Pair(M.Pair(candidate_entry, M.EmptyList), M.EmptyList))))))
        except Exception:
            result = M.EmptyList
        super().__init__(inputs=M.Pair(template, M.Pair(variables, M.Pair(operation,
            M.Pair(carrier, M.Pair(registry, M.EmptyList))))), results=result)


class RebindFiniteOperationTerm(M.Edge):
    """Rebind binary source calls positionally; refuse constants or other heads."""

    def __init__(self, term, variables, source_label, candidate_label, registry):
        result = M.EmptyList
        if M.IsPair(term)() is M.false_value:
            if PG.ChainHasTerm(variables, term)() is M.truth_value:
                result = term
        elif M.IdentityCompare(M.Head(term)(), source_label)() is M.truth_value:
            args = M.Tail(term)()
            if PG.ExactArity(args, M.two, registry)() is M.truth_value:
                left = RebindFiniteOperationTerm(M.Head(args)(), variables, source_label, candidate_label, registry)()
                right = RebindFiniteOperationTerm(M.Head(M.Tail(args)())(), variables, source_label, candidate_label, registry)()
                if M.OrAtom(M.IdentityCompare(left, M.EmptyList)(), M.IdentityCompare(right, M.EmptyList)())() is M.false_value:
                    result = M.Pair(candidate_label, M.Pair(left, M.Pair(right, M.EmptyList)))
        super().__init__(inputs=M.Pair(term, M.Pair(variables, M.Pair(source_label,
            M.Pair(candidate_label, M.Pair(registry, M.EmptyList))))), results=result)


class FiniteOperationClosure(M.Edge):
    """Evaluate every candidate call on the finite Cartesian carrier axes."""

    def __init__(self, operation, variables, remaining_variables, carrier,
                 remaining_carrier, assignment, operations, registry, witnesses=M.EmptyList):
        result = M.Pair(M.truth_value, M.Pair(witnesses, M.Pair(registry, M.EmptyList)))
        if M.IdentityCompare(remaining_variables, M.EmptyList)() is M.truth_value:
            point = PG.ChainReverse(assignment)()
            evaluated = PG.EvaluateNatExpr(operation, PG.ZipEnvironment(variables, point)(), registry, operations)()
            value = M.Head(evaluated)()
            active = M.Head(M.Tail(evaluated)())()
            verdict = M.false_value
            if M.IdentityCompare(value, M.EmptyList)() is M.false_value:
                if A.IsNat(value, active)() is M.truth_value:
                    verdict = PG.ChainContains(carrier, value, active)()
            witness = M.Pair(point, M.Pair(value, M.EmptyList))
            result = M.Pair(verdict, M.Pair(M.Pair(witness, witnesses), M.Pair(active, M.EmptyList)))
        elif M.IsPair(remaining_carrier)() is M.truth_value:
            first = FiniteOperationClosure(operation, variables, M.Tail(remaining_variables)(), carrier,
                carrier, M.Pair(M.Head(remaining_carrier)(), assignment), operations, registry, witnesses)()
            result = first
            if M.Head(first)() is M.truth_value:
                result = FiniteOperationClosure(operation, variables, remaining_variables, carrier,
                    M.Tail(remaining_carrier)(), assignment, operations,
                    M.Head(M.Tail(M.Tail(first)())())(), M.Head(M.Tail(first)())())()
        super().__init__(inputs=M.Pair(operation, M.Pair(variables, M.Pair(remaining_variables,
            M.Pair(carrier, M.Pair(remaining_carrier, M.Pair(assignment, M.Pair(operations,
                M.Pair(registry, M.Pair(witnesses, M.EmptyList))))))))), results=result)


class FiniteTemplateRequirements(M.Edge):
    """Check every supplied explicit equation after rebinding its operation."""

    def __init__(self, requirements, source_name, source_carrier, source_label,
                 candidate_label, carrier, operations, registry, evidence=M.EmptyList):
        from .invariant_miner import CheckOperationEquationDomain

        result = M.Pair(M.false_value, M.Pair(
            M.Pair(M.Char("Malformed or unsupported equation requirement."), M.Pair(requirements, M.EmptyList)),
            M.Pair(registry, M.EmptyList)))
        if M.IdentityCompare(requirements, M.EmptyList)() is M.truth_value:
            result = M.Pair(M.truth_value, M.Pair(evidence, M.Pair(registry, M.EmptyList)))
        elif M.IsPair(requirements)() is M.truth_value:
            named = M.Head(requirements)()
            admitted = M.IsPair(named)()
            if admitted is M.truth_value:
                admitted = M.IdentityCompare(M.Head(named)(), L.NamedRegularityLabel)()
            if admitted is M.truth_value:
                fields = M.Tail(named)()
                admitted = PG.ExactArity(fields, M.five, registry)()
            if admitted is M.truth_value:
                fields = M.Tail(fields)()
                required_operation = M.Head(fields)()
                fields = M.Tail(fields)()
                equation = M.Head(fields)()
                required_carrier = M.Head(M.Tail(fields)())()
                admitted = M.AndAtom(M.Compare(required_operation, source_name)(), M.Compare(required_carrier, source_carrier)())()
                admitted = M.AndAtom(admitted, M.IsPair(equation)())()
            if admitted is M.truth_value:
                admitted = M.IdentityCompare(M.Head(equation)(), L.DiscoveredEquationLabel)()
            if admitted is M.truth_value:
                fields = M.Tail(equation)()
                admitted = PG.ExactArity(fields, M.three, registry)()
            if admitted is M.truth_value:
                variables = M.Head(fields)()
                admitted = M.AndAtom(M.IsPair(variables)(), FiniteVariableChain(variables, registry)())()
            if admitted is M.truth_value:
                lhs = RebindFiniteOperationTerm(M.Head(M.Tail(fields)())(), variables, source_label, candidate_label, registry)()
                rhs = RebindFiniteOperationTerm(M.Head(M.Tail(M.Tail(fields)())())(), variables, source_label, candidate_label, registry)()
                admitted = M.NotAtom(M.OrAtom(M.IdentityCompare(lhs, M.EmptyList)(), M.IdentityCompare(rhs, M.EmptyList)())())()
            if admitted is M.truth_value:
                rebound = M.Pair(L.DiscoveredEquationLabel, M.Pair(variables, M.Pair(lhs, M.Pair(rhs, M.EmptyList))))
                checked = CheckOperationEquationDomain(rebound, variables, variables, carrier, carrier,
                    M.EmptyList, registry, operations, M.EmptyList, M.EmptyList)()
                active = M.Head(M.Tail(checked)())()
                witness = M.Head(M.Tail(M.Tail(checked)())())()
                record = M.Pair(named, M.Pair(rebound, M.Pair(M.Head(checked)(), M.Pair(witness, M.EmptyList))))
                accumulated = M.Pair(record, evidence)
                result = M.Pair(M.false_value, M.Pair(accumulated, M.Pair(active, M.EmptyList)))
                if M.Head(checked)() is M.truth_value:
                    result = FiniteTemplateRequirements(M.Tail(requirements)(), source_name, source_carrier,
                        source_label, candidate_label, carrier, operations, active, accumulated)()
        super().__init__(inputs=M.Pair(requirements, M.Pair(source_name, M.Pair(source_carrier,
            M.Pair(source_label, M.Pair(candidate_label, M.Pair(carrier, M.Pair(operations,
                M.Pair(registry, M.Pair(evidence, M.EmptyList))))))))), results=result)


class CheckFiniteTemplate(M.Edge):
    """Return a bound finite instance and registry; no universal authority."""

    def __init__(self, template, variables, operation, carrier, registry):
        verdict = M.false_value
        active = registry
        evidence = M.Pair(M.Char("Unsupported finite template or candidate scope."), M.EmptyList)
        try:
            scope = FiniteTemplateScope(template, variables, operation, carrier, registry)()
            if M.IsPair(scope)() is M.truth_value:
                source_name = M.Head(scope)()
                scope = M.Tail(scope)()
                source_carrier = M.Head(scope)()
                scope = M.Tail(scope)()
                source_label = M.Head(scope)()
                scope = M.Tail(scope)()
                candidate_label = M.Head(scope)()
                scope = M.Tail(scope)()
                requirements = M.Head(scope)()
                operations = M.Head(M.Tail(scope)())()
                closure = FiniteOperationClosure(operation, variables, variables, carrier, carrier,
                    M.EmptyList, operations, registry)()
                active = M.Head(M.Tail(M.Tail(closure)())())()
                closure_evidence = M.Pair(M.Char("closure"),
                    M.Pair(M.Head(closure)(), M.Pair(M.Head(M.Tail(closure)())(), M.EmptyList)))
                law_evidence = M.EmptyList
                if M.Head(closure)() is M.truth_value:
                    checked = FiniteTemplateRequirements(requirements, source_name, source_carrier,
                        source_label, candidate_label, carrier, operations, active)()
                    verdict = M.Head(checked)()
                    law_evidence = M.Head(M.Tail(checked)())()
                    active = M.Head(M.Tail(M.Tail(checked)())())()
                evidence = M.Pair(closure_evidence, M.Pair(law_evidence, M.EmptyList))
        except Exception:
            verdict = M.false_value
            active = registry
            evidence = M.Pair(M.Char("Malformed finite template or candidate scope."), M.EmptyList)
        instance = M.Pair(L.TemplateInstanceLabel,
            M.Pair(M.Char("finite-algebra-template"), M.Pair(verdict,
                M.Pair(template, M.Pair(variables, M.Pair(operation, M.Pair(carrier,
                    M.Pair(M.Char("exhaustive-finite-replay"), M.Pair(evidence, M.EmptyList)))))))))
        super().__init__(inputs=M.Pair(template, M.Pair(variables, M.Pair(operation,
            M.Pair(carrier, M.Pair(registry, M.EmptyList))))),
            results=M.Pair(instance, M.Pair(active, M.EmptyList)))


class VerifyFiniteTemplateInstance(M.Edge):
    """Pin expected scope, replay every check, and compare recorded evidence.

    The supplied verdict is not used to decide acceptance. Only replay can
    establish satisfaction on the exact expected finite carrier.
    """

    def __init__(self, instance, template, variables, operation, carrier, registry):
        verdict = M.false_value
        active = registry
        try:
            admitted = M.IsPair(instance)()
            if admitted is M.truth_value:
                admitted = M.IdentityCompare(M.Head(instance)(), L.TemplateInstanceLabel)()
            if admitted is M.truth_value:
                fields = M.Tail(instance)()
                admitted = PG.ExactArity(fields, M.eight, registry)()
            if admitted is M.truth_value:
                admitted = M.Compare(M.Head(fields)(), M.Char("finite-algebra-template"))()
                fields = M.Tail(fields)()
                claimed = M.Head(fields)()
                admitted = M.AndAtom(admitted, M.OrAtom(M.IdentityCompare(claimed, M.truth_value)(), M.IdentityCompare(claimed, M.false_value)())())()
                fields = M.Tail(fields)()
                admitted = M.AndAtom(admitted, M.Compare(M.Head(fields)(), template)())()
                fields = M.Tail(fields)()
                admitted = M.AndAtom(admitted, M.Compare(M.Head(fields)(), variables)())()
                fields = M.Tail(fields)()
                admitted = M.AndAtom(admitted, M.Compare(M.Head(fields)(), operation)())()
                fields = M.Tail(fields)()
                admitted = M.AndAtom(admitted, M.Compare(M.Head(fields)(), carrier)())()
                fields = M.Tail(fields)()
                admitted = M.AndAtom(admitted, M.Compare(M.Head(fields)(), M.Char("exhaustive-finite-replay"))())()
                saved_evidence = M.Head(M.Tail(fields)())()
            if admitted is M.truth_value:
                replayed = CheckFiniteTemplate(template, variables, operation, carrier, registry)()
                active = M.Head(M.Tail(replayed)())()
                fields = M.Tail(M.Head(replayed)())()
                fields = M.Tail(fields)()
                fresh_verdict = M.Head(fields)()
                fields = M.Tail(fields)()
                fields = M.Tail(fields)()
                fields = M.Tail(fields)()
                fields = M.Tail(fields)()
                fields = M.Tail(fields)()
                fields = M.Tail(fields)()
                verdict = M.AndAtom(fresh_verdict, M.Compare(saved_evidence, M.Head(fields)())())()
        except Exception:
            verdict = M.false_value
            active = registry
        super().__init__(inputs=M.Pair(instance, M.Pair(template, M.Pair(variables,
            M.Pair(operation, M.Pair(carrier, M.Pair(registry, M.EmptyList)))))),
            results=M.Pair(verdict, M.Pair(active, M.EmptyList)))


__all__ = (
    "CheckFiniteTemplate",
    "VerifyFiniteTemplateInstance",
)
