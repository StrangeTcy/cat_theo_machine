import os
import sys

IMPORT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if IMPORT_ROOT not in sys.path:
    sys.path.insert(0, IMPORT_ROOT)

from hyge import labels as L
from hyge import machine as M
from hyge import planner as Planner
from hyge import proof as P
from hyge.runtime import make_fresh_runtime


runtime = make_fresh_runtime()
graph = runtime.graph
registry = M.FromContextGetConstructors(graph)()
heuristic = runtime.theorem_heuristic

cycle_goal = M.Pair(L.ZeroLabel, M.EmptyList)
cycle_rule = P.MultiRule(M.Pair(cycle_goal, M.EmptyList), cycle_goal)
cycle_rules = M.Pair(cycle_rule, M.EmptyList)
cycle_problem = Planner.PlannerProblem(M.EmptyList, cycle_goal, cycle_rules, heuristic)()
cycle_state = Planner.PlannerState(cycle_problem, registry)()
cycle_step = Planner.PlannerStep(graph, cycle_state, M.one)()
cycle_next_state = M.Head(cycle_step)()
cycle_changed = M.Head(M.Tail(cycle_step)())()
cycle_fields = M.Tail(cycle_next_state)()
cycle_obligations = M.Head(cycle_fields)()
cycle_obligation_count = M.Zero
cycle_remaining = cycle_obligations
while M.IdentityCompare(cycle_remaining, M.EmptyList)() is M.false_value:
    cycle_count_pair = M.Succ(cycle_obligation_count, registry)()
    cycle_obligation_count = M.Head(cycle_count_pair)()
    registry = M.Head(M.Tail(cycle_count_pair)())()
    cycle_remaining = M.Tail(cycle_remaining)()
assert M.IdentityCompare(cycle_changed, M.truth_value)() is M.truth_value
assert M.NatEq(cycle_obligation_count, M.one, registry)() is M.truth_value
cycle_jobs = M.Head(M.Tail(M.Tail(M.Tail(cycle_next_state)())())())()
assert M.IdentityCompare(cycle_jobs, M.EmptyList)() is M.false_value

parent_goal = M.Pair(L.ZeroLabel, M.EmptyList)
child_goal = M.Pair(L.SuccLabel, M.EmptyList)
problem = Planner.PlannerProblem(M.EmptyList, parent_goal, M.EmptyList, heuristic)()
state = Planner.PlannerState(problem, registry)()
state_fields = state
problems = M.Head(state_fields)()
state_fields = M.Tail(state_fields)()
state_obligations = M.Head(state_fields)()
state_fields = M.Tail(state_fields)()
state_fields = M.Tail(state_fields)()
state_fields = M.Tail(state_fields)()
next_obligation_id = M.Head(state_fields)()
registry = M.Head(M.Tail(state_fields)())()
parent = M.Head(state_obligations)()
parent_fields = M.Tail(parent)()
parent_id = M.Head(parent_fields)()
problem_id = M.Head(M.Tail(parent_fields)())()
child_id = next_obligation_id
next_pair = M.Succ(child_id, registry)()
next_obligation_id = M.Head(next_pair)()
registry = M.Head(M.Tail(next_pair)())()
child = Planner.PlannerObligation(
    child_id,
    problem_id,
    child_goal,
    L.FailedLabel,
    M.EmptyList,
    M.EmptyList,
)()
obligations = M.Pair(child, state_obligations)
dependencies = M.Pair(Planner.PlannerDependency(parent_id, child_id)(), M.EmptyList)
propagation_state = Planner.PlannerStateRecord(
    problems,
    obligations,
    dependencies,
    M.EmptyList,
    next_obligation_id,
    registry,
)()
propagation_step = Planner.PlannerStep(graph, propagation_state, M.one)()
propagation_next_state = M.Head(propagation_step)()
propagation_changed = M.Head(M.Tail(propagation_step)())()
assert M.IdentityCompare(propagation_changed, M.truth_value)() is M.truth_value
propagation_obligations = M.Head(M.Tail(propagation_next_state)())()
root_status = M.EmptyList
remaining = propagation_obligations
while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
    obligation_fields = M.Tail(M.Head(remaining)())()
    obligation_id = M.Head(obligation_fields)()
    obligation_fields = M.Tail(obligation_fields)()
    obligation_fields = M.Tail(obligation_fields)()
    obligation_fields = M.Tail(obligation_fields)()
    if M.TermEqual(obligation_id, parent_id)() is M.truth_value:
        root_status = M.Head(obligation_fields)()
        break
    remaining = M.Tail(remaining)()
assert M.IdentityCompare(root_status, L.FailedLabel)() is M.truth_value

supported_goal = M.Pair(L.ZeroLabel, M.EmptyList)
supported_fact = M.Pair(L.SuccLabel, M.EmptyList)
supported_start = M.Pair(supported_fact, M.EmptyList)
supported_state = runtime.evaluate(
    supported_start,
    supported_goal,
    rules=M.EmptyList,
    heuristic=heuristic,
    step_budget=M.one,
)
supported_obligations = M.Head(M.Tail(supported_state)())()
supported_root_fields = M.Tail(M.Head(supported_obligations)())()
supported_root_fields = M.Tail(supported_root_fields)()
supported_root_fields = M.Tail(supported_root_fields)()
supported_root_fields = M.Tail(supported_root_fields)()
supported_root_status = M.Head(supported_root_fields)()
assert M.IdentityCompare(supported_root_status, L.FailedLabel)() is M.truth_value

print("SUPPORTED_ENTRY_LIFECYCLE_OK")
print("PLANNER_LIFECYCLE_REGRESSIONS_OK")
