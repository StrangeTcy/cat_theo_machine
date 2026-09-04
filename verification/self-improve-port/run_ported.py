import sys
sys.path.insert(0, '/tmp')
from cat_theo_machine.runtime import boot_from_packs
from cat_theo_machine.main import PACK_PATHS, _runtime_namespace
import cat_theo_machine.machine as M
from cat_theo_machine import testsuite as TS

runtime, packs = boot_from_packs(PACK_PATHS, _runtime_namespace())
graph = runtime.graph
graph._search_disable_console = M.truth_value

results = {}

for name, cls in [("label_registration_completeness_test", TS.LabelRegistrationCompletenessTest),
                  ("test_shard_cursor_pin_test", TS.TestShardCursorPinTest),
                  ("self_improvement_trace_mining_test", TS.SelfImprovementTraceMiningTest),
                  ("self_improvement_rent_gate_test", TS.SelfImprovementRentGateTest),
                  ("self_improvement_recursive_turn_test", TS.SelfImprovementRecursiveTurnTest),
                  ("invariant_conjecture_test", TS.InvariantConjectureTest),
                  ("self_improvement_memory_cycle_test", TS.SelfImprovementMemoryCycleTest)]:
    inst = cls(graph)
    val = inst()
    results[name] = "PASS" if val is M.truth_value else "FAIL"

for k, v in results.items():
    print(f"{k}: {v}")
