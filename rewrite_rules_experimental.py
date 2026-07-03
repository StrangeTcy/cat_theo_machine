from __future__ import annotations

"""Experimental rewrite rules carried over from the monolith's math-rules block.

These are not part of the default validated rewrite chain. They are kept here so
the larger expression-rewrite surface has a real home during the ongoing split.
"""

from . import machine as M
from .proof import Rule


def _var(name: str):
    return M.Pair(M.VarTag, M.Pair(M.Char(name), M.EmptyList))


def _int(atom):
    return M.Pair(M.ExprIntLabel, M.Pair(atom, M.EmptyList))


class AddZeroLeftRule(Rule):
    def __init__(self):
        a = _var("a")
        pattern = M.Pair(M.ExprAddLabel, M.Pair(_int(M.Zero), M.Pair(a, M.EmptyList)))
        super().__init__(pattern, a)


class AddZeroRightRule(Rule):
    def __init__(self):
        a = _var("a")
        pattern = M.Pair(M.ExprAddLabel, M.Pair(a, M.Pair(_int(M.Zero), M.EmptyList)))
        super().__init__(pattern, a)


class MulOneLeftRule(Rule):
    def __init__(self):
        a = _var("a")
        pattern = M.Pair(M.ExprMulLabel, M.Pair(_int(M.one), M.Pair(a, M.EmptyList)))
        super().__init__(pattern, a)


class MulOneRightRule(Rule):
    def __init__(self):
        a = _var("a")
        pattern = M.Pair(M.ExprMulLabel, M.Pair(a, M.Pair(_int(M.one), M.EmptyList)))
        super().__init__(pattern, a)


class MulZeroLeftRule(Rule):
    def __init__(self):
        a = _var("a")
        zero = _int(M.Zero)
        pattern = M.Pair(M.ExprMulLabel, M.Pair(zero, M.Pair(a, M.EmptyList)))
        super().__init__(pattern, zero)


class MulZeroRightRule(Rule):
    def __init__(self):
        a = _var("a")
        zero = _int(M.Zero)
        pattern = M.Pair(M.ExprMulLabel, M.Pair(a, M.Pair(zero, M.EmptyList)))
        super().__init__(pattern, zero)


class AddAssocRule(Rule):
    def __init__(self):
        a = _var("a")
        b = _var("b")
        c = _var("c")
        inner = M.Pair(M.ExprAddLabel, M.Pair(b, M.Pair(c, M.EmptyList)))
        pattern = M.Pair(M.ExprAddLabel, M.Pair(a, M.Pair(inner, M.EmptyList)))
        left = M.Pair(M.ExprAddLabel, M.Pair(a, M.Pair(b, M.EmptyList)))
        replacement = M.Pair(M.ExprAddLabel, M.Pair(left, M.Pair(c, M.EmptyList)))
        super().__init__(pattern, replacement)


class AddCommuteRule(Rule):
    def __init__(self):
        a = _var("a")
        b = _var("b")
        pattern = M.Pair(M.ExprAddLabel, M.Pair(a, M.Pair(b, M.EmptyList)))
        replacement = M.Pair(M.ExprAddLabel, M.Pair(b, M.Pair(a, M.EmptyList)))
        super().__init__(pattern, replacement)


class DistributeLeftRule(Rule):
    def __init__(self):
        a = _var("a")
        b = _var("b")
        c = _var("c")
        sum_ab = M.Pair(M.ExprAddLabel, M.Pair(a, M.Pair(b, M.EmptyList)))
        pattern = M.Pair(M.ExprMulLabel, M.Pair(sum_ab, M.Pair(c, M.EmptyList)))
        ac = M.Pair(M.ExprMulLabel, M.Pair(a, M.Pair(c, M.EmptyList)))
        bc = M.Pair(M.ExprMulLabel, M.Pair(b, M.Pair(c, M.EmptyList)))
        replacement = M.Pair(M.ExprAddLabel, M.Pair(ac, M.Pair(bc, M.EmptyList)))
        super().__init__(pattern, replacement)


class DistributeRightRule(Rule):
    def __init__(self):
        a = _var("a")
        b = _var("b")
        c = _var("c")
        sum_ab = M.Pair(M.ExprAddLabel, M.Pair(a, M.Pair(b, M.EmptyList)))
        pattern = M.Pair(M.ExprMulLabel, M.Pair(c, M.Pair(sum_ab, M.EmptyList)))
        ca = M.Pair(M.ExprMulLabel, M.Pair(c, M.Pair(a, M.EmptyList)))
        cb = M.Pair(M.ExprMulLabel, M.Pair(c, M.Pair(b, M.EmptyList)))
        replacement = M.Pair(M.ExprAddLabel, M.Pair(ca, M.Pair(cb, M.EmptyList)))
        super().__init__(pattern, replacement)


class FractionAddRule(Rule):
    def __init__(self):
        p = _var("p")
        q = _var("q")
        r = _var("r")
        s = _var("s")
        frac1 = M.Pair(M.ExprFracLabel, M.Pair(p, M.Pair(q, M.EmptyList)))
        frac2 = M.Pair(M.ExprFracLabel, M.Pair(r, M.Pair(s, M.EmptyList)))
        pattern = M.Pair(M.ExprAddLabel, M.Pair(frac1, M.Pair(frac2, M.EmptyList)))
        p_times_s = M.Pair(M.ExprMulLabel, M.Pair(p, M.Pair(s, M.EmptyList)))
        r_times_q = M.Pair(M.ExprMulLabel, M.Pair(r, M.Pair(q, M.EmptyList)))
        num = M.Pair(M.ExprAddLabel, M.Pair(p_times_s, M.Pair(r_times_q, M.EmptyList)))
        den = M.Pair(M.ExprMulLabel, M.Pair(q, M.Pair(s, M.EmptyList)))
        replacement = M.Pair(M.ExprFracLabel, M.Pair(num, M.Pair(den, M.EmptyList)))
        super().__init__(pattern, replacement)


class FractionMulRule(Rule):
    def __init__(self):
        p = _var("p")
        q = _var("q")
        r = _var("r")
        s = _var("s")
        frac1 = M.Pair(M.ExprFracLabel, M.Pair(p, M.Pair(q, M.EmptyList)))
        frac2 = M.Pair(M.ExprFracLabel, M.Pair(r, M.Pair(s, M.EmptyList)))
        pattern = M.Pair(M.ExprMulLabel, M.Pair(frac1, M.Pair(frac2, M.EmptyList)))
        num = M.Pair(M.ExprMulLabel, M.Pair(p, M.Pair(r, M.EmptyList)))
        den = M.Pair(M.ExprMulLabel, M.Pair(q, M.Pair(s, M.EmptyList)))
        replacement = M.Pair(M.ExprFracLabel, M.Pair(num, M.Pair(den, M.EmptyList)))
        super().__init__(pattern, replacement)


class FractionReciprocalRule(Rule):
    def __init__(self):
        p = _var("p")
        q = _var("q")
        frac = M.Pair(M.ExprFracLabel, M.Pair(p, M.Pair(q, M.EmptyList)))
        pattern = M.Pair(M.ExprDivLabel, M.Pair(_int(M.one), M.Pair(frac, M.EmptyList)))
        replacement = M.Pair(M.ExprFracLabel, M.Pair(q, M.Pair(p, M.EmptyList)))
        super().__init__(pattern, replacement)


class PowOneRule(Rule):
    def __init__(self):
        base = _var("base")
        pattern = M.Pair(M.ExprPowLabel, M.Pair(base, M.Pair(_int(M.one), M.EmptyList)))
        super().__init__(pattern, base)


class PowZeroRule(Rule):
    def __init__(self):
        base = _var("base")
        pattern = M.Pair(M.ExprPowLabel, M.Pair(base, M.Pair(_int(M.Zero), M.EmptyList)))
        super().__init__(pattern, _int(M.one))


class MulAssocRule(Rule):
    def __init__(self):
        a = _var("a")
        b = _var("b")
        c = _var("c")
        inner = M.Pair(M.ExprMulLabel, M.Pair(b, M.Pair(c, M.EmptyList)))
        pattern = M.Pair(M.ExprMulLabel, M.Pair(a, M.Pair(inner, M.EmptyList)))
        left = M.Pair(M.ExprMulLabel, M.Pair(a, M.Pair(b, M.EmptyList)))
        replacement = M.Pair(M.ExprMulLabel, M.Pair(left, M.Pair(c, M.EmptyList)))
        super().__init__(pattern, replacement)


def build_experimental_rewrite_rules():
    return [
        AddAssocRule(),
        AddCommuteRule(),
        AddZeroLeftRule(),
        AddZeroRightRule(),
        MulAssocRule(),
        MulOneLeftRule(),
        MulOneRightRule(),
        MulZeroLeftRule(),
        MulZeroRightRule(),
        DistributeLeftRule(),
        DistributeRightRule(),
        FractionAddRule(),
        FractionMulRule(),
        FractionReciprocalRule(),
        PowOneRule(),
        PowZeroRule(),
    ]


def build_experimental_rewrite_rule_chain():
    chain = M.EmptyList
    for rule in reversed(build_experimental_rewrite_rules()):
        chain = M.Pair(rule, chain)
    return chain


__all__ = [name for name in globals() if not name.startswith("_")]
