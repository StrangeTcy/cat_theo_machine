# ============================================================
# math/funceq.py — functional equations as rewrite schemas
#
# A functional equation is DATA: a two-argument ExprEq term over the
# existing expression vocabulary (ApplyLabel / ExprAddLabel /
# ExprMulLabel / ...).  This module compiles such an equation into a
# unary rewrite schema and closes terms under the compiled schema.
#
# Everything here is generic: no equation, function symbol, or
# consequence is named anywhere in this file.  The compiler orients an
# equation exactly as written (no reduction order is imposed — the
# orientation is the equation's own), and the closure enumerates every
# one-step successor at every position of the term.
# ============================================================
from __future__ import annotations

from .. import labels as L
from .. import machine as M
from ..proof import Append, RewriteAtPath, RewriteHere, Rule


class FuncEq(M.Edge):
    """Builds an equation term ExprEq(lhs, rhs): the equation as data."""

    def __init__(self, lhs, rhs):
        self.result = M.Pair(L.ExprEqLabel, M.Pair(lhs, M.Pair(rhs, M.EmptyList)))
        super().__init__(
            inputs=M.Pair(lhs, M.Pair(rhs, M.EmptyList)), results=self.result
        )

    def __call__(self):
        return self.result


class IsEquationTerm(M.Edge):
    """True iff the term is a two-argument ExprEq equation."""

    def __init__(self, term):
        self.result = self._check(term)
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def _check(self, term):
        if M.IsPair(term)() is M.false_value:
            return M.false_value
        if M.IdentityCompare(M.Head(term)(), L.ExprEqLabel)() is M.false_value:
            return M.false_value
        args = M.Tail(term)()
        if M.IsPair(args)() is M.false_value:
            return M.false_value
        rest = M.Tail(args)()
        if M.IsPair(rest)() is M.false_value:
            return M.false_value
        if M.IdentityCompare(M.Tail(rest)(), M.EmptyList)() is M.false_value:
            return M.false_value
        return M.truth_value

    def __call__(self):
        return self.result


class EquationLhs(M.Edge):
    """The left-hand side of a validated equation term."""

    def __init__(self, equation):
        args = M.Tail(equation)()
        self.result = M.Head(args)()
        super().__init__(inputs=M.Pair(equation, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class EquationRhs(M.Edge):
    """The right-hand side of a validated equation term."""

    def __init__(self, equation):
        args = M.Tail(equation)()
        rest = M.Tail(args)()
        self.result = M.Head(rest)()
        super().__init__(inputs=M.Pair(equation, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CompileEquationToSchema(M.Edge):
    """
    Orients an equation term into a unary rewrite schema, as written:
    ExprEq(lhs, rhs) becomes Rule(lhs -> rhs).  Returns
    Pair(truth, Pair(rule, EmptyList)) on a valid equation and
    Pair(false, EmptyList) otherwise.
    """

    def __init__(self, equation, registry):
        self.registry = registry
        self.result = self._compile(equation)
        super().__init__(
            inputs=M.Pair(equation, M.Pair(registry, M.EmptyList)),
            results=self.result,
        )

    def _compile(self, equation):
        if IsEquationTerm(equation)() is M.false_value:
            return M.Pair(M.false_value, M.EmptyList)
        lhs = EquationLhs(equation)()
        rhs = EquationRhs(equation)()
        rule = Rule(lhs, rhs)()
        return M.Pair(M.truth_value, M.Pair(rule, M.EmptyList))

    def __call__(self):
        return self.result


class PathAppend(M.Edge):
    """Appends one path step to a machine path list (0 = head, >=1 = tail)."""

    def __init__(self, path, step):
        self.result = self._append(path, step)
        super().__init__(inputs=M.Pair(path, M.Pair(step, M.EmptyList)), results=self.result)

    def _append(self, path, step):
        if M.IdentityCompare(path, M.EmptyList)() is M.truth_value:
            return M.Pair(step, M.EmptyList)
        return M.Pair(M.Head(path)(), self._append(M.Tail(path)(), step))

    def __call__(self):
        return self.result


class EnumerateSuccessors(M.Edge):
    """
    Every distinct one-step successor of a term under a ruleset, trying
    each rule at every position of the term.  Returns a machine list of
    successor terms (the start term itself is never included).
    """

    def __init__(self, term, rules, registry):
        self.registry = registry
        self.result = self._enumerate(term, rules)

    def _enumerate(self, term, rules):
        positions = self._positions(term, M.EmptyList, M.EmptyList)
        return self._scan(positions, term, rules, M.EmptyList)

    def _positions(self, term, path, acc):
        acc = M.Pair(M.Pair(path, term), acc)
        if M.IsPair(term)() is M.truth_value:
            head_path = PathAppend(path, M.Zero)()
            acc = self._positions(M.Head(term)(), head_path, acc)
            one = M.Head(M.Succ(M.Zero, self.registry)())()
            tail_path = PathAppend(path, one)()
            acc = self._positions(M.Tail(term)(), tail_path, acc)
        return acc

    def _scan(self, positions, term, rules, acc):
        if M.IdentityCompare(positions, M.EmptyList)() is M.truth_value:
            return acc
        element = M.Head(positions)()
        path = M.Head(element)()
        subterm = M.Tail(element)()
        acc = self._try_rules(term, path, subterm, rules, acc)
        return self._scan(M.Tail(positions)(), term, rules, acc)

    def _try_rules(self, term, path, subterm, rules, acc):
        if M.IdentityCompare(rules, M.EmptyList)() is M.truth_value:
            return acc
        rule = M.Head(rules)()
        if self._fires_at(rule, subterm) is M.truth_value:
            nxt = RewriteAtPath(rule, term, path, self.registry)()
            acc = self._add_new(acc, nxt)
        return self._try_rules(term, path, subterm, M.Tail(rules)(), acc)

    def _fires_at(self, rule, subterm):
        if M.IsPair(subterm)() is M.false_value:
            return M.false_value
        fired = RewriteHere(rule, subterm)()
        if M.Compare(fired, subterm)() is M.false_value:
            return M.truth_value
        return M.false_value

    def _add_new(self, acc, nxt):
        if self._contains(acc, nxt) is M.truth_value:
            return acc
        return M.Pair(nxt, acc)

    def _contains(self, acc, target):
        if M.IdentityCompare(acc, M.EmptyList)() is M.truth_value:
            return M.false_value
        if M.Compare(M.Head(acc)(), target)() is M.truth_value:
            return M.truth_value
        return self._contains(M.Tail(acc)(), target)

    def __call__(self):
        return self.result


class CloseTermUnderRules(M.Edge):
    """
    Bounded closure of a term under a ruleset: repeatedly enumerates
    successors until no new term appears or the depth bound is reached.
    Returns the machine list of reachable terms, the start term first.
    """

    def __init__(self, term, rules, depth, registry):
        self.registry = registry
        self.result = self._close(term, rules, depth)

    def _close(self, term, rules, depth):
        return self._rounds(M.Pair(term, M.EmptyList), M.Pair(term, M.EmptyList), rules, depth)

    def _rounds(self, frontier, seen, rules, depth):
        if M.IdentityCompare(depth, M.Zero)() is M.truth_value:
            return seen
        if M.IdentityCompare(frontier, M.EmptyList)() is M.truth_value:
            return seen
        expanded = self._expand(frontier, rules, seen, M.EmptyList)
        new_frontier = M.Head(expanded)()
        new_seen = M.Tail(expanded)()
        pred = M.Head(M.NatPred(depth, self.registry)())()
        return self._rounds(new_frontier, new_seen, rules, pred)

    def _expand(self, frontier, rules, seen, fresh):
        if M.IdentityCompare(frontier, M.EmptyList)() is M.truth_value:
            return M.Pair(fresh, seen)
        term = M.Head(frontier)()
        successors = EnumerateSuccessors(term, rules, self.registry)()
        absorbed = self._absorb(successors, seen, fresh)
        new_fresh = M.Head(absorbed)()
        new_seen = M.Tail(absorbed)()
        rest = self._expand(M.Tail(frontier)(), rules, new_seen, M.EmptyList)
        rest_fresh = M.Head(rest)()
        rest_seen = M.Tail(rest)()
        return M.Pair(Append(new_fresh, rest_fresh)(), rest_seen)

    def _absorb(self, successors, seen, fresh):
        if M.IdentityCompare(successors, M.EmptyList)() is M.truth_value:
            return M.Pair(fresh, seen)
        candidate = M.Head(successors)()
        if self._contains(seen, candidate) is M.truth_value:
            return self._absorb(M.Tail(successors)(), seen, fresh)
        seen = M.Pair(candidate, seen)
        fresh = M.Pair(candidate, fresh)
        return self._absorb(M.Tail(successors)(), seen, fresh)

    def _contains(self, acc, target):
        if M.IdentityCompare(acc, M.EmptyList)() is M.truth_value:
            return M.false_value
        if M.Compare(M.Head(acc)(), target)() is M.truth_value:
            return M.truth_value
        return self._contains(M.Tail(acc)(), target)

    def __call__(self):
        return self.result


class IsNormalForm(M.Edge):
    """
    True iff the term admits no one-step successor under the ruleset:
    machine-checked termination evidence for a closed derivation.
    """

    def __init__(self, term, rules, registry):
        self.registry = registry
        successors = EnumerateSuccessors(term, rules, self.registry)()
        self.result = M.IdentityCompare(successors, M.EmptyList)()
        super().__init__(
            inputs=M.Pair(term, M.Pair(rules, M.Pair(registry, M.EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result


__all__ = [
    "FuncEq",
    "IsEquationTerm",
    "EquationLhs",
    "EquationRhs",
    "CompileEquationToSchema",
    "PathAppend",
    "EnumerateSuccessors",
    "CloseTermUnderRules",
    "IsNormalForm",
]
