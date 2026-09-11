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
)
from . import machine as M


class CanonicalTerm(Edge):
    """A term with commutative-operator arguments put in machine order.

    Delegates to the machine's CanonicalArithmeticTerm over the full
    constructor registry; non-commutative compounds keep their head and
    canonicalize their arguments in place.
    """

    def __init__(self, term):
        self.result = M.CanonicalArithmeticTerm(term, M.AllConstructors)()
        super().__init__(inputs=Pair(term, EmptyList), results=self.result)

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
