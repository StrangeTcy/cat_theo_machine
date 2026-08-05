from __future__ import annotations

from . import machine as M
from . import proof as P


class Rewrite(M.Edge):
    def __init__(self, rule, target, registry):
        self.rule = rule
        self.target = target
        self.registry = registry
        result_atom = self._rewrite(rule, target)
        self.result = M.Pair(result_atom, M.EmptyList)
        super().__init__(
            inputs=M.Pair(rule, M.Pair(target, M.Pair(registry, M.EmptyList))),
            results=self.result,
        )

    def _rewrite(self, rule, target):
        pattern = P.RulePattern(rule)()
        replacement = P.RuleReplacement(rule)()
        match = M.Match(pattern, target)()

        flag = M.Head(match)()
        binds = M.Tail(match)()
        if M.IdentityCompare(flag, M.truth_value)() is M.truth_value:
            inst = M.Instantiate(replacement, binds)()
            return M.Head(inst)()

        if M.IsPair(target)() is M.truth_value:
            new_h = self._rewrite(rule, M.Head(target)())
            new_t = self._rewrite(rule, M.Tail(target)())
            return M.Pair(new_h, new_t)

        return target

    def __call__(self):
        return self.result


class TermEqual(M.Edge):
    def __init__(self, x, y):
        self.result = self._eq(x, y)
        super().__init__(inputs=M.Pair(x, M.Pair(y, M.EmptyList)), results=self.result)

    def _eq(self, x, y):
        stack = M.Pair(M.Pair(x, y), M.EmptyList)
        while M.IdentityCompare(stack, M.EmptyList)() is M.false_value:
            top = M.Head(stack)()
            stack = M.Tail(stack)()
            left = M.Head(top)()
            right = M.Tail(top)()

            if M.IdentityCompare(left, right)() is M.truth_value:
                continue

            x_is_pair = M.IsPair(left)()
            y_is_pair = M.IsPair(right)()
            if M.AndAtom(x_is_pair, y_is_pair)() is M.truth_value:
                stack = M.Pair(M.Pair(M.Head(left)(), M.Head(right)()), stack)
                stack = M.Pair(M.Pair(M.Tail(left)(), M.Tail(right)()), stack)
                continue

            if M.OrAtom(x_is_pair, y_is_pair)() is M.truth_value:
                return M.false_value

            cx = M.GetConstructor(left)()
            cy = M.GetConstructor(right)()
            cx_empty = M.IdentityCompare(cx, M.EmptyList)()
            cy_empty = M.IdentityCompare(cy, M.EmptyList)()
            if M.AndAtom(cx_empty, cy_empty)() is M.truth_value:
                return M.false_value
            if M.OrAtom(cx_empty, cy_empty)() is M.truth_value:
                return M.false_value

            lx = M.Head(cx)()
            ly = M.Head(cy)()
            if M.IdentityCompare(lx, ly)() is M.false_value:
                return M.false_value
            stack = M.Pair(M.Pair(M.Tail(cx)(), M.Tail(cy)()), stack)
        return M.truth_value

    def __call__(self):
        return self.result


FindBinding = M.FindBinding
MergeBindings = M.MergeBindings
Match = M.Match
Instantiate = M.Instantiate
IsPair = M.IsPair
IsEdge = M.IsEdge
IsAtom = M.IsAtom
ContainsVar = P.ContainsVar
IsVarPattern = P.IsVarPattern
TermHead = P.TermHead
RulePattern = P.RulePattern
RuleReplacement = P.RuleReplacement

__all__ = [name for name in globals() if not name.startswith("_")]
