#!/usr/bin/env python3
"""Resolve one cherry-pick conflict: place registrations in the [S] block (class form).

Reads testsuite.py in the rehearsal worktree, finds the single conflict hunk
(<<<<<<< HEAD ... ======= ... >>>>>>>), keeps the HEAD (r1) side, and inserts
the given registration lines immediately before the '# --- end [S] ---'
marker, in class form (the r1 `_register_test` takes the class, not an
instance).
"""
import os
import sys

BASE = os.environ.get("REHEARSE_BASE", "/tmp/cat_theo_machine")
PATH = os.path.join(BASE, "testsuite.py")

REGS = {
    "trace": """    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "self_improvement_trace_mining_test",
            empty,
            SelfImprovementTraceMiningTest,
            M.truth_value,
        )
""",
    "rent": """    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "self_improvement_rent_gate_test",
            empty,
            SelfImprovementRentGateTest,
            M.truth_value,
        )
""",
    "recursive": """    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "self_improvement_recursive_turn_test",
            empty,
            SelfImprovementRecursiveTurnTest,
            M.truth_value,
        )
""",
    "invariant": """    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "invariant_conjecture_test",
            empty,
            InvariantConjectureTest,
            M.truth_value,
        )
""",
    "memory": """    if Gmod.TestShardAccept(graph)() is M.truth_value:
        _register_test(
            graph,
            "self_improvement_memory_cycle_test",
            empty,
            SelfImprovementMemoryCycleTest,
            M.truth_value,
        )
""",
}


def main(name):
    with open(PATH) as f:
        text = f.read()

    start = text.index("<<<<<<< HEAD\n")
    mid = text.index("\n=======\n", start)
    end = text.index("\n>>>>>>> ", mid)
    end_of_marker = text.index("\n", end + 1)

    head_side = text[start + len("<<<<<<< HEAD\n") : mid + 1]
    tail = text[end_of_marker + 1 :]

    marker = "    # --- end [S] ---\n"
    assert marker in head_side, "'# --- end [S] ---' not found in HEAD side"
    head_side = head_side.replace(marker, REGS[name] + marker, 1)

    out = text[:start] + head_side + tail
    with open(PATH, "w") as f:
        f.write(out)
    print(f"resolved {name}: removed {text.count('<<<<<<<')} conflict hunk(s)")


if __name__ == "__main__":
    main(sys.argv[1])
