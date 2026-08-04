import math as _stdlib_math
import multiprocessing
import sys
import time
import traceback
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
THIS_DIR_TEXT = str(THIS_DIR)
PARENT_DIR = str(THIS_DIR.parent)
sys.modules["math"] = _stdlib_math
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)
trimmed_path = []
path_index = 0
while path_index != len(sys.path):
    path_entry = sys.path[path_index]
    if path_entry != THIS_DIR_TEXT:
        trimmed_path.append(path_entry)
    path_index = path_index + 1
sys.path = trimmed_path

from hyge.runtime import boot_from_packs
from hyge.main import PACK_PATHS, _runtime_namespace
from hyge import machine as M
from hyge import proof as Pmod
from hyge import search as Smod


def _status_text(search_cost):
    outcome = Smod.SearchCostOutcome(search_cost)()
    if M.IdentityCompare(outcome, M.SearchSuccessLabel)() is M.truth_value:
        return "SUCCESS"
    if M.IdentityCompare(outcome, M.SearchFailureLabel)() is M.truth_value:
        return "FAILURE"
    if M.IdentityCompare(outcome, M.SearchPausedLabel)() is M.truth_value:
        return "PAUSED"
    if M.IdentityCompare(outcome, M.SearchTimedOutLabel)() is M.truth_value:
        return "TIMED_OUT"
    if M.IdentityCompare(outcome, M.SearchAbortedByUserLabel)() is M.truth_value:
        return "ABORTED"
    return "OTHER"


def main():
    pack_name = "geometry"
    example_name = "tao_problem_1_1_triangle"

    if len(sys.argv) != 1:
        if len(sys.argv) == 2:
            example_name = sys.argv[1]
        else:
            pack_name = sys.argv[1]
            example_name = sys.argv[2]

    Pmod.SetDebugTrace(M.truth_value)()
    print("SEARCHDFS-TEST: pid", multiprocessing.current_process().pid, flush=True)
    print("SEARCHDFS-TEST: boot start", flush=True)
    boot_started_at = time.time()
    runtime, packs = boot_from_packs(PACK_PATHS, _runtime_namespace())
    boot_elapsed = time.time() - boot_started_at
    print("SEARCHDFS-TEST: boot elapsed", round(boot_elapsed, 3), flush=True)

    registry = M.FromContextGetConstructors(runtime.graph)()
    runtime.graph._search_disable_console = M.truth_value
    runtime.graph._search_probe_disable_applicable_cache = M.false_value
    runtime.graph._search_probe_disable_applicable_shards = M.false_value
    runtime.graph._search_probe_disable_anchor_meta = M.truth_value
    print("SEARCHDFS-TEST: debug trace enabled", flush=True)
    print("SEARCHDFS-TEST: multiprocessing start method", multiprocessing.get_start_method(), flush=True)

    pack = packs.by_name(pack_name)
    example = pack.examples[example_name]
    start = example[0]
    goal = example[1]

    print("SEARCHDFS-TEST: start normalize", flush=True)
    normalize_started_at = time.time()
    normalized_start = Pmod.NormalizeKnowledge(start, registry)()
    normalized_goal = Pmod.NormalizeKnowledge(goal, registry)()
    normalize_elapsed = time.time() - normalize_started_at
    print("SEARCHDFS-TEST: normalize elapsed", round(normalize_elapsed, 3), flush=True)
    print("SEARCHDFS-TEST: normalized start", M.PrettyTerm(normalized_start, registry)(), flush=True)
    print("SEARCHDFS-TEST: normalized goal", M.PrettyTerm(normalized_goal, registry)(), flush=True)

    ordered_rules = runtime.ordered_rules()
    compiled_text = "no"
    if M.IdentityCompare(ordered_rules, M.EmptyList)() is M.false_value:
        if Pmod.IsCompiledRule(M.Head(ordered_rules)())() is M.truth_value:
            compiled_text = "yes"
    print("SEARCHDFS-TEST: ordered rules compiled", compiled_text, flush=True)

    print("SEARCHDFS-TEST: search start", flush=True)
    search_started_at = time.time()
    try:
        search_pair = Smod.SearchDFS(
            runtime.graph,
            normalized_start,
            normalized_goal,
            ordered_rules,
            runtime.theorem_heuristic,
            registry,
        )()
    except Exception as error:
        print("SEARCHDFS-TEST: exception", error.__class__.__name__, flush=True)
        print(traceback.format_exc(), flush=True)
        raise
    search_elapsed = time.time() - search_started_at

    plan = M.Head(search_pair)()
    search_cost = M.Head(M.Tail(search_pair)())()
    final_registry = M.FromContextGetConstructors(runtime.graph)()

    print("SEARCHDFS-TEST: search elapsed", round(search_elapsed, 3), flush=True)
    print("SEARCHDFS-TEST: status", _status_text(search_cost), flush=True)
    print("SEARCHDFS-TEST: expanded", M.PrettyTerm(Smod.SearchCostExpanded(search_cost)(), final_registry)(), flush=True)
    print("SEARCHDFS-TEST: generated", M.PrettyTerm(Smod.SearchCostGenerated(search_cost)(), final_registry)(), flush=True)
    print("SEARCHDFS-TEST: frontier_peak", M.PrettyTerm(Smod.SearchCostFrontierPeak(search_cost)(), final_registry)(), flush=True)
    print("SEARCHDFS-TEST: found_depth", M.PrettyTerm(Smod.SearchCostFoundDepth(search_cost)(), final_registry)(), flush=True)

    plan_is_empty = M.Compare(plan, M.EmptyList)() is M.truth_value
    if plan_is_empty:
        print("SEARCHDFS-TEST: plan EMPTY", flush=True)
    else:
        print("SEARCHDFS-TEST: plan", Pmod.PrettyPlanChain(plan, final_registry)(), flush=True)
        derivation_pair = Pmod.BuildDerivation(normalized_start, plan, final_registry)()
        derivation = M.Head(derivation_pair)()
        derivation_registry = M.Head(M.Tail(derivation_pair)())()
        print(
            "SEARCHDFS-TEST: derivation_end",
            M.PrettyTerm(Pmod.DerivationEnd(derivation, derivation_registry)(), derivation_registry)(),
            flush=True,
        )

    print("SEARCHDFS-TEST: done", flush=True)


if __name__ == "__main__":
    main()
