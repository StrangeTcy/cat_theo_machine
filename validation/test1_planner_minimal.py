# ============================================================
# TEST 1: Minimal Planner Lifecycle — Single Rule(start, goal)
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
print("=== TEST 1: Minimal Planner Lifecycle ===")
print()

print("[1] Creating fresh runtime...")
runtime = make_fresh_runtime()
graph = runtime.graph
registry = M.FromContextGetConstructors(graph)()
print("    Runtime OK.")
print()

print("[2] Building concrete rule (ZeroLabel premise -> ZeroLabel conclusion)...")
premise_atom = M.Pair(L.ZeroLabel, M.EmptyList)
conclusion_atom = M.Pair(L.ZeroLabel, M.EmptyList)
identity_rule = P.Rule(premise_atom, conclusion_atom)
print("    Rule created.")
print()

print("[3] Building PlannerProblem...")
start_state = M.Pair(premise_atom, M.EmptyList)
goal = conclusion_atom
rules_list = M.Pair(identity_rule, M.EmptyList)
heuristic = runtime.theorem_heuristic
problem = Planner.PlannerProblem(start_state, goal, rules_list, heuristic)()
print("    Problem created.")
print()

print("[4] Building PlannerState...")
state = Planner.PlannerState(problem, registry)()
print("    PlannerState created.")

state_fields = M.Tail(state)()
obligations = M.Head(state_fields)()
root = M.Head(obligations)()
root_fields = M.Tail(root)()
root_id = M.Head(root_fields)()
rf2 = M.Tail(root_fields)()
rf3 = M.Tail(rf2)()
root_status_before = M.Head(M.Tail(rf3)())()
print(f"    Root obligation id={root_id}, status BEFORE run={root_status_before}")
print()

print("[5] Running PlannerRun (step_budget=1)...")
t_run_start = time.time()
final_state = None
error_msg = None
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
    final_fields = M.Tail(final_state)()
    final_obligations = M.Head(final_fields)()
    final_root = M.Head(final_obligations)()
    frf = M.Tail(final_root)()
    frf2 = M.Tail(frf)()
    frf3 = M.Tail(frf2)()
    final_root_status = M.Head(M.Tail(frf3)())()

    obl_count = 0
    cur = final_obligations
    while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
        obl_count += 1
        cur = M.Tail(cur)()

    print()
    print("=== TEST 1 RESULTS ===")
    print(f"  Root final status:    {final_root_status}")
    proved = M.IdentityCompare(final_root_status, L.ProvedLabel)()
    failed = M.IdentityCompare(final_root_status, L.FailedLabel)()
    pending = M.IdentityCompare(final_root_status, L.PendingLabel)()
    print(f"  Is Proved:  {proved is M.truth_value}")
    print(f"  Is Failed:  {failed is M.truth_value}")
    print(f"  Is Pending: {pending is M.truth_value}")
    print(f"  Obligation count: {obl_count}")
    print(f"  Total time: {time.time() - t0:.3f}s")
else:
    print()
    print("=== TEST 1 RESULTS ===")
    print(f"  STATUS: FAILED - PlannerRun raised exception")
    print(f"  Error: {error_msg}")
    print(f"  Total time: {time.time() - t0:.3f}s")

print()
print("=== TEST 1 COMPLETE ===")
