from __future__ import annotations

from . import labels as L
from . import machine as M


# ============================================================
# Chain utilities over machine Pair chains
# ============================================================


class ChainContains(M.Edge):
    def __init__(self, chain, element):
        self.result = self._contains(chain, element)
        super().__init__(inputs=M.Pair(chain, M.Pair(element, M.EmptyList)), results=self.result)

    def _contains(self, chain, element):
        if M.IdentityCompare(chain, M.EmptyList)() is M.truth_value:
            return M.false_value
        if M.TermEqual(M.Head(chain)(), element)() is M.truth_value:
            return M.truth_value
        return self._contains(M.Tail(chain)(), element)

    def __call__(self):
        return self.result


class ChainAppend(M.Edge):
    def __init__(self, chain, tail):
        self.result = self._append(chain, tail)
        super().__init__(inputs=M.Pair(chain, M.Pair(tail, M.EmptyList)), results=self.result)

    def _append(self, chain, tail):
        if M.IdentityCompare(chain, M.EmptyList)() is M.truth_value:
            return tail
        return M.Pair(M.Head(chain)(), self._append(M.Tail(chain)(), tail))

    def __call__(self):
        return self.result


class ChainLength(M.Edge):
    """A bare label atom counts as a one-element chain; EmptyList is the
    zero-element chain; otherwise the chain is a Pair spine."""

    def __init__(self, chain):
        self.result = self._length(chain)
        super().__init__(inputs=M.Pair(chain, M.EmptyList), results=self.result)

    def _length(self, chain):
        if M.IdentityCompare(chain, M.EmptyList)() is M.truth_value:
            return M.Zero
        if M.IsPair(chain)() is M.truth_value:
            grown = M.Succ(self._length(M.Tail(chain)()), M.AllConstructors)()
            return M.Head(grown)()
        return M.one

    def __call__(self):
        return self.result


class TurnAdd(M.Edge):
    """Machine-nat addition modulo three. Inputs are nat atoms of value
    zero, one, or two, so a single three-fold predecessor step is
    enough."""

    def __init__(self, left, right):
        summed = M.Add(left, right, M.AllConstructors)()
        total = M.Head(summed)()
        overflow = M.NatLess(M.two, total, M.AllConstructors)()
        if overflow is M.truth_value:
            first = M.NatPred(total, M.AllConstructors)()
            second = M.NatPred(M.Head(first)(), M.AllConstructors)()
            third = M.NatPred(M.Head(second)(), M.AllConstructors)()
            self.result = M.Head(third)()
        else:
            self.result = total
        super().__init__(inputs=M.Pair(left, M.Pair(right, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class TurnNegate(M.Edge):
    """Negation modulo three on nat atoms: 0 to 0, 1 to 2, 2 to 1."""

    def __init__(self, turn):
        is_one = M.NatEq(turn, M.one, M.AllConstructors)()
        is_two = M.NatEq(turn, M.two, M.AllConstructors)()
        if is_one is M.truth_value:
            self.result = M.two
        elif is_two is M.truth_value:
            self.result = M.one
        else:
            self.result = M.Zero
        super().__init__(inputs=M.Pair(turn, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class AxisLabelFromTurn(M.Edge):
    def __init__(self, turn):
        is_one = M.NatEq(turn, M.one, M.AllConstructors)()
        is_two = M.NatEq(turn, M.two, M.AllConstructors)()
        if is_one is M.truth_value:
            self.result = L.DecoyBetaLabel
        elif is_two is M.truth_value:
            self.result = L.DecoyGammaLabel
        else:
            self.result = L.DecoyAlphaLabel
        super().__init__(inputs=M.Pair(turn, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class AxisTurnOf(M.Edge):
    """The reflection axis label as a turn nat: alpha to zero, beta to
    one, gamma to two. The inverse of AxisLabelFromTurn."""

    def __init__(self, axis_label):
        is_beta = M.IdentityCompare(axis_label, L.DecoyBetaLabel)()
        is_gamma = M.IdentityCompare(axis_label, L.DecoyGammaLabel)()
        if is_beta is M.truth_value:
            self.result = M.one
        elif is_gamma is M.truth_value:
            self.result = M.two
        else:
            self.result = M.Zero
        super().__init__(inputs=M.Pair(axis_label, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RotationKindFromTurn(M.Edge):
    def __init__(self, turn):
        is_one = M.NatEq(turn, M.one, M.AllConstructors)()
        is_two = M.NatEq(turn, M.two, M.AllConstructors)()
        if is_one is M.truth_value:
            self.result = L.TriangleRotationKindLabel
        elif is_two is M.truth_value:
            self.result = M.Pair(L.TriangleRotationKindLabel, M.Pair(L.TriangleRotationKindLabel, M.EmptyList))
        else:
            self.result = L.TriangleIdentityKindLabel
        super().__init__(inputs=M.Pair(turn, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


# ============================================================
# Triangle carrier
#
# Elements are machine terms:
#   (TriangleTransform rotation120)            one turn
#   (TriangleTransform (rotation120 rotation)) two turns
#   (TriangleTransform (reflection120 (alpha)))
#   (TriangleTransform (reflection120 (beta)))
#   (TriangleTransform (reflection120 (gamma)))
#   (TriangleTransform identity)
#
# Composition reads as "do the right operand first, then the left
# operand". Rotation turns add modulo three. A reflection over axis t
# followed by a rotation of j turns lands on axis (t + j); a rotation
# of j turns followed by a reflection over axis t lands on axis
# (t - j); a reflection over axis u followed by a reflection over
# axis t rotates by (u - t). These are the dihedral relations, and
# they make noncommutativity a concrete observed fact rather than an
# assumption.
# ============================================================


class TriangleTransform(M.Edge):
    def __init__(self, kind):
        self.result = M.Pair(L.TriangleTransformLabel, M.Pair(kind, M.EmptyList))
        super().__init__(inputs=M.Pair(kind, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TriangleCarrierElements(M.Edge):
    def __init__(self):
        self.result = M.Pair(
            TriangleTransform(L.TriangleRotationKindLabel)(),
            M.Pair(
                TriangleTransform(M.Pair(L.TriangleRotationKindLabel, M.Pair(L.TriangleRotationKindLabel, M.EmptyList)))(),
                M.Pair(
                    TriangleTransform(M.Pair(L.TriangleReflectionKindLabel, M.Pair(L.DecoyAlphaLabel, M.EmptyList)))(),
                    M.Pair(
                        TriangleTransform(M.Pair(L.TriangleReflectionKindLabel, M.Pair(L.DecoyBetaLabel, M.EmptyList)))(),
                        M.Pair(
                            TriangleTransform(M.Pair(L.TriangleReflectionKindLabel, M.Pair(L.DecoyGammaLabel, M.EmptyList)))(),
                            M.Pair(TriangleTransform(L.TriangleIdentityKindLabel)(), M.EmptyList),
                        ),
                    ),
                ),
            ),
        )
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class TriangleCarrierProduct(M.Edge):
    def __init__(self, left, right):
        left_kind = M.Head(M.Tail(left)())()
        right_kind = M.Head(M.Tail(right)())()
        left_is_identity = M.IdentityCompare(left_kind, L.TriangleIdentityKindLabel)()
        right_is_identity = M.IdentityCompare(right_kind, L.TriangleIdentityKindLabel)()
        if M.IsPair(left_kind)() is M.truth_value:
            left_is_reflection = M.IdentityCompare(M.Head(left_kind)(), L.TriangleReflectionKindLabel)()
        else:
            left_is_reflection = M.false_value
        if M.IsPair(right_kind)() is M.truth_value:
            right_is_reflection = M.IdentityCompare(M.Head(right_kind)(), L.TriangleReflectionKindLabel)()
        else:
            right_is_reflection = M.false_value

        if M.OrAtom(left_is_identity, right_is_identity)() is M.truth_value:
            if left_is_identity is M.truth_value:
                self.result = right
            else:
                self.result = left
        elif M.AndAtom(left_is_reflection, right_is_reflection)() is M.truth_value:
            left_turn = AxisTurnOf(M.Head(M.Tail(left_kind)())())()
            right_turn = AxisTurnOf(M.Head(M.Tail(right_kind)())())()
            total = TurnAdd(left_turn, TurnNegate(right_turn)())()
            kind = RotationKindFromTurn(total)()
            self.result = TriangleTransform(kind)()
        elif M.AndAtom(left_is_reflection, M.NotAtom(right_is_reflection)())() is M.truth_value:
            axis_turn = AxisTurnOf(M.Head(M.Tail(left_kind)())())()
            turn = ChainLength(right_kind)()
            kind = M.Pair(
                L.TriangleReflectionKindLabel,
                M.Pair(AxisLabelFromTurn(TurnAdd(axis_turn, TurnNegate(turn)())())(), M.EmptyList),
            )
            self.result = TriangleTransform(kind)()
        elif M.AndAtom(M.NotAtom(left_is_reflection)(), right_is_reflection)() is M.truth_value:
            turn = ChainLength(left_kind)()
            axis_turn = AxisTurnOf(M.Head(M.Tail(right_kind)())())()
            kind = M.Pair(
                L.TriangleReflectionKindLabel,
                M.Pair(AxisLabelFromTurn(TurnAdd(axis_turn, turn)())(), M.EmptyList),
            )
            self.result = TriangleTransform(kind)()
        else:
            left_turns = ChainLength(left_kind)()
            right_turns = ChainLength(right_kind)()
            total = TurnAdd(left_turns, right_turns)()
            kind = RotationKindFromTurn(total)()
            self.result = TriangleTransform(kind)()

        super().__init__(inputs=M.Pair(left, M.Pair(right, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class TriangleCarrierIndexOf(M.Edge):
    def __init__(self, element):
        elements = TriangleCarrierElements()()
        self.result = self._index_of(elements, element, M.Zero)
        super().__init__(inputs=M.Pair(element, M.EmptyList), results=self.result)

    def _index_of(self, chain, element, current):
        if M.IdentityCompare(chain, M.EmptyList)() is M.truth_value:
            return M.Zero
        if M.TermEqual(M.Head(chain)(), element)() is M.truth_value:
            return current
        grown = M.Succ(current, M.AllConstructors)()
        return self._index_of(M.Tail(chain)(), element, M.Head(grown)())

    def __call__(self):
        return self.result


class TriangleCarrierRenamedElements(M.Edge):
    def __init__(self):
        self.result = M.Pair(
            M.Pair(L.RenamedElementLabel, M.Pair(M.Zero, M.EmptyList)),
            M.Pair(
                M.Pair(L.RenamedElementLabel, M.Pair(M.one, M.EmptyList)),
                M.Pair(
                    M.Pair(L.RenamedElementLabel, M.Pair(M.two, M.EmptyList)),
                    M.Pair(
                        M.Pair(L.RenamedElementLabel, M.Pair(M.three, M.EmptyList)),
                        M.Pair(
                            M.Pair(L.RenamedElementLabel, M.Pair(M.four, M.EmptyList)),
                            M.Pair(M.Pair(L.RenamedElementLabel, M.Pair(M.five, M.EmptyList)), M.EmptyList),
                        ),
                    ),
                ),
            ),
        )
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class Renamer(M.Edge):
    """Positional bijection from the triangle carrier onto the renamed
    carrier: same position, same transformation role."""

    def __init__(self, element):
        index = TriangleCarrierIndexOf(element)()
        self.result = M.Pair(L.RenamedElementLabel, M.Pair(index, M.EmptyList))
        super().__init__(inputs=M.Pair(element, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RenamedCarrierProduct(M.Edge):
    """Composition transported through the renaming bijection: the
    renamed operation makes the renaming an isomorphism."""

    def __init__(self, left, right):
        left_index = M.Head(M.Tail(left)())()
        right_index = M.Head(M.Tail(right)())()
        left_element = self._element_at_index(left_index)
        right_element = self._element_at_index(right_index)
        composed = TriangleCarrierProduct(left_element, right_element)()
        composed_index = TriangleCarrierIndexOf(composed)()
        self.result = M.Pair(L.RenamedElementLabel, M.Pair(composed_index, M.EmptyList))
        super().__init__(inputs=M.Pair(left, M.Pair(right, M.EmptyList)), results=self.result)

    def _element_at_index(self, index):
        elements = TriangleCarrierElements()()
        return self._walk_to_index(elements, index)

    def _walk_to_index(self, chain, index):
        if M.NatEq(index, M.Zero, M.AllConstructors)() is M.truth_value:
            return M.Head(chain)()
        predecessor = M.NatPred(index, M.AllConstructors)()
        return self._walk_to_index(M.Tail(chain)(), M.Head(predecessor)())

    def __call__(self):
        return self.result


# ============================================================
# Decoy carriers
#
#   Right projection on three elements, x o y = y:
#   closure holds, associativity holds, no two-sided identity exists,
#   so the profile is a semigroup without identity.
#
#   Right projection on four elements with the twist alpha o alpha =
#   delta: closure holds, identity fails, and associativity fails with
#   the concrete counterexample (alpha o alpha) o alpha = alpha while
#   alpha o (alpha o alpha) = delta.
#
#   Both decoys are declared as table operations so the laboratory
#   probes them through exactly the same question interface as the
#   direct triangle operation.
# ============================================================


class DecoyAlpha(M.Edge):
    def __init__(self):
        self.result = M.Pair(L.DecoyAlphaLabel, M.EmptyList)
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class DecoyBeta(M.Edge):
    def __init__(self):
        self.result = M.Pair(L.DecoyBetaLabel, M.EmptyList)
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class DecoyGamma(M.Edge):
    def __init__(self):
        self.result = M.Pair(L.DecoyGammaLabel, M.EmptyList)
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class DecoyDelta(M.Edge):
    """The fourth decoy element (DecoyGammaLabel one), the twisted
    image of alpha o alpha in the nonassociative decoy."""

    def __init__(self):
        self.result = M.Pair(L.DecoyGammaLabel, M.Pair(M.one, M.EmptyList))
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class DecoyCarrierElements(M.Edge):
    def __init__(self):
        self.result = M.Pair(
            DecoyAlpha()(),
            M.Pair(DecoyBeta()(), M.Pair(DecoyGamma()(), M.EmptyList)),
        )
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class DecoyNonAssociativeElements(M.Edge):
    def __init__(self):
        self.result = M.Pair(
            DecoyAlpha()(),
            M.Pair(
                DecoyBeta()(),
                M.Pair(DecoyGamma()(), M.Pair(DecoyDelta()(), M.EmptyList)),
            ),
        )
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class DecoyCarrierProduct(M.Edge):
    """x o y = y on the three-element decoy carrier."""

    def __init__(self, left, right):
        self.result = right
        super().__init__(inputs=M.Pair(left, M.Pair(right, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class DecoyNonAssociativeProduct(M.Edge):
    """Right projection with the twist alpha o alpha = delta."""

    def __init__(self, left, right):
        twisted = M.AndAtom(
            M.TermEqual(left, DecoyAlpha()())(),
            M.TermEqual(right, DecoyAlpha()())(),
        )()
        if twisted is M.truth_value:
            self.result = DecoyDelta()()
        else:
            self.result = right
        super().__init__(inputs=M.Pair(left, M.Pair(right, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class RenamedCarrierTable(M.Edge):
    """The complete operation table of the renamed carrier, built by
    transporting every triangle composition through the renaming."""

    def __init__(self):
        elements = TriangleCarrierRenamedElements()()
        self.result = self._rows(elements, elements)
        super().__init__(inputs=M.EmptyList, results=self.result)

    def _rows(self, elements, remaining):
        if M.IdentityCompare(remaining, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        left = M.Head(remaining)()
        row = self._row(left, elements)
        rest = self._rows(elements, M.Tail(remaining)())
        return ChainAppend(row, rest)()

    def _row(self, left, elements):
        if M.IdentityCompare(elements, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        right = M.Head(elements)()
        value = RenamedCarrierProduct(left, right)()
        cell = DeclaredTableEntry(left, right, value)()
        rest = self._row(left, M.Tail(elements)())
        return M.Pair(cell, rest)

    def __call__(self):
        return self.result


class DecoyRightProjectionTable(M.Edge):
    def __init__(self):
        elements = DecoyCarrierElements()()
        self.result = self._rows(elements, elements)
        super().__init__(inputs=M.EmptyList, results=self.result)

    def _rows(self, elements, remaining):
        if M.IdentityCompare(remaining, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        left = M.Head(remaining)()
        row = self._row(left, elements)
        rest = self._rows(elements, M.Tail(remaining)())
        return ChainAppend(row, rest)()

    def _row(self, left, elements):
        if M.IdentityCompare(elements, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        right = M.Head(elements)()
        value = DecoyCarrierProduct(left, right)()
        cell = DeclaredTableEntry(left, right, value)()
        rest = self._row(left, M.Tail(elements)())
        return M.Pair(cell, rest)

    def __call__(self):
        return self.result


class DecoyNonAssociativeTable(M.Edge):
    def __init__(self):
        elements = DecoyNonAssociativeElements()()
        self.result = self._rows(elements, elements)
        super().__init__(inputs=M.EmptyList, results=self.result)

    def _rows(self, elements, remaining):
        if M.IdentityCompare(remaining, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        left = M.Head(remaining)()
        row = self._row(left, elements)
        rest = self._rows(elements, M.Tail(remaining)())
        return ChainAppend(row, rest)()

    def _row(self, left, elements):
        if M.IdentityCompare(elements, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        right = M.Head(elements)()
        value = DecoyNonAssociativeProduct(left, right)()
        cell = DeclaredTableEntry(left, right, value)()
        rest = self._row(left, M.Tail(elements)())
        return M.Pair(cell, rest)

    def __call__(self):
        return self.result


# ============================================================
# Declared operation
# ============================================================


class DeclaredOperation(M.Edge):
    """(DeclaredOperation name kind elements table)

    One declared binary operation over an explicit finite carrier.
    The direct kind applies the triangle composition construction; the
    table kind reads the recorded table. Carriers of both kinds are
    explicit machine element chains, so every probe question is asked
    through one uniform interface."""

    def __init__(self, name, kind, elements, table):
        fields = M.Pair(name, M.Pair(kind, M.Pair(elements, M.Pair(table, M.EmptyList))))
        self.result = M.Pair(L.DeclaredOperationLabel, fields)
        super().__init__(inputs=fields, results=self.result)

    def __call__(self):
        return self.result


class DeclaredOperationName(M.Edge):
    def __init__(self, operation):
        self.result = M.Head(M.Tail(operation)())()
        super().__init__(inputs=M.Pair(operation, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class DeclaredOperationKind(M.Edge):
    def __init__(self, operation):
        self.result = M.Head(M.Tail(M.Tail(operation)())())()
        super().__init__(inputs=M.Pair(operation, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class DeclaredOperationElements(M.Edge):
    def __init__(self, operation):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(operation)())())())()
        super().__init__(inputs=M.Pair(operation, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class DeclaredOperationTable(M.Edge):
    def __init__(self, operation):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(operation)())())())())()
        super().__init__(inputs=M.Pair(operation, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class DeclaredTableEntry(M.Edge):
    """((left right) value)"""

    def __init__(self, left, right, value):
        self.result = M.Pair(M.Pair(left, M.Pair(right, M.EmptyList)), M.Pair(value, M.EmptyList))
        super().__init__(inputs=M.Pair(left, M.Pair(right, M.Pair(value, M.EmptyList))), results=self.result)

    def __call__(self):
        return self.result


class DeclaredTableEntries(M.Edge):
    """The complete operation table of a declared operation over its
    carrier, in fixed row-major order, read through the operation's
    own application interface."""

    def __init__(self, operation):
        elements = DeclaredOperationElements(operation)()
        self.result = self._rows(operation, elements, elements)
        super().__init__(inputs=M.Pair(operation, M.EmptyList), results=self.result)

    def _rows(self, operation, elements, remaining):
        if M.IdentityCompare(remaining, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        left = M.Head(remaining)()
        row = self._row(operation, left, elements)
        rest_rows = self._rows(operation, elements, M.Tail(remaining)())
        return ChainAppend(row, rest_rows)()

    def _row(self, operation, left, elements):
        if M.IdentityCompare(elements, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        right = M.Head(elements)()
        outcome = TableLookup(operation, left, right)()
        value = M.Head(outcome)()
        cell = DeclaredTableEntry(left, right, value)()
        rest_cells = self._row(operation, left, M.Tail(elements)())
        return M.Pair(cell, rest_cells)

    def __call__(self):
        return self.result


class TableLookup(M.Edge):
    """Applies the declared operation to (left, right).

    The result is a pair whose head is the value atom and whose tail
    is a one-field failure chain: empty on success,
    (MissingTableEntryLabel) when no row applies."""

    def __init__(self, operation, left, right):
        kind = DeclaredOperationKind(operation)()
        is_direct = M.IdentityCompare(kind, L.DirectOperationKindLabel)()
        is_table = M.IdentityCompare(kind, L.TableOperationKindLabel)()
        if is_direct is M.truth_value:
            self.result = M.Pair(TriangleCarrierProduct(left, right)(), M.Pair(M.EmptyList, M.EmptyList))
        elif is_table is M.truth_value:
            table = DeclaredOperationTable(operation)()
            probe = self._lookup(table, left, right)
            if M.IdentityCompare(probe, M.EmptyList)() is M.truth_value:
                self.result = M.Pair(L.OperationFailedLabel, M.Pair(L.MissingTableEntryLabel, M.EmptyList))
            else:
                self.result = M.Pair(probe, M.Pair(M.EmptyList, M.EmptyList))
        else:
            self.result = M.Pair(L.OperationFailedLabel, M.Pair(L.MissingTableEntryLabel, M.EmptyList))
        super().__init__(inputs=M.Pair(operation, M.Pair(left, M.Pair(right, M.EmptyList))), results=self.result)

    def _lookup(self, table, left, right):
        if M.IdentityCompare(table, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        entry = M.Head(table)()
        entry_left = M.Head(M.Head(entry)())()
        entry_right = M.Head(M.Tail(M.Head(entry)())())()
        left_here = M.TermEqual(entry_left, left)()
        right_here = M.TermEqual(entry_right, right)()
        if M.AndAtom(left_here, right_here)() is M.truth_value:
            return M.Head(M.Tail(entry)())()
        return self._lookup(M.Tail(table)(), left, right)

    def __call__(self):
        return self.result


class OperationCell(M.Edge):
    def __init__(self, operation, left, right):
        outcome = TableLookup(operation, left, right)()
        self.result = M.Head(outcome)()
        super().__init__(inputs=M.Pair(operation, M.Pair(left, M.Pair(right, M.EmptyList))), results=self.result)

    def __call__(self):
        return self.result


class DirectTriangleOperation(M.Edge):
    def __init__(self):
        self.result = DeclaredOperation(
            L.TriangleComposeOperationLabel,
            L.DirectOperationKindLabel,
            TriangleCarrierElements()(),
            M.EmptyList,
        )()
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class RenamedTriangleOperation(M.Edge):
    def __init__(self):
        self.result = DeclaredOperation(
            L.RenamedTriangleComposeOperationLabel,
            L.TableOperationKindLabel,
            TriangleCarrierRenamedElements()(),
            RenamedCarrierTable()(),
        )()
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class DecoyRightProjectionOperation(M.Edge):
    def __init__(self):
        self.result = DeclaredOperation(
            L.DecoyRightProjectionOperationLabel,
            L.TableOperationKindLabel,
            DecoyCarrierElements()(),
            DecoyRightProjectionTable()(),
        )()
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class DecoyNonAssociativeOperation(M.Edge):
    def __init__(self):
        self.result = DeclaredOperation(
            L.DecoyLoopOperationLabel,
            L.TableOperationKindLabel,
            DecoyNonAssociativeElements()(),
            DecoyNonAssociativeTable()(),
        )()
        super().__init__(inputs=M.EmptyList, results=self.result)


# ============================================================
# Experimentation
# ============================================================


class ExperimentApplication(M.Edge):
    """(ExperimentApplication left right value)"""

    def __init__(self, left, right, value):
        self.result = M.Pair(L.ExperimentApplicationLabel, M.Pair(left, M.Pair(right, M.Pair(value, M.EmptyList))))
        super().__init__(inputs=M.Pair(left, M.Pair(right, M.Pair(value, M.EmptyList))), results=self.result)

    def __call__(self):
        return self.result


class LaboratoryPlan(M.Edge):
    """A bounded experiment plan: at most `budget` (left, right) pairs
    swept from the carrier in a fixed order. The budget is a machine
    nat; the plan consumes one predecessor per pair."""

    def __init__(self, budget):
        outcome = self._build(budget, M.Zero)
        self.result = M.Head(outcome)()
        super().__init__(inputs=M.Pair(budget, M.EmptyList), results=self.result)

    def _build(self, remaining, current):
        done = M.NatEq(remaining, M.Zero, M.AllConstructors)()
        if done is M.truth_value:
            return M.Pair(M.EmptyList, M.EmptyList)
        entry = M.Pair(current, M.Pair(current, M.EmptyList))
        pred = M.NatPred(remaining, M.AllConstructors)()
        succ = M.Succ(current, M.AllConstructors)()
        rest = self._build(M.Head(pred)(), M.Head(succ)())
        return M.Pair(M.Pair(entry, M.Head(rest)()), M.EmptyList)

    def __call__(self):
        return self.result


class ApplyExperiments(M.Edge):
    """Runs one bounded experiment plan against one declared operation.

    Every application is recorded as an ExperimentApplication. The
    plan ends with one ClosureObservation: machine truth when every
    recorded application stayed inside the carrier, machine falsehood
    when some application left it."""

    def __init__(self, operation, plan):
        self.result = self._run(operation, plan, M.truth_value)
        super().__init__(inputs=M.Pair(operation, M.Pair(plan, M.EmptyList)), results=self.result)

    def _run(self, operation, plan, closed_so_far):
        if M.IdentityCompare(plan, M.EmptyList)() is M.truth_value:
            return M.Pair(ClosureObservation(closed_so_far)(), M.EmptyList)
        pair = M.Head(plan)()
        left = M.Head(pair)()
        right = M.Head(M.Tail(pair)())()
        outcome = TableLookup(operation, left, right)()
        value = M.Head(outcome)()
        application = ExperimentApplication(left, right, value)()
        elements = DeclaredOperationElements(operation)()
        inside = ChainContains(elements, value)()
        if inside is M.truth_value:
            next_closed = closed_so_far
        else:
            next_closed = M.false_value
        rest = self._run(operation, M.Tail(plan)(), next_closed)
        return M.Pair(application, rest)

    def __call__(self):
        return self.result


class ObservedEquation(M.Edge):
    """(ObservedEquation law-label left right sides-equal)"""

    def __init__(self, law_label, left, right, sides_equal):
        self.result = M.Pair(
            L.ObservedEquationLabel,
            M.Pair(law_label, M.Pair(left, M.Pair(right, M.Pair(sides_equal, M.EmptyList)))),
        )
        super().__init__(
            inputs=M.Pair(law_label, M.Pair(left, M.Pair(right, M.Pair(sides_equal, M.EmptyList)))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class Counterexample(M.Edge):
    """(Counterexample law-label left right)"""

    def __init__(self, law_label, left, right):
        self.result = M.Pair(L.CounterexampleLabel, M.Pair(law_label, M.Pair(left, M.Pair(right, M.EmptyList))))
        super().__init__(inputs=M.Pair(law_label, M.Pair(left, M.Pair(right, M.EmptyList))), results=self.result)

    def __call__(self):
        return self.result


class DirectLawProbe(M.Edge):
    """Asks one generic algebraic question of one declared operation
    over its full bounded carrier sweep.

    Verdicts:
      LawHoldsLabel      every tested instance satisfied the law
      LawViolatedLabel   a concrete counterexample was recorded
      LawUnknownLabel    a prerequisite law failed first"""

    def __init__(self, law_label, operation):
        if M.IdentityCompare(law_label, L.ClosureLawLabel)() is M.truth_value:
            self.result = self._probe_closure(operation)
        elif M.IdentityCompare(law_label, L.AssociativeLawLabel)() is M.truth_value:
            self.result = self._probe_associativity(operation)
        elif M.IdentityCompare(law_label, L.IdentityLawLabel)() is M.truth_value:
            self.result = self._probe_identity(operation)
        elif M.IdentityCompare(law_label, L.InverseLawLabel)() is M.truth_value:
            self.result = self._probe_inverses(operation)
        elif M.IdentityCompare(law_label, L.CommutativeLawLabel)() is M.truth_value:
            self.result = self._probe_commutativity(operation)
        else:
            self.result = M.Pair(L.LawUnknownLabel, M.EmptyList)
        super().__init__(inputs=M.Pair(law_label, M.Pair(operation, M.EmptyList)), results=self.result)

    def _probe_closure(self, operation):
        elements = DeclaredOperationElements(operation)()
        findings = self._closure_findings(operation, elements, elements)
        if M.IdentityCompare(findings, M.EmptyList)() is M.truth_value:
            return M.Pair(L.LawHoldsLabel, M.Pair(findings, M.EmptyList))
        return M.Pair(L.LawViolatedLabel, M.Pair(findings, M.EmptyList))

    def _closure_findings(self, operation, elements, remaining):
        if M.IdentityCompare(remaining, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        left = M.Head(remaining)()
        row = self._closure_row_findings(operation, elements, left, elements)
        rest = self._closure_findings(operation, elements, M.Tail(remaining)())
        return ChainAppend(row, rest)()

    def _closure_row_findings(self, operation, elements, left, rights):
        if M.IdentityCompare(rights, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        right = M.Head(rights)()
        outcome = TableLookup(operation, left, right)()
        value = M.Head(outcome)()
        inside = ChainContains(elements, value)()
        rest = self._closure_row_findings(operation, elements, left, M.Tail(rights)())
        if inside is M.truth_value:
            return rest
        return M.Pair(Counterexample(L.ClosureLawLabel, left, right)(), rest)

    def _probe_associativity(self, operation):
        elements = DeclaredOperationElements(operation)()
        findings = self._associativity_findings(operation, elements, elements, elements)
        if M.IdentityCompare(findings, M.EmptyList)() is M.truth_value:
            return M.Pair(L.LawHoldsLabel, M.Pair(findings, M.EmptyList))
        return M.Pair(L.LawViolatedLabel, M.Pair(findings, M.EmptyList))

    def _associativity_findings(self, operation, elements, left_remaining, middle_remaining):
        if M.IdentityCompare(left_remaining, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        left = M.Head(left_remaining)()
        findings = self._associativity_middle(operation, elements, left, middle_remaining)
        rest = self._associativity_findings(operation, elements, M.Tail(left_remaining)(), middle_remaining)
        return ChainAppend(findings, rest)()

    def _associativity_middle(self, operation, elements, left, middle_remaining):
        if M.IdentityCompare(middle_remaining, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        middle = M.Head(middle_remaining)()
        row = self._associativity_row(operation, elements, left, middle, elements)
        rest = self._associativity_middle(operation, elements, left, M.Tail(middle_remaining)())
        return ChainAppend(row, rest)()

    def _associativity_row(self, operation, elements, left, middle, rights):
        if M.IdentityCompare(rights, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        right = M.Head(rights)()
        inner_left = OperationCell(operation, left, middle)()
        left_side = OperationCell(operation, inner_left, right)()
        inner_right = OperationCell(operation, middle, right)()
        right_side = OperationCell(operation, left, inner_right)()
        rest = self._associativity_row(operation, elements, left, middle, M.Tail(rights)())
        if M.TermEqual(left_side, right_side)() is M.truth_value:
            return rest
        return M.Pair(Counterexample(L.AssociativeLawLabel, left, middle)(), rest)

    def _probe_identity(self, operation):
        elements = DeclaredOperationElements(operation)()
        candidates = self._identity_candidates(operation, elements, elements)
        if M.IdentityCompare(candidates, M.EmptyList)() is M.truth_value:
            return M.Pair(L.LawViolatedLabel, M.Pair(M.Pair(L.IdentitySearchExhaustedLabel, M.EmptyList), M.EmptyList))
        return M.Pair(L.LawHoldsLabel, M.Pair(candidates, M.EmptyList))

    def _identity_candidates(self, operation, elements, sweep):
        if M.IdentityCompare(sweep, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        candidate = M.Head(sweep)()
        left_ok = self._left_identity_scan(operation, candidate, elements)
        right_ok = self._right_identity_scan(operation, candidate, elements)
        rest = self._identity_candidates(operation, elements, M.Tail(sweep)())
        if M.AndAtom(left_ok, right_ok)() is M.truth_value:
            return M.Pair(IdentityCandidate(candidate)(), rest)
        return rest

    def _left_identity_scan(self, operation, candidate, elements):
        if M.IdentityCompare(elements, M.EmptyList)() is M.truth_value:
            return M.truth_value
        element = M.Head(elements)()
        value = OperationCell(operation, candidate, element)()
        if M.TermEqual(value, element)() is M.false_value:
            return M.false_value
        return self._left_identity_scan(operation, candidate, M.Tail(elements)())

    def _right_identity_scan(self, operation, candidate, elements):
        if M.IdentityCompare(elements, M.EmptyList)() is M.truth_value:
            return M.truth_value
        element = M.Head(elements)()
        value = OperationCell(operation, element, candidate)()
        if M.TermEqual(value, element)() is M.false_value:
            return M.false_value
        return self._right_identity_scan(operation, candidate, M.Tail(elements)())

    def _probe_inverses(self, operation):
        identity_probe = DirectLawProbe(L.IdentityLawLabel, operation)()
        identity_verdict = M.Head(identity_probe)()
        if M.IdentityCompare(identity_verdict, L.LawHoldsLabel)() is M.false_value:
            return M.Pair(L.LawUnknownLabel, M.Pair(M.Pair(L.IdentitySearchExhaustedLabel, M.EmptyList), M.EmptyList))
        identity_findings = M.Head(M.Tail(identity_probe)())()
        identity_element = M.Head(M.Tail(M.Head(identity_findings)())())()
        elements = DeclaredOperationElements(operation)()
        findings = self._inverse_findings(operation, elements, elements, identity_element)
        if M.IdentityCompare(findings, M.EmptyList)() is M.truth_value:
            return M.Pair(L.LawViolatedLabel, M.Pair(M.Pair(L.InverseSearchExhaustedLabel, M.EmptyList), M.EmptyList))
        return M.Pair(L.LawHoldsLabel, M.Pair(findings, M.EmptyList))

    def _inverse_findings(self, operation, elements, sweep, identity_element):
        if M.IdentityCompare(sweep, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        element = M.Head(sweep)()
        witness = self._inverse_witness(operation, element, elements, identity_element)
        rest = self._inverse_findings(operation, elements, M.Tail(sweep)(), identity_element)
        if M.IdentityCompare(witness, M.EmptyList)() is M.truth_value:
            return M.Pair(Counterexample(L.InverseLawLabel, element, identity_element)(), rest)
        return M.Pair(InverseCandidate(element, witness)(), rest)

    def _inverse_witness(self, operation, element, sweep, identity_element):
        if M.IdentityCompare(sweep, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        candidate = M.Head(sweep)()
        left_value = OperationCell(operation, element, candidate)()
        right_value = OperationCell(operation, candidate, element)()
        left_ok = M.TermEqual(left_value, identity_element)()
        right_ok = M.TermEqual(right_value, identity_element)()
        if M.AndAtom(left_ok, right_ok)() is M.truth_value:
            return candidate
        return self._inverse_witness(operation, element, M.Tail(sweep)(), identity_element)

    def _probe_commutativity(self, operation):
        elements = DeclaredOperationElements(operation)()
        findings = self._commutativity_findings(operation, elements, elements)
        if M.IdentityCompare(findings, M.EmptyList)() is M.truth_value:
            return M.Pair(L.LawHoldsLabel, M.Pair(findings, M.EmptyList))
        return M.Pair(L.LawViolatedLabel, M.Pair(findings, M.EmptyList))

    def _commutativity_findings(self, operation, elements, remaining):
        if M.IdentityCompare(remaining, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        left = M.Head(remaining)()
        row = self._commutativity_row(operation, left, elements)
        rest = self._commutativity_findings(operation, elements, M.Tail(remaining)())
        return ChainAppend(row, rest)()

    def _commutativity_row(self, operation, left, rights):
        if M.IdentityCompare(rights, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        right = M.Head(rights)()
        left_value = OperationCell(operation, left, right)()
        right_value = OperationCell(operation, right, left)()
        same = M.TermEqual(left_value, right_value)()
        rest = self._commutativity_row(operation, left, M.Tail(rights)())
        if same is M.truth_value:
            return rest
        return M.Pair(CommutativityObservation(left, right, left_value, right_value)(), rest)

    def __call__(self):
        return self.result


class ProbeFindings(M.Edge):
    def __init__(self, probe):
        self.result = M.Head(M.Tail(probe)())()
        super().__init__(inputs=M.Pair(probe, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ProbeVerdict(M.Edge):
    def __init__(self, probe):
        self.result = M.Head(probe)()
        super().__init__(inputs=M.Pair(probe, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class IdentityCandidate(M.Edge):
    def __init__(self, element):
        self.result = M.Pair(L.IdentityCandidateLabel, M.Pair(element, M.EmptyList))
        super().__init__(inputs=M.Pair(element, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class InverseCandidate(M.Edge):
    def __init__(self, element, witness):
        self.result = M.Pair(L.InverseCandidateLabel, M.Pair(element, M.Pair(witness, M.EmptyList)))
        super().__init__(inputs=M.Pair(element, M.Pair(witness, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class CommutativityObservation(M.Edge):
    def __init__(self, left, right, left_value, right_value):
        self.result = M.Pair(
            L.CommutativityObservationLabel,
            M.Pair(left, M.Pair(right, M.Pair(left_value, M.Pair(right_value, M.EmptyList)))),
        )
        super().__init__(
            inputs=M.Pair(left, M.Pair(right, M.Pair(left_value, M.Pair(right_value, M.EmptyList)))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class ClosureObservation(M.Edge):
    def __init__(self, flag):
        self.result = M.Pair(L.ClosureObservationLabel, M.Pair(flag, M.EmptyList))
        super().__init__(inputs=M.Pair(flag, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class AssociativitySearchRecord(M.Edge):
    """(AssociativitySearchRecord verdict findings)"""

    def __init__(self, verdict, findings):
        self.result = M.Pair(L.AssociativitySearchRecordLabel, M.Pair(verdict, M.Pair(findings, M.EmptyList)))
        super().__init__(inputs=M.Pair(verdict, M.Pair(findings, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


# ============================================================
# Certified laws and replay
# ============================================================


class CertifiedLaw(M.Edge):
    """(CertifiedLaw law-label method findings replay)"""

    def __init__(self, law_label, method, findings, replay):
        self.result = M.Pair(
            L.CertifiedLawLabel,
            M.Pair(law_label, M.Pair(method, M.Pair(findings, M.Pair(replay, M.EmptyList)))),
        )
        super().__init__(
            inputs=M.Pair(law_label, M.Pair(method, M.Pair(findings, M.Pair(replay, M.EmptyList)))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class CertifiedLawLabelOf(M.Edge):
    def __init__(self, law):
        self.result = M.Head(M.Tail(law)())()
        super().__init__(inputs=M.Pair(law, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CertifiedLawMethodOf(M.Edge):
    def __init__(self, law):
        self.result = M.Head(M.Tail(M.Tail(law)())())()
        super().__init__(inputs=M.Pair(law, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CertifiedLawFindingsOf(M.Edge):
    def __init__(self, law):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(law)())())())()
        super().__init__(inputs=M.Pair(law, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CertifiedLawReplayOf(M.Edge):
    def __init__(self, law):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(law)())())())())()
        super().__init__(inputs=M.Pair(law, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ConjecturedLaw(M.Edge):
    """(ConjecturedLaw law-label supporting-observations
          searched-counterexamples)

    A conjecture from bounded play. Conjectures never enter a proof:
    only CertifiedLaw terms may support a structure recognition."""

    def __init__(self, law_label, supporting, searched):
        self.result = M.Pair(
            L.ConjecturedLawLabel,
            M.Pair(law_label, M.Pair(supporting, M.Pair(searched, M.EmptyList))),
        )
        super().__init__(
            inputs=M.Pair(law_label, M.Pair(supporting, M.Pair(searched, M.EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class ReplayCheckExhaustive(M.Edge):
    """The replay record for a bounded finite carrier: the method stamp
    says the verdict must be re-derivable by walking every instance
    again, independent of the original probe run."""

    def __init__(self, law_label):
        self.result = M.Pair(L.ReplayRecordLabel, M.Pair(L.ExhaustiveFiniteCheckLabel, M.Pair(law_label, M.EmptyList)))
        super().__init__(inputs=M.Pair(law_label, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CheckReplay(M.Edge):
    """Re-derives the law verdict from the replay record against the
    declared operation. Returns ReplayVerifiedLabel when the record
    kind and method are honored and the independent re-derivation
    reaches a definite verdict, ReplayMismatchLabel otherwise."""

    def __init__(self, replay, operation):
        record_kind = M.Head(replay)()
        method = M.Head(M.Tail(replay)())()
        law_label = M.Head(M.Tail(M.Tail(replay)())())()
        kind_ok = M.IdentityCompare(record_kind, L.ReplayRecordLabel)()
        method_ok = M.IdentityCompare(method, L.ExhaustiveFiniteCheckLabel)()
        if M.AndAtom(kind_ok, method_ok)() is M.truth_value:
            probe = DirectLawProbe(law_label, operation)()
            verdict = M.Head(probe)()
            definite = M.OrAtom(
                M.IdentityCompare(verdict, L.LawHoldsLabel)(),
                M.IdentityCompare(verdict, L.LawViolatedLabel)(),
            )()
            if definite is M.truth_value:
                self.result = L.ReplayVerifiedLabel
            else:
                self.result = L.ReplayMismatchLabel
        else:
            self.result = L.ReplayMismatchLabel
        super().__init__(inputs=M.Pair(replay, M.Pair(operation, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


# ============================================================
# Structure signature
# ============================================================


class StructureSignature(M.Edge):
    """(StructureSignature
          carrier-tag
          operation-name
          certified-closure
          certified-associativity
          certified-identity
          certified-inverses
          certified-commutativity
          conjectured-laws
          counterexamples
          evidence)

    The evidence field carries the declared operation the signature
    was derived from, so every certificate in the signature can be
    replayed against it without any outside context."""

    def __init__(
        self,
        carrier_tag,
        operation_name,
        certified_closure,
        certified_associativity,
        certified_identity,
        certified_inverses,
        certified_commutativity,
        conjectured_laws,
        counterexamples,
        evidence,
    ):
        fields = M.Pair(
            carrier_tag,
            M.Pair(
                operation_name,
                M.Pair(
                    certified_closure,
                    M.Pair(
                        certified_associativity,
                        M.Pair(
                            certified_identity,
                            M.Pair(
                                certified_inverses,
                                M.Pair(
                                    certified_commutativity,
                                    M.Pair(
                                        conjectured_laws,
                                        M.Pair(counterexamples, M.Pair(evidence, M.EmptyList)),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        )
        self.result = M.Pair(L.StructureSignatureLabel, fields)
        super().__init__(inputs=fields, results=self.result)

    def __call__(self):
        return self.result


class SignatureCarrierOf(M.Edge):
    def __init__(self, signature):
        self.result = M.Head(M.Tail(signature)())()
        super().__init__(inputs=M.Pair(signature, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SignatureOperationOf(M.Edge):
    def __init__(self, signature):
        self.result = M.Head(M.Tail(M.Tail(signature)())())()
        super().__init__(inputs=M.Pair(signature, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SignatureClosureOf(M.Edge):
    def __init__(self, signature):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(signature)())())())()
        super().__init__(inputs=M.Pair(signature, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SignatureAssociativityOf(M.Edge):
    def __init__(self, signature):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(signature)())())())())()
        super().__init__(inputs=M.Pair(signature, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SignatureIdentityOf(M.Edge):
    def __init__(self, signature):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(signature)())())())())())()
        super().__init__(inputs=M.Pair(signature, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SignatureInversesOf(M.Edge):
    def __init__(self, signature):
        self.result = M.Head(
            M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(signature)())())())())())()
        )()
        super().__init__(inputs=M.Pair(signature, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SignatureCommutativityOf(M.Edge):
    def __init__(self, signature):
        self.result = M.Head(
            M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(signature)())())())())())())()
        )()
        super().__init__(inputs=M.Pair(signature, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SignatureConjecturedLaws(M.Edge):
    def __init__(self, signature):
        self.result = M.Head(
            M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(signature)())())())())())())())()
        )()
        super().__init__(inputs=M.Pair(signature, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SignatureCounterexamplesOf(M.Edge):
    def __init__(self, signature):
        self.result = M.Head(
            M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(signature)())())())())())())())())()
        )()
        super().__init__(inputs=M.Pair(signature, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SignatureEvidenceOf(M.Edge):
    """The full evidence chain: five probe verdicts followed by the
    declared operation they were observed against."""

    def __init__(self, signature):
        self.result = M.Head(
            M.Tail(
                M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(signature)())())())())())())())())()
            )()
        )()
        super().__init__(inputs=M.Pair(signature, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SignatureOperationTerm(M.Edge):
    """The declared operation stored as the sixth field of the
    evidence chain."""

    def __init__(self, signature):
        evidence = M.Head(
            M.Tail(
                M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(signature)())())())())())())())())()
            )()
        )()
        self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(evidence)())())())())())()
        super().__init__(inputs=M.Pair(signature, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SignatureLabelOf(M.Edge):
    def __init__(self, signature):
        self.result = M.Head(signature)()
        super().__init__(inputs=M.Pair(signature, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SignatureForOperation(M.Edge):
    """Probes the five generic laws of one declared operation and
    assembles the unnamed StructureSignature. Certified slots carry a
    CertifiedLaw only where the probe verdict was LawHolds; violated
    and unknown laws leave their slot empty and their findings in the
    counterexample slot. No abstract structure name appears anywhere
    in the output."""

    def __init__(self, operation):
        elements = DeclaredOperationElements(operation)()
        closure_probe = DirectLawProbe(L.ClosureLawLabel, operation)()
        associativity_probe = DirectLawProbe(L.AssociativeLawLabel, operation)()
        identity_probe = DirectLawProbe(L.IdentityLawLabel, operation)()
        inverses_probe = DirectLawProbe(L.InverseLawLabel, operation)()
        commutativity_probe = DirectLawProbe(L.CommutativeLawLabel, operation)()

        closure_verdict = M.Head(closure_probe)()
        associativity_verdict = M.Head(associativity_probe)()
        identity_verdict = M.Head(identity_probe)()
        inverses_verdict = M.Head(inverses_probe)()
        commutativity_verdict = M.Head(commutativity_probe)()

        closure_findings = M.Head(M.Tail(closure_probe)())()
        associativity_findings = M.Head(M.Tail(associativity_probe)())()
        identity_findings = M.Head(M.Tail(identity_probe)())()
        inverses_findings = M.Head(M.Tail(inverses_probe)())()
        commutativity_findings = M.Head(M.Tail(commutativity_probe)())()

        closure_holds = M.IdentityCompare(closure_verdict, L.LawHoldsLabel)()
        associativity_holds = M.IdentityCompare(associativity_verdict, L.LawHoldsLabel)()
        identity_holds = M.IdentityCompare(identity_verdict, L.LawHoldsLabel)()
        inverses_holds = M.IdentityCompare(inverses_verdict, L.LawHoldsLabel)()
        commutativity_holds = M.IdentityCompare(commutativity_verdict, L.LawHoldsLabel)()

        certified_closure = self._certified_when_holds(L.ClosureLawLabel, closure_holds, closure_findings)
        certified_associativity = self._certified_when_holds(L.AssociativeLawLabel, associativity_holds, associativity_findings)
        certified_identity = self._certified_when_holds(L.IdentityLawLabel, identity_holds, identity_findings)
        certified_inverses = self._certified_when_holds(L.InverseLawLabel, inverses_holds, inverses_findings)
        certified_commutativity = self._certified_when_holds(L.CommutativeLawLabel, commutativity_holds, commutativity_findings)

        refuted = self._collect_refuted(
            closure_holds,
            closure_findings,
            self._collect_refuted(
                associativity_holds,
                associativity_findings,
                self._collect_refuted(
                    identity_holds,
                    identity_findings,
                    self._collect_refuted(
                        inverses_holds,
                        inverses_findings,
                        self._collect_refuted(commutativity_holds, commutativity_findings, M.EmptyList),
                    ),
                ),
            ),
        )

        evidence = M.Pair(
            closure_verdict,
            M.Pair(
                associativity_verdict,
                M.Pair(
                    identity_verdict,
                    M.Pair(
                        inverses_verdict,
                        M.Pair(commutativity_verdict, M.Pair(operation, M.EmptyList)),
                    ),
                ),
            ),
        )

        self.result = StructureSignature(
            M.Head(M.Head(elements)())(),
            DeclaredOperationName(operation)(),
            certified_closure,
            certified_associativity,
            certified_identity,
            certified_inverses,
            certified_commutativity,
            M.EmptyList,
            refuted,
            evidence,
        )()
        super().__init__(inputs=M.Pair(operation, M.EmptyList), results=self.result)

    def _certified_when_holds(self, law_label, holds, findings):
        if holds is M.truth_value:
            return CertificationAttempt(law_label, findings)()
        return M.EmptyList

    def _collect_refuted(self, holds, findings, rest):
        if holds is M.truth_value:
            return rest
        return ChainAppend(findings, rest)()

    def __call__(self):
        return self.result


# ============================================================
# Structure candidates
# ============================================================


class BuildStructureCandidate(M.Edge):
    """(StructureCandidate signature declared-label). The declared
    label is the machine's abstract-name proposal. It is not an axiom
    and it certifies nothing; the recognizer alone decides."""

    def __init__(self, signature, declared_label):
        self.result = M.Pair(L.StructureCandidateLabel, M.Pair(signature, M.Pair(declared_label, M.EmptyList)))
        super().__init__(inputs=M.Pair(signature, M.Pair(declared_label, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class WithholdStructureCandidate(M.Edge):
    """(StructureCandidate signature WithheldStructureLabel
          missing-label). The same signature with the abstract name
    withheld: used while a certificate is disabled, when recognition
    must be blocked."""

    def __init__(self, signature, missing_label):
        self.result = M.Pair(
            L.StructureCandidateLabel,
            M.Pair(signature, M.Pair(L.WithheldStructureLabel, M.Pair(missing_label, M.EmptyList))),
        )
        super().__init__(inputs=M.Pair(signature, M.Pair(missing_label, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class WithSignatureSlotWithheld(M.Edge):
    """Rebuilds the signature with the certified law for law_label
    removed: the certification is disabled, the slot is empty, and the
    recognizer must refuse every catalogue entry that requires it."""

    def __init__(self, signature, law_label):
        carrier = SignatureCarrierOf(signature)()
        operation_name = SignatureOperationOf(signature)()
        closure = SignatureClosureOf(signature)()
        associativity = SignatureAssociativityOf(signature)()
        identity = SignatureIdentityOf(signature)()
        inverses = SignatureInversesOf(signature)()
        commutativity = SignatureCommutativityOf(signature)()
        conjectured = SignatureConjecturedLaws(signature)()
        counterexamples = SignatureCounterexamplesOf(signature)()
        evidence = SignatureEvidenceOf(signature)()

        if M.IdentityCompare(law_label, L.ClosureLawLabel)() is M.truth_value:
            closure = M.EmptyList
        elif M.IdentityCompare(law_label, L.AssociativeLawLabel)() is M.truth_value:
            associativity = M.EmptyList
        elif M.IdentityCompare(law_label, L.IdentityLawLabel)() is M.truth_value:
            identity = M.EmptyList
        elif M.IdentityCompare(law_label, L.InverseLawLabel)() is M.truth_value:
            inverses = M.EmptyList
        elif M.IdentityCompare(law_label, L.CommutativeLawLabel)() is M.truth_value:
            commutativity = M.EmptyList

        self.result = StructureSignature(
            carrier,
            operation_name,
            closure,
            associativity,
            identity,
            inverses,
            commutativity,
            conjectured,
            counterexamples,
            evidence,
        )()
        super().__init__(inputs=M.Pair(signature, M.Pair(law_label, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class WithCertificateRestored(M.Edge):
    """Rebuilds the signature with a certified law placed back into its
    slot: the certification is restored and the recognizer's gate opens
    again."""

    def __init__(self, signature, law):
        law_label = CertifiedLawLabelOf(law)()
        carrier = SignatureCarrierOf(signature)()
        operation_name = SignatureOperationOf(signature)()
        closure = SignatureClosureOf(signature)()
        associativity = SignatureAssociativityOf(signature)()
        identity = SignatureIdentityOf(signature)()
        inverses = SignatureInversesOf(signature)()
        commutativity = SignatureCommutativityOf(signature)()
        conjectured = SignatureConjecturedLaws(signature)()
        counterexamples = SignatureCounterexamplesOf(signature)()
        evidence = SignatureEvidenceOf(signature)()

        if M.IdentityCompare(law_label, L.ClosureLawLabel)() is M.truth_value:
            closure = law
        elif M.IdentityCompare(law_label, L.AssociativeLawLabel)() is M.truth_value:
            associativity = law
        elif M.IdentityCompare(law_label, L.IdentityLawLabel)() is M.truth_value:
            identity = law
        elif M.IdentityCompare(law_label, L.InverseLawLabel)() is M.truth_value:
            inverses = law
        elif M.IdentityCompare(law_label, L.CommutativeLawLabel)() is M.truth_value:
            commutativity = law

        self.result = StructureSignature(
            carrier,
            operation_name,
            closure,
            associativity,
            identity,
            inverses,
            commutativity,
            conjectured,
            counterexamples,
            evidence,
        )()
        super().__init__(inputs=M.Pair(signature, M.Pair(law, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class CandidateSignatureOf(M.Edge):
    def __init__(self, candidate):
        self.result = M.Head(M.Tail(candidate)())()
        super().__init__(inputs=M.Pair(candidate, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CandidateDeclaredLabelOf(M.Edge):
    def __init__(self, candidate):
        self.result = M.Head(M.Tail(M.Tail(candidate)())())()
        super().__init__(inputs=M.Pair(candidate, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


# ============================================================
# Process model: checkpoint, worker journals, observation merge,
# serial proposal admission
# ============================================================


class LaboratoryCheckpoint(M.Edge):
    """(LaboratoryCheckpoint checkpoint-id operation budget)

    Immutable input to every worker job. Workers never write back to
    the checkpoint or to each other."""

    def __init__(self, checkpoint_id, operation, budget):
        fields = M.Pair(checkpoint_id, M.Pair(operation, M.Pair(budget, M.EmptyList)))
        self.result = M.Pair(L.LaboratoryCheckpointLabel, fields)
        super().__init__(inputs=fields, results=self.result)

    def __call__(self):
        return self.result


class CheckpointOperationOf(M.Edge):
    def __init__(self, checkpoint):
        self.result = M.Head(M.Tail(M.Tail(checkpoint)())())()
        super().__init__(inputs=M.Pair(checkpoint, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CheckpointBudgetOf(M.Edge):
    def __init__(self, checkpoint):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(checkpoint)())())())()
        super().__init__(inputs=M.Pair(checkpoint, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class WorkerJournal(M.Edge):
    """(WorkerJournal role observations). A private append-only
    observation journal."""

    def __init__(self, role, observations):
        self.result = M.Pair(L.WorkerJournalLabel, M.Pair(role, M.Pair(observations, M.EmptyList)))
        super().__init__(inputs=M.Pair(role, M.Pair(observations, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class JournalRoleOf(M.Edge):
    def __init__(self, journal):
        self.result = M.Head(M.Tail(journal)())()
        super().__init__(inputs=M.Pair(journal, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class JournalObservations(M.Edge):
    def __init__(self, journal):
        self.result = M.Head(M.Tail(M.Tail(journal)())())()
        super().__init__(inputs=M.Pair(journal, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class AppendObservation(M.Edge):
    def __init__(self, journal, observation):
        role = JournalRoleOf(journal)()
        observations = JournalObservations(journal)()
        self.result = WorkerJournal(role, ChainAppend(observations, M.Pair(observation, M.EmptyList))())()
        super().__init__(inputs=M.Pair(journal, M.Pair(observation, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class ObservationLedger(M.Edge):
    """(ObservationLedger entries)"""

    def __init__(self, entries):
        self.result = M.Pair(L.ObservationLedgerLabel, M.Pair(entries, M.EmptyList))
        super().__init__(inputs=M.Pair(entries, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class LedgerEntries(M.Edge):
    def __init__(self, ledger):
        self.result = M.Head(M.Tail(ledger)())()
        super().__init__(inputs=M.Pair(ledger, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class MergeObservationLedgers(M.Edge):
    """Append-only merge of worker journals into one ledger. Sources
    are never mutated; their chains are re-spliced in role order."""

    def __init__(self, journals):
        self.result = self._merge(journals)
        super().__init__(inputs=M.Pair(journals, M.EmptyList), results=self.result)

    def _merge(self, journals):
        if M.IdentityCompare(journals, M.EmptyList)() is M.truth_value:
            return ObservationLedger(M.EmptyList)()
        journal = M.Head(journals)()
        observations = JournalObservations(journal)()
        rest = self._merge(M.Tail(journals)())
        merged_entries = ChainAppend(observations, LedgerEntries(rest)())()
        return ObservationLedger(merged_entries)()

    def __call__(self):
        return self.result


class AdmissionOutcome(M.Edge):
    """(AdmissionOutcome proposal verdict requirements)"""

    def __init__(self, proposal, verdict, requirements):
        self.result = M.Pair(
            L.AdmissionOutcomeLabel,
            M.Pair(proposal, M.Pair(verdict, M.Pair(requirements, M.EmptyList))),
        )
        super().__init__(
            inputs=M.Pair(proposal, M.Pair(verdict, M.Pair(requirements, M.EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class AdmitProposal(M.Edge):
    """Serial proposal admission against the updated baseline. A
    conjectured law enters the certified baseline only when an
    independent direct probe of the same law supports it against the
    declared operation. A counterexample proposal is never admitted as
    structure; it is recorded as a refutation."""

    def __init__(self, proposal, operation):
        proposal_kind = M.Head(proposal)()
        if M.IdentityCompare(proposal_kind, L.ConjecturedLawLabel)() is M.truth_value:
            law_label = M.Head(M.Tail(proposal)())()
            probe = DirectLawProbe(law_label, operation)()
            verdict = M.Head(probe)()
            findings = M.Head(M.Tail(probe)())()
            if M.IdentityCompare(verdict, L.LawHoldsLabel)() is M.truth_value:
                self.result = AdmissionOutcome(proposal, L.CandidateRecognizedLabel, findings)()
            else:
                self.result = AdmissionOutcome(proposal, L.ProposalRejectedLabel, findings)()
        elif M.IdentityCompare(proposal_kind, L.CounterexampleLabel)() is M.truth_value:
            self.result = AdmissionOutcome(proposal, L.ProposalRejectedLabel, M.EmptyList)()
        else:
            self.result = AdmissionOutcome(proposal, L.ProposalRejectedLabel, M.EmptyList)()
        super().__init__(inputs=M.Pair(proposal, M.Pair(operation, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class RunLaboratoryWorker(M.Edge):
    """One worker job: an immutable checkpoint plus a role. The worker
    writes only its private journal and returns it.

    Roles:
      ClosureWorkerRoleLabel         closure experiments
      IdentityWorkerRoleLabel        identity search
      InverseWorkerRoleLabel         inverse search
      CommutativityWorkerRoleLabel   commutativity observations
      AssociativityWorkerRoleLabel   associativity counterexample search"""

    def __init__(self, checkpoint, role):
        operation = CheckpointOperationOf(checkpoint)()
        budget = CheckpointBudgetOf(checkpoint)()
        bounded = M.NatLess(budget, M.six, M.AllConstructors)()
        if bounded is M.false_value:
            self.result = WorkerJournal(role, M.EmptyList)()
        elif M.IdentityCompare(role, L.ClosureWorkerRoleLabel)() is M.truth_value:
            self.result = self._closure_worker(operation)
        elif M.IdentityCompare(role, L.IdentityWorkerRoleLabel)() is M.truth_value:
            self.result = self._identity_worker(operation)
        elif M.IdentityCompare(role, L.InverseWorkerRoleLabel)() is M.truth_value:
            self.result = self._inverse_worker(operation)
        elif M.IdentityCompare(role, L.CommutativityWorkerRoleLabel)() is M.truth_value:
            self.result = self._commutativity_worker(operation)
        elif M.IdentityCompare(role, L.AssociativityWorkerRoleLabel)() is M.truth_value:
            self.result = self._associativity_worker(operation)
        else:
            self.result = WorkerJournal(role, M.EmptyList)()
        super().__init__(inputs=M.Pair(checkpoint, M.Pair(role, M.EmptyList)), results=self.result)

    def _closure_worker(self, operation):
        probe = DirectLawProbe(L.ClosureLawLabel, operation)()
        verdict = M.Head(probe)()
        findings = M.Head(M.Tail(probe)())()
        journal = WorkerJournal(L.ClosureWorkerRoleLabel, findings)()
        holds = M.IdentityCompare(verdict, L.LawHoldsLabel)()
        journal = AppendObservation(journal, ClosureObservation(holds)())()
        if holds is M.truth_value:
            proposal = ConjecturedLaw(
                L.ClosureLawLabel,
                M.Pair(ClosureObservation(M.truth_value)(), M.EmptyList),
                M.EmptyList,
            )()
            return AppendObservation(journal, proposal)()
        return journal

    def _identity_worker(self, operation):
        probe = DirectLawProbe(L.IdentityLawLabel, operation)()
        verdict = M.Head(probe)()
        findings = M.Head(M.Tail(probe)())()
        journal = WorkerJournal(L.IdentityWorkerRoleLabel, findings)()
        if M.IdentityCompare(verdict, L.LawHoldsLabel)() is M.truth_value:
            proposal = ConjecturedLaw(L.IdentityLawLabel, findings, M.EmptyList)()
            return AppendObservation(journal, proposal)()
        return AppendObservation(journal, L.IdentitySearchExhaustedLabel)()

    def _inverse_worker(self, operation):
        probe = DirectLawProbe(L.InverseLawLabel, operation)()
        verdict = M.Head(probe)()
        findings = M.Head(M.Tail(probe)())()
        journal = WorkerJournal(L.InverseWorkerRoleLabel, findings)()
        if M.IdentityCompare(verdict, L.LawHoldsLabel)() is M.truth_value:
            proposal = ConjecturedLaw(L.InverseLawLabel, findings, M.EmptyList)()
            return AppendObservation(journal, proposal)()
        return AppendObservation(journal, L.InverseSearchExhaustedLabel)()

    def _commutativity_worker(self, operation):
        probe = DirectLawProbe(L.CommutativeLawLabel, operation)()
        verdict = M.Head(probe)()
        findings = M.Head(M.Tail(probe)())()
        journal = WorkerJournal(L.CommutativityWorkerRoleLabel, findings)()
        if M.IdentityCompare(verdict, L.LawHoldsLabel)() is M.truth_value:
            proposal = ConjecturedLaw(L.CommutativeLawLabel, findings, M.EmptyList)()
            return AppendObservation(journal, proposal)()
        return journal

    def _associativity_worker(self, operation):
        probe = DirectLawProbe(L.AssociativeLawLabel, operation)()
        verdict = M.Head(probe)()
        findings = M.Head(M.Tail(probe)())()
        record = AssociativitySearchRecord(verdict, findings)()
        journal = WorkerJournal(L.AssociativityWorkerRoleLabel, M.Pair(record, M.EmptyList))()
        if M.IdentityCompare(verdict, L.LawViolatedLabel)() is M.truth_value:
            first = M.Head(findings)()
            witness_left = M.Head(M.Tail(first)())()
            witness_right = M.Head(M.Tail(M.Tail(first)())())()
            refutation = Counterexample(L.AssociativeLawLabel, witness_left, witness_right)()
            return AppendObservation(journal, refutation)()
        if M.IdentityCompare(verdict, L.LawHoldsLabel)() is M.truth_value:
            proposal = ConjecturedLaw(L.AssociativeLawLabel, findings, M.EmptyList)()
            return AppendObservation(journal, proposal)()
        return journal

    def __call__(self):
        return self.result


# ============================================================
# Top-level bounded exploration run
# ============================================================


class ExplorationRun(M.Edge):
    """The bounded exploration entry point.

    Input: one declared operation and an exploration budget (a machine
    nat; the worker roles are bounded by five).

    Output: (ExplorationResult verdict ledger). The ledger carries the
    merged observation chain: closure observations, identity and
    inverse candidates, commutativity observations, associativity
    search records, refutations, and conjectured-law proposals. No
    abstract structure name is assigned during exploration."""

    def __init__(self, operation, budget):
        bounded = M.NatLess(budget, M.six, M.AllConstructors)()
        if bounded is M.false_value:
            ledger = ObservationLedger(M.EmptyList)()
            verdict = L.ExplorationBudgetExhaustedLabel
        else:
            closure_journal = RunLaboratoryWorker(
                LaboratoryCheckpoint(M.one, operation, budget)(),
                L.ClosureWorkerRoleLabel,
            )()
            identity_journal = RunLaboratoryWorker(
                LaboratoryCheckpoint(M.two, operation, budget)(),
                L.IdentityWorkerRoleLabel,
            )()
            inverse_journal = RunLaboratoryWorker(
                LaboratoryCheckpoint(M.three, operation, budget)(),
                L.InverseWorkerRoleLabel,
            )()
            commutativity_journal = RunLaboratoryWorker(
                LaboratoryCheckpoint(M.four, operation, budget)(),
                L.CommutativityWorkerRoleLabel,
            )()
            associativity_journal = RunLaboratoryWorker(
                LaboratoryCheckpoint(M.five, operation, budget)(),
                L.AssociativityWorkerRoleLabel,
            )()
            ledger = MergeObservationLedgers(
                M.Pair(
                    closure_journal,
                    M.Pair(
                        identity_journal,
                        M.Pair(
                            inverse_journal,
                            M.Pair(commutativity_journal, M.Pair(associativity_journal, M.EmptyList)),
                        ),
                    ),
                )
            )()
            verdict = L.ExplorationCompleteLabel
        self.result = M.Pair(L.ExplorationResultLabel, M.Pair(verdict, M.Pair(ledger, M.EmptyList)))
        super().__init__(inputs=M.Pair(operation, M.Pair(budget, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class ExplorationVerdictOf(M.Edge):
    def __init__(self, exploration):
        self.result = M.Head(M.Tail(exploration)())()
        super().__init__(inputs=M.Pair(exploration, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ExplorationLedgerOf(M.Edge):
    def __init__(self, exploration):
        self.result = M.Head(M.Tail(M.Tail(exploration)())())()
        super().__init__(inputs=M.Pair(exploration, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


# ============================================================
# Certification attempt
# ============================================================


class CertificationAttempt(M.Edge):
    """Builds a CertifiedLaw from the observation findings of a
    completed probe: an ExhaustiveFiniteCheck method stamp plus a
    replay record that the recognizer re-derives against the declared
    operation at certification time."""

    def __init__(self, law_label, findings):
        replay = ReplayCheckExhaustive(law_label)()
        self.result = CertifiedLaw(law_label, L.ExhaustiveFiniteCheckLabel, findings, replay)()
        super().__init__(inputs=M.Pair(law_label, M.Pair(findings, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


# ============================================================
# Transfer: consequences of certified structures
# ============================================================


class TransferPrediction(M.Edge):
    """(TransferPrediction certified-laws requested-chain prediction
          source)"""

    def __init__(self, certified_laws, requested_chain, prediction, source):
        self.result = M.Pair(
            L.TransferPredictionLabel,
            M.Pair(certified_laws, M.Pair(requested_chain, M.Pair(prediction, M.Pair(source, M.EmptyList)))),
        )
        super().__init__(
            inputs=M.Pair(
                certified_laws,
                M.Pair(requested_chain, M.Pair(prediction, M.Pair(source, M.EmptyList))),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class PredictTransfer(M.Edge):
    """Given certified laws and a requested composition chain (a b),
    predict the composition from the laws alone. Identity plus inverse
    certificates let the machine answer "a after b" with the identity
    element taken from the identity certificate, without touching the
    operation.

    With the certificates disabled (an empty law chain) the same
    request returns TransferUnavailableLabel: the shortcut exists only
    while the certification exists."""

    def __init__(self, certified_laws, requested_chain):
        identity_law = self._find_law(certified_laws, L.IdentityLawLabel)
        inverse_law = self._find_law(certified_laws, L.InverseLawLabel)
        identity_missing = M.IdentityCompare(identity_law, M.EmptyList)()
        inverse_missing = M.IdentityCompare(inverse_law, M.EmptyList)()
        both_found = M.AndAtom(M.NotAtom(identity_missing)(), M.NotAtom(inverse_missing)())()
        if both_found is M.truth_value:
            findings = CertifiedLawFindingsOf(identity_law)()
            first_candidate = M.Head(findings)()
            identity_element = M.Head(M.Tail(first_candidate)())()
            self.result = TransferPrediction(
                certified_laws,
                requested_chain,
                identity_element,
                L.CertifiedLawLabel,
            )()
        else:
            self.result = TransferPrediction(
                certified_laws,
                requested_chain,
                L.TransferUnavailableLabel,
                M.EmptyList,
            )()
        super().__init__(
            inputs=M.Pair(certified_laws, M.Pair(requested_chain, M.EmptyList)),
            results=self.result,
        )

    def _find_law(self, laws, wanted):
        if M.IdentityCompare(laws, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        law = M.Head(laws)()
        if M.IdentityCompare(CertifiedLawLabelOf(law)(), wanted)() is M.truth_value:
            return law
        return self._find_law(M.Tail(laws)(), wanted)

    def __call__(self):
        return self.result


class EvaluateTransferPrediction(M.Edge):
    """Checks a triangle-carrier transfer prediction against the actual
    triangle composition. Returns TransferConfirmedLabel or
    TransferMismatchLabel."""

    def __init__(self, prediction):
        requested_chain = M.Head(M.Tail(M.Tail(prediction)())())()
        predicted = M.Head(M.Tail(M.Tail(M.Tail(prediction)())())())()
        first = M.Head(requested_chain)()
        second = M.Head(M.Tail(requested_chain)())()
        actual = TriangleCarrierProduct(first, second)()
        if M.TermEqual(predicted, actual)() is M.truth_value:
            self.result = L.TransferConfirmedLabel
        else:
            self.result = L.TransferMismatchLabel
        super().__init__(inputs=M.Pair(prediction, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


__all__ = [name for name in globals() if not name.startswith("_")]
