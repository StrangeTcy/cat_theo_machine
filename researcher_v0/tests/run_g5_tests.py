"""Run the Researcher-v0 G5 executable acceptance tests."""

from __future__ import annotations

import sys

from ... import machine as M
from .. import token_domain as D
from ..chains import IsEmptyTerm
from .test_g5_use import G5Tests


class TestRunResult(M.Edge):
    def __init__(self, tests):
        self.result = self._walk(tests, D.PeanoZero()(), D.PeanoZero()())
        super().__init__(inputs=M.Pair(tests, M.EmptyList), results=self.result)

    def _walk(self, tests, passed, failed):
        if IsEmptyTerm(tests)() is M.truth_value:
            return M.Pair(passed, M.Pair(failed, M.EmptyList))
        entry = M.Head(tests)()
        name = M.Head(entry)()()
        test = M.Tail(entry)()
        result = test()
        if M.Compare(result, M.truth_value)() is M.truth_value:
            print("PASS  " + name)
            passed = D.PeanoSucc(passed)()
        else:
            print("FAIL  " + name)
            failed = D.PeanoSucc(failed)()
        return self._walk(M.Tail(tests)(), passed, failed)

    def __call__(self):
        return self.result


if M.Compare(M.Char(__name__), M.Char("__main__"))() is M.truth_value:
    result = TestRunResult(G5Tests()())()
    passed = D.HeadAt(result, 0)()
    failed = D.HeadAt(result, 1)()
    print("")
    print(
        "passed: "
        + str(D.StructuralCount(passed)())
        + "  failed: "
        + str(D.StructuralCount(failed)())
    )
    if M.Compare(failed, D.PeanoZero()())() is M.truth_value:
        sys.exit(0)
    sys.exit(1)
