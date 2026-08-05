import multiprocessing
import sys
import time
import traceback

from runtime import boot_from_packs
from main import PACK_PATHS, _runtime_namespace
import machine as M
import proof as Pmod
import search as Smod


if __name__ == "__main__":
    pack_name = "geometry"
    obligation_specs = (
        ("side alpha", "tao_problem_1_1_triangle", "tao_side_alpha_from_area_perimeter"),
        ("side beta", "tao_side_beta", "tao_side_beta_from_area_perimeter"),
        ("side gamma", "tao_side_gamma", "tao_side_gamma_from_area_perimeter"),
        ("angle alpha", "tao_angle_alpha", "tao_angle_alpha_from_sides"),
        ("angle beta", "tao_angle_beta", "tao_angle_beta_from_sides"),
        ("angle gamma", "tao_angle_gamma", "tao_angle_gamma_from_sides"),
        ("perimeter identity", "tao_perimeter_identity", "tao_verify_perimeter"),
        ("area identity", "tao_area_identity", "tao_verify_area"),
        ("side alpha positive", "tao_positive_alpha_side", "tao_verify_positive_alpha_side"),
        ("side beta positive", "tao_positive_beta_side", "tao_verify_positive_beta_side"),
        ("side gamma positive", "tao_positive_gamma_side", "tao_verify_positive_gamma_side"),
        ("strict triangle inequality", "tao_strict_triangle_inequality", "tao_verify_strict_triangle_inequality"),
        ("cosine identity alpha", "tao_cosine_alpha_identity", "tao_verify_cosine_alpha"),
        ("cosine identity beta", "tao_cosine_beta_identity", "tao_verify_cosine_beta"),
        ("cosine identity gamma", "tao_cosine_gamma_identity", "tao_verify_cosine_gamma"),
    )

    Pmod.SetDebugTrace(M.truth_value)()
    print("SEARCHDFS-TEST: pid", multiprocessing.current_process().pid)
    print("SEARCHDFS-TEST: boot start")
    sys.stdout.flush()
    boot_started_at = time.time()
    runtime, packs = boot_from_packs(PACK_PATHS, _runtime_namespace())
    boot_elapsed = time.time() - boot_started_at
    print("SEARCHDFS-TEST: boot complete; elapsed=", round(boot_elapsed, 3), "s")

    registry = M.FromContextGetConstructors(runtime.graph)()
    runtime.graph._search_disable_console = M.truth_value
    runtime.graph._search_probe_disable_applicable_cache = M.false_value
    runtime.graph._search_probe_disable_applicable_shards = M.truth_value
    runtime.graph._search_probe_disable_anchor_meta = M.truth_value
    print("SEARCHDFS-TEST: debug trace enabled")
    print("SEARCHDFS-TEST: multiprocessing start method=", multiprocessing.get_start_method())
    print("SEARCHDFS-TEST: applicability workers disabled; direct obligation rules run in-process")

    pack = packs.by_name(pack_name)
    first_example = pack.examples[obligation_specs[0][1]]
    start = first_example[0]
    print("SEARCHDFS-TEST: problem=triangle with given area, perimeter, arithmetic-progression side constraint, and feasibility constraints")
    obligation_count = 15
    print("SEARCHDFS-TEST: required proof obligations=", obligation_count)

    obligation_index = 0
    for obligation_spec in obligation_specs:
        obligation_index = obligation_index + 1
        obligation_example = pack.examples[obligation_spec[1]]
        print(
            "SEARCHDFS-TEST: target",
            obligation_index,
            "of",
            obligation_count,
            obligation_spec[0],
            "=",
            M.PrettyTerm(obligation_example[1], registry)(),
        )
    sys.stdout.flush()

    print("SEARCHDFS-TEST: normalize shared start")
    sys.stdout.flush()
    normalize_started_at = time.time()
    normalized_start = Pmod.NormalizeKnowledge(start, registry)()
    normalize_elapsed = time.time() - normalize_started_at
    print(
        "SEARCHDFS-TEST: normalization complete; elapsed=",
        round(normalize_elapsed, 3),
        "s facts=",
        M.CountRep(M.KnowledgeFacts(normalized_start)())(),
    )

    ordered_rules_reversed = M.EmptyList
    for obligation_spec in obligation_specs:
        ordered_rules_reversed = M.Pair(pack.rule_map[obligation_spec[2]], ordered_rules_reversed)
    ordered_rules = M.Reverse(ordered_rules_reversed)()

    final_example = pack.examples["tao_cosine_gamma_identity"]
    normalized_goal = Pmod.NormalizeKnowledge(final_example[1], registry)()
    direct_heuristic = M.Heuristic(
        M.DFSLabel,
        M.InsertionOrderLabel,
        M.Zero,
        M.one,
        M.one,
        M.one,
    )()

    print("SEARCHDFS-TEST: search start; selected-rules=", M.CountRep(ordered_rules)())
    print("SEARCHDFS-TEST: search completion target=", M.PrettyTerm(normalized_goal, registry)())
    sys.stdout.flush()
    search_started_at = time.time()
    try:
        search_pair = Smod.SearchDFS(
            runtime.graph,
            normalized_start,
            normalized_goal,
            ordered_rules,
            direct_heuristic,
            registry,
        )()
    except Exception as error:
        print("SEARCHDFS-TEST: exception", str(error))
        print(traceback.format_exc())
        sys.stdout.flush()
        raise
    search_elapsed = time.time() - search_started_at

    plan = M.Head(search_pair)()
    search_cost = M.Head(M.Tail(search_pair)())()
    final_registry = M.FromContextGetConstructors(runtime.graph)()
    outcome = Smod.SearchCostOutcome(search_cost)()

    print("SEARCHDFS-TEST: search complete; elapsed=", round(search_elapsed, 3), "s")
    print("SEARCHDFS-TEST: status=", Smod.SearchStatusText(outcome)())
    print("SEARCHDFS-TEST: expanded=", M.PrettyTerm(Smod.SearchCostExpanded(search_cost)(), final_registry)())
    print("SEARCHDFS-TEST: generated=", M.PrettyTerm(Smod.SearchCostGenerated(search_cost)(), final_registry)())
    print("SEARCHDFS-TEST: frontier-peak=", M.PrettyTerm(Smod.SearchCostFrontierPeak(search_cost)(), final_registry)())
    print("SEARCHDFS-TEST: found-depth=", M.PrettyTerm(Smod.SearchCostFoundDepth(search_cost)(), final_registry)())

    all_succeeded = M.truth_value
    derivation_end = normalized_start
    if M.IdentityCompare(outcome, M.SearchSuccessLabel)() is M.false_value:
        all_succeeded = M.false_value
        print("SEARCHDFS-TEST: search did not reach the final concrete obligation")
    elif M.Compare(plan, M.EmptyList)() is M.truth_value:
        all_succeeded = M.false_value
        print("SEARCHDFS-TEST: search returned an empty proof plan")
    else:
        derivation_pair = Pmod.BuildDerivation(normalized_start, plan, final_registry)()
        derivation = M.Head(derivation_pair)()
        derivation_registry = M.Head(M.Tail(derivation_pair)())()
        derivation_end = Pmod.DerivationEnd(derivation, derivation_registry)()
        final_registry = derivation_registry
        print("SEARCHDFS-TEST: derived proof steps=", M.CountRep(plan)())

    obligation_index = 0
    while obligation_index != len(obligation_specs):
        obligation_spec = obligation_specs[obligation_index]
        obligation_example = pack.examples[obligation_spec[1]]
        normalized_obligation = Pmod.NormalizeKnowledge(obligation_example[1], final_registry)()
        obligation_facts = M.KnowledgeFacts(derivation_end)()
        obligation_proved = M.false_value
        while M.IdentityCompare(obligation_facts, M.EmptyList)() is M.false_value:
            if M.TermEqual(M.Head(obligation_facts)(), normalized_obligation)() is M.truth_value:
                obligation_proved = M.truth_value
                obligation_facts = M.EmptyList
            else:
                obligation_facts = M.Tail(obligation_facts)()
        if M.IdentityCompare(obligation_proved, M.truth_value)() is M.truth_value:
            print("SEARCHDFS-TEST: PROVED", obligation_spec[0], "=", M.PrettyTerm(normalized_obligation, final_registry)())
        else:
            all_succeeded = M.false_value
            print("SEARCHDFS-TEST: MISSING", obligation_spec[0], "=", M.PrettyTerm(normalized_obligation, final_registry)())
        obligation_index = obligation_index + 1

    sys.stdout.flush()
    if M.IdentityCompare(all_succeeded, M.truth_value)() is M.truth_value:
        print("DONE")
    else:
        raise RuntimeError("Tao Problem 1.1 proof obligations are incomplete")
