"""Runner for the Researcher-v0 G1 tests.

    python3 -m cat_theo_machine.researcher_v0.tests.run_g1_tests

Run it from the directory that contains the repository (`/home/user`), the
same place the repository's own import probes run from, so that
`cat_theo_machine` is importable as a package. Exit status is 0 when every
test returns truth and 1 otherwise; the failing names are printed.
"""

from __future__ import annotations

import sys

from ... import machine as M
from .test_g1_domain import G1Tests


if __name__ == "__main__":
    passed = 0
    failed = 0
    remaining = G1Tests()()
    while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
        entry = M.Head(remaining)()
        name = M.Head(entry)()()
        # name and result are text atoms; compare them through Compare, not `is`.
        test = M.Tail(entry)()
        result = test()()
        if M.Compare(result, M.truth_value)() is M.truth_value:
            passed = passed + 1
            print("PASS  " + name)
        else:
            failed = failed + 1
            print("FAIL  " + name)
        remaining = M.Tail(remaining)()
    print("")
    print("passed: " + str(passed) + "  failed: " + str(failed))
    if failed == 0:
        sys.exit(0)
    sys.exit(1)
