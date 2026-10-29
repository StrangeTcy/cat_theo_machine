"""Finite algebra satisfaction through explicit operation-role correspondences.

The correspondence carries one positional call binding per required source
operation. Every target operation is closed on the exact finite carrier and
every rebound equation is replayed. Receipts pin executable definitions as
well as syntax; they grant no isomorphism or universal theorem authority.
"""

from . import defined_operations as DO
from . import invariant_miner as IM
from . import labels as L
from . import machine as M
from . import observed_structures as OS
from . import playground as PG
from . import template_matching as TM
from .math import arithmetic as A


class StructureOperationBinding(M.Edge):
    def __init__(self, source_label, formals, candidate_call):
        result = M.Pair(source_label, M.Pair(formals, M.Pair(candidate_call, M.EmptyList)))
        super().__init__(inputs=result, results=result)


class StructureIdentityChain(M.Edge):
    def __init__(self, left, right):
        verdict = M.false_value
        if M.IdentityCompare(left, M.EmptyList)() is M.truth_value:
            verdict = M.IdentityCompare(right, M.EmptyList)()
        elif M.IsPair(left)() is M.truth_value:
            if M.IsPair(right)() is M.truth_value:
                if M.IdentityCompare(M.Head(left)(), M.Head(right)())() is M.truth_value:
                    verdict = StructureIdentityChain(M.Tail(left)(), M.Tail(right)())()
        super().__init__(inputs=M.Pair(left, right), results=verdict)


class StructureBindingLookup(M.Edge):
    def __init__(self, bindings, label):
        result = M.EmptyList
        if M.IsPair(bindings)() is M.truth_value:
            binding = M.Head(bindings)()
            if M.IsPair(binding)() is M.truth_value:
                if M.IdentityCompare(M.Head(binding)(), label)() is M.truth_value:
                    result = binding
            if M.IdentityCompare(result, M.EmptyList)() is M.truth_value:
                result = StructureBindingLookup(M.Tail(bindings)(), label)()
        super().__init__(inputs=M.Pair(bindings, label), results=result)


class StructureSourcesBound(M.Edge):
    def __init__(self, source_operations, bound):
        verdict = M.IdentityCompare(source_operations, M.EmptyList)()
        if M.IsPair(source_operations)() is M.truth_value:
            entry = M.Head(source_operations)()
            label = M.Head(M.Head(M.Tail(M.Tail(entry)())())())()
            if DO.DefinedIdentityMember(label, bound)() is M.truth_value:
                verdict = StructureSourcesBound(M.Tail(source_operations)(), bound)()
        super().__init__(inputs=M.Pair(source_operations, bound), results=verdict)


class StructureBindings(M.Edge):
    """Validate exactly one binding per role and retain definition evidence."""

    def __init__(self, bindings, source_operations, registry, seen=M.EmptyList,
                 candidates=M.EmptyList, evidence=M.EmptyList):
        verdict = M.false_value
        target_operations = candidates
        records = evidence
        if M.IdentityCompare(bindings, M.EmptyList)() is M.truth_value:
            verdict = StructureSourcesBound(source_operations, seen)()
        elif M.IsPair(bindings)() is M.truth_value:
            binding = M.Head(bindings)()
            admitted = PG.ExactArity(binding, M.three, registry)()
            if admitted is M.truth_value:
                source_label = M.Head(binding)()
                formals = M.Head(M.Tail(binding)())()
                call = M.Head(M.Tail(M.Tail(binding)())())()
                source = PG.LookupOperationByLabel(source_label, source_operations)()
                admitted = M.AndAtom(M.IsPair(source)(),
                    M.NotAtom(DO.DefinedIdentityMember(source_label, seen)())())()
                admitted = M.AndAtom(admitted, M.IsPair(formals)())()
                admitted = M.AndAtom(admitted, TM.FiniteVariableChain(formals, registry)())()
                admitted = M.AndAtom(admitted, M.IsPair(call)())()
            if admitted is M.truth_value:
                candidate_label = M.Head(call)()
                admitted = StructureIdentityChain(M.Tail(call)(), formals)()
                executable = DO.ExecutableNatOperationDescriptor(candidate_label, registry)()
                descriptor = M.Head(executable)()
                admitted = M.AndAtom(admitted, M.IsPair(descriptor)())()
            if admitted is M.truth_value:
                source_formals = M.Head(M.Tail(source)())()
                candidate_formals = M.Head(M.Tail(descriptor)())()
                admitted = M.AndAtom(OS.ObservedSameArity(source_formals, formals)(),
                    OS.ObservedSameArity(candidate_formals, formals)())()
            if admitted is M.truth_value:
                if M.IdentityCompare(PG.LookupOperationByLabel(candidate_label, candidates)(), M.EmptyList)() is M.truth_value:
                    target_operations = M.Pair(descriptor, candidates)
                source_evidence = DO.ExecutableNatOperationDescriptor(source_label, registry)()
                record = M.Pair(binding, M.Pair(source_evidence, M.Pair(executable, M.EmptyList)))
                remaining = StructureBindings(M.Tail(bindings)(), source_operations, registry,
                    M.Pair(source_label, seen), target_operations, M.Pair(record, evidence))()
                verdict = M.Head(remaining)()
                target_operations = M.Head(M.Tail(remaining)())()
                records = M.Head(M.Tail(M.Tail(remaining)())())()
        super().__init__(inputs=M.Pair(bindings, M.Pair(source_operations, M.Pair(registry, M.EmptyList))),
            results=M.Pair(verdict, M.Pair(target_operations, M.Pair(records, M.EmptyList))))


class StructureClosure(M.Edge):
    def __init__(self, bindings, carrier, operations, registry, evidence=M.EmptyList):
        verdict = M.IdentityCompare(bindings, M.EmptyList)()
        active = registry
        records = evidence
        if M.IsPair(bindings)() is M.truth_value:
            binding = M.Head(bindings)()
            formals = M.Head(M.Tail(binding)())()
            call = M.Head(M.Tail(M.Tail(binding)())())()
            checked = TM.FiniteOperationClosure(call, formals, formals, carrier,
                carrier, M.EmptyList, operations, registry)()
            verdict = M.Head(checked)()
            active = M.Head(M.Tail(M.Tail(checked)())())()
            records = M.Pair(M.Pair(binding, M.Pair(verdict,
                M.Pair(M.Head(M.Tail(checked)())(), M.EmptyList))), evidence)
            if verdict is M.truth_value:
                remaining = StructureClosure(M.Tail(bindings)(), carrier, operations, active, records)()
                verdict = M.Head(remaining)()
                records = M.Head(M.Tail(remaining)())()
                active = M.Head(M.Tail(M.Tail(remaining)())())()
        super().__init__(inputs=M.Pair(bindings, M.Pair(carrier, M.Pair(operations, M.Pair(registry, M.EmptyList)))),
            results=M.Pair(verdict, M.Pair(records, M.Pair(active, M.EmptyList))))


class RebindStructureTerm(M.Edge):
    """Translate operation heads; constants must belong to both named carriers."""

    def __init__(self, term, variables, bindings, source_carrier, carrier, registry):
        result = M.EmptyList
        if M.IsPair(term)() is M.false_value:
            if PG.ChainHasTerm(variables, term)() is M.truth_value:
                result = term
            elif A.IsNat(term, registry)() is M.truth_value:
                if M.AndAtom(PG.ChainContains(source_carrier, term, registry)(),
                    PG.ChainContains(carrier, term, registry)())() is M.truth_value:
                    result = term
        elif M.IdentityCompare(M.Head(term)(), L.ExprIntLabel)() is M.truth_value:
            arguments = M.Tail(term)()
            if PG.ExactArity(arguments, M.one, registry)() is M.truth_value:
                constant = M.Head(arguments)()
                if A.IsNat(constant, registry)() is M.truth_value:
                    if M.AndAtom(PG.ChainContains(source_carrier, constant, registry)(),
                        PG.ChainContains(carrier, constant, registry)())() is M.truth_value:
                        result = term
        else:
            binding = StructureBindingLookup(bindings, M.Head(term)())()
            if M.IsPair(binding)() is M.truth_value:
                formals = M.Head(M.Tail(binding)())()
                call = M.Head(M.Tail(M.Tail(binding)())())()
                if OS.ObservedSameArity(M.Tail(term)(), formals)() is M.truth_value:
                    rebound = RebindStructureArguments(M.Tail(term)(), variables,
                        bindings, source_carrier, carrier, registry)()
                    if M.Head(rebound)() is M.truth_value:
                        result = M.Pair(M.Head(call)(), M.Tail(rebound)())
        super().__init__(inputs=M.Pair(term, M.Pair(variables, M.Pair(bindings, M.Pair(registry, M.EmptyList)))),
            results=result)


class RebindStructureArguments(M.Edge):
    def __init__(self, arguments, variables, bindings, source_carrier, carrier, registry):
        verdict = M.IdentityCompare(arguments, M.EmptyList)()
        result = M.EmptyList
        if M.IsPair(arguments)() is M.truth_value:
            first = RebindStructureTerm(M.Head(arguments)(), variables, bindings, source_carrier, carrier, registry)()
            if M.IdentityCompare(first, M.EmptyList)() is M.false_value:
                rest = RebindStructureArguments(M.Tail(arguments)(), variables, bindings, source_carrier, carrier, registry)()
                verdict = M.Head(rest)()
                if verdict is M.truth_value:
                    result = M.Pair(first, M.Tail(rest)())
        super().__init__(inputs=M.Pair(arguments, M.Pair(variables, M.Pair(bindings, M.EmptyList))),
            results=M.Pair(verdict, result))


class StructureRequirements(M.Edge):
    def __init__(self, requirements, bindings, source_carrier, carrier, operations, registry, evidence=M.EmptyList):
        verdict = M.IdentityCompare(requirements, M.EmptyList)()
        active = registry
        records = evidence
        if M.IsPair(requirements)() is M.truth_value:
            named = M.Head(requirements)()
            equation = M.Head(M.Tail(M.Tail(M.Tail(named)())())())()
            fields = M.Tail(equation)()
            variables = M.Head(fields)()
            lhs = RebindStructureTerm(M.Head(M.Tail(fields)())(), variables,
                bindings, source_carrier, carrier, registry)()
            rhs = RebindStructureTerm(M.Head(M.Tail(M.Tail(fields)())())(), variables,
                bindings, source_carrier, carrier, registry)()
            if M.OrAtom(M.IdentityCompare(lhs, M.EmptyList)(), M.IdentityCompare(rhs, M.EmptyList)())() is M.false_value:
                rebound = M.Pair(L.DiscoveredEquationLabel, M.Pair(variables, M.Pair(lhs, M.Pair(rhs, M.EmptyList))))
                checked = IM.CheckOperationEquationDomain(rebound, variables, variables,
                    carrier, carrier, M.EmptyList, registry, operations, M.EmptyList, M.EmptyList)()
                verdict = M.Head(checked)()
                active = M.Head(M.Tail(checked)())()
                records = M.Pair(M.Pair(named, M.Pair(rebound, M.Pair(verdict,
                    M.Pair(M.Head(M.Tail(M.Tail(checked)())())(), M.EmptyList)))), evidence)
                if verdict is M.truth_value:
                    remaining = StructureRequirements(M.Tail(requirements)(), bindings,
                        source_carrier, carrier, operations, active, records)()
                    verdict = M.Head(remaining)()
                    records = M.Head(M.Tail(remaining)())()
                    active = M.Head(M.Tail(M.Tail(remaining)())())()
        super().__init__(inputs=M.Pair(requirements, M.Pair(bindings, M.Pair(carrier, M.Pair(registry, M.EmptyList)))),
            results=M.Pair(verdict, M.Pair(records, M.Pair(active, M.EmptyList))))


class CheckFiniteStructure(M.Edge):
    """Return a bound finite receipt and registry after replaying all obligations."""

    def __init__(self, template, bindings, carrier, registry):
        verdict = M.false_value
        active = registry
        evidence = M.Pair(M.Char("Unsupported finite structure scope or correspondence."), M.EmptyList)
        try:
            admitted = M.AndAtom(PG.ExactArity(template, M.four, registry)(), M.IsPair(carrier)())()
            admitted = M.AndAtom(admitted, TM.FiniteNatChain(carrier, registry)())()
            if admitted is M.truth_value:
                admitted = M.IdentityCompare(M.Head(template)(), L.AlgebraicTemplateLabel)()
                fields = M.Tail(template)()
                source_carrier = M.Head(fields)()
                source_catalog = M.Head(M.Tail(fields)())()
                requirements = M.Head(M.Tail(M.Tail(fields)())())()
                admitted = M.AndAtom(admitted, M.IsPair(source_carrier)())()
                admitted = M.AndAtom(admitted, TM.FiniteNatChain(source_carrier, registry)())()
                admitted = M.AndAtom(admitted, M.IsPair(requirements)())()
            if admitted is M.truth_value:
                dependencies = TM.FiniteTemplateDependencies(requirements, source_carrier, source_catalog, registry)()
                admitted = M.Head(dependencies)()
                used = M.Head(M.Tail(dependencies)())()
                admitted = M.AndAtom(admitted, M.IsPair(used)())()
            if admitted is M.truth_value:
                selected = TM.FiniteTemplateSelectedOperations(source_catalog, used, registry)()
                admitted = M.Head(selected)()
            if admitted is M.truth_value:
                described = OS.ObservedExecutableOperations(M.Head(M.Tail(selected)())(), registry)()
                admitted = M.Head(described)()
                sources = M.Head(M.Tail(described)())()
            if admitted is M.truth_value:
                correspondence = StructureBindings(bindings, sources, registry)()
                admitted = M.Head(correspondence)()
            if admitted is M.truth_value:
                operations = M.Head(M.Tail(correspondence)())()
                authorities = M.Head(M.Tail(M.Tail(correspondence)())())()
                closed = StructureClosure(bindings, carrier, operations, registry)()
                active = M.Head(M.Tail(M.Tail(closed)())())()
                closure_evidence = M.Head(M.Tail(closed)())()
                laws = M.EmptyList
                if M.Head(closed)() is M.truth_value:
                    checked = StructureRequirements(requirements, bindings, source_carrier, carrier, operations, active)()
                    verdict = M.Head(checked)()
                    active = M.Head(M.Tail(M.Tail(checked)())())()
                    laws = M.Head(M.Tail(checked)())()
                evidence = M.Pair(authorities, M.Pair(closure_evidence, M.Pair(laws, M.EmptyList)))
        except Exception:
            verdict = M.false_value
            active = registry
            evidence = M.Pair(M.Char("Malformed finite structure or correspondence."), M.EmptyList)
        instance = M.Pair(L.TemplateInstanceLabel, M.Pair(M.Char("finite-operation-structure-v1"),
            M.Pair(verdict, M.Pair(template, M.Pair(bindings, M.Pair(carrier, M.Pair(evidence, M.EmptyList)))))))
        super().__init__(inputs=M.Pair(template, M.Pair(bindings, M.Pair(carrier, M.Pair(registry, M.EmptyList)))),
            results=M.Pair(instance, M.Pair(active, M.EmptyList)))


class VerifyFiniteStructureInstance(M.Edge):
    """Recompute the exact correspondence, definitions, carrier and every witness."""

    def __init__(self, instance, template, bindings, carrier, registry):
        verdict = M.false_value
        active = registry
        try:
            admitted = PG.ExactArity(instance, M.seven, registry)()
            if admitted is M.truth_value:
                admitted = M.IdentityCompare(M.Head(instance)(), L.TemplateInstanceLabel)()
            if admitted is M.truth_value:
                checked = CheckFiniteStructure(template, bindings, carrier, registry)()
                replayed = M.Head(checked)()
                active = M.Head(M.Tail(checked)())()
                verdict = M.AndAtom(M.Head(M.Tail(M.Tail(replayed)())())(), M.Compare(instance, replayed)())()
        except Exception:
            verdict = M.false_value
            active = registry
        super().__init__(inputs=M.Pair(instance, M.Pair(template, M.Pair(bindings,
            M.Pair(carrier, M.Pair(registry, M.EmptyList))))),
            results=M.Pair(verdict, M.Pair(active, M.EmptyList)))
