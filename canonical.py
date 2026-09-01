from __future__ import annotations

"""Canonical ordering of commutative-operator arguments.

The product and sum of non-negative terms are commutative, but the
machine's terms carry their arguments in a fixed order: the rule
product_of_nonnegative_terms derives NonNegative(?x * ?y) with ?x and
?y bound in the order the premises are joined, so it can emit
NonNegative((b^2) * (a^2)) where the goal asks NonNegative((a^2) *
(b^2)). Without a notion that those are the same term, goal
recognition -- which tests exact structural equality -- never sees the
goal, and a genuinely derived fact is missed.

These edges put the arguments of the commutative term constructors
(ExprMulLabel and ExprAddLabel) into one total order, recursively, so
that two terms equal up to commutativity of * and + compare equal after
canonicalization. The ordering is the machine's own structural order
on term ranks; no theorem-specific content lives here -- it treats every
Mul/Add identically regardless of which goal is sought.
"""

from .core import (
    Edge,
    EmptyList,
    Head,
    IdentityCompare,
    Pair,
    Tail,
    false_value,
    truth_value,
)
from .machine import IsPair
from .labels import ExprAddLabel, ExprMulLabel


_COMMUTATIVE_HEADS = Pair(ExprMulLabel, Pair(ExprAddLabel, EmptyList))


class IsCommutativeHead(Edge):
    """True when a term head is one of the commutative operators."""

    def __init__(self, head):
        self.result = self._is(head, _COMMUTATIVE_HEADS)
        super().__init__(inputs=Pair(head, EmptyList), results=self.result)

    def _is(self, head, heads):
        if IdentityCompare(heads, EmptyList)() is truth_value:
            return false_value
        if IdentityCompare(Head(heads)(), head)() is truth_value:
            return truth_value
        return self._is(head, Tail(heads)())

    def __call__(self):
        return self.result


class TermRank(Edge):
    """A host integer rank for total structural ordering of terms.

    Leaves (Char constants, singleton labels, nat atoms) rank below
    compound terms; compounds are ranked by their head's symbol, ties
    broken by argument count, so the order is total and independent of
    object identity. This is an ordering key only -- it never decides
    equality by itself (CanonicalTerm + structural equality does).
    """

    def __init__(self, term):
        self.result = self._rank(term)
        super().__init__(inputs=Pair(term, EmptyList), results=self.result)

    def _rank(self, term):
        if IsPair(term)() is not truth_value:
            symbol = self._symbol(term)
            return (0, symbol, 0)
        head = Head(term)()
        args = Tail(term)()
        return (1, self._symbol(head), self._arg_count(args))

    def _arg_count(self, args):
        if IdentityCompare(args, EmptyList)() is truth_value:
            return 0
        return 1 + self._arg_count(Tail(args)())

    def _symbol(self, atom):
        try:
            value = atom()
        except Exception:
            return ""
        if value is None:
            return ""
        return str(value)

    def __call__(self):
        return self.result


class TermBefore(Edge):
    """True when term x sorts strictly before term y in canonical order.

    Compounds sort after leaves; among compounds, by head symbol then
    argument count; ties (same shape) fall to recursive argument
    comparison, giving a total order.
    """

    def __init__(self, x, y):
        self.result = self._before(x, y)
        super().__init__(inputs=Pair(x, Pair(y, EmptyList)), results=self.result)

    def _before(self, x, y):
        rx = TermRank(x)()
        ry = TermRank(y)()
        if rx < ry:
            return truth_value
        if rx > ry:
            return false_value
        if IsPair(x)() is not truth_value:
            return false_value
        return self._args_before(Tail(x)(), Tail(y)())

    def _args_before(self, xs, ys):
        x_empty = IdentityCompare(xs, EmptyList)() is truth_value
        y_empty = IdentityCompare(ys, EmptyList)() is truth_value
        if x_empty and y_empty:
            return false_value
        if x_empty:
            return truth_value
        if y_empty:
            return false_value
        x = Head(xs)()
        y = Head(ys)()
        if TermBefore(x, y)() is truth_value:
            return truth_value
        if TermBefore(y, x)() is truth_value:
            return false_value
        return self._args_before(Tail(xs)(), Tail(ys)())

    def __call__(self):
        return self.result


class CanonicalTerm(Edge):
    """A term with every commutative operator's arguments ordered.

    Recurses through the term tree; for a Mul/Add the two (or more,
    flattened one level) arguments are canonicalized and sorted by
    TermBefore, then rebuilt under the same head. Non-commutative
    compounds keep their head and canonicalize their arguments in
    place.
    """

    def __init__(self, term):
        self.result = self._canonical(term)
        super().__init__(inputs=Pair(term, EmptyList), results=self.result)

    def _canonical(self, term):
        if IsPair(term)() is not truth_value:
            return term
        head = Head(term)()
        canon_args = self._canonical_args(Tail(term)())
        if IsCommutativeHead(head)() is truth_value:
            ordered = self._sort(canon_args)
            return Pair(head, ordered)
        return Pair(head, canon_args)

    def _canonical_args(self, args):
        if IdentityCompare(args, EmptyList)() is truth_value:
            return EmptyList
        first = self._canonical(Head(args)())
        return Pair(first, self._canonical_args(Tail(args)()))

    def _sort(self, args):
        # Insertion sort over the machine list, comparing by TermBefore.
        return self._insert_all(args, EmptyList)

    def _insert_all(self, remaining, acc):
        if IdentityCompare(remaining, EmptyList)() is truth_value:
            return acc
        return self._insert_all(
            Tail(remaining)(),
            self._insert(Head(remaining)(), acc),
        )

    def _insert(self, item, acc):
        if IdentityCompare(acc, EmptyList)() is truth_value:
            return Pair(item, EmptyList)
        head = Head(acc)()
        if TermBefore(item, head)() is truth_value:
            return Pair(item, acc)
        return Pair(head, self._insert(item, Tail(acc)()))

    def __call__(self):
        return self.result


class CanonicalFact(Edge):
    """A single knowledge fact canonicalized under commutativity."""

    def __init__(self, fact):
        self.result = CanonicalTerm(fact)()
        super().__init__(inputs=Pair(fact, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CanonicalFactChain(Edge):
    """Every fact in a knowledge fact chain canonicalized."""

    def __init__(self, facts):
        self.result = self._map(facts)
        super().__init__(inputs=Pair(facts, EmptyList), results=self.result)

    def _map(self, facts):
        if IdentityCompare(facts, EmptyList)() is truth_value:
            return EmptyList
        first = CanonicalTerm(Head(facts)())()
        return Pair(first, self._map(Tail(facts)()))

    def __call__(self):
        return self.result


__all__ = [name for name in globals() if not name.startswith("_")]
