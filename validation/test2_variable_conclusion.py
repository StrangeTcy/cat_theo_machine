# ============================================================
# TEST 2: Generic Variable-Only Conclusion Case
# ============================================================
import sys, os, time

IMPORT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if IMPORT_ROOT not in sys.path:
    sys.path.insert(0, IMPORT_ROOT)

from hyge import machine as M
from hyge import proof as P
from hyge import labels as L
from hyge import planner as Planner
from hyge.runtime import make_fresh_runtime

t0 = time.time()
print("=== TEST 2: Variable-Only Conclusion Case ===")
print()

print("[1] Creating fresh runtime...")
runtime = make_fresh_runtime()
graph = runtime.graph
registry = M.FromContextGetConstructors(graph)()
print("    Runtime OK.")
print()

print("[2] Building variable-only conclusion rule...")
var_id = M.Pair(M.Zero, M.EmptyList)
var_x = M.Pair(M.VarTag, M.Pair(var_id, M.EmptyList))
print(f"    Var pattern IsVarPattern: {P.IsVarPattern(var_x)() is M.truth_value}")

premise_concrete = M.Pair(L.ZeroLabel, M.EmptyList)
var_conclusion_rule = P.Rule(premise_concrete, var_x)
rule_list = M.Pair(var_conclusion_rule, M.EmptyList)

replacement = P.RuleReplacement(var_conclusion_rule)()
print(f"    Rule replacement IsVarPattern: {P.IsVarPattern(replacement)() is M.truth_value}")
print()

print("[3] Building PlannerProblem...")
goal = M.Pair(L.ZeroLabel, M.EmptyList)
start_state = M.Pair(M.Pair(L.ZeroLabel, M.EmptyList), M.EmptyList)
heuristic = runtime.theorem_heuristic

problem = Planner.PlannerProblem(start_state, goal, rule_list, heuristic)()
state = Planner.PlannerState(problem, registry)()
print("    Problem and State created.")
print()

sf = M.Tail(state)()
obl = M.Head(sf)()
root = M.Head(obl)()
rf = M.Tail(root)()
rf2 = M.Tail(rf)()
rf3 = M.Tail(rf2)()
root_status_before = M.Head(M.Tail(rf3)())()
print(f"[4] Root status BEFORE run: {root_status_before}")
print()

print("[5] Running PlannerRun (step_budget=1)...")
t_run_start = time.time()
final_state = None
error_msg = None
elapsed = 0.0
try:
    final_state = Planner.PlannerRun(graph, state, M.one)()
    elapsed = time.time() - t_run_start
    print(f"    PlannerRun completed in {elapsed:.3f}s")
except Exception as e:
    elapsed = time.time() - t_run_start
    error_msg = "".join(traceback.format_exception_only(e)).strip()
    print(f"    ERROR: {error_msg}")
    traceback.print_exc()

if final_state is not None:
    ff = M.Tail(final_state)()
    fobl = M.Head(ff)()
    froot = M.Head(fobl)()
    frf = M.Tail(froot)()
    frf2 = M.Tail(frf)()
    frf3 = M.Tail(frf2)()
    fstatus = M.Head(M.Tail(frf3)())()

    obl_count = 0
    cur = fobl
    while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
        obl_count += 1
        cur = M.Tail(cur)()

    print()
    print("=== TEST 2 RESULTS ===")
    print(f"  Root final status:    {fstatus}")
    proved = M.IdentityCompare(fstatus, L.ProvedLabel)()
    failed = M.IdentityCompare(fstatus, L.FailedLabel)()
    pending = M.IdentityCompare(fstatus, L.PendingLabel)()
    print(f"  Is Proved:  {proved is M.truth_value}")
    print(f"  Is Failed:  {failed is M.truth_value}")
    print(f"  Is Pending: {pending is M.truth_value}")
    print(f"  Obligation count: {obl_count}")
    if obl_count > 100:
        print(f"  WARNING: Excessive obligation count - possible recursion!")
    else:
        print(f"  OK: Obligation count within bounds.")
    print(f"  Run time: {elapsed:.3f}s")
else:
    print()
    print("=== TEST 2 RESULTS ===")
    print(f"  STATUS: FAILED - PlannerRun raised exception")
    print(f"  Error: {error_msg}")

print(f"  Total time: {time.time() - t0:.3f}s")
print()
print("=== TEST 2 COMPLETE ===")
