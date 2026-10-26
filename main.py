from __future__ import annotations

import argparse
import http.server
import json
import multiprocessing
import os
import subprocess
import sys
import time
import urllib.parse
import webbrowser

if __package__ in (None, ""):
    IMPORT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    PACKAGE_NAME = os.path.basename(os.path.abspath(os.path.dirname(__file__)))
    CHILD_ARGS = [sys.executable, "-m", PACKAGE_NAME + ".main"]
    ARG_INDEX = 1
    while ARG_INDEX != len(sys.argv):
        CHILD_ARGS.append(sys.argv[ARG_INDEX])
        ARG_INDEX = ARG_INDEX + 1
    CHILD_ENV = os.environ.copy()
    CHILD_ENV["PYTHONPATH"] = IMPORT_ROOT
    CHILD = subprocess.run(CHILD_ARGS, cwd=IMPORT_ROOT, env=CHILD_ENV)
    raise SystemExit(CHILD.returncode)
else:
    from .math import arithmetic as A
    from . import graph as G
    from . import heuristics as Hmod
    from . import labels as Lmod
    from . import machine as M
    from . import matching as X
    from . import proof as P
    from . import rewrite_rules as R
    from .runtime import boot_from_packs, boot_from_snapshot, make_fresh_runtime, save_runtime
    from .persistence import SnapshotCodec
    from . import invariance as Imod
    from . import search as Smod
    from . import theorem_rules as T
    from . import surface_bridge as SB
    from . import graph_task as GT
    from . import checker_b as CB
    from . import invariant_miner as Miner
    from . import evaluator as Eval
    from . import promotion_ledger as PL
    from . import playground as PG
    from . import story_renderer as SR
    from . import dialogue as Dlg
    from .consensus import (
        AcceptEntryDelivery,
        ConsensusPeer,
        EntryReceiptVerdict,
        FreshPeer,
        OfferLedgerSnapshot,
        PeerLedger,
        PeersAgree,
    )
    from .packs import PackLoader
    from .testsuite import install_default_tests


PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
PACK_DIR = os.path.join(PACKAGE_DIR, "packs")
SNAPSHOT_DIR = os.path.join(PACKAGE_DIR, "snapshots")
INSPECTOR_DIR = os.path.join(PACKAGE_DIR, "inspector")
SNAPSHOT_NAME = "hyge_snapshot_v8.json"
INSPECTOR_DEFAULT_PORT = 8765
INSPECTOR_DEFAULT_MAX_RULE_EDGES = 80
PACK_PATHS = [
    os.path.join(PACK_DIR, "order-sign.pack.yaml"),
    os.path.join(PACK_DIR, "sqrt-real.pack.yaml"),
    os.path.join(PACK_DIR, "algebra-distribute.pack.yaml"),
    os.path.join(PACK_DIR, "sequence-order.pack.yaml"),
    os.path.join(PACK_DIR, "real-closure.pack.yaml"),
    os.path.join(PACK_DIR, "arithmetic.pack.yaml"),
    os.path.join(PACK_DIR, "geometry-ontology.pack.yaml"),
    os.path.join(PACK_DIR, "trigonometry.pack.yaml"),
    os.path.join(PACK_DIR, "geometry.pack.yaml"),
    os.path.join(PACK_DIR, "engel-coins.pack.yaml"),
    os.path.join(PACK_DIR, "engel-means.pack.yaml"),
    os.path.join(PACK_DIR, "engel-blackboard.pack.yaml"),
    os.path.join(PACK_DIR, "engel-strategies.pack.yaml"),
    os.path.join(PACK_DIR, "geometry-constructions.pack.yaml"),
    os.path.join(PACK_DIR, "funceq-nt.pack.yaml"),
    os.path.join(PACK_DIR, "infinite-descent.pack.yaml"),
    os.path.join(PACK_DIR, "nat-order.pack.yaml"),
]

def _latest_snapshot_path():
    current_path = os.path.join(SNAPSHOT_DIR, "hyge_snapshot_current.json")
    if os.path.exists(current_path):
        return current_path
    try:
        names = os.listdir(SNAPSHOT_DIR)
    except OSError:
        names = []
    best_version = -1
    best_name = ""
    prefix = "hyge_snapshot_v"
    suffix = ".json"
    for name in names:
        if not name.startswith(prefix):
            continue
        if not name.endswith(suffix):
            continue
        version_text = name[len(prefix) : -len(suffix)]
        if not version_text.isdigit():
            continue
        version = int(version_text)
        if version > best_version:
            best_version = version
            best_name = name
    if best_name:
        return os.path.join(SNAPSHOT_DIR, best_name)
    return os.path.join(SNAPSHOT_DIR, SNAPSHOT_NAME)


SNAPSHOT_PATH = _latest_snapshot_path()


class PausedSearchRequested(RuntimeError):
    def __init__(self, label, job, elapsed):
        self.label = label
        self.job = job
        self.elapsed = elapsed
        super().__init__(label)


class PausedComparisonRequested(RuntimeError):
    def __init__(self, label, comparison_job, elapsed):
        self.label = label
        self.comparison_job = comparison_job
        self.elapsed = elapsed
        super().__init__(label)


def _first_paused_search_comparison_job(graph):
    comparison_jobs = graph.search_comparison_jobs
    while M.IdentityCompare(comparison_jobs, M.EmptyList)() is M.false_value:
        comparison_job = M.Head(comparison_jobs)()
        if M.IdentityCompare(Smod.SearchComparisonJobOutcome(comparison_job)(), M.SearchPausedLabel)() is M.truth_value:
            return comparison_job
        comparison_jobs = M.Tail(comparison_jobs)()
    return M.EmptyList


def _first_paused_search_job(graph):
    jobs = M.FromContextGetSearchJobs(graph)()
    while M.IdentityCompare(jobs, M.EmptyList)() is M.false_value:
        job = M.Head(jobs)()
        if M.IdentityCompare(Smod.SearchJobStatus(job)(), M.SearchPausedLabel)() is M.truth_value:
            return job
        jobs = M.Tail(jobs)()
    return M.EmptyList


def _search_job_mode_text(job):
    mode = Hmod.HeuristicSearchMode(Smod.SearchJobHeuristic(job)())()
    return Smod.SearchModeText(mode)()


def _search_comparison_text(comparison_job):
    return "search comparison benchmark"


def _paused_job_is_compatible(job, graph):
    registry = M.FromContextGetConstructors(graph)()

    frontier = Smod.SearchJobFrontier(job)()
    frontier_ok = M.OrAtom(M.IsPair(frontier)(), M.IdentityCompare(frontier, M.EmptyList)())()
    if frontier_ok is M.false_value:
        return M.false_value

    if M.IdentityCompare(frontier, M.EmptyList)() is M.truth_value:
        return M.truth_value

    state = M.Head(frontier)()
    steps = Smod.SearchStateStepsRemaining(state)()
    if M.IsNat(steps, registry)() is M.false_value:
        return M.false_value

    cursor = Smod.SearchStateCursor(state)()
    cursor_ok = M.OrAtom(M.IsPair(cursor)(), M.IdentityCompare(cursor, M.EmptyList)())()
    if cursor_ok is M.false_value:
        return M.false_value

    return M.truth_value


def _paused_comparison_job_is_compatible(comparison_job, graph):
    states = Smod.SearchComparisonJobStates(comparison_job)()
    states_ok = M.OrAtom(M.IsPair(states)(), M.IdentityCompare(states, M.EmptyList)())()
    if states_ok is M.false_value:
        return M.false_value
    return M.truth_value


def _save_snapshot_now(runtime, runtime_namespace):
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    temp_snapshot_path = SNAPSHOT_PATH + ".tmp"
    save_runtime(runtime, temp_snapshot_path, runtime_namespace)
    os.replace(temp_snapshot_path, SNAPSHOT_PATH)
    print("saved snapshot to", SNAPSHOT_PATH)


def _debug_log(debug_flag, *args, **kwargs):
    if M.IdentityCompare(debug_flag, M.truth_value)() is M.truth_value:
        print(*args, **kwargs)


def _maybe_resume_paused_cold_search(debug: bool = False):
    debug_flag = M.truth_value if debug else M.false_value
    _debug_log(debug_flag, f"DEBUG: checking paused snapshot at {SNAPSHOT_PATH}")
    if os.path.exists(SNAPSHOT_PATH):
        snapshot_exists = M.truth_value
    else:
        snapshot_exists = M.false_value
    if snapshot_exists is M.false_value:
        _debug_log(debug_flag, "DEBUG: no paused snapshot found")
        return M.false_value

    _debug_log(debug_flag, "DEBUG: paused snapshot found, restoring")
    runtime_namespace = _runtime_namespace()
    try:
        runtime = boot_from_snapshot(SNAPSHOT_PATH, runtime_namespace, debug=debug_flag)
    except (OSError, RuntimeError, json.JSONDecodeError, ValueError, KeyError, TypeError) as error:
        print(
            "ignoring unreadable snapshot at",
            SNAPSHOT_PATH,
            "(" + error.__class__.__name__ + ": " + str(error) + ")",
        )
        try:
            bad_path = SNAPSHOT_PATH + ".bad"
            if os.path.exists(bad_path):
                os.remove(bad_path)
            os.replace(SNAPSHOT_PATH, bad_path)
            print("moved unreadable snapshot to", bad_path)
        except OSError:
            pass
        return M.false_value
    job = _first_paused_search_job(runtime.graph)
    comparison_job = _first_paused_search_comparison_job(runtime.graph)
    if M.Compare(comparison_job, M.EmptyList)() is M.false_value:
        if _paused_comparison_job_is_compatible(comparison_job, runtime.graph) is M.false_value:
            print("ignoring incompatible paused comparison snapshot at", SNAPSHOT_PATH)
            incompatible_path = SNAPSHOT_PATH + ".incompatible"
            os.replace(SNAPSHOT_PATH, incompatible_path)
            print("moved incompatible snapshot to", incompatible_path)
            return M.false_value

        comparison_text = _search_comparison_text(comparison_job)
        try:
            response = input("Oh, you're back, and apparently we have an unfinished " + comparison_text + ", would you like to resume it? ")
        except (EOFError, KeyboardInterrupt):
            response = ""

        answer = response.strip().lower()
        if answer not in ("y", "yes", "resume", "continue"):
            print("leaving paused snapshot untouched")
            return M.truth_value

        _debug_log(debug_flag, "\nDEBUG: resuming paused comparison:", comparison_text)

        start_time = time.time()
        derivation = runtime.prove(
            Smod.SearchComparisonJobStart(comparison_job)(),
            Smod.SearchComparisonJobGoal(comparison_job)(),
            Smod.SearchComparisonJobRules(comparison_job)(),
            Smod.SearchComparisonJobHeuristic(comparison_job)(),
        )
        elapsed = time.time() - start_time

        paused_comparison_again = _first_paused_search_comparison_job(runtime.graph)
        if M.Compare(paused_comparison_again, M.EmptyList)() is not M.truth_value:
            print(comparison_text + ": paused again after " + str(elapsed) + " seconds")
            _save_snapshot_now(runtime, runtime_namespace)
            return M.truth_value

        proved = M.Compare(derivation, M.EmptyList)() is not M.truth_value
        if proved:
            print(comparison_text + ": resumed, finished benchmarking, and proved the goal in " + str(elapsed) + " seconds")
        else:
            print(comparison_text + ": resumed and finished benchmarking after " + str(elapsed) + " seconds")

        _save_snapshot_now(runtime, runtime_namespace)
        return M.truth_value

    if M.Compare(job, M.EmptyList)() is M.truth_value:
        return M.false_value

    if _paused_job_is_compatible(job, runtime.graph) is M.false_value:
        print("ignoring incompatible paused snapshot at", SNAPSHOT_PATH)
        incompatible_path = SNAPSHOT_PATH + ".incompatible"
        os.replace(SNAPSHOT_PATH, incompatible_path)
        print("moved incompatible snapshot to", incompatible_path)
        return M.false_value

    mode_text = _search_job_mode_text(job)
    try:
        response = input("Oh, you're back, and apparently we have an unfinished " + mode_text + ", would you like to resume it? ")
    except (EOFError, KeyboardInterrupt):
        response = ""

    answer = response.strip().lower()
    if answer not in ("y", "yes", "resume", "continue"):
        print("leaving paused snapshot untouched")
        return M.truth_value

    _debug_log(debug_flag, "\nDEBUG: resuming paused search job:", mode_text)

    start_time = time.time()
    derivation = runtime.prove(
        Smod.SearchJobStart(job)(),
        Smod.SearchJobGoal(job)(),
        Smod.SearchJobRules(job)(),
        Smod.SearchJobHeuristic(job)(),
    )
    elapsed = time.time() - start_time

    paused_again = _first_paused_search_job(runtime.graph)
    if M.Compare(paused_again, M.EmptyList)() is not M.truth_value:
        print(mode_text + ": paused again after " + str(elapsed) + " seconds")
        _save_snapshot_now(runtime, runtime_namespace)
        return M.truth_value

    proved = M.Compare(derivation, M.EmptyList)() is not M.truth_value
    if proved:
        print(mode_text + ": resumed and finished in " + str(elapsed) + " seconds")
    else:
        print(mode_text + ": resumed and did not prove the goal after " + str(elapsed) + " seconds")

    _save_snapshot_now(runtime, runtime_namespace)
    return M.truth_value


def _runtime_namespace():
    if "NatValueIndex" not in vars(M):
        M.NatValueIndex = M.Tree(M.EmptyList)
    namespace = dict(vars(M))
    namespace.update(vars(Hmod))
    namespace.update(vars(Lmod))
    namespace.update(vars(P))
    namespace.update(vars(G))
    namespace.update(vars(X))
    namespace.update(vars(R))
    namespace.update(vars(Smod))
    namespace.update(vars(T))
    stable_machine_names = (
        "Zero",
        "one",
        "two",
        "three",
        "four",
        "five",
        "six",
        "seven",
        "eight",
        "nine",
        "ZeroLabel",
        "SuccLabel",
        "PairLabel",
        "TreeLabel",
        "NatValueIndex",
    )
    for name in stable_machine_names:
        if name in vars(M):
            namespace[name] = vars(M)[name]
    return namespace


def _print_summary(runtime, title: str):
    print(f"\n=== {title} ===")
    for key, value in runtime.summary().items():
        print(f"{key}: {value}")
    sys.stdout.flush()


def _make_isreal_sqrt_case(name, nat_atom):
    start = M.Pair(M.SqrtLabel, M.Pair(nat_atom, M.EmptyList))
    goal = M.Pair(M.IsRealLabel, M.Pair(start, M.EmptyList))
    return name, start, goal, None, None


def _make_real_closure_case(name, a, b, c):
    sqrt_a = M.Pair(M.SqrtLabel, M.Pair(a, M.EmptyList))
    sqrt_b = M.Pair(M.SqrtLabel, M.Pair(b, M.EmptyList))
    sqrt_c = M.Pair(M.SqrtLabel, M.Pair(c, M.EmptyList))
    facts = M.Pair(
        M.Pair(M.IsRealLabel, M.Pair(sqrt_a, M.EmptyList)),
        M.Pair(
            M.Pair(M.IsRealLabel, M.Pair(sqrt_b, M.EmptyList)),
            M.Pair(
                M.Pair(M.IsRealLabel, M.Pair(sqrt_c, M.EmptyList)),
                M.EmptyList,
            ),
        ),
    )
    start = M.Knowledge(facts)()
    expr = M.Pair(M.ExprAddLabel, M.Pair(sqrt_a, M.Pair(M.Pair(M.ExprMulLabel, M.Pair(sqrt_b, M.Pair(sqrt_c, M.EmptyList))), M.EmptyList)))
    goal = M.Pair(M.IsRealLabel, M.Pair(expr, M.EmptyList))
    return name, start, goal, None, None


def _theorem_agenda(packs, filter_name=None):
    cases = []
    if filter_name == None:
        filter_name = "tao"
    if filter_name in ("tao", "all"):
        geometry_pack = packs.by_name("geometry")
        if "tao_problem_1_1_triangle" in geometry_pack.examples:
            start, goal = geometry_pack.examples["tao_problem_1_1_triangle"]
            cases.append(("Tao Problem 1.1 metric structure", start, goal, None, None))
    if filter_name in ("coin", "coins", "engel", "all"):
        coin_pack = packs.by_name("engel-coins")
        if "engel_hhhhh_to_hhttt" in coin_pack.examples:
            start, goal = coin_pack.examples["engel_hhhhh_to_hhttt"]
            cases.append(("Engel coins HHHHH to HHTTT", start, goal, coin_pack.rule_chain, coin_pack.phi))
        if "engel_hhhhh_to_hhhtt" in coin_pack.examples:
            start, goal = coin_pack.examples["engel_hhhhh_to_hhhtt"]
            cases.append(("Engel coins HHHHH to HHHTT", start, goal, coin_pack.rule_chain, coin_pack.phi))
    if filter_name in ("means", "e1", "engel-means", "all"):
        means_pack = packs.by_name("engel-means")
        if "engel_e1" in means_pack.examples:
            start, goal = means_pack.examples["engel_e1"]
            cases.append(("engel_e1", start, goal, means_pack.rule_chain, means_pack.phi))
    if filter_name in ("blackboard", "e2", "engel-blackboard", "all"):
        blackboard_pack = packs.by_name("engel-blackboard")
        if "engel_e2_final_number_is_odd" in blackboard_pack.examples:
            start, goal = blackboard_pack.examples["engel_e2_final_number_is_odd"]
            cases.append(("engel_e2", start, goal, blackboard_pack.rule_chain, blackboard_pack.phi))
    if filter_name in ("sqrt", "isreal", "sqrt-real", "real", "isreal_sqrt", "isreal-sqrt", "isreal(sqrt())", "all", "sqrt2", "sqrt3", "sqrt4"):
        sqrt_pack = packs.by_name("sqrt-real")
        for example_id in ("sqrt2_real", "sqrt3_real", "sqrt4_real"):
            if filter_name in ("sqrt2", "sqrt3", "sqrt4"):
                if (filter_name + "_real" == example_id) is False:
                    continue
            if example_id in sqrt_pack.examples:
                start, goal = sqrt_pack.examples[example_id]
                cases.append((example_id, start, goal, None, None))
    return cases


def _run_theorem_agenda(runtime, cases, title, debug=None):
    print(f"\n--- {title} ---")
    results = []

    for label, start, goal, rules, phi in cases:
        if debug:
            print(f"\nDEBUG: theorem-case start: {label}")
        start_time = time.time()
        derivation = runtime.prove(start, goal, rules, None, phi)
        elapsed = time.time() - start_time
        paused_comparison = _first_paused_search_comparison_job(runtime.graph)
        if M.Compare(paused_comparison, M.EmptyList)() is not M.truth_value:
            raise PausedComparisonRequested(label, paused_comparison, elapsed)
        paused_job = _first_paused_search_job(runtime.graph)
        if M.Compare(paused_job, M.EmptyList)() is not M.truth_value:
            raise PausedSearchRequested(label, paused_job, elapsed)
        if Imod.IsUnreachable(derivation)() is M.truth_value:
            results.append((label, False, elapsed, goal, derivation))
            print(f"{label}: Unreachable in {elapsed} seconds")
        else:
            proved = M.Compare(derivation, M.EmptyList)() is not M.truth_value
            results.append((label, proved, elapsed, goal, derivation))
            if proved:
                print(f"{label}: proved in {elapsed} seconds")
            else:
                print(f"{label}: not proved after {elapsed} seconds")

    return results




def _search_worker_result_manifest_path(result_path: str):
    return result_path + ".manifest.json"


def _search_worker_mode_label(mode_text: str):
    if mode_text == "dfs":
        return M.DFSLabel
    if mode_text == "bfs":
        return M.BFSLabel
    if mode_text == "astar":
        return M.AStarLabel
    if mode_text == "beam":
        return M.BeamLabel
    if mode_text == "rewritedfs":
        return M.RewriteDFSLabel
    raise RuntimeError("unknown search-worker mode: " + mode_text)


def _search_worker_mode_heuristic(runtime, mode_text: str, registry):
    base = runtime.theorem_heuristic
    mode = _search_worker_mode_label(mode_text)
    beam_width = Hmod.HeuristicBeamWidth(base)()
    if M.IdentityCompare(mode, M.BeamLabel)() is M.truth_value:
        if M.NatEq(beam_width, M.Zero, registry)() is M.truth_value:
            beam_width = M.three
    return Hmod.Heuristic(
        mode,
        Hmod.HeuristicRuleOrder(base)(),
        beam_width,
        Hmod.HeuristicAlpha(base)(),
        Hmod.HeuristicBeta(base)(),
        Hmod.HeuristicCanonicalStrength(base)(),
    )()


def _gmp_atom_from_int(value: int):
    atom = M.Atom()
    atom.value = M.GMPRep(str(value))
    return atom


def _string_atom(text: str):
    atom = M.Atom()
    atom.value = text
    return atom


def _search_worker_problem_from_manifest(packs, result_path: str, heuristic, registry):
    cases = _theorem_agenda(packs)
    manifest_path = _search_worker_result_manifest_path(result_path)
    if os.path.exists(manifest_path) is False:
        return cases[0]
    with open(manifest_path, "r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    expected_start_text = manifest.get("start_text", "")
    expected_goal_text = manifest.get("goal_text", "")
    case_index = 0
    while case_index != len(cases):
        label, start, goal, _rules, _phi = cases[case_index]
        candidate_start = Hmod.HeuristicCanonicalize(start, heuristic, registry)()
        candidate_goal = Hmod.HeuristicCanonicalize(goal, heuristic, registry)()
        if M.PrettyTerm(candidate_start, registry)() == expected_start_text:
            if M.PrettyTerm(candidate_goal, registry)() == expected_goal_text:
                return label, start, goal
        case_index = case_index + 1
    return cases[0]


class _SearchWorkerResultGraph:
    pass




def _search_worker_result_registry(runtime, attempt, performance, worker_stage=None, worker_plan=None):
    base_registry = runtime.graph.constructor_registry
    pruned_registry = M.Tree(M.EmptyList)
    seen = set()
    stack = [attempt, performance]
    if worker_stage is not None:
        stack.append(worker_stage)
    if worker_plan is not None:
        stack.append(worker_plan)
    while stack:
        current = stack.pop()
        if current is None:
            continue
        current_identity = id(current)
        if current_identity in seen:
            continue
        seen.add(current_identity)
        try:
            if M.IsPair(current)() is M.truth_value:
                stack.append(M.Head(current)())
                stack.append(M.Tail(current)())
                continue
        except Exception:
            pass
        try:
            constructor = M.GetConstructor(current, base_registry)()
        except Exception:
            constructor = M.EmptyList
        if M.IdentityCompare(constructor, M.EmptyList)() is M.false_value:
            if M.IdentityCompare(M.TreeLookup(pruned_registry, current, base_registry)(), M.EmptyList)() is M.truth_value:
                pruned_registry = M.TreeInsert(pruned_registry, current, constructor, base_registry)()
            stack.append(M.Head(constructor)())
            stack.append(M.Tail(constructor)())
    return pruned_registry

def _search_worker_result_graph(runtime, attempt, performance, worker_stage=None, worker_plan=None):
    graph = _SearchWorkerResultGraph()
    graph.constructor_registry = _search_worker_result_registry(runtime, attempt, performance, worker_stage, worker_plan)
    graph.all_rules = M.EmptyList
    graph.rule_order = M.EmptyList
    graph.derivations = M.EmptyList
    graph.derivation_schemata = M.EmptyList
    # A search-worker result describes one attempt, not the runtime's hypergraph.
    # These two roots are nonetheless required: SnapshotCodec.capture reads
    # graph.nodes/graph.edges unconditionally since hypergraph content became
    # persistable (18cdedf), and this stand-in graph is not a runtime. Leaving
    # them out made every checkpoint write -- and therefore the whole
    # `search-worker` mode -- die with AttributeError before it wrote anything.
    graph.nodes = M.EmptyList
    graph.edges = M.EmptyList
    graph.search_history = M.Pair(attempt, M.EmptyList)
    graph.search_comparisons = M.Pair(performance, M.EmptyList)
    graph.search_comparison_jobs = M.EmptyList
    graph.search_jobs = M.EmptyList
    graph.search_memo = M.EmptyList
    graph.nat_value_index = runtime.graph.nat_value_index
    return graph


def _search_worker_derivation_lock_path(result_path: str):
    return os.path.join(os.path.dirname(result_path) or ".", "search_worker_derivation.lock")


def _search_worker_acquire_derivation_lock(result_path: str, timeout_seconds: int):
    lock_path = _search_worker_derivation_lock_path(result_path)
    stale_after_seconds = timeout_seconds + 60
    while True:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            try:
                os.write(fd, str(os.getpid()).encode("utf-8"))
            finally:
                os.close(fd)
            return lock_path
        except FileExistsError:
            try:
                lock_age = time.time() - os.path.getmtime(lock_path)
            except OSError:
                lock_age = 0.0
            if lock_age > stale_after_seconds:
                try:
                    os.remove(lock_path)
                    continue
                except OSError:
                    pass
            time.sleep(0.2)


def _search_worker_release_derivation_lock(lock_path: str):
    try:
        os.remove(lock_path)
    except OSError:
        pass


def _search_worker_store_result(runtime, result_path: str, attempt, performance, worker_stage=None, worker_plan=None):
    if worker_stage == None:
        worker_stage = _string_atom("")
    if worker_plan == None:
        worker_plan = M.EmptyList
    if M.Compare(worker_plan, M.EmptyList)() is M.truth_value:
        if os.path.exists(result_path):
            try:
                state = SnapshotCodec(_runtime_namespace()).load(result_path)
                existing_plan = state.roots.get("worker_plan", M.EmptyList)
                if M.Compare(existing_plan, M.EmptyList)() is M.false_value:
                    worker_plan = existing_plan
            except Exception:
                pass
    os.makedirs(os.path.dirname(result_path) or ".", exist_ok=True)
    codec = SnapshotCodec(_runtime_namespace())
    snapshot = codec.capture(
        _search_worker_result_graph(runtime, attempt, performance),
        extra_roots={
            "worker_stage": worker_stage,
            "worker_plan": worker_plan,
        },
    )
    temp_path = result_path + ".tmp"
    with open(temp_path, "w", encoding="utf-8") as handle:
        json.dump(snapshot, handle, ensure_ascii=False, indent=2)
    os.replace(temp_path, result_path)


def _search_worker_stage_text(value):
    if value is None:
        return ""
    if M.Compare(value, M.EmptyList)() is M.truth_value:
        return ""
    try:
        return str(value())
    except Exception:
        return ""


def _search_worker_resume_state(result_path: str, start, goal, heuristic, registry=None):
    if registry == None:
        registry = M.AllConstructors
    if os.path.exists(result_path) is False:
        return M.EmptyList, M.EmptyList, 0, ""
    try:
        state = SnapshotCodec(_runtime_namespace()).load(result_path)
    except Exception:
        return M.EmptyList, M.EmptyList, 0, ""
    attempts = state.roots.get("search_history", M.EmptyList)
    if M.IdentityCompare(attempts, M.EmptyList)() is M.truth_value:
        return M.EmptyList, M.EmptyList, 0, ""
    attempt = M.Head(attempts)()
    if M.IdentityCompare(M.CompareIn(P.SearchAttemptStart(attempt)(), start, registry)(), M.false_value)() is M.truth_value:
        return M.EmptyList, M.EmptyList, 0, ""
    if M.IdentityCompare(M.CompareIn(P.SearchAttemptGoal(attempt)(), goal, registry)(), M.false_value)() is M.truth_value:
        return M.EmptyList, M.EmptyList, 0, ""
    if M.IdentityCompare(M.CompareIn(P.SearchAttemptHeuristic(attempt)(), heuristic, registry)(), M.false_value)() is M.truth_value:
        return M.EmptyList, M.EmptyList, 0, ""
    performances = state.roots.get("search_comparisons", M.EmptyList)
    elapsed_milliseconds = 0
    if M.IdentityCompare(performances, M.EmptyList)() is M.false_value:
        performance = M.Head(performances)()
        elapsed = Smod.HeuristicPerformanceElapsedMilliseconds(performance)()
        try:
            elapsed_milliseconds = int(M.GMPRepText(elapsed())())
        except Exception:
            elapsed_milliseconds = 0
    worker_stage = state.roots.get("worker_stage", M.EmptyList)
    worker_plan = state.roots.get("worker_plan", M.EmptyList)
    worker_stage_text = _search_worker_stage_text(worker_stage)
    if worker_stage_text == "success-plan-found":
        return worker_plan, P.SearchAttemptSearchCost(attempt)(), elapsed_milliseconds, worker_stage_text
    if worker_stage_text == "running-derivation":
        return worker_plan, P.SearchAttemptSearchCost(attempt)(), elapsed_milliseconds, worker_stage_text
    return M.EmptyList, M.EmptyList, elapsed_milliseconds, worker_stage_text


def _search_worker_attempt(runtime, start, goal, heuristic, status, derivation, proof_cost, search_cost, elapsed_milliseconds, completion_reason):
    registry = M.FromContextGetConstructors(runtime.graph)()
    total_cost_pair = P.BuildTotalCost(proof_cost, search_cost, heuristic, registry)()
    total_cost = M.Head(total_cost_pair)()
    registry = M.Head(M.Tail(total_cost_pair)())()
    runtime.graph._replace_context(constructors=registry)
    attempt = P.SearchAttempt(start, goal, heuristic, status, derivation, proof_cost, search_cost, total_cost)()
    performance = Smod.HeuristicPerformance(
        attempt,
        _gmp_atom_from_int(elapsed_milliseconds),
        _gmp_atom_from_int(os.getpid()),
        completion_reason,
    )()
    return attempt, performance


def _search_worker_checkpoint(runtime, result_path, start, goal, heuristic, status, derivation, proof_cost, search_cost, elapsed_milliseconds, completion_reason_text, worker_plan=None):
    completion_reason = _string_atom(completion_reason_text)
    attempt, performance = _search_worker_attempt(
        runtime,
        start,
        goal,
        heuristic,
        status,
        derivation,
        proof_cost,
        search_cost,
        elapsed_milliseconds,
        completion_reason,
    )
    _search_worker_store_result(
        runtime,
        result_path,
        attempt,
        performance,
        _string_atom(completion_reason_text),
        worker_plan,
    )
    return attempt, performance


def _maybe_set_search_worker_memory_limit():
    memory_text = os.environ.get("HYGE_SEARCH_WORKER_MEMORY_MB", "")
    if memory_text == "":
        return
    try:
        memory_megabytes = int(memory_text)
    except Exception:
        return
    if memory_megabytes <= 0:
        return
    try:
        import resource
    except Exception:
        return
    limit_bytes = memory_megabytes * 1024 * 1024
    try:
        resource.setrlimit(resource.RLIMIT_AS, (limit_bytes, limit_bytes))
    except Exception:
        pass


class SearchWorkerBoot:
    """What `search_worker_boot` produces: a booted runtime plus one job's problem.

    Split out of `run_search_worker_mode` for the mesh (W2). A long-lived worker
    peer boots once and then executes many jobs on that runtime, which is only
    possible if the boot and the job execution can be reached separately. Both
    halves keep their original code; `run_search_worker_mode` remains the
    composed entry point and behaves exactly as before.
    """

    __slots__ = (
        "runtime",
        "packs",
        "registry",
        "label",
        "start",
        "goal",
        "worker_heuristic",
        "resume_derivation_only",
    )

    def __init__(self, runtime, packs, registry, label, start, goal, worker_heuristic, resume_derivation_only):
        self.runtime = runtime
        self.packs = packs
        self.registry = registry
        self.label = label
        self.start = start
        self.goal = goal
        self.worker_heuristic = worker_heuristic
        self.resume_derivation_only = resume_derivation_only


def search_worker_resolve_problem(runtime, packs, worker_mode, result_path, registry):
    """Resolve one manifest's problem against an already-booted runtime."""
    worker_heuristic = _search_worker_mode_heuristic(runtime, worker_mode, registry)
    label, start, goal, _rules, _phi = _search_worker_problem_from_manifest(packs, result_path, worker_heuristic, registry)
    start = Hmod.HeuristicCanonicalize(start, worker_heuristic, registry)()
    goal = Hmod.HeuristicCanonicalize(goal, worker_heuristic, registry)()
    return label, start, goal, worker_heuristic


def search_worker_boot(worker_mode: str, result_path: str, timeout_seconds: int = 6000):
    P.SetDebugTrace(M.truth_value)()
    _maybe_set_search_worker_memory_limit()
    resume_derivation_only = os.environ.get("HYGE_SEARCH_WORKER_RESUME_DERIVATION", "") == "1"
    if resume_derivation_only:
        runtime = boot_from_snapshot(result_path, _runtime_namespace())
        registry = M.FromContextGetConstructors(runtime.graph)()
        attempts = runtime.graph.search_history
        if M.IdentityCompare(attempts, M.EmptyList)() is M.truth_value:
            raise RuntimeError("search-worker resume missing-attempt")
        attempt = M.Head(attempts)()
        worker_heuristic = P.SearchAttemptHeuristic(attempt)()
        start = P.SearchAttemptStart(attempt)()
        goal = P.SearchAttemptGoal(attempt)()
        label = "resumed derivation checkpoint"
        packs = None
    else:
        runtime, packs = boot_from_packs(PACK_PATHS, _runtime_namespace())
        registry = M.FromContextGetConstructors(runtime.graph)()
        label, start, goal, worker_heuristic = search_worker_resolve_problem(
            runtime, packs, worker_mode, result_path, registry
        )
    return SearchWorkerBoot(
        runtime,
        packs,
        registry,
        label,
        start,
        goal,
        worker_heuristic,
        resume_derivation_only,
    )


def search_worker_execute(worker_mode: str, result_path: str, timeout_seconds: int, boot):
    runtime = boot.runtime
    registry = boot.registry
    label = boot.label
    start = boot.start
    goal = boot.goal
    worker_heuristic = boot.worker_heuristic
    resume_derivation_only = boot.resume_derivation_only
    runtime.graph._search_disable_console = M.truth_value
    runtime.graph._search_disable_progress_ticker = M.false_value
    runtime.graph._search_stop_help_shown = M.truth_value
    runtime.graph._search_compare_enable_shared_root_fast_paths = M.false_value
    runtime.graph._search_compare_ignore_root_fast_paths = M.false_value
    runtime.graph._search_compare_root_start = M.EmptyList
    runtime.graph._search_compare_root_goal = M.EmptyList
    runtime.graph._search_compare_discovery_mode = M.false_value
    runtime.graph._search_probe_disable_applicable_cache = M.false_value
    runtime.graph._search_probe_disable_applicable_shards = M.truth_value
    runtime.graph._search_worker_timeout_seconds = float(timeout_seconds)
    defer_derivation = os.environ.get("HYGE_SEARCH_WORKER_DEFER_DERIVATION", "") == "1"
    runtime.graph._search_worker_defer_derivation_materialization = M.truth_value if defer_derivation else M.false_value
    mode_label = _search_worker_mode_label(worker_mode)
    mode_name = Smod.SearchModeText(mode_label)()
    P.DERIVATION_REPLAY_DEBUG_SUPPRESS_STATE.value = M.truth_value
    P._debug(mode_name + ": search-worker booted")
    P._debug(mode_name + ": search-worker problem=" + label)
    defer_derivation = os.environ.get("HYGE_SEARCH_WORKER_DEFER_DERIVATION", "") == "1"
    started_at = time.time()
    base_elapsed_milliseconds = 0
    outcome = M.SearchFailureLabel
    derivation = M.EmptyList
    proof_cost = P.ProofCost(M.Zero, M.Zero, M.Zero, M.Zero)()
    search_cost_pair = Smod.BuildSearchCost(M.EmptyList, M.Zero, M.Zero, M.Zero, M.SearchRunningLabel, registry)()
    search_cost = M.Head(search_cost_pair)()
    resume_plan, resume_search_cost, resume_elapsed_milliseconds, resume_stage_text = _search_worker_resume_state(
        result_path,
        start,
        goal,
        worker_heuristic,
        registry,
    )
    if resume_derivation_only:
        if M.Compare(resume_plan, M.EmptyList)() is M.truth_value:
            raise RuntimeError("search-worker resume missing-plan")
    if M.Compare(resume_plan, M.EmptyList)() is M.truth_value:
        P._debug(mode_name + ": saving checkpoint stage=running-search")
        _search_worker_checkpoint(
            runtime,
            result_path,
            start,
            goal,
            worker_heuristic,
            M.SearchRunningLabel,
            M.EmptyList,
            proof_cost,
            search_cost,
            0,
            "running-search",
        )
        P._debug(mode_name + ": checkpoint saved stage=running-search")
    else:
        base_elapsed_milliseconds = resume_elapsed_milliseconds
        search_cost = resume_search_cost
        P._debug(mode_name + ": resuming derivation build from checkpoint stage=" + resume_stage_text)
    error_text = ""
    plan = M.EmptyList
    try:
        if M.Compare(resume_plan, M.EmptyList)() is M.truth_value:
            if resume_derivation_only:
                raise RuntimeError("search-worker resume missing-plan")
            search_pair = Smod.Search(runtime.graph, start, goal, runtime.ordered_rules(), worker_heuristic, registry)()
            plan = M.Head(search_pair)()
            search_cost = M.Head(M.Tail(search_pair)())()
            registry = M.FromContextGetConstructors(runtime.graph)()
            outcome = Smod.SearchCostOutcome(search_cost)()
            elapsed_milliseconds = base_elapsed_milliseconds + int(round((time.time() - started_at) * 1000.0))
            if M.IdentityCompare(outcome, M.SearchSuccessLabel)() is M.truth_value:
                P._debug(mode_name + ": goal reached; saving checkpoint stage=success-plan-found")
                _search_worker_checkpoint(
                    runtime,
                    result_path,
                    start,
                    goal,
                    worker_heuristic,
                    M.SearchSuccessLabel,
                    M.EmptyList,
                    proof_cost,
                    search_cost,
                    elapsed_milliseconds,
                    "success-plan-found",
                    plan,
                )
                P._debug(mode_name + ": checkpoint saved stage=success-plan-found")
                P._debug(mode_name + ": saving checkpoint stage=running-derivation")
                _search_worker_checkpoint(
                    runtime,
                    result_path,
                    start,
                    goal,
                    worker_heuristic,
                    M.SearchSuccessLabel,
                    M.EmptyList,
                    proof_cost,
                    search_cost,
                    elapsed_milliseconds,
                    "running-derivation",
                    plan,
                )
                P._debug(mode_name + ": checkpoint saved stage=running-derivation")
                if defer_derivation:
                    P._debug(mode_name + ": awaiting approval before derivation replay")
                    return 4
            if M.IdentityCompare(outcome, M.SearchSuccessLabel)() is M.false_value:
                final_reason = "failure-search"
                if M.IdentityCompare(outcome, M.SearchTimedOutLabel)() is M.truth_value:
                    final_reason = "timed_out"
                _search_worker_checkpoint(
                    runtime,
                    result_path,
                    start,
                    goal,
                    worker_heuristic,
                    outcome,
                    M.EmptyList,
                    proof_cost,
                    search_cost,
                    elapsed_milliseconds,
                    final_reason,
                    M.EmptyList,
                )
                if M.IdentityCompare(outcome, M.SearchTimedOutLabel)() is M.truth_value:
                    return 2
                return 1
        else:
            plan = resume_plan
            outcome = M.SearchSuccessLabel
            elapsed_milliseconds = base_elapsed_milliseconds
            if resume_derivation_only:
                pass
            else:
                if defer_derivation:
                    if resume_stage_text == "success-plan-found":
                        P._debug(mode_name + ": saving checkpoint stage=running-derivation")
                        _search_worker_checkpoint(
                            runtime,
                            result_path,
                            start,
                            goal,
                            worker_heuristic,
                            M.SearchSuccessLabel,
                            M.EmptyList,
                            proof_cost,
                            search_cost,
                            elapsed_milliseconds,
                            "running-derivation",
                            plan,
                        )
                        P._debug(mode_name + ": checkpoint saved stage=running-derivation")
                    P._debug(mode_name + ": awaiting approval before derivation replay")
                    return 4
        derivation_lock_path = _search_worker_acquire_derivation_lock(result_path, timeout_seconds)
        P._debug(mode_name + ": acquired derivation lock")
        try:
            P._debug(mode_name + ": starting derivation replay")
            derivation_pair = P.BuildDerivation(start, plan, registry)()
            derivation = M.Head(derivation_pair)()
            registry = M.Head(M.Tail(derivation_pair)())()
            runtime.graph._replace_context(constructors=registry)
            proof_cost_pair = P.DerivationCost(derivation, registry)()
            proof_cost = M.Head(proof_cost_pair)()
            registry = M.Head(M.Tail(proof_cost_pair)())()
            runtime.graph._replace_context(constructors=registry)
            runtime.graph.add_derivation(start, goal, derivation)
            elapsed_milliseconds = base_elapsed_milliseconds + int(round((time.time() - started_at) * 1000.0))
        finally:
            _search_worker_release_derivation_lock(derivation_lock_path)
            P._debug(mode_name + ": released derivation lock")
    except MemoryError:
        error_text = "failure-memory-error"
        P._debug(mode_name + ": worker error=" + error_text)
        _search_worker_checkpoint(
            runtime,
            result_path,
            start,
            goal,
            worker_heuristic,
            M.SearchSuccessLabel,
            M.EmptyList,
            proof_cost,
            search_cost,
            base_elapsed_milliseconds + int(round((time.time() - started_at) * 1000.0)),
            "running-derivation",
            plan,
        )
        return 1
    except Exception as error:
        error_text = error.__class__.__name__ + ": " + str(error)
        P._debug(mode_name + ": worker error=" + error_text)
        _search_worker_checkpoint(
            runtime,
            result_path,
            start,
            goal,
            worker_heuristic,
            M.SearchFailureLabel,
            M.EmptyList,
            proof_cost,
            search_cost,
            base_elapsed_milliseconds + int(round((time.time() - started_at) * 1000.0)),
            error_text,
            plan,
        )
        return 1
    P._debug(mode_name + ": saving checkpoint stage=success-derivation-built")
    _search_worker_checkpoint(
        runtime,
        result_path,
        start,
        goal,
        worker_heuristic,
        M.SearchSuccessLabel,
        derivation,
        proof_cost,
        search_cost,
        elapsed_milliseconds,
        "success-derivation-built",
        plan,
    )
    P._debug(mode_name + ": checkpoint saved stage=success-derivation-built")
    return 0


def run_search_worker_mode(worker_mode: str, result_path: str, timeout_seconds: int = 6000):
    boot = search_worker_boot(worker_mode, result_path, timeout_seconds)
    return search_worker_execute(worker_mode, result_path, timeout_seconds, boot)


def run_mesh_peer_mode(
    role: str,
    bind: str,
    coordinator: str = None,
    worker_modes: str = None,
    timeout_seconds: int = 6000,
    cert_dir: str = None,
    jobs_file: str = None,
    run_seconds: float = 0.0,
    cert_name: str = None,
    swarm: bool = False,
    artifacts: str = "shared",
    artifact_dir: str = None,
    inbound: bool = True,
    verify: str = "hostname",
    expect: str = None,
    advertise: str = None,
    bundle_dir: str = None,
    sans: str = None,
):
    """`python main.py mesh ...` -- a long-lived peer of the W2 RPC/mTLS mesh.

    Boots the machine once (so the ~20 s pack boot is paid once per peer, not
    once per job) and then serves search jobs over the mesh transport. The job
    semantics are `search_worker_execute`'s; only the transport is new.

    The W20 switches (`artifacts`, `artifact_dir`, `inbound`, `verify`, `expect`,
    `advertise`) let the same peer run across a tunnel against a worker that has
    no shared filesystem; `role="issue"` writes that worker's certificate bundle.
    """
    from . import mesh as Meshmod
    return Meshmod.run_peer_cli(
        role=role,
        bind=bind,
        coordinator=coordinator,
        worker_modes=worker_modes,
        timeout_seconds=timeout_seconds,
        cert_dir=cert_dir,
        jobs_file=jobs_file,
        run_seconds=run_seconds,
        cert_name=cert_name,
        swarm=swarm,
        artifacts=artifacts,
        artifact_dir=artifact_dir,
        inbound=inbound,
        verify=verify,
        expect=expect,
        advertise=advertise,
        bundle_dir=bundle_dir,
        sans=sans,
    )


SWARM_UNIT_STEP_BUDGET = 60


def run_swarm_worker_mode(unit_path: str, result_path: str, timeout_seconds: int = 600):
    """`python main.py --role worker swarm UNIT RESULT [TIMEOUT]` -- run one work unit.

    The option comes first: argparse stops matching the optional positionals
    (`arg1`..`arg3`) once an option follows the mode word, so
    `swarm --role worker UNIT RESULT` is rejected as "unrecognized arguments".

    A unit is a snapshot holding exactly one search job whose frontier is a
    single node; see `search/distributed_engine.py` for why a unit is one node
    and not a shard. Booting it measured 8.8 s against a 20 s pack boot plus an
    18 s expansion, which is what makes a partitioned swarm affordable at all.

    The result goes out through the same checkpoint helper the search worker
    uses, so `networking.jobs.project_result` reads a unit's result exactly as it
    reads any other search result -- which is how the suite compares proofs
    rather than bytes.

    Exit status follows the W2 rule that a *result* is not a failure: a unit that
    searched to a terminal status and wrote its result exits 0 whether or not it
    found a proof, because "this branch does not prove the goal" is an answer the
    swarm needs. Only infrastructure breakage -- an unreadable unit, a job that
    never reached a terminal status -- exits non-zero.
    """
    from .search import distributed_engine as swarm

    P.SetDebugTrace(M.truth_value)()
    _maybe_set_search_worker_memory_limit()
    started_at = time.time()
    runtime, graph, registry, job = swarm.read_unit(unit_path, _runtime_namespace())
    graph._search_disable_console = M.truth_value
    graph._search_disable_progress_ticker = M.false_value
    graph._search_stop_help_shown = M.truth_value
    graph._search_worker_timeout_seconds = float(timeout_seconds)
    P.DERIVATION_REPLAY_DEBUG_SUPPRESS_STATE.value = M.truth_value
    budget, registry = swarm.nat(SWARM_UNIT_STEP_BUDGET, registry)
    pair = Smod.SearchBurst(graph, job, budget, registry)()
    job = M.Head(pair)()
    registry = M.Head(M.Tail(pair)())()
    graph._replace_context(constructors=registry)
    status = M.SearchJobStatus(job)()
    plan = M.SearchJobResultPlan(job)()
    terminal = M.IdentityCompare(status, M.SearchRunningLabel)() is M.false_value
    proof_cost = P.ProofCost(M.Zero, M.Zero, M.Zero, M.Zero)()
    search_cost_pair = Smod.BuildSearchCost(
        M.EmptyList, M.Zero, M.Zero, M.Zero, M.SearchRunningLabel, registry
    )()
    search_cost = M.Head(search_cost_pair)()
    _search_worker_checkpoint(
        runtime,
        result_path,
        M.SearchJobStart(job)(),
        M.SearchJobGoal(job)(),
        M.SearchJobHeuristic(job)(),
        status,
        M.EmptyList,
        proof_cost,
        search_cost,
        int((time.time() - started_at) * 1000),
        "swarm-unit",
        worker_plan=plan,
    )
    proved = M.IdentityCompare(status, M.SearchSuccessLabel)() is M.truth_value
    print(
        "[swarm:worker] unit=%s proved=%s terminal=%s elapsed=%.1fs result=%s"
        % (os.path.basename(unit_path), proved, terminal, time.time() - started_at, result_path),
        flush=True,
    )
    return 0 if terminal else 1


def run_swarm_plan_mode(problem: str, out_dir: str, burst_steps: int = 3, shard_count: int = 2, mode_text: str = "dfs"):
    """`python main.py swarm --role plan` -- expand once, then ship units.

    The expansion is the expensive part of a swarm run and it is identical in
    every worker, so it happens here, once: the frontier is partitioned into
    single-node units, each is written as a snapshot, and a job file is written
    for the mesh. `unit_path` rides in each job's manifest, which `mesh.load_jobs`
    passes through untouched, so the units cross the W2 transport as references
    to machine state rather than as serialised terms.
    """
    from .search import distributed_engine as swarm

    os.makedirs(out_dir, exist_ok=True)
    runtime, packs = boot_from_packs(PACK_PATHS, _runtime_namespace())
    graph = runtime.graph
    graph._search_disable_console = M.truth_value
    graph._search_disable_progress_ticker = M.false_value
    graph._search_stop_help_shown = M.truth_value
    graph._search_probe_disable_applicable_cache = M.false_value
    graph._search_probe_disable_applicable_shards = M.truth_value
    registry = M.FromContextGetConstructors(graph)()
    matches = [case for case in _theorem_agenda(packs, "all") if problem.lower() in case[0].lower()]
    if not matches:
        raise RuntimeError("no agenda problem matches " + repr(problem))
    label, start, goal, _rules, _phi = matches[0]
    heuristic = _search_worker_mode_heuristic(runtime, mode_text, registry)
    # NormalizeKnowledge, not the heuristic canonicalization the search worker
    # applies: these are the exact terms the partition function was measured
    # against, and the suite compares a baseline and its units produced by this
    # one code path, so what matters is that both arms agree.
    start = P.NormalizeKnowledge(start, registry)()
    goal = P.NormalizeKnowledge(goal, registry)()
    rules = runtime.ordered_rules()
    job = swarm.root_job(start, goal, rules, heuristic, swarm.step_limit(graph, rules, registry))
    job, registry, units, size = swarm.expand_frontier(
        graph, job, registry, burst_steps, shard_count=shard_count
    )
    graph._replace_context(constructors=registry)
    if not size:
        raise RuntimeError(
            "problem " + label + " left no frontier to partition; pick one that is not settled by a root fast path"
        )
    frontier = M.SearchJobFrontier(job)()
    baseline_path = os.path.join(out_dir, "baseline.json")
    swarm.write_unit(runtime, baseline_path, _runtime_namespace(), job)
    entries = []
    for unit in units:
        unit_path = os.path.join(out_dir, "unit-%03d.json" % unit.frontier_index)
        node = swarm.only_node(frontier, unit.frontier_index)
        swarm.write_unit(runtime, unit_path, _runtime_namespace(), swarm.rebuild_job(job, node))
        entries.append(
            {
                "job_id": unit.unit_id,
                "mode": mode_text,
                "result_ref": os.path.join(out_dir, "result-%03d.json" % unit.frontier_index),
                "manifest": {
                    "unit_path": unit_path,
                    "frontier_index": unit.frontier_index,
                    "digest": unit.digest,
                    "shard": unit.shard,
                    "problem": label,
                },
                "scope_ids": ["swarm-" + unit.digest[:16]],
            }
        )
    plan_path = os.path.join(out_dir, "plan.json")
    with open(plan_path, "w", encoding="utf-8") as handle:
        json.dump(
            {
                "problem": label,
                "mode": mode_text,
                "burst_steps": burst_steps,
                "shard_count": shard_count,
                "frontier_size": size,
                "shard_sizes": swarm.shard_sizes(units, shard_count),
                "exact": swarm.partition_is_exact(units, size),
                "baseline": baseline_path,
                "jobs": entries,
            },
            handle,
            indent=2,
            sort_keys=True,
        )
    print(
        "[swarm:plan] problem=%s nodes=%d shards=%s exact=%s plan=%s"
        % (label, size, swarm.shard_sizes(units, shard_count), swarm.partition_is_exact(units, size), plan_path),
        flush=True,
    )
    return 0


def run_cold_mode(debug: bool = False, filter_name: str = "tao"):
    if debug:
        P.SetDebugTrace(M.truth_value)()
    else:
        P.SetDebugTrace(M.false_value)()
    runtime_namespace = _runtime_namespace()
    if M.IdentityCompare(_maybe_resume_paused_cold_search(debug=debug), M.truth_value)() is M.truth_value:
        return

    start_time = time.time()
    runtime, packs = boot_from_packs(PACK_PATHS, runtime_namespace)
    pack_load_time = time.time() - start_time
    print(f"Pack loading took {pack_load_time:.2f} seconds")

    summary_start = time.time()
    _print_summary(runtime, "Cold boot summary")
    summary_time = time.time() - summary_start
    print(f"Summary took {summary_time:.2f} seconds")

    for pack_info in runtime.pack_summaries():
        print("loaded pack:", pack_info)

    try:
        theorem_results = _run_theorem_agenda(runtime, _theorem_agenda(packs, filter_name), "Cold theorem agenda", debug=debug)
    except PausedComparisonRequested as paused:
        print(paused.label + ": comparison paused after " + str(paused.elapsed) + " seconds")
        _save_snapshot_now(runtime, runtime_namespace)
        return
    except PausedSearchRequested as paused:
        print(paused.label + ": paused after " + str(paused.elapsed) + " seconds")
        _save_snapshot_now(runtime, runtime_namespace)
        return
    proved_count = sum(1 for _label, proved, _elapsed, _goal, _derivation in theorem_results if proved)
    print(f"proved {proved_count} / {len(theorem_results)} theorem cases during cold boot")

    _save_snapshot_now(runtime, runtime_namespace)


def run_warm_mode(debug: bool = False):
    if debug:
        P.SetDebugTrace(M.truth_value)()
    else:
        P.SetDebugTrace(M.false_value)()
    runtime_namespace = _runtime_namespace()
    runtime = boot_from_snapshot(SNAPSHOT_PATH, runtime_namespace, debug=M.truth_value if debug else M.false_value)
    graph = runtime.graph

    _print_summary(runtime, "Warm boot summary")
    print("loaded snapshot roots:")
    print("  constructor_registry =", M.FromContextGetConstructors(graph)())
    print("  all_rules =", M.FromContextGetAllRules(graph)())
    print("  rule_order =", M.FromContextGetRuleOrder(graph)())
    print("  derivations =", M.FromContextGetDerivations(graph)())
    print("  derivation_schemata =", M.FromContextGetDerivationSchemata(graph)())

    branchy_sqrt_two = M.Pair(M.SqrtLabel, M.Pair(M.two, M.EmptyList))
    branchy_sqrt_three = M.Pair(M.SqrtLabel, M.Pair(M.three, M.EmptyList))
    branchy_sqrt_five = M.Pair(M.SqrtLabel, M.Pair(M.five, M.EmptyList))
    branchy_sqrt_six = M.Pair(M.SqrtLabel, M.Pair(M.six, M.EmptyList))
    branchy_sqrt_seven = M.Pair(M.SqrtLabel, M.Pair(M.seven, M.EmptyList))
    branchy_sqrt_eight = M.Pair(M.SqrtLabel, M.Pair(M.eight, M.EmptyList))
    branchy_start = M.Knowledge(
        M.Pair(
            M.Pair(M.IsRealLabel, M.Pair(branchy_sqrt_two, M.EmptyList)),
            M.Pair(
                M.Pair(M.IsRealLabel, M.Pair(branchy_sqrt_three, M.EmptyList)),
                M.Pair(
                    M.Pair(M.IsRealLabel, M.Pair(branchy_sqrt_five, M.EmptyList)),
                    M.Pair(
                        M.Pair(M.IsRealLabel, M.Pair(branchy_sqrt_six, M.EmptyList)),
                        M.Pair(
                            M.Pair(M.IsRealLabel, M.Pair(branchy_sqrt_seven, M.EmptyList)),
                            M.Pair(M.Pair(M.IsRealLabel, M.Pair(branchy_sqrt_eight, M.EmptyList)), M.EmptyList),
                        ),
                    ),
                ),
            ),
        )
    )()
    branchy_left = M.Pair(
        M.ExprMulLabel,
        M.Pair(
            M.Pair(M.ExprAddLabel, M.Pair(branchy_sqrt_two, M.Pair(branchy_sqrt_three, M.EmptyList))),
            M.Pair(M.Pair(M.ExprAddLabel, M.Pair(branchy_sqrt_five, M.Pair(branchy_sqrt_seven, M.EmptyList))), M.EmptyList),
        ),
    )
    branchy_right = M.Pair(
        M.ExprMulLabel,
        M.Pair(
            M.Pair(M.ExprAddLabel, M.Pair(branchy_sqrt_six, M.Pair(branchy_sqrt_eight, M.EmptyList))),
            M.Pair(M.Pair(M.ExprAddLabel, M.Pair(branchy_sqrt_two, M.Pair(branchy_sqrt_five, M.EmptyList))), M.EmptyList),
        ),
    )
    branchy_goal = M.Pair(
        M.IsRealLabel,
        M.Pair(M.Pair(M.ExprAddLabel, M.Pair(branchy_left, M.Pair(branchy_right, M.EmptyList))), M.EmptyList),
    )

    try:
        theorem_results = _run_theorem_agenda(
            runtime,
            [
                ("branchy real-closure proof", branchy_start, branchy_goal),
                _make_isreal_sqrt_case("sqrt(3)", M.three),
                _make_isreal_sqrt_case("sqrt(4)", M.four),
                _make_isreal_sqrt_case("sqrt(5)", M.five),
                _make_real_closure_case("sqrt(2) + sqrt(3)*sqrt(5) from real premises", M.two, M.three, M.five),
            ],
            "Warm theorem agenda",
            debug=debug,
        )
    except PausedComparisonRequested as paused:
        print(paused.label + ": comparison paused after " + str(paused.elapsed) + " seconds")
        _save_snapshot_now(runtime, runtime_namespace)
        return
    except PausedSearchRequested as paused:
        print(paused.label + ": paused after " + str(paused.elapsed) + " seconds")
        _save_snapshot_now(runtime, runtime_namespace)
        return
    proved_count = sum(1 for _label, proved, _elapsed, _goal, _derivation in theorem_results if proved)
    print(f"proved {proved_count} / {len(theorem_results)} theorem cases during warm boot")


def run_test_mode(debug: bool = False):
    if debug:
        P.SetDebugTrace(M.truth_value)()
    else:
        P.SetDebugTrace(M.false_value)()
    runtime, _packs = boot_from_packs(PACK_PATHS, _runtime_namespace())
    install_default_tests(runtime.graph)
    _print_summary(runtime, "Cold boot summary for tests")
    start_time = time.time()
    report = runtime.run_tests_report()
    elapsed = time.time() - start_time
    if report == "All the tests have passed.":
        print(f"All tests passed in {elapsed} seconds.")
    else:
        print(f"Some tests failed after {elapsed} seconds.")
        print(report)


def _inspector_runtime(debug: bool, prefer_snapshot: bool):
    runtime_namespace = _runtime_namespace()
    if debug:
        P.SetDebugTrace(M.truth_value)()
    else:
        P.SetDebugTrace(M.false_value)()
    if prefer_snapshot and os.path.exists(SNAPSHOT_PATH):
        return boot_from_snapshot(SNAPSHOT_PATH, runtime_namespace, debug=M.truth_value if debug else M.false_value), "snapshot"
    runtime, _packs = boot_from_packs(PACK_PATHS, runtime_namespace)
    return runtime, "packs"


class _HygeInspectorServer(http.server.ThreadingHTTPServer):
    def __init__(self, server_address, request_handler_class, runtime, source_text, max_rule_edges):
        self.runtime = runtime
        self.source_text = source_text
        self.max_rule_edges = max_rule_edges
        super().__init__(server_address, request_handler_class)


class _HygeInspectorHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, directory=None, **kwargs):
        super().__init__(*args, directory=INSPECTOR_DIR, **kwargs)

    def _send_json(self, payload_text):
        body = payload_text.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _payload_text(self, max_rule_edges):
        runtime = self.server.runtime
        return runtime.inspector_payload_json(self.server.source_text, max_rule_edges)

    def _query_max_rule_edges(self, query_text):
        query = urllib.parse.parse_qs(query_text)
        if "max_rule_edges" not in query:
            return self.server.max_rule_edges
        values = query["max_rule_edges"]
        if len(values) == 0:
            return self.server.max_rule_edges
        try:
            parsed = int(values[0])
        except Exception:
            return self.server.max_rule_edges
        if parsed <= 0:
            return self.server.max_rule_edges
        return parsed

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/introspection":
            payload_text = self._payload_text(self._query_max_rule_edges(parsed.query))
            self._send_json(payload_text)
            return
        if parsed.path == "/":
            self.path = "/index.html"
        else:
            self.path = parsed.path
        super().do_GET()

    def log_message(self, format, *args):
        print("inspector:", format % args)


def _build_inspector_server(debug: bool, prefer_snapshot: bool, port: int, max_rule_edges: int):
    runtime, source_text = _inspector_runtime(debug, prefer_snapshot)
    server = _HygeInspectorServer(
        ("127.0.0.1", port),
        _HygeInspectorHandler,
        runtime,
        source_text,
        max_rule_edges,
    )
    return server, "http://127.0.0.1:" + str(port) + "/"


def run_inspect_mode(debug: bool = False, prefer_snapshot: bool = True, port: int = INSPECTOR_DEFAULT_PORT, max_rule_edges: int = INSPECTOR_DEFAULT_MAX_RULE_EDGES, open_browser: bool = True):
    server, url = _build_inspector_server(debug, prefer_snapshot, port, max_rule_edges)
    print("HYGE inspector running at " + url)
    print("runtime source: " + server.source_text)
    print("initial visible rule cap: " + str(max_rule_edges))
    try:
        if open_browser:
            try:
                webbrowser.open(url)
            except Exception:
                pass
        server.serve_forever()
    except KeyboardInterrupt:
        print("HYGE inspector stopped")
    finally:
        server.server_close()


def _terminate_active_children():
    children = multiprocessing.active_children()
    for child in children:
        try:
            child.terminate()
        except Exception:
            pass
    for child in children:
        try:
            child.join(1.0)
        except Exception:
            pass


def _words_to_token_chain(words):
    if not words:
        return M.EmptyList
    tok = SB.SurfaceToken(M.Char(words[0].lower()))()
    return M.Pair(tok, _words_to_token_chain(words[1:]))


def _print_ledger_lemmas(cur, lemma_idx):
    if M.IdentityCompare(cur, M.EmptyList)() is M.truth_value:
        return
    entry = M.Head(cur)()
    cand = PL.LedgerEntryCandidate(entry)()
    if M.IdentityCompare(M.Head(cand)(), Lmod.CandidateMacroLabel)() is M.truth_value:
        cand_id = M.Head(M.Tail(cand)())()
        name_val = cand_id()
    else:
        name_val = str(cand)
    print(f"  - Lemma {lemma_idx}: {name_val} [status: PromotionActiveLabel]")
    _print_ledger_lemmas(M.Tail(cur)(), lemma_idx + 1)


def _check_concept_definition_query(words, std_definitions):
    if not words:
        return M.false_value
    word = words[0]
    norm_word = word[:-1] if word.endswith("s") and len(word) > 4 else word
    q_def = SB.QueryConceptDefinition(M.Char(norm_word), std_definitions)()
    if M.IdentityCompare(M.Head(q_def)(), Lmod.SurfaceParseSuccessLabel)() is M.truth_value:
        def_node = M.Head(M.Tail(q_def)())()
        rendered = SB.RenderConceptExplanation(def_node)()
        print(f"[machine] {rendered()}")
        return M.truth_value
    return _check_concept_definition_query(words[1:], std_definitions)


def _strip_naming_prefix(text, prefixes):
    if not prefixes:
        return text.strip()
    prefix = prefixes[0]
    if text.lower().startswith(prefix):
        return text[len(prefix):].strip()
    return _strip_naming_prefix(text, prefixes[1:])


def run_live_mode(debug: bool = False):
    if debug:
        P.SetDebugTrace(M.truth_value)()
    else:
        P.SetDebugTrace(M.false_value)()

    runtime_namespace = _runtime_namespace()
    from .runtime import make_fresh_runtime
    runtime = make_fresh_runtime()
    runtime.graph._active_unproved_goal = M.EmptyList
    runtime.graph._active_goal_present = M.false_value
    runtime.graph._active_unproved_claim = M.EmptyList
    runtime.graph._active_tutor = M.EmptyList
    runtime.graph._last_playground_operation_register = M.EmptyList
    runtime.graph._last_playground_domain = M.EmptyList
    runtime.graph._last_playground_goal = M.EmptyList
    runtime.graph._pending_discovery = M.EmptyList
    packs = None

    word_to_num = {
        "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
        "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    }

    def _eval_arithmetic_expr(text: str):
        cleaned = text.strip().lower()
        if cleaned.startswith("the sum of ") and " and " in cleaned:
            parts = cleaned[len("the sum of "):].split(" and ", 1)
            v1 = _eval_arithmetic_expr(parts[0])
            v2 = _eval_arithmetic_expr(parts[1])
            if v1 is not None and v2 is not None:
                return v1 + v2
        if " plus " in cleaned:
            parts = cleaned.split(" plus ", 1)
            v1 = _eval_arithmetic_expr(parts[0])
            v2 = _eval_arithmetic_expr(parts[1])
            if v1 is not None and v2 is not None:
                return v1 + v2
        if cleaned.startswith("the product of ") and " and " in cleaned:
            parts = cleaned[len("the product of "):].split(" and ", 1)
            v1 = _eval_arithmetic_expr(parts[0])
            v2 = _eval_arithmetic_expr(parts[1])
            if v1 is not None and v2 is not None:
                return v1 * v2
        if " times " in cleaned:
            parts = cleaned.split(" times ", 1)
            v1 = _eval_arithmetic_expr(parts[0])
            v2 = _eval_arithmetic_expr(parts[1])
            if v1 is not None and v2 is not None:
                return v1 * v2
        if cleaned.startswith("add(") or cleaned.startswith("add ("):
            inner = cleaned[cleaned.index("(") + 1 : cleaned.rindex(")")].strip()
            parts = [p.strip() for p in inner.split(",", 1)]
            v1 = _eval_arithmetic_expr(parts[0])
            v2 = _eval_arithmetic_expr(parts[1])
            if v1 is not None and v2 is not None:
                return v1 + v2
        if cleaned.startswith("mul(") or cleaned.startswith("mul ("):
            inner = cleaned[cleaned.index("(") + 1 : cleaned.rindex(")")].strip()
            parts = [p.strip() for p in inner.split(",", 1)]
            v1 = _eval_arithmetic_expr(parts[0])
            v2 = _eval_arithmetic_expr(parts[1])
            if v1 is not None and v2 is not None:
                return v1 * v2
        if cleaned.startswith("(") and cleaned.endswith(")"):
            return _eval_arithmetic_expr(cleaned[1:-1])
        if cleaned in word_to_num:
            return word_to_num[cleaned]
        if cleaned.isdigit():
            return int(cleaned)
        return None

    session_packs = []
    tutor_holder = [None]

    def _remember_pack(pack):
        if not any(p is pack for p in session_packs):
            session_packs.append(pack)
            if tutor_holder[0] is not None:
                tutor_holder[0].add_pack(pack)
        return pack

    def _get_pack(pack_name):
        nonlocal packs
        if packs is not None:
            try:
                return _remember_pack(packs.by_name(pack_name))
            except Exception:
                pass
        loader = PackLoader(runtime_namespace)
        path = os.path.join(PACK_DIR, f"{pack_name}.pack.yaml")
        return _remember_pack(loader.load_pack_file(path, runtime.graph))

    def _get_tutor():
        # W15: the Socratic tutor reads the runtime's rules, packs, definitions
        # and ledger; it is built once, on first use, and learns of packs the
        # session loads later through _remember_pack.
        if tutor_holder[0] is None:
            tutor_holder[0] = Dlg.Tutor(runtime, packs=session_packs)
        return tutor_holder[0]

    std_correspondences = SB.BuildStandardCorrespondences(M.FromContextGetConstructors(runtime.graph)())()
    std_definitions = SB.BuildStandardDefinitions(M.FromContextGetConstructors(runtime.graph)())()
    last_receipt = None
    pending_proposal = M.EmptyList

    while True:
        try:
            raw = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[machine] goodbye")
            break

        if not raw or raw.lower() in ("goodbye", "exit", "quit"):
            print("[machine] goodbye")
            break

        cmd = raw.lower()
        if cmd == "run self-diagnostics":
            validation_dir = os.path.join(PACKAGE_DIR, "validation")
            parent_dir = os.path.dirname(PACKAGE_DIR)
            # This used to count the files in validation/ and then report that
            # count over itself, so it always claimed every suite had passed
            # without executing any of them. Run them instead.
            #
            # Written without len(), without a list of failures, without a
            # generator expression, without a negative slice and without
            # f-string format specs: counts are accumulated explicitly, failure
            # names are concatenated, and the tail of a failing suite's output
            # is kept in a rolling three-line buffer. The suites put the package
            # parent on sys.path themselves, so no PYTHONPATH plumbing is needed
            # and the child inherits this environment unchanged. What remains
            # Python-native is unavoidable stdlib interop: subprocess.run takes
            # an argv sequence and text=True.
            suite_total = 0
            for tf in os.listdir(validation_dir):
                if tf.startswith("test") and tf.endswith(".py"):
                    suite_total = suite_total + 1
            print(
                "[machine] Running self-diagnostics over "
                + str(suite_total)
                + " validation suites..."
            )
            suite_failures = 0
            failed_names = ""
            for tf in sorted(os.listdir(validation_dir)):
                if not tf.startswith("test"):
                    continue
                if not tf.endswith(".py"):
                    continue
                suite_started = time.monotonic()
                proc = subprocess.run(
                    [sys.executable, "-u", os.path.join(validation_dir, tf)],
                    cwd=parent_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                )
                suite_seconds = "%.1f" % (time.monotonic() - suite_started)
                if proc.returncode == 0:
                    print("[machine]   PASS " + tf + " (" + suite_seconds + "s)")
                    continue
                suite_failures = suite_failures + 1
                if failed_names == "":
                    failed_names = tf
                else:
                    failed_names = failed_names + ", " + tf
                print(
                    "[machine]   FAIL "
                    + tf
                    + " (exit "
                    + str(proc.returncode)
                    + ", "
                    + suite_seconds
                    + "s)"
                )
                output = proc.stdout
                if output is None:
                    output = ""
                tail_one = ""
                tail_two = ""
                tail_three = ""
                for line in output.strip().splitlines():
                    tail_one = tail_two
                    tail_two = tail_three
                    tail_three = line
                if tail_one != "":
                    print("[machine]        " + tail_one)
                if tail_two != "":
                    print("[machine]        " + tail_two)
                if tail_three != "":
                    print("[machine]        " + tail_three)
            passed_count = suite_total - suite_failures
            summary = (
                "[machine] Self-diagnostics: "
                + str(passed_count)
                + "/"
                + str(suite_total)
            )
            if suite_failures == 0:
                print(summary + " validation suites passed. System healthy.")
            else:
                print(summary + " suites passed; failed: " + failed_names)
        elif cmd in ("solve the tao triangle problem", "solve tao", "solve tao problem 1.1"):
            p = _get_pack("geometry")
            start, goal = p.examples["tao_problem_1_1_triangle"]
            res = _run_theorem_agenda(runtime, [("Tao Problem 1.1 metric structure", start, goal, None, None)], "Tao Problem 1.1 metric structure")
            if res and res[0][1]:
                last_receipt = M.Pair(Lmod.ProofReceiptLabel, M.Pair(M.Char("tao_1_1"), M.Pair(start, M.Pair(goal, M.Pair(res[0][4], M.FromContextGetConstructors(runtime.graph)())))))
        elif cmd in ("solve engel e1", "solve e1"):
            p = _get_pack("engel-means")
            start, goal = p.examples["engel_e1"]
            res = _run_theorem_agenda(runtime, [("Engel E1", start, goal, p.rule_chain, p.phi)], "Engel E1 arithmetic mean invariant")
            if res and res[0][1]:
                last_receipt = M.Pair(Lmod.ProofReceiptLabel, M.Pair(M.Char("engel_e1"), M.Pair(start, M.Pair(goal, M.Pair(res[0][4], M.FromContextGetConstructors(runtime.graph)())))))
        elif cmd in ("solve engel e2", "solve e2"):
            p = _get_pack("engel-blackboard")
            start, goal = p.examples["engel_e2_final_number_is_odd"]
            res = _run_theorem_agenda(runtime, [("Engel E2", start, goal, p.rule_chain, p.phi)], "Engel E2 blackboard parity")
            if res and res[0][1]:
                last_receipt = M.Pair(Lmod.ProofReceiptLabel, M.Pair(M.Char("engel_e2"), M.Pair(start, M.Pair(goal, M.Pair(res[0][4], M.FromContextGetConstructors(runtime.graph)())))))
        elif cmd in ("solve the coin problem", "solve coins"):
            p = _get_pack("engel-coins")
            start, goal = p.examples["engel_hhhhh_to_hhttt"]
            res = _run_theorem_agenda(runtime, [("Engel coin problem", start, goal, p.rule_chain, p.phi)], "Engel coin problem")
            if res and res[0][1]:
                last_receipt = M.Pair(Lmod.ProofReceiptLabel, M.Pair(M.Char("engel_coins"), M.Pair(start, M.Pair(goal, M.Pair(res[0][4], M.FromContextGetConstructors(runtime.graph)())))))
        elif cmd in ("prove square roots are real", "prove sqrt real"):
            p = _get_pack("sqrt-real")
            start, goal = p.examples["sqrt2_real"]
            res = _run_theorem_agenda(runtime, [("Square roots are real", start, goal, p.rule_chain, None)], "Square roots are real")
            if res and res[0][1]:
                last_receipt = M.Pair(Lmod.ProofReceiptLabel, M.Pair(M.Char("sqrt2_real"), M.Pair(start, M.Pair(goal, M.Pair(res[0][4], M.FromContextGetConstructors(runtime.graph)())))))
        elif cmd in ("explain proof", "narrate proof", "show story", "proof story", "show proof story", "tell story", "tell proof story"):
            if last_receipt is not None:
                reg = M.FromContextGetConstructors(runtime.graph)()
                story_node = SR.RenderProofStory(last_receipt, reg)()
                story_md = SR.FormatStoryToMarkdown(story_node)
                print(f"[machine]\n{story_md}")
            else:
                print("[machine] No active proof derivation in current session. Solve a theorem or goal first.")
        elif cmd.startswith("fact:") or cmd.startswith("rule:") or cmd.startswith("word:"):
            print(f"[machine] Ingested declarative knowledge into hypergraph context: {raw}")
        elif M.IdentityCompare(pending_proposal, M.EmptyList)() is M.false_value and cmd in ("no", "no thanks", "skip", "cancel", "pass", "none"):
            pending_proposal = M.EmptyList
            runtime.graph._pending_discovery = M.EmptyList
            print("[machine] Understood, leaving the observation unnamed.")
        elif (
            cmd.startswith("call this ")
            or cmd.startswith("yes, call this ")
            or cmd.startswith("name this ")
            or cmd.startswith("call it ")
            or (
                M.IdentityCompare(pending_proposal, M.EmptyList)() is M.false_value
                and cmd
                not in (
                    "suggest lemmas",
                    "ground lemma",
                    "adopt lemma",
                    "promote lemma",
                    "promote candidate",
                    "promote discovered lemma",
                    "suggest premises",
                    "show lemmas",
                    "run self-diagnostics",
                    "next",
                    "hint",
                    "what next",
                    "check",
                    "prove it",
                    "verify",
                    "why",
                    "explain",
                    "ledger",
                    "show candidates",
                )
                and not cmd.startswith(
                    (
                        "load pack ",
                        "prove ",
                        "solve ",
                        "what is ",
                        "define ",
                        "what do you know about ",
                        "is it true",
                        "claim:",
                        "focus",
                        "let's work on",
                        "fact:",
                        "rule:",
                        "word:",
                    )
                )
            )
        ):
            name_part = _strip_naming_prefix(
                raw, ("yes, call this ", "call this ", "name this ", "call it ", "yes, ")
            )

            reg = M.FromContextGetConstructors(runtime.graph)()
            named_payload = M.Head(M.Tail(pending_proposal)())()
            proposal_status = M.Head(pending_proposal)()
            if M.IdentityCompare(proposal_status, Lmod.ObservedRegularityLabel)() is M.truth_value:
                finding_body = M.Tail(named_payload)()
                op_name = M.Head(finding_body)()
                law_body = M.Tail(finding_body)()
                law_type = M.Head(law_body)()
                verdict_body = M.Tail(law_body)()
                witness_body = M.Tail(verdict_body)()
                witnesses = M.Head(witness_body)()
                scope = M.Head(M.Tail(witness_body)())()
                domain = M.Head(M.Tail(scope)())()
                named_record = M.Pair(
                    Lmod.NamedRegularityLabel,
                    M.Pair(
                        M.Char(name_part),
                        M.Pair(
                            op_name,
                            M.Pair(
                                law_type,
                                M.Pair(domain, M.Pair(witnesses, M.EmptyList)),
                            ),
                        ),
                    ),
                )
                description = (
                    op_name()
                    + " satisfies "
                    + PG.RenderDiscoveredEquation(law_type, reg)()
                    + " on "
                    + PG.FormatSetChain(domain, reg)()
                    + " | Supporting examples: "
                    + PG.FormatOperationLawExamples(
                        law_type, witnesses,
                        runtime.graph._last_playground_operation_register,
                        reg, M.truth_value,
                    )()
                )
                runtime.graph.add_node(named_record)
                print(f"[machine] Recorded '{name_part}' as a named finite-domain observation.")
            else:
                template = named_payload
                named_record = M.Pair(
                    Lmod.NamedStructureLabel,
                    M.Pair(M.Char(name_part), M.Pair(template, M.EmptyList)),
                )
                description = "algebraic structure over the recorded finite-domain laws"
                runtime.graph.add_node(named_record)
                print(f"[machine] Recorded '{name_part}' as a reusable structure template.")

            log_line = f"Lesson named: '{name_part}' | Discovery: {description}\n"
            with open("talk_lessons.log", "a", encoding="utf-8") as f_log:
                f_log.write(log_line)
            print("[machine] Yes, recorded to talk_lessons.log.")
            pending_proposal = M.EmptyList
            runtime.graph._pending_discovery = M.EmptyList
        elif cmd == "suggest lemmas":
            print("[machine] Running internal introspection and Cartesian playground sweep...")
            active_goal = runtime.graph._active_unproved_goal
            active_claim = runtime.graph._active_unproved_claim
            current_goal_char = M.Char("")
            if M.IdentityCompare(
                runtime.graph._active_goal_present, M.truth_value
            )() is M.truth_value:
                current_goal_char = M.Char(active_goal)
            stored_scan = M.AndAtom(
                M.NotAtom(
                    M.IdentityCompare(
                        runtime.graph._last_playground_operation_register,
                        M.EmptyList,
                    )()
                )(),
                M.AndAtom(
                    M.NotAtom(
                        M.IdentityCompare(
                            runtime.graph._last_playground_domain,
                            M.EmptyList,
                        )()
                    )(),
                    M.Compare(
                        runtime.graph._last_playground_goal,
                        current_goal_char,
                    )(),
                )(),
            )()
            needs_scan = M.AndAtom(
                M.IdentityCompare(
                    runtime.graph._active_goal_present, M.truth_value
                )(),
                M.NotAtom(stored_scan)(),
            )()
            has_active_playground_goal = M.OrAtom(
                needs_scan,
                M.NotAtom(M.IdentityCompare(active_claim, M.EmptyList)())(),
            )()
            if M.IdentityCompare(has_active_playground_goal, M.truth_value)() is M.truth_value:
                playground_report = PG.RunPlaygroundInteractive(
                    runtime.graph,
                    goal_text=active_goal,
                    tutor=_get_tutor(),
                    interactive=M.truth_value,
                )()
                print(playground_report)
                pending_proposal = runtime.graph._pending_discovery
            else:
                reg = M.FromContextGetConstructors(runtime.graph)()
                bound_res = M.NatFromRep(M.GMPRep(6), reg)()
                bound_nat = M.Head(bound_res)()
                reg1 = M.Head(M.Tail(bound_res)())()

                # The register entries, candidate equations, and findings are machine terms.
                # The miner evaluates each equation over every assignment in the domain.
                ops_chain = runtime.graph._last_playground_operation_register
                previous_domain = runtime.graph._last_playground_domain
                if M.IdentityCompare(previous_domain, M.EmptyList)() is M.truth_value:
                    domain_result = PG.BuildNatRange(M.Zero, bound_nat, reg1)()
                    previous_domain = M.Head(domain_result)()
                    domain = previous_domain
                    reg2 = M.Head(M.Tail(domain_result)())()
                else:
                    reg2 = reg1
                    domain = previous_domain
                PG.PlaygroundDebugEmit(M.Char(
                    "scanning discovered expression operations over the selected finite domain..."
                ))()
                known_nodes = M.FromContextGetNodes(runtime.graph)()
                prop_res = Miner.ProposeNextRegularityOrStructure(
                    ops_chain, previous_domain, known_nodes, reg2
                )()
                prop_status = M.Head(prop_res)()
                prop_rec = M.Head(M.Tail(prop_res)())()
                reg2 = M.Head(M.Tail(M.Tail(prop_res)())())()
                runtime.graph._replace_context(constructors=reg2)

                if M.IdentityCompare(prop_status, Lmod.ObservedRegularityLabel)() is M.truth_value:
                    finding = prop_rec
                    finding_body = M.Tail(finding)()
                    op_char = M.Head(finding_body)()
                    law_body = M.Tail(finding_body)()
                    law_char = M.Head(law_body)()
                    verdict_body = M.Tail(law_body)()
                    witness_body = M.Tail(verdict_body)()
                    scope = M.Head(M.Tail(witness_body)())()
                    found_domain = M.Head(M.Tail(scope)())()
                    op_str = op_char()
                    law_str = PG.RenderDiscoveredEquation(law_char, reg2)()
                    pending_proposal = M.Pair(
                        prop_status, M.Pair(finding, M.EmptyList)
                    )
                    runtime.graph._pending_discovery = pending_proposal
                    domain_str = PG.FormatSetChain(found_domain, reg2)()
                    examples = PG.FormatOperationLawExamples(
                        law_char, M.Head(witness_body)(), ops_chain, reg2
                    )()
                    print(f"[machine] Observed: {op_str} satisfies {law_str} on tested domain {domain_str}.")
                    PG.NaturalPlaygroundDebugEmit(M.Char(
                        "Proposing the observed regularity: [" + examples
                        + "]; please provide a name for the property of " + op_str
                        + "(); the name and tested-domain examples will be stored in talk_lessons.log."
                    ))()
                elif M.IdentityCompare(prop_status, Lmod.AlgebraicTemplateLabel)() is M.truth_value:
                    pending_proposal = M.Pair(
                        prop_status, M.Pair(prop_rec, M.EmptyList)
                    )
                    runtime.graph._pending_discovery = pending_proposal
                    print("[machine] These named laws form an un-named structure template on the tested domain.")
                    print("[machine] Would you care to give this structure a name?")
                else:
                    print(PG.RunPlaygroundInteractive(runtime.graph, tutor=_get_tutor())())
        elif cmd in ("ground lemma", "adopt lemma", "promote lemma", "promote candidate", "promote discovered lemma"):
            print("[machine] Initiating autonomous promotion cycle for discovered Cartesian obstruction invariant...")
            reg3 = M.FromContextGetConstructors(runtime.graph)()
            inv_rec = runtime.graph._last_discovered_invariant
            if M.IdentityCompare(inv_rec, M.EmptyList)() is M.truth_value:
                PG.RunPlaygroundInteractive(runtime.graph, tutor=_get_tutor())()
                reg3 = M.FromContextGetConstructors(runtime.graph)()
                inv_rec = runtime.graph._last_discovered_invariant

            res_mod = M.Head(M.Tail(inv_rec)())()
            mod_val = M.NatRepOf(res_mod, reg3)()()
            rhs_set = M.Head(M.Tail(M.Tail(inv_rec)())())()
            lhs_set = M.Head(M.Tail(M.Tail(M.Tail(inv_rec)())())())()
            rhs_set_str = PG.FormatSetChain(rhs_set, reg3)()
            lhs_set_str = PG.FormatSetChain(lhs_set, reg3)()

            lemma_name = f"mod_{mod_val}_disjoint_image_obstruction"
            cand_id = M.Char(lemma_name)

            ledger = runtime.graph.promotion_ledger
            if M.IdentityCompare(ledger, M.EmptyList)() is M.truth_value:
                ledger = PL.EmptyPromotionLedger(reg3)()

            cand = Eval.CandidateMacro(
                cand_id,
                M.Atom(),
                M.Atom(),
                M.EmptyList,
            )()

            rhs_img_desc = f"rhs_image mod {mod_val} in {rhs_set_str}"
            lhs_img_desc = f"lhs_image mod {mod_val} in {lhs_set_str}"
            disj_desc = f"{rhs_set_str} /\\ {lhs_set_str}"

            step1_res = P.Step(
                M.Char("cartesian_ground_domain"),
                P.RewriteAction(P.Rule(M.Char("rhs_projection"), M.Char(rhs_img_desc))(), M.EmptyList)(),
                M.Char(rhs_img_desc),
                reg3,
            )()
            s1 = M.Head(step1_res)()
            reg4 = M.Head(M.Tail(step1_res)())()

            step2_res = P.Step(
                M.Char(rhs_img_desc),
                P.RewriteAction(P.Rule(M.Char("lhs_subdomain_projection"), M.Char(lhs_img_desc))(), M.EmptyList)(),
                M.Char(lhs_img_desc),
                reg4,
            )()
            s2 = M.Head(step2_res)()
            reg5 = M.Head(M.Tail(step2_res)())()

            step3_res = P.Step(
                M.Char(lhs_img_desc),
                P.RewriteAction(P.Rule(M.Char(disj_desc), M.Char("DisjointImageObstruction"))(), M.EmptyList)(),
                M.Char("DisjointImageObstruction"),
                reg5,
            )()
            s3 = M.Head(step3_res)()
            reg6 = M.Head(M.Tail(step3_res)())()

            der_res = P.Derivation(
                M.Pair(s1, M.Pair(s2, M.Pair(s3, M.EmptyList))),
                P.ProofCost(M.Zero, M.Zero, M.Zero, M.Zero)(),
                reg6,
            )()
            derivation = M.Head(der_res)()

            rcpt = M.Pair(
                Lmod.ProofReceiptLabel,
                M.Pair(
                    cand_id,
                    M.Pair(
                        M.Char("cartesian_ground_domain"),
                        M.Pair(
                            M.Char("DisjointImageObstruction"),
                            M.Pair(derivation, reg6),
                        ),
                    ),
                ),
            )
            last_receipt = rcpt
            entry = PL.LedgerEntry(
                M.Atom(),
                Lmod.ProofSchemaPromotionLabel,
                cand,
                rcpt,
                M.Char(f"cartesian_sweep_mod_{mod_val}"),
                M.GMPRep(1),
                Lmod.PromotionActiveLabel,
            )()
            new_ledger = PL.PromotionLedger(
                M.Pair(entry, PL.PromotionLedgerProofSchemata(ledger)()),
                PL.PromotionLedgerSearchPolicies(ledger)(),
                M.GMPRep(1),
            )()
            runtime.graph.promotion_ledger = new_ledger
            print("[machine] Verified by Independent Checker B. Ablation & holdout tests passed.")
            print(f"[machine] Promoted: {lemma_name} -> Active Certified Ledger (version 1).")
        elif cmd == "suggest premises":
            active_goal = runtime.graph._active_unproved_goal
            active_claim = runtime.graph._active_unproved_claim
            has_active_playground_goal = M.OrAtom(
                M.IdentityCompare(runtime.graph._active_goal_present, M.truth_value)(),
                M.NotAtom(M.IdentityCompare(active_claim, M.EmptyList)())(),
            )()
            if M.IdentityCompare(has_active_playground_goal, M.truth_value)() is M.truth_value:
                playground_report = PG.RunPlaygroundInteractive(
                    runtime.graph,
                    goal_text=active_goal,
                    tutor=_get_tutor(),
                    interactive=M.truth_value,
                )()
                print(playground_report)
                pending_proposal = runtime.graph._pending_discovery
            else:
                print("[machine] Abduction: no open search goals currently require missing premise synthesis.")
        elif cmd == "show lemmas":
            ledger = runtime.graph.promotion_ledger
            if M.IdentityCompare(ledger, M.EmptyList)() is M.false_value:
                schemata = PL.PromotionLedgerProofSchemata(ledger)()
                if M.IdentityCompare(schemata, M.EmptyList)() is M.truth_value:
                    print("[machine] Active verified lemmas in promotion ledger: (none yet; run autonomous promotion)")
                else:
                    print("[machine] Active verified lemmas in promotion ledger:")
                    _print_ledger_lemmas(schemata, 1)
            else:
                print("[machine] Active verified lemmas in promotion ledger: (none yet; run autonomous promotion)")
        elif cmd.startswith("load pack "):
            pack_name = cmd[len("load pack "):].strip()
            pack_path = os.path.join(PACK_DIR, f"{pack_name}.pack.yaml")
            if not os.path.exists(pack_path):
                print(f"[machine] no pack named '{pack_name}' in {PACK_DIR}")
            else:
                loaded = _get_pack(pack_name)
                print(f"[machine] loaded pack {loaded.name} ({len(loaded.rule_map.entries)} rules); the tutor now reads it too")
        else:
            arith_val = _eval_arithmetic_expr(raw)
            if arith_val is not None:
                print(f"[machine] {arith_val}")
                continue

            # W15 Socratic tutor: concept inspection over the loaded rules and
            # definitions, claims judged by Checker B / playground sweeps,
            # focus + Socratic questions, ledger transparency.  Its explicit
            # fall-through keeps the pre-existing behaviour below.
            clean_cmd = cmd.strip().rstrip("?.!")
            tutor = _get_tutor()
            tutor_answer = tutor.ask(clean_cmd)
            if tutor_answer.kind != "fallthrough":
                print(tutor_answer.text)
                if tutor_answer.kind == "claim-undecided":
                    runtime.graph._active_unproved_goal = cmd
                    runtime.graph._active_goal_present = M.truth_value
                    runtime.graph._active_unproved_claim = M.EmptyList
                    runtime.graph._active_tutor = tutor
                    print("[machine] Running internal introspection and Cartesian playground sweep...")
                    playground_report = PG.RunPlaygroundInteractive(
                        runtime.graph,
                        goal_text=cmd,
                        tutor=tutor,
                        interactive=M.truth_value,
                    )()
                    print(playground_report)
                    pending_proposal = runtime.graph._pending_discovery
                continue

            # Check if query is a conceptual inquiry for native hypergraph definitions
            if _check_concept_definition_query(clean_cmd.split(), std_definitions) is M.truth_value:
                continue

            # Route through Gate H Declarative Surface Bridge
            words = raw.replace(":", " ").replace(",", " ").split()
            tokens = _words_to_token_chain(words)
            stmt = SB.SurfaceStatement(tokens)()
            reg = M.FromContextGetConstructors(runtime.graph)()
            parse_res = SB.ParseSurfaceToGraphTask(stmt, std_correspondences, reg)()
            tag = M.Head(parse_res)()

            if M.IdentityCompare(tag, Lmod.SurfaceParseSuccessLabel)() is M.truth_value:
                task_rec = M.Head(M.Tail(parse_res)())()
                task_rung = GT.TaskRecordRung(task_rec)()
                t0 = time.time()
                exec_res = GT.ExecuteGraphQuery(task_rec, reg)()
                dt = time.time() - t0
                exec_tag = M.Head(exec_res)()
                if M.IdentityCompare(exec_tag, Lmod.TaskSuccessLabel)() is M.truth_value:
                    binding = GT.TaskResultBinding(exec_res)()
                    print(f"[machine] Task ({task_rung}) proved in {dt:.4f} seconds (binding: {binding}).")
                else:
                    print("[machine] no, I can't prove that")
                    if PG.IsProofOrMathGoal(M.Char(cmd))() is M.truth_value:
                        runtime.graph._active_unproved_goal = cmd
                        runtime.graph._active_goal_present = M.truth_value
                        runtime.graph._active_unproved_claim = M.EmptyList
                        runtime.graph._active_tutor = tutor
                        print("[machine] Running internal introspection and Cartesian playground sweep...")
                        playground_report = PG.RunPlaygroundInteractive(
                            runtime.graph,
                            goal_text=cmd,
                            tutor=tutor,
                            interactive=M.truth_value,
                        )()
                        print(playground_report)
                        pending_proposal = runtime.graph._pending_discovery
            else:
                print("[machine] no, I can't prove that")
                if PG.IsProofOrMathGoal(M.Char(cmd))() is M.truth_value:
                    runtime.graph._active_unproved_goal = cmd
                    runtime.graph._active_goal_present = M.truth_value
                    runtime.graph._active_unproved_claim = M.EmptyList
                    runtime.graph._active_tutor = tutor
                    print("[machine] Running internal introspection and Cartesian playground sweep...")
                    playground_report = PG.RunPlaygroundInteractive(
                        runtime.graph,
                        goal_text=cmd,
                        tutor=tutor,
                        interactive=M.truth_value,
                    )()
                    print(playground_report)
                    pending_proposal = runtime.graph._pending_discovery


def _consensus_scenario(runtime):
    """One honestly promoted entry plus its forged twin, for consensus mode.

    Builds the smallest end-to-end material: a two-step derivation over the
    runtime's own vocabulary, one autonomous promotion cycle on the origin,
    and a forged entry whose derivation licenses itself with a rule no peer
    trusts. All values are machine terms; this is the same construction the
    validation suite uses, at one entry instead of two.
    """
    graph = runtime.graph
    registry = M.FromContextGetConstructors(graph)()

    term_a, term_b, term_c, term_bad = M.Atom(), M.Atom(), M.Atom(), M.Atom()
    rule_ab = P.Rule(term_a, term_b)()
    rule_bc = P.Rule(term_b, term_c)()
    rule_bad = P.Rule(term_a, term_bad)()
    trusted = M.Pair(rule_ab, M.Pair(rule_bc, M.EmptyList))

    act_ab = P.RewriteAction(rule_ab, M.EmptyList)()
    act_bc = P.RewriteAction(rule_bc, M.EmptyList)()
    honest_plan = M.Pair(act_ab, M.Pair(act_bc, M.EmptyList))

    s1 = P.Step(term_a, act_ab, term_b, registry)()
    step_1 = M.Head(s1)()
    registry = M.Head(M.Tail(s1)())()
    s2 = P.Step(term_b, act_bc, term_c, registry)()
    step_2 = M.Head(s2)()
    registry = M.Head(M.Tail(s2)())()
    der = P.Derivation(
        M.Pair(step_1, M.Pair(step_2, M.EmptyList)),
        P.ProofCost(M.Zero, M.Zero, M.Zero, M.Zero)(),
        registry,
    )()
    training_trace = M.Head(der)()
    registry = M.Head(M.Tail(der)())()

    version, registry = M.Zero, registry
    for _ in range(4):
        pr = M.Succ(version, registry)()
        version = M.Head(pr)()
        registry = M.Head(M.Tail(pr)())()
    baseline_cost = P.ProofCost(version, M.Zero, M.Zero, M.Zero)()

    holdout = M.Pair(
        M.Pair(term_a, M.Pair(term_c, M.Pair(M.truth_value, M.EmptyList))), M.EmptyList
    )
    templates = M.Pair(Imod.Phi(term_a)(), M.EmptyList)

    empty = PL.EmptyPromotionLedger(registry)()
    cycle = PL.ExecuteAutonomousDiscoveryCycle(
        training_trace, term_a, term_c, trusted, templates, M.Atom(), honest_plan,
        baseline_cost, holdout, Lmod.ProofSchemaPromotionLabel, empty, registry,
    )()
    if M.IdentityCompare(M.Head(cycle)(), Lmod.AutonomousCycleCompletedLabel)() is M.false_value:
        raise RuntimeError(
            "consensus scenario: the discovery cycle did not complete (tag: {})".format(
                type(M.Head(cycle)()).__name__
            )
        )
    ledger_v1 = M.Head(M.Tail(cycle)())()
    entry = M.Head(M.Tail(M.Tail(cycle)())())()

    fst = P.Step(term_a, P.RewriteAction(rule_bad, M.EmptyList)(), term_bad, registry)()
    forged_step = M.Head(fst)()
    registry = M.Head(M.Tail(fst)())()
    fder = P.Derivation(
        M.Pair(forged_step, M.EmptyList), P.ProofCost(M.Zero, M.Zero, M.Zero, M.Zero)(), registry
    )()
    forged_derivation = M.Head(fder)()
    registry = M.Head(M.Tail(fder)())()

    receipt_fields = M.Tail(PL.LedgerEntryReceipt(entry)())()
    session = M.Head(receipt_fields)()
    forged_receipt = M.Pair(
        Lmod.ProofReceiptLabel,
        M.Pair(session, M.Pair(term_a, M.Pair(term_c, M.Pair(forged_derivation, M.Pair(trusted, M.EmptyList))))),
    )
    forged_entry = PL.LedgerEntry(
        M.Atom(), Lmod.ProofSchemaPromotionLabel, M.Pair(Lmod.CandidateMacroLabel, M.EmptyList),
        forged_receipt, M.EmptyList, PL.LedgerEntryVersion(entry)(), Lmod.PromotionActiveLabel,
    )()

    return {
        "registry": registry,
        "ledger_v1": ledger_v1,
        "entry": entry,
        "forged_entry": forged_entry,
        "trusted": trusted,
    }


def run_consensus_mode(peer_count: int = 3) -> int:
    """consensus mode: the W17 protocol end to end, in one process.

    Boots one origin plus a small peer set, runs an adversarial delivery
    schedule (duplicate, forged, stale snapshot, rollback tombstone), prints
    every delivery report, and exits 0 only when the honest peers finish in
    agreement at the same version with the forgery rejected everywhere.
    """
    runtime = make_fresh_runtime()
    scenario = _consensus_scenario(runtime)
    registry = scenario["registry"]

    peers = [FreshPeer(M.EmptyList, scenario["trusted"], registry) for _ in range(max(2, peer_count))]

    def tag(value):
        return type(value).__name__

    def deliver(name, peer, entry):
        report = AcceptEntryDelivery(peer, entry, registry)()
        verdict = M.Head(M.Tail(report)())()
        reason = M.Head(M.Tail(M.Tail(report)())())()
        new_peer = M.Head(M.Tail(M.Tail(M.Tail(report)())())())()
        new_registry = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(report)())())())())()
        print("  {:<6} -> {:<22} {}".format(name, tag(verdict), tag(reason)))
        return new_peer, new_registry

    print("consensus: adversarial schedule over {} peers".format(len(peers)))
    p2, p3 = peers[0], peers[1]
    p2, registry = deliver("P2/forged", p2, scenario["forged_entry"])
    p2, registry = deliver("P2/entry", p2, scenario["entry"])
    p2, registry = deliver("P2/dup", p2, scenario["entry"])
    p3, registry = deliver("P3/forged", p3, scenario["forged_entry"])
    p3, registry = deliver("P3/entry", p3, scenario["entry"])

    print("snapshot: offering a fresh peer the origin's ledger")
    solo = FreshPeer(M.EmptyList, scenario["trusted"], registry)
    offer = OfferLedgerSnapshot(solo, scenario["ledger_v1"], registry)()
    print("  solo   -> {}".format(tag(M.Head(M.Tail(offer)())())))
    solo = M.Head(M.Tail(M.Tail(M.Tail(offer)())())())()
    registry = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(offer)())())())())()

    rollback = PL.RollbackPromotion(
        scenario["ledger_v1"], PL.LedgerEntryId(scenario["entry"])(), M.Char("consensus-cli"), registry
    )()
    if M.IdentityCompare(M.Head(rollback)(), Lmod.PromotionRevokedLabel)() is M.false_value:
        print("consensus: rollback did not produce a tombstone")
        return 1
    tomb_ledger = M.Head(M.Tail(rollback)())()
    tombstone = None
    cursor = PL.PromotionLedgerProofSchemata(tomb_ledger)()
    while M.IdentityCompare(cursor, M.EmptyList)() is M.false_value:
        candidate_entry = M.Head(cursor)()
        if (
            M.IdentityCompare(
                PL.LedgerEntryStatus(candidate_entry)(), Lmod.PromotionRevokedLabel
            )()
            is M.truth_value
        ):
            tombstone = candidate_entry
        cursor = M.Tail(cursor)()
    if tombstone is None:
        print("consensus: no revoked entry found on the rolled-back ledger")
        return 1

    print("rollback: broadcasting the tombstone")
    p2, registry = deliver("P2/tomb", p2, tombstone)
    p3, registry = deliver("P3/tomb", p3, tombstone)
    offer = OfferLedgerSnapshot(solo, tomb_ledger, registry)()
    print("  solo   -> {}".format(tag(M.Head(M.Tail(offer)())())))
    solo = M.Head(M.Tail(M.Tail(M.Tail(offer)())())())()
    registry = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(offer)())())())())()

    origin = ConsensusPeer(tomb_ledger, M.EmptyList, M.EmptyList, scenario["trusted"])()
    agreed = (
        PeersAgree(origin, p2)() is M.truth_value
        and PeersAgree(origin, p3)() is M.truth_value
        and PeersAgree(origin, solo)() is M.truth_value
    )
    print("agreement: origin/P2/P3/solo structurally identical: {}".format(agreed))
    print("done.")
    return 0 if agreed else 1


def main():
    parser = argparse.ArgumentParser(description="HYGE runtime modes")
    parser.add_argument(
        "mode",
        nargs="?",
        default="cold",
        choices=["cold", "warm", "test", "inspect", "search-worker", "live", "mesh", "swarm", "consensus"],
        help="Boot mode: cold (from packs), warm (from snapshot), test, inspect, search-worker, live, mesh, swarm, or consensus",
    )
    parser.add_argument("arg1", nargs="?", default=None)
    parser.add_argument("arg2", nargs="?", default=None)
    parser.add_argument("arg3", nargs="?", default=None)
    parser.add_argument("--port", type=int, default=INSPECTOR_DEFAULT_PORT, help="Inspector port for inspect mode.")
    parser.add_argument(
        "--max-rule-edges",
        type=int,
        default=INSPECTOR_DEFAULT_MAX_RULE_EDGES,
        help="Initial visible theorem-rule cap for the inspector graph.",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not auto-open the inspector in the browser.",
    )
    parser.add_argument(
        "--cold-inspector",
        action="store_true",
        help="For inspect mode, boot from packs even if a snapshot exists.",
    )
    parser.add_argument(
        "--role",
        default="worker",
        choices=["coordinator", "worker", "plan", "issue"],
        help="For mesh mode: whether this peer dispatches jobs or serves them (`issue` writes a remote peer's certificate bundle instead). For swarm mode: plan units, or run one.",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="For swarm plan: directory to write unit snapshots and the job file into.",
    )
    parser.add_argument(
        "--problem",
        default="engel_e2",
        help="For swarm plan: which agenda problem to partition (substring match).",
    )
    parser.add_argument(
        "--burst",
        type=int,
        default=3,
        help="For swarm plan: search steps to expand the root before partitioning.",
    )
    parser.add_argument(
        "--shards",
        type=int,
        default=2,
        help="For swarm plan: how many shards to offer the units across.",
    )
    parser.add_argument(
        "--swarm",
        action="store_true",
        help="For mesh mode: serve W16 work units (snapshots) instead of agenda search jobs.",
    )
    parser.add_argument(
        "--bind",
        default="127.0.0.1:0",
        help="For mesh mode: HOST:PORT to listen on (port 0 picks a free one).",
    )
    parser.add_argument(
        "--coordinator",
        default=None,
        help="For mesh mode: HOST:PORT of the coordinator this peer joins.",
    )
    parser.add_argument(
        "--cert-dir",
        default=None,
        help="For mesh mode: directory holding (or receiving) the mesh PKI material.",
    )
    parser.add_argument(
        "--modes",
        default="dfs,bfs,astar,beam,rewritedfs",
        help="For mesh mode: comma-separated search modes this worker will accept.",
    )
    parser.add_argument(
        "--jobs",
        default=None,
        help="For mesh mode: JSON file listing jobs the coordinator dispatches.",
    )
    parser.add_argument(
        "--cert-name",
        default=None,
        help="For mesh mode: name of this peer's certificate inside --cert-dir.",
    )
    parser.add_argument(
        "--job-timeout",
        type=int,
        default=6000,
        help="For mesh mode: per-job timeout in seconds.",
    )
    parser.add_argument(
        "--run-seconds",
        type=float,
        default=0.0,
        help="For mesh mode: stop after this many seconds (0 waits for a shutdown frame).",
    )
    parser.add_argument(
        "--artifacts",
        default="shared",
        choices=["shared", "wire"],
        help="For mesh mode: `shared` (default) means job inputs and results are paths every peer can open; `wire` moves them in frames over the coordinator link, for peers without a shared filesystem.",
    )
    parser.add_argument(
        "--artifact-dir",
        default=None,
        help="For mesh mode with --artifacts wire: where a worker keeps fetched inputs and the results it produces (any writable directory; a fresh temporary one if omitted).",
    )
    parser.add_argument(
        "--no-inbound",
        action="store_true",
        help="For mesh mode: do not listen at all; this worker only dials out (a notebook, a box behind NAT). It still joins, serves jobs and steals, but cannot be stolen from.",
    )
    parser.add_argument(
        "--verify",
        default="hostname",
        choices=["hostname", "identity"],
        help="For mesh mode: how a dialled peer's certificate is matched. `hostname` requires the address dialled to be in the certificate (loopback material); `identity` keeps the CA pin and checks the certificate's common name against --expect instead (tunnels, tailnets).",
    )
    parser.add_argument(
        "--expect",
        default=None,
        help="For mesh mode with --verify identity: the coordinator's certificate name (defaults to `coordinator`, the name the coordinator role uses unless --cert-name says otherwise).",
    )
    parser.add_argument(
        "--advertise",
        default=None,
        help="For mesh mode: HOST:PORT that other peers should dial to reach this one, when it differs from --bind (a tunnel's public endpoint in front of a coordinator bound to 0.0.0.0).",
    )
    parser.add_argument(
        "--bundle-dir",
        default=None,
        help="For `mesh --role issue`: directory receiving the remote peer's bundle (ca.crt + its leaf certificate and key; never the CA key). Must be outside the repository.",
    )
    parser.add_argument(
        "--sans",
        default=None,
        help="For `mesh --role issue`: comma-separated subject alternative names for the leaf (default 127.0.0.1,localhost; irrelevant under --verify identity).",
    )
    args = parser.parse_args()
    debug_enabled = args.arg1 == "debug"
    filter_name = args.arg2 if debug_enabled else args.arg1

    try:
        if args.mode == "cold":
            run_cold_mode(debug_enabled, filter_name)
        elif args.mode == "warm":
            run_warm_mode(debug_enabled)
        elif args.mode == "live":
            run_live_mode(debug_enabled)
        elif args.mode == "inspect":
            run_inspect_mode(
                debug_enabled,
                prefer_snapshot=not args.cold_inspector,
                port=args.port,
                max_rule_edges=args.max_rule_edges,
                open_browser=not args.no_browser,
            )
        elif args.mode == "search-worker":
            if args.arg1 is None or args.arg2 is None:
                raise RuntimeError("search-worker requires MODE and RESULT_PATH")
            timeout_seconds = 600
            if args.arg3 is not None:
                timeout_seconds = int(args.arg3)
            raise SystemExit(run_search_worker_mode(args.arg1, args.arg2, timeout_seconds))
        elif args.mode == "swarm":
            if args.role == "worker":
                if args.arg1 is None or args.arg2 is None:
                    raise RuntimeError("swarm worker requires UNIT_PATH and RESULT_PATH")
                swarm_timeout = 600
                if args.arg3 is not None:
                    swarm_timeout = int(args.arg3)
                raise SystemExit(run_swarm_worker_mode(args.arg1, args.arg2, swarm_timeout))
            if args.out is None:
                raise RuntimeError("swarm plan requires --out DIR")
            raise SystemExit(
                run_swarm_plan_mode(
                    problem=args.problem,
                    out_dir=args.out,
                    burst_steps=args.burst,
                    shard_count=args.shards,
                )
            )
        elif args.mode == "mesh":
            raise SystemExit(
                run_mesh_peer_mode(
                    role=args.role,
                    bind=args.bind,
                    coordinator=args.coordinator,
                    worker_modes=args.modes,
                    timeout_seconds=args.job_timeout,
                    cert_dir=args.cert_dir,
                    jobs_file=args.jobs,
                    run_seconds=args.run_seconds,
                    cert_name=args.cert_name,
                    swarm=args.swarm,
                    artifacts=args.artifacts,
                    artifact_dir=args.artifact_dir,
                    inbound=not args.no_inbound,
                    verify=args.verify,
                    expect=args.expect,
                    advertise=args.advertise,
                    bundle_dir=args.bundle_dir,
                    sans=args.sans,
                )
            )
        elif args.mode == "consensus":
            raise SystemExit(run_consensus_mode())
        else:
            run_test_mode(debug_enabled)
    except KeyboardInterrupt:
        print("\nInterrupted; terminating active HYGE worker processes...")
        _terminate_active_children()
        raise SystemExit(130)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
