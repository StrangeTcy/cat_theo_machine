"""Researcher-v0 — inert chain operations (no Python containers).

Every list in this package is a `machine.Pair` chain, exactly as the rest of
the substrate does it. Each operation here is an `Edge` class whose `result`
is the answer; there are no module-level functions and no mutable module
state. Call sites read `Class(args)()`.
"""

from __future__ import annotations

from .. import machine as M


class ChainLength(M.Edge):
    """Number of terms in a Pair chain (reporting int)."""

    def __init__(self, chain):
        self.result = self._length(chain, 0)
        super().__init__(inputs=M.Pair(chain, M.EmptyList), results=self.result)

    def _length(self, chain, so_far):
        if M.IdentityCompare(chain, M.EmptyList)() is M.truth_value:
            return so_far
        return self._length(M.Tail(chain)(), so_far + 1)

    def __call__(self):
        return self.result


class ChainAppend(M.Edge):
    """A new chain with `term` added at the end (input chain unchanged)."""

    def __init__(self, chain, term):
        self.result = self._append(chain, term)
        super().__init__(
            inputs=M.Pair(chain, M.Pair(term, M.EmptyList)), results=self.result
        )

    def _append(self, chain, term):
        if M.IdentityCompare(chain, M.EmptyList)() is M.truth_value:
            return M.Pair(term, M.EmptyList)
        return M.Pair(M.Head(chain)(), self._append(M.Tail(chain)(), term))

    def __call__(self):
        return self.result


class ChainJoin(M.Edge):
    """A new chain: every term of `second` appended after `first`."""

    def __init__(self, first, second):
        self.result = self._join(first, second)
        super().__init__(
            inputs=M.Pair(first, M.Pair(second, M.EmptyList)), results=self.result
        )

    def _join(self, first, second):
        if M.IdentityCompare(second, M.EmptyList)() is M.truth_value:
            return first
        extended = ChainAppend(first, M.Head(second)())()
        return self._join(extended, M.Tail(second)())

    def __call__(self):
        return self.result


class ChainHas(M.Edge):
    """Does the chain contain a term `Compare`-equal to `term`?"""

    def __init__(self, chain, term):
        self.result = self._scan(chain, term)
        super().__init__(
            inputs=M.Pair(chain, M.Pair(term, M.EmptyList)), results=self.result
        )

    def _scan(self, chain, term):
        if M.IdentityCompare(chain, M.EmptyList)() is M.truth_value:
            return M.false_value
        if M.Compare(M.Head(chain)(), term)() is M.truth_value:
            return M.truth_value
        return self._scan(M.Tail(chain)(), term)

    def __call__(self):
        return self.result


class ChainIndex(M.Edge):
    """Index of the first term `Compare`-equal to `term`, else EmptyList."""

    def __init__(self, chain, term):
        self.result = self._scan(chain, term, 0)
        super().__init__(
            inputs=M.Pair(chain, M.Pair(term, M.EmptyList)), results=self.result
        )

    def _scan(self, chain, term, position):
        if M.IdentityCompare(chain, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        if M.Compare(M.Head(chain)(), term)() is M.truth_value:
            return position
        return self._scan(M.Tail(chain)(), term, position + 1)

    def __call__(self):
        return self.result


class ChainWithoutIndex(M.Edge):
    """A new chain with the term at `position` removed."""

    def __init__(self, chain, position):
        self.result = self._rebuild(chain, position, 0)
        super().__init__(
            inputs=M.Pair(chain, M.Pair(position, M.EmptyList)), results=self.result
        )

    def _rebuild(self, chain, position, current):
        if M.IdentityCompare(chain, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        if current == position:
            return M.Tail(chain)()
        return M.Pair(
            M.Head(chain)(), self._rebuild(M.Tail(chain)(), position, current + 1)
        )

    def __call__(self):
        return self.result


class TextLess(M.Edge):
    """Display-order comparison of two text payloads (`<` on their symbols)."""

    def __init__(self, first, second):
        left = first() if callable(first) else first
        right = second() if callable(second) else second
        self.result = M.truth_value if left < right else M.false_value
        super().__init__(
            inputs=M.Pair(first, M.Pair(second, M.EmptyList)), results=self.result
        )

    def __call__(self):
        return self.result


class ChainInsertSortedText(M.Edge):
    """Insert a text atom into a chain kept in ascending text order.

    The sorted chain is how the ruleset digest becomes order-independent
    (A2.2): the digest is taken over the sorted per-rule digests.
    """

    def __init__(self, chain, atom):
        self.result = self._insert(chain, atom)
        super().__init__(
            inputs=M.Pair(chain, M.Pair(atom, M.EmptyList)), results=self.result
        )

    def _insert(self, chain, atom):
        if M.IdentityCompare(chain, M.EmptyList)() is M.truth_value:
            return M.Pair(atom, M.EmptyList)
        if TextLess(atom, M.Head(chain)())() is M.truth_value:
            return M.Pair(atom, chain)
        return M.Pair(M.Head(chain)(), self._insert(M.Tail(chain)(), atom))

    def __call__(self):
        return self.result


class ChainSortText(M.Edge):
    """A new chain holding the same text atoms in ascending order."""

    def __init__(self, chain):
        self.result = self._sort(chain, M.EmptyList)
        super().__init__(inputs=M.Pair(chain, M.EmptyList), results=self.result)

    def _sort(self, remaining, built):
        if M.IdentityCompare(remaining, M.EmptyList)() is M.truth_value:
            return built
        return self._sort(
            M.Tail(remaining)(),
            ChainInsertSortedText(built, M.Head(remaining)())(),
        )

    def __call__(self):
        return self.result


class IsEmptyTerm(M.Edge):
    """Is this term `EmptyList` itself?

    `IdentityCompare` walks atom identity (`core.py:202` reads `.id`), so it is
    for atoms only: an index or count carried as a Python int must be tested
    for emptiness here instead.
    """

    def __init__(self, term):
        if term is M.EmptyList:
            self.result = M.truth_value
        else:
            self.result = M.false_value
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result
