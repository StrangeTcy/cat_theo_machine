# ============================================================
# Gate B — Native Persistence & Cold Resume Verification Suite
# Verifies full snapshot round trip, cold resume, and integrity
# across characters, rules, planner states, derivation receipts,
# graph tasks, promotion ledgers, and surface language bridges.
# ============================================================
import json
import os
import sys
import tempfile
import time

IMPORT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARENT_ROOT = os.path.dirname(IMPORT_ROOT)
if PARENT_ROOT not in sys.path:
    sys.path.insert(0, PARENT_ROOT)
if IMPORT_ROOT not in sys.path:
    sys.path.insert(0, IMPORT_ROOT)

from cat_theo_machine import checker_b as CB
from cat_theo_machine import constructors as C
from cat_theo_machine import curriculum as Curr
from cat_theo_machine import graph as G
from cat_theo_machine import graph_task as GT
from cat_theo_machine import labels as L
from cat_theo_machine import machine as M
from cat_theo_machine import persistence as Persist
from cat_theo_machine import planner as Planner
from cat_theo_machine import proof as P
from cat_theo_machine import promotion_ledger as PL
from cat_theo_machine import surface_bridge as SB


def run_all_tests():
    t0 = time.time()
    print("=== TEST 12: Gate B — Native Persistence & Cold Resume ===")
    print()

    passed = 0
    total = 7

    runtime = Persist.make_fresh_runtime() if hasattr(Persist, "make_fresh_runtime") else None
    if runtime is None:
        from cat_theo_machine.runtime import make_fresh_runtime
        runtime = make_fresh_runtime()

    graph = runtime.graph
    registry = M.FromContextGetConstructors(graph)()
    namespace = Persist._runtime_namespace_for_restore()
    codec = Persist.SnapshotCodec(namespace)

    # ------------------------------------------------------------
    # Probe 1: Non-singleton Character Atom and Label Preservation
    # ------------------------------------------------------------
    print("[Probe 1] Non-singleton Character Atom & Label Round-Trip")
    char_a = M.Char("alpha")
    char_b = M.Char("beta_42")
    custom_lbl = L.TaoProblem11AreaValueLabel

    probe1_term = M.Pair(char_a, M.Pair(char_b, M.Pair(custom_lbl, M.EmptyList)))
    snap1 = codec.capture_objects({"probe1_term": probe1_term})
    state1 = codec.load_snapshot(snap1)
    loaded1 = state1.roots["probe1_term"]

    # Verify structural equality and symbol preservation
    restored_char_a = M.Head(loaded1)()
    restored_char_b = M.Head(M.Tail(loaded1)())()
    restored_lbl = M.Head(M.Tail(M.Tail(loaded1)())())()

    eq_a = restored_char_a.symbol == "alpha"
    eq_b = restored_char_b.symbol == "beta_42"
    eq_lbl = M.IdentityCompare(restored_lbl, L.TaoProblem11AreaValueLabel)() is M.truth_value

    if eq_a and eq_b and eq_lbl:
        print("  [PASS] Character atoms and labels preserved exactly.")
        passed += 1
    else:
        print(f"  [FAIL] Probe 1 failed: eq_a={eq_a}, eq_b={eq_b}, eq_lbl={eq_lbl}")

    # ------------------------------------------------------------
    # Probe 2: Canonical Snapshot Ingestion & Rule Set Validation
    # ------------------------------------------------------------
    print()
    print("[Probe 2] Fresh Snapshot File Cold Load & Rule Integrity")
    current_snap_path = os.path.join(IMPORT_ROOT, "snapshots", "hyge_snapshot_current.json")
    if os.path.exists(current_snap_path):
        with open(current_snap_path, "r", encoding="utf-8") as f:
            snap2_data = json.load(f)
        state2 = codec.load_snapshot(snap2_data)
        rule_order = state2.roots["rule_order"]
        ctor_reg = state2.roots["constructor_registry"]
        has_rules = M.IdentityCompare(rule_order, M.EmptyList)() is M.false_value
        has_reg = M.IdentityCompare(ctor_reg, M.EmptyList)() is M.false_value
        if has_rules and has_reg:
            print("  [PASS] Fresh snapshot cold load succeeded with complete rules and registry.")
            passed += 1
        else:
            print(f"  [FAIL] Probe 2 failed: has_rules={has_rules}, has_reg={has_reg}")
    else:
        print(f"  [FAIL] Snapshot file not found at {current_snap_path}")

    # ------------------------------------------------------------
    # Probe 3: Paused Planner State Cold Resume
    # ------------------------------------------------------------
    print()
    print("[Probe 3] Paused Planner State Round-Trip and Cold Resume")
    p_goal = M.Pair(L.ZeroLabel, M.EmptyList)
    p_heuristic = P.DefaultAnchorPreferenceHeuristic()
    p_problem = Planner.PlannerProblem(M.EmptyList, p_goal, M.EmptyList, p_heuristic)()
    p_state = Planner.PlannerState(p_problem, registry)()

    snap3 = codec.capture_objects({"planner_state": p_state})
    state3 = codec.load_snapshot(snap3)
    loaded_planner_state = state3.roots["planner_state"]

    loaded_problems = M.Head(loaded_planner_state)()
    loaded_obligations = M.Head(M.Tail(loaded_planner_state)())()
    has_obligations = M.IdentityCompare(loaded_obligations, M.EmptyList)() is M.false_value

    if has_obligations:
        print("  [PASS] Paused planner state restored and obligations preserved.")
        passed += 1
    else:
        print(f"  [FAIL] Probe 3 failed: obligations was EmptyList")

    # ------------------------------------------------------------
    # Probe 4: Independent Checker B Derivation Verification after Restore
    # ------------------------------------------------------------
    print()
    print("[Probe 4] Proof Derivation Receipt Verification Across Snapshot")
    atom_a = M.Atom()
    atom_b = M.Atom()
    term_a = M.Pair(atom_a, M.EmptyList)
    term_b = M.Pair(atom_b, M.EmptyList)

    rule_1 = P.Rule(term_a, term_b)()
    trusted_rules = M.Pair(rule_1, M.EmptyList)

    action_1 = P.RewriteAction(rule_1, M.EmptyList)()
    step_1_res = P.Step(term_a, action_1, term_b, registry)()
    step_1 = M.Head(step_1_res)()
    registry = M.Head(M.Tail(step_1_res)())()

    valid_steps = M.Pair(step_1, M.EmptyList)
    cost_zero = P.ProofCost(M.Zero, M.Zero, M.Zero, M.Zero)()
    der_res = P.Derivation(valid_steps, cost_zero, registry)()
    valid_derivation = M.Head(der_res)()
    registry = M.Head(M.Tail(der_res)())()

    snap4 = codec.capture_objects({"derivation": valid_derivation, "rules": trusted_rules, "term_a": term_a, "term_b": term_b})
    state4 = codec.load_snapshot(snap4)
    loaded_derivation = state4.roots["derivation"]
    loaded_rules = state4.roots["rules"]
    loaded_term_a = state4.roots["term_a"]
    loaded_term_b = state4.roots["term_b"]

    verify_check = CB.VerifyDerivation(loaded_derivation, loaded_term_a, loaded_term_b, loaded_rules, registry)()
    verify_status = M.Head(verify_check)()
    is_receipt_ok = M.IdentityCompare(verify_status, L.DerivationVerifiedLabel)() is M.truth_value

    if is_receipt_ok:
        print("  [PASS] Derivation restored and verified by Independent Checker B.")
        passed += 1
    else:
        print(f"  [FAIL] Probe 4 failed: derivation verification gave {verify_status}")

    # ------------------------------------------------------------
    # Probe 5: Canonical Graph Task Ingestion & Execution from Restored Graph
    # ------------------------------------------------------------
    print()
    print("[Probe 5] Canonical Graph Task Ingestion & Execution from Restored Graph")
    edge_e = M.Atom()
    node_a = M.Atom()
    node_b = M.Atom()
    var_x = M.Var()
    gt_task_pair = Curr.BuildRung1RetrievalTask(
        M.Atom(), edge_e, node_a, node_b, var_x, registry
    )()

    snap5 = codec.capture_objects({"task": gt_task_pair})
    state5 = codec.load_snapshot(snap5)
    loaded_task_pair = state5.roots["task"]

    exec_result = GT.ExecuteGraphQuery(loaded_task_pair, registry)()
    exec_status = M.Head(exec_result)()
    is_gt_ok = M.IdentityCompare(exec_status, L.TaskSuccessLabel)() is M.truth_value

    if is_gt_ok:
        print("  [PASS] Canonical graph task restored and executed in graph space.")
        passed += 1
    else:
        print(f"  [FAIL] Probe 5 failed: query status was {exec_status}")

    # ------------------------------------------------------------
    # Probe 6: Autonomous Promotion Ledger Round-Trip
    # ------------------------------------------------------------
    print()
    print("[Probe 6] Promotion Ledger Round-Trip & Version Monotonicity")
    base_ledger = PL.EmptyPromotionLedger(registry)()
    one_res = M.Succ(M.Zero, registry)()
    one_val = M.Head(one_res)()

    c_receipt = M.Pair(L.ProofReceiptLabel, M.Pair(term_a, M.Pair(term_b, M.Pair(valid_steps, M.Pair(cost_zero, M.EmptyList)))))
    entry1 = PL.LedgerEntry(
        M.Atom(),
        L.ProofSchemaPromotionLabel,
        M.Atom(),
        c_receipt,
        M.Atom(),
        one_val,
        L.PromotionActiveLabel,
    )()
    ledger_with_entry = M.Pair(
        L.PromotionLedgerLabel,
        M.Pair(
            M.Pair(entry1, M.EmptyList),
            M.Pair(M.EmptyList, M.Pair(one_val, M.EmptyList)),
        ),
    )

    snap6 = codec.capture_objects({"ledger": ledger_with_entry})
    state6 = codec.load_snapshot(snap6)
    loaded_ledger = state6.roots["ledger"]

    active_query = PL.QueryActivePromotions(loaded_ledger, L.ProofSchemaPromotionLabel, registry)()
    has_active = M.IdentityCompare(active_query, M.EmptyList)() is M.false_value

    if has_active:
        print("  [PASS] Promotion ledger restored and active promotions queried.")
        passed += 1
    else:
        print("  [FAIL] Probe 6 failed: no active promotions found in restored ledger.")

    # ------------------------------------------------------------
    # Probe 7: Reversible Surface Language Bridge Round-Trip
    # ------------------------------------------------------------
    print()
    print("[Probe 7] Reversible Surface Language Grammar & Statement Round-Trip")
    sb_token = SB.SurfaceToken(M.Char("triangle"))()
    sb_statement = SB.SurfaceStatement(M.Pair(sb_token, M.EmptyList))()

    snap7 = codec.capture_objects({"stmt": sb_statement})
    state7 = codec.load_snapshot(snap7)
    loaded_stmt = state7.roots["stmt"]

    loaded_tokens = M.Head(M.Tail(loaded_stmt)())()
    loaded_tok = M.Head(loaded_tokens)()
    tok_val = M.Head(M.Tail(loaded_tok)())()
    is_tok_match = tok_val.symbol == "triangle"

    if is_tok_match:
        print("  [PASS] Surface language statement and tokens restored reversibly.")
        passed += 1
    else:
        print(f"  [FAIL] Probe 7 failed: token symbol mismatch ({tok_val})")

    # ------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------
    print()
    print(f"=== TEST 12 COMPLETE: {passed}/{total} Probes Passed in {time.time() - t0:.2f}s ===")
    if passed == total:
        print("STATUS: ALL PROBES PASSED (Gate B Verified)")
        return 0
    else:
        print(f"STATUS: FAILED ({total - passed} probes failed)")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
