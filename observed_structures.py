"""Bind replayed finite observations into pending structure candidates.

The source equations determine the operation dependencies. Display names do
not select them. Each supplied witness must occur in an exhaustive replay on
the exact finite Nat carrier. A bundle supplies neither carrier closure nor
a universal law, proof authority, theorem transfer, or graph mutation.
"""

from . import labels as L
from . import machine as M
from . import operation_catalog as OC
from . import playground as PG
from . import template_matching as TM
from .math import arithmetic as A


class ObservedSameArity(M.Edge):
    """Compare proper chain lengths through their machine structure."""

    def __init__(self, left, right):
        verdict = M.false_value
        if M.IdentityCompare(left, M.EmptyList)() is M.truth_value:
            verdict = M.IdentityCompare(right, M.EmptyList)()
        elif M.IsPair(left)() is M.truth_value:
            if M.IsPair(right)() is M.truth_value:
                verdict = ObservedSameArity(M.Tail(left)(), M.Tail(right)())()
        super().__init__(
            inputs=M.Pair(left, M.Pair(right, M.EmptyList)), results=verdict,
        )


class ObservedExecutableOperations(M.Edge):
    """Validate unique executable descriptors and return canonical replay entries.

    The supplied display names and formatting metadata carry no authority.
    Executable labels, formal arities and positional bodies must agree with
    the implemented catalog. Result: verdict, canonical entries.
    """

    def __init__(self, operations, registry, seen=M.EmptyList):
        verdict = M.false_value
        canonical_entries = M.EmptyList
        if M.IdentityCompare(operations, M.EmptyList)() is M.truth_value:
            verdict = M.truth_value
        elif M.IsPair(operations)() is M.truth_value:
            entry = M.Head(operations)()
            admitted = PG.ExactArity(entry, M.eight, registry)()
            if admitted is M.truth_value:
                formals = M.Head(M.Tail(entry)())()
                body = M.Head(M.Tail(M.Tail(entry)())())()
                admitted = M.AndAtom(
                    M.IsPair(formals)(), TM.FiniteVariableChain(formals, registry)(),
                )()
                admitted = M.AndAtom(admitted, M.IsPair(body)())()
            if admitted is M.truth_value:
                label = M.Head(body)()
                admitted = M.NotAtom(PG.ChainHasTerm(seen, label)())()
                admitted = M.AndAtom(admitted, M.Compare(M.Tail(body)(), formals)())()
                canonical = OC.NatOperationDescription(label)()
                admitted = M.AndAtom(admitted, M.IsPair(canonical)())()
            if admitted is M.truth_value:
                canonical_formals = M.Head(M.Tail(canonical)())()
                admitted = ObservedSameArity(formals, canonical_formals)()
            if admitted is M.truth_value:
                remaining = ObservedExecutableOperations(
                    M.Tail(operations)(), registry, M.Pair(label, seen),
                )()
                verdict = M.Head(remaining)()
                if verdict is M.truth_value:
                    canonical_entries = M.Pair(
                        canonical, M.Head(M.Tail(remaining)())(),
                    )
        super().__init__(
            inputs=M.Pair(operations, M.Pair(registry, M.Pair(seen, M.EmptyList))),
            results=M.Pair(verdict, M.Pair(canonical_entries, M.EmptyList)),
        )


class AppendObservedOperations(M.Edge):
    """Preserve first-use order when joining validated operation dependencies."""

    def __init__(self, accumulated, incoming):
        result = accumulated
        if M.IsPair(incoming)() is M.truth_value:
            entry = M.Head(incoming)()
            if PG.ChainHasTerm(accumulated, entry)() is M.false_value:
                result = PG.ChainConcat(accumulated, M.Pair(entry, M.EmptyList))()
            result = AppendObservedOperations(result, M.Tail(incoming)())()
        super().__init__(
            inputs=M.Pair(accumulated, M.Pair(incoming, M.EmptyList)), results=result,
        )


class ObservedTermOperations(M.Edge):
    """Admit a term and collect exact descriptors for its operation heads.

    Result: verdict, used descriptors. Constants and indeterminates add no
    dependencies; an ExprInt must wrap one nonnegative Nat constant.
    """

    def __init__(self, term, variables, operations, registry, used=M.EmptyList):
        verdict = M.false_value
        dependencies = used
        if M.IsPair(term)() is M.false_value:
            if PG.ChainHasTerm(variables, term)() is M.truth_value:
                verdict = M.truth_value
            elif M.OrAtom(
                M.IdentityCompare(term, M.truth_value)(),
                M.IdentityCompare(term, M.false_value)(),
            )() is M.truth_value:
                verdict = M.truth_value
            elif A.IsNat(term, registry)() is M.truth_value:
                verdict = M.NotAtom(M.NatLess(term, M.Zero, registry)())()
        elif M.IdentityCompare(M.Head(term)(), L.ExprIntLabel)() is M.truth_value:
            arguments = M.Tail(term)()
            if PG.ExactArity(arguments, M.one, registry)() is M.truth_value:
                value = M.Head(arguments)()
                if A.IsNat(value, registry)() is M.truth_value:
                    verdict = M.NotAtom(M.NatLess(value, M.Zero, registry)())()
        else:
            entry = PG.LookupOperationByLabel(M.Head(term)(), operations)()
            if M.IsPair(entry)() is M.truth_value:
                arguments = M.Tail(term)()
                formals = M.Head(M.Tail(entry)())()
                if ObservedSameArity(arguments, formals)() is M.truth_value:
                    dependencies = AppendObservedOperations(
                        used, M.Pair(entry, M.EmptyList),
                    )()
                    checked = ObservedArgumentOperations(
                        arguments, variables, operations, registry, dependencies,
                    )()
                    verdict = M.Head(checked)()
                    dependencies = M.Head(M.Tail(checked)())()
        super().__init__(
            inputs=M.Pair(term, M.Pair(variables, M.Pair(operations,
                M.Pair(registry, M.Pair(used, M.EmptyList))))),
            results=M.Pair(verdict, M.Pair(dependencies, M.EmptyList)),
        )


class ObservedArgumentOperations(M.Edge):
    """Visit a proper argument chain, retaining shared operation bindings."""

    def __init__(self, arguments, variables, operations, registry, used=M.EmptyList):
        verdict = M.false_value
        dependencies = used
        if M.IdentityCompare(arguments, M.EmptyList)() is M.truth_value:
            verdict = M.truth_value
        elif M.IsPair(arguments)() is M.truth_value:
            checked = ObservedTermOperations(
                M.Head(arguments)(), variables, operations, registry, used,
            )()
            if M.Head(checked)() is M.truth_value:
                remaining = ObservedArgumentOperations(
                    M.Tail(arguments)(), variables, operations, registry,
                    M.Head(M.Tail(checked)())(),
                )()
                verdict = M.Head(remaining)()
                dependencies = M.Head(M.Tail(remaining)())()
        super().__init__(
            inputs=M.Pair(arguments, M.Pair(variables, M.Pair(operations,
                M.Pair(registry, M.Pair(used, M.EmptyList))))),
            results=M.Pair(verdict, M.Pair(dependencies, M.EmptyList)),
        )


class ObservedWitnessSubset(M.Edge):
    """Require each original witness to occur structurally in fresh replay."""

    def __init__(self, witnesses, replayed):
        verdict = M.false_value
        if M.IdentityCompare(witnesses, M.EmptyList)() is M.truth_value:
            verdict = M.truth_value
        elif M.IsPair(witnesses)() is M.truth_value:
            if PG.ChainHasTerm(replayed, M.Head(witnesses)())() is M.truth_value:
                verdict = ObservedWitnessSubset(M.Tail(witnesses)(), replayed)()
        super().__init__(
            inputs=M.Pair(witnesses, M.Pair(replayed, M.EmptyList)), results=verdict,
        )


class ReplayObservedFinding(M.Edge):
    """Replay one scoped source record without trusting its supplied verdict.

    Result: verdict, used descriptors, evidence record, threaded registry.
    Evidence: source, used descriptors, complete replay witness chain.
    """

    def __init__(self, source, domain, operations, replay_operations, registry):
        from .invariant_miner import CheckOperationEquationDomain

        active = registry
        verdict = M.false_value
        used = M.EmptyList
        evidence = M.EmptyList
        admitted = M.IsPair(source)()
        if admitted is M.truth_value:
            admitted = M.IdentityCompare(M.Head(source)(), L.ObservedRegularityLabel)()
        if admitted is M.truth_value:
            fields = M.Tail(source)()
            admitted = PG.ExactArity(fields, M.five, registry)()
        if admitted is M.truth_value:
            fields = M.Tail(fields)()
            equation = M.Head(fields)()
            fields = M.Tail(fields)()
            claimed = M.Head(fields)()
            fields = M.Tail(fields)()
            witnesses = M.Head(fields)()
            scope = M.Head(M.Tail(fields)())()
            admitted = M.IdentityCompare(claimed, M.truth_value)()
            admitted = M.AndAtom(admitted, M.IsPair(witnesses)())()
            admitted = M.AndAtom(admitted, PG.ExactArity(scope, M.two, registry)())()
        if admitted is M.truth_value:
            admitted = M.AndAtom(
                M.Compare(M.Head(scope)(), M.Char("holds"))(),
                M.Compare(M.Head(M.Tail(scope)())(), domain)(),
            )()
            admitted = M.AndAtom(admitted, M.IsPair(equation)())()
        if admitted is M.truth_value:
            admitted = M.IdentityCompare(M.Head(equation)(), L.DiscoveredEquationLabel)()
            fields = M.Tail(equation)()
            admitted = M.AndAtom(admitted, PG.ExactArity(fields, M.three, registry)())()
        if admitted is M.truth_value:
            variables = M.Head(fields)()
            admitted = M.AndAtom(
                M.IsPair(variables)(), TM.FiniteVariableChain(variables, registry)(),
            )()
        if admitted is M.truth_value:
            terms = M.Tail(fields)()
            checked_terms = ObservedArgumentOperations(
                terms, variables, operations, registry,
            )()
            admitted = M.Head(checked_terms)()
            used = M.Head(M.Tail(checked_terms)())()
            admitted = M.AndAtom(admitted, M.IsPair(used)())()
        if admitted is M.truth_value:
            checked = CheckOperationEquationDomain(
                equation, variables, variables, domain, domain, M.EmptyList,
                registry, replay_operations, M.EmptyList, M.EmptyList,
            )()
            active = M.Head(M.Tail(checked)())()
            replayed = M.Head(M.Tail(M.Tail(checked)())())()
            if M.Head(checked)() is M.truth_value:
                verdict = ObservedWitnessSubset(witnesses, replayed)()
                if verdict is M.truth_value:
                    evidence = M.Pair(
                        source, M.Pair(used, M.Pair(replayed, M.EmptyList)),
                    )
        super().__init__(
            inputs=M.Pair(source, M.Pair(domain, M.Pair(operations,
                M.Pair(replay_operations, M.Pair(registry, M.EmptyList))))),
            results=M.Pair(verdict, M.Pair(used,
                M.Pair(evidence, M.Pair(active, M.EmptyList)))),
        )


class ReplayObservedFindings(M.Edge):
    """Replay every source, sharing a registry and retaining per-source evidence.

    Result: verdict, joined used descriptors, evidence chain, registry.
    """

    def __init__(self, findings, domain, operations, replay_operations, registry):
        active = registry
        verdict = M.false_value
        used = M.EmptyList
        evidence = M.EmptyList
        if M.IdentityCompare(findings, M.EmptyList)() is M.truth_value:
            verdict = M.truth_value
        elif M.IsPair(findings)() is M.truth_value:
            current = ReplayObservedFinding(
                M.Head(findings)(), domain, operations, replay_operations, registry,
            )()
            fields = M.Tail(current)()
            current_used = M.Head(fields)()
            fields = M.Tail(fields)()
            current_evidence = M.Head(fields)()
            active = M.Head(M.Tail(fields)())()
            if M.Head(current)() is M.truth_value:
                remaining = ReplayObservedFindings(
                    M.Tail(findings)(), domain, operations, replay_operations, active,
                )()
                fields = M.Tail(remaining)()
                remaining_used = M.Head(fields)()
                fields = M.Tail(fields)()
                remaining_evidence = M.Head(fields)()
                active = M.Head(M.Tail(fields)())()
                verdict = M.Head(remaining)()
                if verdict is M.truth_value:
                    used = AppendObservedOperations(current_used, remaining_used)()
                    evidence = M.Pair(current_evidence, remaining_evidence)
        super().__init__(
            inputs=M.Pair(findings, M.Pair(domain, M.Pair(operations,
                M.Pair(replay_operations, M.Pair(registry, M.EmptyList))))),
            results=M.Pair(verdict, M.Pair(used,
                M.Pair(evidence, M.Pair(active, M.EmptyList)))),
        )


class BuildObservedStructureBundle(M.Edge):
    """Return a pending finite bundle and registry, or EmptyList and registry.

    Bundle fields: observed-structure-bundle-v1, exact carrier, used operation
    descriptors, source findings, replay evidence, PendingLabel.
    """

    def __init__(self, findings, domain, operations, registry):
        bundle = M.EmptyList
        active = registry
        try:
            admitted = M.AndAtom(M.IsPair(domain)(), TM.FiniteNatChain(domain, registry)())()
            admitted = M.AndAtom(admitted, M.IsPair(findings)())()
            admitted = M.AndAtom(admitted, M.IsPair(operations)())()
            if admitted is M.truth_value:
                executable = ObservedExecutableOperations(operations, registry)()
                admitted = M.Head(executable)()
            if admitted is M.truth_value:
                checked = ReplayObservedFindings(
                    findings, domain, operations, M.Head(M.Tail(executable)())(), registry,
                )()
                fields = M.Tail(checked)()
                used = M.Head(fields)()
                fields = M.Tail(fields)()
                evidence = M.Head(fields)()
                active = M.Head(M.Tail(fields)())()
                if M.Head(checked)() is M.truth_value:
                    bundle = M.Pair(
                        M.Char("observed-structure-bundle-v1"),
                        M.Pair(domain, M.Pair(used, M.Pair(findings,
                            M.Pair(evidence, M.Pair(L.PendingLabel, M.EmptyList))))),
                    )
        except Exception:
            bundle = M.EmptyList
            active = registry
        super().__init__(
            inputs=M.Pair(findings, M.Pair(domain, M.Pair(operations,
                M.Pair(registry, M.EmptyList)))),
            results=M.Pair(bundle, M.Pair(active, M.EmptyList)),
        )


class VerifyObservedStructureBundle(M.Edge):
    """Rebuild under the expected source scope and compare the entire bundle."""

    def __init__(self, bundle, findings, domain, operations, registry):
        verdict = M.false_value
        active = registry
        try:
            rebuilt = BuildObservedStructureBundle(findings, domain, operations, registry)()
            expected = M.Head(rebuilt)()
            active = M.Head(M.Tail(rebuilt)())()
            if M.IdentityCompare(expected, M.EmptyList)() is M.false_value:
                verdict = M.Compare(bundle, expected)()
        except Exception:
            verdict = M.false_value
            active = registry
        super().__init__(
            inputs=M.Pair(bundle, M.Pair(findings, M.Pair(domain, M.Pair(operations,
                M.Pair(registry, M.EmptyList))))),
            results=M.Pair(verdict, M.Pair(active, M.EmptyList)),
        )
