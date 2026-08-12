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
    from .runtime import boot_from_packs, boot_from_snapshot, save_runtime
    from .persistence import SnapshotCodec
    from . import invariance as Imod
    from . import search as Smod
    from . import theorem_rules as T
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
    os.path.join(PACK_DIR, "real-closure.pack.yaml"),
    os.path.join(PACK_DIR, "arithmetic.pack.yaml"),
    os.path.join(PACK_DIR, "geometry-ontology.pack.yaml"),
    os.path.join(PACK_DIR, "trigonometry.pack.yaml"),
    os.path.join(PACK_DIR, "geometry.pack.yaml"),
    os.path.join(PACK_DIR, "engel-coins.pack.yaml"),
    os.path.join(PACK_DIR, "engel-means.pack.yaml"),
]

def _latest_snapshot_path():
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
    if filter_name in ("sqrt", "isreal", "sqrt-real", "real", "isreal_sqrt", "isreal-sqrt", "isreal(sqrt())", "all", "sqrt2", "sqrt3", "sqrt4"):
        sqrt_pack = packs.by_name("sqrt-real")
        for example_id in ("sqrt2_real", "sqrt3_real", "sqrt4_real"):
            if filter_name in ("sqrt2", "sqrt3", "sqrt4"):
                if (filter_name + "_real" == example_id) is False:
                    continue
            if example_id in sqrt_pack.examples:
                start, goal = sqrt_pack.examples[example_id]
<<<<<<< HEAD
                cases.append((example_id, start, goal))
=======
                cases.append((example_id, start, goal, None, None))
>>>>>>> 843917a (Prove Knowledge boards by pack phi: preserve, then prune.)
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


def run_search_worker_mode(worker_mode: str, result_path: str, timeout_seconds: int = 6000):
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
    else:
        runtime, packs = boot_from_packs(PACK_PATHS, _runtime_namespace())
        registry = M.FromContextGetConstructors(runtime.graph)()
        worker_heuristic = _search_worker_mode_heuristic(runtime, worker_mode, registry)
        label, start, goal, _rules, _phi = _search_worker_problem_from_manifest(packs, result_path, worker_heuristic, registry)
        start = Hmod.HeuristicCanonicalize(start, worker_heuristic, registry)()
        goal = Hmod.HeuristicCanonicalize(goal, worker_heuristic, registry)()
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


def main():
    parser = argparse.ArgumentParser(description="HYGE runtime modes")
    parser.add_argument(
        "mode",
        nargs="?",
        default="cold",
        choices=["cold", "warm", "test", "inspect", "search-worker"],
        help="Boot mode: cold (from packs), warm (from snapshot), test, inspect, or search-worker",
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
    args = parser.parse_args()
    debug_enabled = args.arg1 == "debug"
    filter_name = args.arg2 if debug_enabled else args.arg1

    try:
        if args.mode == "cold":
            run_cold_mode(debug_enabled, filter_name)
        elif args.mode == "warm":
            run_warm_mode(debug_enabled)
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
        else:
            run_test_mode(debug_enabled)
    except KeyboardInterrupt:
        print("\nInterrupted; terminating active HYGE worker processes...")
        _terminate_active_children()
        raise SystemExit(130)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
