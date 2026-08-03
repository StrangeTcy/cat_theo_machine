import time

from hyge.runtime import boot_from_packs
from hyge.main import PACK_PATHS, _runtime_namespace
from hyge import machine as M
from hyge import labels as Lmod
from hyge import proof as Pmod
from hyge import search as Smod

runtime, packs = boot_from_packs(PACK_PATHS, _runtime_namespace())
registry = M.FromContextGetConstructors(runtime.graph)()
runtime.graph._search_disable_console = M.truth_value

geometry_pack = packs.by_name("geometry")
start, goal = geometry_pack.examples["tao_problem_1_1_triangle"]

start_time = time.time()
search_pair = Smod.SearchDFS(
    runtime.graph,
    start,
    goal,
    runtime.ordered_rules(),
    runtime.theorem_heuristic,
    registry,
)()
elapsed = time.time() - start_time

plan = M.Head(search_pair)()
search_cost = M.Head(M.Tail(search_pair)())()
final_registry = M.FromContextGetConstructors(runtime.graph)()

status_text = "OTHER"
if M.IdentityCompare(Smod.SearchCostOutcome(search_cost)(), M.SearchSuccessLabel)() is M.truth_value:
    status_text = "SUCCESS"
elif M.IdentityCompare(Smod.SearchCostOutcome(search_cost)(), M.SearchFailureLabel)() is M.truth_value:
    status_text = "FAILURE"
elif M.IdentityCompare(Smod.SearchCostOutcome(search_cost)(), M.SearchPausedLabel)() is M.truth_value:
    status_text = "PAUSED"
elif M.IdentityCompare(Smod.SearchCostOutcome(search_cost)(), M.SearchTimedOutLabel)() is M.truth_value:
    status_text = "TIMED_OUT"
elif M.IdentityCompare(Smod.SearchCostOutcome(search_cost)(), M.SearchAbortedByUserLabel)() is M.truth_value:
    status_text = "ABORTED"

print("mode:", "SearchDFS")
print("elapsed-seconds:", elapsed)
print("status:", status_text)
print("expanded:", M.PrettyTerm(Smod.SearchCostExpanded(search_cost)(), final_registry)())
print("generated:", M.PrettyTerm(Smod.SearchCostGenerated(search_cost)(), final_registry)())
print("frontier-peak:", M.PrettyTerm(Smod.SearchCostFrontierPeak(search_cost)(), final_registry)())
print("found-depth:", M.PrettyTerm(Smod.SearchCostFoundDepth(search_cost)(), final_registry)())

if M.Compare(plan, M.EmptyList)() is M.truth_value:
    print("plan:", "EMPTY")
else:
    print("plan:", Pmod.PrettyPlanChain(plan, final_registry)())
    derivation_pair = Pmod.BuildDerivation(Pmod.NormalizeKnowledge(start, final_registry)(), plan, final_registry)()
    derivation = M.Head(derivation_pair)()
    final_registry = M.Head(M.Tail(derivation_pair)())()
    print("derivation-end:", M.PrettyTerm(Pmod.DerivationEnd(derivation, final_registry)(), final_registry)())
