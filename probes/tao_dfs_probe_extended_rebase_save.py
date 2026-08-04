import time
import traceback

from hyge.runtime import boot_from_packs
from hyge.main import PACK_PATHS, _runtime_namespace
from hyge import machine as M
from hyge import labels as Lmod
from hyge import knowledge as K
from hyge import proof as Pmod
from hyge import search as Smod
from hyge.search.engine import _SearchStepKernel

Pmod.SetDebugTrace(M.truth_value)()
print("DEBUG-EXT: starting extended Tao DFS probe")
print("DEBUG-EXT: booting runtime from packs")
boot_started_at = time.time()
runtime, packs = boot_from_packs(PACK_PATHS, _runtime_namespace())
print("DEBUG-EXT: runtime booted in", time.time() - boot_started_at, "seconds")
registry = M.FromContextGetConstructors(runtime.graph)()
runtime.graph._search_disable_console = M.truth_value
print("DEBUG-EXT: console disabled for probe")
print("DEBUG-EXT: pack order-sign loaded")
print("DEBUG-EXT: pack sqrt-real loaded")
print("DEBUG-EXT: pack algebra-distribute loaded")
print("DEBUG-EXT: pack real-closure loaded")
print("DEBUG-EXT: pack arithmetic loaded")
print("DEBUG-EXT: pack geometry-ontology loaded")
print("DEBUG-EXT: pack trigonometry loaded")
print("DEBUG-EXT: pack geometry loaded")

trace_path = "/home/user/tao_dfs_probe_extended_traceback.txt"
trace_file = open(trace_path, "w", encoding="utf-8")
trace_file.write("extended tao dfs probe tracebacks\n")

print("DEBUG-EXT: loading Tao problem example from geometry pack")
geometry_pack = packs.by_name("geometry")
start, goal = geometry_pack.examples["tao_problem_1_1_triangle"]
print("DEBUG-EXT: raw start built")
print("DEBUG-EXT: raw start =", M.PrettyTerm(start, registry)())
print("DEBUG-EXT: raw goal =", M.PrettyTerm(goal, registry)())

normalize_start_started_at = time.time()
print("DEBUG-EXT: normalizing start knowledge")
try:
    normalized_start = Pmod.NormalizeKnowledge(start, registry)()
    print("DEBUG-EXT: normalized start in", time.time() - normalize_start_started_at, "seconds")
    print("DEBUG-EXT: normalized start =", M.PrettyTerm(normalized_start, registry)())
except Exception:
    print("DEBUG-EXT: normalizing start raised")
    trace_file.write("normalize-start\n")
    trace_file.write(traceback.format_exc())
    raise

normalize_goal_started_at = time.time()
print("DEBUG-EXT: normalizing goal")
try:
    normalized_goal = Pmod.NormalizeKnowledge(goal, registry)()
    print("DEBUG-EXT: normalized goal in", time.time() - normalize_goal_started_at, "seconds")
    print("DEBUG-EXT: normalized goal =", M.PrettyTerm(normalized_goal, registry)())
except Exception:
    print("DEBUG-EXT: normalizing goal raised")
    trace_file.write("normalize-goal\n")
    trace_file.write(traceback.format_exc())
    raise

print("DEBUG-EXT: checking derivation cache before search")
cache_started_at = time.time()
try:
    cached = runtime.graph.lookup_derivation(normalized_start, normalized_goal)
    print("DEBUG-EXT: derivation cache lookup finished in", time.time() - cache_started_at, "seconds")
    if M.Compare(cached, M.EmptyList)() is M.truth_value:
        print("DEBUG-EXT: derivation cache miss")
    else:
        print("DEBUG-EXT: derivation cache hit")
except Exception:
    print("DEBUG-EXT: derivation cache lookup raised")
    trace_file.write("derivation-cache\n")
    trace_file.write(traceback.format_exc())
    raise

print("DEBUG-EXT: loading ordered rules")
rules_started_at = time.time()
ordered_rules = runtime.ordered_rules()
print("DEBUG-EXT: ordered rules loaded in", time.time() - rules_started_at, "seconds")

max_steps = runtime.graph.next_rule_index
if M.IdentityCompare(max_steps, M.EmptyList)() is M.truth_value:
    count_rep = M.CountRep(ordered_rules)()
    max_steps = M.Atom()
    max_steps.value = count_rep
elif M.NatEq(max_steps, M.Zero, registry)() is M.truth_value:
    count_rep = M.CountRep(ordered_rules)()
    max_steps = M.Atom()
    max_steps.value = count_rep
print("DEBUG-EXT: ordered rule max-steps =", M.PrettyTerm(max_steps, registry)())
print("DEBUG-EXT: building root state")
root_state = M.SearchState(normalized_start, M.EmptyList, M.EmptyList, max_steps)()
print("DEBUG-EXT: root current =", M.PrettyTerm(M.SearchStateCurrent(root_state)(), registry)())
print("DEBUG-EXT: root steps =", M.PrettyTerm(M.SearchStateStepsRemaining(root_state)(), registry)())
if M.IdentityCompare(M.SearchStateCursor(root_state)(), M.EmptyList)() is M.truth_value:
    print("DEBUG-EXT: root cursor is empty before theorem seeding")
else:
    print("DEBUG-EXT: root cursor is already populated before theorem seeding")

print("DEBUG-EXT: building root job")
root_job = M.SearchJob(
    normalized_start,
    normalized_goal,
    ordered_rules,
    runtime.theorem_heuristic,
    M.SearchRunningLabel,
    M.Pair(root_state, M.EmptyList),
    M.Zero,
    M.Zero,
    M.Zero,
    M.EmptyList,
    M.EmptyList,
    M.EmptyList,
    M.EmptyList,
    M.one,
)()
print("DEBUG-EXT: root job frontier size =", M.PrettyTerm(M.SearchJobFrontierSize(root_job)(), registry)())

print("DEBUG-EXT: creating SearchStep kernel")
kernel_started_at = time.time()
kernel = _SearchStepKernel(
    runtime.graph,
    root_job,
    ordered_rules,
    runtime.theorem_heuristic,
    normalized_goal,
    registry,
    None,
    None,
)
print("DEBUG-EXT: kernel created in", time.time() - kernel_started_at, "seconds")

print("DEBUG-EXT: probing cached solution for root")
cached_solution_started_at = time.time()
try:
    cached_solution = kernel._cached_solution(
        M.SearchStateCurrent(root_state)(),
        normalized_goal,
        M.SearchStatePlan(root_state)(),
        M.SearchStateStepsRemaining(root_state)(),
    )
    print("DEBUG-EXT: cached solution probe finished in", time.time() - cached_solution_started_at, "seconds")
    if M.Compare(cached_solution, M.EmptyList)() is M.truth_value:
        print("DEBUG-EXT: no cached solution for root")
    else:
        print("DEBUG-EXT: cached solution exists for root")
except Exception:
    print("DEBUG-EXT: cached solution probe raised")
    trace_file.write("cached-solution\n")
    trace_file.write(traceback.format_exc())
    raise

print("DEBUG-EXT: probing knowledge head index for root")
head_index_started_at = time.time()
root_facts = Pmod.KnowledgeFacts(M.SearchStateCurrent(root_state)())()
root_head_index = K.KnowledgeHeadIndexInsertChain(M.EmptyTree, root_facts, registry)()
print("DEBUG-EXT: root knowledge head index built in", time.time() - head_index_started_at, "seconds")
print("DEBUG-EXT: probing applicable theorem rules for root")
applicable_started_at = time.time()
try:
    applicable_rules = kernel._theorem_applicable_rules_for(M.SearchStateCurrent(root_state)())
    print("DEBUG-EXT: applicable theorem rules ready in", time.time() - applicable_started_at, "seconds")
    applicable_count_pair = M.Count(applicable_rules, kernel.registry)()
    applicable_count = M.Head(applicable_count_pair)()
    kernel.registry = M.Head(M.Tail(applicable_count_pair)())()
    print("DEBUG-EXT: applicable theorem rule count =", M.PrettyTerm(applicable_count, kernel.registry)())
    if Smod.SearchChainHasAt(applicable_rules, M.Zero)() is M.truth_value:
        print("DEBUG-EXT: applicable theorem 0 =", Pmod.PrettyRule(Smod.SearchChainAt(applicable_rules, M.Zero)(), kernel.registry)())
    if Smod.SearchChainHasAt(applicable_rules, M.one)() is M.truth_value:
        print("DEBUG-EXT: applicable theorem 1 =", Pmod.PrettyRule(Smod.SearchChainAt(applicable_rules, M.one)(), kernel.registry)())
    if Smod.SearchChainHasAt(applicable_rules, M.two)() is M.truth_value:
        print("DEBUG-EXT: applicable theorem 2 =", Pmod.PrettyRule(Smod.SearchChainAt(applicable_rules, M.two)(), kernel.registry)())
    if Smod.SearchChainHasAt(applicable_rules, M.three)() is M.truth_value:
        print("DEBUG-EXT: applicable theorem 3 =", Pmod.PrettyRule(Smod.SearchChainAt(applicable_rules, M.three)(), kernel.registry)())
    if Smod.SearchChainHasAt(applicable_rules, M.four)() is M.truth_value:
        print("DEBUG-EXT: applicable theorem 4 =", Pmod.PrettyRule(Smod.SearchChainAt(applicable_rules, M.four)(), kernel.registry)())
except Exception:
    print("DEBUG-EXT: applicable theorem probe raised")
    trace_file.write("applicable-theorems\n")
    trace_file.write(traceback.format_exc())
    raise

print("DEBUG-EXT: probing ordered theorem rules for root")
ordered_theorems_started_at = time.time()
try:
    ordered_theorems = kernel._theorem_rules_for(M.SearchStateCurrent(root_state)(), normalized_goal)
    print("DEBUG-EXT: ordered theorem rules ready in", time.time() - ordered_theorems_started_at, "seconds")
    ordered_theorem_count_pair = M.Count(ordered_theorems, kernel.registry)()
    ordered_theorem_count = M.Head(ordered_theorem_count_pair)()
    kernel.registry = M.Head(M.Tail(ordered_theorem_count_pair)())()
    print("DEBUG-EXT: ordered theorem rule count =", M.PrettyTerm(ordered_theorem_count, kernel.registry)())
    if Smod.SearchChainHasAt(ordered_theorems, M.Zero)() is M.truth_value:
        print("DEBUG-EXT: ordered theorem 0 =", Pmod.PrettyRule(Smod.SearchChainAt(ordered_theorems, M.Zero)(), kernel.registry)())
    if Smod.SearchChainHasAt(ordered_theorems, M.one)() is M.truth_value:
        print("DEBUG-EXT: ordered theorem 1 =", Pmod.PrettyRule(Smod.SearchChainAt(ordered_theorems, M.one)(), kernel.registry)())
    if Smod.SearchChainHasAt(ordered_theorems, M.two)() is M.truth_value:
        print("DEBUG-EXT: ordered theorem 2 =", Pmod.PrettyRule(Smod.SearchChainAt(ordered_theorems, M.two)(), kernel.registry)())
    if Smod.SearchChainHasAt(ordered_theorems, M.three)() is M.truth_value:
        print("DEBUG-EXT: ordered theorem 3 =", Pmod.PrettyRule(Smod.SearchChainAt(ordered_theorems, M.three)(), kernel.registry)())
    if Smod.SearchChainHasAt(ordered_theorems, M.four)() is M.truth_value:
        print("DEBUG-EXT: ordered theorem 4 =", Pmod.PrettyRule(Smod.SearchChainAt(ordered_theorems, M.four)(), kernel.registry)())
except Exception:
    print("DEBUG-EXT: ordered theorem probe raised")
    trace_file.write("ordered-theorems\n")
    trace_file.write(traceback.format_exc())
    raise

print("DEBUG-EXT: probing one raw kernel advance from the root")
advance_started_at = time.time()
try:
    advance_result = kernel._advance_state(root_state, normalized_goal)
    print("DEBUG-EXT: kernel advance finished in", time.time() - advance_started_at, "seconds")
    advance_success = kernel._advance_result_success(advance_result)
    advance_child = kernel._advance_result_child(advance_result)
    advance_continuation = kernel._advance_result_continuation(advance_result)
    advance_generated = kernel._advance_result_generated(advance_result)
    if M.Compare(advance_success, M.EmptyList)() is M.truth_value:
        print("DEBUG-EXT: kernel advance did not reach goal immediately")
    else:
        print("DEBUG-EXT: kernel advance reached goal immediately")
        print("DEBUG-EXT: success plan =", Pmod.PrettyPlanChain(advance_success, kernel.registry)())
    if M.Compare(advance_child, M.EmptyList)() is M.truth_value:
        print("DEBUG-EXT: kernel advance produced no child")
    else:
        print("DEBUG-EXT: kernel advance child current =", M.PrettyTerm(M.SearchStateCurrent(advance_child)(), kernel.registry)())
        print("DEBUG-EXT: kernel advance child plan =", Pmod.PrettyPlanChain(M.Reverse(M.SearchStatePlan(advance_child)())(), kernel.registry)())
    if M.Compare(advance_continuation, M.EmptyList)() is M.truth_value:
        print("DEBUG-EXT: kernel advance produced no continuation")
    else:
        print("DEBUG-EXT: kernel advance continuation current =", M.PrettyTerm(M.SearchStateCurrent(advance_continuation)(), kernel.registry)())
        continuation_cursor = M.SearchStateCursor(advance_continuation)()
        if M.IdentityCompare(continuation_cursor, M.EmptyList)() is M.truth_value:
            print("DEBUG-EXT: continuation cursor is empty")
        elif M.IdentityCompare(M.Head(continuation_cursor)(), M.SearchTheoremCursorLabel)() is M.truth_value:
            print("DEBUG-EXT: continuation cursor is theorem")
            continuation_rules = M.SearchTheoremCursorRules(continuation_cursor)()
            continuation_rule_count_pair = M.Count(continuation_rules, kernel.registry)()
            continuation_rule_count = M.Head(continuation_rule_count_pair)()
            kernel.registry = M.Head(M.Tail(continuation_rule_count_pair)())()
            print("DEBUG-EXT: continuation theorem count =", M.PrettyTerm(continuation_rule_count, kernel.registry)())
            if Smod.SearchChainHasAt(continuation_rules, M.Zero)() is M.truth_value:
                print("DEBUG-EXT: continuation theorem 0 =", Pmod.PrettyRule(Smod.SearchChainAt(continuation_rules, M.Zero)(), kernel.registry)())
        elif M.IdentityCompare(M.Head(continuation_cursor)(), M.SearchRewriteCursorLabel)() is M.truth_value:
            print("DEBUG-EXT: continuation cursor is rewrite")
        else:
            print("DEBUG-EXT: continuation cursor has unknown label")
    print("DEBUG-EXT: kernel advance generated increment =", M.PrettyTerm(advance_generated, kernel.registry)())
except Exception:
    print("DEBUG-EXT: kernel advance raised")
    trace_file.write("kernel-advance\n")
    trace_file.write(traceback.format_exc())
    raise

print("DEBUG-EXT: probing one full SearchStep from the root")
step_started_at = time.time()
try:
    step_pair = Smod.SearchStep(runtime.graph, root_job, kernel.registry)()
    stepped_job = M.Head(step_pair)()
    registry = M.Head(M.Tail(step_pair)())()
    runtime.graph._replace_context(constructors=registry)
    print("DEBUG-EXT: SearchStep finished in", time.time() - step_started_at, "seconds")
    if M.IdentityCompare(M.SearchJobStatus(stepped_job)(), M.SearchRunningLabel)() is M.truth_value:
        print("DEBUG-EXT: SearchStep status = RUNNING")
    elif M.IdentityCompare(M.SearchJobStatus(stepped_job)(), M.SearchFailureLabel)() is M.truth_value:
        print("DEBUG-EXT: SearchStep status = FAILURE")
    elif M.IdentityCompare(M.SearchJobStatus(stepped_job)(), M.SearchSuccessLabel)() is M.truth_value:
        print("DEBUG-EXT: SearchStep status = SUCCESS")
    elif M.IdentityCompare(M.SearchJobStatus(stepped_job)(), M.SearchPausedLabel)() is M.truth_value:
        print("DEBUG-EXT: SearchStep status = PAUSED")
    else:
        print("DEBUG-EXT: SearchStep status = OTHER")
    print("DEBUG-EXT: SearchStep frontier size =", M.PrettyTerm(M.SearchJobFrontierSize(stepped_job)(), registry)())
    print("DEBUG-EXT: SearchStep expanded =", M.PrettyTerm(M.SearchJobExpanded(stepped_job)(), registry)())
    print("DEBUG-EXT: SearchStep generated =", M.PrettyTerm(M.SearchJobGenerated(stepped_job)(), registry)())
    print("DEBUG-EXT: SearchStep frontier peak =", M.PrettyTerm(M.SearchJobFrontierPeak(stepped_job)(), registry)())
    stepped_frontier = M.SearchJobFrontier(stepped_job)()
    if M.Compare(stepped_frontier, M.EmptyList)() is M.truth_value:
        print("DEBUG-EXT: SearchStep frontier is empty")
    else:
        frontier_head = M.Head(stepped_frontier)()
        print("DEBUG-EXT: SearchStep frontier head current =", M.PrettyTerm(M.SearchStateCurrent(frontier_head)(), registry)())
        print("DEBUG-EXT: SearchStep frontier head plan =", Pmod.PrettyPlanChain(M.Reverse(M.SearchStatePlan(frontier_head)())(), registry)())
except Exception:
    print("DEBUG-EXT: SearchStep raised")
    trace_file.write("search-step\n")
    trace_file.write(traceback.format_exc())
    raise

print("DEBUG-EXT: probing full SearchDFS run")
dfs_started_at = time.time()
try:
    search_pair = Smod.SearchDFS(
        runtime.graph,
        start,
        goal,
        ordered_rules,
        runtime.theorem_heuristic,
        registry,
    )()
    search_plan = M.Head(search_pair)()
    search_cost = M.Head(M.Tail(search_pair)())()
    final_registry = M.FromContextGetConstructors(runtime.graph)()
    print("DEBUG-EXT: SearchDFS completed in", time.time() - dfs_started_at, "seconds")
    if M.IdentityCompare(Smod.SearchCostOutcome(search_cost)(), M.SearchSuccessLabel)() is M.truth_value:
        print("DEBUG-EXT: SearchDFS outcome = SUCCESS")
    elif M.IdentityCompare(Smod.SearchCostOutcome(search_cost)(), M.SearchFailureLabel)() is M.truth_value:
        print("DEBUG-EXT: SearchDFS outcome = FAILURE")
    elif M.IdentityCompare(Smod.SearchCostOutcome(search_cost)(), M.SearchPausedLabel)() is M.truth_value:
        print("DEBUG-EXT: SearchDFS outcome = PAUSED")
    elif M.IdentityCompare(Smod.SearchCostOutcome(search_cost)(), M.SearchTimedOutLabel)() is M.truth_value:
        print("DEBUG-EXT: SearchDFS outcome = TIMED_OUT")
    elif M.IdentityCompare(Smod.SearchCostOutcome(search_cost)(), M.SearchAbortedByUserLabel)() is M.truth_value:
        print("DEBUG-EXT: SearchDFS outcome = ABORTED")
    else:
        print("DEBUG-EXT: SearchDFS outcome = OTHER")
    print("DEBUG-EXT: SearchDFS expanded =", M.PrettyTerm(Smod.SearchCostExpanded(search_cost)(), final_registry)())
    print("DEBUG-EXT: SearchDFS generated =", M.PrettyTerm(Smod.SearchCostGenerated(search_cost)(), final_registry)())
    print("DEBUG-EXT: SearchDFS frontier peak =", M.PrettyTerm(Smod.SearchCostFrontierPeak(search_cost)(), final_registry)())
    print("DEBUG-EXT: SearchDFS found depth =", M.PrettyTerm(Smod.SearchCostFoundDepth(search_cost)(), final_registry)())
    if M.Compare(search_plan, M.EmptyList)() is M.truth_value:
        print("DEBUG-EXT: SearchDFS plan is empty")
    else:
        print("DEBUG-EXT: SearchDFS plan =", Pmod.PrettyPlanChain(search_plan, final_registry)())
except Exception:
    print("DEBUG-EXT: SearchDFS raised")
    trace_file.write("search-dfs\n")
    trace_file.write(traceback.format_exc())
    raise

trace_file.close()
print("DEBUG-EXT: traceback file written to", trace_path)
