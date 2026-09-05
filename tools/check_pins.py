"""Recompute the shard-cursor pins without booting the machine.

`TestShardCursorPinTest` walks `testsuite.py` at run time and compares three
numbers against constants in its own class. This recomputes the same walk from
the same source, so the pins can be checked in a second instead of a suite
run -- which is what makes it useful as the last step of `tools/recover.sh`:
after a reset it proves the tree is the tree, without paying for a boot.

The walk is reproduced exactly, including the part that looks like a bug. The
string it starts from occurs first inside the pin test's own source, so the
body it walks begins at that line and the first mention of the pinned test
name is the test's own `if pinned < 0 ...` line. There the cursor is still 0,
so `pinned` is set to -1 and stays "unset"; the next mention is the real
registration. Changing either detail moves the number without anything being
wrong, which is the reason this file copies the walk rather than re-deriving
it.

Two remediations, and the output says which one applies:

    cursor-pin-moved    the index or shard moved. A registration landed
                        before the pinned test, which is the partition rule
                        breaking. An integrator re-baselines the suite.
    guard-count-stale   only the guard count moved. Someone added a test,
                        which is intended; the commit that added it updates
                        EXPECTED_GUARD_COUNT in the same commit.

Usage:  python3 tools/check_pins.py     (exit 0 = pins hold)
"""

from __future__ import annotations

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TESTSUITE = os.path.join(os.path.dirname(HERE), "testsuite.py")

GUARD = "Gmod.TestShardAccept(graph)() is M.truth_value"
PINNED_NAME = "learned_memory_checkpoint_test"


def derive(source):
    """The walk TestShardCursorPinTest performs, copied verbatim."""

    start = source.index("def install_default_tests(graph):")
    body = source[start:]
    cursor = 0
    pinned = -1
    for line in body.split("\n"):
        if GUARD in line:
            cursor = cursor + 1
        if pinned < 0 and PINNED_NAME in line:
            pinned = cursor - 1
    shard = 0
    if pinned >= 0:
        shard = pinned % 2
    return cursor, pinned, shard


def expected(source):
    """The three constants, read from the class that owns them."""

    constants = {}
    for name in ("EXPECTED_GUARD_COUNT", "EXPECTED_CURSOR_INDEX", "EXPECTED_SHARD"):
        match = re.search(r"^\s*%s = (\d+)\s*$" % name, source, re.MULTILINE)
        if match is None:
            return None
        constants[name] = int(match.group(1))
    return constants


def main():
    with open(TESTSUITE, "r", encoding="utf-8") as handle:
        source = handle.read()

    constants = expected(source)
    if constants is None:
        print("could not read the pin constants from testsuite.py")
        return 1

    guard_count, pinned_index, pinned_shard = derive(source)
    want_guards = constants["EXPECTED_GUARD_COUNT"]
    want_index = constants["EXPECTED_CURSOR_INDEX"]
    want_shard = constants["EXPECTED_SHARD"]

    print("guards: %d pin: %d" % (guard_count, want_guards))
    print("index:  %d pin: %d" % (pinned_index, want_index))
    print("shard:  %d pin: %d" % (pinned_shard, want_shard))

    if pinned_index != want_index or pinned_shard != want_shard:
        print("RESULT: cursor-pin-moved  <- hard: the partition rule moved. "
              "An integrator re-baselines the suite; do not bump the number.")
        return 1
    if guard_count != want_guards:
        print("RESULT: guard-count-stale  <- soft: a test was added. Update "
              "EXPECTED_GUARD_COUNT to %d in the same commit." % guard_count)
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
