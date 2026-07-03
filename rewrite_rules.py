from __future__ import annotations

"""Working active rewrite rules.

Only the currently validated rewrite rules live here. The larger experimental
AST rule layer can remain in ``hyge.machine`` until a later true extraction.
"""

from . import machine as M
from .heuristics import Heuristic
from .labels import InsertionOrderLabel, RewriteDFSLabel
from .proof import Rule


class DistributeRightRule(Rule):
    def __init__(self):
        a_name = M.Char("a")
        b_name = M.Char("b")
        c_name = M.Char("c")

        a = M.Pair(M.VarTag, M.Pair(a_name, M.EmptyList))
        b = M.Pair(M.VarTag, M.Pair(b_name, M.EmptyList))
        c = M.Pair(M.VarTag, M.Pair(c_name, M.EmptyList))

        sum_ab = M.Pair(M.ExprAddLabel, M.Pair(a, M.Pair(b, M.EmptyList)))
        pattern = M.Pair(M.ExprMulLabel, M.Pair(c, M.Pair(sum_ab, M.EmptyList)))

        ca = M.Pair(M.ExprMulLabel, M.Pair(c, M.Pair(a, M.EmptyList)))
        cb = M.Pair(M.ExprMulLabel, M.Pair(c, M.Pair(b, M.EmptyList)))
        replacement = M.Pair(M.ExprAddLabel, M.Pair(ca, M.Pair(cb, M.EmptyList)))

        super().__init__(pattern, replacement)


class MulAssocRule(Rule):
    def __init__(self):
        a_name = M.Char("a")
        b_name = M.Char("b")
        c_name = M.Char("c")

        a = M.Pair(M.VarTag, M.Pair(a_name, M.EmptyList))
        b = M.Pair(M.VarTag, M.Pair(b_name, M.EmptyList))
        c = M.Pair(M.VarTag, M.Pair(c_name, M.EmptyList))

        inner = M.Pair(M.ExprMulLabel, M.Pair(b, M.Pair(c, M.EmptyList)))
        pattern = M.Pair(M.ExprMulLabel, M.Pair(a, M.Pair(inner, M.EmptyList)))

        left = M.Pair(M.ExprMulLabel, M.Pair(a, M.Pair(b, M.EmptyList)))
        replacement = M.Pair(M.ExprMulLabel, M.Pair(left, M.Pair(c, M.EmptyList)))

        super().__init__(pattern, replacement)


def build_distrib_assoc_demo_terms():
    a_sym = M.Char("a")
    b_sym = M.Char("b")
    c_sym = M.Char("c")
    d_sym = M.Char("d")

    cd = M.Pair(M.ExprMulLabel, M.Pair(c_sym, M.Pair(d_sym, M.EmptyList)))
    b_plus_cd = M.Pair(M.ExprAddLabel, M.Pair(b_sym, M.Pair(cd, M.EmptyList)))
    expr_start = M.Pair(M.ExprMulLabel, M.Pair(a_sym, M.Pair(b_plus_cd, M.EmptyList)))

    ab = M.Pair(M.ExprMulLabel, M.Pair(a_sym, M.Pair(b_sym, M.EmptyList)))
    ac = M.Pair(M.ExprMulLabel, M.Pair(a_sym, M.Pair(c_sym, M.EmptyList)))
    acd = M.Pair(M.ExprMulLabel, M.Pair(ac, M.Pair(d_sym, M.EmptyList)))
    expr_goal = M.Pair(M.ExprAddLabel, M.Pair(ab, M.Pair(acd, M.EmptyList)))

    return expr_start, expr_goal


def build_default_rewrite_rule_chain():
    r1 = DistributeRightRule()
    r2 = MulAssocRule()
    return M.Pair(r1, M.Pair(r2, M.EmptyList))


def build_default_rewrite_heuristic():
    return Heuristic(
        RewriteDFSLabel,
        InsertionOrderLabel,
        M.Zero,
        M.one,
        M.one,
    )()


__all__ = [name for name in globals() if not name.startswith("_")]
