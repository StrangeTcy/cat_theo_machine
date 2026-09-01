from __future__ import annotations

"""Canonical ordering of commutative-operator arguments.

Product and sum are commutative, but a term carries its arguments in the
order they were built, so a derived NonNegative((b^2) * (a^2)) is not
structurally equal to the goal NonNegative((a^2) * (b^2)) and goal
recognition (which tests exact structural equality) misses it.

Canonicalization puts the arguments of every commutative operator into one
total order, recursively, so two terms equal up to commutativity compare
equal afterwards. The ordering and all arithmetic normalisation are done by
the machine's own canonicalizer edge (which orders nats by NatLess and
atoms by their machine order, and flattens/rebuilds Add/Mul/Eq as machine
pairs) -- this module exposes only fact/fact-chain mappings over it and
contains no host ordering (no host ints, tuples, strings, or host
comparison of term ranks). No theorem-specific content lives here: every
Mul/Add is treated identically.
"""

from .core import (
    Edge,
    EmptyList,
    Head,
    IdentityCompare,
    Pair,
    Tail,
    truth_value,
)
from . import machine as M
from .labels import ExprAddLabel, ExprEqLabel, ExprMulLabel


def _is_arithmetic_head(head):
    is_mul = IdentityCompare(head, ExprMulLabel)()
    if is_mul is truth_value:
        return truth_value
    is_add = IdentityCompare(head, ExprAddLabel)()
    if is_add is truth_value:
        return truth_value
    return IdentityCompare(head, ExprEqLabel)()


class CanonicalTerm(Edge):
    """A term with commutative-operator arguments put in machine order.

    Only the commutative arithmetic operators (Mul/Add/Eq) are reordered, by
    delegating that subterm to the machine's CanonicalArithmeticTerm edge,
    which orders nats by NatLess and atoms by machine order. Every other
    compound (predicates such as NonNegative/IsReal/Sqrt, surface chains) is
    preserved structurally -- its head kept and its arguments canonicalized
    in place -- so non-arithmetic facts are never interned or reshaped.
    """

    def __init__(self, term):
        self.result = self._canonical(term)
        super().__init__(inputs=Pair(term, EmptyList), results=self.result)

    def _canonical(self, term):
        is_pair = M.IsPair(term)()
        if is_pair is truth_value:
            head = Head(term)()
            is_ac = _is_arithmetic_head(head)
            if is_ac is truth_value:
                return M.CanonicalArithmeticTerm(term, M.AllConstructors)()
            return Pair(head, self._canonical_args(Tail(term)()))
        return term

    def _canonical_args(self, args):
        empty = IdentityCompare(args, EmptyList)()
        if empty is truth_value:
            return EmptyList
        first = self._canonical(Head(args)())
        return Pair(first, self._canonical_args(Tail(args)()))

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
        empty = IdentityCompare(facts, EmptyList)()
        if empty is M.truth_value:
            return EmptyList
        first = CanonicalTerm(Head(facts)())()
        return Pair(first, self._map(Tail(facts)()))

    def __call__(self):
        return self.result
