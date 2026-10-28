"""Machine-term operation descriptions stored in the constructor registry."""

from . import labels as L
from . import machine as M


class NatOperationDescription(M.Edge):
    """Describe the implemented arithmetic vocabulary without host callables."""

    def __init__(self, label):
        variables = M.Pair(M.Char("x"), M.Pair(M.Char("y"), M.EmptyList))
        name = M.EmptyList
        print_form = M.Char(" ? ")
        precedence = M.two
        polynomial = M.false_value
        degree_rule = M.Char("refuse")
        law_depth = M.Char("bounded")
        if M.IdentityCompare(label, L.ExprAddLabel)() is M.truth_value:
            name = M.Char("add")
            print_form = M.Char(" + ")
            polynomial = M.truth_value
            degree_rule = M.Char("max")
        elif M.IdentityCompare(label, L.ExprMulLabel)() is M.truth_value:
            name = M.Char("mul")
            print_form = M.Char("*")
            precedence = M.three
            polynomial = M.truth_value
            degree_rule = M.Char("sum")
        elif M.IdentityCompare(label, L.ExprPowLabel)() is M.truth_value:
            name = M.Char("pow")
            print_form = M.Char("^")
            precedence = M.four
            law_depth = M.Char("expensive")
        elif M.IdentityCompare(label, L.ExprModuloLabel)() is M.truth_value:
            name = M.Char("modulo")
            print_form = M.Char(" mod ")
            precedence = M.one
        elif M.IdentityCompare(label, L.ExprSubtractLabel)() is M.truth_value:
            name = M.Char("natural subtraction")
            print_form = M.Char(" - ")
        elif M.IdentityCompare(label, L.ExprGcdLabel)() is M.truth_value:
            name = M.Char("gcd")
            print_form = M.Char(" gcd ")
            precedence = M.three
        elif M.IdentityCompare(label, L.ExprDivLabel)() is M.truth_value:
            name = M.Char("divide")
            print_form = M.Char(" / ")
            precedence = M.three
        elif M.IdentityCompare(label, L.ExprEqLabel)() is M.truth_value:
            name = M.Char("compare_equality")
            print_form = M.Char(" == ")
            precedence = M.one
        elif M.IdentityCompare(label, L.ExprLtLabel)() is M.truth_value:
            name = M.Char("compare_less")
            print_form = M.Char(" < ")
            precedence = M.one
        elif M.IdentityCompare(label, L.ExprNegLabel)() is M.truth_value:
            variables = M.Pair(M.Char("x"), M.EmptyList)
            name = M.Char("negate")
            print_form = M.Char("neg")
            precedence = M.four
        elif M.IdentityCompare(label, L.DividesLabel)() is M.truth_value:
            name = M.Char("divides")
            print_form = M.Char(" divides ")
            precedence = M.one
        elif M.IdentityCompare(label, L.CoprimeLabel)() is M.truth_value:
            name = M.Char("coprime")
            print_form = M.Char(" coprime ")
            precedence = M.one
        elif M.IdentityCompare(label, L.NotCoprimeLabel)() is M.truth_value:
            name = M.Char("not_coprime")
            print_form = M.Char(" not_coprime ")
            precedence = M.one
        elif M.IdentityCompare(label, L.NatModEqLabel)() is M.truth_value:
            variables = M.Pair(M.Char("x"), M.Pair(M.Char("m"), M.Pair(M.Char("r"), M.EmptyList)))
            name = M.Char("compare_modulo")
            print_form = M.Char(" mod_eq ")
            precedence = M.one
        elif M.IdentityCompare(label, L.ImpliesLabel)() is M.truth_value:
            name = M.Char("implies")
            print_form = M.Char(" implies ")
            precedence = M.one
        result = M.EmptyList
        if M.IdentityCompare(name, M.EmptyList)() is M.false_value:
            result = M.Pair(
                name,
                M.Pair(variables, M.Pair(M.Pair(label, variables),
                    M.Pair(print_form, M.Pair(precedence,
                        M.Pair(polynomial, M.Pair(degree_rule,
                            M.Pair(law_depth, M.EmptyList))))))),
            )
        super().__init__(inputs=M.Pair(label, M.EmptyList), results=result)


class RegisteredNatOperationCatalog(M.Edge):
    """Read the registered descriptions; absence remains an empty catalog."""

    def __init__(self, registry):
        key = M.Pair(L.NatOperationCatalogLabel, M.EmptyList)
        record = M.TreeLookup(registry, key, registry)()
        result = M.EmptyList
        if M.IsPair(record)() is M.truth_value:
            if M.IdentityCompare(M.Head(record)(), L.NatOperationCatalogLabel)() is M.truth_value:
                result = M.Tail(record)()
        super().__init__(inputs=M.Pair(registry, M.EmptyList), results=result)


class RegisterNatOperationCatalog(M.Edge):
    """Install the implemented vocabulary once when a runtime register boots."""

    def __init__(self, registry):
        key = M.Pair(L.NatOperationCatalogLabel, M.EmptyList)
        record = M.TreeLookup(registry, key, registry)()
        result = registry
        if M.IdentityCompare(record, M.EmptyList)() is M.truth_value:
            entries = M.EmptyList
            entries = M.Pair(NatOperationDescription(L.ExprNegLabel)(), entries)
            entries = M.Pair(NatOperationDescription(L.ExprPowLabel)(), entries)
            entries = M.Pair(NatOperationDescription(L.ImpliesLabel)(), entries)
            entries = M.Pair(NatOperationDescription(L.NatModEqLabel)(), entries)
            entries = M.Pair(NatOperationDescription(L.NotCoprimeLabel)(), entries)
            entries = M.Pair(NatOperationDescription(L.CoprimeLabel)(), entries)
            entries = M.Pair(NatOperationDescription(L.DividesLabel)(), entries)
            entries = M.Pair(NatOperationDescription(L.ExprGcdLabel)(), entries)
            entries = M.Pair(NatOperationDescription(L.ExprSubtractLabel)(), entries)
            entries = M.Pair(NatOperationDescription(L.ExprModuloLabel)(), entries)
            entries = M.Pair(NatOperationDescription(L.ExprLtLabel)(), entries)
            entries = M.Pair(NatOperationDescription(L.ExprEqLabel)(), entries)
            entries = M.Pair(NatOperationDescription(L.ExprDivLabel)(), entries)
            entries = M.Pair(NatOperationDescription(L.ExprMulLabel)(), entries)
            entries = M.Pair(NatOperationDescription(L.ExprAddLabel)(), entries)
            record = M.Pair(L.NatOperationCatalogLabel, entries)
            result = M.TreeInsert(registry, key, record, registry)()
        super().__init__(inputs=M.Pair(registry, M.EmptyList), results=result)
