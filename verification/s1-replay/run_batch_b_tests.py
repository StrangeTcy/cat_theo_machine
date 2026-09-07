#!/usr/bin/env python3
"""Batch-B named-test invocation: 7 batch-A checks + 2 canonical S1 checks.

Run against a checkout that already has batch A (six-phase loop port) and
batch B (canonical S1 = 897c07c, adapted) applied, with the checkout
importable as the `cat_theo_machine` package.

Usage (from the checkout root's parent, so `cat_theo_machine` resolves):

    cd /path/to          # parent of the cat_theo_machine checkout
    python3 cat_theo_machine/verification/s1-replay/run_batch_b_tests.py

The script inserts the checkout root's parent onto sys.path.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))  # checkout root (named cat_theo_machine)
sys.path.insert(0, os.path.dirname(ROOT))      # its parent, for `import cat_theo_machine`

from cat_theo_machine.runtime import boot_from_packs
from cat_theo_machine.main import PACK_PATHS, _runtime_namespace
import cat_theo_machine.machine as M
from cat_theo_machine import testsuite as TS


def main():
    runtime, packs = boot_from_packs(PACK_PATHS, _runtime_namespace())
    graph = runtime.graph
    graph._search_disable_console = M.truth_value

    def run(name, cls):
        try:
            inst = cls(graph)
            val = inst()
            return "PASS" if val is M.truth_value else "NON-TRUTH (%s)" % getattr(val, "__name__", val)
        except Exception as exc:
            return "ERROR %s: %s" % (type(exc).__name__, exc)

    tests = [
        ("label_registration_completeness_test", TS.LabelRegistrationCompletenessTest),
        ("test_shard_cursor_pin_test", TS.TestShardCursorPinTest),
        ("relation_contract_record_inserts_and_ablates_test", TS.RelationContractRecordInsertsAndAblatesTest),
        ("relation_contract_never_variable_test", TS.RelationContractNeverVariableTest),
        ("self_improvement_trace_mining_test", TS.SelfImprovementTraceMiningTest),
        ("self_improvement_rent_gate_test", TS.SelfImprovementRentGateTest),
        ("self_improvement_recursive_turn_test", TS.SelfImprovementRecursiveTurnTest),
        ("invariant_conjecture_test", TS.InvariantConjectureTest),
        ("self_improvement_memory_cycle_test", TS.SelfImprovementMemoryCycleTest),
    ]
    for name, cls in tests:
        print("%s: %s" % (name, run(name, cls)))


if __name__ == "__main__":
    main()
