from __future__ import annotations

from .. import machine as M


class IsNat(M.Edge):
    def __init__(self, x, registry):
        self.result = self._check(x, registry)
        super().__init__(inputs=M.Pair(x, M.Pair(registry, M.EmptyList)), results=self.result)

    def _check(self, x, registry):
        rep = M.NatRepOf(x, registry)()
        if M.IdentityCompare(rep, M.EmptyList)() is M.truth_value:
            return M.false_value
        return M.truth_value

    def __call__(self):
        return self.result


class Add(M.Edge):
    def __init__(self, a, b, registry):
        nat_a = IsNat(a, registry)()
        nat_b = IsNat(b, registry)()
        if M.AndAtom(nat_a, nat_b)() is M.truth_value:
            atom_result = self._add(a, b, registry)
        else:
            atom_result = M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))

        self.result = atom_result
        super().__init__(inputs=M.Pair(a, M.Pair(b, M.Pair(registry, M.EmptyList))), results=self.result)

    def _add(self, a, b, registry):
        rep_a = M.NatRepOf(a, registry)()
        rep_b = M.NatRepOf(b, registry)()
        if M.IdentityCompare(rep_a, M.EmptyList)() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
        if M.IdentityCompare(rep_b, M.EmptyList)() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
        sum_rep = M.GMPRep(rep_a() + rep_b())
        return M.NatFromRep(sum_rep, registry)()

    def __call__(self):
        return self.result


class Multiply(M.Edge):
    def __init__(self, a, b, registry):
        nat_a = IsNat(a, registry)()
        nat_b = IsNat(b, registry)()
        if M.AndAtom(nat_a, nat_b)() is M.truth_value:
            atom_result = self._mul(a, b, registry)
        else:
            atom_result = M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))

        self.result = atom_result
        super().__init__(inputs=M.Pair(a, M.Pair(b, M.Pair(registry, M.EmptyList))), results=self.result)

    def _mul(self, a, b, registry):
        rep_a = M.NatRepOf(a, registry)()
        rep_b = M.NatRepOf(b, registry)()
        if M.IdentityCompare(rep_a, M.EmptyList)() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
        if M.IdentityCompare(rep_b, M.EmptyList)() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
        product_rep = M.GMPRep(rep_a() * rep_b())
        return M.NatFromRep(product_rep, registry)()

    def __call__(self):
        return self.result


Succ = M.Succ
NatPred = M.NatPred
Count = M.Count
NatEq = M.NatEq
NatLess = M.NatLess
FractionLabel = M.FractionLabel
Fraction = M.Fraction
FractionLeft = M.FractionLeft
FractionRight = M.FractionRight
IsFraction = M.IsFraction
WholeLabel = M.WholeLabel
Whole = M.Whole
WholeLeft = M.WholeLeft
WholeRight = M.WholeRight
IsWhole = M.IsWhole
WholeAdd = M.WholeAdd
WholeMultiply = M.WholeMultiply
NatText = M.NatText
FractionText = M.FractionText
WholeText = M.WholeText

one = M.one
two = M.two
three = M.three
four = M.four
five = M.five
six = M.six
seven = M.seven
eight = M.eight
nine = M.nine

__all__ = [
    "IsNat",
    "Add",
    "Multiply",
    "Succ",
    "NatPred",
    "Count",
    "NatEq",
    "NatLess",
    "FractionLabel",
    "Fraction",
    "FractionLeft",
    "FractionRight",
    "IsFraction",
    "WholeLabel",
    "Whole",
    "WholeLeft",
    "WholeRight",
    "IsWhole",
    "WholeAdd",
    "WholeMultiply",
    "NatText",
    "FractionText",
    "WholeText",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
]


def sync_from_namespace(namespace):
    for name in (
        "one",
        "two",
        "three",
        "four",
        "five",
        "six",
        "seven",
        "eight",
        "nine",
    ):
        if name in namespace:
            globals()[name] = namespace[name]
