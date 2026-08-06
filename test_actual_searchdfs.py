from __future__ import annotations

import multiprocessing
import os
import subprocess
import sys
import time
import traceback

try:
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass

if __package__ in (None, ""):
    IMPORT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    PACKAGE_NAME = os.path.basename(os.path.abspath(os.path.dirname(__file__)))
    CHILD_ARGS = [sys.executable, "-m", PACKAGE_NAME + ".test_actual_searchdfs"]
    ARG_INDEX = 1
    while ARG_INDEX != len(sys.argv):
        CHILD_ARGS.append(sys.argv[ARG_INDEX])
        ARG_INDEX = ARG_INDEX + 1
    CHILD_ENV = os.environ.copy()
    CHILD_ENV["PYTHONPATH"] = IMPORT_ROOT
    CHILD = subprocess.run(CHILD_ARGS, cwd=IMPORT_ROOT, env=CHILD_ENV)
    raise SystemExit(CHILD.returncode)

from .runtime import boot_from_packs
from .main import PACK_PATHS, _runtime_namespace
from . import knowledge as Kmod
from . import machine as M
from . import proof as Pmod
from . import search as Smod


if __name__ == "__main__":
    Pmod.SetDebugTrace(M.truth_value)()
    print("SEARCHDFS-TEST: pid", multiprocessing.current_process().pid)
    print("SEARCHDFS-TEST: boot start")
    boot_started_at = time.time()
    runtime, packs = boot_from_packs(PACK_PATHS, _runtime_namespace())
    boot_elapsed = time.time() - boot_started_at
    print("SEARCHDFS-TEST: boot elapsed", round(boot_elapsed, 3))

    registry = M.FromContextGetConstructors(runtime.graph)()
    runtime.graph._search_disable_console = M.truth_value
    runtime.graph._search_disable_progress_ticker = M.truth_value
    runtime.graph._search_probe_disable_applicable_cache = M.false_value
    runtime.graph._search_probe_disable_applicable_shards = M.false_value
    runtime.graph._search_probe_disable_anchor_meta = M.truth_value
    print("SEARCHDFS-TEST: debug trace enabled")
    print("SEARCHDFS-TEST: multiprocessing start method", multiprocessing.get_start_method())

    pack = packs.by_name("geometry")

    example_1 = pack.examples["tao_problem_1_1_triangle"]
    goal_2_example = pack.examples["tao_side_beta"]
    goal_3_example = pack.examples["tao_side_gamma"]
    goal_4_example = pack.examples["tao_angle_alpha"]
    goal_5_example = pack.examples["tao_angle_beta"]
    goal_6_example = pack.examples["tao_angle_gamma"]
    goal_7_example = pack.examples["tao_perimeter_identity"]
    goal_8_example = pack.examples["tao_area_identity"]
    goal_9_example = pack.examples["tao_positive_alpha_side"]
    goal_10_example = pack.examples["tao_positive_beta_side"]
    goal_11_example = pack.examples["tao_positive_gamma_side"]
    goal_12_example = pack.examples["tao_strict_triangle_inequality"]
    goal_13_example = pack.examples["tao_cosine_alpha_identity"]
    goal_14_example = pack.examples["tao_cosine_beta_identity"]
    goal_15_example = pack.examples["tao_cosine_gamma_identity"]

    start, goal_1_raw = example_1
    _ignored_start_2, goal_2_raw = goal_2_example
    _ignored_start_3, goal_3_raw = goal_3_example
    _ignored_start_4, goal_4_raw = goal_4_example
    _ignored_start_5, goal_5_raw = goal_5_example
    _ignored_start_6, goal_6_raw = goal_6_example
    _ignored_start_7, goal_7_raw = goal_7_example
    _ignored_start_8, goal_8_raw = goal_8_example
    _ignored_start_9, goal_9_raw = goal_9_example
    _ignored_start_10, goal_10_raw = goal_10_example
    _ignored_start_11, goal_11_raw = goal_11_example
    _ignored_start_12, goal_12_raw = goal_12_example
    _ignored_start_13, goal_13_raw = goal_13_example
    _ignored_start_14, goal_14_raw = goal_14_example
    _ignored_start_15, goal_15_raw = goal_15_example

    print("SEARCHDFS-TEST: problem=triangle with given area, perimeter, arithmetic-progression side constraint, feasibility constraints")
    print("SEARCHDFS-TEST: required proof obligations=15")
    print("SEARCHDFS-TEST: target 1 of 15 side alpha")
    print("SEARCHDFS-TEST: target 2 of 15 side beta")
    print("SEARCHDFS-TEST: target 3 of 15 side gamma")
    print("SEARCHDFS-TEST: target 4 of 15 angle alpha")
    print("SEARCHDFS-TEST: target 5 of 15 angle beta")
    print("SEARCHDFS-TEST: target 6 of 15 angle gamma")
    print("SEARCHDFS-TEST: target 7 of 15 perimeter identity")
    print("SEARCHDFS-TEST: target 8 of 15 area identity")
    print("SEARCHDFS-TEST: target 9 of 15 side alpha positive")
    print("SEARCHDFS-TEST: target 10 of 15 side beta positive")
    print("SEARCHDFS-TEST: target 11 of 15 side gamma positive")
    print("SEARCHDFS-TEST: target 12 of 15 strict triangle inequality")
    print("SEARCHDFS-TEST: target 13 of 15 cosine identity alpha")
    print("SEARCHDFS-TEST: target 14 of 15 cosine identity beta")
    print("SEARCHDFS-TEST: target 15 of 15 cosine identity gamma")

    print("SEARCHDFS-TEST: start normalize")
    normalize_started_at = time.time()
    normalized_start = Pmod.NormalizeKnowledge(start, registry)()
    normalized_goal_15 = Pmod.NormalizeKnowledge(goal_15_raw, registry)()
    normalize_elapsed = time.time() - normalize_started_at
    print("SEARCHDFS-TEST: normalize elapsed", round(normalize_elapsed, 3))
    print("SEARCHDFS-TEST: normalized shared start ready")
    print("SEARCHDFS-TEST: normalized final goal ready")

    print("SEARCHDFS-TEST: build selected rules")
    ordered_rules = M.Pair(
        pack.rule_map["tao_side_alpha_from_area_perimeter"],
        M.Pair(
            pack.rule_map["tao_side_beta_from_area_perimeter"],
            M.Pair(
                pack.rule_map["tao_side_gamma_from_area_perimeter"],
                M.Pair(
                    pack.rule_map["tao_angle_alpha_from_sides"],
                    M.Pair(
                        pack.rule_map["tao_angle_beta_from_sides"],
                        M.Pair(
                            pack.rule_map["tao_angle_gamma_from_sides"],
                            M.Pair(
                                pack.rule_map["tao_verify_perimeter"],
                                M.Pair(
                                    pack.rule_map["tao_verify_area"],
                                    M.Pair(
                                        pack.rule_map["tao_verify_positive_alpha_side"],
                                        M.Pair(
                                            pack.rule_map["tao_verify_positive_beta_side"],
                                            M.Pair(
                                                pack.rule_map["tao_verify_positive_gamma_side"],
                                                M.Pair(
                                                    pack.rule_map["tao_verify_strict_triangle_inequality"],
                                                    M.Pair(
                                                        pack.rule_map["tao_verify_cosine_alpha"],
                                                        M.Pair(
                                                            pack.rule_map["tao_verify_cosine_beta"],
                                                            M.Pair(
                                                                pack.rule_map["tao_verify_cosine_gamma"],
                                                                M.EmptyList,
                                                            ),
                                                        ),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )

    print("SEARCHDFS-TEST: selected rules built")
    compiled_text = "no"
    if M.IdentityCompare(ordered_rules, M.EmptyList)() is M.false_value:
        if Pmod.IsCompiledRule(M.Head(runtime.ordered_rules())())() is M.truth_value:
            compiled_text = "yes"
    print("SEARCHDFS-TEST: ordered rules compiled", compiled_text)
    print("SEARCHDFS-TEST: search start")

    direct_heuristic = M.Heuristic(
        M.DFSLabel,
        M.InsertionOrderLabel,
        M.Zero,
        M.one,
        M.one,
        M.Zero,
    )()

    search_started_at = time.time()
    try:
        search_pair = Smod.SearchDFS(
            runtime.graph,
            normalized_start,
            normalized_goal_15,
            ordered_rules,
            direct_heuristic,
            registry,
        )()
    except Exception as error:
        print("SEARCHDFS-TEST: exception", str(error))
        print(traceback.format_exc())
        raise
    search_elapsed = time.time() - search_started_at

    plan = M.Head(search_pair)()
    search_cost = M.Head(M.Tail(search_pair)())()
    final_registry = M.FromContextGetConstructors(runtime.graph)()
    outcome = Smod.SearchCostOutcome(search_cost)()
    status_text = "OTHER"
    if M.IdentityCompare(outcome, M.SearchSuccessLabel)() is M.truth_value:
        status_text = "SUCCESS"
    else:
        if M.IdentityCompare(outcome, M.SearchFailureLabel)() is M.truth_value:
            status_text = "FAILURE"
        else:
            if M.IdentityCompare(outcome, M.SearchPausedLabel)() is M.truth_value:
                status_text = "PAUSED"
            else:
                if M.IdentityCompare(outcome, M.SearchTimedOutLabel)() is M.truth_value:
                    status_text = "TIMED_OUT"
                else:
                    if M.IdentityCompare(outcome, M.SearchAbortedByUserLabel)() is M.truth_value:
                        status_text = "ABORTED"

    print("SEARCHDFS-TEST: search elapsed", round(search_elapsed, 3))
    print("SEARCHDFS-TEST: status", status_text)
    print("SEARCHDFS-TEST: expanded", M.PrettyTerm(Smod.SearchCostExpanded(search_cost)(), final_registry)())
    print("SEARCHDFS-TEST: generated", M.PrettyTerm(Smod.SearchCostGenerated(search_cost)(), final_registry)())
    print("SEARCHDFS-TEST: frontier_peak", M.PrettyTerm(Smod.SearchCostFrontierPeak(search_cost)(), final_registry)())
    print("SEARCHDFS-TEST: found_depth", M.PrettyTerm(Smod.SearchCostFoundDepth(search_cost)(), final_registry)())

    all_succeeded = M.truth_value
    derivation_end = normalized_start
    derivation_exact_trie = M.EmptyTree

    if M.IdentityCompare(outcome, M.SearchSuccessLabel)() is M.false_value:
        all_succeeded = M.false_value
        print("SEARCHDFS-TEST: search did not reach the final concrete obligation")
    else:
        if M.Compare(plan, M.EmptyList)() is M.truth_value:
            all_succeeded = M.false_value
            print("SEARCHDFS-TEST: search returned an empty proof plan")
        else:
            print("SEARCHDFS-TEST: plan", Pmod.PrettyPlanChain(plan, final_registry)())
            derivation_pair = Pmod.BuildDerivation(normalized_start, plan, final_registry)()
            derivation = M.Head(derivation_pair)()
            derivation_registry = M.Head(M.Tail(derivation_pair)())()
            derivation_end = Pmod.DerivationEnd(derivation, derivation_registry)()
            final_registry = derivation_registry
            if Pmod.IsKnowledge(derivation_end)() is M.truth_value:
                derivation_exact_trie = Kmod.KnowledgeTrieInsertChain(
                    M.EmptyTree,
                    Pmod.KnowledgeFacts(derivation_end)(),
                    final_registry,
                )()
            print("SEARCHDFS-TEST: derivation_end", M.PrettyTerm(derivation_end, final_registry)())

    print("SEARCHDFS-TEST: normalize obligation checks")
    normalized_goal_1 = Pmod.NormalizeKnowledge(goal_1_raw, final_registry)()
    normalized_goal_2 = Pmod.NormalizeKnowledge(goal_2_raw, final_registry)()
    normalized_goal_3 = Pmod.NormalizeKnowledge(goal_3_raw, final_registry)()
    normalized_goal_4 = Pmod.NormalizeKnowledge(goal_4_raw, final_registry)()
    normalized_goal_5 = Pmod.NormalizeKnowledge(goal_5_raw, final_registry)()
    normalized_goal_6 = Pmod.NormalizeKnowledge(goal_6_raw, final_registry)()
    normalized_goal_7 = Pmod.NormalizeKnowledge(goal_7_raw, final_registry)()
    normalized_goal_8 = Pmod.NormalizeKnowledge(goal_8_raw, final_registry)()
    normalized_goal_9 = Pmod.NormalizeKnowledge(goal_9_raw, final_registry)()
    normalized_goal_10 = Pmod.NormalizeKnowledge(goal_10_raw, final_registry)()
    normalized_goal_11 = Pmod.NormalizeKnowledge(goal_11_raw, final_registry)()
    normalized_goal_12 = Pmod.NormalizeKnowledge(goal_12_raw, final_registry)()
    normalized_goal_13 = Pmod.NormalizeKnowledge(goal_13_raw, final_registry)()
    normalized_goal_14 = Pmod.NormalizeKnowledge(goal_14_raw, final_registry)()
    normalized_goal_15 = Pmod.NormalizeKnowledge(goal_15_raw, final_registry)()

    proved_1 = M.false_value
    if Pmod.IsKnowledge(derivation_end)() is M.truth_value:
        proved_1 = Kmod.KnowledgeTrieHasFact(derivation_exact_trie, normalized_goal_1, final_registry)()
    if M.IdentityCompare(proved_1, M.truth_value)() is M.truth_value:
        print("SEARCHDFS-TEST: PROVED side alpha", M.PrettyTerm(normalized_goal_1, final_registry)())
    else:
        all_succeeded = M.false_value
        print("SEARCHDFS-TEST: MISSING side alpha", M.PrettyTerm(normalized_goal_1, final_registry)())

    proved_2 = M.false_value
    if Pmod.IsKnowledge(derivation_end)() is M.truth_value:
        proved_2 = Kmod.KnowledgeTrieHasFact(derivation_exact_trie, normalized_goal_2, final_registry)()
    if M.IdentityCompare(proved_2, M.truth_value)() is M.truth_value:
        print("SEARCHDFS-TEST: PROVED side beta", M.PrettyTerm(normalized_goal_2, final_registry)())
    else:
        all_succeeded = M.false_value
        print("SEARCHDFS-TEST: MISSING side beta", M.PrettyTerm(normalized_goal_2, final_registry)())

    proved_3 = M.false_value
    if Pmod.IsKnowledge(derivation_end)() is M.truth_value:
        proved_3 = Kmod.KnowledgeTrieHasFact(derivation_exact_trie, normalized_goal_3, final_registry)()
    if M.IdentityCompare(proved_3, M.truth_value)() is M.truth_value:
        print("SEARCHDFS-TEST: PROVED side gamma", M.PrettyTerm(normalized_goal_3, final_registry)())
    else:
        all_succeeded = M.false_value
        print("SEARCHDFS-TEST: MISSING side gamma", M.PrettyTerm(normalized_goal_3, final_registry)())

    proved_4 = M.false_value
    if Pmod.IsKnowledge(derivation_end)() is M.truth_value:
        proved_4 = Kmod.KnowledgeTrieHasFact(derivation_exact_trie, normalized_goal_4, final_registry)()
    if M.IdentityCompare(proved_4, M.truth_value)() is M.truth_value:
        print("SEARCHDFS-TEST: PROVED angle alpha", M.PrettyTerm(normalized_goal_4, final_registry)())
    else:
        all_succeeded = M.false_value
        print("SEARCHDFS-TEST: MISSING angle alpha", M.PrettyTerm(normalized_goal_4, final_registry)())

    proved_5 = M.false_value
    if Pmod.IsKnowledge(derivation_end)() is M.truth_value:
        proved_5 = Kmod.KnowledgeTrieHasFact(derivation_exact_trie, normalized_goal_5, final_registry)()
    if M.IdentityCompare(proved_5, M.truth_value)() is M.truth_value:
        print("SEARCHDFS-TEST: PROVED angle beta", M.PrettyTerm(normalized_goal_5, final_registry)())
    else:
        all_succeeded = M.false_value
        print("SEARCHDFS-TEST: MISSING angle beta", M.PrettyTerm(normalized_goal_5, final_registry)())

    proved_6 = M.false_value
    if Pmod.IsKnowledge(derivation_end)() is M.truth_value:
        proved_6 = Kmod.KnowledgeTrieHasFact(derivation_exact_trie, normalized_goal_6, final_registry)()
    if M.IdentityCompare(proved_6, M.truth_value)() is M.truth_value:
        print("SEARCHDFS-TEST: PROVED angle gamma", M.PrettyTerm(normalized_goal_6, final_registry)())
    else:
        all_succeeded = M.false_value
        print("SEARCHDFS-TEST: MISSING angle gamma", M.PrettyTerm(normalized_goal_6, final_registry)())

    proved_7 = M.false_value
    if Pmod.IsKnowledge(derivation_end)() is M.truth_value:
        proved_7 = Kmod.KnowledgeTrieHasFact(derivation_exact_trie, normalized_goal_7, final_registry)()
    if M.IdentityCompare(proved_7, M.truth_value)() is M.truth_value:
        print("SEARCHDFS-TEST: PROVED perimeter identity", M.PrettyTerm(normalized_goal_7, final_registry)())
    else:
        all_succeeded = M.false_value
        print("SEARCHDFS-TEST: MISSING perimeter identity", M.PrettyTerm(normalized_goal_7, final_registry)())

    proved_8 = M.false_value
    if Pmod.IsKnowledge(derivation_end)() is M.truth_value:
        proved_8 = Kmod.KnowledgeTrieHasFact(derivation_exact_trie, normalized_goal_8, final_registry)()
    if M.IdentityCompare(proved_8, M.truth_value)() is M.truth_value:
        print("SEARCHDFS-TEST: PROVED area identity", M.PrettyTerm(normalized_goal_8, final_registry)())
    else:
        all_succeeded = M.false_value
        print("SEARCHDFS-TEST: MISSING area identity", M.PrettyTerm(normalized_goal_8, final_registry)())

    proved_9 = M.false_value
    if Pmod.IsKnowledge(derivation_end)() is M.truth_value:
        proved_9 = Kmod.KnowledgeTrieHasFact(derivation_exact_trie, normalized_goal_9, final_registry)()
    if M.IdentityCompare(proved_9, M.truth_value)() is M.truth_value:
        print("SEARCHDFS-TEST: PROVED side alpha positive", M.PrettyTerm(normalized_goal_9, final_registry)())
    else:
        all_succeeded = M.false_value
        print("SEARCHDFS-TEST: MISSING side alpha positive", M.PrettyTerm(normalized_goal_9, final_registry)())

    proved_10 = M.false_value
    if Pmod.IsKnowledge(derivation_end)() is M.truth_value:
        proved_10 = Kmod.KnowledgeTrieHasFact(derivation_exact_trie, normalized_goal_10, final_registry)()
    if M.IdentityCompare(proved_10, M.truth_value)() is M.truth_value:
        print("SEARCHDFS-TEST: PROVED side beta positive", M.PrettyTerm(normalized_goal_10, final_registry)())
    else:
        all_succeeded = M.false_value
        print("SEARCHDFS-TEST: MISSING side beta positive", M.PrettyTerm(normalized_goal_10, final_registry)())

    proved_11 = M.false_value
    if Pmod.IsKnowledge(derivation_end)() is M.truth_value:
        proved_11 = Kmod.KnowledgeTrieHasFact(derivation_exact_trie, normalized_goal_11, final_registry)()
    if M.IdentityCompare(proved_11, M.truth_value)() is M.truth_value:
        print("SEARCHDFS-TEST: PROVED side gamma positive", M.PrettyTerm(normalized_goal_11, final_registry)())
    else:
        all_succeeded = M.false_value
        print("SEARCHDFS-TEST: MISSING side gamma positive", M.PrettyTerm(normalized_goal_11, final_registry)())

    proved_12 = M.false_value
    if Pmod.IsKnowledge(derivation_end)() is M.truth_value:
        proved_12 = Kmod.KnowledgeTrieHasFact(derivation_exact_trie, normalized_goal_12, final_registry)()
    if M.IdentityCompare(proved_12, M.truth_value)() is M.truth_value:
        print("SEARCHDFS-TEST: PROVED strict triangle inequality", M.PrettyTerm(normalized_goal_12, final_registry)())
    else:
        all_succeeded = M.false_value
        print("SEARCHDFS-TEST: MISSING strict triangle inequality", M.PrettyTerm(normalized_goal_12, final_registry)())

    proved_13 = M.false_value
    if Pmod.IsKnowledge(derivation_end)() is M.truth_value:
        proved_13 = Kmod.KnowledgeTrieHasFact(derivation_exact_trie, normalized_goal_13, final_registry)()
    if M.IdentityCompare(proved_13, M.truth_value)() is M.truth_value:
        print("SEARCHDFS-TEST: PROVED cosine identity alpha", M.PrettyTerm(normalized_goal_13, final_registry)())
    else:
        all_succeeded = M.false_value
        print("SEARCHDFS-TEST: MISSING cosine identity alpha", M.PrettyTerm(normalized_goal_13, final_registry)())

    proved_14 = M.false_value
    if Pmod.IsKnowledge(derivation_end)() is M.truth_value:
        proved_14 = Kmod.KnowledgeTrieHasFact(derivation_exact_trie, normalized_goal_14, final_registry)()
    if M.IdentityCompare(proved_14, M.truth_value)() is M.truth_value:
        print("SEARCHDFS-TEST: PROVED cosine identity beta", M.PrettyTerm(normalized_goal_14, final_registry)())
    else:
        all_succeeded = M.false_value
        print("SEARCHDFS-TEST: MISSING cosine identity beta", M.PrettyTerm(normalized_goal_14, final_registry)())

    proved_15 = M.false_value
    if Pmod.IsKnowledge(derivation_end)() is M.truth_value:
        proved_15 = Kmod.KnowledgeTrieHasFact(derivation_exact_trie, normalized_goal_15, final_registry)()
    if M.IdentityCompare(proved_15, M.truth_value)() is M.truth_value:
        print("SEARCHDFS-TEST: PROVED cosine identity gamma", M.PrettyTerm(normalized_goal_15, final_registry)())
    else:
        all_succeeded = M.false_value
        print("SEARCHDFS-TEST: MISSING cosine identity gamma", M.PrettyTerm(normalized_goal_15, final_registry)())

    if M.IdentityCompare(all_succeeded, M.truth_value)() is M.truth_value:
        print("DONE")
    else:
        raise RuntimeError("Tao Problem 1.1 proof obligations are incomplete")
