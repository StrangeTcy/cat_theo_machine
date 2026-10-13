# ============================================================
# TEST 10: Gate E & F Graph Tasks & 7-Rung Curriculum Suite
# ============================================================
import os
import sys
import time

IMPORT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if IMPORT_ROOT not in sys.path:
    sys.path.insert(0, IMPORT_ROOT)

from cat_theo_machine import curriculum as Curric
from cat_theo_machine import graph_task as GT
from cat_theo_machine import labels as L
from cat_theo_machine import machine as M
from cat_theo_machine import proof as P
from cat_theo_machine.runtime import make_fresh_runtime

t0 = time.time()
print("=== TEST 10: Gate E & F Graph Tasks & 7-Rung Curriculum Suite ===")
print()

print("[1] Initializing runtime, hypergraph, and registry...")
runtime = make_fresh_runtime()
graph = runtime.graph
registry = M.FromContextGetConstructors(graph)()
print("    Runtime OK.")
print()

# Domain Tags & Nodes
edge_e = M.Atom()
edge_f = M.Atom()
rel_r = M.Atom()

node_a = M.Atom()
node_b = M.Atom()
node_c = M.Atom()
node_d = M.Atom()
node_goal = M.Atom()
node_alias = M.Atom()

var_x = M.Var()
var_y = M.Var()
var_z = M.Var()

print("[2] Test Case 1: Rung 1 — Single-Edge Retrieval...")
task_1_res = Curric.BuildRung1RetrievalTask(
    M.Atom(), edge_e, node_a, node_b, var_x, registry
)()
res_1 = GT.ExecuteGraphQuery(task_1_res, registry)()
tag_1 = M.Head(res_1)()
is_ok_1 = M.IdentityCompare(tag_1, L.TaskSuccessLabel)() is M.truth_value
print(f"    Rung 1 Verdict: {tag_1} (Passed: {is_ok_1})")
assert is_ok_1, "Test 1 Failed: Rung 1 Single-Edge Retrieval failed!"

print("[3] Test Case 2: Rung 2 — Two-Edge Relational Join...")
task_2_res = Curric.BuildRung2JoinTask(
    M.Atom(), edge_e, node_a, node_b, node_c, var_x, var_y, registry
)()
res_2 = GT.ExecuteGraphQuery(task_2_res, registry)()
tag_2 = M.Head(res_2)()
is_ok_2 = M.IdentityCompare(tag_2, L.TaskSuccessLabel)() is M.truth_value
print(f"    Rung 2 Verdict: {tag_2} (Passed: {is_ok_2})")
assert is_ok_2, "Test 2 Failed: Rung 2 Two-Edge Join failed!"

print("[4] Test Case 3: Rung 3 — Repeated-Variable Constraint...")
task_3_res = Curric.BuildRung3ConstraintTask(
    M.Atom(), rel_r, node_a, node_b, var_x, registry
)()
res_3 = GT.ExecuteGraphQuery(task_3_res, registry)()
tag_3 = M.Head(res_3)()
is_ok_3 = M.IdentityCompare(tag_3, L.TaskSuccessLabel)() is M.truth_value
print(f"    Rung 3 Verdict: {tag_3} (Passed: {is_ok_3})")
assert is_ok_3, "Test 3 Failed: Rung 3 Constraint Satisfaction failed!"

print("[5] Test Case 4: Rung 4 — Two-Hop Rule Derivation...")
fact_a = M.Pair(edge_e, M.Pair(node_a, M.EmptyList))
fact_b = M.Pair(edge_e, M.Pair(node_b, M.EmptyList))
fact_c = M.Pair(edge_e, M.Pair(node_c, M.EmptyList))
task_4_res = Curric.BuildRung4DerivationTask(
    M.Atom(), fact_a, fact_b, fact_c, registry
)()
res_4 = GT.ExecuteGraphQuery(task_4_res, registry)()
tag_4 = M.Head(res_4)()
is_ok_4 = M.IdentityCompare(tag_4, L.TaskSuccessLabel)() is M.truth_value
print(f"    Rung 4 Verdict: {tag_4} (Passed: {is_ok_4})")
assert is_ok_4, "Test 4 Failed: Rung 4 Derivation failed!"

print("[6] Test Case 5: Rung 5 — Identity & Alias Normalization...")
task_5_res = Curric.BuildRung5AliasTask(
    M.Atom(), edge_e, node_alias, node_a, node_b, var_x, registry
)()
res_5 = GT.ExecuteGraphQuery(task_5_res, registry)()
tag_5 = M.Head(res_5)()
is_ok_5 = M.IdentityCompare(tag_5, L.TaskSuccessLabel)() is M.truth_value
print(f"    Rung 5 Verdict: {tag_5} (Passed: {is_ok_5})")
assert is_ok_5, "Test 5 Failed: Rung 5 Alias Normalization failed!"

print("[7] Test Case 6: Rung 6 — Explicit Negative / Failure Result...")
task_6_res = Curric.BuildRung6NegativeTask(
    M.Atom(), edge_e, node_a, node_b, node_c, registry
)()
res_6 = GT.ExecuteGraphQuery(task_6_res, registry)()
tag_6 = M.Head(res_6)()
is_ok_6 = M.IdentityCompare(tag_6, L.TaskSuccessLabel)() is M.truth_value
print(f"    Rung 6 Verdict: {tag_6} (Passed: {is_ok_6})")
assert is_ok_6, "Test 6 Failed: Rung 6 Negative Detection failed!"

print("[8] Test Case 7: Rung 7 — Planner Multi-Query Decomposition...")
task_7_res = Curric.BuildRung7PlannerTask(
    M.Atom(),
    edge_e,
    edge_f,
    node_a,
    node_b,
    node_c,
    node_goal,
    var_x,
    var_y,
    var_z,
    registry,
)()
res_7 = GT.ExecuteGraphQuery(task_7_res, registry)()
tag_7 = M.Head(res_7)()
is_ok_7 = M.IdentityCompare(tag_7, L.TaskSuccessLabel)() is M.truth_value
print(f"    Rung 7 Verdict: {tag_7} (Passed: {is_ok_7})")
assert is_ok_7, "Test 7 Failed: Rung 7 Planner Decomposition failed!"

print("[9] Test Case 8: Robustness Noise Invariance Suite...")
distractor_1 = M.Pair(
    edge_e, M.Pair(M.Atom(), M.Pair(M.Atom(), M.EmptyList))
)
distractor_2 = M.Pair(
    rel_r, M.Pair(M.Atom(), M.Pair(M.Atom(), M.EmptyList))
)
distractor_facts = M.Pair(distractor_1, M.Pair(distractor_2, M.EmptyList))

# Mutate tasks with duplicates and distractors
noisy_task_1 = Curric.MutateWithNoise(
    task_1_res, distractor_facts, registry
)()
noisy_task_2 = Curric.MutateWithNoise(
    task_2_res, distractor_facts, registry
)()
noisy_task_3 = Curric.MutateWithNoise(
    task_3_res, distractor_facts, registry
)()
noisy_task_5 = Curric.MutateWithNoise(
    task_5_res, distractor_facts, registry
)()
noisy_task_7 = Curric.MutateWithNoise(
    task_7_res, distractor_facts, registry
)()

curriculum_suite = M.Pair(
    noisy_task_1,
    M.Pair(
        noisy_task_2,
        M.Pair(
            noisy_task_3,
            M.Pair(
                task_4_res,
                M.Pair(
                    noisy_task_5,
                    M.Pair(
                        task_6_res,
                        M.Pair(noisy_task_7, M.EmptyList),
                    ),
                ),
            ),
        ),
    ),
)

suite_eval_res = Curric.EvaluateCurriculumSuite(
    curriculum_suite, registry
)()
suite_tag = M.Head(suite_eval_res)()
is_suite_ok = (
    M.IdentityCompare(suite_tag, L.CurriculumSuiteResultLabel)()
    is M.truth_value
)

passed_tasks = M.Head(M.Tail(suite_eval_res)())()
failed_tasks = M.Head(M.Tail(M.Tail(suite_eval_res)())())()

passed_count = 0
cur = passed_tasks
while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
    passed_count += 1
    cur = M.Tail(cur)()

failed_count = 0
cur = failed_tasks
while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
    failed_count += 1
    cur = M.Tail(cur)()

print(
    f"    Curriculum Suite Verdict: {suite_tag} (Passed: {is_suite_ok})"
)
print(
    f"    Passed Tasks: {passed_count}/7, Failed Tasks: {failed_count}/7"
)
assert (
    is_suite_ok and passed_count == 7 and failed_count == 0
), "Test 8 Failed: Robustness curriculum evaluation failed!"

print()
print(
    f"=== ALL 8 GATE E & F CURRICULUM & ROBUSTNESS TESTS PASSED in {time.time() - t0:.3f}s ==="
)
