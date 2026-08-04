import sys
import time

sys.path.insert(0, '/home/user')

from hyge.runtime import boot_from_packs
from hyge.main import PACK_PATHS, _runtime_namespace
from hyge import machine as M
from hyge import proof as P
from hyge.search.engine import _SearchStepKernel

print('CLOSURE: boot start', flush=True)
runtime, packs = boot_from_packs(PACK_PATHS, _runtime_namespace())
registry = M.FromContextGetConstructors(runtime.graph)()
graph = runtime.graph
graph._search_disable_console = M.truth_value
graph._search_probe_disable_applicable_cache = M.false_value
graph._search_probe_disable_applicable_shards = M.truth_value
graph._search_probe_disable_anchor_meta = M.truth_value
geometry_pack = packs.by_name('geometry')
start, goal = geometry_pack.examples['tao_problem_1_1_triangle']
current = P.NormalizeKnowledge(start, registry)()
goal = P.NormalizeKnowledge(goal, registry)()
rules = runtime.ordered_rules()
max_steps = graph.next_rule_index
if M.IdentityCompare(max_steps, M.EmptyList)() is M.truth_value:
    count_rep = M.CountRep(rules)()
    max_steps = M.Atom()
    max_steps.value = count_rep
else:
    if M.NatEq(max_steps, M.Zero, registry)() is M.truth_value:
        count_rep = M.CountRep(rules)()
        max_steps = M.Atom()
        max_steps.value = count_rep
job = M.SearchJob(
    current,
    goal,
    rules,
    runtime.theorem_heuristic,
    M.SearchRunningLabel,
    M.Pair(M.SearchState(current, M.EmptyList, M.EmptyList, max_steps)(), M.EmptyList),
    M.Zero,
    M.Zero,
    M.Zero,
    M.EmptyList,
    M.EmptyList,
    M.EmptyList,
    M.EmptyList,
    M.one,
)()
kernel = _SearchStepKernel(graph, job, rules, runtime.theorem_heuristic, goal, registry, None, None)
round_count = 0
changed = M.truth_value
print('CLOSURE: start', flush=True)
while M.IdentityCompare(changed, M.truth_value)() is M.truth_value:
    if kernel._goal_reached(current, goal) is M.truth_value:
        break
    changed = M.false_value
    indexes = kernel._theorem_indexes_for(current)
    head_index = M.Head(indexes)()
    exact_trie = M.Head(M.Tail(indexes)())()
    applicable = P.FilterApplicableRulesWithIndex(rules, current, head_index, kernel.registry, exact_trie)()
    cursor = applicable
    while M.IdentityCompare(cursor, M.EmptyList)() is M.false_value:
        rule = M.Head(cursor)()
        next_term = kernel._apply_theorem_rule_at_root(rule, current)
        next_term = kernel._canonical_term(next_term)
        if M.TermEqual(next_term, current)() is M.false_value:
            current = next_term
            changed = M.truth_value
        cursor = M.Tail(cursor)()
    round_count = round_count + 1
    print('CLOSURE: round', round_count, flush=True)
    if round_count == 40:
        break
print('CLOSURE: goal', kernel._goal_reached(current, goal) is M.truth_value, flush=True)
print('CLOSURE: rounds', round_count, flush=True)
print('CLOSURE: done', flush=True)
