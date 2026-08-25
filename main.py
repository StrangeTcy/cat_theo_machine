from __future__ import annotations

import argparse
import http.server
import io
import json
import multiprocessing
import os
import subprocess
import sys
import time
import urllib.parse
import webbrowser
from contextlib import redirect_stdout

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
    from .persistence import SnapshotCodec, SnapshotSaveDeadline, SnapshotSaveTimeout
    from . import invariance as Imod
    from . import search as Smod
    from . import theorem_rules as T
    from . import wire as W
    from . import session as Sess
    from . import daemon as Dmn
    from .testsuite import install_default_tests


PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
PACK_DIR = os.path.join(PACKAGE_DIR, "packs")
SNAPSHOT_DIR = os.path.join(PACKAGE_DIR, "snapshots")
INSPECTOR_DIR = os.path.join(PACKAGE_DIR, "inspector")
SNAPSHOT_NAME = "hyge_snapshot_v8.json"
SNAPSHOT_SAVE_TIMEOUT_SECONDS = 120.0
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
    os.path.join(PACK_DIR, "number-theory.pack.yaml"),
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


def _save_snapshot_now(
    runtime,
    runtime_namespace,
    snapshot_path=None,
    timeout_seconds=SNAPSHOT_SAVE_TIMEOUT_SECONDS,
):
    target_path = SNAPSHOT_PATH if snapshot_path is None else snapshot_path
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    deadline = SnapshotSaveDeadline(timeout_seconds)
    print(
        "snapshot save: "
        + format(timeout_seconds, ".0f")
        + "-second deadline started for "
        + target_path,
        flush=True,
    )
    try:
        save_runtime(runtime, target_path, runtime_namespace, deadline=deadline, progress=M.truth_value)
    except SnapshotSaveTimeout:
        raise
    except Exception as error:
        print(
            "snapshot save FAILED during " + deadline.phase + ": " + str(error),
            flush=True,
        )
        raise
    finally:
        deadline.close()
    print("saved snapshot to", target_path, flush=True)


def _debug_log(debug_flag, *args, **kwargs):
    if M.IdentityCompare(debug_flag, M.truth_value)() is M.truth_value:
        print(*args, **kwargs)


def _maybe_resume_paused_cold_search(debug: bool = False, snapshot_path=None):
    target_path = SNAPSHOT_PATH if snapshot_path is None else snapshot_path
    debug_flag = M.truth_value if debug else M.false_value
    _debug_log(debug_flag, f"DEBUG: checking paused snapshot at {target_path}")
    if os.path.exists(target_path):
        snapshot_exists = M.truth_value
    else:
        snapshot_exists = M.false_value
    if snapshot_exists is M.false_value:
        _debug_log(debug_flag, "DEBUG: no paused snapshot found")
        return M.false_value

    _debug_log(debug_flag, "DEBUG: snapshot found, checking paused-job roots")
    runtime_namespace = _runtime_namespace()
    try:
        probe_codec = SnapshotCodec(runtime_namespace)
        probe_state = probe_codec.load(target_path)
        snapshot_empty = probe_state.symbols["EmptyList"]
        snapshot_search_jobs = snapshot_empty
        if "search_jobs" in probe_state.roots:
            snapshot_search_jobs = probe_state.roots["search_jobs"]
        snapshot_comparison_jobs = snapshot_empty
        if "search_comparison_jobs" in probe_state.roots:
            snapshot_comparison_jobs = probe_state.roots["search_comparison_jobs"]
        if M.AndAtom(
            M.IdentityCompare(snapshot_search_jobs, snapshot_empty)(),
            M.IdentityCompare(snapshot_comparison_jobs, snapshot_empty)(),
        )() is M.truth_value:
            _debug_log(debug_flag, "DEBUG: snapshot contains no paused-job roots")
            return M.false_value

        _debug_log(debug_flag, "DEBUG: paused-job root found, restoring snapshot")
        runtime = boot_from_snapshot(
            target_path,
            runtime_namespace,
            debug=debug_flag,
            save_upgraded_snapshot=M.false_value,
        )
    except (OSError, RuntimeError, json.JSONDecodeError, ValueError, KeyError, TypeError) as error:
        print(
            "ignoring unreadable snapshot at",
            target_path,
            "(" + error.__class__.__name__ + ": " + str(error) + ")",
        )
        try:
            bad_path = target_path + ".bad"
            if os.path.exists(bad_path):
                os.remove(bad_path)
            os.replace(target_path, bad_path)
            print("moved unreadable snapshot to", bad_path)
        except OSError:
            pass
        return M.false_value
    job = _first_paused_search_job(runtime.graph)
    comparison_job = _first_paused_search_comparison_job(runtime.graph)
    if M.Compare(comparison_job, M.EmptyList)() is M.false_value:
        if _paused_comparison_job_is_compatible(comparison_job, runtime.graph) is M.false_value:
            print("ignoring incompatible paused comparison snapshot at", target_path)
            incompatible_path = target_path + ".incompatible"
            os.replace(target_path, incompatible_path)
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
            _save_snapshot_now(runtime, runtime_namespace, target_path)
            return M.truth_value

        proved = M.Compare(derivation, M.EmptyList)() is not M.truth_value
        if proved:
            print(comparison_text + ": resumed, finished benchmarking, and proved the goal in " + str(elapsed) + " seconds")
        else:
            print(comparison_text + ": resumed and finished benchmarking after " + str(elapsed) + " seconds")

        _save_snapshot_now(runtime, runtime_namespace, target_path)
        return M.truth_value

    if M.Compare(job, M.EmptyList)() is M.truth_value:
        return M.false_value

    if _paused_job_is_compatible(job, runtime.graph) is M.false_value:
        print("ignoring incompatible paused snapshot at", target_path)
        incompatible_path = target_path + ".incompatible"
        os.replace(target_path, incompatible_path)
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
        _save_snapshot_now(runtime, runtime_namespace, target_path)
        return M.truth_value

    proved = M.Compare(derivation, M.EmptyList)() is not M.truth_value
    if proved:
        print(mode_text + ": resumed and finished in " + str(elapsed) + " seconds")
    else:
        print(mode_text + ": resumed and did not prove the goal after " + str(elapsed) + " seconds")

    _save_snapshot_now(runtime, runtime_namespace, target_path)
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
    if os.environ.get("HYGE_SEARCH_WORKER_DEBUG", "") == "1":
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
        # A comparison worker is a whole proof in its own process. It boots
        # from packs like any other, so it needs the taught rules too --
        # otherwise a search that fans out loses exactly the concepts the
        # trainer added.
        _teach_runtime_taught_rules(runtime)
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

def _teach_runtime_taught_rules(runtime, taught_version=M.EmptyList):
    """Give a pack-booted runtime the rules the trainer taught.

    The conversation compiles definitions into laws in its own version;
    a proof cold-boots from packs and never saw them, so a taught concept
    could not take part in a proof. Every proof boot passes through here:
    cold mode, the conversation's own proof runtime, and the daemon's,
    so no mode is the one where teaching quietly does not apply.

    A caller holding the live taught version hands it over; anyone else
    reads the shared checkpoint, which is where that version persists.
    Rules go in through the ordinary add_rule -- the same door the packs
    came in by.
    """
    if M.IdentityCompare(taught_version, M.EmptyList)() is M.truth_value:
        checkpoint_path = os.path.join(SNAPSHOT_DIR, Dmn.DAEMON_STATE_NAME)
        if os.path.exists(checkpoint_path) is False:
            return M.Zero
        restored = W.load_checkpoint(checkpoint_path)
        if M.IdentityCompare(restored, M.EmptyList)() is M.truth_value:
            return M.Zero
        taught_version = M.Head(restored)()
    taught_count = M.Zero
    remaining = G.TaughtDefinitionRules(
        taught_version,
        G.DefaultCorrespondenceVocabulary()(),
        M.FromContextGetConstructors(runtime.graph)(),
    )()
    while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
        runtime.graph.add_rule(M.Head(remaining)())
        stepped = M.Succ(taught_count, M.FromContextGetConstructors(runtime.graph)())()
        taught_count = M.Head(stepped)()
        remaining = M.Tail(remaining)()
    remaining = G.InstalledTaughtRules(taught_version)()
    while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
        runtime.graph.add_rule(M.Head(remaining)())
        stepped = M.Succ(taught_count, M.FromContextGetConstructors(runtime.graph)())()
        taught_count = M.Head(stepped)()
        remaining = M.Tail(remaining)()
    taught_text = M.GMPRepText(
        M.NatRepOf(taught_count, M.FromContextGetConstructors(runtime.graph)())(),
    )()
    if G.GMPEqualText(taught_text, "0")() is M.false_value:
        print(
            "taught rules added to this proof: " + taught_text,
            flush=True,
        )
    return taught_count


def run_cold_mode(
    debug: bool = False,
    filter_name: str = "tao",
    snapshot_path=None,
    snapshot_save_timeout_seconds=SNAPSHOT_SAVE_TIMEOUT_SECONDS,
):
    if debug:
        P.SetDebugTrace(M.truth_value)()
    else:
        P.SetDebugTrace(M.false_value)()
    runtime_namespace = _runtime_namespace()
    if M.IdentityCompare(_maybe_resume_paused_cold_search(debug=debug, snapshot_path=snapshot_path), M.truth_value)() is M.truth_value:
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

    _teach_runtime_taught_rules(runtime)

    try:
        theorem_results = _run_theorem_agenda(runtime, _theorem_agenda(packs, filter_name), "Cold theorem agenda", debug=debug)
    except PausedComparisonRequested as paused:
        print(paused.label + ": comparison paused after " + str(paused.elapsed) + " seconds")
        _save_snapshot_now(runtime, runtime_namespace, snapshot_path, snapshot_save_timeout_seconds)
        return
    except PausedSearchRequested as paused:
        print(paused.label + ": paused after " + str(paused.elapsed) + " seconds")
        _save_snapshot_now(runtime, runtime_namespace, snapshot_path, snapshot_save_timeout_seconds)
        return
    proved_count = sum(1 for _label, proved, _elapsed, _goal, _derivation in theorem_results if proved)
    print(f"proved {proved_count} / {len(theorem_results)} theorem cases during cold boot")

    _save_snapshot_now(runtime, runtime_namespace, snapshot_path, snapshot_save_timeout_seconds)


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


def run_talk_mode(sentence: str = None):
    """Natural-language interaction through Surface/Meaning correspondence laws.

    The host contributes only the I/O boundary: words become Char atoms in
    Surface chains, and typed lines are appended to a lesson transcript that
    is replayed through the same machine path on the next boot. Grammar,
    training-example meanings, induction, validation, and approval records
    all live in machine terms and the proposal store. Sentences whose
    meaning is a Task term dispatch the formal runtime modes.
    """
    vocabulary = G.DefaultCorrespondenceVocabulary()()
    # One DefinitionFragment for the whole session. Its root and trie
    # states are identity atoms; a learned word's arcs reference them.
    # Building a fresh fragment per line would orphan every learned arc
    # on a root no engine visits again -- structure equal, identity
    # lost, the same trap as every other identity-keyed store here.
    definition_fragment = G.DefinitionFragment()()
    reading_policy = G.DefaultReadingPolicy()()
    ARTICLE_WORDS = M.Pair(
        M.Char("a"), M.Pair(M.Char("an"), M.Pair(M.Char("the"), M.EmptyList)),
    )
    COPULA_WORDS = M.Pair(M.Char("is"), M.Pair(M.Char("are"), M.EmptyList))
    WHAT_IS_WORDS = M.Pair(
        M.Char("what"), M.Pair(M.Char("is"), ARTICLE_WORDS),
    )
    reading_digits = M.Head(M.Tail(M.Tail(vocabulary)())())()
    registry = M.AllConstructors
    examples = M.EmptyList
    proposal_store = G.ProposalStore(M.EmptyList)()
    learned_version = G.GraphVersion(M.EmptyList, M.EmptyList, M.EmptyList)()
    # Talk state is checkpoint-backed so that a cycling process and this
    # conversation share one version rather than two disjoint ones. The
    # daemon is the only writer of activations; talk submits and reads.
    talk_checkpoint_path = os.path.join(SNAPSHOT_DIR, "talk_state.wire")
    talk_mark_path = os.path.join(SNAPSHOT_DIR, "talk_state.mark")
    # A running daemon announces itself with a liveness file it writes at
    # start and removes at exit. The inbox cannot serve as that signal: the
    # daemon consumes it, so its absence is ambiguous.
    daemon_live_path = os.path.join(SNAPSHOT_DIR, Dmn.DAEMON_LIVE_NAME)
    talk_ledger = G.FiringLedger(M.AllConstructors)
    # Lesson lines already folded into the checkpoint above. The mark is
    # only trusted when the checkpoint it describes exists: without the
    # folded state, every line must be replayed. Any doubt replays more,
    # never fewer -- a lesson skipped in error is silently forgotten.
    replay_mark_text = "0"
    if os.path.exists(talk_checkpoint_path):
        restored = W.load_checkpoint(talk_checkpoint_path)
        if M.IdentityCompare(restored, M.EmptyList)() is M.false_value:
            learned_version = M.Head(restored)()
            proposal_store = M.Head(M.Tail(restored)())()
            talk_ledger = M.Head(M.Tail(M.Tail(restored)())())()
            if os.path.exists(talk_mark_path):
                try:
                    with open(talk_mark_path, "r", encoding="utf-8") as stream:
                        replay_mark_text = M.GMPRepText(
                            M.GMPRep(stream.read().strip()),
                        )()
                except (OSError, ValueError):
                    replay_mark_text = "0"
    pending_queue = M.EmptyList
    pending_rule = M.EmptyList
    pending_bridge = M.EmptyList
    decided_laws = M.EmptyList
    proof_runtime = M.EmptyList
    last_outcome = M.EmptyList
    last_derivation = M.EmptyList
    last_goal = M.EmptyList
    last_proof_registry = M.EmptyList
    lesson_path = os.path.join(SNAPSHOT_DIR, "talk_lessons.log")

    def _words(text):
        """A typed line as a chain of words, by the reading policy.

        This was a chain of host replaces -- lowercase the line, blank
        the sentence punctuation, pad the brackets and the comma, split
        on whitespace, spell out any all-digit word -- and then a host
        list for the callers to slice. Six decisions about what a word
        is, made where nothing could state them, retire them or learn
        them, and a comma was a word because of a .replace. They are
        chains in DefaultReadingPolicy now; WordsOfStream applies them
        and hands back a chain, which is what every caller below walks.
        """
        return G.WordsOfText(text, reading_policy, reading_digits)()

    def _speak_chain(chain):
        spoken = []
        remaining = chain
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            word = M.Head(remaining)()
            if G.IsLawTerm(word)() is M.truth_value:
                spoken.append("<law>")
            else:
                try:
                    value = word()
                    if value is None:
                        spoken.append("?")
                    else:
                        spoken.append(str(value))
                except Exception:
                    spoken.append("?")
            remaining = M.Tail(remaining)()
        return " ".join(spoken)

    def _speak_pattern(surface_term):
        spoken = []
        remaining = M.Head(M.Tail(surface_term)())()
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            word = M.Head(remaining)()
            if P.IsVarPattern(word)() is M.truth_value:
                spoken.append(str(M.Head(M.Tail(word)())()()))
            elif M.IsPair(word)() is M.truth_value:
                # Group reduction splices whole terms (Sqrt(7), a Nat from
                # "(64)") into surface chains; render them as meanings, not
                # as the None their .value slot holds.
                spoken.append(_speak_meaning(word))
            else:
                try:
                    spoken.append(str(word()))
                except Exception:
                    spoken.append("?")
            remaining = M.Tail(remaining)()
        return " ".join(spoken)

    def _speak_meaning(term):
        if M.IsPair(term)() is M.truth_value:
            head = M.Head(term)()
            if M.IdentityCompare(head, Lmod.MeaningLabel)() is M.truth_value:
                return _speak_meaning(M.Head(M.Tail(term)())())
            if M.IdentityCompare(head, Lmod.SurfaceLabel)() is M.truth_value:
                return _speak_pattern(term)
            if M.IdentityCompare(head, M.ExprMulLabel)() is M.truth_value:
                args = M.Tail(term)()
                return (
                    "Mul(" + _speak_meaning(M.Head(args)()) + ", "
                    + _speak_meaning(M.Head(M.Tail(args)())()) + ")"
                )
            if M.IdentityCompare(head, M.ExprAddLabel)() is M.truth_value:
                args = M.Tail(term)()
                return (
                    "Add(" + _speak_meaning(M.Head(args)()) + ", "
                    + _speak_meaning(M.Head(M.Tail(args)())()) + ")"
                )
            if M.IdentityCompare(head, Lmod.EqualLabel)() is M.truth_value:
                args = M.Tail(term)()
                return (
                    "Equal(" + _speak_meaning(M.Head(args)()) + ", "
                    + _speak_meaning(M.Head(M.Tail(args)())()) + ")"
                )
            if M.IdentityCompare(head, M.IsRealLabel)() is M.truth_value:
                return "IsReal(" + _speak_meaning(M.Head(M.Tail(term)())()) + ")"
            if M.IdentityCompare(head, M.SqrtLabel)() is M.truth_value:
                return "Sqrt(" + _speak_meaning(M.Head(M.Tail(term)())()) + ")"
            if P.IsVarPattern(term)() is M.truth_value:
                return str(M.Head(M.Tail(term)())()())
        rep = M.NatRepOf(term, registry)()
        if M.IdentityCompare(rep, M.EmptyList)() is M.false_value:
            return str(rep())
        try:
            return str(term())
        except Exception:
            return "?"

    def _log_lesson(line):
        try:
            os.makedirs(SNAPSHOT_DIR, exist_ok=True)
            with open(lesson_path, "a", encoding="utf-8") as stream:
                stream.write(line + "\n")
        except OSError:
            pass

    def _meaning_of(text):
        nonlocal registry
        words = _words(text)
        if M.IdentityCompare(words, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        interpreted = G.ConverseInterpretations(
            vocabulary, G.Surface(words)(), registry,
        )()
        interpretations = M.Head(interpreted)()
        registry = M.Head(M.Tail(interpreted)())()
        if M.IdentityCompare(interpretations, M.EmptyList)() is M.truth_value:
            # The question path reduces parenthesis groups before matching
            # templates; the meaning side of a training example deserves the
            # same grammar. Without this, 'mul ( three , sqrt ( seven ) )'
            # is rejected while the identical shape is understood as a
            # question -- the trainer is told to use a notation the reader
            # then refuses.
            reduced = G.SurfaceReduceGroups(
                vocabulary, G.Surface(words)(), registry,
            )()
            reduced_surface = M.Head(reduced)()
            registry = M.Head(M.Tail(reduced)())()
            if M.IdentityCompare(
                reduced_surface, M.EmptyList,
            )() is M.false_value:
                interpreted = G.ConverseInterpretations(
                    vocabulary, reduced_surface, registry,
                )()
                interpretations = M.Head(interpreted)()
                registry = M.Head(M.Tail(interpreted)())()
        if M.IdentityCompare(interpretations, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        if M.IdentityCompare(
            M.Tail(interpretations)(), M.EmptyList,
        )() is M.false_value:
            return M.EmptyList
        return M.Head(M.Head(interpretations)())()

    def _extend_vocabulary():
        nonlocal vocabulary
        learned = G.InstalledCorrespondenceLaws(learned_version)()
        vocabulary = G.VocabularyWithTemplates(
            G.DefaultCorrespondenceVocabulary()(),
            learned,
        )()

    debug_enabled = True

    def _debug(text):
        if debug_enabled:
            print("DEBUG: " + text)

    def _count_chain(chain):
        count = 0
        remaining = chain
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            count = count + 1
            remaining = M.Tail(remaining)()
        return count

    def _label_spoken(label):
        for name, value in vars(Lmod).items():
            if value is label and name.endswith("Label"):
                return name[:-5]
        return "something"

    def _speak_definition_node(node):
        parts = []
        walker = G.DefinitionNodeConditions(node)()
        while M.IdentityCompare(walker, M.EmptyList)() is M.false_value:
            condition = M.Head(walker)()
            label = M.Head(condition)()
            if M.IdentityCompare(
                label, Lmod.NonNegativeLabel,
            )() is M.truth_value:
                parts.append("non-negative")
            elif M.IdentityCompare(label, Lmod.HoleLabel)() is M.truth_value:
                parts.append(
                    "an undefined " + _label_spoken(M.Head(M.Tail(condition)())()),
                )
            elif M.IdentityCompare(
                label, Lmod.ExactFillersLabel,
            )() is M.truth_value:
                parts.append("only [one, itself] as divisor")
            else:
                parts.append(_label_spoken(label))
            walker = M.Tail(walker)()
        definiendum = G.DefinitionNodeDefiniendum(node)()
        concept = M.Head(M.Tail(definiendum)())()
        spoken_concept = "?"
        if M.IsPair(concept)() is M.truth_value:
            if M.IdentityCompare(
                M.Head(concept)(), Lmod.HoleLabel,
            )() is M.truth_value:
                word = M.Head(M.Tail(concept)())()
                spoken_concept = str(word()) + " (new from this line)"
        else:
            spoken_concept = str(concept())
        category_term = M.Head(M.Tail(M.Tail(definiendum)())())()
        category = M.Head(M.Tail(category_term)())()
        return (
            "a " + spoken_concept + " is a " + str(category())
            + ", " + " and ".join(parts)
        )

    def _definition_graph_answer(line):
        """Read the line as symbol events; return the answer or None.

        The client observes each character through the indexed engine;
        the fragment composes what it knows. When a word-shaped hole
        remains, the grammar says what category wants it, a provisional
        sense with a hole for a meaning enters through the delta
        agenda, and the chart completes without anything re-observing.
        The definition installs in the learned version together with
        the word's arcs and a permanent sense: the next line that uses
        the word parses with no gap at all. There is no word-chain
        fallback to record a definition the reader cannot read.
        """
        bundle = definition_fragment
        arcs = M.Head(bundle)()
        senses = M.Head(M.Tail(bundle)())()
        productions = M.Head(M.Tail(M.Tail(bundle)())())()
        root = M.Head(M.Tail(M.Tail(M.Tail(bundle)())())())()
        def_category = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(bundle)())())())())()
        alphabet_walker = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(bundle)())())())())())())())())())()
        spc_category = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(bundle)())())())())())())())())())())()

        learned_arcs_reversed = M.EmptyList
        learned_senses_reversed = M.EmptyList

        def _collect_learned(node):
            nonlocal learned_arcs_reversed, learned_senses_reversed
            if M.IsPair(node)() is M.false_value:
                return
            node_head = M.Head(node)()
            if M.IdentityCompare(
                node_head, Lmod.FormArcLabel,
            )() is M.truth_value:
                learned_arcs_reversed = M.Pair(node, learned_arcs_reversed)
            elif M.IdentityCompare(
                node_head, Lmod.FormSenseLabel,
            )() is M.truth_value:
                learned_senses_reversed = M.Pair(
                    node, learned_senses_reversed,
                )
            elif M.IsPair(node_head)() is M.truth_value:
                # Installed chains hold arcs, sense and DefinitionNode
                # as one element; their members are nodes too.
                inner = node
                while M.IdentityCompare(
                    inner, M.EmptyList,
                )() is M.false_value:
                    _collect_learned(M.Head(inner)())
                    inner = M.Tail(inner)()

        node_walker = G.GraphNodes(learned_version)()
        while M.IdentityCompare(node_walker, M.EmptyList)() is M.false_value:
            _collect_learned(M.Head(node_walker)())
            node_walker = M.Tail(node_walker)()
        all_arcs = arcs
        arc_walker = M.Reverse(learned_arcs_reversed)()
        while M.IdentityCompare(arc_walker, M.EmptyList)() is M.false_value:
            all_arcs = M.Pair(M.Head(arc_walker)(), all_arcs)
            arc_walker = M.Tail(arc_walker)()
        all_senses = senses
        sense_walker = M.Reverse(learned_senses_reversed)()
        while M.IdentityCompare(sense_walker, M.EmptyList)() is M.false_value:
            all_senses = M.Pair(M.Head(sense_walker)(), all_senses)
            sense_walker = M.Tail(sense_walker)()

        symbols = {}
        alphabet_stepper = alphabet_walker
        while M.IdentityCompare(alphabet_stepper, M.EmptyList)() is M.false_value:
            symbol_atom = M.Head(alphabet_stepper)()
            symbols[str(symbol_atom())] = symbol_atom
            alphabet_stepper = M.Tail(alphabet_stepper)()
        covered = M.truth_value
        index = 0
        cursors = {}
        engine = None
        while index < len(line):
            ch = line[index]
            if ch not in symbols:
                covered = M.false_value
                index = len(line)
            else:
                if engine is None:
                    engine = G.RecogniseForms(
                        M.EmptyList, all_arcs, all_senses, root, productions,
                    )
                if index not in cursors:
                    cursors[index] = M.GMPRep(str(index))
                if index + 1 not in cursors:
                    cursors[index + 1] = M.GMPRep(str(index + 1))
                engine.Observe(
                    M.Char(line), cursors[index], symbols[ch],
                    cursors[index + 1],
                )
                index = index + 1
        if covered is M.false_value:
            return None, learned_version
        result = engine.Drain()
        readings = M.Head(result)()
        top = G.SpanningDefinitionReading(
            readings, def_category, cursors[0], cursors[len(line)],
        )()

        provisional = M.EmptyList
        gap_category = M.EmptyList
        word_atom = M.EmptyList
        gap_rounds_text = "0"
        while M.IdentityCompare(top, M.EmptyList)() is M.truth_value:
            if G.GMPEqualText(gap_rounds_text, "8")() is M.truth_value:
                return None, learned_version
            gap_rounds_text = G.GMPSuccText(gap_rounds_text)()
            gap = G.LexicalGap(
                M.Head(engine.result)(), productions, spc_category,
                cursors[len(line)],
            )()
            if M.IdentityCompare(gap, M.EmptyList)() is M.truth_value:
                return None, learned_version
            gap_start = M.Head(gap)()
            gap_end = M.Head(M.Tail(gap)())()
            gap_category = M.Head(M.Tail(M.Tail(gap)())())()
            start_index = int(M.GMPRepText(gap_start)())
            end_index = int(M.GMPRepText(gap_end)())
            gap_symbols_reversed = M.EmptyList
            walker = end_index - 1
            while walker >= start_index:
                gap_symbols_reversed = M.Pair(
                    symbols[line[walker]], gap_symbols_reversed,
                )
                walker = walker - 1
            word_atom = M.Char(line[start_index:end_index])
            provisional = G.ProvisionalWord(
                root, gap_symbols_reversed, gap_category, word_atom,
            )()
            engine.Learn(
                M.Head(provisional)(),
                M.Pair(M.Head(M.Tail(provisional)())(), M.EmptyList),
            )
            top = G.SpanningDefinitionReading(
                M.Head(engine.result)(), def_category,
                cursors[0], cursors[len(line)],
            )()
        conditions = G.DefinitionNodeConditions(top)()
        # A predicate is defined when something says what it means.
        # NonNegative is structural; everything else earns its place
        # from the pack-concept index -- the constructors that HEAD
        # rules in the loaded packs. Divides stops being a hole the
        # moment number-theory.pack's laws speak for it: the parsed
        # definition and the proving substrate meet at one atom.
        defined = M.Pair(Lmod.NonNegativeLabel, M.EmptyList)
        concept_walker = pack_concepts
        while M.IdentityCompare(concept_walker, M.EmptyList)() is M.false_value:
            defined = M.Pair(
                M.Head(M.Tail(M.Head(concept_walker)())())(),
                defined,
            )
            concept_walker = M.Tail(concept_walker)()
        holed = G.PredicateHoles(conditions, defined)()
        holed_conditions = M.Head(holed)()
        dependencies = M.Head(M.Tail(holed)())()
        holed_node = G.DefinitionNode(
            G.DefinitionNodeDefiniendum(top)(),
            G.DefinitionNodeBinder(top)(),
            holed_conditions,
        )()

        installed_reversed = M.Pair(holed_node, M.EmptyList)
        if M.IdentityCompare(provisional, M.EmptyList)() is M.false_value:
            final_state = M.Head(M.Tail(M.Tail(provisional)())())()
            permanent_sense = G.FormSense(
                final_state, gap_category, word_atom,
            )()
            arc_walker = M.Head(provisional)()
            while M.IdentityCompare(arc_walker, M.EmptyList)() is M.false_value:
                installed_reversed = M.Pair(
                    M.Head(arc_walker)(), installed_reversed,
                )
                arc_walker = M.Tail(arc_walker)()
            installed_reversed = M.Pair(permanent_sense, installed_reversed)
        next_version = G.GraphVersion(
            M.Pair(
                M.Reverse(installed_reversed)(),
                G.GraphNodes(learned_version)(),
            ),
            G.GraphEdges(learned_version)(),
            G.GraphVersionInvariants(learned_version)(),
        )()
        spoken = []
        dependency_walker = dependencies
        while M.IdentityCompare(
            dependency_walker, M.EmptyList,
        )() is M.false_value:
            spoken.append(_label_spoken(M.Head(dependency_walker)()))
            dependency_walker = M.Tail(dependency_walker)()
        if spoken:
            answer = (
                "I've formed this graph: "
                + _speak_definition_node(holed_node)
                + ". But I need definitions of: " + ", ".join(spoken) + "."
            )
        else:
            answer = (
                "I've formed this graph: " + _speak_definition_node(holed_node)
                + ". Every predicate in it is grounded."
            )
        return answer, next_version

    def _question_graph_answer(line):
        """Read a question line as symbol events; return the answer or None.

        The same engine, the same learned lexicon, the same gap loop:
        a question is a line the question shape must span. When it
        does, the question parsed -- answering it needs grounded
        definitions, which the dependencies name.
        """
        nonlocal learned_version
        # The one crossing where the typed line becomes symbol events.
        # A capital I and a trailing ? are typography, not symbols the
        # grammar carries; normalized here once, where the host string
        # is converted, and nowhere past this point.
        line = line.strip().lower()
        while line.endswith("?"):
            line = line[:-1]
        line = line.strip()
        # An expression subject -- "is (two plus five) prime" -- is
        # arithmetic inside grammar. The group is cut at the boundary,
        # evaluated through ConverseValue (all interpretations must
        # agree; no silent pick), and the line re-enters with the
        # value's own word. The grammar never sees brackets; the
        # arithmetic never sees the question shape. Each reader reads
        # what it owns.
        open_at = line.find("(")
        if open_at != -1:
            close_at = line.rfind(")")
            if close_at == -1 or close_at < open_at:
                return "The brackets in that question do not balance."
            group_words = _words(line[open_at + 1:close_at])
            if M.IdentityCompare(group_words, M.EmptyList)() is M.truth_value:
                return "The brackets in that question are empty."
            group_value = G.ConverseValue(
                vocabulary,
                G.Surface(group_words)(),
                registry,
            )()
            value_nat = M.Head(group_value)()
            if M.IdentityCompare(value_nat, M.EmptyList)() is M.truth_value:
                return (
                    "I could not evaluate the bracketed expression to "
                    "one agreed value."
                )
            value_word = M.EmptyList
            word_entry_probe = M.Head(M.Tail(vocabulary)())()
            while M.IdentityCompare(
                word_entry_probe, M.EmptyList,
            )() is M.false_value:
                entry = M.Head(word_entry_probe)()
                if M.NatEq(
                    M.Head(M.Tail(entry)())(), value_nat, registry,
                )() is M.truth_value:
                    value_word = M.Head(entry)()
                    word_entry_probe = M.EmptyList
                else:
                    word_entry_probe = M.Tail(word_entry_probe)()
            if M.IdentityCompare(value_word, M.EmptyList)() is M.truth_value:
                return (
                    "The bracketed expression evaluates beyond the "
                    "number words I can speak."
                )
            line = (
                line[:open_at].strip() + " " + str(value_word())
                + " " + line[close_at + 1:].strip()
            ).strip()
        bundle = definition_fragment
        arcs = M.Head(bundle)()
        senses = M.Head(M.Tail(bundle)())()
        productions = M.Head(M.Tail(M.Tail(bundle)())())()
        root = M.Head(M.Tail(M.Tail(M.Tail(bundle)())())())()
        alphabet = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(bundle)())())())())())())())())())()
        spc_category = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(bundle)())())())())())())())())())())()
        question_category = M.EmptyList
        walker = productions
        while M.IdentityCompare(walker, M.EmptyList)() is M.false_value:
            production = M.Head(walker)()
            result_atom = M.Head(M.Tail(M.Tail(M.Tail(production)())())())()
            if M.IsPair(result_atom)() is M.false_value:
                if result_atom() == "QUESTION":
                    question_category = result_atom
                    walker = M.EmptyList
                else:
                    walker = M.Tail(walker)()
            else:
                walker = M.Tail(walker)()
        if M.IdentityCompare(question_category, M.EmptyList)() is M.truth_value:
            _debug("question: no question category in the grammar")
            return None

        learned_arcs_reversed = M.EmptyList
        learned_senses_reversed = M.EmptyList

        def _collect_learned(node):
            nonlocal learned_arcs_reversed, learned_senses_reversed
            if M.IsPair(node)() is M.false_value:
                return
            node_head = M.Head(node)()
            if M.IdentityCompare(
                node_head, Lmod.FormArcLabel,
            )() is M.truth_value:
                learned_arcs_reversed = M.Pair(node, learned_arcs_reversed)
            elif M.IdentityCompare(
                node_head, Lmod.FormSenseLabel,
            )() is M.truth_value:
                learned_senses_reversed = M.Pair(
                    node, learned_senses_reversed,
                )
            elif M.IsPair(node_head)() is M.truth_value:
                # The definition path installs a whole chain of nodes
                # as one element (arcs, sense, DefinitionNode together);
                # a chained element's members are nodes too.
                inner = node
                while M.IdentityCompare(
                    inner, M.EmptyList,
                )() is M.false_value:
                    _collect_learned(M.Head(inner)())
                    inner = M.Tail(inner)()

        node_walker = G.GraphNodes(learned_version)()
        while M.IdentityCompare(node_walker, M.EmptyList)() is M.false_value:
            _collect_learned(M.Head(node_walker)())
            node_walker = M.Tail(node_walker)()
        all_arcs = arcs
        arc_walker = M.Reverse(learned_arcs_reversed)()
        while M.IdentityCompare(arc_walker, M.EmptyList)() is M.false_value:
            all_arcs = M.Pair(M.Head(arc_walker)(), all_arcs)
            arc_walker = M.Tail(arc_walker)()
        all_senses = senses
        sense_walker = M.Reverse(learned_senses_reversed)()
        while M.IdentityCompare(sense_walker, M.EmptyList)() is M.false_value:
            all_senses = M.Pair(M.Head(sense_walker)(), all_senses)
            sense_walker = M.Tail(sense_walker)()

        symbols = {}
        alphabet_stepper = alphabet
        while M.IdentityCompare(alphabet_stepper, M.EmptyList)() is M.false_value:
            symbol_atom = M.Head(alphabet_stepper)()
            symbols[str(symbol_atom())] = symbol_atom
            alphabet_stepper = M.Tail(alphabet_stepper)()
        covered = M.truth_value
        index = 0
        cursors = {}
        engine = None
        while index < len(line):
            ch = line[index]
            if ch not in symbols:
                covered = M.false_value
                index = len(line)
            else:
                if engine is None:
                    engine = G.RecogniseForms(
                        M.EmptyList, all_arcs, all_senses, root, productions,
                    )
                if index not in cursors:
                    cursors[index] = M.GMPRep(str(index))
                if index + 1 not in cursors:
                    cursors[index + 1] = M.GMPRep(str(index + 1))
                engine.Observe(
                    M.Char(line), cursors[index], symbols[ch],
                    cursors[index + 1],
                )
                index = index + 1
        if covered is M.false_value:
            _debug("question: alphabet does not cover the line")
            return None
        engine.Drain()
        top = G.SpanningDefinitionReading(
            M.Head(engine.result)(), question_category,
            cursors[0], cursors[len(line)],
        )()
        rounds_text = "0"
        while M.IdentityCompare(top, M.EmptyList)() is M.truth_value:
            if G.GMPEqualText(rounds_text, "8")() is M.truth_value:
                _debug("question: gap rounds exhausted")
                return None
            rounds_text = G.GMPSuccText(rounds_text)()
            gap = G.LexicalGap(
                M.Head(engine.result)(), productions, spc_category,
                cursors[len(line)],
            )()
            if M.IdentityCompare(gap, M.EmptyList)() is M.truth_value:
                _debug("question: no lexical gap proposable")
                return None
            gap_start = M.Head(gap)()
            gap_end = M.Head(M.Tail(gap)())()
            gap_category = M.Head(M.Tail(M.Tail(gap)())())()
            start_index = int(M.GMPRepText(gap_start)())
            end_index = int(M.GMPRepText(gap_end)())
            gap_symbols_reversed = M.EmptyList
            walker = end_index - 1
            while walker >= start_index:
                gap_symbols_reversed = M.Pair(
                    symbols[line[walker]], gap_symbols_reversed,
                )
                walker = walker - 1
            provisional = G.ProvisionalWord(
                root, gap_symbols_reversed, gap_category,
                M.Char(line[start_index:end_index]),
            )()
            engine.Learn(
                M.Head(provisional)(),
                M.Pair(M.Head(M.Tail(provisional)())(), M.EmptyList),
            )
            top = G.SpanningDefinitionReading(
                M.Head(engine.result)(), question_category,
                cursors[0], cursors[len(line)],
            )()
        def _render_term(term, depth=0):
            if depth > 6:
                return "..."
            if M.IsPair(term)() is M.truth_value:
                return ("(" + _render_term(M.Head(term)(), depth + 1) + " "
                        + _render_term(M.Tail(term)(), depth + 1) + ")")
            if term is M.EmptyList:
                return "-"
            spoken = _label_spoken(term)
            if spoken != "something":
                return spoken
            try:
                value = term()
                if value is not None:
                    return str(value)
            except Exception:
                pass
            return "?"
        _debug("question meaning: " + _render_term(top))
        # The reading's subject rides in a Hole when the word was
        # learned mid-parse: Hole(word, ...). A number word resolves to
        # its Nat through the correspondence vocabulary -- the same
        # atom the packs count with.
        subject_word = M.EmptyList
        if M.IsPair(top)() is M.truth_value:
            if M.IdentityCompare(
                M.Head(top)(), Lmod.HoleLabel,
            )() is M.truth_value:
                subject_word = G.HolePredicate(top)()
        if M.IdentityCompare(subject_word, M.EmptyList)() is M.truth_value:
            return (
                "The question parses, but I cannot find its subject."
            )
        word_entries = M.Head(M.Tail(vocabulary)())()
        subject_nat = G.CorrespondenceResolveWord(
            word_entries,
            G.Surface(M.Pair(subject_word, M.EmptyList))(),
        )()
        if M.IdentityCompare(subject_nat, M.EmptyList)() is M.truth_value:
            return (
                "The question parses, but '" + str(subject_word())
                + "' does not name a number I know."
            )
        # Find the installed DefinitionNode. The learned version's node
        # store holds installed chains as single elements; walk one
        # level into any element that is itself a chain of terms.
        definition_node = M.EmptyList
        node_probe = G.GraphNodes(learned_version)()
        while M.IdentityCompare(node_probe, M.EmptyList)() is M.false_value:
            candidate = M.Head(node_probe)()
            if M.IsPair(candidate)() is M.truth_value:
                if M.IdentityCompare(
                    M.Head(candidate)(), Lmod.DefinitionNodeLabel,
                )() is M.truth_value:
                    definition_node = candidate
                elif M.IsPair(M.Head(candidate)())() is M.truth_value:
                    inner_probe = candidate
                    while M.IdentityCompare(
                        inner_probe, M.EmptyList,
                    )() is M.false_value:
                        inner = M.Head(inner_probe)()
                        if M.IsPair(inner)() is M.truth_value:
                            if M.IdentityCompare(
                                M.Head(inner)(), Lmod.DefinitionNodeLabel,
                            )() is M.truth_value:
                                definition_node = inner
                        inner_probe = M.Tail(inner_probe)()
            node_probe = M.Tail(node_probe)()
        if M.IdentityCompare(definition_node, M.EmptyList)() is M.truth_value:
            return (
                "The question parses. I cannot answer it yet: no "
                "installed definition speaks for it."
            )
        # The primality shape: an ExactFillers condition restricting
        # Divides. Resolve its allowed chain -- number words through
        # the vocabulary, the reflexive to the subject -- and ask
        # ExactDivisorRestriction, the bounded walk whose refutation
        # carries the offending divisor as a witness.
        conditions = G.DefinitionNodeConditions(definition_node)()
        exact = M.EmptyList
        condition_probe = conditions
        while M.IdentityCompare(
            condition_probe, M.EmptyList,
        )() is M.false_value:
            condition = M.Head(condition_probe)()
            if M.IsPair(condition)() is M.truth_value:
                if M.IdentityCompare(
                    M.Head(condition)(), Lmod.ExactFillersLabel,
                )() is M.truth_value:
                    exact = condition
            condition_probe = M.Tail(condition_probe)()
        if M.IdentityCompare(exact, M.EmptyList)() is M.truth_value:
            return (
                "The question parses and the definition is installed, "
                "but its conditions carry no restriction I can check."
            )
        allowed = M.Head(
            M.Tail(M.Tail(M.Tail(M.Tail(exact)())())())(),
        )()
        # In the installed node every reflexive was resolved to the
        # binder's variable (ResolveReflexives): "itself" IS the bound
        # self. Under this question the self is the subject, so the
        # binder variable resolves to the subject's Nat; number words
        # resolve through the vocabulary.
        binder_variable = G.BinderSelf(
            G.DefinitionNodeBinder(definition_node)(),
        )()
        allowed_nats = M.EmptyList
        allowed_probe = allowed
        while M.IdentityCompare(
            allowed_probe, M.EmptyList,
        )() is M.false_value:
            item = M.Head(allowed_probe)()
            resolved = M.EmptyList
            if item is binder_variable:
                resolved = subject_nat
            elif M.IsPair(item)() is M.truth_value:
                if M.IdentityCompare(
                    M.Head(item)(), Lmod.ReflexiveLabel,
                )() is M.truth_value:
                    resolved = subject_nat
            else:
                resolved = G.CorrespondenceResolveWord(
                    word_entries,
                    G.Surface(M.Pair(item, M.EmptyList))(),
                )()
            if M.IdentityCompare(resolved, M.EmptyList)() is M.false_value:
                allowed_nats = M.Pair(resolved, allowed_nats)
            allowed_probe = M.Tail(allowed_probe)()
        searched = G.ExactDivisorRestriction(
            top, subject_nat, allowed_nats, registry,
        )()
        verdict = M.Head(searched)()
        evidence = M.Head(M.Tail(searched)())()
        if M.IdentityCompare(verdict, M.truth_value)() is M.truth_value:
            return (
                "Yes: every divisor of " + str(subject_word())
                + " is among the allowed ones."
            )
        if M.IdentityCompare(verdict, M.false_value)() is M.truth_value:
            witness = M.Head(M.Tail(M.Tail(evidence)())())()
            witness_nat = M.Head(M.Tail(witness)())()
            witness_rep = M.NatRepOf(witness_nat, registry)()
            return (
                "No: " + M.GMPRepText(witness_rep)() + " divides "
                + str(subject_word())
                + " and is not among the allowed divisors."
            )
        return (
            "The search hit its cap before deciding; I do not know."
        )

    def _handle_definition(line, record=True):
        nonlocal learned_version, registry
        # The reader computes; this caller commits. One writer of the
        # session state, one place the lesson is logged and persisted --
        # the reader returns (answer, next_version) and mutates nothing.
        graph_answer, next_version = _definition_graph_answer(line)
        if graph_answer is not None:
            learned_version = next_version
            if record:
                _log_lesson(line)
            _persist_talk_state()
            return graph_answer
        return ("I could not read that definition. The line has a word or a "
                + "shape my grammar does not cover; nothing was recorded.")
        body = line.split(":", 1)[1].strip()
        words = _words(body)
        if M.IdentityCompare(words, M.EmptyList)() is M.truth_value:
            return "A definition is 'definition: a TERM is ...'."
        # The defined term is the first non-article word; everything after
        # the copula is the body. 'a triangle is a figure with three sides'
        # -> term 'triangle', body 'a figure with three sides'.
        split = G.DefinitionTermAndBody(words, ARTICLE_WORDS, COPULA_WORDS)()
        if M.IdentityCompare(split, M.EmptyList)() is M.truth_value:
            return "I could not find the term being defined."
        term_word = M.Head(split)()
        term_text = term_word()
        body_chain = M.Head(M.Tail(split)())()
        definition = G.Definition(
            term_word,
            G.Surface(body_chain)(),
        )()
        installed = G.InstallDefinition(learned_version, definition)()
        new_version = M.Head(installed)()
        existing = M.Head(M.Tail(installed)())() if M.IdentityCompare(
            M.Tail(installed)(), M.EmptyList,
        )() is M.false_value else M.EmptyList
        if M.IdentityCompare(existing, M.EmptyList)() is M.false_value:
            return (
                "I already have a definition of '" + term_text + "': "
                + _speak_chain(
                    M.Head(M.Tail(G.DefinitionBody(existing)())())(),
                )
            )
        learned_version = new_version
        # A word may already be bridged when its definition arrives -- the
        # trainer defined it after linking, or is refining an earlier
        # definition. Either way the subject already names a constructor,
        # so the definition is groundable now and should reach the rule
        # graph without waiting for a bridge question that will not come.
        definition_law_line = ""
        law_result = G.InstallDefinitionLaws(
            learned_version,
            definition,
            vocabulary,
            registry,
        )()
        learned_version = M.Head(law_result)()
        definition_law_count = M.Head(M.Tail(law_result)())()
        definition_law_text = M.GMPRepText(
            M.NatRepOf(definition_law_count, registry)(),
        )()
        if G.GMPEqualText(definition_law_text, "0")() is M.false_value:
            definition_law_line = (
                " It compiled to " + definition_law_text
                + " law(s); the prover now rewrites with them."
            )
        if record:
            _log_lesson(line)
        _persist_talk_state()
        open_words = G.DefinitionOpenDependencies(
            learned_version, definition, vocabulary, registry,
        )()
        if M.IdentityCompare(open_words, M.EmptyList)() is M.truth_value:
            return (
                "Recorded: a " + term_text + " is "
                + _speak_chain(body_chain) + ". Every word in it is grounded."
                + definition_law_line
                + _propose_bridge(term_text)
            )
        spoken = []
        remaining_open = open_words
        while M.IdentityCompare(remaining_open, M.EmptyList)() is M.false_value:
            spoken.append(str(M.Head(remaining_open)()()))
            remaining_open = M.Tail(remaining_open)()
        return (
            "Recorded: a " + term_text + " is " + _speak_chain(body_chain) + ". "
            + "But I do not know what "
            + " or ".join("'" + w + "'" for w in spoken)
            + " " + ("is" if len(spoken) == 1 else "are")
            + ". Define "
            + ("it" if len(spoken) == 1 else "them")
            + " with 'definition: a " + spoken[0] + " is ...'."
            + definition_law_line
            + _propose_bridge(term_text)
        )

    def _spoken_from_label_name(name):
        out = []
        for ch in name[:-5]:
            if ch.isupper() and out:
                out.append(" ")
            out.append(ch.lower())
        return "".join(out)

    def _word_chain_text(word_chain):
        out = []
        remaining_chars = word_chain
        while M.IdentityCompare(remaining_chars, M.EmptyList)() is M.false_value:
            out.append(str(M.Head(remaining_chars)()()))
            remaining_chars = M.Tail(remaining_chars)()
        return "".join(out)

    def _pack_concept_index(loaded_packs, rules_tree):
        """Bridge-noticing index from loader-emitted symbol maps.

        Every LoadedPack carries symbol_map: the Pair(word_chain,
        Pair(atom, Empty)) chain of associations its compilation
        crossed the host boundary for, emitted by the loader at the
        single legitimate crossing point. This index walks those
        chains and keeps the atoms that HEAD an installed rule's
        pattern (RulePatternHeads on the loaded rule tree): only
        rule-bearing constructors are concepts worth offering. No
        namespace consultation, no source re-parsing: the loader
        vouched for every entry.

        Returns Pair(concept_chain, Pair(name_chain, EmptyList)) --
        concepts for the bridge proposal, names for speaking labels.
        """
        rule_heads = G.RulePatternHeads(rules_tree, registry)()
        index_chain = M.EmptyList
        name_chain = M.EmptyList
        seen = M.EmptyList
        named = M.EmptyList
        for pack in loaded_packs:
            remaining = pack.symbol_map
            while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
                entry = M.Head(remaining)()
                word_chain = M.Head(entry)()
                atom = M.Head(M.Tail(entry)())()
                name_text = _word_chain_text(word_chain)
                if name_text.endswith("Label"):
                    spoken_word = M.Char(_spoken_from_label_name(name_text))
                    if G.ChainHasWordStructural(
                        named, spoken_word,
                    )() is M.false_value:
                        named = M.Pair(spoken_word, named)
                        name_chain = M.Pair(
                            M.Pair(spoken_word, M.Pair(atom, M.EmptyList)),
                            name_chain,
                        )
                    if G.ChainHasTerm(rule_heads, atom)() is M.truth_value:
                        concept_word = M.Char(name_text[:-5].lower())
                        if G.ChainHasWordStructural(
                            seen, concept_word,
                        )() is M.false_value:
                            seen = M.Pair(concept_word, seen)
                            index_chain = M.Pair(
                                M.Pair(
                                    concept_word,
                                    M.Pair(atom, M.EmptyList),
                                ),
                                index_chain,
                            )
                remaining = M.Tail(remaining)()
        return M.Pair(index_chain, M.Pair(name_chain, M.EmptyList))

    def _bootstrap_concept_index():
        """Bootstrap fallback: the same index from pack SOURCES.

        Talk mode boots without loaded packs, so there are no
        loader-emitted symbol maps to read yet. Until the first proof
        boot supersedes it through _adopt_pack_concepts, this fallback
        parses the pack sources at the YAML boundary and resolves
        names through the runtime namespace -- the Step-36 shape:
        the host implementation demoted to bootstrap, the
        loader-vouched chains the installed reader.
        """
        import yaml

        namespace = _runtime_namespace()
        index_chain = M.EmptyList
        name_chain = M.EmptyList
        seen = M.EmptyList
        named = M.EmptyList

        def _heads(spec):
            if not spec:
                return
            call = spec.get("call") or {}
            head = call.get("head") or {}
            name = head.get("sym")
            if name:
                yield name
            for arg in call.get("args") or ():
                if "call" in (arg or {}):
                    for inner in _heads(arg):
                        yield inner

        for pack_path in PACK_PATHS:
            try:
                with open(pack_path, "r", encoding="utf-8") as stream:
                    data = yaml.safe_load(stream.read())
            except OSError:
                continue
            if not data:
                continue
            for rule in data.get("rules") or ():
                pattern = rule.get("pattern") or {}
                pattern_head = ((pattern.get("call") or {}).get("head") or {}).get("sym")
                premise_heads = []
                for premise in rule.get("premises") or ():
                    premise_head = (
                        (premise.get("call") or {}).get("head") or {}
                    ).get("sym")
                    if premise_head:
                        premise_heads.append(premise_head)
                # A multi-premise rule fires on its premise heads the
                # way a pattern rule fires on its pattern head: both
                # make the constructor a concept rules speak for.
                if pattern_head is None and premise_heads:
                    pattern_head = premise_heads[0]
                spec_heads = list(_heads(pattern)) + list(
                    _heads(rule.get("replacement") or {}),
                )
                for premise in rule.get("premises") or ():
                    spec_heads.extend(_heads(premise))
                for name in spec_heads:
                    if not name.endswith("Label") or name not in namespace:
                        continue
                    spoken_word = M.Char(_spoken_from_label_name(name))
                    if G.ChainHasWordStructural(
                        named, spoken_word,
                    )() is M.false_value:
                        named = M.Pair(spoken_word, named)
                        name_chain = M.Pair(
                            M.Pair(
                                spoken_word,
                                M.Pair(namespace[name], M.EmptyList),
                            ),
                            name_chain,
                        )
                if not pattern_head or not pattern_head.endswith("Label"):
                    continue
                if pattern_head not in namespace:
                    continue
                word = M.Char(pattern_head[:-5].lower())
                if G.ChainHasWordStructural(seen, word)() is M.truth_value:
                    continue
                seen = M.Pair(word, seen)
                index_chain = M.Pair(
                    M.Pair(word, M.Pair(namespace[pattern_head], M.EmptyList)),
                    index_chain,
                )
        return M.Pair(index_chain, M.Pair(name_chain, M.EmptyList))

    _bootstrap_bundle = _bootstrap_concept_index()
    pack_concepts = M.Head(_bootstrap_bundle)()
    pack_label_names = M.Head(M.Tail(_bootstrap_bundle)())()

    def _adopt_pack_concepts(loaded_packs, rules_tree):
        nonlocal pack_concepts, pack_label_names
        bundle = _pack_concept_index(loaded_packs, rules_tree)
        pack_concepts = M.Head(bundle)()
        pack_label_names = M.Head(M.Tail(bundle)())()


    def _pack_constructor_for(term_text):
        """The rule-bearing pack constructor this word names, or EmptyList.

        Walks the pack-concept index -- constructors that head rule
        patterns in the pack sources -- and matches the word
        structurally. The noticing reads pack structure; the linking
        stays gated on the trainer.
        """
        word = M.Char(term_text)
        remaining = pack_concepts
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            entry = M.Head(remaining)()
            if M.Compare(M.Head(entry)(), word)() is M.truth_value:
                return M.Head(M.Tail(entry)())()
            remaining = M.Tail(remaining)()
        return M.EmptyList

    def _propose_bridge(term_text):
        nonlocal pending_bridge
        constructor = _pack_constructor_for(term_text)
        if M.IdentityCompare(constructor, M.EmptyList)() is M.truth_value:
            return ""
        existing = G.BridgeFor(learned_version, M.Char(term_text))()
        if M.IdentityCompare(existing, M.EmptyList)() is M.false_value:
            return ""
        pending_bridge = M.Pair(
            M.Char(term_text),
            M.Pair(constructor, M.EmptyList),
        )
        return (
            " The packs also know '" + term_text + "' as a constructor "
            "with its own ontology; shall I link the word to it? "
            "(bridge yes/bridge no)"
        )

    def _handle_bridge_decision(line, record=True):
        nonlocal pending_bridge, learned_version
        if M.IdentityCompare(pending_bridge, M.EmptyList)() is M.truth_value:
            return "There is no bridge awaiting a decision."
        if record:
            _log_lesson(line)
        word = M.Head(pending_bridge)()
        constructor = M.Head(M.Tail(pending_bridge)())()
        pending_bridge = M.EmptyList
        if line.strip().lower() == "bridge no":
            return "Recorded; the word stays unlinked."
        installed = G.InstallBridge(learned_version, word, constructor)()
        learned_version = M.Head(installed)()
        # The bridge is what makes the definition groundable: its subject
        # now names a constructor, so the body's own bridged words can be
        # asserted of it. Compile the definition into laws and install
        # them, so a taught concept enters the rule graph the search reads
        # rather than sitting beside it as a recitable sentence.
        law_line = ""
        definition = G.DefinitionFor(learned_version, word)()
        if M.IdentityCompare(definition, M.EmptyList)() is M.false_value:
            law_result = G.InstallDefinitionLaws(
                learned_version,
                definition,
                vocabulary,
                registry,
            )()
            learned_version = M.Head(law_result)()
            law_count = M.Head(M.Tail(law_result)())()
            law_text = M.GMPRepText(M.NatRepOf(law_count, registry)())()
            if G.GMPEqualText(law_text, "0")() is M.false_value:
                law_line = (
                    " The definition compiled to " + law_text
                    + " law(s); the prover now rewrites with them."
                )
        _persist_talk_state()
        return (
            "Linked: '" + str(word()) + "' now names the pack constructor. "
            "'what is " + str(word()) + "' can answer from the ontology."
            + law_line
        )

    def _speak_label(label):
        """The spoken word for a pack label, from the pack-concept index."""
        remaining = pack_label_names
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            entry = M.Head(remaining)()
            if M.Head(M.Tail(entry)())() is label:
                return str(M.Head(entry)()())
            remaining = M.Tail(remaining)()
        return "?"

    def _handle_what_is(line):
        # accepted shapes: 'what is a triangle', 'what is triangle'
        term_word = G.SoleWord(
            G.WordChainWithout(_words(line), WHAT_IS_WORDS)(),
        )()
        if M.IdentityCompare(term_word, M.EmptyList)() is M.truth_value:
            return None
        term_text = term_word()
        bridge = G.BridgeFor(learned_version, term_word)()
        ontology_line = ""
        if M.IdentityCompare(bridge, M.EmptyList)() is M.false_value:
            if proof_runtime is not M.EmptyList:
                constructor = G.BridgeConstructor(bridge)()
                facts = G.OntologyFactsFor(
                    M.FromContextGetAllRules(proof_runtime.graph)(),
                    constructor,
                    registry,
                )()
                spoken_facts = []
                remaining_facts = facts
                while M.IdentityCompare(
                    remaining_facts, M.EmptyList,
                )() is M.false_value:
                    spoken_facts.append(_speak_label(M.Head(remaining_facts)()))
                    remaining_facts = M.Tail(remaining_facts)()
                if spoken_facts:
                    ontology_line = (
                        " The packs add: a " + term_text + " "
                        + "; ".join(
                            "is a " + f if f in ("polygon",)
                            else "has " + f for f in spoken_facts
                        )
                        + "."
                    )
            else:
                ontology_line = (
                    " (linked to the pack constructor; ask again after a "
                    "proof has loaded the packs to hear its ontology)"
                )
        definition = G.DefinitionFor(learned_version, M.Char(term_text))()
        if M.IdentityCompare(definition, M.EmptyList)() is M.truth_value:
            if ontology_line:
                return (
                    "I have no taught definition of '" + term_text + "'."
                    + ontology_line
                )
            return "I have no definition of '" + term_text + "'."
        body = G.DefinitionBody(definition)()
        answer = (
            "a " + term_text + " is "
            + _speak_chain(M.Head(M.Tail(body)())())
            + ontology_line
        )
        open_words = G.DefinitionOpenDependencies(
            learned_version, definition, vocabulary, registry,
        )()
        if M.IdentityCompare(open_words, M.EmptyList)() is M.false_value:
            spoken = []
            remaining_open = open_words
            while M.IdentityCompare(
                remaining_open, M.EmptyList,
            )() is M.false_value:
                spoken.append(str(M.Head(remaining_open)()()))
                remaining_open = M.Tail(remaining_open)()
            answer = (
                answer + " (still undefined: "
                + ", ".join(spoken) + ")"
            )
        return answer

    def _handle_training(line, record=True):
        nonlocal examples, proposal_store, registry, pending_queue
        body = line.split(":", 1)[1].strip()
        if "<->" not in body:
            return "A training example is 'training example: WORDS <-> MEANING'."
        surface_text, meaning_text = body.split("<->", 1)
        surface_words = _words(surface_text.strip())
        if M.IdentityCompare(surface_words, M.EmptyList)() is M.truth_value:
            return "The surface side of that example is empty."
        _debug("reading training pair: '" + _speak_chain(surface_words)
               + "' <-> '" + meaning_text.strip() + "'")
        meaning = _meaning_of(meaning_text.strip())
        if M.IdentityCompare(meaning, M.EmptyList)() is M.truth_value:
            _debug("meaning side did not interpret; example dropped")
            return (
                "I cannot interpret the meaning side '" + meaning_text.strip()
                + "'; say it in words or as mul ( a , b ) / add ( a , b )."
            )
        _debug("meaning interpreted as " + _speak_meaning(meaning))
        surface = G.Surface(surface_words)()
        duplicate = M.false_value
        remaining = examples
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            prior = M.Head(remaining)()
            same_surface = M.Compare(
                G.CorrespondenceExampleSurface(prior)(), surface,
            )()
            same_meaning = M.Compare(
                G.CorrespondenceExampleMeaning(prior)(), meaning,
            )()
            if M.AndAtom(same_surface, same_meaning)() is M.truth_value:
                duplicate = M.truth_value
                remaining = M.EmptyList
            else:
                remaining = M.Tail(remaining)()
        if M.IdentityCompare(duplicate, M.truth_value)() is M.truth_value:
            _debug("structurally equal example already recorded; not re-added")
            return "I already have that exact example."
        example = G.CorrespondenceExample(surface, meaning, M.Char("trainer"))()
        examples = M.Pair(example, examples)
        _debug("evidence store now holds "
               + str(_count_chain(examples)) + " example(s)")
        if record:
            _log_lesson(line)
            _debug("lesson line appended to " + lesson_path)
        _debug("compressing evidence: anti-unifying example pairs, "
               "validating candidates against every recorded example...")
        word_entries = M.Head(M.Tail(vocabulary)())()
        generated = G.GenerateCorrespondenceProposals(
            G.ProposalStore(M.EmptyList)(),
            M.Reverse(examples)(),
            word_entries,
            registry,
        )()
        candidate_store = M.Head(generated)()
        registry = M.Head(M.Tail(M.Tail(generated)())())()
        entries = G.ProposalStoreAll(candidate_store)()
        _debug("induction produced " + str(_count_chain(entries))
               + " validated candidate(s)")
        queued_count = 0
        while M.IdentityCompare(entries, M.EmptyList)() is M.false_value:
            entry = M.Head(entries)()
            proposal = G.ProposalEntryProposal(entry)()
            law = G.ProposalLaw(proposal)()
            already_decided = M.false_value
            prior_laws = decided_laws
            while M.IdentityCompare(prior_laws, M.EmptyList)() is M.false_value:
                if M.Compare(M.Head(prior_laws)(), law)() is M.truth_value:
                    already_decided = M.truth_value
                    prior_laws = M.EmptyList
                else:
                    prior_laws = M.Tail(prior_laws)()
            already_queued = M.false_value
            queued = pending_queue
            while M.IdentityCompare(queued, M.EmptyList)() is M.false_value:
                queued_entry = M.Head(queued)()
                queued_proposal = M.Head(queued_entry)()
                if M.Compare(
                    G.ProposalLaw(queued_proposal)(), law,
                )() is M.truth_value:
                    already_queued = M.truth_value
                    queued = M.EmptyList
                else:
                    queued = M.Tail(queued)()
            if M.IdentityCompare(already_decided, M.false_value)() is M.truth_value:
                if M.IdentityCompare(already_queued, M.false_value)() is M.truth_value:
                    _debug("formulating rule from the candidate...")
                    proposal_store = G.ProposalStoreSubmit(
                        proposal_store, proposal,
                    )()
                    annotations = G.ProposalEntryAnnotations(entry)()
                    while M.IdentityCompare(
                        annotations, M.EmptyList,
                    )() is M.false_value:
                        proposal_store = G.ProposalStoreAttach(
                            proposal_store,
                            proposal,
                            M.Head(annotations)(),
                        )()
                        annotations = M.Tail(annotations)()
                    left_nodes = G.GraphNodes(G.LawLeft(law)())()
                    right_nodes = G.GraphNodes(G.LawRight(law)())()
                    pattern_text = _speak_pattern(M.Head(left_nodes)())
                    meaning_text_out = _speak_meaning(M.Head(right_nodes)())
                    count = 0
                    remaining = M.Reverse(examples)()
                    sources = []
                    while M.IdentityCompare(
                        remaining, M.EmptyList,
                    )() is M.false_value:
                        covered = G.CorrespondenceApply(
                            law,
                            G.CorrespondenceExampleSurface(
                                M.Head(remaining)(),
                            )(),
                        )()
                        if M.IdentityCompare(
                            covered, M.EmptyList,
                        )() is M.false_value:
                            count = count + 1
                            sources.append(
                                _speak_pattern(
                                    G.CorrespondenceExampleSurface(
                                        M.Head(remaining)(),
                                    )(),
                                ),
                            )
                        remaining = M.Tail(remaining)()
                    prompt = (
                        "I propose a rule: '" + pattern_text + "' == "
                        + meaning_text_out
                        + "; provenance: anti-unified from " + str(count)
                        + " covering examples [" + "; ".join(sources)
                        + "], validated on every recorded example"
                        + " with parse/render round trip; approve? (yes/no)"
                    )
                    pending_entry = M.Pair(
                        proposal,
                        M.Pair(prompt, M.EmptyList),
                    )
                    pending_queue = M.Reverse(
                        M.Pair(
                            pending_entry,
                            M.Reverse(pending_queue)(),
                        ),
                    )()
                    queued_count = queued_count + 1
                    _debug("rule submitted as a pending proposal; "
                           "queued for decision")
            entries = M.Tail(entries)()
        if M.IdentityCompare(pending_queue, M.EmptyList)() is M.false_value:
            first_pending = M.Head(pending_queue)()
            first_prompt = M.Head(M.Tail(first_pending)())()
            if queued_count > 1:
                return (
                    "(" + str(_count_chain(pending_queue))
                    + " proposals await decisions; here is the first)\n"
                    + "hyge> " + first_prompt
                )
            return first_prompt
        _debug("no new candidate survived validation; waiting for more evidence")
        return "Recorded. I need more examples before I can propose a rule."

    def _render_refusal(reason):
        """One line naming the violated bound, its measure, and the reading.

        A refusal is not a rejection: the proposal stays in the store,
        still approved, and activates unchanged once the bound is raised.
        """
        if M.IsPair(reason)() is M.false_value:
            return "Refused, and no reason term was recorded."
        if M.TermEqual(
            M.Head(reason)(), Lmod.ReasonSafetyLabel,
        )() is M.false_value:
            return "Refused before the safety floor; the proposal stays pending."
        invariant = M.Head(M.Tail(reason)())()
        return (
            "Refused by the safety floor: "
            + G.SafetyInvariantName(invariant)()()
            + " (measure "
            + G.SafetyInvariantMeasure(invariant)()()
            + ", bound "
            + M.GMPRepText(G.SafetyInvariantBound(invariant)())()
            + "). The proposal stays pending and activates unchanged once "
            + "the bound is raised."
        )

    def _persist_talk_state():
        """Write the shared checkpoint, unless a daemon owns it.

        One writer per file. With a daemon cycling, talk state reaches the
        shared version through the inbox instead.
        """
        if os.path.exists(daemon_live_path):
            Dmn.submit_to_inbox(
                SNAPSHOT_DIR,
                proposal_store,
                learned_version,
            )
            _debug("submitted taught graph data to the daemon inbox")
            return
        W.save_checkpoint(
            talk_checkpoint_path,
            learned_version,
            proposal_store,
            talk_ledger,
        )
        _debug("talk state written to " + talk_checkpoint_path)

    def _handle_decision(line, record=True):
        nonlocal proposal_store, learned_version, decided_laws, pending_queue, pending_rule
        if M.IdentityCompare(pending_rule, M.EmptyList)() is M.false_value:
            decided_proposal = pending_rule
            pending_rule = M.EmptyList
            decided_laws = M.Pair(
                G.ProposalLaw(decided_proposal)(), decided_laws,
            )
            if record:
                _log_lesson(line)
                _debug("decision '" + line + "' appended to " + lesson_path)
            if line == "yes":
                approval = G.Approved(
                    decided_proposal, M.Char("trainer"),
                )()
                proposal_store = G.ProposalStoreAttach(
                    proposal_store, decided_proposal, approval,
                )()
                approved_entries = G.ProposalStoreApproved(proposal_store)()
                entry = M.EmptyList
                while M.IdentityCompare(
                    approved_entries, M.EmptyList,
                )() is M.false_value:
                    candidate = M.Head(approved_entries)()
                    if M.TermEqual(
                        G.ProposalEntryProposal(candidate)(),
                        decided_proposal,
                    )() is M.truth_value:
                        entry = candidate
                    approved_entries = M.Tail(approved_entries)()
                if os.path.exists(daemon_live_path):
                    rule_origin = G.ProposalOrigin(decided_proposal)()
                    if M.IsPair(rule_origin)() is M.truth_value:
                        source_premises = M.Head(M.Tail(rule_origin)())()
                        source_replacement = M.Head(
                            M.Tail(M.Tail(rule_origin)())(),
                        )()
                        learned_version = G.InstallTaughtRuleSource(
                            learned_version,
                            source_premises,
                            source_replacement,
                        )()
                    _persist_talk_state()
                    return (
                        "Recorded and submitted. The daemon will activate it "
                        "on its next cycle."
                    )
                activated = G.ActivateProposal(
                    learned_version,
                    entry,
                    proposal_store,
                )()
                installed_version = M.Head(activated)()
                refusal = M.Head(M.Tail(activated)())()
                if M.IdentityCompare(
                    installed_version, M.EmptyList,
                )() is M.truth_value:
                    _persist_talk_state()
                    return _render_refusal(refusal)
                learned_version = installed_version
                _extend_vocabulary()
                _persist_talk_state()
                return (
                    "Recorded and activated. The deduction is now installed "
                    "in the graph."
                )
            rejection = G.Rejected(
                decided_proposal,
                M.Char("trainer"),
                M.Char("declined"),
            )()
            proposal_store = G.ProposalStoreAttach(
                proposal_store, decided_proposal, rejection,
            )()
            _persist_talk_state()
            return "Recorded the rejection. The deduction stays out of the graph."
        if M.IdentityCompare(pending_queue, M.EmptyList)() is M.truth_value:
            return "There is no proposal awaiting a decision."
        if record:
            _log_lesson(line)
            _debug("decision '" + line + "' appended to " + lesson_path)
        decided_entry = M.Head(pending_queue)()
        decided_proposal = M.Head(decided_entry)()
        pending_queue = M.Tail(pending_queue)()
        decided_laws = M.Pair(
            G.ProposalLaw(decided_proposal)(), decided_laws,
        )
        if line == "yes":
            _debug("attaching Approved(proposal, trainer) to the proposal store")
            approval = G.Approved(decided_proposal, M.Char("trainer"))()
            proposal_store = G.ProposalStoreAttach(
                proposal_store, decided_proposal, approval,
            )()
            approved_entries = G.ProposalStoreApproved(proposal_store)()
            entry = M.EmptyList
            while M.IdentityCompare(
                approved_entries, M.EmptyList,
            )() is M.false_value:
                candidate = M.Head(approved_entries)()
                if M.TermEqual(
                    G.ProposalEntryProposal(candidate)(),
                    decided_proposal,
                )() is M.truth_value:
                    entry = candidate
                approved_entries = M.Tail(approved_entries)()
            # With a daemon running, approval is a submission rather than an
            # act: the daemon is the only writer of the shared state, so it
            # takes the activation decision through the ordinary gates. Talk
            # mode standalone keeps activating in-process, so nothing about
            # single-process use changes.
            if os.path.exists(daemon_live_path):
                _persist_talk_state()
                _debug("submitted to the daemon inbox; it will activate")
                return ("Recorded and submitted. The daemon will activate it "
                        "on its next cycle.")
            _debug("activating through ActivateProposal; "
                   "recording the Next splice in the learned version")
            activated = G.ActivateProposal(
                learned_version, entry, proposal_store,
            )()
            installed_version = M.Head(activated)()
            refusal = M.Head(M.Tail(activated)())()
            if M.IdentityCompare(installed_version, M.EmptyList)() is M.truth_value:
                _extend_vocabulary()
                _persist_talk_state()
                return _render_refusal(refusal)
            learned_version = installed_version
            _extend_vocabulary()
            _persist_talk_state()
            _debug("vocabulary rebuilt from installed correspondence laws; "
                   "rule persists via the lesson transcript")
            outcome = "Recorded and activated. The rule is now part of my grammar."
        else:
            _debug("attaching Rejected(proposal, trainer, declined) "
                   "to the proposal store")
            rejection = G.Rejected(
                decided_proposal, M.Char("trainer"), M.Char("declined"),
            )()
            proposal_store = G.ProposalStoreAttach(
                proposal_store, decided_proposal, rejection,
            )()
            outcome = "Recorded the rejection. The rule stays out of my grammar."
        if M.IdentityCompare(pending_queue, M.EmptyList)() is M.false_value:
            first_pending = M.Head(pending_queue)()
            outcome = outcome + "\nhyge> " + M.Head(M.Tail(first_pending)())()
        return outcome

    def _explain_last():
        nonlocal registry
        if M.IdentityCompare(last_derivation, M.EmptyList)() is M.false_value:
            return P.ExplainDerivation(
                last_derivation,
                last_goal,
                last_proof_registry,
            )()
        if M.IdentityCompare(last_outcome, M.EmptyList)() is M.truth_value:
            return "I have not answered anything yet; there is nothing to explain."
        meaning = M.Head(M.Tail(M.Tail(last_outcome)())())()
        body = M.Head(M.Tail(meaning)())()
        word_entries = M.Head(M.Tail(vocabulary)())()
        if M.IsPair(body)() is M.truth_value:
            is_even_prop = M.TermEqual(M.Head(body)(), Lmod.EvenPropLabel)()
            is_odd_prop = M.TermEqual(M.Head(body)(), Lmod.OddPropLabel)()
            if M.OrAtom(is_even_prop, is_odd_prop)() is M.truth_value:
                concept = "even" if is_even_prop is M.truth_value else "odd"
                evaluated = G.MeaningEvaluate(
                    M.Head(M.Tail(body)())(), word_entries, registry,
                )()
                subject = M.Head(evaluated)()
                registry = M.Head(M.Tail(evaluated)())()
                if M.IdentityCompare(subject, M.EmptyList)() is M.truth_value:
                    return "I could not re-evaluate the subject to explain it."
                searched = G.WitnessSearchEven(
                    body, subject, registry, odd=is_odd_prop,
                )()
                verdict = M.Head(searched)()
                evidence = M.Head(M.Tail(searched)())()
                registry = M.Head(M.Tail(M.Tail(searched)())())()
                subject_text = _speak_meaning(subject)
                if M.IdentityCompare(verdict, M.truth_value)() is M.truth_value:
                    witness = M.Head(M.Tail(M.Tail(evidence)())())()
                    witness_nat = M.Head(M.Tail(witness)())()
                    witness_text = _speak_meaning(witness_nat)
                    if concept == "even":
                        return (
                            "because " + subject_text + " = "
                            + witness_text + " + " + witness_text
                            + ": the witness " + witness_text
                            + " confirms it is even."
                        )
                    return (
                        "because " + subject_text + " = "
                        + witness_text + " + " + witness_text + " + 1"
                        + ": the witness " + witness_text
                        + " confirms it is odd."
                    )
                if M.IdentityCompare(verdict, M.false_value)() is M.truth_value:
                    return (
                        "because no k with "
                        + ("k + k" if concept == "even" else "k + k + 1")
                        + " = " + subject_text
                        + " exists: refuted, no witness."
                    )
                return (
                    "the witness search hit its cap before deciding; "
                    "I do not know."
                )
            if M.TermEqual(M.Head(body)(), Lmod.EqualLabel)() is M.truth_value:
                left = M.Head(M.Tail(body)())()
                right = M.Head(M.Tail(M.Tail(body)())())()
                evaluated = G.MeaningEvaluate(left, word_entries, registry)()
                left_value = M.Head(evaluated)()
                registry = M.Head(M.Tail(evaluated)())()
                evaluated = G.MeaningEvaluate(right, word_entries, registry)()
                right_value = M.Head(evaluated)()
                registry = M.Head(M.Tail(evaluated)())()
                if M.IdentityCompare(left_value, M.EmptyList)() is M.truth_value:
                    return "I could not re-evaluate the left side to explain it."
                if M.IdentityCompare(right_value, M.EmptyList)() is M.truth_value:
                    return "I could not re-evaluate the right side to explain it."
                verdict = M.NatEq(left_value, right_value, registry)()
                if M.IdentityCompare(verdict, M.truth_value)() is M.truth_value:
                    closing = "; the values are equal, so the answer was yes."
                else:
                    closing = "; the values differ, so the answer was no."
                return (
                    "because " + _speak_meaning(left)
                    + " evaluates to " + _speak_meaning(left_value)
                    + ", and " + _speak_meaning(right)
                    + " evaluates to " + _speak_meaning(right_value)
                    + closing
                )
        answer = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(last_outcome)())())())())()
        if M.IdentityCompare(answer, M.EmptyList)() is M.truth_value:
            return (
                "the sentence meant " + _speak_meaning(body)
                + ", but no rendered answer was recorded."
            )
        return (
            "because the sentence meant " + _speak_meaning(body)
            + ", which evaluates to " + _speak_chain(M.Head(M.Tail(answer)())())
            + "."
        )

    def _respond(line, record=True):
        nonlocal registry, proof_runtime
        nonlocal last_outcome, last_derivation, last_goal, last_proof_registry
        nonlocal pending_rule, learned_version, proposal_store
        lowered = line.lower()
        if lowered.startswith("query:"):
            known_constructors = G.RuleConstructors(
                learned_version,
                pack_concepts,
            )()
            parsed_query = G.ParseRuleText(
                line[6:].strip(),
                reading_policy,
                reading_digits,
                known_constructors,
                M.truth_value,
            )()
            goal = M.Head(parsed_query)()
            reason = M.Head(M.Tail(parsed_query)())()
            if M.IdentityCompare(goal, M.EmptyList)() is M.truth_value:
                detail = M.EmptyList
                if M.IsPair(reason)() is M.truth_value:
                    detail = M.Head(M.Tail(reason)())()
                if M.IdentityCompare(detail, M.EmptyList)() is M.false_value:
                    return (
                        "I could not parse that query ("
                        + str(detail())
                        + "). Use Predicate(constant)."
                    )
                return "I could not parse that query. Use Predicate(constant)."
            facts = G.InstalledTaughtFacts(learned_version)()
            rules = G.InstalledTaughtRules(learned_version)()
            growing = M.truth_value
            rounds_text = "0"
            while M.IdentityCompare(
                growing, M.truth_value,
            )() is M.truth_value:
                if G.GMPEqualText(rounds_text, "200")() is M.truth_value:
                    growing = M.false_value
                else:
                    rounds_text = G.GMPSuccText(rounds_text)()
                    growing = M.false_value
                    remaining_rules = rules
                    while M.IdentityCompare(
                        remaining_rules, M.EmptyList,
                    )() is M.false_value:
                        taught_rule = M.Head(remaining_rules)()
                        bindings = P.JoinPremises(
                            P.RulePremises(taught_rule)(),
                            facts,
                            M.EmptyList,
                        )()
                        while M.IdentityCompare(
                            bindings, M.EmptyList,
                        )() is M.false_value:
                            binding = M.Head(bindings)()
                            instantiated = M.Instantiate(
                                P.RuleReplacement(taught_rule)(),
                                binding,
                            )()
                            derived = M.Head(instantiated)()
                            seen = M.false_value
                            fact_scan = facts
                            while M.IdentityCompare(
                                fact_scan, M.EmptyList,
                            )() is M.false_value:
                                if M.Compare(
                                    M.Head(fact_scan)(), derived,
                                )() is M.truth_value:
                                    seen = M.truth_value
                                    fact_scan = M.EmptyList
                                else:
                                    fact_scan = M.Tail(fact_scan)()
                            if M.IdentityCompare(
                                seen, M.false_value,
                            )() is M.truth_value:
                                facts = M.Pair(derived, facts)
                                growing = M.truth_value
                            bindings = M.Tail(bindings)()
                        remaining_rules = M.Tail(remaining_rules)()
            goal_found = M.false_value
            fact_scan = facts
            while M.IdentityCompare(
                fact_scan, M.EmptyList,
            )() is M.false_value:
                if M.Compare(M.Head(fact_scan)(), goal)() is M.truth_value:
                    goal_found = M.truth_value
                    fact_scan = M.EmptyList
                else:
                    fact_scan = M.Tail(fact_scan)()
            last_goal = goal
            last_proof_registry = registry
            last_derivation = M.EmptyList
            last_outcome = M.EmptyList
            if M.IdentityCompare(goal_found, M.truth_value)() is M.truth_value:
                return (
                    "yes; derived " + line[6:].strip()
                    + " from the taught facts and approved rules."
                )
            return "no; I could not derive " + line[6:].strip() + "."
            start = M.Knowledge(facts)()
            if proof_runtime is M.EmptyList:
                print(
                    "hyge> loading the theorem runtime for the taught facts and rules",
                    flush=True,
                )
                quiet_boot = io.StringIO()
                with redirect_stdout(quiet_boot):
                    proof_runtime, _proof_packs = boot_from_packs(
                        PACK_PATHS,
                        _runtime_namespace(),
                    )
                _adopt_pack_concepts(
                    proof_runtime.loaded_packs,
                    M.FromContextGetAllRules(proof_runtime.graph)(),
                )
                _teach_runtime_taught_rules(
                    proof_runtime,
                    learned_version,
                )
                proof_runtime.graph._search_disable_console = M.truth_value
                proof_runtime.graph._search_disable_progress_ticker = M.truth_value
                registry = M.FromContextGetConstructors(
                    proof_runtime.graph,
                )()
            derivation = proof_runtime.prove(start, goal)
            last_goal = goal
            last_proof_registry = M.FromContextGetConstructors(
                proof_runtime.graph,
            )()
            last_derivation = derivation
            last_outcome = M.EmptyList
            if M.IdentityCompare(
                derivation, M.EmptyList,
            )() is M.false_value:
                return "yes\n" + P.ExplainDerivation(
                    derivation,
                    goal,
                    last_proof_registry,
                )()
            return "no; I could not derive " + line[6:].strip() + "."
        if lowered.startswith("fact:"):
            known_constructors = G.RuleConstructors(
                learned_version,
                pack_concepts,
            )()
            parsed_fact = G.ParseRuleText(
                line[5:].strip(),
                reading_policy,
                reading_digits,
                known_constructors,
                M.truth_value,
            )()
            fact = M.Head(parsed_fact)()
            reason = M.Head(M.Tail(parsed_fact)())()
            if M.IdentityCompare(fact, M.EmptyList)() is M.truth_value:
                detail = M.EmptyList
                if M.IsPair(reason)() is M.truth_value:
                    detail = M.Head(M.Tail(reason)())()
                if M.IdentityCompare(detail, M.EmptyList)() is M.false_value:
                    return (
                        "I could not parse that fact ("
                        + str(detail())
                        + "). Use Predicate(constant)."
                    )
                return "I could not parse that fact. Use Predicate(constant)."
            installed_fact = G.InstallTaughtFact(learned_version, fact)()
            learned_version = M.Head(installed_fact)()
            if record:
                _log_lesson(line)
            _persist_talk_state()
            return "Recorded fact: " + line[5:].strip()
        if lowered.startswith("rule:"):
            if M.IdentityCompare(
                pending_rule, M.EmptyList,
            )() is M.false_value:
                return "Please approve or reject the pending rule first."
            known_constructors = G.RuleConstructors(
                learned_version,
                pack_concepts,
            )()
            parsed_rule = G.ParseRuleText(
                line[5:].strip(),
                reading_policy,
                reading_digits,
                known_constructors,
            )()
            rule = M.Head(parsed_rule)()
            reason = M.Head(M.Tail(parsed_rule)())()
            if M.IdentityCompare(rule, M.EmptyList)() is M.truth_value:
                if M.IsPair(reason)() is M.truth_value:
                    reason_kind = M.Head(reason)()
                    if M.Compare(
                        reason_kind,
                        M.Char("unknown-constructor"),
                    )() is M.truth_value:
                        unknown = M.Head(M.Tail(reason)())()
                        return (
                            "I do not know the constructor '"
                            + str(unknown())
                            + "'. Teach its definition first."
                        )
                    detail = M.Head(M.Tail(reason)())()
                    return (
                        "I could not parse that rule ("
                        + str(detail())
                        + "). Use P(x), Q(x) -> R(x)."
                    )
                return "I could not parse that rule. Use P(x), Q(x) -> R(x)."
            law = G.CompileDeductionToLaw(rule)()
            if M.IdentityCompare(law, M.EmptyList)() is M.truth_value:
                return (
                    "I could not compile that rule as a monotone deduction; "
                    "it needs at least one premise and one conclusion."
                )
            rule_origin = M.Pair(
                M.Char("dialogue-rule"),
                M.Pair(
                    P.RulePremises(rule)(),
                    M.Pair(P.RuleReplacement(rule)(), M.EmptyList),
                ),
            )
            proposal = G.Proposal(law, rule_origin)()
            proposal_store = G.ProposalStoreSubmit(
                proposal_store,
                proposal,
            )()
            pending_rule = proposal
            if record:
                _log_lesson(line)
            _persist_talk_state()
            return (
                "I propose a deduction rule: "
                + line[5:].strip()
                + ". It keeps every premise and adds the conclusion. "
                + "Approve? (yes/no)"
            )
        if lowered.startswith("training example:"):
            return _handle_training(line, record=record)
        if lowered.startswith("definition:"):
            return _handle_definition(line, record=record)
        if lowered.startswith("is "):
            question_answer = _question_graph_answer(line)
            if question_answer is not None:
                return question_answer
        if lowered.startswith("what is "):
            spoken_definition = _handle_what_is(line)
            if spoken_definition is not None:
                return spoken_definition
        if lowered in ("yes", "no"):
            if M.IdentityCompare(
                pending_rule, M.EmptyList,
            )() is M.false_value:
                return _handle_decision(lowered, record=record)
            if M.IdentityCompare(pending_queue, M.EmptyList)() is M.false_value:
                return _handle_decision(lowered, record=record)
        if lowered.strip() in ("bridge yes", "bridge no"):
            return _handle_bridge_decision(lowered.strip(), record=record)
        if lowered.strip() in ("why", "why?", "explain", "explain?"):
            return _explain_last()
        words = _words(line)
        if M.IdentityCompare(words, M.EmptyList)() is M.truth_value:
            return None
        surface = G.Surface(words)()
        result = G.Converse(vocabulary, surface, registry)()
        outcome = M.Head(result)()
        registry = M.Head(M.Tail(result)())()
        label = M.Head(outcome)()
        if M.IdentityCompare(label, Lmod.UnderstoodLabel)() is M.truth_value:
            last_outcome = outcome
            last_derivation = M.EmptyList
            last_goal = M.EmptyList
            last_proof_registry = M.EmptyList
            meaning = M.Head(M.Tail(M.Tail(outcome)())())()
            body = M.Head(M.Tail(meaning)())()
            if M.IsPair(body)() is M.truth_value:
                if M.TermEqual(M.Head(body)(), Lmod.TaskLabel)() is M.truth_value:
                    task_name = str(M.Head(M.Tail(body)())()())
                    task_atom = M.Char(task_name)
                    known_task = M.false_value
                    if M.Compare(
                        task_atom, M.Char("self-diagnostics"),
                    )() is M.truth_value:
                        known_task = M.truth_value
                    elif M.Compare(task_atom, M.Char("tao"))() is M.truth_value:
                        known_task = M.truth_value
                    elif M.Compare(task_atom, M.Char("e1"))() is M.truth_value:
                        known_task = M.truth_value
                    elif M.Compare(task_atom, M.Char("e2"))() is M.truth_value:
                        known_task = M.truth_value
                    elif M.Compare(task_atom, M.Char("coins"))() is M.truth_value:
                        known_task = M.truth_value
                    elif M.Compare(task_atom, M.Char("sqrt"))() is M.truth_value:
                        known_task = M.truth_value
                    if M.IdentityCompare(
                        known_task, M.false_value,
                    )() is M.truth_value:
                        return "I know the task '" + task_name + "' but cannot run it."
                    print("hyge> running task: " + task_name)
                    # A task is a guest in the conversation, not the
                    # conversation itself. The e2 run proves its theorem and
                    # then tries to snapshot a 200,000-object graph inside a
                    # 120-second deadline; the timeout used to escape through
                    # here and end the session, discarding the proof that had
                    # just succeeded. A task that fails reports and the prompt
                    # returns.
                    try:
                        if M.Compare(
                            task_atom, M.Char("self-diagnostics"),
                        )() is M.truth_value:
                            run_test_mode(False)
                        elif M.Compare(task_atom, M.Char("tao"))() is M.truth_value:
                            run_cold_mode(False, "tao")
                        elif M.Compare(task_atom, M.Char("e1"))() is M.truth_value:
                            run_cold_mode(False, "e1")
                        elif M.Compare(task_atom, M.Char("e2"))() is M.truth_value:
                            run_cold_mode(False, "e2")
                        elif M.Compare(task_atom, M.Char("coins"))() is M.truth_value:
                            run_cold_mode(False, "coins")
                        elif M.Compare(task_atom, M.Char("sqrt"))() is M.truth_value:
                            run_cold_mode(False, "sqrt")
                    except SnapshotSaveTimeout as timeout_error:
                        return ("task '" + task_name + "' finished, but saving "
                                "the snapshot timed out: " + str(timeout_error)
                                + " The work stands; only the save was lost.")
                    except KeyboardInterrupt:
                        raise
                    except Exception as task_error:
                        return ("task '" + task_name + "' failed: "
                                + str(task_error))
                    return "task '" + task_name + "' finished."
                if M.TermEqual(M.Head(body)(), M.IsRealLabel)() is M.truth_value:
                    subject = M.Head(M.Tail(body)())()
                    if M.IsPair(subject)() is M.truth_value:
                        if M.TermEqual(M.Head(subject)(), M.SqrtLabel)() is M.truth_value:
                            source_meaning = M.Head(M.Tail(subject)())()
                            word_entries = M.Head(M.Tail(vocabulary)())()
                            evaluated = G.MeaningEvaluate(
                                source_meaning,
                                word_entries,
                                registry,
                            )()
                            radicand = M.Head(evaluated)()
                            registry = M.Head(M.Tail(evaluated)())()
                            if M.IdentityCompare(radicand, M.EmptyList)() is M.false_value:
                                # Replayed lines are lessons being folded
                                # back in, not questions being asked now.
                                # A proof leaves no persistent state, so
                                # re-proving one at boot spends minutes to
                                # produce nothing -- and it printed proof
                                # chatter before the user said anything.
                                # Old logs still contain question lines;
                                # skip them here rather than punishing
                                # every boot for a line logged before
                                # questions stopped being logged.
                                if not record:
                                    return "yes (recorded question; not re-proved during replay)"
                                # Proving a root takes minutes, and every
                                # word of it used to be swallowed: the boot
                                # is wrapped in redirect_stdout and the
                                # search console is switched off. A silent
                                # prompt is indistinguishable from a hung
                                # one, so say what is happening and when it
                                # finishes.
                                print(
                                    "hyge> understood the proposition; "
                                    "proving it now",
                                    flush=True,
                                )
                                proof_started_at = time.time()
                                if proof_runtime is M.EmptyList:
                                    # The proof runtime always cold-boots from
                                    # packs: snapshot-rehydrated rule chains
                                    # lose their Edge wrappers and crash
                                    # Prove on the next session.
                                    print(
                                        "hyge> loading the theorem packs "
                                        "(first proof this session)",
                                        flush=True,
                                    )
                                    boot_started_at = time.time()
                                    quiet_boot = io.StringIO()
                                    with redirect_stdout(quiet_boot):
                                        proof_runtime, _proof_packs = boot_from_packs(
                                            PACK_PATHS,
                                            _runtime_namespace(),
                                        )
                                    # The loader emitted each pack's
                                    # symbol_map during this boot; adopt
                                    # them so bridge noticing and label
                                    # speech read loader-vouched terms.
                                    _adopt_pack_concepts(
                                        proof_runtime.loaded_packs,
                                        M.FromContextGetAllRules(
                                            proof_runtime.graph,
                                        )(),
                                    )
                                    # This is the boot a conversation
                                    # proves through, and the trainer is
                                    # sitting right here: teach it what
                                    # they taught before it searches.
                                    _teach_runtime_taught_rules(
                                        proof_runtime,
                                        learned_version,
                                    )
                                    print(
                                        "hyge> packs loaded in "
                                        + format(
                                            time.time() - boot_started_at,
                                            ".1f",
                                        )
                                        + " s; searching for a derivation",
                                        flush=True,
                                    )
                                    proof_runtime.graph._search_disable_console = (
                                        M.truth_value
                                    )
                                    proof_runtime.graph._search_disable_progress_ticker = (
                                        M.truth_value
                                    )
                                    registry = M.FromContextGetConstructors(
                                        proof_runtime.graph,
                                    )()
                                start = M.Pair(
                                    M.SqrtLabel,
                                    M.Pair(radicand, M.EmptyList),
                                )
                                goal = M.Pair(
                                    M.IsRealLabel,
                                    M.Pair(start, M.EmptyList),
                                )
                                derivation = proof_runtime.prove(start, goal)
                                print(
                                    "hyge> search finished in "
                                    + format(
                                        time.time() - proof_started_at,
                                        ".1f",
                                    )
                                    + " s",
                                    flush=True,
                                )
                                # Questions are not lessons. A proof leaves
                                # nothing persistent -- the derivation lives
                                # in this session's proof runtime -- so a
                                # logged question only makes every later
                                # boot re-prove it for minutes and discard
                                # the result. Teaching lines and decisions
                                # are logged where they happen; this line
                                # is not.
                                if M.IdentityCompare(
                                    derivation,
                                    M.EmptyList,
                                )() is M.false_value:
                                    proof_registry = M.FromContextGetConstructors(
                                        proof_runtime.graph,
                                    )()
                                    steps = P.DerivationSteps(
                                        derivation,
                                        proof_registry,
                                    )()
                                    if M.IdentityCompare(
                                        steps,
                                        M.EmptyList,
                                    )() is M.truth_value:
                                        return (
                                            "yes (the derivation steps were "
                                            "not replayed this session)"
                                        )
                                    last_derivation = derivation
                                    last_goal = goal
                                    last_proof_registry = proof_registry
                                    return "yes\n" + P.ExplainDerivation(
                                        derivation,
                                        goal,
                                        proof_registry,
                                    )()
                                return "I could not prove that proposition."
                    return "I understood the proposition, but cannot yet prove that form."
            answer = M.Head(
                M.Tail(M.Tail(M.Tail(M.Tail(outcome)())())())(),
            )()
            if M.IdentityCompare(answer, M.EmptyList)() is M.truth_value:
                # No answer Surface exists when the value is symbolic --
                # Mul(three, Sqrt(2)) has no number word. The meaning is
                # still the answer; speak it as a term.
                meaning = M.Head(M.Tail(M.Tail(outcome)())())()
                evaluated = G.MeaningEvaluate(
                    meaning,
                    M.Head(M.Tail(vocabulary)())(),
                    registry,
                )()
                value = M.Head(evaluated)()
                registry = M.Head(M.Tail(evaluated)())()
                if M.IdentityCompare(value, M.EmptyList)() is M.false_value:
                    return _speak_meaning(value)
                return "I understood, but could not render the answer."
            return _speak_chain(M.Head(M.Tail(answer)())())
        if M.IdentityCompare(label, Lmod.AmbiguousLabel)() is M.truth_value:
            interpretations = M.Head(M.Tail(M.Tail(outcome)())())()
            count = 0
            remaining = interpretations
            while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
                count = count + 1
                remaining = M.Tail(remaining)()
            return (
                "That sentence has " + str(count)
                + " disagreeing readings; say which grouping you intend."
            )
        reason = M.Head(M.Tail(M.Tail(outcome)())())()
        reason_label = M.Head(reason)()
        if M.IdentityCompare(
            reason_label,
            Lmod.ReasonUnknownWordLabel,
        )() is M.truth_value:
            unknown = _speak_chain(M.Head(M.Tail(reason)())())
            return "I do not know the word: " + unknown
        if M.IdentityCompare(
            reason_label,
            Lmod.ReasonGroupValueLabel,
        )() is M.truth_value:
            return ("The parentheses balance, but I cannot evaluate what is "
                    "inside them: " + _speak_chain(M.Head(M.Tail(reason)())()))
        if M.IdentityCompare(
            reason_label,
            Lmod.ReasonGroupLabel,
        )() is M.truth_value:
            return "The parentheses in that sentence do not balance."
        if M.IdentityCompare(
            reason_label,
            Lmod.ReasonEvaluationLabel,
        )() is M.truth_value:
            return "I parsed that sentence but could not evaluate it."
        return "I know those words but have no correspondence law for that shape."

    # The checkpoint restores learned_version, but vocabulary is derived
    # data: without this rebuild, laws loaded from disk are invisible to
    # the tokenizer-facing word list and every learned word reports
    # "I do not know the word" until something reinstalls a law. The
    # knowledge survived; the index into it did not.
    _extend_vocabulary()

    replayed = 0
    skipped = 0
    if os.path.exists(lesson_path):
        try:
            with open(lesson_path, "r", encoding="utf-8") as stream:
                lesson_lines = [item.strip() for item in stream.read().splitlines()]
        except OSError:
            lesson_lines = []
        # Replay only lines the checkpoint has not already absorbed. The
        # cursor counts non-blank lines, matching how the mark was written,
        # so blank-line edits cannot shift the boundary.
        cursor_text = "0"
        debug_enabled = False
        for lesson in lesson_lines:
            if lesson:
                if G.GMPLessText(cursor_text, replay_mark_text)() is M.truth_value:
                    skipped = skipped + 1
                else:
                    _respond(lesson, record=False)
                    replayed = replayed + 1
                cursor_text = G.GMPSuccText(cursor_text)()
        debug_enabled = True
        if replayed:
            _persist_talk_state()
            try:
                with open(talk_mark_path, "w", encoding="utf-8") as stream:
                    stream.write(cursor_text)
            except OSError:
                pass

    if sentence is not None:
        answer = _respond(sentence)
        print(answer if answer is not None else "Say something.")
        return

    print("HYGE talk mode. Speak arithmetic; an empty line or 'goodbye' ends it.")
    print("Known forms: 'the sum of A and B', 'A plus B', 'the product of A and B',")
    print("'A times B', mul ( A , B ), add ( A , B ), or a number word (zero..nine).")
    print("Parentheses group subexpressions: 'two times (two plus two)'.")
    print("Teach me: 'training example: double two <-> mul ( two , two )'.")
    print("Teach facts: 'fact: Human(alice)'.")
    print("Teach deductions: 'rule: Human(x), Adult(x) -> Sage(x)'.")
    print("Ask taught rules: 'query: Sage(alice)'.")
    print("Tasks: 'run self-diagnostics', 'solve the tao triangle problem',")
    print("'solve engel e1', 'solve engel e2', 'solve the coin problem',")
    print("'prove square roots are real'.")
    if replayed:
        print("(replayed " + str(replayed) + " lesson lines from " + lesson_path + ")")
    if M.IdentityCompare(pending_queue, M.EmptyList)() is M.false_value:
        first_pending = M.Head(pending_queue)()
        print("hyge> (" + str(_count_chain(pending_queue))
              + " proposal(s) from the replayed lessons still await your decision)")
        print("hyge> " + M.Head(M.Tail(first_pending)())())
    while True:
        try:
            line = input("you> ")
        except EOFError:
            print()
            break
        stripped = line.strip()
        if stripped == "" or stripped == "goodbye":
            print("hyge> goodbye")
            break
        answer = _respond(stripped)
        print("hyge> " + (answer if answer is not None else "Say something."))


def run_test_mode(debug: bool = False):
    if debug:
        P.SetDebugTrace(M.truth_value)()
    else:
        P.SetDebugTrace(M.false_value)()
    runtime, _packs = boot_from_packs(PACK_PATHS, _runtime_namespace())
    runtime.graph._search_disable_console = M.truth_value
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


def run_ingest_mode(records_path: str):
    """Batch ingestion of structured TrainingRecords.

    python main.py ingest <training_records_file>

    For each TrainingRecord in the file: load the meaning structure as
    Knowledge, create a PlannerAlternative carrying the trainer-supplied
    strategy method, attempt the conclusion obligation, and record an
    AttemptResult. Reuses the pack loader, the invariance pipeline, and the
    planner; no new proof engine.
    """
    from . import training as T

    runtime, packs = boot_from_packs(PACK_PATHS, _runtime_namespace())
    _print_summary(runtime, "Cold boot summary for ingest")

    loader = T.TrainingRecordLoader(_runtime_namespace())
    records = loader.load_records_file(records_path)

    print(f"\n--- Ingestion: {os.path.basename(records_path)} ({len(records)} record(s)) ---")
    attempts = ()
    for index, (record, rules_pack) in enumerate(records, start=1):
        attempt, summary = T.attempt_training_record(runtime, packs, record, rules_pack)
        attempts = attempts + (attempt,)
        print(
            f"{index}. {summary.record_id}: {summary.status_text} "
            f"via {summary.method_text} in {summary.elapsed:.2f}s "
            f"(planner root {summary.planner_root_status}, "
            f"method alternative {summary.alternative_status}, "
            f"derivation retained {summary.retained})"
        )
        if summary.failure_reason:
            print(f"   reason: {summary.failure_reason}")
        sys.stdout.flush()

    print(f"\ningested {len(attempts)} record(s)")


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


def run_live_mode(requested_workers):
    """One process, two children: the conversation and the cycling daemon.

    The daemon is spawned as a subprocess and its commentary is drained by
    a reader thread that prints above the prompt, so its output appears as
    it happens without corrupting a line being typed. The conversation
    runs in this process's foreground, because a REPL needs the terminal.

    Killing this process kills the daemon with it: the child is terminated
    in the finally block, and its liveness file removed, so a later talk
    session does not believe a dead daemon is still cycling.
    """
    import threading

    # PACKAGE_DIR is this package; its parent is the import root, which is
    # what a child needs on PYTHONPATH to import hyge. IMPORT_ROOT itself
    # only exists in the re-exec branch above, so it is recomputed here.
    import_root = os.path.dirname(PACKAGE_DIR)
    import shlex

    daemon_command = (
        "HYGE_LIVE_DAEMON=1 exec "
        + shlex.quote(sys.executable)
        + " -u -m "
        + shlex.quote(__package__ + ".main")
        + " daemon --workers "
        + shlex.quote(str(requested_workers))
    )
    daemon_child = subprocess.Popen(
        daemon_command,
        cwd=import_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        shell=True,
    )

    def drain():
        for line in daemon_child.stdout:
            sys.stdout.write("\r\033[K[machine] " + line.rstrip() + "\nyou> ")
            sys.stdout.flush()

    reader = threading.Thread(target=drain, daemon=True)
    reader.start()
    print("live mode: the machine is cycling while you talk. "
          "Its work appears as [machine] lines.")
    try:
        run_talk_mode()
    finally:
        daemon_child.terminate()
        try:
            daemon_child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            daemon_child.kill()
        live_path = os.path.join(SNAPSHOT_DIR, Dmn.DAEMON_LIVE_NAME)
        if os.path.exists(live_path):
            os.remove(live_path)
        print("live mode: daemon stopped.")


def main():
    parser = argparse.ArgumentParser(description="HYGE runtime modes")
    parser.add_argument(
        "mode",
        nargs="?",
        default="talk",
        choices=[
            "talk", "cold", "warm", "test", "inspect", "search-worker",
            "ingest", "daemon", "live",
        ],
        help=(
            "Boot mode: talk (default; natural-language interaction through "
            "correspondence laws), cold (from packs), warm (from snapshot), "
            "test, inspect, search-worker, ingest (training records), or "
            "daemon (cycle the shared talk state), or live (one process "
            "supervising a conversation and a cycling daemon)"
        ),
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=0,
        help="daemon mode: worker processes per cycle (0 = single process)",
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
        if args.mode == "talk":
            run_talk_mode(sentence=args.arg1)
        elif args.mode == "cold":
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
        elif args.mode == "ingest":
            if args.arg1 is None:
                raise RuntimeError("ingest requires a training-records file path")
            run_ingest_mode(args.arg1)
        elif args.mode == "live":
            run_live_mode(args.workers)
        elif args.mode == "daemon":
            # arg1: how many cycles to run. arg2: how many worker processes
            # each cycle fans out to, zero for a single-process cycle.
            # arg1 is a GMP count text and stays one. arg2 is a host process
            # count -- multiprocessing needs an int the same way a PID or an
            # exit code does -- so argparse produces it directly rather than
            # this code converting a machine numeral into one.
            Dmn.run_daemon(
                SNAPSHOT_DIR,
                M.GMPRep("100" if args.arg1 is None else args.arg1),
                worker_count=args.workers,
            )
        else:
            run_test_mode(debug_enabled)
    except KeyboardInterrupt:
        print("\nInterrupted; terminating active HYGE worker processes...")
        _terminate_active_children()
        raise SystemExit(130)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
