from __future__ import annotations

from . import machine as M
from . import binder as B


class ToyGoal(M.Edge):
    def __init__(self):
        var_n = B.BinderVar("n")()
        body = B.ImpliesTerm(
            B.GreaterTerm(var_n, M.Char("1"))(),
            B.EqTerm(B.PlusTerm(var_n, M.Char("0"))(), var_n)(),
        )()
        self.result = B.ForallTerm(var_n, body)()
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class ToyCertificate(M.Edge):
    def __init__(self):
        self.leaf_flag = M.false_value
        self.implies_flag = M.false_value
        self.forall_flag = M.false_value
        self.toy_goal = ToyGoal()()
        var_n = B.BinderVar("n")()
        fresh = B.BinderVar("nf")()
        body = B.ImpliesTerm(
            B.GreaterTerm(var_n, M.Char("1"))(),
            B.EqTerm(B.PlusTerm(var_n, M.Char("0"))(), var_n)(),
        )()
        hypothesis = B.GreaterTerm(fresh, M.Char("1"))()
        consequent = B.EqTerm(B.PlusTerm(fresh, M.Char("0"))(), fresh)()
        self.toy_globals = M.EmptyList
        self.toy_trusted = M.Pair(consequent, M.EmptyList)
        self.toy_branch = M.Char("b0")
        outer_scope = M.EmptyList
        inner_scope = M.Pair(B.ScopeEntry("s0", hypothesis)(), M.EmptyList)
        leaf_pair = B.TrustedTheorem(consequent, inner_scope, self.toy_branch, self.toy_globals, self.toy_trusted)()
        self.leaf_flag = M.Head(leaf_pair)()
        if self.leaf_flag is M.false_value:
            self.result = M.Pair(M.false_value, M.EmptyList)
        else:
            leaf_cert = M.Tail(leaf_pair)()
            implies_pair = B.ImpliesIntroduction(
                hypothesis, leaf_cert, outer_scope, self.toy_branch, self.toy_globals, self.toy_trusted
            )()
            self.implies_flag = M.Head(implies_pair)()
            if self.implies_flag is M.false_value:
                self.result = M.Pair(M.false_value, M.EmptyList)
            else:
                implies_cert = M.Tail(implies_pair)()
                evidence = B.FreshnessEvidence(var_n, outer_scope)()
                self.result = B.ForallIntroduction(
                    var_n,
                    body,
                    fresh,
                    evidence,
                    implies_cert,
                    outer_scope,
                    self.toy_branch,
                    self.toy_globals,
                    self.toy_trusted,
                )()
                self.forall_flag = M.Head(self.result)()
        if self.leaf_flag is M.truth_value and M.Head(self.result)() is M.truth_value:
            self.toy_cert = M.Tail(self.result)()
        else:
            self.toy_cert = M.EmptyList
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class ToyCorrupted(M.Edge):
    def __init__(self, variant):
        self.result = self._corrupt(variant)
        super().__init__(inputs=M.EmptyList, results=self.result)

    def _corrupt(self, variant):
        toy_pair = ToyCertificate()()
        if M.Head(toy_pair)() is M.false_value:
            return M.EmptyList
        cert = M.Tail(toy_pair)()
        if variant == 0:
            return B.ReplaceCertField(cert, 7, B.FalseTerm()())()
        if variant == 1:
            return B.ReplaceCertField(cert, 2, B.BinderVar("zz")())()
        if variant == 2:
            var_n = B.BinderVar("n")()
            extra = B.GreaterTerm(M.Char("q"), M.Char("0"))()
            checked = M.Pair(B.ScopeEntry("sx", extra)(), M.EmptyList)
            return B.ReplaceCertField(cert, 3, B.FreshnessEvidence(var_n, checked)())()
        return M.EmptyList

    def __call__(self):
        return self.result


__all__ = (
    "ToyGoal",
    "ToyCertificate",
    "ToyCorrupted",
)
