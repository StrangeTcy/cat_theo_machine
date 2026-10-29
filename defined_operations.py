"""Explicit composite Nat definitions over a closed primitive expression grammar."""

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


class RegisteredDefinedNatOperation(M.Edge):
    """Read and revalidate the body and matching descriptor at every use."""

    def __init__(self, label, registry):
        record = M.EmptyList
        try:
            key = M.Pair(L.NatOperationCatalogLabel, M.Pair(label, M.EmptyList))
            candidate = M.TreeLookup(registry, key, registry)()
            admitted = PG.ExactArity(candidate, M.four, registry)()
            if admitted is M.truth_value:
                admitted = M.Compare(M.Head(candidate)(), M.Char("defined-nat-operation-v1"))()
                fields = M.Tail(candidate)()
                admitted = M.AndAtom(admitted, M.IdentityCompare(M.Head(fields)(), label)())()
                formals = M.Head(M.Tail(fields)())()
                body = M.Head(M.Tail(M.Tail(fields)())())()
                admitted = M.AndAtom(admitted, DefinedSymbol(label, registry)())()
                admitted = M.AndAtom(admitted,
                    M.IdentityCompare(OC.NatOperationDescription(label)(), M.EmptyList)())()
                admitted = M.AndAtom(admitted, M.NotAtom(M.IdentityCompare(label, L.ExprIntLabel)())())()
                admitted = M.AndAtom(admitted, M.IsPair(formals)())()
                admitted = M.AndAtom(admitted, DefinedFormals(formals, registry)())()
                admitted = M.AndAtom(admitted, M.NotAtom(DefinedIdentityMember(label, formals)())())()
            if admitted is M.truth_value:
                admitted = DefinedBody(body, formals, registry)()
            if admitted is M.truth_value:
                descriptor = PG.LookupOperationByLabel(label, OC.RegisteredNatOperationCatalog(registry)())()
                admitted = M.Compare(descriptor, DefinedNatOperationDescription(label, formals)())()
            if admitted is M.truth_value:
                record = candidate
        except Exception:
            record = M.EmptyList
        super().__init__(inputs=M.Pair(label, M.Pair(registry, M.EmptyList)), results=record)


class RegisterDefinedNatOperation(M.Edge):
    """Register an inert primitive expression once; refusal preserves the registry.

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
                admitted = DefinedBody(body, formals, registry)()
            if admitted is M.truth_value:
                descriptor = DefinedNatOperationDescription(label, formals)()
                record = M.Pair(M.Char("defined-nat-operation-v1"),
                    M.Pair(label, M.Pair(formals, M.Pair(body, M.EmptyList))))
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
            body = M.Head(M.Tail(M.Tail(fields)())())()
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
