"""Runner for the Researcher-v0 G2 tests.

    python3 -m cat_theo_machine.researcher_v0.tests.run_g2_tests

Run it from the directory that contains the repository (`/home/user`), the
same place the repository's own import probes run from, so that
`cat_theo_machine` is importable as a package.

The runner has two phases, in this order:

1. generation — build the task set, drop exact duplicates with the drop
   recorded, and write `researcher_v0/tasks/tasks.jsonl`. The summary counts
   (generated / dropped / delivered / canonical / collapse groups) are host
   reporting values printed here;
2. tests — run the G2 test chain. Exit status is 0 when every test returns
   truth and 1 otherwise; the failing names are printed.

No task is run, nothing is mined, proved or pruned, and no outcome is issued.
"""

from __future__ import annotations

import os
import sys

from ... import machine as M
from .. import task_generation as G
from .test_g2_tasks import G2Tests


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    package = os.path.dirname(here)
    tasks_dir = os.path.join(package, "tasks")
    os.makedirs(tasks_dir, exist_ok=True)

    generated = G.GenerateAllRows()()
    split = G.DropExactDuplicates(generated)()
    kept = M.Head(split)()
    drops = M.Head(M.Tail(split)())()
    G.WriteTasksFile(
        os.path.join(tasks_dir, "tasks.jsonl"), G.RowsToJsonl(kept)()
    )()
    print("G2 generation summary (host reporting values):")
    print("  generated rows : " + str(G.CountRows(generated)()))
    print("  dropped        : " + str(G.CountRows(drops)()))
    print("  delivered rows : " + str(G.CountRows(kept)()))
    print("  canonical      : " + str(G.CountDistinctCanonical(kept)()))
    print("  collapse groups: " + str(G.CountCollapseGroups(kept)()))
    print("")

    passed = 0
    failed = 0
    remaining = G2Tests()()
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
