import time
from hyge.runtime import boot_from_packs
from hyge.main import PACK_PATHS, _runtime_namespace
from hyge import machine as M
from hyge import proof as P
from hyge import search as S

print('BOOT start', flush=True)
runtime, packs = boot_from_packs(PACK_PATHS, _runtime_namespace())
registry = M.FromContextGetConstructors(runtime.graph)()
g = runtime.graph
g._search_disable_console = M.truth_value
g._search_probe_disable_applicable_cache = M.false_value
g._search_probe_disable_applicable_shards = M.truth_value
g._search_probe_disable_anchor_meta = M.truth_value
geometry_pack = packs.by_name('geometry')
start, goal = geometry_pack.examples['tao_problem_1_1_triangle']
start = P.NormalizeKnowledge(start, registry)()
goal = P.NormalizeKnowledge(goal, registry)()
ordered_rules = runtime.ordered_rules()
max_steps = g.next_rule_index
if M.IdentityCompare(max_steps, M.EmptyList)() is M.truth_value or M.NatEq(max_steps, M.Zero, registry)() is M.truth_value:
    count_rep = M.CountRep(ordered_rules)()
    max_steps = M.Atom()
    max_steps.value = count_rep
job = M.SearchJob(
    start,
    goal,
    ordered_rules,
    runtime.theorem_heuristic,
    M.SearchRunningLabel,
    M.Pair(M.SearchState(start, M.EmptyList, M.EmptyList, max_steps)(), M.EmptyList),
    M.Zero,
    M.Zero,
    M.Zero,
    M.EmptyList,
    M.EmptyList,
    M.EmptyList,
    M.EmptyList,
    M.one,
)()
print('BOOT done', flush=True)
t0 = time.time()
step_pair = S.SearchStep(g, job, registry)()
elapsed = time.time() - t0
job = M.Head(step_pair)()
registry = M.Head(M.Tail(step_pair)())()
g._replace_context(constructors=registry)
print('STEP elapsed', round(elapsed, 3), flush=True)
print('running', M.IdentityCompare(M.SearchJobStatus(job)(), M.SearchRunningLabel)() is M.truth_value, flush=True)
print('success', M.IdentityCompare(M.SearchJobStatus(job)(), M.SearchSuccessLabel)() is M.truth_value, flush=True)
print('failure', M.IdentityCompare(M.SearchJobStatus(job)(), M.SearchFailureLabel)() is M.truth_value, flush=True)
print('expanded', M.PrettyTerm(M.SearchJobExpanded(job)(), registry)(), flush=True)
print('generated', M.PrettyTerm(M.SearchJobGenerated(job)(), registry)(), flush=True)
print('frontier', M.PrettyTerm(M.SearchJobFrontierSize(job)(), registry)(), flush=True)
frontier = M.SearchJobFrontier(job)()
print('frontier-empty', M.IdentityCompare(frontier, M.EmptyList)() is M.truth_value, flush=True)
if M.IdentityCompare(frontier, M.EmptyList)() is M.false_value:
    head = M.Head(frontier)()
    print('head plan', P.PrettyPlanChain(M.Reverse(M.SearchStatePlan(head)())(), registry)(), flush=True)
    print('head current', M.PrettyTerm(M.SearchStateCurrent(head)(), registry)(), flush=True)
print('DONE', flush=True)
