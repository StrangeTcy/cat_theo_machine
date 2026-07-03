from __future__ import annotations

from . import machine as M
from .graph import Reverse
from .proof import Rule

SqrtLabel = M.SqrtLabel
SqrtSeqTermLabel = M.SqrtSeqTermLabel
NewtonStepTermLabel = M.NewtonStepTermLabel
NewtonPositiveLabel = M.NewtonPositiveLabel
NewtonErrorIdentityLabel = M.NewtonErrorIdentityLabel
NewtonErrorShrinksLabel = M.NewtonErrorShrinksLabel
SqrtSeqCauchyLabel = M.SqrtSeqCauchyLabel
IsCauchyLabel = M.IsCauchyLabel
RealNumLabel = M.RealNumLabel
IsRealLabel = M.IsRealLabel


class SqrtUnfoldRule(Rule):
    def __init__(self):
        a_name = M.Char("a")
        a = M.Pair(M.VarTag, M.Pair(a_name, M.EmptyList))
        pattern = M.Pair(SqrtLabel, M.Pair(a, M.EmptyList))
        replacement = M.Pair(SqrtSeqTermLabel, M.Pair(a, M.EmptyList))
        super().__init__(pattern, replacement)


class SqrtSeqToNewtonStepRule(Rule):
    def __init__(self):
        a_name = M.Char("a")
        a = M.Pair(M.VarTag, M.Pair(a_name, M.EmptyList))
        seq = M.Pair(SqrtSeqTermLabel, M.Pair(a, M.EmptyList))
        pattern = seq
        replacement = M.Pair(NewtonStepTermLabel, M.Pair(seq, M.EmptyList))
        super().__init__(pattern, replacement)


class NewtonPositiveRule(Rule):
    def __init__(self):
        s_name = M.Char("s")
        s = M.Pair(M.VarTag, M.Pair(s_name, M.EmptyList))
        pattern = M.Pair(NewtonStepTermLabel, M.Pair(s, M.EmptyList))
        replacement = M.Pair(NewtonPositiveLabel, M.Pair(s, M.EmptyList))
        super().__init__(pattern, replacement)


class NewtonErrorIdentityRule(Rule):
    def __init__(self):
        s_name = M.Char("s")
        s = M.Pair(M.VarTag, M.Pair(s_name, M.EmptyList))
        pattern = M.Pair(NewtonPositiveLabel, M.Pair(s, M.EmptyList))
        replacement = M.Pair(NewtonErrorIdentityLabel, M.Pair(s, M.EmptyList))
        super().__init__(pattern, replacement)


class NewtonErrorShrinksRule(Rule):
    def __init__(self):
        s_name = M.Char("s")
        s = M.Pair(M.VarTag, M.Pair(s_name, M.EmptyList))
        pattern = M.Pair(NewtonErrorIdentityLabel, M.Pair(s, M.EmptyList))
        replacement = M.Pair(NewtonErrorShrinksLabel, M.Pair(s, M.EmptyList))
        super().__init__(pattern, replacement)


class NewtonShrinksToCauchyRule(Rule):
    def __init__(self):
        s_name = M.Char("s")
        s = M.Pair(M.VarTag, M.Pair(s_name, M.EmptyList))
        pattern = M.Pair(NewtonErrorShrinksLabel, M.Pair(s, M.EmptyList))
        replacement = M.Pair(SqrtSeqCauchyLabel, M.Pair(s, M.EmptyList))
        super().__init__(pattern, replacement)


class SqrtSeqCauchyToIsCauchyRule(Rule):
    def __init__(self):
        s_name = M.Char("s")
        s = M.Pair(M.VarTag, M.Pair(s_name, M.EmptyList))
        pattern = M.Pair(SqrtSeqCauchyLabel, M.Pair(s, M.EmptyList))
        replacement = M.Pair(IsCauchyLabel, M.Pair(s, M.EmptyList))
        super().__init__(pattern, replacement)


class CauchyToRealNumRule(Rule):
    def __init__(self):
        s_name = M.Char("s")
        s = M.Pair(M.VarTag, M.Pair(s_name, M.EmptyList))
        pattern = M.Pair(IsCauchyLabel, M.Pair(s, M.EmptyList))
        replacement = M.Pair(RealNumLabel, M.Pair(s, M.EmptyList))
        super().__init__(pattern, replacement)


class RealNumSqrtSeqToIsRealSqrtRule(Rule):
    def __init__(self):
        a_name = M.Char("a")
        a = M.Pair(M.VarTag, M.Pair(a_name, M.EmptyList))
        seq = M.Pair(SqrtSeqTermLabel, M.Pair(a, M.EmptyList))
        sqrt_a = M.Pair(SqrtLabel, M.Pair(a, M.EmptyList))
        pattern = M.Pair(RealNumLabel, M.Pair(seq, M.EmptyList))
        replacement = M.Pair(IsRealLabel, M.Pair(sqrt_a, M.EmptyList))
        super().__init__(pattern, replacement)


def install_default_theorem_rules(graph):
    graph.add_rule(SqrtUnfoldRule())
    graph.add_rule(SqrtSeqToNewtonStepRule())
    graph.add_rule(NewtonPositiveRule())
    graph.add_rule(NewtonErrorIdentityRule())
    graph.add_rule(NewtonErrorShrinksRule())
    graph.add_rule(NewtonShrinksToCauchyRule())
    graph.add_rule(SqrtSeqCauchyToIsCauchyRule())
    graph.add_rule(CauchyToRealNumRule())
    graph.add_rule(RealNumSqrtSeqToIsRealSqrtRule())
    return graph


def build_default_theorem_rule_chain(graph):
    return Reverse(M.FromContextGetRuleOrder(graph)())()


__all__ = [name for name in globals() if not name.startswith("_")]
