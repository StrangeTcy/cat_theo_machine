"""Registered Nat expressions with checked, frozen dependency expansion."""

from . import labels as L
from . import machine as M
from . import operation_catalog as OC
from . import playground as PG
from .math import arithmetic as A


class DefinedIdentityMember(M.Edge):
    def __init__(self, symbol, chain):
        verdict = M.false_value
        if M.IsPair(chain)() is M.truth_value:
            verdict = M.IdentityCompare(symbol, M.Head(chain)())()
            if verdict is M.false_value:
                verdict = DefinedIdentityMember(symbol, M.Tail(chain)())()
        super().__init__(inputs=M.Pair(symbol, chain), results=verdict)


class DefinedSymbol(M.Edge):
    def __init__(self, symbol, registry):
        verdict = M.NotAtom(M.IsPair(symbol)())()
        verdict = M.AndAtom(verdict, M.NotAtom(M.IdentityCompare(symbol, M.EmptyList)())())()
        verdict = M.AndAtom(verdict, M.NotAtom(A.IsNat(symbol, registry)())())()
        verdict = M.AndAtom(verdict, M.NotAtom(M.IsWhole(symbol, registry)())())()
        verdict = M.AndAtom(verdict, M.NotAtom(M.OrAtom(
            M.IdentityCompare(symbol, M.truth_value)(),
            M.IdentityCompare(symbol, M.false_value)(),
        )())())()
        super().__init__(inputs=M.Pair(symbol, M.Pair(registry, M.EmptyList)), results=verdict)


class DefinedFormals(M.Edge):
    def __init__(self, formals, registry, seen=M.EmptyList):
        verdict = M.false_value
        if M.IdentityCompare(formals, M.EmptyList)() is M.truth_value:
            verdict = M.truth_value
        elif M.IsPair(formals)() is M.truth_value:
            formal = M.Head(formals)()
            if DefinedSymbol(formal, registry)() is M.truth_value:
                if DefinedIdentityMember(formal, seen)() is M.false_value:
                    verdict = DefinedFormals(M.Tail(formals)(), registry, M.Pair(formal, seen))()
        super().__init__(inputs=M.Pair(formals, M.Pair(registry, seen)), results=verdict)


class DefinedBody(M.Edge):
    """Admit only declared formals, Nat constants, Add, Mul, and literal Nat powers."""

    def __init__(self, body, formals, registry):
        verdict = DefinedIdentityMember(body, formals)()
        if verdict is M.false_value:
            if A.IsNat(body, registry)() is M.truth_value:
                verdict = M.NotAtom(M.NatLess(body, M.Zero, registry)())()
            elif M.IsPair(body)() is M.truth_value:
                label = M.Head(body)()
                arguments = M.Tail(body)()
                if M.IdentityCompare(label, L.ExprIntLabel)() is M.truth_value:
                    if PG.ExactArity(arguments, M.one, registry)() is M.truth_value:
                        constant = M.Head(arguments)()
                        if A.IsNat(constant, registry)() is M.truth_value:
                            verdict = M.NotAtom(M.NatLess(constant, M.Zero, registry)())()
                elif PG.ExactArity(arguments, M.two, registry)() is M.truth_value:
                    left = M.Head(arguments)()
                    right = M.Head(M.Tail(arguments)())()
                    if M.IdentityCompare(label, L.ExprPowLabel)() is M.truth_value:
                        if A.IsNat(right, registry)() is M.truth_value:
                            if M.NatLess(right, M.Zero, registry)() is M.false_value:
                                verdict = DefinedBody(left, formals, registry)()
                    elif M.OrAtom(M.IdentityCompare(label, L.ExprAddLabel)(),
                        M.IdentityCompare(label, L.ExprMulLabel)())() is M.truth_value:
                        verdict = M.AndAtom(DefinedBody(left, formals, registry)(),
                            DefinedBody(right, formals, registry)())()
        super().__init__(inputs=M.Pair(body, M.Pair(formals, M.Pair(registry, M.EmptyList))), results=verdict)


class DefinedNatOperationDescription(M.Edge):
    """Describe executable syntax without asserting polynomial proof authority."""

    def __init__(self, label, formals):
        metadata = M.Pair(M.Char(" defined "), M.Pair(M.four,
            M.Pair(M.false_value, M.Pair(M.Char("refuse"), M.Pair(M.Char("expensive"), M.EmptyList)))))
        descriptor = M.Pair(M.Char("defined Nat operation"),
            M.Pair(formals, M.Pair(M.Pair(label, formals), metadata)))
        super().__init__(inputs=M.Pair(label, formals), results=descriptor)


class DefinedSyntaxIdentity(M.Edge):
    """Compare expression shape while retaining every atomic reference."""

    def __init__(self, left, right):
        verdict = M.IdentityCompare(left, right)()
        if verdict is M.false_value:
            if M.IsPair(left)() is M.truth_value:
                if M.IsPair(right)() is M.truth_value:
                    verdict = M.AndAtom(DefinedSyntaxIdentity(M.Head(left)(), M.Head(right)())(),
                        DefinedSyntaxIdentity(M.Tail(left)(), M.Tail(right)())())()
        super().__init__(inputs=M.Pair(left, right), results=verdict)


class DefinedDependencyIdentity(M.Edge):
    """Dependency receipts pin the exact registered records in call order."""

    def __init__(self, left, right):
        verdict = M.false_value
        if M.IdentityCompare(left, M.EmptyList)() is M.truth_value:
            verdict = M.IdentityCompare(right, M.EmptyList)()
        elif M.IsPair(left)() is M.truth_value:
            if M.IsPair(right)() is M.truth_value:
                if M.IdentityCompare(M.Head(left)(), M.Head(right)())() is M.truth_value:
                    verdict = DefinedDependencyIdentity(M.Tail(left)(), M.Tail(right)())()
        super().__init__(inputs=M.Pair(left, right), results=verdict)


class DefinedSameArity(M.Edge):
    def __init__(self, left, right):
        verdict = M.false_value
        if M.IdentityCompare(left, M.EmptyList)() is M.truth_value:
            verdict = M.IdentityCompare(right, M.EmptyList)()
        elif M.IsPair(left)() is M.truth_value:
            if M.IsPair(right)() is M.truth_value:
                verdict = DefinedSameArity(M.Tail(left)(), M.Tail(right)())()
        super().__init__(inputs=M.Pair(left, right), results=verdict)


class DefinedOperationExpansion(M.Edge):
    """Project primitive syntax from a validated v1 or v2 record."""

    def __init__(self, record):
        fields = M.Tail(M.Tail(M.Tail(record)())())()
        result = M.Head(fields)()
        if M.Compare(M.Head(record)(), M.Char("defined-nat-operation-v2"))() is M.truth_value:
            result = M.Head(M.Tail(fields)())()
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=result)


class DefinedSourceArguments(M.Edge):
    def __init__(self, arguments, formals, registry, seen):
        verdict = M.IdentityCompare(arguments, M.EmptyList)()
        expanded = M.EmptyList
        dependencies = M.EmptyList
        if M.IsPair(arguments)() is M.truth_value:
            first = DefinedSourceExpansion(M.Head(arguments)(), formals, registry, seen)()
            if M.Head(first)() is M.truth_value:
                rest = DefinedSourceArguments(M.Tail(arguments)(), formals, registry, seen)()
                verdict = M.Head(rest)()
                if verdict is M.truth_value:
                    expanded = M.Pair(M.Head(M.Tail(first)())(), M.Head(M.Tail(rest)())())
                    dependencies = PG.ChainConcat(M.Head(M.Tail(M.Tail(first)())())(),
                        M.Head(M.Tail(M.Tail(rest)())())())()
        super().__init__(inputs=M.Pair(arguments, M.Pair(formals, M.Pair(registry, seen))),
            results=M.Pair(verdict, M.Pair(expanded, M.Pair(dependencies, M.EmptyList))))


class DefinedSourceExpansion(M.Edge):
    """Expand earlier definitions by identity substitution and record their use."""

    def __init__(self, source, formals, registry, seen=M.EmptyList):
        verdict = DefinedBody(source, formals, registry)()
        expanded = M.EmptyList
        dependencies = M.EmptyList
        if verdict is M.truth_value:
            expanded = source
        elif M.IsPair(source)() is M.truth_value:
            label = M.Head(source)()
            arguments = M.Tail(source)()
            primitive = M.OrAtom(M.IdentityCompare(label, L.ExprAddLabel)(),
                M.OrAtom(M.IdentityCompare(label, L.ExprMulLabel)(),
                    M.IdentityCompare(label, L.ExprPowLabel)())())()
            definition = M.EmptyList
            admitted = M.false_value
            if primitive is M.truth_value:
                admitted = PG.ExactArity(arguments, M.two, registry)()
                if admitted is M.truth_value:
                    if M.IdentityCompare(label, L.ExprPowLabel)() is M.truth_value:
                        exponent = M.Head(M.Tail(arguments)())()
                        admitted = A.IsNat(exponent, registry)()
            else:
                definition = RegisteredDefinedNatOperation(label, registry, seen)()
                if M.IsPair(definition)() is M.truth_value:
                    dependency_formals = M.Head(M.Tail(M.Tail(definition)())())()
                    admitted = DefinedSameArity(dependency_formals, arguments)()
            if admitted is M.truth_value:
                checked = DefinedSourceArguments(arguments, formals, registry, seen)()
                admitted = M.Head(checked)()
            if admitted is M.truth_value:
                expanded_arguments = M.Head(M.Tail(checked)())()
                dependencies = M.Head(M.Tail(M.Tail(checked)())())()
                if primitive is M.truth_value:
                    expanded = M.Pair(label, expanded_arguments)
                else:
                    expanded = ExpandDefinedBody(DefinedOperationExpansion(definition)(),
                        dependency_formals, expanded_arguments)()
                    dependencies = M.Pair(definition, dependencies)
                verdict = DefinedBody(expanded, formals, registry)()
        if verdict is M.false_value:
            expanded = M.EmptyList
            dependencies = M.EmptyList
        super().__init__(inputs=M.Pair(source, M.Pair(formals, M.Pair(registry, seen))),
            results=M.Pair(verdict, M.Pair(expanded, M.Pair(dependencies, M.EmptyList))))


class RegisteredDefinedNatOperation(M.Edge):
    """Read and revalidate the body and matching descriptor at every use."""

    def __init__(self, label, registry, seen=M.EmptyList):
        record = M.EmptyList
        try:
            key = M.Pair(L.NatOperationCatalogLabel, M.Pair(label, M.EmptyList))
            candidate = M.TreeLookup(registry, key, registry)()
            version_one = M.false_value
            version_two = M.false_value
            if PG.ExactArity(candidate, M.four, registry)() is M.truth_value:
                version_one = M.Compare(M.Head(candidate)(), M.Char("defined-nat-operation-v1"))()
            elif PG.ExactArity(candidate, M.six, registry)() is M.truth_value:
                version_two = M.Compare(M.Head(candidate)(), M.Char("defined-nat-operation-v2"))()
            admitted = M.AndAtom(M.OrAtom(version_one, version_two)(),
                M.NotAtom(DefinedIdentityMember(label, seen)())())()
            if admitted is M.truth_value:
                fields = M.Tail(candidate)()
                admitted = M.AndAtom(admitted, M.IdentityCompare(M.Head(fields)(), label)())()
                formals = M.Head(M.Tail(fields)())()
                source_fields = M.Tail(M.Tail(fields)())()
                source = M.Head(source_fields)()
                admitted = M.AndAtom(admitted, DefinedSymbol(label, registry)())()
                admitted = M.AndAtom(admitted,
                    M.IdentityCompare(OC.NatOperationDescription(label)(), M.EmptyList)())()
                admitted = M.AndAtom(admitted, M.NotAtom(M.IdentityCompare(label, L.ExprIntLabel)())())()
                admitted = M.AndAtom(admitted, M.IsPair(formals)())()
                admitted = M.AndAtom(admitted, DefinedFormals(formals, registry)())()
                admitted = M.AndAtom(admitted, M.NotAtom(DefinedIdentityMember(label, formals)())())()
            if admitted is M.truth_value:
                if version_one is M.truth_value:
                    admitted = DefinedBody(source, formals, registry)()
                else:
                    checked = DefinedSourceExpansion(source, formals, registry, M.Pair(label, seen))()
                    admitted = M.Head(checked)()
                    body = M.Head(M.Tail(source_fields)())()
                    dependencies = M.Head(M.Tail(M.Tail(source_fields)())())()
                    admitted = M.AndAtom(admitted,
                        DefinedSyntaxIdentity(body, M.Head(M.Tail(checked)())())())()
                    admitted = M.AndAtom(admitted, DefinedDependencyIdentity(dependencies,
                        M.Head(M.Tail(M.Tail(checked)())())())())()
            if admitted is M.truth_value:
                descriptor = PG.LookupOperationByLabel(label, OC.RegisteredNatOperationCatalog(registry)())()
                admitted = M.Compare(descriptor, DefinedNatOperationDescription(label, formals)())()
                if admitted is M.truth_value:
                    admitted = DefinedSyntaxIdentity(M.Head(M.Tail(descriptor)())(), formals)()
                if admitted is M.truth_value:
                    admitted = DefinedSyntaxIdentity(M.Head(M.Tail(M.Tail(descriptor)())())(),
                        M.Pair(label, formals))()
            if admitted is M.truth_value:
                record = candidate
        except Exception:
            record = M.EmptyList
        super().__init__(inputs=M.Pair(label, M.Pair(registry, M.EmptyList)), results=record)


class ExecutableNatOperationDescriptor(M.Edge):
    """Return Pair(descriptor, Pair(validated custom record or EmptyList, EmptyList))."""

    def __init__(self, label, registry):
        descriptor = OC.NatOperationDescription(label)()
        definition = M.EmptyList
        if M.IdentityCompare(descriptor, M.EmptyList)() is M.truth_value:
            definition = RegisteredDefinedNatOperation(label, registry)()
            if M.IsPair(definition)() is M.truth_value:
                formals = M.Head(M.Tail(M.Tail(definition)())())()
                descriptor = DefinedNatOperationDescription(label, formals)()
        super().__init__(inputs=M.Pair(label, M.Pair(registry, M.EmptyList)),
            results=M.Pair(descriptor, M.Pair(definition, M.EmptyList)))


class RegisterDefinedNatOperation(M.Edge):
    """Register a checked expression once; refusal preserves the registry.

    Return Pair(verdict, Pair(registry, Pair(descriptor, EmptyList))).
    Formals are a nonempty chain of distinct anonymous atomic identities.
    The definition key is Pair(NatOperationCatalogLabel, Pair(label, EmptyList));
    registration adds no rewrite rule or universal mathematical claim.
    """

    def __init__(self, label, formals, body, registry):
        verdict = M.false_value
        active = registry
        descriptor = M.EmptyList
        try:
            admitted = DefinedSymbol(label, registry)()
            admitted = M.AndAtom(admitted,
                M.IdentityCompare(OC.NatOperationDescription(label)(), M.EmptyList)())()
            admitted = M.AndAtom(admitted, M.NotAtom(M.IdentityCompare(label, L.ExprIntLabel)())())()
            admitted = M.AndAtom(admitted, M.IsPair(formals)())()
            admitted = M.AndAtom(admitted, DefinedFormals(formals, registry)())()
            admitted = M.AndAtom(admitted, M.NotAtom(DefinedIdentityMember(label, formals)())())()
            key = M.Pair(L.NatOperationCatalogLabel, M.Pair(label, M.EmptyList))
            admitted = M.AndAtom(admitted,
                M.IdentityCompare(M.TreeLookup(registry, key, registry)(), M.EmptyList)())()
            catalog = OC.RegisteredNatOperationCatalog(registry)()
            admitted = M.AndAtom(admitted,
                M.IdentityCompare(PG.LookupOperationByLabel(label, catalog)(), M.EmptyList)())()
            if admitted is M.truth_value:
                checked = DefinedSourceExpansion(body, formals, registry, M.Pair(label, M.EmptyList))()
                admitted = M.Head(checked)()
            if admitted is M.truth_value:
                descriptor = DefinedNatOperationDescription(label, formals)()
                record = M.Pair(M.Char("defined-nat-operation-v1"),
                    M.Pair(label, M.Pair(formals, M.Pair(body, M.EmptyList))))
                expanded = M.Head(M.Tail(checked)())()
                dependencies = M.Head(M.Tail(M.Tail(checked)())())()
                if M.IsPair(dependencies)() is M.truth_value:
                    record = M.Pair(M.Char("defined-nat-operation-v2"), M.Pair(label,
                        M.Pair(formals, M.Pair(body, M.Pair(expanded, M.Pair(dependencies, M.EmptyList))))))
                active = M.TreeInsert(registry, key, record, registry)()
                active = OC.ExtendNatOperationCatalog(descriptor, active)()
                verdict = M.truth_value
        except Exception:
            verdict = M.false_value
            active = registry
            descriptor = M.EmptyList
        super().__init__(
            inputs=M.Pair(label, M.Pair(formals, M.Pair(body, M.Pair(registry, M.EmptyList)))),
            results=M.Pair(verdict, M.Pair(active, M.Pair(descriptor, M.EmptyList))),
        )


class DefinedArgumentValues(M.Edge):
    def __init__(self, formals, arguments, environment, registry, operations):
        verdict = M.false_value
        values = M.EmptyList
        active = registry
        if M.IdentityCompare(formals, M.EmptyList)() is M.truth_value:
            verdict = M.IdentityCompare(arguments, M.EmptyList)()
        elif M.IsPair(arguments)() is M.truth_value:
            evaluated = PG.EvaluateNatExpr(M.Head(arguments)(), environment, registry, operations)()
            value = M.Head(evaluated)()
            active = M.Head(M.Tail(evaluated)())()
            if A.IsNat(value, active)() is M.truth_value:
                if M.NatLess(value, M.Zero, active)() is M.false_value:
                    rest = DefinedArgumentValues(M.Tail(formals)(), M.Tail(arguments)(),
                        environment, active, operations)()
                    verdict = M.Head(rest)()
                    values = M.Pair(value, M.Head(M.Tail(rest)())())
                    active = M.Head(M.Tail(M.Tail(rest)())())()
        super().__init__(
            inputs=M.Pair(formals, M.Pair(arguments, M.Pair(environment, M.Pair(registry, M.EmptyList)))),
            results=M.Pair(verdict, M.Pair(values, M.Pair(active, M.EmptyList))),
        )


class DefinedBoundValue(M.Edge):
    def __init__(self, symbol, formals, values):
        result = M.EmptyList
        if M.IsPair(formals)() is M.truth_value:
            if M.IdentityCompare(symbol, M.Head(formals)())() is M.truth_value:
                result = M.Head(values)()
            else:
                result = DefinedBoundValue(symbol, M.Tail(formals)(), M.Tail(values)())()
        super().__init__(inputs=M.Pair(symbol, M.Pair(formals, values)), results=result)


class ExpandDefinedBody(M.Edge):
    """Substitute evaluated Nats by reference identity; inserted values bind nothing."""

    def __init__(self, body, formals, values):
        result = DefinedBoundValue(body, formals, values)()
        if M.IdentityCompare(result, M.EmptyList)() is M.truth_value:
            result = body
            if M.IsPair(body)() is M.truth_value:
                label = M.Head(body)()
                arguments = M.Tail(body)()
                if M.IdentityCompare(label, L.ExprIntLabel)() is M.false_value:
                    result = M.Pair(label,
                        M.Pair(ExpandDefinedBody(M.Head(arguments)(), formals, values)(),
                            M.Pair(ExpandDefinedBody(M.Head(M.Tail(arguments)())(), formals, values)(), M.EmptyList)))
        super().__init__(inputs=M.Pair(body, M.Pair(formals, values)), results=result)


class EvaluateDefinedNatOperation(M.Edge):
    """Execute a revalidated registered body through the existing primitive evaluator."""

    def __init__(self, label, arguments, environment, registry, operations):
        result = M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
        definition = RegisteredDefinedNatOperation(label, registry)()
        if M.IsPair(definition)() is M.truth_value:
            fields = M.Tail(definition)()
            formals = M.Head(M.Tail(fields)())()
            body = DefinedOperationExpansion(definition)()
            evaluated = DefinedArgumentValues(formals, arguments, environment, registry, operations)()
            active = M.Head(M.Tail(M.Tail(evaluated)())())()
            result = M.Pair(M.EmptyList, M.Pair(active, M.EmptyList))
            if M.Head(evaluated)() is M.truth_value:
                expanded = ExpandDefinedBody(body, formals, M.Head(M.Tail(evaluated)())())()
                primitives = M.Pair(OC.NatOperationDescription(L.ExprAddLabel)(),
                    M.Pair(OC.NatOperationDescription(L.ExprMulLabel)(),
                        M.Pair(OC.NatOperationDescription(L.ExprPowLabel)(), M.EmptyList)))
                result = PG.EvaluateNatExpr(expanded, M.EmptyList, active, primitives)()
        super().__init__(inputs=M.Pair(label, M.Pair(arguments, M.Pair(environment,
            M.Pair(registry, M.Pair(operations, M.EmptyList))))), results=result)
