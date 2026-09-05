# ============================================================
# TEST 3: Compilation / YAML / 8-Pack Load Checks
# ============================================================
import sys, os, time

IMPORT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if IMPORT_ROOT not in sys.path:
    sys.path.insert(0, IMPORT_ROOT)

from hyge import machine as M
from hyge import proof as P
from hyge import labels as L
from hyge import planner as Plannermod
from hyge.runtime import make_fresh_runtime, boot_from_packs

t0 = time.time()
print("=== TEST 3: Compilation / YAML / 8-Pack Load Checks ===")
print()

PACK_DIR = r"Q:\hyge\packs"
PACK_PATHS = [
    os.path.join(PACK_DIR, "order-sign.pack.yaml"),
    os.path.join(PACK_DIR, "sqrt-real.pack.yaml"),
    os.path.join(PACK_DIR, "algebra-distribute.pack.yaml"),
    os.path.join(PACK_DIR, "real-closure.pack.yaml"),
    os.path.join(PACK_DIR, "arithmetic.pack.yaml"),
    os.path.join(PACK_DIR, "geometry-ontology.pack.yaml"),
    os.path.join(PACK_DIR, "trigonometry.pack.yaml"),
    os.path.join(PACK_DIR, "geometry.pack.yaml"),
]

print(f"[1] Checking pack directory: {PACK_DIR}")
existing = [p for p in PACK_PATHS if os.path.exists(p)]
missing = [p for p in PACK_PATHS if not os.path.exists(p)]
print(f"    Found: {len(existing)} packs")
if missing:
    for m in missing:
        print(f"    MISSING: {m}")
print()

print("[2] Loading all packs via boot_from_packs...")
namespace = {}
t_load_start = time.time()
runtime = None
load_error = None
try:
    runtime, loaded = boot_from_packs(existing, namespace)
    t_load_end = time.time()
    print(f"    All {len(existing)} packs loaded in {t_load_end - t_load_start:.3f}s")
except Exception as e:
    t_load_end = time.time()
    load_error = f"{e!r}"
    print(f"    ERROR loading packs: {load_error}")
    import traceback
    traceback.print_exc()

if runtime is None:
    print()
    print("=== TEST 3 RESULTS (ABORTED) ===")
    print(f"  STATUS: FAILED - Pack loading failed")
    print(f"  Error: {load_error}")
    print(f"  Total time: {time.time() - t0:.3f}s")
    sys.exit(1)

graph = runtime.graph
registry = M.FromContextGetConstructors(graph)()
print()

print("[3] Checking rule counts...")
all_rules = M.FromContextGetAllRules(graph)()
rule_count = 0
cur = all_rules
while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
    rule_count += 1
    cur = M.Tail(cur)()
print(f"    Total rules in graph: {rule_count}")

rule_order = M.FromContextGetRuleOrder(graph)()
order_count = 0
cur = rule_order
while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
    order_count += 1
    cur = M.Tail(cur)()
print(f"    Rules in order list: {order_count}")
print()

print("[4] Compiling rule chain...")
t_comp_start = time.time()
compile_error = None
compiled = None
comp_count = 0
try:
    compiled = P.CompileRuleChain(rule_order, registry)()
    t_comp_end = time.time()
    print(f"    Compilation OK in {t_comp_end - t_comp_start:.3f}s")
except Exception as e:
    t_comp_end = time.time()
    compile_error = f"{e!r}"
    print(f"    ERROR during compilation: {compile_error}")
    import traceback
    traceback.print_exc()

if compiled is not None:
    cur = compiled
    while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
        comp_count += 1
        cur = M.Tail(cur)()
    print(f"    Compiled rules: {comp_count}")
print()

print("[5] Testing planner with loaded rules...")
simple_start = M.Pair(L.ZeroLabel, M.EmptyList)
simple_goal = M.Pair(L.ZeroLabel, M.EmptyList)
heuristic = runtime.theorem_heuristic

rules_for_planner = compiled if compiled is not None else rule_order
problem = Plannermod.PlannerProblem(simple_start, simple_goal, rules_for_planner, heuristic)()
state = Plannermod.PlannerState(problem, registry)()

sf = M.Tail(state)()
obl = M.Head(sf)()
root = M.Head(obl)()
rf = M.Tail(root)()
rf2 = M.Tail(rf)()
rf3 = M.Tail(rf2)()
root_status_initial = M.Head(M.Tail(rf3)())()
print(f"    Planner state created, root status: {root_status_initial}")

t_plan_start = time.time()
plan_error = None
final_state = None
try:
    final_state = Plannermod.PlannerRun(graph, state, M.one)()
    t_plan_end = time.time()
    print(f"    PlannerRun OK in {t_plan_end - t_plan_start:.3f}s")

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
    print(f"    Final root status: {fstatus}, obligation count: {obl_count}")
except Exception as e:
    t_plan_end = time.time()
    plan_error = f"{e!r}"
    print(f"    ERROR in PlannerRun: {plan_error}")
    import traceback
    traceback.print_exc()

print()
print("=== TEST 3 RESULTS ===")
print(f"  Packs loaded:     {len(existing)}/8")
print(f"  Total rules:      {rule_count}")
comp_str = str(comp_count) if compiled is not None else "N/A (error)"
print(f"  Compiled rules:   {comp_str}")
print(f"  Load time:        {t_load_end - t_load_start:.3f}s")
if compiled is not None:
    print(f"  Compile time:     {t_comp_end - t_comp_start:.3f}s")
if compile_error:
    print(f"  Compile error:    {compile_error}")
if plan_error:
    print(f"  Planner error:    {plan_error}")
print(f"  Total time:       {time.time() - t0:.3f}s")
print()
print("=== TEST 3 COMPLETE ===")
