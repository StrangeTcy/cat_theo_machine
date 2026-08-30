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
    # A console interrupt reaches the re-exec parent as well as the
    # child; the parent bows out quietly and lets the child's own
    # teardown speak.
    try:
        CHILD = subprocess.run(CHILD_ARGS, cwd=IMPORT_ROOT, env=CHILD_ENV)
    except KeyboardInterrupt:
        raise SystemExit(130)
    raise SystemExit(CHILD.returncode)
else:
    from .math import arithmetic as A
    from . import graph as G
    from . import heuristics as Hmod
    from . import labels as Lmod
    from . import machine as M
    from . import matching as X
    from . import mining as Min
    from . import parity as Par
    from . import residue as Res
    from . import modular as Mod
    from . import euclid as Euc
    from . import story_talk_adapter as StoryTalk
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
    os.path.join(PACK_DIR, "mystery-micro.pack.yaml"),
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
    if filter_name in ("mystery", "all"):
        mystery_pack = packs.by_name("mystery-micro")
        if "mystery_micro_before_reveal" in mystery_pack.examples:
            start, goal = mystery_pack.examples["mystery_micro_before_reveal"]
            cases.append(
                ("mystery micro: contradiction refutes the alibi",
                 start, goal, mystery_pack.rule_chain, mystery_pack.phi),
            )
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
    taught_count = G.AddTaughtDerivationSchemata(
        runtime.graph,
        G.InstalledTaughtDerivationSchemata(taught_version)(),
        taught_count,
    )()
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
    scoped_assumptions = M.EmptyList
    scoped_divisibility_assumptions = M.EmptyList
    scoped_congruence_assumptions = M.EmptyList
    scoped_integer_equations = M.EmptyList
    last_parity_stall = M.EmptyList
    last_residue_stall = M.EmptyList
    last_modular_stall = M.EmptyList
    last_euclidean_stall = M.EmptyList
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
    pending_gaps = M.EmptyList
    pending_process = M.EmptyList
    pending_bridge = M.EmptyList
    # Open words the packs can ground wait their turn here: each entry
    # is the same Pair(word, Pair(constructor, EmptyList)) a bridge
    # decision consumes, loaded one at a time as the previous bridge is
    # decided.
    pending_bridge_queue = M.EmptyList
    # The questions on the table, one at a time: each entry is
    # Pair(kind, Pair(prompt, EmptyList)) with kind one of "rule",
    # "bridge", "process". A reply asks only the head; every decision
    # pops the ask it answered and surfaces the next. No reply stacks
    # two questions, and no answer is ever met with deafness.
    pending_asks = M.EmptyList
    # A correspondence the daemon found and proposed sits here while it
    # is the question on the table: the proposal term itself, decided by
    # a bare yes or no, routed to the daemon through the inbox like
    # every other activation. machine_asked holds every proposal already
    # surfaced, so a pending finding is asked once, not once per cycle.
    pending_machine = M.EmptyList
    machine_asked = M.EmptyList
    # The part of a taught problem the machine is still asking for:
    # "board" (the numbers), "neighbors" (the pairs a move touches),
    # or "step" (how much a move adds). A bare line at the prompt
    # answers the standing question; the meaning graph grows from the
    # machine's own questions.
    pending_problem_kind = ""
    # Words of the taught problem still without meaning, asked one at
    # a time: the chain holds the words in order of appearance, the
    # slot holds the word the standing question asks about. A bare
    # line at the prompt is its meaning; 'skip' passes one word,
    # 'skip all' stops the asking.
    pending_unknown_words = M.EmptyList
    pending_unknown_word = M.EmptyList
    decided_laws = M.EmptyList
    proof_runtime = M.EmptyList
    last_outcome = M.EmptyList
    last_derivation = M.EmptyList
    last_goal = M.EmptyList
    last_proof_registry = M.EmptyList
    lesson_path = os.path.join(SNAPSHOT_DIR, "talk_lessons.log")

    def _push_ask(kind_text, prompt_text):
        """Queue a question; entries are Pair(kind, Pair(prompt, Empty))."""
        nonlocal pending_asks
        entry = M.Pair(
            M.Char(kind_text), M.Pair(M.Char(prompt_text), M.EmptyList),
        )
        if M.IdentityCompare(pending_asks, M.EmptyList)() is M.truth_value:
            pending_asks = M.Pair(entry, M.EmptyList)
            return
        pending_asks = M.Reverse(
            M.Pair(entry, M.Reverse(pending_asks)()),
        )()

    def _pop_ask(kind_text):
        """Retire the first queued question of the answered kind.

        The answered question is not always the head -- an answer can
        decide a rule question while a bridge question stands in front
        of it -- so the first ask of the kind is retired wherever it
        sits.
        """
        nonlocal pending_asks
        if M.IdentityCompare(pending_asks, M.EmptyList)() is M.truth_value:
            return
        head_entry = M.Head(pending_asks)()
        if M.Compare(
            M.Head(head_entry)(), M.Char(kind_text),
        )() is M.truth_value:
            pending_asks = M.Tail(pending_asks)()
            return
        kept_reversed = M.EmptyList
        scan = pending_asks
        retired = M.false_value
        while M.IdentityCompare(scan, M.EmptyList)() is M.false_value:
            entry = M.Head(scan)()
            if M.IdentityCompare(
                retired, M.truth_value,
            )() is M.truth_value:
                kept_reversed = M.Pair(entry, kept_reversed)
            else:
                if M.Compare(
                    M.Head(entry)(), M.Char(kind_text),
                )() is M.truth_value:
                    retired = M.truth_value
                else:
                    kept_reversed = M.Pair(entry, kept_reversed)
            scan = M.Tail(scan)()
        if M.IdentityCompare(
            retired, M.truth_value,
        )() is M.truth_value:
            pending_asks = M.Reverse(kept_reversed)()

    def _ask_next_line():
        """The one question on the table, or nothing."""
        if M.IdentityCompare(pending_asks, M.EmptyList)() is M.truth_value:
            return ""
        head_entry = M.Head(pending_asks)()
        prompt_atom = M.Head(M.Tail(head_entry)())()
        return " " + str(prompt_atom())

    # Read-back: the daemon is the only writer of the shared state, so
    # this process adopts its writes. At each turn the checkpoint's
    # stamp is checked; when the daemon has written, its version, its
    # proposals, and its firing ledger merge into memory through the
    # same idempotent union the daemon itself applies.
    last_state_stamp = 0.0
    if os.path.exists(talk_checkpoint_path):
        last_state_stamp = os.path.getmtime(talk_checkpoint_path)

    def _machine_ask_text(proposal):
        """The question a machine-found correspondence puts to the human."""
        payload = G.ProposalLaw(proposal)()
        if G.IsRuleUnification(payload)() is M.truth_value:
            keep_rule = P.PrettyRule(
                P.MultiRule(
                    G.RuleUnificationKeepPremises(payload)(),
                    G.RuleUnificationKeepReplacement(payload)(),
                )(),
                registry,
            )()
            retire_rule = P.PrettyRule(
                P.MultiRule(
                    G.RuleUnificationRetirePremises(payload)(),
                    G.RuleUnificationRetireReplacement(payload)(),
                )(),
                registry,
            )()
            kind_text = "up to instantiation"
            if M.Compare(
                G.RuleUnificationKind(payload)(),
                M.Char("renaming"),
            )() is M.truth_value:
                kind_text = "up to renaming"
            return (
                "A correspondence turned up in the background: the rule '"
                + keep_rule
                + "' and the rule '"
                + retire_rule
                + "' are one rule "
                + kind_text
                + ". Unify them? (yes/no)"
            )
        if G.IsSubgraphReformulation(payload)() is M.truth_value:
            pattern_text = M.PrettyTerm(
                G.SubgraphReformulationPattern(payload)(),
                registry,
            )()
            count_text = M.GMPRepText(
                G.SubgraphReformulationCount(payload)(),
            )()
            return (
                "A correspondence turned up in the background: the subgraph "
                + pattern_text
                + " is in the graph "
                + count_text
                + " times. Reformulate it under one name? (yes/no)"
            )
        return "The machine proposes a correspondence. Approve? (yes/no)"

    def _adopt_daemon_state():
        """Take the daemon's writes in, and surface what it found."""
        nonlocal learned_version, proposal_store, talk_ledger
        nonlocal pending_machine, machine_asked, last_state_stamp
        if not os.path.exists(daemon_live_path):
            return
        if not os.path.exists(talk_checkpoint_path):
            return
        current_state_stamp = os.path.getmtime(talk_checkpoint_path)
        if current_state_stamp == last_state_stamp:
            return
        last_state_stamp = current_state_stamp
        read_back = W.load_checkpoint(talk_checkpoint_path)
        if M.IdentityCompare(read_back, M.EmptyList)() is M.false_value:
            learned_version = G.MergeGraphVersion(
                M.Head(read_back)(),
                learned_version,
            )()
            read_back_store = Dmn.DaemonMergeInbox(
                proposal_store,
                M.Head(M.Tail(read_back)())(),
            )()
            proposal_store = M.Head(read_back_store)()
            talk_ledger = M.Head(
                M.Tail(M.Tail(read_back)())(),
            )()
            _debug("read the daemon's state back")
        # What the daemon found in the background becomes a question on
        # the table, one at a time: pending proposals the machine itself
        # submitted, waiting on the human, not yet surfaced.
        machine_scan = G.ProposalStoreEntries(proposal_store)()
        while M.IdentityCompare(machine_scan, M.EmptyList)() is M.false_value:
            entry = M.Head(machine_scan)()
            machine_scan = M.Tail(machine_scan)()
            proposal = G.ProposalEntryProposal(entry)()
            origin = G.ProposalOrigin(proposal)()
            machine_found = M.false_value
            if M.IsPair(origin)() is M.truth_value:
                if M.Compare(
                    M.Head(origin)(),
                    M.Char("machine-correspondence"),
                )() is M.truth_value:
                    machine_found = M.truth_value
            undecided = M.false_value
            if M.IdentityCompare(machine_found, M.truth_value)() is M.truth_value:
                undecided = M.truth_value
                annotation_scan = G.ProposalEntryAnnotations(entry)()
                while M.IdentityCompare(
                    annotation_scan,
                    M.EmptyList,
                )() is M.false_value:
                    annotation = M.Head(annotation_scan)()
                    if M.IsPair(annotation)() is M.truth_value:
                        if M.TermEqual(
                            M.Head(annotation)(),
                            Lmod.ApprovedLabel,
                        )() is M.truth_value:
                            undecided = M.false_value
                            annotation_scan = M.EmptyList
                        elif M.TermEqual(
                            M.Head(annotation)(),
                            Lmod.RejectedLabel,
                        )() is M.truth_value:
                            undecided = M.false_value
                            annotation_scan = M.EmptyList
                    if M.IdentityCompare(
                        annotation_scan,
                        M.EmptyList,
                    )() is M.false_value:
                        annotation_scan = M.Tail(annotation_scan)()
            already_asked = M.false_value
            if M.IdentityCompare(undecided, M.truth_value)() is M.truth_value:
                asked_scan = machine_asked
                while M.IdentityCompare(
                    asked_scan,
                    M.EmptyList,
                )() is M.false_value:
                    if M.Compare(M.Head(asked_scan)(), proposal)() is M.truth_value:
                        already_asked = M.truth_value
                        asked_scan = M.EmptyList
                    else:
                        asked_scan = M.Tail(asked_scan)()
            slot_free = M.IdentityCompare(
                pending_machine,
                M.EmptyList,
            )() is M.truth_value
            if (
                M.IdentityCompare(machine_found, M.truth_value)() is M.truth_value
                and M.IdentityCompare(undecided, M.truth_value)() is M.truth_value
                and M.IdentityCompare(already_asked, M.truth_value)() is M.false_value
                and slot_free
            ):
                question = _machine_ask_text(proposal)
                machine_asked = M.Pair(proposal, machine_asked)
                pending_machine = proposal
                _push_ask("machine", question)
                print("hyge> " + question)
                machine_scan = M.EmptyList

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

    def _numeral_value_text(term):
        """The GMP value text of a vocabulary numeral word, or EmptyList."""
        word_entries = M.Head(M.Tail(vocabulary)())()
        entry_scan = word_entries
        while M.IdentityCompare(
            entry_scan, M.EmptyList,
        )() is M.false_value:
            entry = M.Head(entry_scan)()
            if M.Compare(M.Head(entry)(), term)() is M.truth_value:
                return M.GMPRepText(
                    M.NatRepOf(
                        M.Head(M.Tail(entry)())(), registry,
                    )(),
                )()
            entry_scan = M.Tail(entry_scan)()
        return M.EmptyList

    def _ground_arithmetic_value(term):
        """Evaluate add and times over numeral words, or EmptyList.

        The machine's own numbers do the work: word entries carry Nat
        values, and the GMP text arithmetic computes with them. A term
        that is not ground arithmetic evaluates to nothing.
        """
        if M.IsPair(term)() is not M.truth_value:
            return _numeral_value_text(term)
        head = M.Head(term)()
        args = M.Tail(term)()
        if M.IdentityCompare(args, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        if M.Compare(head, M.Char("add"))() is M.truth_value:
            if M.IdentityCompare(
                M.Tail(args)(), M.EmptyList,
            )() is M.false_value:
                left = _ground_arithmetic_value(M.Head(args)())
                right = _ground_arithmetic_value(
                    M.Head(M.Tail(args)())(),
                )
                if left is not M.EmptyList:
                    if right is not M.EmptyList:
                        return G.GMPAddText(left, right)()
            return M.EmptyList
        if M.Compare(head, M.Char("times"))() is M.truth_value:
            if M.IdentityCompare(
                M.Tail(args)(), M.EmptyList,
            )() is M.false_value:
                left = _ground_arithmetic_value(M.Head(args)())
                right = _ground_arithmetic_value(
                    M.Head(M.Tail(args)())(),
                )
                if left is not M.EmptyList:
                    if right is not M.EmptyList:
                        return G.GMPMulText(left, right)()
            return M.EmptyList
        if M.Compare(head, M.Char("sub"))() is M.truth_value:
            if M.IdentityCompare(
                M.Tail(args)(), M.EmptyList,
            )() is M.false_value:
                left = _ground_arithmetic_value(M.Head(args)())
                right = _ground_arithmetic_value(
                    M.Head(M.Tail(args)())(),
                )
                if left is not M.EmptyList:
                    if right is not M.EmptyList:
                        return G.GMPSubText(left, right)()
            return M.EmptyList
        return _numeral_value_text(term)

    def _words_of_value_text(value_text):
        """The spoken words of a small value, from the word entries."""
        word_entries = M.Head(M.Tail(vocabulary)())()
        entry_scan = word_entries
        while M.IdentityCompare(
            entry_scan, M.EmptyList,
        )() is M.false_value:
            entry = M.Head(entry_scan)()
            entry_text = M.GMPRepText(
                M.NatRepOf(
                    M.Head(M.Tail(entry)())(), registry,
                )(),
            )()
            if M.IdentityCompare(
                G.GMPEqualText(entry_text, value_text)(),
                M.truth_value,
            )() is M.truth_value:
                return str(M.Head(entry)()())
            entry_scan = M.Tail(entry_scan)()
        return value_text

    def _division_texts(a_text, n_text):
        """The division of n by a: Pair(quotient, remainder) texts.

        Repeated subtraction with the machine's own GMP arithmetic:
        n = a*q + r with r below a. a must be above zero.
        """
        quotient_text = "0"
        remainder_text = n_text
        while M.IdentityCompare(
            G.GMPLessText(remainder_text, a_text)(),
            M.truth_value,
        )() is M.false_value:
            remainder_text = G.GMPSubText(
                remainder_text, a_text,
            )()
            quotient_text = G.GMPSuccText(quotient_text)()
        return M.Pair(quotient_text, M.Pair(remainder_text, M.EmptyList))

    def _computed_divisibility(term):
        """Compute a ground divisible(A, N) claim by trial division.

        Returns Pair(Char("holds"), Pair(remainder_text, EmptyList))
        when the division leaves no remainder, Pair(Char("differs"),
        Pair(remainder_text, EmptyList)) when it leaves one, and
        EmptyList when the term is not a ground divisibility claim.
        """
        if M.IsPair(term)() is not M.truth_value:
            return M.EmptyList
        # The claim may speak the word or the constructor the word
        # bridges to -- a bridged 'divisible' parses to the pack's
        # division concept, and the arithmetic follows the bridge.
        acceptable_heads = M.Pair(M.Char("divisible"), M.EmptyList)
        divisible_bridge = G.BridgeFor(
            learned_version, M.Char("divisible"),
        )()
        if M.IdentityCompare(
            divisible_bridge, M.EmptyList,
        )() is M.false_value:
            acceptable_heads = M.Pair(
                G.BridgeConstructor(divisible_bridge)(),
                acceptable_heads,
            )
        head_known = M.false_value
        head_scan = acceptable_heads
        while M.IdentityCompare(
            head_scan, M.EmptyList,
        )() is M.false_value:
            if M.Compare(
                M.Head(term)(), M.Head(head_scan)(),
            )() is M.truth_value:
                head_known = M.truth_value
                head_scan = M.EmptyList
            else:
                head_scan = M.Tail(head_scan)()
        if M.IdentityCompare(
            head_known, M.false_value,
        )() is M.truth_value:
            return M.EmptyList
        args = M.Tail(term)()
        if M.IdentityCompare(args, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        if M.IdentityCompare(
            M.Tail(args)(), M.EmptyList,
        )() is M.truth_value:
            return M.EmptyList
        divisor_value = _ground_arithmetic_value(M.Head(args)())
        number_value = _ground_arithmetic_value(
            M.Head(M.Tail(args)())(),
        )
        if divisor_value is M.EmptyList:
            return M.EmptyList
        if number_value is M.EmptyList:
            return M.EmptyList
        if M.IdentityCompare(
            G.GMPEqualText(divisor_value, "0")(),
            M.truth_value,
        )() is M.truth_value:
            return M.EmptyList
        division = _division_texts(divisor_value, number_value)
        remainder_text = str(M.Head(M.Tail(division)())())
        if M.IdentityCompare(
            G.GMPEqualText(remainder_text, "0")(),
            M.truth_value,
        )() is M.truth_value:
            return M.Pair(
                M.Char("holds"), M.Pair(remainder_text, M.EmptyList),
            )
        return M.Pair(
            M.Char("differs"), M.Pair(remainder_text, M.EmptyList),
        )

    def _verify_ground_equation(fact):
        """Check a ground arithmetic equation before recording it.

        Returns EmptyList when the fact is not a same(equation,
        numeral) claim. Returns Pair(Char("holds"), EmptyList) when
        the machine's own numbers confirm it, and Pair(Char("differs"),
        Pair(computed_text, EmptyList)) with the computed value when
        they do not.
        """
        if M.IsPair(fact)() is not M.truth_value:
            return M.EmptyList
        if M.Compare(
            M.Head(fact)(), M.Char("same"),
        )() is not M.truth_value:
            return M.EmptyList
        args = M.Tail(fact)()
        if M.IdentityCompare(args, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        if M.IdentityCompare(
            M.Tail(args)(), M.EmptyList,
        )() is M.truth_value:
            return M.EmptyList
        left = M.Head(args)()
        right = M.Head(M.Tail(args)())()
        left_value = _ground_arithmetic_value(left)
        right_value = _ground_arithmetic_value(right)
        if left_value is M.EmptyList:
            return M.EmptyList
        if right_value is M.EmptyList:
            return M.EmptyList
        if M.IdentityCompare(
            G.GMPEqualText(left_value, right_value)(),
            M.truth_value,
        )() is M.truth_value:
            return M.Pair(M.Char("holds"), M.EmptyList)
        return M.Pair(
            M.Char("differs"),
            M.Pair(left_value, M.EmptyList),
        )

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
        nonlocal pending_rule, proposal_store
        nonlocal pending_bridge
        nonlocal pending_process
        nonlocal pending_asks
        nonlocal pending_queue
        nonlocal pending_bridge_queue
        nonlocal pending_machine
        # A new definition supersedes the questions still on the table:
        # outstanding pendings keep their slots, but the asks restart
        # from this definition's own questions, one at a time. A
        # correspondence found in the background survives the restart --
        # it is still the machine's open question, waiting on the human.
        pending_asks = M.EmptyList
        pending_bridge_queue = M.EmptyList
        if M.IdentityCompare(pending_machine, M.EmptyList)() is M.false_value:
            _push_ask("machine", _machine_ask_text(pending_machine))
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
        # The grammar reader could not span the line; the structural
        # reader still can. A definition is a term, a copula, and a
        # body -- the split needs no grammar beyond that, and the
        # definition is recorded, bridged, and reported with its open
        # dependencies rather than refused.
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
        term_display = term_text.replace("_", " ")
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
            # A duplicate definition is a gap probe. The recorded
            # definition is restated, and what it still lacks is
            # computed from the state -- an unbridged term, a process
            # whose keep/strike answer never landed -- with the first
            # gap raised as the question on the table.
            existing_body = M.Head(
                M.Tail(G.DefinitionBody(existing)())(),
            )()
            duplicate_line = (
                "I already have a definition of '" + term_display + "': "
                + _speak_chain(existing_body)
            )
            # An operator still standing in the recorded reading gates
            # the compilation: its case split is re-proposed first, so
            # the definition can be interpreted and compiled.
            _reraise_operator_gap(term_word, term_text)
            _reraise_shape_gap(term_word, existing)
            body_is_process = M.false_value
            body_scan = existing_body
            while M.IdentityCompare(
                body_scan, M.EmptyList,
            )() is M.false_value:
                if M.Compare(
                    M.Head(body_scan)(), M.Char("process"),
                )() is M.truth_value:
                    body_is_process = M.truth_value
                    body_scan = M.EmptyList
                else:
                    body_scan = M.Tail(body_scan)()
            if M.IdentityCompare(
                body_is_process, M.truth_value,
            )() is M.truth_value:
                has_process_rules = M.false_value
                rule_scan = G.GraphNodes(learned_version)()
                while M.IdentityCompare(
                    rule_scan, M.EmptyList,
                )() is M.false_value:
                    rule_node = M.Head(rule_scan)()
                    rule_scan = M.Tail(rule_scan)()
                    if M.IsPair(rule_node)() is M.truth_value:
                        if M.Compare(
                            M.Head(rule_node)(), M.Char("process-rule"),
                        )() is M.truth_value:
                            if M.Compare(
                                M.Head(M.Tail(rule_node)())(), term_word,
                            )() is M.truth_value:
                                has_process_rules = M.truth_value
                                rule_scan = M.EmptyList
                if M.IdentityCompare(
                    has_process_rules, M.false_value,
                )() is M.truth_value:
                    pending_process = term_word
                    _push_ask(
                        "process",
                        " define this process for me in keep/strike"
                        + " terms",
                    )
            existing_bridge = G.BridgeFor(learned_version, term_word)()
            if M.IdentityCompare(
                existing_bridge, M.EmptyList,
            )() is M.truth_value:
                if M.IdentityCompare(
                    _pack_constructor_for(term_text), M.EmptyList,
                )() is M.truth_value:
                    pending_bridge = M.Pair(
                        term_word,
                        M.Pair(M.Char(term_text), M.EmptyList),
                    )
                    _push_ask(
                        "bridge",
                        " The word '" + term_display + "' names something"
                        + " new; make it a constructor of its own?"
                        + " (bridge yes/bridge no)",
                    )
            _propose_bridge(term_text)
            # The duplicate's open words get their grounding offers
            # too: a word the packs or the taught rules can name is
            # offered here, not only at first teach.
            duplicate_open = G.DefinitionOpenDependencies(
                learned_version, existing, vocabulary, registry,
            )()
            duplicate_spoken = []
            duplicate_open_scan = duplicate_open
            while M.IdentityCompare(
                duplicate_open_scan, M.EmptyList,
            )() is M.false_value:
                duplicate_spoken.append(
                    str(M.Head(duplicate_open_scan)()()),
                )
                duplicate_open_scan = M.Tail(duplicate_open_scan)()
            _queue_open_word_candidates(duplicate_spoken)
            return duplicate_line + _ask_next_line()
        learned_version = new_version
        # The body is interpreted with the binder discipline before any
        # compilation: 'itself' resolves to the reading's self variable,
        # 'only' and 'no' become operator terms, and the reading node
        # lands in the graph where the compiler's gate can see it.
        interpretation = G.InterpretDefinitionBody(term_word, body_chain)()
        interpreted_chain = M.Head(M.Tail(interpretation)())()
        interpreted_conditions = G.InterpretOperators(interpreted_chain)()
        learned_version = G.GraphVersion(
            M.Pair(
                G.DefinitionReading(
                    term_word,
                    M.Head(interpretation)(),
                    interpreted_chain,
                    interpreted_conditions,
                )(),
                G.GraphNodes(learned_version)(),
            ),
            G.GraphEdges(learned_version)(),
            G.GraphVersionInvariants(learned_version)(),
        )()
        # 'no' denies its segment: the negation lives as a case split,
        # one branch for the segment holding, one for the defined term,
        # proposed through the ordinary approval gate.
        negation_line = ""
        # 'only' restricts to its list: the exclusive items become a
        # split over same(d, item) -- one branch per item, the binder's
        # self rendered as the defined term -- proposed through the
        # same gate. The list separator is 'and'; stop words fall away;
        # the reflexive contributes the term itself.
        restriction_line = ""
        only_proposed = M.false_value
        conditions_scan = interpreted_conditions
        while M.IdentityCompare(
            conditions_scan, M.EmptyList,
        )() is M.false_value:
            condition = M.Head(conditions_scan)()
            if M.IsPair(condition)() is M.truth_value:
                if M.Compare(
                    M.Head(condition)(), Lmod.NoLabel,
                )() is M.truth_value:
                    segment = M.Head(M.Tail(condition)())()
                    segment_word = M.EmptyList
                    segment_scan = segment
                    while M.IdentityCompare(
                        segment_scan, M.EmptyList,
                    )() is M.false_value:
                        segment_item = M.Head(segment_scan)()
                        if M.IsPair(segment_item)() is M.truth_value:
                            segment_scan = M.Tail(segment_scan)()
                        else:
                            if G.SurfaceChainHasWord(
                                G.DEFINITION_STOP_WORDS, segment_item,
                            )() is M.truth_value:
                                segment_scan = M.Tail(segment_scan)()
                            else:
                                segment_word = segment_item
                                segment_scan = M.EmptyList
                    if M.IdentityCompare(
                        segment_word, M.EmptyList,
                    )() is M.false_value:
                        split_body = (
                            str(segment_word()) + "(x), "
                            + term_text + "(x)"
                        )
                        split_text = "one of " + split_body
                        known_constructors = G.RuleConstructors(
                            learned_version,
                            pack_concepts,
                        )()
                        parsed_case = G.ParseRuleText(
                            split_body,
                            reading_policy,
                            reading_digits,
                            known_constructors,
                            M.Char("exactly-one"),
                        )()
                        case_split = M.Head(parsed_case)()
                        case_reason = M.Head(M.Tail(parsed_case)())()
                        if M.IdentityCompare(
                            case_split, M.EmptyList,
                        )() is M.false_value:
                            exactly_one = G.CaseSplitExactlyOne(case_split)()
                            case_origin = M.Pair(
                                M.Char("case-split"),
                                M.Pair(
                                    exactly_one,
                                    M.Pair(term_word, M.EmptyList),
                                ),
                            )
                            case_proposal = G.Proposal(
                                case_split, case_origin,
                            )()
                            proposal_store = G.ProposalStoreSubmit(
                                proposal_store, case_proposal,
                            )()
                            pending_rule = case_proposal
                            negation_line = (
                                " The 'no' denies its segment, so a case"
                                + " split is proposed: " + split_text
                                + ". Approve? (yes/no)"
                            )
                            conditions_scan = M.EmptyList
            if M.IdentityCompare(
                only_proposed, M.truth_value,
            )() is M.false_value:
                if M.IdentityCompare(
                    conditions_scan, M.EmptyList,
                )() is M.false_value:
                    condition = M.Head(conditions_scan)()
                    if M.IsPair(condition)() is M.truth_value:
                        if M.Compare(
                            M.Head(condition)(), Lmod.OnlyLabel,
                        )() is M.truth_value:
                            segment = M.Head(M.Tail(condition)())()
                            items_reversed = M.EmptyList
                            current_reversed = M.EmptyList
                            segment_walk = segment
                            while M.IdentityCompare(
                                segment_walk, M.EmptyList,
                            )() is M.false_value:
                                seg_item = M.Head(segment_walk)()
                                if M.Compare(
                                    seg_item, M.Char("and"),
                                )() is M.truth_value:
                                    items_reversed = M.Pair(
                                        M.Reverse(current_reversed)(),
                                        items_reversed,
                                    )
                                    current_reversed = M.EmptyList
                                else:
                                    current_reversed = M.Pair(
                                        seg_item, current_reversed,
                                    )
                                segment_walk = M.Tail(segment_walk)()
                            if M.IdentityCompare(
                                current_reversed, M.EmptyList,
                            )() is M.false_value:
                                items_reversed = M.Pair(
                                    M.Reverse(current_reversed)(),
                                    items_reversed,
                                )
                            items = M.Reverse(items_reversed)()
                            branch_texts_reversed = []
                            item_scan = items
                            while M.IdentityCompare(
                                item_scan, M.EmptyList,
                            )() is M.false_value:
                                item_chain = M.Head(item_scan)()
                                item_text = ""
                                inner_scan = item_chain
                                while M.IdentityCompare(
                                    inner_scan, M.EmptyList,
                                )() is M.false_value:
                                    part = M.Head(inner_scan)()
                                    part_text = ""
                                    if M.IsPair(part)() is M.truth_value:
                                        if M.Compare(
                                            M.Head(part)(), M.VarTag,
                                        )() is M.truth_value:
                                            part_text = term_text
                                    else:
                                        if G.SurfaceChainHasWord(
                                            G.DEFINITION_STOP_WORDS, part,
                                        )() is M.false_value:
                                            part_text = str(part())
                                    if part_text != "":
                                        if item_text == "":
                                            item_text = part_text
                                        else:
                                            item_text = (
                                                item_text + " " + part_text
                                            )
                                    inner_scan = M.Tail(inner_scan)()
                                if item_text != "":
                                    branch_texts_reversed.append(
                                        "same(d, " + item_text + ")"
                                    )
                                item_scan = M.Tail(item_scan)()
                            if branch_texts_reversed:
                                only_split_body = ", ".join(
                                    branch_texts_reversed
                                )
                                only_split_text = (
                                    "one of " + only_split_body
                                )
                                known_constructors = G.RuleConstructors(
                                    learned_version,
                                    pack_concepts,
                                )()
                                parsed_only = G.ParseRuleText(
                                    only_split_body,
                                    reading_policy,
                                    reading_digits,
                                    known_constructors,
                                    M.Char("exactly-one"),
                                )()
                                only_split = M.Head(parsed_only)()
                                if M.IdentityCompare(
                                    only_split, M.EmptyList,
                                )() is M.false_value:
                                    only_exactly = G.CaseSplitExactlyOne(
                                        only_split,
                                    )()
                                    only_origin = M.Pair(
                                        M.Char("case-split"),
                                        M.Pair(
                                            only_exactly,
                                            M.Pair(term_word, M.EmptyList),
                                        ),
                                    )
                                    only_proposal = G.Proposal(
                                        only_split, only_origin,
                                    )()
                                    proposal_store = G.ProposalStoreSubmit(
                                        proposal_store, only_proposal,
                                    )()
                                    pending_rule = only_proposal
                                    restriction_line = (
                                        " The 'only' restricts to its list,"
                                        + " so a case split is proposed: "
                                        + only_split_text
                                        + ". Approve? (yes/no)"
                                    )
                                    only_proposed = M.truth_value
            if M.IdentityCompare(
                conditions_scan, M.EmptyList,
            )() is M.false_value:
                conditions_scan = M.Tail(conditions_scan)()
        operator_line = ""
        operator_count_text = M.GMPRepText(
            M.Head(M.Tail(M.Tail(interpretation)())())(),
        )()
        if G.GMPEqualText(operator_count_text, "0")() is M.false_value:
            operator_line = (
                " Its 'only' and 'no' are recorded as operators with the"
                + " reflexive bound; it compiles to no law while they"
                + " stand uninterpreted."
            )
        # A term with no bridge and no pack constructor names something
        # new: propose minting a constructor of its own, through the
        # same bridge gate as a pack link. A defined term becomes
        # predicable -- rules can speak it, queries can parse it.
        mint_line = ""
        existing_bridge = G.BridgeFor(learned_version, term_word)()
        if M.IdentityCompare(existing_bridge, M.EmptyList)() is M.truth_value:
            pack_constructor = _pack_constructor_for(term_text)
            if M.IdentityCompare(
                pack_constructor, M.EmptyList,
            )() is M.truth_value:
                pending_bridge = M.Pair(
                    term_word,
                    M.Pair(M.Char(term_text), M.EmptyList),
                )
                mint_line = (
                    " The word '" + term_display + "' names something"
                    + " new; make it a constructor of its own?"
                    + " (bridge yes/bridge no)"
                )
        # A definition whose body characterizes its term as a process
        # asks for the process's operational definition: what does the
        # process keep, what does it strike. The ask is the gap
        # discipline applied to the genus -- 'process' is the open
        # word, and the question solicits its keep/strike meaning.
        process_ask_line = ""
        process_scan = body_chain
        while M.IdentityCompare(
            process_scan, M.EmptyList,
        )() is M.false_value:
            process_word = M.Head(process_scan)()
            if G.SurfaceChainHasWord(
                ARTICLE_WORDS, process_word,
            )() is M.truth_value:
                process_scan = M.Tail(process_scan)()
            else:
                if M.Compare(process_word, M.Char("process"))() is M.truth_value:
                    pending_process = term_word
                    process_ask_line = (
                        " define this process for me in keep/strike"
                        + " terms"
                    )
                process_scan = M.EmptyList
        # A body the templates cannot read proposes its own shape: the
        # trainer's phrasing becomes a template law -- stop words stay
        # literal, content words become slots, the first content word
        # reads as the genus. Nothing about the shape is in the
        # machine; the line itself is the grammar lesson.
        shape_line = ""
        body_reading = G.DefinitionBodyReading(
            definition, vocabulary, registry,
        )()
        if M.IdentityCompare(body_reading, M.EmptyList)() is M.truth_value:
            shape_reversed = M.EmptyList
            shape_scan = body_chain
            genus_variable = M.EmptyList
            first_content = M.truth_value
            shape_words = 0
            while M.IdentityCompare(
                shape_scan, M.EmptyList,
            )() is M.false_value:
                body_word = M.Head(shape_scan)()
                if G.SurfaceChainHasWord(
                    G.DEFINITION_STOP_WORDS, body_word,
                )() is M.truth_value:
                    shape_reversed = M.Pair(body_word, shape_reversed)
                else:
                    slot_variable = M.Pair(
                        M.VarTag,
                        M.Pair(M.Char("?" + str(body_word())), M.EmptyList),
                    )
                    shape_reversed = M.Pair(slot_variable, shape_reversed)
                    if M.IdentityCompare(
                        first_content, M.truth_value,
                    )() is M.truth_value:
                        genus_variable = slot_variable
                        first_content = M.false_value
                shape_words = shape_words + 1
                shape_scan = M.Tail(shape_scan)()
            if M.IdentityCompare(
                genus_variable, M.EmptyList,
            )() is M.false_value:
                shape_chain = M.Reverse(shape_reversed)()
                shape_surface = G.Surface(shape_chain)()
                genus_meaning = G.Meaning(
                    M.Pair(
                        Lmod.DefinitionGenusLabel,
                        M.Pair(
                            G.Surface(M.Pair(genus_variable, M.EmptyList))(),
                            M.EmptyList,
                        ),
                    ),
                )()
                shape_law = G.CompileRuleToLaw(
                    P.Rule(shape_surface, genus_meaning),
                )()
                if M.IdentityCompare(shape_law, M.EmptyList)() is M.false_value:
                    shape_proposal = G.Proposal(
                        shape_law,
                        M.Pair(
                            M.Char("definition-shape"),
                            M.Pair(term_word, M.EmptyList),
                        ),
                    )()
                    proposal_store = G.ProposalStoreSubmit(
                        proposal_store, shape_proposal,
                    )()
                    # A restriction proposal may already occupy the
                    # decision slot; a second proposal must queue
                    # behind it, not silently replace it.
                    if M.IdentityCompare(
                        pending_rule, M.EmptyList,
                    )() is M.false_value:
                        pending_queue = M.Reverse(
                            M.Pair(
                                M.Pair(
                                    shape_proposal,
                                    M.Pair(
                                        M.Char(
                                            " The body's shape is new to"
                                            + " me; reading its first word"
                                            + " as the genus would make it"
                                            + " a template. Approve this"
                                            + " shape? (yes/no)",
                                        ),
                                        M.EmptyList,
                                    ),
                                ),
                                M.Reverse(pending_queue)(),
                            ),
                        )()
                    else:
                        pending_rule = shape_proposal
                    shape_line = (
                        " The body's shape is new to me; reading its"
                        + " first word as the genus would make it a"
                        + " template. Approve this shape? (yes/no)"
                    )
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
        # One question at a time: the questions this definition raised
        # queue in their listed order -- restriction, mint, shape,
        # process -- and the reply asks only the first. Each decision
        # pops its ask and surfaces the next, so no reply ever stacks
        # two questions and no stray yes lands on deaf ears.
        if restriction_line != "":
            _push_ask("rule", restriction_line)
        if mint_line != "":
            _push_ask("bridge", mint_line)
        if shape_line != "":
            _push_ask("rule", shape_line)
        if process_ask_line != "":
            _push_ask("process", process_ask_line)
        _propose_bridge(term_text)
        open_words = G.DefinitionOpenDependencies(
            learned_version, definition, vocabulary, registry,
        )()
        if M.IdentityCompare(open_words, M.EmptyList)() is M.truth_value:
            return (
                "Recorded: a " + term_display + " is "
                + _speak_chain(body_chain) + ". Every word in it is grounded."
                + operator_line
                + negation_line
                + definition_law_line
                + _ask_next_line()
            )
        spoken = []
        remaining_open = open_words
        while M.IdentityCompare(remaining_open, M.EmptyList)() is M.false_value:
            spoken.append(str(M.Head(remaining_open)()()))
            remaining_open = M.Tail(remaining_open)()
        # The packs or the taught rules may know the open words.
        _queue_open_word_candidates(spoken)
        return (
            "Recorded: a " + term_display + " is " + _speak_chain(body_chain) + ". "
            + "But I do not know what "
            + " or ".join("'" + w + "'" for w in spoken)
            + " " + ("is" if len(spoken) == 1 else "are")
            + ". Define "
            + ("it" if len(spoken) == 1 else "them")
            + " with 'definition: a " + spoken[0] + " is ...'."
            + operator_line
            + negation_line
            + definition_law_line
            + _ask_next_line()
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

    def _pack_candidate_for_word(word_text):
        """The pack constructor an unknown word could name, or EmptyList.

        Returns Pair(candidate_word, Pair(constructor, EmptyList)).
        Exact matches and singular folds come first; failing those, a
        shared five-letter stem notices derivational kin like
        'divisible' and 'divides'. The noticing only proposes -- the
        trainer's bridge decision connects.
        """
        word = M.Char(word_text)
        singular = G.WordSingular(word)()
        remaining = pack_concepts
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            entry = M.Head(remaining)()
            if M.Compare(M.Head(entry)(), word)() is M.truth_value:
                return entry
            if M.IdentityCompare(singular, M.EmptyList)() is M.false_value:
                if M.Compare(M.Head(entry)(), singular)() is M.truth_value:
                    return entry
            remaining = M.Tail(remaining)()
        if len(word_text) >= 6:
            stem = word_text[:4]
            remaining = pack_concepts
            while M.IdentityCompare(
                remaining, M.EmptyList,
            )() is M.false_value:
                entry = M.Head(remaining)()
                candidate_text = str(M.Head(entry)()())
                if (
                    candidate_text.startswith(stem)
                    and len(candidate_text) >= 6
                ):
                    return entry
                remaining = M.Tail(remaining)()
        return M.EmptyList

    def _taught_predicate_for_word(word_text):
        """A predicate the installed taught rules already speak.

        Returns Pair(predicate_word, Pair(predicate_word, EmptyList))
        shaped like a pack entry, so the same bridge machinery links an
        open body word to the predicate the rules use -- 'number' can
        name what the taught number rules speak.
        """
        word = M.Char(word_text)
        singular = G.WordSingular(word)()
        rule_scan = G.InstalledTaughtRules(learned_version)()
        while M.IdentityCompare(
            rule_scan, M.EmptyList,
        )() is M.false_value:
            taught_rule = M.Head(rule_scan)()
            replacement = P.RuleReplacement(taught_rule)()
            if M.IsPair(replacement)() is M.truth_value:
                head_word = M.Head(replacement)()
                if M.Compare(head_word, word)() is M.truth_value:
                    return M.Pair(
                        head_word, M.Pair(head_word, M.EmptyList),
                    )
                if M.IdentityCompare(
                    singular, M.EmptyList,
                )() is M.false_value:
                    if M.Compare(head_word, singular)() is M.truth_value:
                        return M.Pair(
                            head_word, M.Pair(head_word, M.EmptyList),
                        )
            rule_scan = M.Tail(rule_scan)()
        return M.EmptyList

    def _queue_open_word_candidates(spoken_list):
        """Offer pack or taught-predicate links for open words.

        Each open word with a pack concept or a taught predicate
        behind it queues a bridge question; the asks surface one at a
        time behind whatever is already on the table. The same offers
        are raised wherever an open word blocks -- a fresh definition,
        a duplicate definition probing its gaps, a question the word
        keeps out -- so the grounding is offered at the point of
        failure, not only at first teach.
        """
        nonlocal pending_bridge_queue
        candidates_reversed = M.EmptyList
        for open_word_text in spoken_list:
            # An offer already standing for this word is not repeated:
            # the pending bridge or its queue carries it.
            already_offered = M.false_value
            offer_word = M.Char(open_word_text)
            if M.IdentityCompare(
                pending_bridge, M.EmptyList,
            )() is M.false_value:
                if M.Compare(
                    M.Head(pending_bridge)(), offer_word,
                )() is M.truth_value:
                    already_offered = M.truth_value
            offer_scan = pending_bridge_queue
            while M.IdentityCompare(
                offer_scan, M.EmptyList,
            )() is M.false_value:
                if M.Compare(
                    M.Head(M.Head(offer_scan)())(), offer_word,
                )() is M.truth_value:
                    already_offered = M.truth_value
                    offer_scan = M.EmptyList
                else:
                    offer_scan = M.Tail(offer_scan)()
            if M.IdentityCompare(
                already_offered, M.truth_value,
            )() is M.truth_value:
                continue
            open_candidate = _pack_candidate_for_word(open_word_text)
            candidate_source = "pack"
            if M.IdentityCompare(
                open_candidate, M.EmptyList,
            )() is M.truth_value:
                open_candidate = _taught_predicate_for_word(open_word_text)
                candidate_source = "taught"
            if M.IdentityCompare(
                open_candidate, M.EmptyList,
            )() is M.false_value:
                candidate_word_text = str(M.Head(open_candidate)()())
                if candidate_source == "pack":
                    ask_text = (
                        " The packs know '" + candidate_word_text
                        + "'; link '" + open_word_text + "' to it?"
                        + " (bridge yes/bridge no)"
                    )
                else:
                    ask_text = (
                        " The taught rules speak '" + candidate_word_text
                        + "'; link '" + open_word_text + "' to it?"
                        + " (bridge yes/bridge no)"
                    )
                candidates_reversed = M.Pair(
                    M.Pair(
                        M.Pair(
                            M.Char(open_word_text),
                            M.Pair(
                                M.Head(M.Tail(open_candidate)())(),
                                M.EmptyList,
                            ),
                        ),
                        M.Pair(M.Char(ask_text), M.EmptyList),
                    ),
                    candidates_reversed,
                )
        candidate_scan = M.Reverse(candidates_reversed)()
        combined_reversed = M.Reverse(pending_bridge_queue)()
        while M.IdentityCompare(
            candidate_scan, M.EmptyList,
        )() is M.false_value:
            candidate_pair = M.Head(candidate_scan)()
            candidate_entry = M.Head(candidate_pair)()
            candidate_ask = M.Head(M.Tail(candidate_pair)())()
            combined_reversed = M.Pair(
                candidate_entry, combined_reversed,
            )
            _push_ask("bridge", str(candidate_ask()))
            candidate_scan = M.Tail(candidate_scan)()
        pending_bridge_queue = M.Reverse(combined_reversed)()

    def _propose_restriction_from_conditions(term_word, term_text, conditions):
        """Rebuild the case split an OnlyOf condition carries.

        The recorded reading's conditions hold the same list the
        fresh-teach flow parsed; the split is rebuilt from them so a
        decision that predates the interpretation machinery -- or was
        never made -- can be proposed again. Returns
        Pair(proposal, Pair(split_text, EmptyList)), or EmptyList when
        no Only condition stands.
        """
        nonlocal proposal_store
        condition_scan = conditions
        while M.IdentityCompare(
            condition_scan, M.EmptyList,
        )() is M.false_value:
            condition = M.Head(condition_scan)()
            if M.IsPair(condition)() is M.truth_value:
                if M.Compare(
                    M.Head(condition)(), Lmod.OnlyLabel,
                )() is M.truth_value:
                    segment = M.Head(M.Tail(condition)())()
                    items_reversed = M.EmptyList
                    current_reversed = M.EmptyList
                    segment_walk = segment
                    while M.IdentityCompare(
                        segment_walk, M.EmptyList,
                    )() is M.false_value:
                        seg_item = M.Head(segment_walk)()
                        if M.Compare(
                            seg_item, M.Char("and"),
                        )() is M.truth_value:
                            items_reversed = M.Pair(
                                M.Reverse(current_reversed)(),
                                items_reversed,
                            )
                            current_reversed = M.EmptyList
                        else:
                            current_reversed = M.Pair(
                                seg_item, current_reversed,
                            )
                        segment_walk = M.Tail(segment_walk)()
                    if M.IdentityCompare(
                        current_reversed, M.EmptyList,
                    )() is M.false_value:
                        items_reversed = M.Pair(
                            M.Reverse(current_reversed)(),
                            items_reversed,
                        )
                    items = M.Reverse(items_reversed)()
                    branch_texts_reversed = []
                    item_scan = items
                    while M.IdentityCompare(
                        item_scan, M.EmptyList,
                    )() is M.false_value:
                        item_chain = M.Head(item_scan)()
                        item_text = ""
                        inner_scan = item_chain
                        while M.IdentityCompare(
                            inner_scan, M.EmptyList,
                        )() is M.false_value:
                            part = M.Head(inner_scan)()
                            part_text = ""
                            if M.IsPair(part)() is M.truth_value:
                                if M.Compare(
                                    M.Head(part)(), M.VarTag,
                                )() is M.truth_value:
                                    part_text = term_text
                            else:
                                if G.SurfaceChainHasWord(
                                    G.DEFINITION_STOP_WORDS, part,
                                )() is M.false_value:
                                    part_text = str(part())
                            if part_text != "":
                                if item_text == "":
                                    item_text = part_text
                                else:
                                    item_text = (
                                        item_text + " " + part_text
                                    )
                            inner_scan = M.Tail(inner_scan)()
                        if item_text != "":
                            branch_texts_reversed.append(
                                "same(d, " + item_text + ")"
                            )
                        item_scan = M.Tail(item_scan)()
                    if branch_texts_reversed:
                        only_split_body = ", ".join(branch_texts_reversed)
                        known_constructors = G.RuleConstructors(
                            learned_version,
                            pack_concepts,
                        )()
                        parsed_only = G.ParseRuleText(
                            only_split_body,
                            reading_policy,
                            reading_digits,
                            known_constructors,
                            M.Char("exactly-one"),
                        )()
                        only_split = M.Head(parsed_only)()
                        if M.IdentityCompare(
                            only_split, M.EmptyList,
                        )() is M.false_value:
                            only_exactly = G.CaseSplitExactlyOne(
                                only_split,
                            )()
                            only_origin = M.Pair(
                                M.Char("case-split"),
                                M.Pair(
                                    only_exactly,
                                    M.Pair(term_word, M.EmptyList),
                                ),
                            )
                            only_proposal = G.Proposal(
                                only_split, only_origin,
                            )()
                            proposal_store = G.ProposalStoreSubmit(
                                proposal_store, only_proposal,
                            )()
                            return M.Pair(
                                only_proposal,
                                M.Pair(
                                    "one of " + only_split_body,
                                    M.EmptyList,
                                ),
                            )
            condition_scan = M.Tail(condition_scan)()
        return M.EmptyList

    def _reraise_operator_gap(term_word, term_text):
        """Queue the case-split question a standing operator gates on.

        A reading whose chain still carries Only/No markers gates the
        compilation; the split that interprets them is re-proposed from
        the reading's own conditions and queued as the question on the
        table, so a stale decision -- or a missing one -- can be made
        wherever the gap blocks.
        """
        nonlocal pending_queue
        # An identical split already queued or pending is not
        # re-proposed.
        already_raised = M.false_value
        queue_scan = pending_queue
        while M.IdentityCompare(
            queue_scan, M.EmptyList,
        )() is M.false_value:
            queued_proposal = M.Head(M.Head(queue_scan)())()
            queued_origin = G.ProposalOrigin(queued_proposal)()
            if M.IsPair(queued_origin)() is M.truth_value:
                if M.Compare(
                    M.Head(queued_origin)(), M.Char("case-split"),
                )() is M.truth_value:
                    if M.IdentityCompare(
                        M.Tail(M.Tail(queued_origin)())(),
                        M.EmptyList,
                    )() is M.false_value:
                        if M.Compare(
                            M.Head(
                                M.Tail(M.Tail(queued_origin)())(),
                            )(),
                            term_word,
                        )() is M.truth_value:
                            already_raised = M.truth_value
                            queue_scan = M.EmptyList
            if M.IdentityCompare(
                queue_scan, M.EmptyList,
            )() is M.false_value:
                queue_scan = M.Tail(queue_scan)()
        if M.IdentityCompare(
            already_raised, M.false_value,
        )() is M.truth_value:
            if M.IdentityCompare(
                pending_rule, M.EmptyList,
            )() is M.false_value:
                pending_origin = G.ProposalOrigin(pending_rule)()
                if M.IsPair(pending_origin)() is M.truth_value:
                    if M.Compare(
                        M.Head(pending_origin)(), M.Char("case-split"),
                    )() is M.truth_value:
                        if M.IdentityCompare(
                            M.Tail(M.Tail(pending_origin)())(),
                            M.EmptyList,
                        )() is M.false_value:
                            if M.Compare(
                                M.Head(
                                    M.Tail(M.Tail(pending_origin)())(),
                                )(),
                                term_word,
                            )() is M.truth_value:
                                already_raised = M.truth_value
        if M.IdentityCompare(
            already_raised, M.truth_value,
        )() is M.truth_value:
            return M.false_value
        reading = G.DefinitionReadingFor(learned_version, term_word)()
        if M.IdentityCompare(reading, M.EmptyList)() is M.truth_value:
            return M.false_value
        reading_chain = M.Head(
            M.Tail(M.Tail(M.Tail(reading)())())(),
        )()
        markers_stand = M.false_value
        chain_scan = reading_chain
        while M.IdentityCompare(
            chain_scan, M.EmptyList,
        )() is M.false_value:
            chain_item = M.Head(chain_scan)()
            if M.IsPair(chain_item)() is M.truth_value:
                if M.OrAtom(
                    M.Compare(
                        M.Head(chain_item)(), Lmod.OnlyLabel,
                    )(),
                    M.Compare(
                        M.Head(chain_item)(), Lmod.NoLabel,
                    )(),
                )() is M.truth_value:
                    markers_stand = M.truth_value
                    chain_scan = M.EmptyList
            if M.IdentityCompare(
                chain_scan, M.EmptyList,
            )() is M.false_value:
                chain_scan = M.Tail(chain_scan)()
        if M.IdentityCompare(
            markers_stand, M.false_value,
        )() is M.truth_value:
            return M.false_value
        reading_conditions = M.Head(
            M.Tail(
                M.Tail(M.Tail(M.Tail(reading)())())(),
            )(),
        )()
        rebuilt = _propose_restriction_from_conditions(
            term_word, term_text, reading_conditions,
        )
        if M.IdentityCompare(rebuilt, M.EmptyList)() is M.truth_value:
            return M.false_value
        split_proposal = M.Head(rebuilt)()
        split_text = str(M.Head(M.Tail(rebuilt)())())
        prompt_text = (
            " The 'only' restricts to its list, so a case split is"
            + " proposed: " + split_text + ". Approve? (yes/no)"
        )
        pending_queue = M.Reverse(
            M.Pair(
                M.Pair(
                    split_proposal,
                    M.Pair(prompt_text, M.EmptyList),
                ),
                M.Reverse(pending_queue)(),
            ),
        )()
        _push_ask("rule", prompt_text)
        return M.truth_value

    def _reraise_shape_gap(term_word, definition):
        """Queue the shape question a readable body still lacks.

        A body the correspondence templates cannot read needs its shape
        law -- the trainer's phrasing as a template, the first content
        word as the genus -- before it can compile. The shape is
        re-proposed from the recorded body wherever the gap blocks, so
        a decision that predates the machinery or never happened can
        be made now. Returns truth when a shape was queued.
        """
        nonlocal proposal_store, pending_queue
        # A shape already queued or pending for this term is not
        # re-proposed.
        already_raised = M.false_value
        queue_scan = pending_queue
        while M.IdentityCompare(
            queue_scan, M.EmptyList,
        )() is M.false_value:
            queued_proposal = M.Head(M.Head(queue_scan)())()
            queued_origin = G.ProposalOrigin(queued_proposal)()
            if M.IsPair(queued_origin)() is M.truth_value:
                if M.Compare(
                    M.Head(queued_origin)(),
                    M.Char("definition-shape"),
                )() is M.truth_value:
                    if M.IdentityCompare(
                        M.Tail(queued_origin)(), M.EmptyList,
                    )() is M.false_value:
                        if M.Compare(
                            M.Head(M.Tail(queued_origin)())(),
                            term_word,
                        )() is M.truth_value:
                            already_raised = M.truth_value
                            queue_scan = M.EmptyList
            if M.IdentityCompare(
                queue_scan, M.EmptyList,
            )() is M.false_value:
                queue_scan = M.Tail(queue_scan)()
        if M.IdentityCompare(
            already_raised, M.false_value,
        )() is M.truth_value:
            if M.IdentityCompare(
                pending_rule, M.EmptyList,
            )() is M.false_value:
                pending_origin = G.ProposalOrigin(pending_rule)()
                if M.IsPair(pending_origin)() is M.truth_value:
                    if M.Compare(
                        M.Head(pending_origin)(),
                        M.Char("definition-shape"),
                    )() is M.truth_value:
                        if M.IdentityCompare(
                            M.Tail(pending_origin)(), M.EmptyList,
                        )() is M.false_value:
                            if M.Compare(
                                M.Head(M.Tail(pending_origin)())(),
                                term_word,
                            )() is M.truth_value:
                                already_raised = M.truth_value
        if M.IdentityCompare(
            already_raised, M.truth_value,
        )() is M.truth_value:
            return M.false_value
        # Only a body the templates cannot read needs its shape.
        body_reading = G.DefinitionBodyReading(
            definition, vocabulary, registry,
        )()
        if M.IdentityCompare(
            body_reading, M.EmptyList,
        )() is M.false_value:
            return M.false_value
        body = G.DefinitionBody(definition)()
        shape_body_chain = M.Head(M.Tail(body)())()
        shape_reversed = M.EmptyList
        shape_scan = shape_body_chain
        genus_variable = M.EmptyList
        first_content = M.truth_value
        while M.IdentityCompare(
            shape_scan, M.EmptyList,
        )() is M.false_value:
            body_word = M.Head(shape_scan)()
            if G.SurfaceChainHasWord(
                G.DEFINITION_STOP_WORDS, body_word,
            )() is M.truth_value:
                shape_reversed = M.Pair(body_word, shape_reversed)
            else:
                slot_variable = M.Pair(
                    M.VarTag,
                    M.Pair(
                        M.Char("?" + str(body_word())),
                        M.EmptyList,
                    ),
                )
                shape_reversed = M.Pair(
                    slot_variable, shape_reversed,
                )
                if M.IdentityCompare(
                    first_content, M.truth_value,
                )() is M.truth_value:
                    genus_variable = slot_variable
                    first_content = M.false_value
            shape_scan = M.Tail(shape_scan)()
        if M.IdentityCompare(
            genus_variable, M.EmptyList,
        )() is M.truth_value:
            return M.false_value
        shape_chain = M.Reverse(shape_reversed)()
        shape_surface = G.Surface(shape_chain)()
        genus_meaning = G.Meaning(
            M.Pair(
                Lmod.DefinitionGenusLabel,
                M.Pair(
                    G.Surface(
                        M.Pair(genus_variable, M.EmptyList),
                    )(),
                    M.EmptyList,
                ),
            ),
        )()
        shape_law = G.CompileRuleToLaw(
            P.Rule(shape_surface, genus_meaning),
        )()
        if M.IdentityCompare(
            shape_law, M.EmptyList,
        )() is M.truth_value:
            return M.false_value
        shape_proposal = G.Proposal(
            shape_law,
            M.Pair(
                M.Char("definition-shape"),
                M.Pair(term_word, M.EmptyList),
            ),
        )()
        proposal_store = G.ProposalStoreSubmit(
            proposal_store, shape_proposal,
        )()
        prompt_text = (
            " The body's shape is new to me; reading its first word"
            + " as the genus would make it a template. Approve this"
            + " shape? (yes/no)"
        )
        pending_queue = M.Reverse(
            M.Pair(
                M.Pair(
                    shape_proposal,
                    M.Pair(prompt_text, M.EmptyList),
                ),
                M.Reverse(pending_queue)(),
            ),
        )()
        _push_ask("rule", prompt_text)
        return M.truth_value

    def _ensure_bridge_loaded():
        """Load the next queued open-word bridge, if one waits."""
        nonlocal pending_bridge, pending_bridge_queue
        if M.IdentityCompare(pending_bridge, M.EmptyList)() is M.truth_value:
            if M.IdentityCompare(
                pending_bridge_queue, M.EmptyList,
            )() is M.false_value:
                pending_bridge = M.Head(pending_bridge_queue)()
                pending_bridge_queue = M.Tail(pending_bridge_queue)()

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
        _push_ask(
            "bridge",
            " The packs also know '" + term_text + "' as a constructor "
            "with its own ontology; shall I link the word to it? "
            "(bridge yes/bridge no)",
        )
        return ""

    def _handle_bridge_decision(line, record=True):
        nonlocal pending_bridge, learned_version
        if M.IdentityCompare(pending_bridge, M.EmptyList)() is M.truth_value:
            # A bridge answer with no bridge awaiting it: either a
            # question stands that wants another grammar, or none does.
            if M.IdentityCompare(
                pending_asks, M.EmptyList,
            )() is M.false_value:
                return (
                    "A bridge answer does not fit the question on the"
                    + " table." + _ask_next_line()
                )
            return "There is no bridge awaiting a decision."
        if record:
            _log_lesson(line)
        word = M.Head(pending_bridge)()
        constructor = M.Head(M.Tail(pending_bridge)())()
        pending_bridge = M.EmptyList
        if line.strip().lower() == "bridge no":
            _pop_ask("bridge")
            return "Recorded; the word stays unlinked." + _ask_next_line()
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
        # A new grounding can unblock other definitions: a body whose
        # genus is this word could not compile before, and can now --
        # and so could a body that merely MENTIONS the word among its
        # open dependencies. Re-compile every installed definition
        # whose genus resolves through this bridge or whose open words
        # include the bridged word.
        unblocked_text = "0"
        unblocked_scan = G.InstalledDefinitions(learned_version)()
        while M.IdentityCompare(
            unblocked_scan, M.EmptyList,
        )() is M.false_value:
            other_definition = M.Head(unblocked_scan)()
            if M.IdentityCompare(
                G.DefinitionTerm(other_definition)(), word,
            )() is M.truth_value:
                unblocked_scan = M.Tail(unblocked_scan)()
            else:
                other_reading = G.DefinitionBodyReading(
                    other_definition, vocabulary, registry,
                )()
                if M.IdentityCompare(
                    other_reading, M.EmptyList,
                )() is M.truth_value:
                    unblocked_scan = M.Tail(unblocked_scan)()
                else:
                    other_term = M.Head(M.Tail(other_reading)())()
                    other_genus_slot = M.Head(M.Tail(other_term)())()
                    other_genus = G.ReadingWordConstructor(
                        learned_version, other_genus_slot,
                    )()
                    word_in_body = M.false_value
                    other_body = M.Head(
                        M.Tail(
                            G.DefinitionBody(other_definition)(),
                        )(),
                    )()
                    body_word_scan = other_body
                    body_singular = G.WordSingular(word)()
                    while M.IdentityCompare(
                        body_word_scan, M.EmptyList,
                    )() is M.false_value:
                        body_word = M.Head(body_word_scan)()
                        if M.Compare(body_word, word)() is M.truth_value:
                            word_in_body = M.truth_value
                            body_word_scan = M.EmptyList
                        else:
                            if M.IdentityCompare(
                                body_singular, M.EmptyList,
                            )() is M.false_value:
                                if M.Compare(
                                    body_word, body_singular,
                                )() is M.truth_value:
                                    word_in_body = M.truth_value
                                    body_word_scan = M.EmptyList
                            if M.IdentityCompare(
                                body_word_scan, M.EmptyList,
                            )() is M.false_value:
                                body_word_scan = M.Tail(body_word_scan)()
                    if M.IdentityCompare(
                        M.OrAtom(
                            M.IdentityCompare(
                                other_genus, constructor,
                            )(),
                            word_in_body,
                        )(),
                        M.truth_value,
                    )() is M.truth_value:
                        other_result = G.InstallDefinitionLaws(
                            learned_version,
                            other_definition,
                            vocabulary,
                            registry,
                        )()
                        learned_version = M.Head(other_result)()
                        other_count = M.Head(M.Tail(other_result)())()
                        other_text = M.GMPRepText(
                            M.NatRepOf(other_count, registry)(),
                        )()
                        if G.GMPEqualText(other_text, "0")() is M.false_value:
                            unblocked_text = G.GMPAddText(
                                unblocked_text, other_text,
                            )()
                    unblocked_scan = M.Tail(unblocked_scan)()
        if G.GMPEqualText(unblocked_text, "0")() is M.false_value:
            _extend_vocabulary()
            law_line = (
                law_line + " Grounding '" + str(word()) + "' unblocked"
                + " definitions worth " + unblocked_text
                + " more law(s)."
            )
        _persist_talk_state()
        # The reply states where the constructor came from as a fact
        # of the index: a pack constructor is one the pack-concept
        # index knows; any other was minted from the taught term
        # itself. And the ontology promise is made only when rules
        # actually speak for the constructor.
        pack_known = M.false_value
        pack_scan = pack_concepts
        while M.IdentityCompare(
            pack_scan, M.EmptyList,
        )() is M.false_value:
            if M.Compare(
                M.Head(M.Tail(M.Head(pack_scan)())())(), constructor,
            )() is M.truth_value:
                pack_known = M.truth_value
                pack_scan = M.EmptyList
            else:
                pack_scan = M.Tail(pack_scan)()
        if M.IdentityCompare(pack_known, M.truth_value)() is M.truth_value:
            source_line = " now names the pack constructor."
        else:
            taught_known = M.false_value
            taught_scan = G.InstalledTaughtRules(learned_version)()
            while M.IdentityCompare(
                taught_scan, M.EmptyList,
            )() is M.false_value:
                taught_rule = M.Head(taught_scan)()
                taught_replacement = P.RuleReplacement(taught_rule)()
                if M.IsPair(taught_replacement)() is M.truth_value:
                    if M.Compare(
                        M.Head(taught_replacement)(), constructor,
                    )() is M.truth_value:
                        taught_known = M.truth_value
                        taught_scan = M.EmptyList
                    else:
                        taught_scan = M.Tail(taught_scan)()
                else:
                    taught_scan = M.Tail(taught_scan)()
            if M.IdentityCompare(
                taught_known, M.truth_value,
            )() is M.truth_value:
                source_line = (
                    " now names the taught predicate '"
                    + str(constructor()) + "'."
                )
            else:
                source_line = " now names a constructor of its own."
        ontology_line = ""
        if proof_runtime is not M.EmptyList:
            ontology_facts = G.OntologyFactsFor(
                M.FromContextGetAllRules(proof_runtime.graph)(),
                constructor,
                registry,
            )()
            if M.IdentityCompare(
                ontology_facts, M.EmptyList,
            )() is M.false_value:
                ontology_line = (
                    " 'what is " + str(word()) + "' can answer from"
                    + " the ontology."
                )
        _pop_ask("bridge")
        return (
            "Linked: '" + str(word()) + "'" + source_line
            + ontology_line + law_line + _ask_next_line()
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
        # accepted shapes: 'what is a triangle', 'what is triangle',
        # and phrase terms: 'what is a sieve of eratosthenes' -- a
        # definition whose term is a phrase joins it with underscores,
        # so the question joins the same way to find it.
        term_word = G.SoleWord(
            G.WordChainWithout(_words(line), WHAT_IS_WORDS)(),
        )()
        if M.IdentityCompare(term_word, M.EmptyList)() is M.truth_value:
            subject_words = G.WordChainWithout(_words(line), WHAT_IS_WORDS)()
            while M.IdentityCompare(
                subject_words, M.EmptyList,
            )() is M.false_value:
                if G.SurfaceChainHasWord(
                    ARTICLE_WORDS, M.Head(subject_words)(),
                )() is M.truth_value:
                    subject_words = M.Tail(subject_words)()
                else:
                    subject_words = M.EmptyList
            joined_text = ""
            join_scan = G.WordChainWithout(_words(line), WHAT_IS_WORDS)()
            while M.IdentityCompare(
                join_scan, M.EmptyList,
            )() is M.false_value:
                if G.SurfaceChainHasWord(
                    ARTICLE_WORDS, M.Head(join_scan)(),
                )() is M.truth_value:
                    if joined_text == "":
                        join_scan = M.Tail(join_scan)()
                        continue
                    break
                if joined_text != "":
                    joined_text = joined_text + "_"
                joined_text = joined_text + str(M.Head(join_scan)()())
                join_scan = M.Tail(join_scan)()
            if joined_text == "":
                return None
            phrase_term = M.Char(joined_text)
            if M.IdentityCompare(
                G.DefinitionFor(learned_version, phrase_term)(),
                M.EmptyList,
            )() is M.truth_value:
                return None
            term_word = phrase_term
        term_text = term_word()
        bridge = G.BridgeFor(learned_version, term_word)()
        ontology_line = ""
        if M.IdentityCompare(bridge, M.EmptyList)() is M.false_value:
            # Whether the constructor is a pack constructor is a fact
            # of the index, read once for both branches below: the
            # ontology is pack machinery and is only spoken of a
            # constructor the packs actually know.
            bridge_constructor = G.BridgeConstructor(bridge)()
            bridge_pack_known = M.false_value
            bridge_pack_scan = pack_concepts
            while M.IdentityCompare(
                bridge_pack_scan, M.EmptyList,
            )() is M.false_value:
                if M.Compare(
                    M.Head(
                        M.Tail(M.Head(bridge_pack_scan)())(),
                    )(),
                    bridge_constructor,
                )() is M.truth_value:
                    bridge_pack_known = M.truth_value
                    bridge_pack_scan = M.EmptyList
                else:
                    bridge_pack_scan = M.Tail(bridge_pack_scan)()
            if proof_runtime is not M.EmptyList:
                if M.IdentityCompare(
                    bridge_pack_known, M.truth_value,
                )() is M.truth_value:
                    facts = G.OntologyFactsFor(
                        M.FromContextGetAllRules(proof_runtime.graph)(),
                        bridge_constructor,
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
                if M.IdentityCompare(
                    bridge_pack_known, M.truth_value,
                )() is M.truth_value:
                    ontology_line = (
                        " (linked to the pack constructor; ask again"
                        + " after a proof has run to hear its ontology)"
                    )
        definition = G.DefinitionFor(learned_version, M.Char(term_text))()
        if M.IdentityCompare(definition, M.EmptyList)() is M.truth_value:
            # 'what is primes' after 'a prime is ...' -- the plural asks
            # for the singular's definition.
            singular_term = G.WordSingular(M.Char(term_text))()
            if M.IdentityCompare(
                singular_term, M.EmptyList,
            )() is M.false_value:
                definition = G.DefinitionFor(
                    learned_version, singular_term,
                )()
        if M.IdentityCompare(definition, M.EmptyList)() is M.truth_value:
            if G.DefinitionNodeWordKnown(
                learned_version, M.Char(term_text),
            )() is M.truth_value:
                return (
                    "a " + term_text.replace("_", " ")
                    + " has a parsed definition in the graph; its reading"
                    + " came through the definition grammar."
                )
            if ontology_line:
                return (
                    "I have no taught definition of '" + term_text + "'."
                    + ontology_line
                )
            return "I have no definition of '" + term_text + "'."
        body = G.DefinitionBody(definition)()
        answer = (
            "a " + term_text.replace("_", " ") + " is "
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

    def _store_origins_text(store):
        """One debug text naming each store entry by origin and rule."""
        texts = []
        entries = G.ProposalStoreEntries(store)()
        while M.IdentityCompare(entries, M.EmptyList)() is M.false_value:
            entry = M.Head(entries)()
            proposal = G.ProposalEntryProposal(entry)()
            origin = G.ProposalOrigin(proposal)()
            kind_text = "machine"
            if M.IsPair(origin)() is M.truth_value:
                origin_head = M.Head(origin)()
                if M.Compare(
                    origin_head, M.Char("dialogue-rule"),
                )() is M.truth_value:
                    sources = P.PrettyRule(
                        P.MultiRule(
                            M.Head(M.Tail(origin)())(),
                            M.Head(M.Tail(M.Tail(origin)())())(),
                        )(),
                        registry,
                    )()
                    kind_text = "dialogue " + sources
                elif M.Compare(
                    origin_head, M.Char("machine-correspondence"),
                )() is M.truth_value:
                    kind_text = "correspondence"
            texts.append(kind_text)
            entries = M.Tail(entries)()
        return "; ".join(texts)

    def _advance_unknown_word():
        """Retire the asked word; ask the next, or stop the asking."""
        nonlocal pending_unknown_words, pending_unknown_word
        _pop_ask("word")
        if M.IdentityCompare(
            pending_unknown_words, M.EmptyList,
        )() is M.false_value:
            pending_unknown_word = M.Head(pending_unknown_words)()
            pending_unknown_words = M.Tail(pending_unknown_words)()
            _push_ask(
                "word",
                "What does '"
                + str(pending_unknown_word())
                + "' mean?",
            )
        else:
            pending_unknown_word = M.EmptyList

    def _chain_count_text(chain):
        """Count a chain by the machine's own text arithmetic.

        Not M.Count: the count is spoken, never carried as a Succ
        chain, so the cached text counter is the right tool -- the
        same one the daemon's cycles are counted with.
        """
        count_text = "0"
        chain_scan = chain
        while M.IdentityCompare(
            chain_scan, M.EmptyList,
        )() is M.false_value:
            count_text = G.GMPSuccText(count_text)()
            chain_scan = M.Tail(chain_scan)()
        return count_text

    def _words_of_count_text(count_text):
        """A count spoken digit-wise, the machine's way past nine."""
        digit_words = []
        for digit_char in count_text:
            digit_word = _numeral_word_of_value(digit_char)
            if digit_word is M.EmptyList:
                return count_text
            digit_words.append(str(digit_word()))
        return " ".join(digit_words)

    def _numeral_word_of_value(value_text):
        """The spoken word of a value, from the word entries."""
        word_entries = M.Head(M.Tail(vocabulary)())()
        entry_scan = word_entries
        while M.IdentityCompare(
            entry_scan, M.EmptyList,
        )() is M.false_value:
            entry = M.Head(entry_scan)()
            entry_text = M.GMPRepText(
                M.NatRepOf(
                    M.Head(M.Tail(entry)())(), registry,
                )(),
            )()
            if M.IdentityCompare(
                G.GMPEqualText(entry_text, value_text)(),
                M.truth_value,
            )() is M.truth_value:
                return M.Head(entry)()
            entry_scan = M.Tail(entry_scan)()
        return M.EmptyList

    def _problem_state():
        """The taught problem's parts: numbers, move pairs, step."""
        holds = []
        neighbors = []
        step_text = M.EmptyList
        fact_scan = G.InstalledTaughtFacts(learned_version)()
        while M.IdentityCompare(
            fact_scan, M.EmptyList,
        )() is M.false_value:
            fact = M.Head(fact_scan)()
            if M.IsPair(fact)() is M.truth_value:
                fact_head = M.Head(fact)()
                fact_args = M.Tail(fact)()
                if M.Compare(
                    fact_head, M.Char("holds"),
                )() is M.truth_value:
                    if M.IdentityCompare(
                        M.Tail(M.Tail(fact_args)())(),
                        M.EmptyList,
                    )() is M.truth_value:
                        sector = M.Head(fact_args)()
                        value = M.Head(M.Tail(fact_args)())()
                        value_text = _numeral_value_text(value)
                        if value_text is not M.EmptyList:
                            if M.IsPair(sector)() is M.false_value:
                                holds.append((sector, value_text))
                elif M.Compare(
                    fact_head, M.Char("neighbor"),
                )() is M.truth_value:
                    if M.IdentityCompare(
                        M.Tail(M.Tail(fact_args)())(),
                        M.EmptyList,
                    )() is M.truth_value:
                        neighbors.append(
                            (
                                M.Head(fact_args)(),
                                M.Head(M.Tail(fact_args)())(),
                            ),
                        )
                elif M.Compare(
                    fact_head, M.Char("step"),
                )() is M.truth_value:
                    if M.IdentityCompare(
                        M.Tail(fact_args)(), M.EmptyList,
                    )() is M.truth_value:
                        step_text = _numeral_value_text(
                            M.Head(fact_args)(),
                        )
            fact_scan = M.Tail(fact_scan)()
        ordered = True
        for sector, _value_text in holds:
            if _numeral_value_text(sector) is M.EmptyList:
                ordered = False
        if ordered and holds:
            holds = sorted(
                holds,
                key=lambda entry: int(
                    _numeral_value_text(entry[0]),
                ),
            )
        return holds, neighbors, step_text

    def _missing_problem_parts():
        """The question for the first part the graph still lacks."""
        nonlocal pending_problem_kind
        holds, neighbors, step_text = _problem_state()
        if not holds:
            pending_problem_kind = "board"
            return (
                "Which numbers are written into the sectors, in order?"
                + " Answer with the numbers alone, like:"
                + " one, zero, one."
            )
        if not neighbors:
            pending_problem_kind = "neighbors"
            return (
                "Which pairs of sectors may one move touch? Answer"
                + " like: one and two, two and three."
            )
        if step_text is M.EmptyList:
            pending_problem_kind = "step"
            return (
                "How much does one move add to each of its two"
                + " numbers? Answer with the number alone, like: one."
            )
        pending_problem_kind = ""
        return ""

    def _speak_arithmetic(term):
        """An add/sub chain over sectors, spoken as words."""
        if M.IsPair(term)() is M.truth_value:
            term_head = M.Head(term)()
            term_args = M.Tail(term)()
            if M.IdentityCompare(
                M.Tail(M.Tail(term_args)())(),
                M.EmptyList,
            )() is M.truth_value:
                left = M.Head(term_args)()
                right = M.Head(M.Tail(term_args)())()
                if M.Compare(
                    term_head, M.Char("add"),
                )() is M.truth_value:
                    return (
                        _speak_arithmetic(left)
                        + " plus "
                        + _speak_arithmetic(right)
                    )
                if M.Compare(
                    term_head, M.Char("sub"),
                )() is M.truth_value:
                    return (
                        _speak_arithmetic(left)
                        + " minus "
                        + _speak_arithmetic(right)
                    )
        if term is M.EmptyList:
            return ""
        try:
            return str(term())
        except Exception:
            return "?"

    def _run_invariant_sweep():
        """Run the sweep and speak what it returns, as terms."""
        nonlocal learned_version
        holds, neighbors, step_text = _problem_state()
        holds_chain = M.EmptyList
        for sector, value_text in reversed(holds):
            holds_chain = M.Pair(
                M.Pair(sector, M.Pair(M.Char(value_text), M.EmptyList)),
                holds_chain,
            )
        neighbors_chain = M.EmptyList
        for sector_a, sector_b in reversed(neighbors):
            neighbors_chain = M.Pair(
                M.Pair(
                    sector_a, M.Pair(sector_b, M.EmptyList),
                ),
                neighbors_chain,
            )
        outcome = G.SuggestInvariants(
            holds_chain,
            neighbors_chain,
            M.Char(step_text),
        )()
        findings = M.Head(outcome)()
        states_chain = M.Head(M.Tail(outcome)())()
        tested_chain = M.Head(M.Tail(M.Tail(outcome)())())()
        # The sweep is recorded whole before anything is spoken: the
        # states it walked, the expressions it tested, the findings.
        # The counts in the reply are counted from these recorded
        # chains by the machine's own counting, so every number the
        # reply speaks is a number the graph can be asked for.
        states_count_text = _chain_count_text(states_chain)
        tested_count_text = _chain_count_text(tested_chain)
        findings_scan = findings
        while M.IdentityCompare(
            findings_scan, M.EmptyList,
        )() is M.false_value:
            finding = M.Head(findings_scan)()
            findings_scan = M.Tail(findings_scan)()
            node = M.Pair(
                M.Char("suggested-invariant"),
                M.Pair(finding, M.EmptyList),
            )
            learned_version = G.GraphVersion(
                M.Pair(node, G.GraphNodes(learned_version)()),
                G.GraphEdges(learned_version)(),
                G.GraphVersionInvariants(learned_version)(),
            )()
        sweep_node = M.Pair(
            M.Char("invariant-sweep"),
            M.Pair(
                states_chain,
                M.Pair(
                    tested_chain,
                    M.Pair(findings, M.EmptyList),
                ),
            ),
        )
        learned_version = G.GraphVersion(
            M.Pair(sweep_node, G.GraphNodes(learned_version)()),
            G.GraphEdges(learned_version)(),
            G.GraphVersionInvariants(learned_version)(),
        )()
        _persist_talk_state()
        reply_lines = [
            "The sweep is recorded in the graph. It holds "
            + _words_of_count_text(
                states_count_text,
            )
            + " states, each within two moves and each a chain of"
            + " sector and value, and "
            + _words_of_count_text(
                tested_count_text,
            )
            + " expressions, each number added, subtracted, or left"
            + " out -- counted from the record, not claimed.",
        ]
        if M.IdentityCompare(
            findings, M.EmptyList,
        )() is M.truth_value:
            reply_lines.append("Nothing stayed unchanged.")
        findings_scan = findings
        while M.IdentityCompare(
            findings_scan, M.EmptyList,
        )() is M.false_value:
            finding = M.Head(findings_scan)()
            findings_scan = M.Tail(findings_scan)()
            expression = M.Head(finding)()
            constant_rep = M.Head(M.Tail(finding)())()
            opposite = M.Head(M.Tail(M.Tail(finding)())())()
            finding_text = (
                _speak_arithmetic(expression)
                + " stays "
                + _words_of_value_text(
                    M.GMPRepText(constant_rep)(),
                )
            )
            if M.IdentityCompare(
                opposite, M.truth_value,
            )() is M.truth_value:
                cancellation = _words_of_value_text(
                    G.GMPSubText(step_text, step_text)(),
                )
                finding_text = finding_text + (
                    ". Every move adds "
                    + _words_of_value_text(step_text)
                    + " to two neighboring numbers, and in it each"
                    + " neighboring pair carries opposite signs: "
                    + _words_of_value_text(step_text)
                    + " minus "
                    + _words_of_value_text(step_text)
                    + " is "
                    + cancellation
                    + ", so a move changes nothing"
                )
            reply_lines.append(finding_text + ".")
        return "\n".join(reply_lines)

    def _try_problem_answer(line, record=True):
        """A bare line answers the standing problem question."""
        nonlocal learned_version, pending_problem_kind
        if pending_problem_kind == "":
            return None
        if ":" in line:
            return None
        words = G.WordsOfText(
            line.lower(), reading_policy, reading_digits,
        )()
        word_atoms = []
        word_texts = []
        word_scan = words
        while M.IdentityCompare(
            word_scan, M.EmptyList,
        )() is M.false_value:
            word_atom = M.Head(word_scan)()
            word_scan = M.Tail(word_scan)()
            if M.Compare(
                word_atom, M.Char(","),
            )() is M.truth_value:
                continue
            word_atoms.append(word_atom)
            word_texts.append(str(word_atom()))

        def _numeral_or_none(text):
            value_text = _numeral_value_text(M.Char(text))
            if value_text is M.EmptyList:
                return None
            return value_text

        if pending_problem_kind == "board":
            values = []
            for word_text in word_texts:
                value_text = _numeral_or_none(word_text)
                if value_text is None:
                    return None
                values.append(value_text)
            if len(values) < 2:
                return None
            recorded = []
            for position, value_text in enumerate(values):
                sector = _numeral_word_of_value(str(position + 1))
                if sector is M.EmptyList:
                    return None
                value_word = _numeral_word_of_value(value_text)
                if value_word is M.EmptyList:
                    return None
                fact = M.Pair(
                    M.Char("holds"),
                    M.Pair(sector, M.Pair(value_word, M.EmptyList)),
                )
                installed = G.InstallTaughtFact(
                    learned_version, fact,
                )()
                learned_version = M.Head(installed)()
                recorded.append(
                    "sector "
                    + str(sector())
                    + " holds "
                    + str(value_word()),
                )
            if record:
                _log_lesson(line)
            _persist_talk_state()
            _pop_ask("problem")
            next_missing = _missing_problem_parts()
            if next_missing != "":
                _push_ask("problem", next_missing)
                return (
                    "Recorded: "
                    + "; ".join(recorded)
                    + "."
                    + _ask_next_line()
                )
            return (
                "Recorded: "
                + "; ".join(recorded)
                + ".\n"
                + _run_invariant_sweep()
            )
        if pending_problem_kind == "neighbors":
            pairs = []
            index = 0
            while index < len(word_texts):
                first = _numeral_or_none(word_texts[index])
                if first is None:
                    return None
                if index + 2 >= len(word_texts):
                    return None
                if word_texts[index + 1] != "and":
                    return None
                second = _numeral_or_none(word_texts[index + 2])
                if second is None:
                    return None
                pairs.append(
                    (word_atoms[index], word_atoms[index + 2]),
                )
                index = index + 3
            if not pairs:
                return None
            for sector_a, sector_b in pairs:
                fact = M.Pair(
                    M.Char("neighbor"),
                    M.Pair(
                        sector_a,
                        M.Pair(sector_b, M.EmptyList),
                    ),
                )
                installed = G.InstallTaughtFact(
                    learned_version, fact,
                )()
                learned_version = M.Head(installed)()
            if record:
                _log_lesson(line)
            _persist_talk_state()
            _pop_ask("problem")
            recorded_text = "; ".join(
                str(sector_a()) + " and " + str(sector_b())
                for sector_a, sector_b in pairs
            )
            next_missing = _missing_problem_parts()
            if next_missing != "":
                _push_ask("problem", next_missing)
                return (
                    "Recorded the pairs a move may touch: "
                    + recorded_text
                    + "."
                    + _ask_next_line()
                )
            return (
                "Recorded the pairs a move may touch: "
                + recorded_text
                + ".\n"
                + _run_invariant_sweep()
            )
        if pending_problem_kind == "step":
            if len(word_texts) != 1:
                return None
            value_text = _numeral_or_none(word_texts[0])
            if value_text is None:
                return None
            value_word = _numeral_word_of_value(value_text)
            if value_word is M.EmptyList:
                return None
            fact = M.Pair(
                M.Char("step"),
                M.Pair(value_word, M.EmptyList),
            )
            installed = G.InstallTaughtFact(
                learned_version, fact,
            )()
            learned_version = M.Head(installed)()
            if record:
                _log_lesson(line)
            _persist_talk_state()
            _pop_ask("problem")
            return (
                "Recorded: one move adds "
                + str(value_word())
                + " to each of its two numbers.\n"
                + _run_invariant_sweep()
            )
        return None


    def _unblock_definition_for(decided_proposal):
        """An approved split or shape unblocks the definition it came
        from: its operators or its template now stand interpreted, so
        the definition compiles and its words enter the vocabulary.

        Installs the ExactlyOne structure a split's generic activation
        does not carry, re-compiles the definition named in the origin,
        and returns the report line (empty when nothing compiled).
        """
        nonlocal learned_version
        rule_origin = G.ProposalOrigin(decided_proposal)()
        if M.IdentityCompare(rule_origin, M.EmptyList)() is M.truth_value:
            return ""
        if M.IsPair(rule_origin)() is not M.truth_value:
            return ""
        unblock_term = M.EmptyList
        if M.Compare(
            M.Head(rule_origin)(), M.Char("case-split"),
        )() is M.truth_value:
            learned_version = G.InstallCaseSplit(
                learned_version,
                G.ProposalLaw(decided_proposal)(),
            )()
            if M.IdentityCompare(
                M.Tail(M.Tail(rule_origin)())(), M.EmptyList,
            )() is M.false_value:
                unblock_term = M.Head(
                    M.Tail(M.Tail(rule_origin)())(),
                )()
                # The approved split interprets the operators: rewrite
                # the reading with the flat Only/No markers lifted out
                # of the chain -- they live on as the reading's
                # conditions and the installed split -- so the
                # compilation gate sees a body it may compile.
                split_reading = G.DefinitionReadingFor(
                    learned_version, unblock_term,
                )()
                if M.IdentityCompare(
                    split_reading, M.EmptyList,
                )() is M.false_value:
                    split_binder = M.Head(
                        M.Tail(M.Tail(split_reading)())(),
                    )()
                    split_chain = M.Head(
                        M.Tail(
                            M.Tail(M.Tail(split_reading)())(),
                        )(),
                    )()
                    split_conditions = M.Head(
                        M.Tail(
                            M.Tail(
                                M.Tail(M.Tail(split_reading)())(),
                            )(),
                        )(),
                    )()
                    kept_reversed = M.EmptyList
                    chain_scan = split_chain
                    while M.IdentityCompare(
                        chain_scan, M.EmptyList,
                    )() is M.false_value:
                        chain_item = M.Head(chain_scan)()
                        item_is_operator = M.false_value
                        if M.IsPair(chain_item)() is M.truth_value:
                            if M.OrAtom(
                                M.Compare(
                                    M.Head(chain_item)(),
                                    Lmod.OnlyLabel,
                                )(),
                                M.Compare(
                                    M.Head(chain_item)(),
                                    Lmod.NoLabel,
                                )(),
                            )() is M.truth_value:
                                item_is_operator = M.truth_value
                        if M.IdentityCompare(
                            item_is_operator, M.false_value,
                        )() is M.truth_value:
                            kept_reversed = M.Pair(
                                chain_item, kept_reversed,
                            )
                        chain_scan = M.Tail(chain_scan)()
                    rewritten_reading = G.DefinitionReading(
                        unblock_term,
                        split_binder,
                        M.Reverse(kept_reversed)(),
                        split_conditions,
                    )()
                    learned_version = G.GraphVersion(
                        M.Pair(
                            rewritten_reading,
                            G.GraphNodes(learned_version)(),
                        ),
                        G.GraphEdges(learned_version)(),
                        G.GraphVersionInvariants(learned_version)(),
                    )()
        elif M.Compare(
            M.Head(rule_origin)(), M.Char("definition-shape"),
        )() is M.truth_value:
            unblock_term = M.Head(M.Tail(rule_origin)())()
            # The shape law goes in here as well: the daemon activates
            # it in the shared state on its cycle, but the
            # conversation's own version needs it now for the compile
            # to read the body. The merge dedups the double install.
            learned_version = G.InstallLaw(
                learned_version,
                G.ProposalLaw(decided_proposal)(),
            )()
            _extend_vocabulary()
        if M.IdentityCompare(
            unblock_term, M.EmptyList,
        )() is M.truth_value:
            return ""
        unblock_definition = G.DefinitionFor(
            learned_version, unblock_term,
        )()
        if M.IdentityCompare(
            unblock_definition, M.EmptyList,
        )() is M.truth_value:
            return ""
        unblock_result = G.InstallDefinitionLaws(
            learned_version,
            unblock_definition,
            vocabulary,
            registry,
        )()
        learned_version = M.Head(unblock_result)()
        unblock_count = M.Head(M.Tail(unblock_result)())()
        unblock_text = M.GMPRepText(
            M.NatRepOf(unblock_count, registry)(),
        )()
        if G.GMPEqualText(unblock_text, "0")() is M.truth_value:
            # A zero compile with the operators interpreted leaves the
            # body unreadable: its shape is the remaining gap, and it
            # is queued so the approval's reply surfaces it next.
            _reraise_shape_gap(unblock_term, unblock_definition)
            return ""
        _extend_vocabulary()
        return (
            " The definition compiled to " + unblock_text
            + " law(s); the prover now rewrites with them."
        )

    def _handle_decision(line, record=True):
        # Every decision answers at most one question: the inner flow
        # decides the proposal, the wrapper retires the ask it answered
        # and surfaces the next question on the table.
        outcome = _decide_inner(line, record=record)
        _pop_ask("rule")
        return outcome + _ask_next_line()

    def _handle_machine_decision(line, record=True):
        """Decide a correspondence the daemon found in the background.

        The proposal is machine-made but the decision is the human's,
        and the activation is the daemon's: yes attaches the approval
        and submits through the inbox, and the next daemon cycle unifies
        the rules or names the subgraph itself. No leaves the graph as
        it is, recorded as declined.
        """
        nonlocal proposal_store, pending_machine
        if M.IdentityCompare(pending_machine, M.EmptyList)() is M.truth_value:
            return "There is no correspondence awaiting a decision."
        decided = pending_machine
        pending_machine = M.EmptyList
        if record:
            _log_lesson(line)
            _debug("decision '" + line + "' appended to " + lesson_path)
        payload = G.ProposalLaw(decided)()
        if line == "yes":
            approval = G.Approved(decided, M.Char("trainer"))()
            proposal_store = G.ProposalStoreAttach(
                proposal_store, decided, approval,
            )()
            _persist_talk_state()
            _pop_ask("machine")
            if G.IsRuleUnification(payload)() is M.truth_value:
                return (
                    "Recorded and submitted. The daemon will unify them"
                    + " on its next cycle." + _ask_next_line()
                )
            if G.IsSubgraphReformulation(payload)() is M.truth_value:
                return (
                    "Recorded and submitted. The daemon will reformulate"
                    + " it on its next cycle." + _ask_next_line()
                )
            return (
                "Recorded and submitted. The daemon will activate it on"
                + " its next cycle." + _ask_next_line()
            )
        rejection = G.Rejected(
            decided,
            M.Char("trainer"),
            M.Char("declined"),
        )()
        proposal_store = G.ProposalStoreAttach(
            proposal_store, decided, rejection,
        )()
        _persist_talk_state()
        _pop_ask("machine")
        return (
            "Recorded the rejection. The graph stays as it was."
            + _ask_next_line()
        )

    def _decide_inner(line, record=True):
        nonlocal proposal_store, learned_version, decided_laws, pending_queue, pending_rule
        nonlocal pending_gaps
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
                approved_payload = G.ProposalLaw(decided_proposal)()
                if G.IsInventedLemma(approved_payload)() is M.truth_value:
                    learned_version = G.GraphVersion(
                        M.Pair(
                            approved_payload,
                            G.GraphNodes(learned_version)(),
                        ),
                        G.GraphEdges(learned_version)(),
                        G.GraphVersionInvariants(learned_version)(),
                    )()
                    invented_proposition = G.InventedLemmaProposition(
                        approved_payload,
                    )()
                    if M.IsPair(invented_proposition)() is M.truth_value:
                        if M.IdentityCompare(
                            M.Head(invented_proposition)(), M.ExprEqLabel,
                        )() is M.truth_value:
                            invented_left = M.Head(
                                M.Tail(invented_proposition)(),
                            )()
                            invented_right = M.Head(
                                M.Tail(M.Tail(invented_proposition)())(),
                            )()
                            learned_version = G.InstallTaughtRuleSource(
                                learned_version,
                                M.Pair(invented_left, M.EmptyList),
                                invented_right,
                            )()
                    _persist_talk_state()
                    approved_certificate = G.InventedLemmaCertificate(
                        approved_payload,
                    )()
                    if M.IsPair(approved_certificate)() is M.truth_value:
                        if M.Compare(
                            M.Head(approved_certificate)(),
                            M.Char("well-ordering-descent-certificate"),
                        )() is M.truth_value:
                            return "Recorded the invented minimal-counterexample descent with nested parity dependencies."
                        if M.Compare(
                            M.Head(approved_certificate)(),
                            M.Char("mod-three-well-ordering-descent-certificate"),
                        )() is M.truth_value:
                            return "Recorded the invented mod-3 descent with nested residue dependencies."
                        if M.Compare(
                            M.Head(approved_certificate)(),
                            M.Char("bounded-modulus-descent-certificate"),
                        )() is M.truth_value:
                            return "Recorded the modulus-parameterized descent with nested residue dependencies."
                        if M.Compare(
                            M.Head(approved_certificate)(), M.Char("invention-evidence"),
                        )() is M.truth_value:
                            approved_structural = M.Head(M.Tail(approved_certificate)())()
                            if M.IsPair(approved_structural)() is M.truth_value:
                                if M.Compare(
                                    M.Head(approved_structural)(),
                                    M.Char("parity-case-split"),
                                )() is M.truth_value:
                                    return "Recorded the parity lemma with both case branches in its replay certificate."
                                if M.Compare(
                                    M.Head(approved_structural)(),
                                    M.Char("mod-three-case-split"),
                                )() is M.truth_value:
                                    return "Recorded the mod-3 lemma with all three residue branches in its replay certificate."
                                if M.Compare(
                                    M.Head(approved_structural)(),
                                    M.Char("bounded-residue-case-split"),
                                )() is M.truth_value:
                                    return "Recorded the modulus-parameterized lemma with every residue branch in its replay certificate."
                                if M.Compare(
                                    M.Head(approved_structural)(),
                                    M.Char("euclidean-descent-trace"),
                                )() is M.truth_value:
                                    return "Recorded the Euclidean algorithm lemma with its witnessed remainder-descent trace."
                        dependency_tail = M.Tail(
                            M.Tail(M.Tail(M.Tail(approved_certificate)())())(),
                        )()
                        if M.IdentityCompare(
                            dependency_tail, M.EmptyList,
                        )() is M.false_value:
                            return "Recorded the invented cubic lemma with its verified rewrite and nested SOS dependency."
                    return "Recorded the invented lemma and its verified rewrite rule."
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
                    proposal_payload = G.ProposalLaw(decided_proposal)()
                    if G.IsTaughtDerivationSchema(
                        proposal_payload,
                    )() is M.truth_value:
                        learned_version = G.GraphVersion(
                            M.Pair(
                                proposal_payload,
                                G.GraphNodes(learned_version)(),
                            ),
                            G.GraphEdges(learned_version)(),
                            G.GraphVersionInvariants(learned_version)(),
                        )()
                    else:
                        rule_origin = G.ProposalOrigin(decided_proposal)()
                        if M.IsPair(rule_origin)() is M.truth_value:
                            if M.Compare(
                                M.Head(rule_origin)(), M.Char("case-split"),
                            )() is M.false_value:
                                if M.IsPair(
                                    M.Tail(M.Tail(rule_origin)())(),
                                )() is M.truth_value:
                                    source_premises = M.Head(
                                        M.Tail(rule_origin)(),
                                    )()
                                    source_replacement = M.Head(
                                        M.Tail(M.Tail(rule_origin)())(),
                                    )()
                                    learned_version = G.InstallTaughtRuleSource(
                                        learned_version,
                                        source_premises,
                                        source_replacement,
                                    )()
                    compiled_line = _unblock_definition_for(decided_proposal)
                    _persist_talk_state()
                    return (
                        "Recorded and submitted. The daemon will activate it "
                        "on its next cycle." + compiled_line
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
                # An approved split or shape unblocks the definition it
                # came from; its operators or template now stand
                # interpreted and the definition can be compiled.
                compiled_line = _unblock_definition_for(decided_proposal)
                if compiled_line != "":
                    _persist_talk_state()
                    return (
                        "Recorded and activated. The deduction is now"
                        + " installed in the graph." + compiled_line
                    )
                taught_rule_terms = M.EmptyList
                rule_origin = G.ProposalOrigin(decided_proposal)()
                if M.IsPair(rule_origin)() is M.truth_value:
                    # A rule origin carries premises and a replacement;
                    # a case-split origin carries its exactly-one and
                    # the term it interprets, and neither is a rule
                    # source.
                    if M.Compare(
                        M.Head(rule_origin)(), M.Char("case-split"),
                    )() is M.false_value:
                        if M.IsPair(
                            M.Tail(M.Tail(rule_origin)())(),
                        )() is M.truth_value:
                            taught_rule_terms = M.Pair(
                                M.Head(M.Tail(rule_origin)())(),
                                M.Pair(
                                    M.Head(
                                        M.Tail(M.Tail(rule_origin)())(),
                                    )(),
                                    M.EmptyList,
                                ),
                            )
                inspection = G.InspectGaps(
                    pending_gaps,
                    last_goal,
                    learned_version,
                    taught_rule_terms,
                )()
                learned_version = M.Head(inspection)()
                pending_gaps = M.Head(M.Tail(inspection)())()
                gap_ask = M.Head(
                    M.Tail(M.Tail(M.Tail(inspection)())())(),
                )()
                if M.IdentityCompare(gap_ask, M.EmptyList)() is M.false_value:
                    learned_version = G.InstallAskedQuestion(
                        learned_version,
                        G.AskedQuestion(
                            M.Head(M.Tail(gap_ask)())(),
                            M.Head(gap_ask)(),
                            M.Head(M.Tail(M.Tail(gap_ask)())())(),
                        )(),
                    )()
                    _persist_talk_state()
                    return (
                        "Recorded and activated. "
                        + _speak_chain(
                            M.Head(M.Tail(M.Head(gap_ask)())())(),
                        )
                    )
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
                compiled_line = _unblock_definition_for(decided_proposal)
                _persist_talk_state()
                _debug("submitted to the daemon inbox; it will activate")
                return ("Recorded and submitted. The daemon will activate it "
                        "on its next cycle." + compiled_line)
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
            outcome = (
                "Recorded and activated. The rule is now part of my grammar."
                + _unblock_definition_for(decided_proposal)
            )
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
        nonlocal pending_rule, learned_version, proposal_store, talk_ledger
        nonlocal pending_gaps
        nonlocal pending_process
        nonlocal pending_unknown_words, pending_unknown_word
        nonlocal scoped_assumptions, scoped_divisibility_assumptions
        nonlocal scoped_congruence_assumptions
        nonlocal scoped_integer_equations, last_parity_stall, last_residue_stall
        nonlocal last_modular_stall, last_euclidean_stall
        lowered = line.lower()
        if StoryTalk.StoryCommandRecognized(line)() is M.truth_value:
            return StoryTalk.StoryTalkResponse(line)()
        if lowered.strip() == "clear assumptions":
            scoped_assumptions = M.EmptyList
            scoped_divisibility_assumptions = M.EmptyList
            scoped_congruence_assumptions = M.EmptyList
            scoped_integer_equations = M.EmptyList
            return "Cleared the session-scoped assumptions."
        if lowered.startswith("assume:"):
            assumption_text = line[7:].strip()
            folded_assumption = assumption_text.lower()
            if folded_assumption.startswith("congruentmod(") and folded_assumption.endswith(")"):
                body_text = assumption_text[13:-1]
                first_comma = body_text.find(",")
                second_comma = body_text.find(",", first_comma + 1)
                third_comma = body_text.find(",", second_comma + 1)
                if first_comma == -1 or second_comma == -1 or third_comma == -1:
                    return "I could not parse that witnessed congruence fact."
                modulus = G.ParsePolynomialExpressionText(
                    body_text[:first_comma].strip(), reading_digits,
                )()
                left = G.ParsePolynomialExpressionText(
                    body_text[first_comma + 1:second_comma].strip(), reading_digits,
                )()
                right = G.ParsePolynomialExpressionText(
                    body_text[second_comma + 1:third_comma].strip(), reading_digits,
                )()
                witness = G.ParsePolynomialExpressionText(
                    body_text[third_comma + 1:].strip(), reading_digits,
                )()
                congruence = Res.WitnessedCongruence(
                    modulus, left, right, witness,
                )()
                if Res.VerifyWitnessedCongruence(
                    congruence, M.EmptyList, registry,
                )() is M.false_value:
                    return "Rejected the fabricated congruence witness: a-b-m*w did not normalize to zero."
                scoped_congruence_assumptions = M.Pair(
                    congruence, scoped_congruence_assumptions,
                )
                return "Scoped witnessed congruence; a-b-m*w normalized to zero."
            if folded_assumption.startswith("divides(") and folded_assumption.endswith(")"):
                body_text = assumption_text[8:-1]
                first_comma = body_text.find(",")
                second_comma = body_text.find(",", first_comma + 1)
                if first_comma == -1 or second_comma == -1:
                    return "I could not parse that witnessed divisibility fact."
                divisor = G.ParsePolynomialExpressionText(
                    body_text[:first_comma].strip(), reading_digits,
                )()
                dividend = G.ParsePolynomialExpressionText(
                    body_text[first_comma + 1:second_comma].strip(), reading_digits,
                )()
                witness = G.ParsePolynomialExpressionText(
                    body_text[second_comma + 1:].strip(), reading_digits,
                )()
                fact = Par.WitnessedDivides(divisor, dividend, witness)()
                verified = Par.VerifyWitnessedDivisibility(
                    fact, M.EmptyList, registry,
                )()
                if verified is M.false_value:
                    return "Rejected the fabricated divisibility witness: n-d*w did not normalize to zero."
                record = Par.DivisibilityAssumption(
                    fact, M.EmptyList, M.Char("normalized-zero"),
                )()
                scoped_divisibility_assumptions = M.Pair(
                    record, scoped_divisibility_assumptions,
                )
                return "Scoped witnessed divisibility fact; n-d*w normalized to zero."
            if folded_assumption.startswith("even(") and folded_assumption.endswith(")"):
                expression = G.ParsePolynomialExpressionText(
                    assumption_text[5:-1], reading_digits,
                )()
                if M.IdentityCompare(expression, M.EmptyList)() is M.truth_value:
                    return "I could not parse that witnessed parity assumption."
                verified_assumption = Par.MakeEvenAssumption(expression, registry)()
                if M.IdentityCompare(
                    verified_assumption, M.EmptyList,
                )() is M.truth_value:
                    return "Rejected the parity assumption because its witness did not normalize."
                scoped_divisibility_assumptions = M.Pair(
                    verified_assumption, scoped_divisibility_assumptions,
                )
                fact = Par.DivisibilityAssumptionFact(verified_assumption)()
                return (
                    "Scoped witnessed assumption: "
                    + M.PrettyTerm(fact, registry)()
                    + "; witness identity normalized to zero."
                )
            equation = G.ParsePolynomialEquationText(
                assumption_text, reading_digits,
            )()
            if M.IdentityCompare(equation, M.EmptyList)() is M.false_value:
                scoped_integer_equations = M.Pair(
                    equation, scoped_integer_equations,
                )
                return (
                    "Scoped integer equation: "
                    + M.PrettyTerm(equation, registry)()
                    + "."
                )
            assumption = G.ParsePolynomialInequalityText(
                assumption_text, reading_digits,
            )()
            if M.IdentityCompare(assumption, M.EmptyList)() is M.truth_value:
                return "I could not parse that scoped assumption."
            scoped_assumptions = M.Pair(assumption, scoped_assumptions)
            return (
                "Scoped assumption: "
                + M.PrettyTerm(assumption, registry)()
                + "."
            )
        # A bare line at the prompt answers the problem question that
        # stands: the numbers, the pairs a move touches, or the step.
        problem_answer = _try_problem_answer(line, record=record)
        if problem_answer is not None:
            return problem_answer
        # A bare line is the meaning of the word the standing
        # question asks about; it is recorded through the word
        # teaching path, as if the trainer had typed it there.
        if M.IdentityCompare(
            pending_unknown_word, M.EmptyList,
        )() is M.false_value:
            is_command = (
                lowered.startswith("suggest ")
                or lowered.startswith("bridge ")
                or lowered.startswith("why not ")
                or lowered.startswith("explain ")
                or lowered.startswith("prove that")
                or lowered.startswith("solve ")
                or lowered.startswith("keep ")
                or lowered.startswith("show ")
                or lowered.startswith("what is ")
                or lowered.startswith("what are the ")
                or lowered.startswith("how many ")
                or lowered.startswith("why are these two definitions equivalent")
                or lowered == "goodbye"
                or lowered == "help"
            )
            if ":" not in line and lowered not in ("yes", "no") and not is_command:
                if lowered == "skip all":
                    _pop_ask("word")
                    pending_unknown_words = M.EmptyList
                    pending_unknown_word = M.EmptyList
                    if record:
                        _log_lesson(line)
                    return (
                        "Stopped asking for word meanings."
                        + _ask_next_line()
                    )
                if lowered == "skip":
                    skipped_word = str(pending_unknown_word())
                    _advance_unknown_word()
                    if record:
                        _log_lesson(line)
                    if M.IdentityCompare(
                        pending_unknown_word, M.EmptyList,
                    )() is M.truth_value:
                        return (
                            "Passed '"
                            + skipped_word
                            + "'. No more words to ask about."
                            + _ask_next_line()
                        )
                    return (
                        "Passed '"
                        + skipped_word
                        + "'."
                        + _ask_next_line()
                    )
                word_line = (
                    "word: "
                    + str(pending_unknown_word())
                    + " means "
                    + line.strip()
                )
                word_reply = _respond(word_line, record=record)
                _advance_unknown_word()
                if M.IdentityCompare(
                    pending_unknown_word, M.EmptyList,
                )() is M.truth_value:
                    return (
                        word_reply
                        + " No more words to ask about."
                    )
                return word_reply + _ask_next_line()
        if lowered.startswith("word:"):
            parsed_word = G.ParseWordText(
                line[5:].strip(),
                reading_policy,
                reading_digits,
            )()
            word_facts = M.Head(parsed_word)()
            taught_terms = word_facts
            word_reason = M.Head(M.Tail(parsed_word)())()
            if M.IdentityCompare(word_facts, M.EmptyList)() is M.truth_value:
                detail = M.EmptyList
                if M.IsPair(word_reason)() is M.truth_value:
                    detail = M.Head(M.Tail(word_reason)())()
                if M.IdentityCompare(detail, M.EmptyList)() is M.false_value:
                    return "I could not parse that word lesson (" + str(detail()) + ")."
                return "I could not parse that word lesson."
            while M.IdentityCompare(word_facts, M.EmptyList)() is M.false_value:
                installed_word_fact = G.InstallTaughtFact(
                    learned_version,
                    M.Head(word_facts)(),
                )()
                learned_version = M.Head(installed_word_fact)()
                word_facts = M.Tail(word_facts)()
            if record:
                _log_lesson(line)
            inspection = G.InspectGaps(
                pending_gaps,
                last_goal,
                learned_version,
                taught_terms,
            )()
            learned_version = M.Head(inspection)()
            pending_gaps = M.Head(M.Tail(inspection)())()
            gap_ask = M.Head(
                M.Tail(M.Tail(M.Tail(inspection)())())(),
            )()
            if M.IdentityCompare(gap_ask, M.EmptyList)() is M.false_value:
                learned_version = G.InstallAskedQuestion(
                    learned_version,
                    G.AskedQuestion(
                        M.Head(M.Tail(gap_ask)())(),
                        M.Head(gap_ask)(),
                        M.Head(M.Tail(M.Tail(gap_ask)())())(),
                    )(),
                )()
                _persist_talk_state()
                return _speak_chain(
                    M.Head(M.Tail(M.Head(gap_ask)())())(),
                )
            _persist_talk_state()
            acknowledged = G.RenderAcknowledgement(
                M.Head(M.Tail(M.Head(M.Head(parsed_word)())())())(),
            )()
            if M.IdentityCompare(acknowledged, M.EmptyList)() is M.false_value:
                return _speak_chain(
                    M.Head(M.Tail(acknowledged)())(),
                )
            return "Recorded word grounding: " + line[5:].strip()
        if lowered.startswith("training problem:"):
            # The problem enters as its own words, one utterance. The
            # machine reads it with its reading policy, keeps it as a
            # term in the graph, and says what it could and could not
            # read: the words it knows, the numbers it speaks, and the
            # words still without meaning, to be grounded by teaching.
            problem_text = line[len("training problem:"):].strip()
            problem_words = G.WordsOfText(
                problem_text,
                reading_policy,
                reading_digits,
            )()
            word_entries = M.Head(M.Tail(vocabulary)())()
            problem_known = []
            problem_unknown = []
            problem_numbers = []
            current_run = []
            word_scan = problem_words
            while M.IdentityCompare(
                word_scan, M.EmptyList,
            )() is M.false_value:
                problem_word = M.Head(word_scan)()
                word_scan = M.Tail(word_scan)()
                if M.Compare(
                    problem_word, M.Char(","),
                )() is M.truth_value:
                    continue
                resolved = G.CorrespondenceResolveWord(
                    word_entries,
                    G.Surface(M.Pair(problem_word, M.EmptyList))(),
                )()
                if M.IdentityCompare(
                    resolved, M.EmptyList,
                )() is M.false_value:
                    problem_known.append(problem_word)
                    if M.IsNat(resolved, registry)() is M.truth_value:
                        current_run.append(problem_word)
                    else:
                        if len(current_run) > 1:
                            problem_numbers.append(list(current_run))
                        current_run = []
                else:
                    if len(current_run) > 1:
                        problem_numbers.append(list(current_run))
                    current_run = []
                    known_unknown = False
                    for seen_word in problem_unknown:
                        if M.Compare(
                            seen_word, problem_word,
                        )() is M.truth_value:
                            known_unknown = True
                    if not known_unknown:
                        problem_unknown.append(problem_word)
            if len(current_run) > 1:
                problem_numbers.append(list(current_run))
            problem_node = M.Pair(
                M.Char("training-problem"),
                M.Pair(problem_words, M.EmptyList),
            )
            learned_version = G.GraphVersion(
                M.Pair(problem_node, G.GraphNodes(learned_version)()),
                G.GraphEdges(learned_version)(),
                G.GraphVersionInvariants(learned_version)(),
            )()
            if record:
                _log_lesson(line)
            _persist_talk_state()
            known_texts = [
                str(word()) for word in problem_known
            ]
            number_texts = [
                ", ".join(str(word()) for word in run)
                for run in problem_numbers
            ]
            unknown_texts = [
                str(word()) for word in problem_unknown
            ]
            reply_text = (
                "Recorded the problem, "
                + str(len(problem_known) + len(problem_unknown))
                + " words."
            )
            if number_texts:
                reply_text = reply_text + (
                    " The numbers it speaks: "
                    + "; and ".join(number_texts)
                    + "."
                )
            if unknown_texts:
                reply_text = reply_text + (
                    " These words I do not know: "
                    + ", ".join(unknown_texts)
                    + ". I will ask for each meaning in turn; say"
                    + " skip to pass one, skip all to stop."
                )
                unknown_chain = M.EmptyList
                for unknown_word in reversed(problem_unknown):
                    unknown_chain = M.Pair(unknown_word, unknown_chain)
                pending_unknown_words = unknown_chain
                if M.IdentityCompare(
                    pending_unknown_words, M.EmptyList,
                )() is M.false_value:
                    pending_unknown_word = M.Head(
                        pending_unknown_words,
                    )()
                    pending_unknown_words = M.Tail(
                        pending_unknown_words,
                    )()
                    _push_ask(
                        "word",
                        "What does '"
                        + str(pending_unknown_word())
                        + "' mean?",
                    )
            elif known_texts:
                reply_text = reply_text + (
                    " Every word in it is known to me."
                )
            return reply_text + _ask_next_line()
        if lowered.startswith("suggest invariants"):
            # The machine explores its own reach and returns what
            # never changes, as terms: the sweep itself runs in the
            # graph layer over the taught board, moves, and step, and
            # each finding is an add/sub chain over the sectors beside
            # its constant value. The reply is those terms, spoken.
            parts_missing = _missing_problem_parts()
            if parts_missing != "":
                _push_ask("problem", parts_missing)
                return (
                    "The problem is not fully held yet."
                    + _ask_next_line()
                )
            return _run_invariant_sweep()
        if lowered.strip() == "show lemmas":
            rendered = G.InventedLemmaDisplayText(
                G.GraphNodes(learned_version)(), M.one, registry,
            )()
            if M.Compare(rendered, M.Char(""))() is M.truth_value:
                return "No invented lemmas are recorded."
            return str(rendered())
        if lowered.startswith("suggest lemmas"):
            if M.IdentityCompare(pending_rule, M.EmptyList)() is M.false_value:
                return "Please approve or reject the pending proposal first."
            if M.IdentityCompare(last_euclidean_stall, M.EmptyList)() is M.false_value:
                first_text = M.Head(last_euclidean_stall)()()
                second_text = M.Head(M.Tail(last_euclidean_stall)())()()
                euclidean_invented = Euc.EuclideanAlgorithmLemma(
                    first_text, second_text, registry,
                )()
                if M.IdentityCompare(euclidean_invented, M.EmptyList)() is M.truth_value:
                    return "Euclidean invention refused: remainder descent did not verify."
                euclidean_proposal = G.Proposal(
                    euclidean_invented, M.Char("euclidean-descent-invention"),
                )()
                proposal_store = G.ProposalStoreSubmit(
                    proposal_store, euclidean_proposal,
                )()
                pending_rule = euclidean_proposal
                last_euclidean_stall = M.EmptyList
                _push_ask("rule", "Approve the Euclidean descent lemma? (yes/no)")
                _persist_talk_state()
                return (
                    "Generated a remainder-witnessed Euclidean trace: every transition "
                    "proves a=b*q+r, 0<=r<b, common-divisor invariance, and strict descent.\n"
                    "Approve this candidate? Enter yes or no."
                )
            if M.IdentityCompare(last_modular_stall, M.EmptyList)() is M.false_value:
                modular_kind = M.Head(last_modular_stall)()
                modular_invented = M.EmptyList
                modular_response = ""
                if M.Compare(
                    modular_kind, M.Char("bounded-residue-case-stall"),
                )() is M.truth_value:
                    modulus = M.Head(M.Tail(last_modular_stall)())()
                    variable = M.Head(M.Tail(M.Tail(last_modular_stall)())())()
                    modular_invented = Mod.BoundedResidueCaseLemma(
                        modulus, variable, registry,
                    )()
                    if M.IdentityCompare(modular_invented, M.EmptyList)() is M.truth_value:
                        return "Residue invention refused: at least one nonzero branch has square remainder zero."
                    modular_response = (
                        "Generated every residue branch for modulus "
                        + Mod.IntegerText(modulus)() + "; each nonzero branch has a "
                        "normalization-verified nonzero square remainder."
                    )
                elif M.Compare(
                    modular_kind, M.Char("bounded-modulus-descent-stall"),
                )() is M.truth_value:
                    modulus = M.Head(M.Tail(last_modular_stall)())()
                    equation = M.Head(M.Tail(M.Tail(last_modular_stall)())())()
                    positivity = M.Head(
                        M.Tail(M.Tail(M.Tail(last_modular_stall)())())(),
                    )()
                    case_lemma = Mod.FindBoundedResidueLemma(
                        G.GraphNodes(learned_version)(), modulus, registry,
                    )()
                    coupled_lemma = Mod.FindCoupledBoundedResidueLemma(
                        G.GraphNodes(learned_version)(), modulus, registry,
                    )()
                    descent_map = Mod.GenBoundedModulusDescentMap(
                        modulus, equation, coupled_lemma, case_lemma,
                        positivity, registry,
                    )()
                    if M.IdentityCompare(case_lemma, M.EmptyList)() is M.truth_value:
                        return "Cannot invent bounded-modulus descent: residue dependency missing."
                    if M.IdentityCompare(coupled_lemma, M.EmptyList)() is M.truth_value:
                        return "Cannot invent bounded-modulus descent: coupled dependency missing."
                    if M.IdentityCompare(descent_map, M.EmptyList)() is M.truth_value:
                        return "Bounded-modulus descent refused: reproduction or strict decrease failed."
                    modular_invented = Mod.BoundedModulusDescentLemma(
                        modulus, equation, descent_map, coupled_lemma, case_lemma,
                    )()
                    modular_response = (
                        "Discovered a modulus-parameterized descent map from the stored "
                        "witnesses and verified reproduction, positivity, and both strict decreases."
                    )
                if M.IdentityCompare(modular_invented, M.EmptyList)() is M.false_value:
                    modular_proposal = G.Proposal(
                        modular_invented, M.Char("bounded-modulus-invention"),
                    )()
                    proposal_store = G.ProposalStoreSubmit(
                        proposal_store, modular_proposal,
                    )()
                    pending_rule = modular_proposal
                    last_modular_stall = M.EmptyList
                    _push_ask("rule", "Approve the bounded-modulus lemma? (yes/no)")
                    _persist_talk_state()
                    return modular_response + "\nApprove this candidate? Enter yes or no."
            if M.IdentityCompare(last_residue_stall, M.EmptyList)() is M.false_value:
                residue_kind = M.Head(last_residue_stall)()
                residue_invented = M.EmptyList
                residue_response = ""
                if M.Compare(
                    residue_kind, M.Char("mod-three-case-stall"),
                )() is M.truth_value:
                    variable = M.Head(M.Tail(last_residue_stall)())()
                    residue_invented = Res.ModThreeCaseLemma(variable, registry)()
                    residue_response = (
                        "Invented exhaustive mod-3 split with explicit residue branches "
                        "0, 1, and 2. The nonzero branches normalize their squares to "
                        "3*q+1 and close by contradiction."
                    )
                elif M.Compare(
                    residue_kind, M.Char("mod-three-descent-stall"),
                )() is M.truth_value:
                    equation = M.Head(M.Tail(last_residue_stall)())()
                    positivity = M.Head(M.Tail(M.Tail(last_residue_stall)())())()
                    case_lemma = Res.FindModThreeLemma(
                        G.GraphNodes(learned_version)(),
                    )()
                    coupled_lemma = Res.FindCoupledModThreeLemma(
                        G.GraphNodes(learned_version)(),
                    )()
                    descent_map = Res.GenModThreeDescentMap(
                        equation, coupled_lemma, case_lemma,
                        positivity, registry,
                    )()
                    if M.IdentityCompare(case_lemma, M.EmptyList)() is M.truth_value:
                        return "Cannot invent mod-3 descent: the residue-case lemma is missing."
                    if M.IdentityCompare(coupled_lemma, M.EmptyList)() is M.truth_value:
                        return "Cannot invent mod-3 descent: the coupled residue lemma is missing."
                    if M.IdentityCompare(descent_map, M.EmptyList)() is M.truth_value:
                        return "Mod-3 descent refused: reproduction or strict decrease was not verified."
                    residue_invented = Res.ModThreeDescentLemma(
                        equation, descent_map, coupled_lemma, case_lemma,
                    )()
                    residue_response = (
                        "Discovered mod-3 descent map (x,y)->(y,u) from x=3*u; "
                        "normalization reproduced y^2=3*u^2 and the positive-square "
                        "comparison rule proved both strict decreases."
                    )
                if M.IdentityCompare(residue_invented, M.EmptyList)() is M.false_value:
                    residue_proposal = G.Proposal(
                        residue_invented, M.Char("residue-domain-invention"),
                    )()
                    proposal_store = G.ProposalStoreSubmit(
                        proposal_store, residue_proposal,
                    )()
                    pending_rule = residue_proposal
                    last_residue_stall = M.EmptyList
                    _push_ask("rule", "Approve the invented residue lemma? (yes/no)")
                    _persist_talk_state()
                    return residue_response + "\nApprove this candidate? Enter yes or no."
            if M.IdentityCompare(last_parity_stall, M.EmptyList)() is M.false_value:
                stall_kind = M.Head(last_parity_stall)()
                invented = M.EmptyList
                response = ""
                if M.Compare(
                    stall_kind, M.Char("parity-case-split-stall"),
                )() is M.truth_value:
                    variable = M.Head(M.Tail(last_parity_stall)())()
                    invented = Par.ParityCaseSplitLemma(variable, registry)()
                    response = (
                        "Invented parity case split with two explicit branches:\n"
                        "  1. " + M.PrettyTerm(variable, registry)()
                        + " := 2*k [even branch closed]\n"
                        "  2. " + M.PrettyTerm(variable, registry)()
                        + " := 2*k+1 [odd-square contradiction closed]\n"
                        "Both branches were independently normalized."
                    )
                elif M.Compare(
                    stall_kind, M.Char("descent-stall"),
                )() is M.truth_value:
                    equation = M.Head(M.Tail(last_parity_stall)())()
                    positivity = M.Head(M.Tail(M.Tail(last_parity_stall)())())()
                    parity_lemma = Par.FindParityLemma(
                        G.GraphNodes(learned_version)(),
                    )()
                    coupled_lemma = Par.FindCoupledParityLemma(
                        G.GraphNodes(learned_version)(),
                    )()
                    descent_map = Par.GenDescentMap(
                        equation,
                        coupled_lemma,
                        parity_lemma,
                        positivity,
                        registry,
                    )()
                    if M.IdentityCompare(
                        parity_lemma, M.EmptyList,
                    )() is M.truth_value:
                        return "Cannot invent descent: the saved parity case-split lemma is missing."
                    if M.IdentityCompare(
                        coupled_lemma, M.EmptyList,
                    )() is M.truth_value:
                        return "Cannot invent descent: the coupled-parity lemma is missing."
                    if M.IdentityCompare(
                        descent_map, M.EmptyList,
                    )() is M.truth_value:
                        return "Descent refused: positivity, reproduction, or strict decrease was not verified."
                    invented = Par.DescentLemma(
                        equation, descent_map, coupled_lemma, parity_lemma,
                    )()
                    response = (
                        "Discovered descent map from the witnessed parity substitution:\n"
                        "  (x,y) -> (y,u)\n"
                        "Reproduced the equation by normalization and discharged "
                        "0<u, u<y, and y<x with the positive-square comparison rule."
                    )
                if M.IdentityCompare(invented, M.EmptyList)() is M.false_value:
                    invented_proposal = G.Proposal(
                        invented, M.Char("integer-domain-invention"),
                    )()
                    proposal_store = G.ProposalStoreSubmit(
                        proposal_store, invented_proposal,
                    )()
                    pending_rule = invented_proposal
                    last_parity_stall = M.EmptyList
                    _push_ask("rule", "Approve the invented integer lemma? (yes/no)")
                    _persist_talk_state()
                    return response + "\nApprove this candidate? Enter yes or no."
            if M.IdentityCompare(pending_rule, M.EmptyList)() is M.false_value:
                return "Please approve or reject the pending proposal first."
            stall = G.InstalledStallRecord(learned_version)()
            if M.IdentityCompare(stall, M.EmptyList)() is M.truth_value:
                return "No stalled search to analyze. Run a 'query:' command first."
            candidates = Min.InventFromStall(stall, registry)()
            if M.IdentityCompare(candidates, M.EmptyList)() is M.truth_value:
                return "The bounded invention biases found no useful candidate."
            candidate = M.Head(candidates)()
            proposition = M.Head(candidate)()
            provenance = M.Head(M.Tail(candidate)())()
            status = M.Head(M.Tail(M.Tail(candidate)())())()
            structural_certificate = M.Head(
                M.Tail(M.Tail(M.Tail(candidate)())())(),
            )()
            trial = M.Head(
                M.Tail(M.Tail(M.Tail(M.Tail(candidate)())())())(),
            )()
            validation = M.Head(
                M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(candidate)())())())())(),
            )()
            if M.Compare(
                Min.CandidateValidationStatus(validation)(),
                M.Char("refuted"),
            )() is M.truth_value:
                return "The generated candidate was independently refuted and discarded."
            certificate = M.Pair(
                M.Char("invention-evidence"),
                M.Pair(
                    structural_certificate,
                    M.Pair(trial, M.Pair(validation, M.EmptyList)),
                ),
            )
            obligations_text = ""
            nested_dependency = M.EmptyList
            if M.IsPair(structural_certificate)() is M.truth_value:
                if M.Compare(
                    M.Head(structural_certificate)(),
                    M.Char("bounded-additive-sos"),
                )() is M.truth_value:
                    sos_identity = M.Head(
                        M.Tail(M.Tail(structural_certificate)())(),
                    )()
                    obligations_text = (
                        "\nPositivity obligations:"
                        + Min.SquareObligationDisplayText(
                            Min.AdditiveSOSSummands(sos_identity)(), registry,
                        )()
                    )
                elif M.Compare(
                    M.Head(structural_certificate)(),
                    M.Char("bounded-perfect-square"),
                )() is M.truth_value:
                    square = M.Head(
                        M.Tail(M.Tail(M.Tail(structural_certificate)())())(),
                    )()
                    obligations_text = (
                        "\nPositivity obligations:"
                        + Min.SquareObligationDisplayText(
                            M.Pair(square, M.EmptyList), registry,
                        )()
                    )
                elif M.Compare(
                    M.Head(structural_certificate)(),
                    M.Char("bounded-linear-factor-vanishing"),
                )() is M.truth_value:
                    cubic_variables = M.Head(M.Tail(structural_certificate)())()
                    if Min.VariablesHaveNonnegativeAssumptions(
                        cubic_variables, scoped_assumptions,
                    )() is M.false_value:
                        return "A cubic identity was verified, but its linear factor is not nonnegative under the scoped assumptions."
                    discovery = M.Head(
                        M.Tail(M.Tail(structural_certificate)())(),
                    )()
                    quotient = M.Head(M.Tail(M.Tail(discovery)())())()
                    quotient_expression = Min.CanonicalPolynomialExpression(quotient)()
                    quotient_obligation = M.Pair(
                        M.ExprLeLabel,
                        M.Pair(
                            M.Pair(M.ExprIntLabel, M.Pair(M.Zero, M.EmptyList)),
                            M.Pair(quotient_expression, M.EmptyList),
                        ),
                    )
                    dependency = Min.FindSOSDependency(
                        G.GraphNodes(learned_version)(), quotient_obligation, registry,
                    )()
                    if M.IdentityCompare(dependency, M.EmptyList)() is M.truth_value:
                        return "A cubic identity was verified, but its invented SOS dependency is missing."
                    nested_dependency = M.Head(M.Tail(dependency)())()
                    factor = M.Head(M.Tail(discovery)())()
                    obligations_text = (
                        "\nFactor obligations:"
                        "\n  1. 0 <= "
                        + M.PrettyTerm(Min.CanonicalPolynomialExpression(factor)(), registry)()
                        + " [scoped assumptions + additive nonnegative]"
                        "\n  2. 0 <= " + M.PrettyTerm(quotient_expression, registry)()
                        + " [nested invented SOS lemma]"
                    )
            if M.IdentityCompare(nested_dependency, M.EmptyList)() is M.false_value:
                certificate = M.Pair(
                    M.Char("invention-evidence"),
                    M.Pair(
                        structural_certificate,
                        M.Pair(
                            trial,
                            M.Pair(
                                validation,
                                M.Pair(nested_dependency, M.EmptyList),
                            ),
                        ),
                    ),
                )
            invented = G.InventedLemma(
                proposition,
                G.StallRecordGoal(stall)(),
                M.EmptyList,
                status,
                M.Zero,
                certificate,
            )()
            invented_proposal = G.Proposal(
                invented, M.Char("stall-invention"),
            )()
            proposal_store = G.ProposalStoreSubmit(
                proposal_store, invented_proposal,
            )()
            pending_rule = invented_proposal
            _push_ask("rule", "Approve the invented lemma? (yes/no)")
            _persist_talk_state()
            return (
                "Analyzing stall on: "
                + M.PrettyTerm(G.StallRecordGoal(stall)(), registry)()
                + "\n1. " + M.PrettyTerm(proposition, registry)()
                + " [Source: " + str(provenance())
                + " | Status: " + str(status()) + "]"
                + obligations_text
                + "\nApprove this candidate? Enter yes or no."
            )
        if lowered.startswith("suggest premises"):
            if M.IdentityCompare(pending_rule, M.EmptyList)() is M.false_value:
                return "Please approve or reject the pending rule first."
            if M.IdentityCompare(last_goal, M.EmptyList)() is M.truth_value:
                return "No recent search has stalled; ask a question or run a query first."
            rules = G.InstalledTaughtRules(learned_version)()
            facts = G.InstalledTaughtFacts(learned_version)()
            cand_rule = G.SuggestMissingPremise(last_goal, rules, facts, registry)()
            if M.IdentityCompare(cand_rule, M.EmptyList)() is M.truth_value:
                return "I could not derive a sound candidate lemma for the stalled goal."
            witness = G.ResidualWitness(
                last_goal,
                P.RulePremises(cand_rule)(),
                P.RuleReplacement(cand_rule)(),
            )()
            learned_version = G.InstallResidualWitness(
                learned_version,
                witness,
            )()
            generalized_rule = G.GeneralizeResidualWitness(
                learned_version,
                witness,
                registry,
            )()
            generalized = M.false_value
            if M.IdentityCompare(generalized_rule, M.EmptyList)() is M.false_value:
                cand_rule = generalized_rule
                generalized = M.truth_value
            cand_payload = M.EmptyList
            if M.IdentityCompare(
                P.RulePremises(cand_rule)(), M.EmptyList,
            )() is M.truth_value:
                schema_start = M.Pair(
                    M.VarTag,
                    M.Pair(M.Char("?schema-start"), M.EmptyList),
                )
                schema_goal = P.RuleReplacement(cand_rule)()
                cand_payload = G.TaughtDerivationSchema(
                    schema_start,
                    schema_goal,
                    G.SchemaValidationEvidence(schema_goal)(),
                )()
            else:
                cand_payload = G.CompileDeductionToLaw(cand_rule)()
            if M.IdentityCompare(cand_payload, M.EmptyList)() is M.truth_value:
                _persist_talk_state()
                return "I could not compile a candidate lemma for the stalled goal."
            origin_label = M.Char("dialogue-rule")
            if M.IdentityCompare(generalized, M.truth_value)() is M.truth_value:
                origin_label = M.Char("residual-generalization")
            cand_origin = M.Pair(
                origin_label,
                M.Pair(
                    P.RulePremises(cand_rule)(),
                    M.Pair(
                        P.RuleReplacement(cand_rule)(),
                        M.EmptyList,
                    ),
                ),
            )
            cand_proposal = G.Proposal(cand_payload, cand_origin)()
            proposal_store = G.ProposalStoreSubmit(proposal_store, cand_proposal)()
            pending_rule = cand_proposal
            _persist_talk_state()
            return (
                "From the stalled goal "
                + M.PrettyTerm(last_goal, registry)()
                + ", I propose candidate lemma: "
                + P.PrettyRule(cand_rule, M.AllConstructors)()
                + ". Approve? (yes/no)"
            )
        if lowered.startswith("explain "):
            # The derivation itself, spoken: the claim is re-derived
            # from the taught facts under the taught rules, and the
            # steps that reach it are narrated -- which rule applied,
            # from what, to what. Nothing new is concluded; the
            # recorded teaching is only said out loud.
            explain_text = line[8:].strip()
            known_constructors = G.RuleConstructors(
                learned_version,
                pack_concepts,
            )()
            parsed_explain = G.ParseRuleText(
                explain_text,
                reading_policy,
                reading_digits,
                known_constructors,
                M.truth_value,
            )()
            explain_goal = M.Head(parsed_explain)()
            if M.IdentityCompare(
                explain_goal, M.EmptyList,
            )() is M.truth_value:
                return (
                    "I could not read that as a claim. Use"
                    + " 'explain Predicate(constant)?'"
                )
            explain_rules = G.InstalledTaughtRules(learned_version)()
            # The machine's own arithmetic joins the start knowledge:
            # every ground equation or divisibility the rules' premises
            # speak is computed here, exactly as the query path does,
            # so the narrative rests on the machine's numbers.
            explain_facts = G.InstalledTaughtFacts(learned_version)()
            explain_compute_reversed = M.EmptyList
            explain_rule_scan = explain_rules
            while M.IdentityCompare(
                explain_rule_scan, M.EmptyList,
            )() is M.false_value:
                explain_premise_scan = P.RulePremises(
                    M.Head(explain_rule_scan)(),
                )()
                while M.IdentityCompare(
                    explain_premise_scan, M.EmptyList,
                )() is M.false_value:
                    explain_compute_reversed = M.Pair(
                        M.Head(explain_premise_scan)(),
                        explain_compute_reversed,
                    )
                    explain_premise_scan = M.Tail(
                        explain_premise_scan,
                    )()
                explain_rule_scan = M.Tail(explain_rule_scan)()
            explain_compute_scan = M.Reverse(
                explain_compute_reversed,
            )()
            while M.IdentityCompare(
                explain_compute_scan, M.EmptyList,
            )() is M.false_value:
                explain_term = M.Head(explain_compute_scan)()
                explain_target = explain_term
                if M.IsPair(explain_term)() is M.truth_value:
                    if M.Compare(
                        M.Head(explain_term)(), M.Char("not"),
                    )() is M.truth_value:
                        if M.IdentityCompare(
                            M.Tail(explain_term)(), M.EmptyList,
                        )() is M.false_value:
                            explain_target = M.Head(
                                M.Tail(explain_term)(),
                            )()
                explain_division = _computed_divisibility(
                    explain_target,
                )
                explain_equation = _verify_ground_equation(
                    explain_target,
                )
                explain_verdicts = M.Pair(
                    explain_division,
                    M.Pair(explain_equation, M.EmptyList),
                )
                explain_verdict_scan = explain_verdicts
                while M.IdentityCompare(
                    explain_verdict_scan, M.EmptyList,
                )() is M.false_value:
                    explain_verdict = M.Head(explain_verdict_scan)()
                    if M.IdentityCompare(
                        explain_verdict, M.EmptyList,
                    )() is M.false_value:
                        if M.Compare(
                            M.Head(explain_verdict)(),
                            M.Char("holds"),
                        )() is M.truth_value:
                            explain_facts = M.Pair(
                                explain_target,
                                explain_facts,
                            )
                        else:
                            explain_facts = M.Pair(
                                M.Pair(
                                    M.Char("not"),
                                    M.Pair(
                                        explain_target,
                                        M.EmptyList,
                                    ),
                                ),
                                explain_facts,
                            )
                    explain_verdict_scan = M.Tail(
                        explain_verdict_scan,
                    )()
                explain_compute_scan = M.Tail(explain_compute_scan)()
            # The narrative walks the teaching backward: the claim,
            # the rule that concludes it, each premise -- a fact the
            # trainer stated, a sum the machine computed, or another
            # concluded claim, followed in turn. A rule is used only
            # when every one of its premises resolves; a premise left
            # with variables is grounded against the recorded facts.
            # Nothing is searched beyond the teaching and nothing new
            # is derived; the recorded argument is spoken from its own
            # steps.
            def _explain_has_var(term, depth):
                if depth > 12:
                    return False
                if P.IsVarPattern(term)() is M.truth_value:
                    return True
                if M.IsPair(term)() is not M.truth_value:
                    return False
                if _explain_has_var(M.Head(term)(), depth + 1):
                    return True
                return _explain_has_var(M.Tail(term)(), depth + 1)

            def _explain_ground_from_facts(
                pattern, bindings, fact_chain, rule_chain,
            ):
                # A premise still holding variables is grounded first
                # against the recorded facts, then against the rules'
                # own conclusions: a derived premise names the rule
                # that concludes it, and the narrative follows.
                fact_scan = fact_chain
                while M.IdentityCompare(
                    fact_scan, M.EmptyList,
                )() is M.false_value:
                    candidate = M.Head(fact_scan)()
                    grounded = G.TermMatchBindings(
                        pattern,
                        candidate,
                        bindings,
                    )()
                    if M.IdentityCompare(
                        M.Head(grounded)(), M.truth_value,
                    )() is M.truth_value:
                        return M.Pair(
                            candidate,
                            M.Pair(M.Tail(grounded)(), M.EmptyList),
                        )
                    fact_scan = M.Tail(fact_scan)()
                rule_scan = rule_chain
                while M.IdentityCompare(
                    rule_scan, M.EmptyList,
                )() is M.false_value:
                    candidate_rule = M.Head(rule_scan)()
                    candidate = P.RuleReplacement(candidate_rule)()
                    grounded = G.TermMatchBindings(
                        pattern,
                        candidate,
                        bindings,
                    )()
                    if M.IdentityCompare(
                        M.Head(grounded)(), M.truth_value,
                    )() is M.truth_value:
                        instantiated = M.Head(
                            M.Instantiate(
                                candidate,
                                M.Tail(grounded)(),
                            )(),
                        )()
                        if _explain_has_var(instantiated, 0) is False:
                            return M.Pair(
                                instantiated,
                                M.Pair(
                                    M.Tail(grounded)(),
                                    M.EmptyList,
                                ),
                            )
                    rule_scan = M.Tail(rule_scan)()
                return M.EmptyList

            def _explain_resolve(target, depth, rule_chain, fact_chain):
                if depth > 12:
                    return M.EmptyList
                if M.IdentityCompare(
                    target, M.EmptyList,
                )() is M.truth_value:
                    return M.EmptyList
                target_text = M.PrettyTerm(target, registry)()
                is_computed_equation = M.false_value
                computed_line = ""
                if M.IsPair(target)() is M.truth_value:
                    if M.Compare(
                        M.Head(target)(), M.Char("same"),
                    )() is M.truth_value:
                        verdict = _verify_ground_equation(target)
                        if M.IdentityCompare(
                            verdict, M.EmptyList,
                        )() is M.false_value:
                            is_computed_equation = M.truth_value
                            if M.Compare(
                                M.Head(verdict)(),
                                M.Char("holds"),
                            )() is M.truth_value:
                                computed_line = (
                                    "the machine computed the left"
                                    + " side; it is the right side"
                                )
                    if M.Compare(
                        M.Head(target)(), M.Char("not"),
                    )() is M.truth_value:
                        inner = M.Head(M.Tail(target)())()
                        if M.IsPair(inner)() is M.truth_value:
                            if M.Compare(
                                M.Head(inner)(), M.Char("same"),
                            )() is M.truth_value:
                                verdict = _verify_ground_equation(inner)
                                if M.IdentityCompare(
                                    verdict, M.EmptyList,
                                )() is M.false_value:
                                    is_computed_equation = M.truth_value
                                    if M.Compare(
                                        M.Head(verdict)(),
                                        M.Char("differs"),
                                    )() is M.truth_value:
                                        computed_line = (
                                            "the machine computed"
                                            + " the left side; it is "
                                            + _words_of_value_text(
                                                str(
                                                    M.Head(
                                                        M.Tail(
                                                            verdict,
                                                        )(),
                                                    )(),
                                                ),
                                            )
                                            + ", not the right side"
                                        )
                if M.IdentityCompare(
                    is_computed_equation, M.truth_value,
                )() is M.truth_value:
                    return [
                        " " * depth
                        + target_text
                        + " -- " + computed_line + ".",
                    ]
                fact_scan = fact_chain
                while M.IdentityCompare(
                    fact_scan, M.EmptyList,
                )() is M.false_value:
                    if M.Compare(
                        M.Head(fact_scan)(), target,
                    )() is M.truth_value:
                        return [
                            " " * depth
                            + target_text
                            + " -- a recorded fact.",
                        ]
                    fact_scan = M.Tail(fact_scan)()
                rule_scan = rule_chain
                while M.IdentityCompare(
                    rule_scan, M.EmptyList,
                )() is M.false_value:
                    explain_rule = M.Head(rule_scan)()
                    replacement = P.RuleReplacement(explain_rule)()
                    matched = G.TermMatchBindings(
                        replacement,
                        target,
                        M.EmptyList,
                    )()
                    if M.IdentityCompare(
                        M.Head(matched)(), M.truth_value,
                    )() is M.truth_value:
                        bindings = M.Tail(matched)()
                        premise_scan = P.RulePremises(explain_rule)()
                        premise_lines = []
                        resolved = M.truth_value
                        while M.IdentityCompare(
                            premise_scan, M.EmptyList,
                        )() is M.false_value:
                            premise = M.Head(premise_scan)()
                            premise_scan = M.Tail(premise_scan)()
                            bound_premise = M.Head(
                                M.Instantiate(
                                    premise, bindings,
                                )(),
                            )()
                            if _explain_has_var(bound_premise, 0):
                                grounding = _explain_ground_from_facts(
                                    bound_premise,
                                    bindings,
                                    fact_chain,
                                    rule_chain,
                                )
                                if M.IdentityCompare(
                                    grounding, M.EmptyList,
                                )() is M.truth_value:
                                    resolved = M.false_value
                                    premise_scan = M.EmptyList
                                else:
                                    bound_premise = M.Head(
                                        grounding,
                                    )()
                                    bindings = M.Head(
                                        M.Tail(grounding)(),
                                    )()
                            if M.IdentityCompare(
                                resolved, M.truth_value,
                            )() is M.truth_value:
                                sub_lines = _explain_resolve(
                                    bound_premise,
                                    depth + 2,
                                    rule_chain,
                                    fact_chain,
                                )
                                if sub_lines is None:
                                    resolved = M.false_value
                                    premise_scan = M.EmptyList
                                else:
                                    premise_lines.extend(sub_lines)
                        if M.IdentityCompare(
                            resolved, M.truth_value,
                        )() is M.truth_value:
                            return [
                                " " * depth
                                + target_text
                                + " -- by the taught rule '"
                                + P.PrettyRule(
                                    explain_rule, registry,
                                )()
                                + "':",
                            ] + premise_lines
                    rule_scan = M.Tail(rule_scan)()
                return None

            explain_lines = _explain_resolve(
                explain_goal,
                0,
                explain_rules,
                explain_facts,
            )
            if explain_lines is None:
                return (
                    "I could not account for "
                    + explain_text
                    + " from the recorded teaching."
                )
            return "\n".join(explain_lines)
        if lowered.startswith("query:"):
            parity_query_text = line[6:].strip()
            folded_parity_query = parity_query_text.lower()
            if folded_parity_query.startswith("gcd(") and folded_parity_query.endswith(")"):
                comma = parity_query_text.find(",")
                if comma == -1:
                    return "I could not parse the GCD pair."
                first_text = parity_query_text[4:comma].strip()
                second_text = parity_query_text[comma + 1:-1].strip()
                euclidean_lemma = Euc.FindEuclideanAlgorithmLemma(
                    G.GraphNodes(learned_version)(),
                )()
                if M.IdentityCompare(euclidean_lemma, M.EmptyList)() is M.truth_value:
                    probe = Euc.EuclideanDescentTrace(
                        first_text, second_text, registry,
                    )()
                    if M.IdentityCompare(probe, M.EmptyList)() is M.truth_value:
                        return "Euclidean descent refused: inputs must be nonnegative and not both zero."
                    last_euclidean_stall = M.Pair(
                        M.Char(first_text), M.Pair(M.Char(second_text), M.EmptyList),
                    )
                    return (
                        "no replayable Euclidean descent is saved. Type 'suggest lemmas' "
                        "to generate remainder witnesses and a well-ordering certificate."
                    )
                replay = Euc.ReplayEuclideanAlgorithmLemma(
                    euclidean_lemma, first_text, second_text, registry,
                )()
                if M.IdentityCompare(replay, M.EmptyList)() is M.truth_value:
                    return "Euclidean replay refused: a remainder, bound, or descent obligation failed."
                gcd_text = Euc.ReplayGCDText(replay)()
                divisibility = Euc.VerifyGCDDivisibility(
                    first_text, second_text, gcd_text,
                )()
                if divisibility is M.false_value:
                    return "Euclidean replay refused: the terminal value did not divide both inputs."
                learned_version = G.CreditInventedLemmaReplay(
                    learned_version, replay, euclidean_lemma, registry,
                )()
                _persist_talk_state()
                return (
                    "yes; remainder-witnessed descent terminated at gcd(" + first_text
                    + "," + second_text + ") = " + gcd_text
                    + "; every step verified a=b*q+r and 0<=r<b."
                )
            if folded_parity_query.startswith("congruentmod(") and folded_parity_query.endswith(")"):
                body_text = parity_query_text[13:-1]
                first_comma = body_text.find(",")
                second_comma = body_text.find(",", first_comma + 1)
                third_comma = body_text.find(",", second_comma + 1)
                if first_comma == -1 or second_comma == -1 or third_comma == -1:
                    return "I could not parse that witnessed congruence query."
                modulus = G.ParsePolynomialExpressionText(
                    body_text[:first_comma].strip(), reading_digits,
                )()
                left = G.ParsePolynomialExpressionText(
                    body_text[first_comma + 1:second_comma].strip(), reading_digits,
                )()
                right = G.ParsePolynomialExpressionText(
                    body_text[second_comma + 1:third_comma].strip(), reading_digits,
                )()
                witness = G.ParsePolynomialExpressionText(
                    body_text[third_comma + 1:].strip(), reading_digits,
                )()
                congruence = Res.WitnessedCongruence(
                    modulus, left, right, witness,
                )()
                if Res.VerifyWitnessedCongruence(
                    congruence, M.EmptyList, registry,
                )() is M.truth_value:
                    return "yes; the congruence witness normalized a-b-m*w to zero."
                return "no; the congruence witness failed normalization."
            if folded_parity_query.startswith("divides(4,") or folded_parity_query.startswith("divides(5,"):
                modular_implication = folded_parity_query.find(" implies ")
                modular_conjunction = folded_parity_query.find(" and divides(")
                modulus_comma = parity_query_text.find(",")
                modulus = G.ParsePolynomialExpressionText(
                    parity_query_text[8:modulus_comma].strip(), reading_digits,
                )()
                if modular_implication != -1:
                    conclusion_text = parity_query_text[modular_implication + 9:].strip()
                    comma = conclusion_text.find(",")
                    variable_text = conclusion_text[comma + 1:-1].strip()
                    variable = G.ParsePolynomialExpressionText(
                        variable_text, reading_digits,
                    )()
                    case_lemma = Mod.FindBoundedResidueLemma(
                        G.GraphNodes(learned_version)(), modulus, registry,
                    )()
                    if M.IdentityCompare(case_lemma, M.EmptyList)() is M.truth_value:
                        last_modular_stall = M.Pair(
                            M.Char("bounded-residue-case-stall"),
                            M.Pair(modulus, M.Pair(variable, M.EmptyList)),
                        )
                        return (
                            "no; this modulus needs a bounded exhaustive residue split. "
                            "Type 'suggest lemmas' to generate all residue branches."
                        )
                    premise = Mod.WitnessedDivides(
                        modulus, Mod.SquareExpression(variable)(),
                        Mod.SquareExpression(Mod.ModulusWitnessVariable(modulus, variable)())(),
                    )()
                    replay = Mod.ReplayBoundedResidueLemma(
                        case_lemma, modulus, variable, premise, registry,
                    )()
                    if M.IdentityCompare(replay, M.EmptyList)() is M.truth_value:
                        return "no; the bounded residue certificate did not revalidate."
                    learned_version = G.CreditInventedLemmaReplay(
                        learned_version, replay, case_lemma, registry,
                    )()
                    _persist_talk_state()
                    return (
                        "yes; replayed every residue class modulo "
                        + Mod.IntegerText(modulus)()
                        + " and closed each nonzero-square branch by its verified remainder."
                    )
                if modular_conjunction != -1:
                    if M.IdentityCompare(scoped_integer_equations, M.EmptyList)() is M.truth_value:
                        return "no; coupled residue propagation needs a scoped equation."
                    equation = M.Head(scoped_integer_equations)()
                    case_lemma = Mod.FindBoundedResidueLemma(
                        G.GraphNodes(learned_version)(), modulus, registry,
                    )()
                    if M.IdentityCompare(case_lemma, M.EmptyList)() is M.truth_value:
                        return "no; the bounded residue lemma is missing."
                    coupled = Mod.CoupledBoundedResidueProof(
                        modulus, equation, case_lemma, registry,
                    )()
                    if M.IdentityCompare(coupled, M.EmptyList)() is M.truth_value:
                        return "no; coupled residue witness propagation did not normalize."
                    first_nested = M.Head(M.Tail(M.Tail(coupled)())())()
                    learned_version = G.CreditInventedLemmaReplay(
                        learned_version, first_nested, case_lemma, registry,
                    )()
                    refreshed = Mod.FindBoundedResidueLemma(
                        G.GraphNodes(learned_version)(), modulus, registry,
                    )()
                    coupled_lemma = Mod.CoupledBoundedResidueLemma(
                        modulus, equation, refreshed, coupled,
                    )()
                    if M.IdentityCompare(
                        Mod.FindCoupledBoundedResidueLemma(
                            G.GraphNodes(learned_version)(), modulus, registry,
                        )(),
                        M.EmptyList,
                    )() is M.truth_value:
                        learned_version = G.GraphVersion(
                            M.Pair(coupled_lemma, G.GraphNodes(learned_version)()),
                            G.GraphEdges(learned_version)(),
                            G.GraphVersionInvariants(learned_version)(),
                        )()
                    _persist_talk_state()
                    return (
                        "yes; replayed the bounded-modulus square lemma twice, normalized "
                        "the coupled witness equation, and credited the dependency once."
                    )
            if folded_parity_query.startswith("divides(3,"):
                residue_implication = folded_parity_query.find(" implies ")
                residue_conjunction = folded_parity_query.find(" and divides(3,")
                if residue_implication != -1:
                    conclusion_text = parity_query_text[residue_implication + 9:].strip()
                    comma = conclusion_text.find(",")
                    variable_text = conclusion_text[comma + 1:-1].strip()
                    variable = G.ParsePolynomialExpressionText(
                        variable_text, reading_digits,
                    )()
                    case_lemma = Res.FindModThreeLemma(G.GraphNodes(learned_version)())()
                    if M.IdentityCompare(case_lemma, M.EmptyList)() is M.truth_value:
                        last_residue_stall = M.Pair(
                            M.Char("mod-three-case-stall"), M.Pair(variable, M.EmptyList),
                        )
                        return (
                            "no; divisibility of a square by 3 needs all three residue "
                            "classes. Type 'suggest lemmas' to invent the case split."
                        )
                    premise = Res.WitnessedDivides(
                        Res.IntegerThree()(), Res.SquareExpression(variable)(),
                        Res.SquareExpression(Res.ResidueWitnessVariable(variable)())(),
                    )()
                    replay = Res.ReplayModThreeLemma(
                        case_lemma, variable, premise, registry,
                    )()
                    if M.IdentityCompare(replay, M.EmptyList)() is M.truth_value:
                        return "no; the saved mod-3 case split did not revalidate."
                    learned_version = G.CreditInventedLemmaReplay(
                        learned_version, replay, case_lemma, registry,
                    )()
                    _persist_talk_state()
                    return (
                        "yes; replayed residues 0, 1, and 2 modulo 3; the two "
                        "nonzero-square branches contradict divisibility by 3."
                    )
                if residue_conjunction != -1:
                    if M.IdentityCompare(scoped_integer_equations, M.EmptyList)() is M.truth_value:
                        return "no; coupled mod-3 divisibility needs a scoped equation."
                    equation = M.Head(scoped_integer_equations)()
                    case_lemma = Res.FindModThreeLemma(G.GraphNodes(learned_version)())()
                    if M.IdentityCompare(case_lemma, M.EmptyList)() is M.truth_value:
                        return "no; the saved mod-3 square lemma is missing."
                    coupled = Res.CoupledModThreeProof(equation, case_lemma, registry)()
                    if M.IdentityCompare(coupled, M.EmptyList)() is M.truth_value:
                        return "no; coupled mod-3 witness propagation did not normalize."
                    first_nested = M.Head(M.Tail(M.Tail(coupled)())())()
                    learned_version = G.CreditInventedLemmaReplay(
                        learned_version, first_nested, case_lemma, registry,
                    )()
                    refreshed_case = Res.FindModThreeLemma(G.GraphNodes(learned_version)())()
                    coupled_lemma = Res.CoupledModThreeLemma(
                        equation, refreshed_case, coupled,
                    )()
                    if M.IdentityCompare(
                        Res.FindCoupledModThreeLemma(G.GraphNodes(learned_version)())(),
                        M.EmptyList,
                    )() is M.truth_value:
                        learned_version = G.GraphVersion(
                            M.Pair(coupled_lemma, G.GraphNodes(learned_version)()),
                            G.GraphEdges(learned_version)(),
                            G.GraphVersionInvariants(learned_version)(),
                        )()
                    _persist_talk_state()
                    return (
                        "yes; derived 3|x^2, replayed the saved residue lemma for x, "
                        "normalized y^2=3*u^2, replayed it for y, and credited the "
                        "dependency once."
                    )
            if folded_parity_query.startswith("divides(") and folded_parity_query.endswith(")"):
                body_text = parity_query_text[8:-1]
                first_comma = body_text.find(",")
                second_comma = body_text.find(",", first_comma + 1)
                if first_comma == -1 or second_comma == -1:
                    return "I could not parse that witnessed divisibility query."
                divisor = G.ParsePolynomialExpressionText(
                    body_text[:first_comma].strip(), reading_digits,
                )()
                dividend = G.ParsePolynomialExpressionText(
                    body_text[first_comma + 1:second_comma].strip(), reading_digits,
                )()
                witness = G.ParsePolynomialExpressionText(
                    body_text[second_comma + 1:].strip(), reading_digits,
                )()
                fact = Par.WitnessedDivides(divisor, dividend, witness)()
                if Par.VerifyWitnessedDivisibility(
                    fact, M.EmptyList, registry,
                )() is M.truth_value:
                    return "yes; the supplied divisibility witness normalized n-d*w to zero."
                return "no; the supplied divisibility witness failed normalization."
            if folded_parity_query.startswith("even("):
                implication_marker = folded_parity_query.find(" implies ")
                if M.Compare(
                    M.Char(str(implication_marker)), M.Char("-1"),
                )() is M.false_value:
                    implication_tail = parity_query_text[implication_marker + 9:].strip()
                    variable_text = implication_tail[5:-1]
                    variable = G.ParsePolynomialExpressionText(variable_text, reading_digits)()
                    parity_lemma = Par.FindParityLemma(G.GraphNodes(learned_version)())()
                    if M.IdentityCompare(parity_lemma, M.EmptyList)() is M.truth_value:
                        last_parity_stall = M.Pair(
                            M.Char("parity-case-split-stall"), M.Pair(variable, M.EmptyList),
                        )
                        return (
                            "no; Even(" + variable_text + "^2) -> Even(" + variable_text
                            + ") needs exhaustive parity cases. Type 'suggest lemmas' to invent them."
                        )
                    square_fact = Par.WitnessedDivides(
                        Par.IntegerTwo()(), Par.SquareExpression(variable)(),
                        Par.SquareExpression(Par.EvenWitnessVariable(variable)())(),
                    )()
                    replay = Par.ReplayParityLemma(parity_lemma, variable, square_fact, registry)()
                    if M.IdentityCompare(replay, M.EmptyList)() is M.truth_value:
                        return "no; the saved parity case split did not revalidate."
                    learned_version = G.CreditInventedLemmaReplay(
                        learned_version, replay, parity_lemma, registry,
                    )()
                    _persist_talk_state()
                    return (
                        "yes; replayed both parity branches: the even branch provides a "
                        "witness, and the odd branch contradicts Even(" + variable_text + "^2)."
                    )
                conjunction_marker = folded_parity_query.find(" and even(")
                if M.Compare(
                    M.Char(str(conjunction_marker)), M.Char("-1"),
                )() is M.false_value:
                    if M.IdentityCompare(scoped_integer_equations, M.EmptyList)() is M.truth_value:
                        return "no; coupled parity needs a scoped integer equation."
                    equation = M.Head(scoped_integer_equations)()
                    parity_lemma = Par.FindParityLemma(G.GraphNodes(learned_version)())()
                    if M.IdentityCompare(parity_lemma, M.EmptyList)() is M.truth_value:
                        return "no; coupled parity needs the saved parity case-split lemma."
                    coupled = Par.CoupledParityProof(equation, parity_lemma, registry)()
                    if M.IdentityCompare(coupled, M.EmptyList)() is M.truth_value:
                        return "no; the two witnessed parity steps did not normalize."
                    first_nested = M.Head(M.Tail(M.Tail(coupled)())())()
                    learned_version = G.CreditInventedLemmaReplay(
                        learned_version, first_nested, parity_lemma, registry,
                    )()
                    refreshed_parity = Par.FindParityLemma(G.GraphNodes(learned_version)())()
                    coupled_lemma = Par.CoupledParityLemma(
                        equation, refreshed_parity, coupled,
                    )()
                    if M.IdentityCompare(
                        Par.FindCoupledParityLemma(G.GraphNodes(learned_version)())(),
                        M.EmptyList,
                    )() is M.truth_value:
                        learned_version = G.GraphVersion(
                            M.Pair(coupled_lemma, G.GraphNodes(learned_version)()),
                            G.GraphEdges(learned_version)(),
                            G.GraphVersionInvariants(learned_version)(),
                        )()
                    _persist_talk_state()
                    return (
                        "yes; derived Even(x^2), replayed the saved parity lemma for x, "
                        "normalized y^2 = 2*u^2, replayed it for y, and credited the "
                        "dependency once."
                    )
                expression = G.ParsePolynomialExpressionText(
                    parity_query_text[5:-1], reading_digits,
                )()
                propagated = Par.PropagateEvenSquare(
                    expression, scoped_divisibility_assumptions, registry,
                )()
                if M.IdentityCompare(propagated, M.EmptyList)() is M.truth_value:
                    return "no; no normalization-verified divisibility witness supports that parity goal."
                return (
                    "yes; propagated witnessed divisibility through squaring; the new "
                    "witness is 2*k^2 and its identity normalized to zero."
                )
            if folded_parity_query.startswith("no positive integers") or folded_parity_query.startswith("no integers"):
                marker = folded_parity_query.find("satisfy")
                if marker == -1:
                    return "I could not parse that nonexistence goal."
                equation = G.ParsePolynomialEquationText(
                    parity_query_text[marker + 7:].strip(), reading_digits,
                )()
                if M.IdentityCompare(equation, M.EmptyList)() is M.truth_value:
                    return "I could not parse the descent equation."
                positivity = M.false_value
                if folded_parity_query.startswith("no positive integers"):
                    positivity = M.truth_value
                bounded_modulus = Mod.FindBoundedResidueModulusForEquation(
                    G.GraphNodes(learned_version)(), equation, registry,
                )()
                if M.IdentityCompare(
                    bounded_modulus, M.EmptyList,
                )() is M.false_value:
                    modular_descent = Mod.FindBoundedModulusDescentLemma(
                        G.GraphNodes(learned_version)(), bounded_modulus, registry,
                    )()
                    if M.IdentityCompare(modular_descent, M.EmptyList)() is M.truth_value:
                        last_modular_stall = M.Pair(
                            M.Char("bounded-modulus-descent-stall"),
                            M.Pair(
                                bounded_modulus,
                                M.Pair(equation, M.Pair(positivity, M.EmptyList)),
                            ),
                        )
                        return (
                            "no; no verified modulus-" + Mod.IntegerText(bounded_modulus)()
                            + " descent is saved. Type 'suggest lemmas' to discover it "
                            "from the bounded residue proof."
                        )
                    modular_replay = Mod.ReplayBoundedModulusDescentLemma(
                        modular_descent, bounded_modulus, equation,
                        G.GraphNodes(learned_version)(), positivity, registry,
                    )()
                    if M.Compare(
                        M.Head(modular_replay)(),
                        M.Char("bounded-modulus-descent-replay-failure"),
                    )() is M.truth_value:
                        return "Cannot replay bounded-modulus descent: " + str(
                            M.Head(M.Tail(modular_replay)())()(),
                        ) + "."
                    learned_version = G.CreditInventedLemmaReplay(
                        learned_version, modular_replay, modular_descent, registry,
                    )()
                    case_dependency = Mod.FindBoundedResidueLemma(
                        G.GraphNodes(learned_version)(), bounded_modulus, registry,
                    )()
                    coupled_dependency = Mod.FindCoupledBoundedResidueLemma(
                        G.GraphNodes(learned_version)(), bounded_modulus, registry,
                    )()
                    coupled_proof = Mod.CoupledBoundedResidueProof(
                        bounded_modulus, equation, case_dependency, registry,
                    )()
                    case_replay = M.Head(M.Tail(M.Tail(coupled_proof)())())()
                    learned_version = G.CreditInventedLemmaReplay(
                        learned_version, case_replay, case_dependency, registry,
                    )()
                    coupled_dependency = Mod.FindCoupledBoundedResidueLemma(
                        G.GraphNodes(learned_version)(), bounded_modulus, registry,
                    )()
                    coupled_credit = M.Pair(
                        M.Char("invented-lemma-replay-derivation"),
                        M.Pair(
                            Mod.CoupledBoundedResidueGoal(bounded_modulus, equation)(),
                            M.Pair(
                                coupled_dependency,
                                M.Pair(
                                    coupled_proof,
                                    M.Pair(
                                        M.Char("nested-bounded-residue-replay"),
                                        M.Pair(
                                            M.Char("witness-normalization"),
                                            M.Pair(M.Char("proved"), M.EmptyList),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    )
                    learned_version = G.CreditInventedLemmaReplay(
                        learned_version, coupled_credit, coupled_dependency, registry,
                    )()
                    _persist_talk_state()
                    return (
                        "yes; replayed the modulus-parameterized residue dependencies, "
                        "reconstructed (x,y)->(y,u), verified strict decrease, and "
                        "applied minimal-counterexample descent."
                    )
                residue_family = M.OrAtom(
                    Res.IsModThreeSquareEquation(equation, registry)(),
                    Res.IsModNineSquareEquation(equation, registry)(),
                )()
                if residue_family is M.truth_value:
                    residue_descent = Res.FindModThreeDescentLemma(
                        G.GraphNodes(learned_version)(),
                    )()
                    if M.IdentityCompare(residue_descent, M.EmptyList)() is M.truth_value:
                        last_residue_stall = M.Pair(
                            M.Char("mod-three-descent-stall"),
                            M.Pair(equation, M.Pair(positivity, M.EmptyList)),
                        )
                        return (
                            "no; no verified mod-3 descent is saved. Type 'suggest "
                            "lemmas' to discover it from the residue witnesses."
                        )
                    residue_replay = Res.ReplayModThreeDescentLemma(
                        residue_descent, equation,
                        G.GraphNodes(learned_version)(), positivity, registry,
                    )()
                    if M.Compare(
                        M.Head(residue_replay)(),
                        M.Char("mod-three-descent-replay-failure"),
                    )() is M.truth_value:
                        return "Cannot replay mod-3 descent: " + str(
                            M.Head(M.Tail(residue_replay)())()(),
                        ) + "."
                    learned_version = G.CreditInventedLemmaReplay(
                        learned_version, residue_replay, residue_descent, registry,
                    )()
                    case_dependency = Res.FindModThreeLemma(
                        G.GraphNodes(learned_version)(),
                    )()
                    coupled_dependency = Res.FindCoupledModThreeLemma(
                        G.GraphNodes(learned_version)(),
                    )()
                    coupled_proof = Res.CoupledModThreeProof(
                        equation, case_dependency, registry,
                    )()
                    case_replay = M.Head(M.Tail(M.Tail(coupled_proof)())())()
                    learned_version = G.CreditInventedLemmaReplay(
                        learned_version, case_replay, case_dependency, registry,
                    )()
                    coupled_dependency = Res.FindCoupledModThreeLemma(
                        G.GraphNodes(learned_version)(),
                    )()
                    coupled_credit = M.Pair(
                        M.Char("invented-lemma-replay-derivation"),
                        M.Pair(
                            Res.CoupledModThreeGoal(equation)(),
                            M.Pair(
                                coupled_dependency,
                                M.Pair(
                                    coupled_proof,
                                    M.Pair(
                                        M.Char("nested-mod-three-replay"),
                                        M.Pair(
                                            M.Char("witness-normalization"),
                                            M.Pair(M.Char("proved"), M.EmptyList),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    )
                    learned_version = G.CreditInventedLemmaReplay(
                        learned_version, coupled_credit, coupled_dependency, registry,
                    )()
                    _persist_talk_state()
                    return (
                        "yes; replayed the mod-3 residue dependencies, reconstructed "
                        "(x,y)->(y,u), verified positivity and strict decrease, and "
                        "applied minimal-counterexample descent."
                    )
                descent_lemma = Par.FindDescentLemma(G.GraphNodes(learned_version)())()
                if M.IdentityCompare(descent_lemma, M.EmptyList)() is M.truth_value:
                    last_parity_stall = M.Pair(
                        M.Char("descent-stall"),
                        M.Pair(equation, M.Pair(positivity, M.EmptyList)),
                    )
                    return (
                        "no; no verified minimal-counterexample descent is saved. "
                        "Type 'suggest lemmas' to search for a descent map."
                    )
                replay = Par.ReplayDescentLemma(
                    descent_lemma, equation, G.GraphNodes(learned_version)(),
                    positivity, registry,
                )()
                if M.Compare(
                    M.Head(replay)(), M.Char("descent-replay-failure"),
                )() is M.truth_value:
                    return "Cannot replay descent: " + str(M.Head(M.Tail(replay)())()()) + "."
                learned_version = G.CreditInventedLemmaReplay(
                    learned_version, replay, descent_lemma, registry,
                )()
                parity_dependency = Par.FindParityLemma(
                    G.GraphNodes(learned_version)(),
                )()
                coupled_dependency = Par.FindCoupledParityLemma(
                    G.GraphNodes(learned_version)(),
                )()
                coupled_replay = Par.CoupledParityProof(
                    equation, parity_dependency, registry,
                )()
                parity_replay = M.Head(
                    M.Tail(M.Tail(coupled_replay)())(),
                )()
                learned_version = G.CreditInventedLemmaReplay(
                    learned_version,
                    parity_replay,
                    parity_dependency,
                    registry,
                )()
                coupled_dependency = Par.FindCoupledParityLemma(
                    G.GraphNodes(learned_version)(),
                )()
                coupled_credit_replay = M.Pair(
                    M.Char("invented-lemma-replay-derivation"),
                    M.Pair(
                        Par.CoupledParityGoal(equation)(),
                        M.Pair(
                            coupled_dependency,
                            M.Pair(
                                coupled_replay,
                                M.Pair(
                                    M.Char("nested-parity-replay"),
                                    M.Pair(
                                        M.Char("witness-normalization"),
                                        M.Pair(M.Char("proved"), M.EmptyList),
                                    ),
                                ),
                            ),
                        ),
                    ),
                )
                learned_version = G.CreditInventedLemmaReplay(
                    learned_version,
                    coupled_credit_replay,
                    coupled_dependency,
                    registry,
                )()
                _persist_talk_state()
                return (
                    "yes; replayed the nested parity dependencies, reconstructed "
                    "(x,y)->(y,u), verified positivity and strict decrease, and "
                    "applied minimal-counterexample descent."
                )
            known_constructors = G.RuleConstructors(
                learned_version,
                pack_concepts,
            )()
            polynomial_goal = G.ParsePolynomialInequalityText(
                line[6:].strip(), reading_digits,
            )()
            parsed_query = M.EmptyList
            if M.IdentityCompare(
                polynomial_goal, M.EmptyList,
            )() is M.truth_value:
                parsed_query = G.ParseRuleText(
                    line[6:].strip(),
                    reading_policy,
                    reading_digits,
                    known_constructors,
                    M.truth_value,
                )()
                goal = M.Head(parsed_query)()
                reason = M.Head(M.Tail(parsed_query)())()
            else:
                goal = polynomial_goal
                reason = M.EmptyList
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
            recorded_case_conclusions = G.InstalledCaseConclusions(
                learned_version,
            )()
            recorded_case = M.EmptyList
            while M.IdentityCompare(
                recorded_case_conclusions, M.EmptyList,
            )() is M.false_value:
                candidate_case = M.Head(recorded_case_conclusions)()
                if M.Compare(
                    G.CaseConclusionCandidate(candidate_case)(),
                    goal,
                )() is M.truth_value:
                    recorded_case = candidate_case
                    recorded_case_conclusions = M.EmptyList
                else:
                    recorded_case_conclusions = M.Tail(
                        recorded_case_conclusions,
                    )()
            if M.IdentityCompare(recorded_case, M.EmptyList)() is M.false_value:
                return (
                    "yes; " + line[6:].strip()
                    + " is already recorded as a case-elimination conclusion."
                )
            facts = G.InstalledTaughtFacts(learned_version)()
            facts = P.Append(scoped_assumptions, facts)()
            schema_hit = G.LookupTaughtDerivationSchema(
                learned_version,
                P.Knowledge(facts)(),
                goal,
            )()
            if M.IdentityCompare(schema_hit, M.EmptyList)() is M.false_value:
                schema = M.Head(M.Tail(M.Tail(schema_hit)())())()
                consultation = G.SchemaConsultation(
                    schema,
                    P.Knowledge(facts)(),
                    goal,
                )()
                talk_ledger.append(
                    G.FiringRecord(
                        schema,
                        learned_version,
                        learned_version,
                        M.Pair(consultation, M.EmptyList),
                        M.Zero,
                        M.Zero,
                        M.Zero,
                        M.Zero,
                        M.one,
                    )(),
                )
                last_goal = goal
                _persist_talk_state()
                return (
                    "yes; derived " + line[6:].strip()
                    + " from an approved taught schema."
                )
            # Recorded case conclusions join the working set the way
            # taught facts do: what the elimination established is
            # available to later rules, so the sieve's process rules
            # conclude from what the sieve itself decided.
            conclusion_join_scan = G.InstalledCaseConclusions(
                learned_version,
            )()
            while M.IdentityCompare(
                conclusion_join_scan, M.EmptyList,
            )() is M.false_value:
                facts = M.Pair(
                    G.CaseConclusionCandidate(
                        M.Head(conclusion_join_scan)(),
                    )(),
                    facts,
                )
                conclusion_join_scan = M.Tail(
                    conclusion_join_scan,
                )()
            # The numeral words' analytic sameness facts join the
            # working set the way pack laws do: distinct numeral words
            # name distinct numbers, each names itself. A taught
            # different(x, y) -> not(same(x, y)) law turns them into
            # refutations; nothing is guessed for words the digit
            # chain does not own. They join only when something in the
            # query can speak them -- the goal, or a rule's premise or
            # replacement naming same or different -- because a
            # working set that cannot use them only pays for carrying
            # them.
            sameness_spoken = M.false_value
            if M.IsPair(goal)() is M.truth_value:
                if M.Compare(M.Head(goal)(), M.Char("same"))() is M.truth_value:
                    sameness_spoken = M.truth_value
                elif M.Compare(M.Head(goal)(), M.Char("different"))() is M.truth_value:
                    sameness_spoken = M.truth_value
            rule_speak_scan = G.InstalledTaughtRules(learned_version)()
            while M.IdentityCompare(
                rule_speak_scan, M.EmptyList,
            )() is M.false_value:
                if M.IdentityCompare(
                    sameness_spoken, M.truth_value,
                )() is M.truth_value:
                    rule_speak_scan = M.EmptyList
                else:
                    speak_rule = M.Head(rule_speak_scan)()
                    speak_scan = P.RulePremises(speak_rule)()
                    if M.IdentityCompare(
                        speak_scan, M.EmptyList,
                    )() is M.truth_value:
                        speak_scan = P.RuleReplacement(speak_rule)()
                    while M.IdentityCompare(
                        speak_scan, M.EmptyList,
                    )() is M.false_value:
                        speak_term = M.Head(speak_scan)()
                        if M.IsPair(speak_term)() is M.truth_value:
                            if M.Compare(
                                M.Head(speak_term)(), M.Char("same"),
                            )() is M.truth_value:
                                sameness_spoken = M.truth_value
                                speak_scan = M.EmptyList
                            elif M.Compare(
                                M.Head(speak_term)(), M.Char("different"),
                            )() is M.truth_value:
                                sameness_spoken = M.truth_value
                                speak_scan = M.EmptyList
                            elif M.Compare(
                                M.Head(speak_term)(), M.Char("not"),
                            )() is M.truth_value:
                                inner_speak = M.Head(
                                    M.Tail(speak_term)(),
                                )()
                                if M.IsPair(inner_speak)() is M.truth_value:
                                    if M.Compare(
                                        M.Head(inner_speak)(),
                                        M.Char("same"),
                                    )() is M.truth_value:
                                        sameness_spoken = M.truth_value
                                        speak_scan = M.EmptyList
                        if M.IdentityCompare(
                            speak_scan, M.EmptyList,
                        )() is M.false_value:
                            speak_scan = M.Tail(speak_scan)()
                    if M.IdentityCompare(
                        rule_speak_scan, M.EmptyList,
                    )() is M.false_value:
                        rule_speak_scan = M.Tail(rule_speak_scan)()
            numeral_facts = M.Pair(
                M.EmptyList, M.Pair(M.EmptyList, M.EmptyList),
            )
            if M.IdentityCompare(
                sameness_spoken, M.truth_value,
            )() is M.truth_value:
                numeral_facts = G.NumeralSamenessFacts(reading_digits)()
            numeral_scan = M.Head(numeral_facts)()
            while M.IdentityCompare(
                numeral_scan, M.EmptyList,
            )() is M.false_value:
                facts = M.Pair(M.Head(numeral_scan)(), facts)
                numeral_scan = M.Tail(numeral_scan)()
            numeral_scan = M.Head(M.Tail(numeral_facts)())()
            while M.IdentityCompare(
                numeral_scan, M.EmptyList,
            )() is M.false_value:
                facts = M.Pair(M.Head(numeral_scan)(), facts)
                numeral_scan = M.Tail(numeral_scan)()
            rules = G.InstalledTaughtRules(learned_version)()
            # The machine runs its own trial divisions: every ground
            # divisibility claim the goal or a rule's premises speak is
            # computed before chaining, and the computed polarity joins
            # the working set -- the sieve strikes its own candidates.
            computation_terms_reversed = M.EmptyList
            if M.IsPair(goal)() is M.truth_value:
                computation_terms_reversed = M.Pair(
                    goal, computation_terms_reversed,
                )
            rule_compute_scan = rules
            while M.IdentityCompare(
                rule_compute_scan, M.EmptyList,
            )() is M.false_value:
                compute_rule = M.Head(rule_compute_scan)()
                premise_compute_scan = P.RulePremises(compute_rule)()
                while M.IdentityCompare(
                    premise_compute_scan, M.EmptyList,
                )() is M.false_value:
                    computation_terms_reversed = M.Pair(
                        M.Head(premise_compute_scan)(),
                        computation_terms_reversed,
                    )
                    premise_compute_scan = M.Tail(
                        premise_compute_scan,
                    )()
                rule_compute_scan = M.Tail(rule_compute_scan)()
            computation_scan = M.Reverse(
                computation_terms_reversed,
            )()
            while M.IdentityCompare(
                computation_scan, M.EmptyList,
            )() is M.false_value:
                compute_term = M.Head(computation_scan)()
                compute_target = compute_term
                if M.IsPair(compute_term)() is M.truth_value:
                    if M.Compare(
                        M.Head(compute_term)(), M.Char("not"),
                    )() is M.truth_value:
                        if M.IdentityCompare(
                            M.Tail(compute_term)(), M.EmptyList,
                        )() is M.false_value:
                            compute_target = M.Head(
                                M.Tail(compute_term)(),
                            )()
                division_verdict = _computed_divisibility(
                    compute_target,
                )
                if M.IdentityCompare(
                    division_verdict, M.EmptyList,
                )() is M.false_value:
                    if M.Compare(
                        M.Head(division_verdict)(), M.Char("holds"),
                    )() is M.truth_value:
                        facts = M.Pair(compute_target, facts)
                    else:
                        facts = M.Pair(
                            M.Pair(
                                M.Char("not"),
                                M.Pair(compute_target, M.EmptyList),
                            ),
                            facts,
                        )
                # The same discipline for equations: a ground
                # same(expression, numeral) the goal or a rule's
                # premises speak is computed by the machine's own
                # numbers, and the computed polarity joins the working
                # set. A taught rule may lean on arithmetic the machine
                # never ran.
                equation_verdict = _verify_ground_equation(
                    compute_target,
                )
                if M.IdentityCompare(
                    equation_verdict, M.EmptyList,
                )() is M.false_value:
                    if M.Compare(
                        M.Head(equation_verdict)(),
                        M.Char("holds"),
                    )() is M.truth_value:
                        facts = M.Pair(compute_target, facts)
                    else:
                        facts = M.Pair(
                            M.Pair(
                                M.Char("not"),
                                M.Pair(compute_target, M.EmptyList),
                            ),
                            facts,
                        )
                computation_scan = M.Tail(computation_scan)()
            case_splits = G.InstalledCaseSplits(learned_version)()
            case_relevant = M.false_value
            relevant_splits_reversed = M.EmptyList
            relevance_scan = case_splits
            while M.IdentityCompare(
                relevance_scan, M.EmptyList,
            )() is M.false_value:
                relevance_candidates = M.Head(
                    M.Tail(G.CaseSplitExactlyOne(
                        M.Head(relevance_scan)(),
                    )())(),
                )()
                while M.IdentityCompare(
                    relevance_candidates, M.EmptyList,
                )() is M.false_value:
                    # A candidate speaks in placeholders -- exactly-one
                    # parses its arguments as symbols -- so relevance is
                    # the predicate: a goal about cat(fido) is this
                    # split's business when a branch speaks cat. The
                    # binding inside CaseSplitQuery enforces the arity.
                    if M.IsPair(
                        M.Head(relevance_candidates)(),
                    )() is M.truth_value:
                        if M.IsPair(goal)() is M.truth_value:
                            if M.Compare(
                                M.Head(M.Head(relevance_candidates)())(),
                                M.Head(goal)(),
                            )() is M.truth_value:
                                case_relevant = M.truth_value
                                relevant_splits_reversed = M.Pair(
                                    M.Head(relevance_scan)(),
                                    relevant_splits_reversed,
                                )
                                relevance_candidates = M.EmptyList
                            else:
                                relevance_candidates = M.Tail(
                                    relevance_candidates,
                                )()
                        else:
                            relevance_candidates = M.EmptyList
                    else:
                        relevance_candidates = M.Tail(relevance_candidates)()
                relevance_scan = M.Tail(relevance_scan)()
            if M.IdentityCompare(case_relevant, M.truth_value)() is M.truth_value:
                case_query = G.CaseSplitQuery(
                    facts,
                    rules,
                    M.Reverse(relevant_splits_reversed)(),
                    goal,
                )()
                case_status = M.Head(case_query)()
                case_kind = M.Head(M.Tail(case_query)())()
                case_conclusion = M.Head(
                    M.Tail(M.Tail(case_query)())(),
                )()
                if M.Compare(
                    case_kind, M.Char("all-branches-refuted"),
                )() is M.truth_value:
                    return (
                        "no; all ExactlyOne branches were refuted while "
                        + "checking " + line[6:].strip() + "."
                    )
                if M.Compare(
                    case_kind, M.Char("multiple-consistent-cases"),
                )() is M.truth_value:
                    return (
                        "no; multiple ExactlyOne branches remain consistent, "
                        + "so " + line[6:].strip() + " is not established."
                    )
                if M.Compare(
                    case_kind,
                    M.Char("consistent-case-does-not-prove-goal"),
                )() is M.truth_value:
                    case_refuted = M.Head(
                        M.Tail(M.Tail(M.Tail(case_query)())())(),
                    )()
                    goal_refuted = M.false_value
                    refuted_scan = case_refuted
                    while M.IdentityCompare(
                        refuted_scan, M.EmptyList,
                    )() is M.false_value:
                        if M.Compare(
                            M.Head(refuted_scan)(), goal,
                        )() is M.truth_value:
                            goal_refuted = M.truth_value
                            refuted_scan = M.EmptyList
                        else:
                            refuted_scan = M.Tail(refuted_scan)()
                    if M.IdentityCompare(
                        goal_refuted, M.truth_value,
                    )() is M.truth_value:
                        return (
                            "no; the case split refutes "
                            + line[6:].strip()
                            + " -- another branch holds for it and"
                            + " exactly one applies."
                        )
                    not_goal = M.Pair(
                        M.Char("not"), M.Pair(goal, M.EmptyList),
                    )
                    not_found = M.false_value
                    rule_scan = rules
                    while M.IdentityCompare(
                        rule_scan, M.EmptyList,
                    )() is M.false_value:
                        if M.IdentityCompare(
                            not_found, M.truth_value,
                        )() is M.truth_value:
                            rule_scan = M.EmptyList
                        else:
                            taught_rule = M.Head(rule_scan)()
                            bindings = P.JoinPremises(
                                P.RulePremises(taught_rule)(),
                                facts,
                                M.EmptyList,
                            )()
                            while M.IdentityCompare(
                                bindings, M.EmptyList,
                            )() is M.false_value:
                                if M.IdentityCompare(
                                    not_found, M.truth_value,
                                )() is M.truth_value:
                                    bindings = M.EmptyList
                                else:
                                    binding = M.Head(bindings)()
                                    instantiated = M.Instantiate(
                                        P.RuleReplacement(taught_rule)(),
                                        binding,
                                    )()
                                    derived = M.Head(instantiated)()
                                    if M.Compare(
                                        derived, not_goal,
                                    )() is M.truth_value:
                                        not_found = M.truth_value
                                        bindings = M.EmptyList
                                    else:
                                        bindings = M.Tail(bindings)()
                            if M.IdentityCompare(
                                rule_scan, M.EmptyList,
                            )() is M.false_value:
                                rule_scan = M.Tail(rule_scan)()
                    if M.IdentityCompare(
                        not_found, M.truth_value,
                    )() is M.truth_value:
                        return (
                            "no; " + line[6:].strip() + " is refuted --"
                            + " its negation is derivable from the"
                            + " taught rules and the numeral words'"
                            + " own differences."
                        )
                    return (
                        "no; the one consistent branch does not prove "
                        + line[6:].strip() + "."
                    )
                if M.IdentityCompare(
                    case_status, M.truth_value,
                )() is M.truth_value:
                    learned_version = G.InstallCaseConclusion(
                        learned_version,
                        case_conclusion,
                    )()
                    _persist_talk_state()
                    return (
                        "yes; established " + line[6:].strip()
                        + " by case elimination. The case conclusion was recorded."
                    )
                return (
                    "no; the one consistent branch does not prove "
                    + line[6:].strip() + "."
                )
            growing = M.truth_value
            rounds_text = "0"
            chain_capped = M.false_value
            while M.IdentityCompare(
                growing, M.truth_value,
            )() is M.truth_value:
                if G.GMPEqualText(rounds_text, "2")() is M.truth_value:
                    growing = M.false_value
                    chain_capped = M.truth_value
                else:
                    rounds_text = G.GMPSuccText(rounds_text)()
                    goal_early = M.false_value
                    goal_scan = facts
                    while M.IdentityCompare(
                        goal_scan, M.EmptyList,
                    )() is M.false_value:
                        if M.Compare(
                            M.Head(goal_scan)(), goal,
                        )() is M.truth_value:
                            goal_early = M.truth_value
                            goal_scan = M.EmptyList
                        else:
                            goal_scan = M.Tail(goal_scan)()
                    if M.IdentityCompare(
                        goal_early, M.truth_value,
                    )() is M.truth_value:
                        growing = M.false_value
                        rounds_text = "2"
                        remaining_rules = M.EmptyList
                    else:
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
                                instantiated_premises = P.InstantiateFactList(
                                    P.RulePremises(taught_rule)(),
                                    binding,
                                )()
                                taught_derivation = G.TaughtDerivation(
                                    derived,
                                    taught_rule,
                                    instantiated_premises,
                                )()
                                learned_version = G.InstallTaughtDerivation(
                                    learned_version,
                                    taught_derivation,
                                )()
                                facts = M.Pair(derived, facts)
                                growing = M.truth_value
                            bindings = M.Tail(bindings)()
                        remaining_rules = M.Tail(remaining_rules)()
            goal_found = M.false_value
            goal_refuted = M.false_value
            fact_scan = facts
            while M.IdentityCompare(
                fact_scan, M.EmptyList,
            )() is M.false_value:
                candidate_fact = M.Head(fact_scan)()
                if M.IsPair(candidate_fact)() is M.truth_value:
                    if M.Compare(
                        M.Head(candidate_fact)(), M.Char("not"),
                    )() is M.truth_value:
                        if M.Compare(
                            M.Head(M.Tail(candidate_fact)())(), goal,
                        )() is M.truth_value:
                            goal_refuted = M.truth_value
                goal_matches = M.Compare(candidate_fact, goal)()
                if M.IdentityCompare(
                    goal_matches, M.truth_value,
                )() is M.false_value:
                    if M.IsPair(candidate_fact)() is M.truth_value:
                        if M.IsPair(goal)() is M.truth_value:
                            if M.Compare(
                                M.Head(candidate_fact)(),
                                Lmod.SupportedLabel,
                            )() is M.truth_value:
                                if M.Compare(
                                    M.Head(goal)(),
                                    Lmod.SupportedLabel,
                                )() is M.truth_value:
                                    goal_arguments = M.Tail(goal)()
                                    fact_arguments = M.Tail(candidate_fact)()
                                    if M.IdentityCompare(
                                        goal_arguments, M.EmptyList,
                                    )() is M.false_value:
                                        if M.IdentityCompare(
                                            M.Tail(goal_arguments)(),
                                            M.EmptyList,
                                        )() is M.truth_value:
                                            if M.IdentityCompare(
                                                fact_arguments, M.EmptyList,
                                            )() is M.false_value:
                                                if M.Compare(
                                                    M.Head(goal_arguments)(),
                                                    M.Head(fact_arguments)(),
                                                )() is M.truth_value:
                                                    goal_matches = M.truth_value
                if M.IdentityCompare(
                    goal_matches, M.truth_value,
                )() is M.truth_value:
                    goal_found = M.truth_value
                    fact_scan = M.EmptyList
                else:
                    fact_scan = M.Tail(fact_scan)()
            last_goal = goal
            last_proof_registry = registry
            last_derivation = M.EmptyList
            last_outcome = M.EmptyList
            _persist_talk_state()
            if M.IdentityCompare(goal_found, M.truth_value)() is M.truth_value:
                return (
                    "yes; derived " + line[6:].strip()
                    + " from the taught facts and approved rules."
                )
            if M.IdentityCompare(
                goal_refuted, M.truth_value,
            )() is M.truth_value:
                return (
                    "no; " + line[6:].strip() + " is refuted -- its"
                    + " negation is derivable from the taught rules and"
                    + " the numeral words' own differences."
                )
            forward_failure = (
                "no; I could not derive " + line[6:].strip()
                + "."
            )
            if M.IdentityCompare(
                chain_capped, M.truth_value,
            )() is M.truth_value:
                forward_failure = (
                    "no; I could not derive " + line[6:].strip()
                    + " within the forward-chaining cap."
                )
            start = M.Knowledge(facts)()
            if M.IdentityCompare(
                polynomial_goal, M.EmptyList,
            )() is M.false_value:
                replay_hit = Min.ReplaySavedInventedLemma(
                    learned_version, goal, registry, scoped_assumptions,
                )()
                if M.IdentityCompare(replay_hit, M.EmptyList)() is M.false_value:
                    replay = M.Head(replay_hit)()
                    replay_lemma = M.Head(M.Tail(replay_hit)())()
                    replay_status = M.Head(
                        M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(replay)())())())())())(),
                    )()
                    if M.Compare(replay_status, M.Char("proved"))() is M.false_value:
                        if M.Compare(
                            replay_status, M.Char("missing-invented-dependency"),
                        )() is M.truth_value:
                            return "Cannot replay cubic lemma: missing invented SOS dependency."
                        if M.Compare(
                            replay_status, M.Char("missing-scoped-assumptions"),
                        )() is M.truth_value:
                            return "Cannot replay cubic lemma: x+y+z nonnegativity is not supported by the scoped assumptions."
                        return "Cannot replay the saved cubic lemma: " + str(replay_status()) + "."
                    learned_version = G.CreditInventedLemmaReplay(
                        learned_version, replay, replay_lemma, registry,
                    )()
                    used_nested_dependency = M.false_value
                    nested_evidence = M.Head(
                        M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(replay)())())())())(),
                    )()
                    if M.IsPair(nested_evidence)() is M.truth_value:
                        dependency_hit = M.Head(nested_evidence)()
                        if M.IsPair(dependency_hit)() is M.truth_value:
                            nested_replay = M.Head(dependency_hit)()
                            if M.IsPair(nested_replay)() is M.truth_value:
                                if M.Compare(
                                    M.Head(nested_replay)(),
                                    M.Char("invented-lemma-replay-derivation"),
                                )() is M.truth_value:
                                    used_nested_dependency = M.truth_value
                                    nested_lemma = M.Head(M.Tail(dependency_hit)())()
                                    learned_version = G.CreditInventedLemmaReplay(
                                        learned_version,
                                        nested_replay,
                                        nested_lemma,
                                        registry,
                                    )()
                    first_composed_replay = M.Head(
                        M.Tail(M.Tail(M.Tail(replay)())())(),
                    )()
                    second_composed_replay = M.Head(
                        M.Tail(M.Tail(M.Tail(M.Tail(replay)())())())(),
                    )()
                    if M.IsPair(first_composed_replay)() is M.truth_value:
                        if M.IsPair(second_composed_replay)() is M.truth_value:
                            if M.Compare(
                                M.Head(first_composed_replay)(),
                                M.Char("invented-lemma-replay-derivation"),
                            )() is M.truth_value:
                                if M.Compare(
                                    M.Head(second_composed_replay)(),
                                    M.Char("invented-lemma-replay-derivation"),
                                )() is M.truth_value:
                                    refreshed_lemma = G.LookupInventedLemma(
                                        learned_version,
                                        G.InventedLemmaGoal(replay_lemma)(),
                                    )()
                                    if M.IdentityCompare(
                                        refreshed_lemma, M.EmptyList,
                                    )() is M.false_value:
                                        learned_version = G.CreditInventedLemmaReplay(
                                            learned_version,
                                            second_composed_replay,
                                            refreshed_lemma,
                                            registry,
                                        )()
                    last_goal = goal
                    last_derivation = replay
                    replay_explanation = (
                        "yes; replayed the saved algebraic identity, "
                        "proved its nonnegativity obligations, and derived "
                        + line[6:].strip() + "."
                    )
                    if used_nested_dependency is M.truth_value:
                        replay_explanation = (
                            "yes; replayed the cubic factorization, proved "
                            "x+y+z nonnegative from the scoped assumptions, "
                            "reused the saved SOS lemma for the quadratic "
                            "factor, applied product nonnegativity, and derived "
                            + line[6:].strip() + "."
                        )
                    replay_step = M.Head(
                        M.Tail(M.Tail(M.Tail(replay)())())(),
                    )()
                    if M.IsPair(replay_step)() is M.truth_value:
                        if M.Compare(
                            M.Head(replay_step)(),
                            M.Char("invented-lemma-replay-derivation"),
                        )() is M.truth_value:
                            second_step = M.Head(
                                M.Tail(M.Tail(M.Tail(M.Tail(replay)())())())(),
                            )()
                            first_instance = M.Head(M.Tail(replay_step)())()
                            second_instance = M.Head(M.Tail(second_step)())()
                            replay_explanation = (
                                "yes; composed two independently revalidated "
                                "compound substitutions of the saved lemma:\n"
                                "1. " + M.PrettyTerm(first_instance, registry)()
                                + "\n2. " + M.PrettyTerm(second_instance, registry)()
                                + "\nThen inequality transitivity derived "
                                + line[6:].strip() + "."
                            )
                    _persist_talk_state()
                    return replay_explanation
                stall_graph = G.Hypergraph(registry)
                stall_graph._search_disable_console = M.truth_value
                stall_graph._search_disable_progress_ticker = M.truth_value
                stall_heuristic = Hmod.Heuristic(
                    M.DFSLabel,
                    M.InsertionOrderLabel,
                    M.three,
                    M.one,
                    M.one,
                    M.one,
                )()
                stall_rules = P.CompileRuleChain(
                    G.InstalledTaughtRules(learned_version)(), registry,
                )()
                searched = M.Search(
                    stall_graph,
                    start,
                    goal,
                    stall_rules,
                    stall_heuristic,
                    registry,
                )()
                stall = M.Head(M.Tail(M.Tail(searched)())())()
                if M.IdentityCompare(stall, M.EmptyList)() is M.truth_value:
                    _persist_talk_state()
                    return forward_failure + " Search returned no stall evidence."
                learned_version = G.InstallStallRecord(
                    learned_version, stall,
                )()
                frontier_count_pair = M.Count(
                    G.StallRecordFrontier(stall)(), registry,
                )()
                frontier_count = M.Head(frontier_count_pair)()
                registry = M.Head(M.Tail(frontier_count_pair)())()
                _persist_talk_state()
                return (
                    forward_failure + " Search failed after "
                    + M.PrettyTerm(
                        G.StallRecordFuelUsed(stall)(), registry,
                    )()
                    + " steps. "
                    + M.PrettyTerm(frontier_count, registry)()
                    + " frontier states preserved. Type 'suggest lemmas'"
                    + " to analyze the stall."
                )
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
            stall = M.EmptyList
            if M.IdentityCompare(stall, M.EmptyList)() is M.false_value:
                learned_version = G.InstallStallRecord(
                    learned_version, stall,
                )()
                frontier_count_pair = M.Count(
                    G.StallRecordFrontier(stall)(), registry,
                )()
                frontier_count = M.Head(frontier_count_pair)()
                registry = M.Head(M.Tail(frontier_count_pair)())()
                _persist_talk_state()
                return (
                    forward_failure + " Search failed after "
                    + M.PrettyTerm(
                        G.StallRecordFuelUsed(stall)(), registry,
                    )()
                    + " steps. "
                    + M.PrettyTerm(frontier_count, registry)()
                    + " frontier states preserved. Type 'suggest lemmas'"
                    + " to analyze the stall."
                )
            goal_target = goal
            if M.IsPair(goal)() is M.truth_value:
                goal_target = M.Head(goal)()
            residual_gap = M.Pair(
                Lmod.ResidualGapLabel,
                M.Pair(goal_target, M.EmptyList),
            )
            pending_gaps = M.Pair(residual_gap, pending_gaps)
            learned_version = G.InstallGap(learned_version, residual_gap)()
            _persist_talk_state()
            return (
                forward_failure + " No bounded search frontier was preserved."
            )
        if lowered.startswith("why not "):
            # The failed query's own explanation: what stands between
            # the goal and its derivation, computed from the state --
            # the rules that would conclude it and the premises they
            # are missing, the splits that would decide it and the
            # branches still standing, the divisions already run.
            why_not_text = line[8:].strip().rstrip("?.!")
            known_constructors = G.RuleConstructors(
                learned_version,
                pack_concepts,
            )()
            parsed_why_not = G.ParseRuleText(
                why_not_text,
                reading_policy,
                reading_digits,
                known_constructors,
                M.truth_value,
            )()
            why_not_goal = M.Head(parsed_why_not)()
            if M.IdentityCompare(
                why_not_goal, M.EmptyList,
            )() is M.truth_value:
                return (
                    "I could not read that as a claim. Use"
                    + " 'why not Predicate(constant)?'"
                )
            if M.IsPair(why_not_goal)() is not M.truth_value:
                return (
                    "I could not read that as a claim. Use"
                    + " 'why not Predicate(constant)?'"
                )
            why_not_head = M.Head(why_not_goal)()
            why_not_facts = G.InstalledTaughtFacts(learned_version)()
            why_not_rules = G.InstalledTaughtRules(learned_version)()
            # The divisions the goal and the rules speak run first, so
            # the missing-premise report never counts a computed
            # divisibility as missing.
            why_not_terms_reversed = M.Pair(
                why_not_goal, M.EmptyList,
            )
            why_not_rule_scan = why_not_rules
            while M.IdentityCompare(
                why_not_rule_scan, M.EmptyList,
            )() is M.false_value:
                why_not_premise_scan = P.RulePremises(
                    M.Head(why_not_rule_scan)(),
                )()
                while M.IdentityCompare(
                    why_not_premise_scan, M.EmptyList,
                )() is M.false_value:
                    why_not_terms_reversed = M.Pair(
                        M.Head(why_not_premise_scan)(),
                        why_not_terms_reversed,
                    )
                    why_not_premise_scan = M.Tail(
                        why_not_premise_scan,
                    )()
                why_not_rule_scan = M.Tail(why_not_rule_scan)()
            why_not_computed_lines = []
            why_not_compute_scan = why_not_terms_reversed
            while M.IdentityCompare(
                why_not_compute_scan, M.EmptyList,
            )() is M.false_value:
                why_not_term = M.Head(why_not_compute_scan)()
                why_not_target = why_not_term
                if M.IsPair(why_not_term)() is M.truth_value:
                    if M.Compare(
                        M.Head(why_not_term)(), M.Char("not"),
                    )() is M.truth_value:
                        if M.IdentityCompare(
                            M.Tail(why_not_term)(), M.EmptyList,
                        )() is M.false_value:
                            why_not_target = M.Head(
                                M.Tail(why_not_term)(),
                            )()
                why_not_verdict = _computed_divisibility(
                    why_not_target,
                )
                if M.IdentityCompare(
                    why_not_verdict, M.EmptyList,
                )() is M.false_value:
                    if M.Compare(
                        M.Head(why_not_verdict)(), M.Char("holds"),
                    )() is M.truth_value:
                        why_not_facts = M.Pair(
                            why_not_target, why_not_facts,
                        )
                        why_not_computed_lines.append(
                            "the division in it is exact",
                        )
                    else:
                        why_not_facts = M.Pair(
                            M.Pair(
                                M.Char("not"),
                                M.Pair(
                                    why_not_target, M.EmptyList,
                                ),
                            ),
                            why_not_facts,
                        )
                        why_not_computed_lines.append(
                            "the division in it leaves remainder "
                            + _words_of_value_text(
                                str(
                                    M.Head(
                                        M.Tail(why_not_verdict)(),
                                    )(),
                                ),
                            ),
                        )
                why_not_compute_scan = M.Tail(
                    why_not_compute_scan,
                )()
            # The rules that would conclude the goal, each with the
            # premises the working set does not carry.
            why_not_rule_lines = []
            why_not_match_scan = why_not_rules
            while M.IdentityCompare(
                why_not_match_scan, M.EmptyList,
            )() is M.false_value:
                why_not_rule = M.Head(why_not_match_scan)()
                why_not_replacement = P.RuleReplacement(
                    why_not_rule,
                )()
                if M.IsPair(why_not_replacement)() is M.truth_value:
                    if M.Compare(
                        M.Head(why_not_replacement)(), why_not_head,
                    )() is M.truth_value:
                        unmet_renders = []
                        unmet_scan = P.RulePremises(why_not_rule)()
                        while M.IdentityCompare(
                            unmet_scan, M.EmptyList,
                        )() is M.false_value:
                            unmet_premise = M.Head(unmet_scan)()
                            unmet_bindings = P.JoinPremises(
                                M.Pair(unmet_premise, M.EmptyList),
                                why_not_facts,
                                M.EmptyList,
                            )()
                            if M.IdentityCompare(
                                unmet_bindings, M.EmptyList,
                            )() is M.truth_value:
                                unmet_renders.append(
                                    M.PrettyTerm(
                                        unmet_premise, registry,
                                    )(),
                                )
                            unmet_scan = M.Tail(unmet_scan)()
                        if unmet_renders:
                            why_not_rule_lines.append(
                                P.PrettyRule(
                                    why_not_rule, M.AllConstructors,
                                )()
                                + " is missing "
                                + ", ".join(unmet_renders)
                            )
                why_not_match_scan = M.Tail(why_not_match_scan)()
            # The splits whose branches would decide the goal.
            why_not_split_lines = []
            why_not_split_scan = G.InstalledCaseSplits(
                learned_version,
            )()
            while M.IdentityCompare(
                why_not_split_scan, M.EmptyList,
            )() is M.false_value:
                why_not_split = M.Head(why_not_split_scan)()
                why_not_candidates = M.Head(
                    M.Tail(
                        G.CaseSplitExactlyOne(why_not_split)(),
                    )(),
                )()
                why_not_candidate_scan = why_not_candidates
                while M.IdentityCompare(
                    why_not_candidate_scan, M.EmptyList,
                )() is M.false_value:
                    why_not_candidate = M.Head(
                        why_not_candidate_scan,
                    )()
                    if M.IsPair(why_not_candidate)() is M.truth_value:
                        if M.Compare(
                            M.Head(why_not_candidate)(),
                            why_not_head,
                        )() is M.truth_value:
                            candidate_renders = []
                            render_candidate_scan = why_not_candidates
                            while M.IdentityCompare(
                                render_candidate_scan, M.EmptyList,
                            )() is M.false_value:
                                candidate_renders.append(
                                    M.PrettyTerm(
                                        M.Head(
                                            render_candidate_scan,
                                        )(),
                                        registry,
                                    )(),
                                )
                                render_candidate_scan = M.Tail(
                                    render_candidate_scan,
                                )()
                            why_not_split_lines.append(
                                "the case split over "
                                + ", ".join(candidate_renders)
                                + " speaks it; its other branches"
                                + " are not refuted"
                            )
                            why_not_candidate_scan = M.EmptyList
                        else:
                            why_not_candidate_scan = M.Tail(
                                why_not_candidate_scan,
                            )()
                    else:
                        why_not_candidate_scan = M.Tail(
                            why_not_candidate_scan,
                        )()
                why_not_split_scan = M.Tail(why_not_split_scan)()
            # The elimination itself is checked with the same
            # machinery the query uses: when the split would conclude,
            # the reply says so instead of listing gaps.
            why_not_relevant_reversed = M.EmptyList
            why_not_relevant_scan = G.InstalledCaseSplits(
                learned_version,
            )()
            while M.IdentityCompare(
                why_not_relevant_scan, M.EmptyList,
            )() is M.false_value:
                why_not_relevant_candidates = M.Head(
                    M.Tail(
                        G.CaseSplitExactlyOne(
                            M.Head(why_not_relevant_scan)(),
                        )(),
                    )(),
                )()
                why_not_candidate_scan = why_not_relevant_candidates
                while M.IdentityCompare(
                    why_not_candidate_scan, M.EmptyList,
                )() is M.false_value:
                    if M.IsPair(
                        M.Head(why_not_candidate_scan)(),
                    )() is M.truth_value:
                        if M.Compare(
                            M.Head(
                                M.Head(why_not_candidate_scan)(),
                            )(),
                            why_not_head,
                        )() is M.truth_value:
                            why_not_relevant_reversed = M.Pair(
                                M.Head(why_not_relevant_scan)(),
                                why_not_relevant_reversed,
                            )
                            why_not_candidate_scan = M.EmptyList
                        else:
                            why_not_candidate_scan = M.Tail(
                                why_not_candidate_scan,
                            )()
                    else:
                        why_not_candidate_scan = M.Tail(
                            why_not_candidate_scan,
                        )()
                why_not_relevant_scan = M.Tail(
                    why_not_relevant_scan,
                )()
            if M.IdentityCompare(
                why_not_relevant_reversed, M.EmptyList,
            )() is M.false_value:
                why_not_case = G.CaseSplitQuery(
                    why_not_facts,
                    why_not_rules,
                    M.Reverse(why_not_relevant_reversed)(),
                    why_not_goal,
                )()
                if M.IdentityCompare(
                    M.Head(why_not_case)(), M.truth_value,
                )() is M.truth_value:
                    return (
                        why_not_text + " does derive: the case"
                        + " split leaves it the one standing branch."
                        + " Ask 'query: " + why_not_text + "' again."
                    )
            reply_parts = []
            if why_not_computed_lines:
                reply_parts.append(
                    "; ".join(why_not_computed_lines)
                )
            if why_not_rule_lines:
                reply_parts.append(
                    "; ".join(why_not_rule_lines)
                )
            if why_not_split_lines:
                reply_parts.append(
                    "; ".join(why_not_split_lines)
                )
            if not reply_parts:
                return (
                    "Nothing concludes " + why_not_text
                    + ": no taught rule's conclusion and no case"
                    + " split's branch speaks '"
                    + str(why_not_head())
                    + "'. Teach a rule that concludes it, or a case"
                    + " split over it."
                )
            return (
                why_not_text + " does not derive: "
                + "; ".join(reply_parts) + "."
            )
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
            # A ground arithmetic equation is computed, not trusted:
            # the machine's own numbers check same(add(times(two,
            # three), one), seven) before it is recorded, and a false
            # equation is refused rather than learned.
            equation_target = fact
            equation_negated = M.false_value
            equation_computed_line = ""
            if M.IsPair(fact)() is M.truth_value:
                if M.Compare(
                    M.Head(fact)(), M.Char("not"),
                )() is M.truth_value:
                    if M.IdentityCompare(
                        M.Tail(fact)(), M.EmptyList,
                    )() is M.false_value:
                        equation_target = M.Head(
                            M.Tail(fact)(),
                        )()
                        equation_negated = M.truth_value
            equation_check = _verify_ground_equation(equation_target)
            if M.IdentityCompare(
                equation_check, M.EmptyList,
            )() is M.false_value:
                if M.Compare(
                    M.Head(equation_check)(), M.Char("differs"),
                )() is M.truth_value:
                    if M.IdentityCompare(
                        equation_negated, M.truth_value,
                    )() is M.truth_value:
                        equation_computed_line = (
                            " Computed: the left side computes to "
                            + _words_of_value_text(
                                str(
                                    M.Head(
                                        M.Tail(equation_check)(),
                                    )(),
                                ),
                            )
                            + ", not the right side."
                        )
                    else:
                        _persist_talk_state()
                        return (
                            "That is not so: the left side computes to "
                            + _words_of_value_text(
                                str(
                                    M.Head(
                                        M.Tail(equation_check)(),
                                    )(),
                                ),
                            )
                            + ". I will not record it."
                        )
                else:
                    if M.IdentityCompare(
                        equation_negated, M.truth_value,
                    )() is M.truth_value:
                        _persist_talk_state()
                        return (
                            "That is not so: the two sides are equal."
                            + " I will not record it."
                        )
            # A ground divisibility claim is computed the same way: the
            # machine divides N by A itself, refuses a claim its own
            # division contradicts, and confirms one it verifies.
            division_computed_line = ""
            division_target = fact
            division_negated = M.false_value
            if M.IsPair(fact)() is M.truth_value:
                if M.Compare(
                    M.Head(fact)(), M.Char("not"),
                )() is M.truth_value:
                    if M.IdentityCompare(
                        M.Tail(fact)(), M.EmptyList,
                    )() is M.false_value:
                        division_target = M.Head(
                            M.Tail(fact)(),
                        )()
                        division_negated = M.truth_value
            division_verdict = _computed_divisibility(
                division_target,
            )
            if M.IdentityCompare(
                division_verdict, M.EmptyList,
            )() is M.false_value:
                division_holds = M.IdentityCompare(
                    M.Compare(
                        M.Head(division_verdict)(), M.Char("holds"),
                    )(),
                    M.truth_value,
                )() is M.truth_value
                division_remainder = _words_of_value_text(
                    str(
                        M.Head(
                            M.Tail(division_verdict)(),
                        )(),
                    ),
                )
                if M.IdentityCompare(
                    division_negated, M.truth_value,
                )() is M.truth_value:
                    if division_holds:
                        _persist_talk_state()
                        return (
                            "That is not so: the division is exact."
                            + " I will not record it."
                        )
                    division_computed_line = (
                        " Computed: the machine's own division"
                        + " leaves remainder "
                        + division_remainder + "."
                    )
                else:
                    if division_holds:
                        division_computed_line = (
                            " Computed: the machine's own division"
                            + " is exact."
                        )
                    else:
                        _persist_talk_state()
                        return (
                            "That is not so: the division leaves"
                            + " remainder " + division_remainder
                            + ", not zero. I will not record it."
                        )
            installed_fact = G.InstallTaughtFact(learned_version, fact)()
            learned_version = M.Head(installed_fact)()
            if record:
                _log_lesson(line)
            inspection = G.InspectGaps(
                pending_gaps,
                last_goal,
                learned_version,
                fact,
            )()
            learned_version = M.Head(inspection)()
            pending_gaps = M.Head(M.Tail(inspection)())()
            gap_ask = M.Head(
                M.Tail(M.Tail(M.Tail(inspection)())())(),
            )()
            if M.IdentityCompare(gap_ask, M.EmptyList)() is M.false_value:
                learned_version = G.InstallAskedQuestion(
                    learned_version,
                    G.AskedQuestion(
                        M.Head(M.Tail(gap_ask)())(),
                        M.Head(gap_ask)(),
                        M.Head(M.Tail(M.Tail(gap_ask)())())(),
                    )(),
                )()
                _persist_talk_state()
                return _speak_chain(
                    M.Head(M.Tail(M.Head(gap_ask)())())(),
                )
            _persist_talk_state()
            computed_line = ""
            if M.IdentityCompare(
                equation_check, M.EmptyList,
            )() is M.false_value:
                if M.IdentityCompare(
                    equation_negated, M.truth_value,
                )() is M.false_value:
                    computed_line = (
                        " Computed: the machine's own numbers confirm it."
                    )
            computed_line = (
                computed_line + equation_computed_line
            )
            computed_line = computed_line + division_computed_line
            acknowledged = G.RenderAcknowledgement(fact)()
            if M.IdentityCompare(acknowledged, M.EmptyList)() is M.false_value:
                return _speak_chain(
                    M.Head(M.Tail(acknowledged)())(),
                ) + computed_line
            return "Recorded fact: " + line[5:].strip() + computed_line
        if lowered.startswith("keep ") and M.IdentityCompare(
            pending_process, M.EmptyList,
        )() is M.truth_value:
            # A keep/strike answer with no process awaiting it: either
            # it misses the question on the table, or nothing does.
            if M.IdentityCompare(
                pending_asks, M.EmptyList,
            )() is M.false_value:
                return (
                    "A keep/strike answer does not fit the question on"
                    + " the table." + _ask_next_line()
                )
            return "No process is awaiting a keep/strike answer."
        if M.IdentityCompare(pending_process, M.EmptyList)() is M.false_value:
            if lowered.startswith("keep "):
                # The operational answer to the process ask: keep and
                # strike clauses, each naming a concept from the store.
                # The nouns resolve through the singular fold against
                # the taught definitions; each clause becomes a rule
                # tying the process verb to the resolved concept.
                defined_term = pending_process
                pending_process = M.EmptyList
                # A semicolon separates clauses exactly as a comma
                # does; the reading policy does not blank it, so the
                # line is normalized before the words are read.
                answer_words = _words(line.replace(";", ","))
                clauses_reversed = M.EmptyList
                noun_reversed = M.EmptyList
                clause_mode = M.EmptyList
                word_scan = answer_words
                while M.IdentityCompare(
                    word_scan, M.EmptyList,
                )() is M.false_value:
                    answer_word = M.Head(word_scan)()
                    if M.Compare(answer_word, M.Char(","))() is M.truth_value:
                        if M.IdentityCompare(
                            clause_mode, M.EmptyList,
                        )() is M.false_value:
                            if M.IdentityCompare(
                                noun_reversed, M.EmptyList,
                            )() is M.false_value:
                                clauses_reversed = M.Pair(
                                    M.Pair(
                                        clause_mode,
                                        M.Reverse(noun_reversed)(),
                                    ),
                                    clauses_reversed,
                                )
                        clause_mode = M.EmptyList
                        noun_reversed = M.EmptyList
                    elif M.Compare(answer_word, M.Char("keep"))() is M.truth_value:
                        clause_mode = answer_word
                    elif M.Compare(answer_word, M.Char("strike"))() is M.truth_value:
                        clause_mode = answer_word
                    else:
                        if M.IdentityCompare(
                            clause_mode, M.EmptyList,
                        )() is M.false_value:
                            noun_reversed = M.Pair(
                                answer_word, noun_reversed,
                            )
                    word_scan = M.Tail(word_scan)()
                if M.IdentityCompare(
                    clause_mode, M.EmptyList,
                )() is M.false_value:
                    if M.IdentityCompare(
                        noun_reversed, M.EmptyList,
                    )() is M.false_value:
                        clauses_reversed = M.Pair(
                            M.Pair(
                                clause_mode,
                                M.Reverse(noun_reversed)(),
                            ),
                            clauses_reversed,
                        )
                clauses = M.Reverse(clauses_reversed)()
                unresolved = M.EmptyList
                rule_texts = []
                clause_scan = clauses
                while M.IdentityCompare(
                    clause_scan, M.EmptyList,
                )() is M.false_value:
                    clause = M.Head(clause_scan)()
                    clause_verb = M.Head(clause)()
                    noun_chain = M.Tail(clause)()
                    if M.IdentityCompare(
                        noun_chain, M.EmptyList,
                    )() is M.truth_value:
                        clause_scan = M.Tail(clause_scan)()
                    else:
                        noun_word = M.Head(noun_chain)()
                        resolved = noun_word
                        if M.IdentityCompare(
                            G.DefinitionFor(learned_version, resolved)(),
                            M.EmptyList,
                        )() is M.truth_value:
                            singular = G.WordSingular(resolved)()
                            if M.IdentityCompare(
                                singular, M.EmptyList,
                            )() is M.false_value:
                                if M.IdentityCompare(
                                    G.DefinitionFor(
                                        learned_version, singular,
                                    )(),
                                    M.EmptyList,
                                )() is M.truth_value:
                                    resolved = noun_word
                                else:
                                    resolved = singular
                        if M.IdentityCompare(
                            G.DefinitionFor(learned_version, resolved)(),
                            M.EmptyList,
                        )() is M.truth_value:
                            unresolved = M.Pair(resolved, unresolved)
                        else:
                            rule_texts.append(
                                str(resolved())
                                + "(x) -> "
                                + str(clause_verb())
                                + "(x)"
                            )
                    clause_scan = M.Tail(clause_scan)()
                if unresolved is not M.EmptyList:
                    pending_process = defined_term
                    spoken_unresolved = []
                    unresolved_scan = unresolved
                    while M.IdentityCompare(
                        unresolved_scan, M.EmptyList,
                    )() is M.false_value:
                        spoken_unresolved.append(
                            str(M.Head(unresolved_scan)()())
                        )
                        unresolved_scan = M.Tail(unresolved_scan)()
                    return (
                        "I do not know the concept(s) "
                        + ", ".join(spoken_unresolved)
                        + "; define them first." + _ask_next_line()
                    )
                installed_lines = []
                for rule_text in rule_texts:
                    known_constructors = G.RuleConstructors(
                        learned_version,
                        pack_concepts,
                    )()
                    parsed_process_rule = G.ParseRuleText(
                        rule_text,
                        reading_policy,
                        reading_digits,
                        known_constructors,
                        M.false_value,
                    )()
                    process_rule = M.Head(parsed_process_rule)()
                    if M.IdentityCompare(
                        process_rule, M.EmptyList,
                    )() is M.truth_value:
                        return (
                            "I could not turn '" + rule_text
                            + "' into a rule."
                        )
                    learned_version = G.GraphVersion(
                        M.Pair(
                            M.Pair(
                                M.Char("taught-rule"),
                                M.Pair(
                                    P.RulePremises(process_rule)(),
                                    M.Pair(
                                        P.RuleReplacement(process_rule)(),
                                        M.EmptyList,
                                    ),
                                ),
                            ),
                            M.Pair(
                                M.Pair(
                                    M.Char("process-rule"),
                                    M.Pair(
                                        defined_term,
                                        M.Pair(
                                            P.RulePremises(process_rule)(),
                                            M.Pair(
                                                P.RuleReplacement(
                                                    process_rule,
                                                )(),
                                                M.EmptyList,
                                            ),
                                        ),
                                    ),
                                ),
                                G.GraphNodes(learned_version)(),
                            ),
                        ),
                        G.GraphEdges(learned_version)(),
                        G.GraphVersionInvariants(learned_version)(),
                    )()
                    installed_lines.append(rule_text)
                if record:
                    _log_lesson(line)
                _persist_talk_state()
                _pop_ask("process")
                return (
                    "The process of '" + str(defined_term()) + "' is"
                    + " recorded: "
                    + "; ".join(installed_lines)
                    + "." + _ask_next_line()
                )
        if lowered.startswith("lemma:"):
            lemma_text = line[6:].strip()
            polynomial_lemma = G.ParsePolynomialInequalityText(
                lemma_text, reading_digits,
            )()
            if M.IdentityCompare(
                polynomial_lemma, M.EmptyList,
            )() is M.false_value:
                schema_start = M.Pair(
                    M.VarTag,
                    M.Pair(M.Char("?lemma-start"), M.EmptyList),
                )
                schema = G.TaughtDerivationSchema(
                    schema_start,
                    polynomial_lemma,
                    M.Pair(
                        M.Char("human-taught-lemma"), M.EmptyList,
                    ),
                )()
                learned_version = G.GraphVersion(
                    M.Pair(schema, G.GraphNodes(learned_version)()),
                    G.GraphEdges(learned_version)(),
                    G.GraphVersionInvariants(learned_version)(),
                )()
                if record:
                    _log_lesson(line)
                _persist_talk_state()
                return (
                    "Recorded the symbolic inequality lemma: "
                    + M.PrettyTerm(polynomial_lemma, registry)() + "."
                )
            known_constructors = G.RuleConstructors(
                learned_version,
                pack_concepts,
            )()
            parsed_lemma = G.ParseRuleText(
                lemma_text,
                reading_policy,
                reading_digits,
                known_constructors,
                M.false_value,
            )()
            lemma_rule = M.Head(parsed_lemma)()
            if M.IdentityCompare(lemma_rule, M.EmptyList)() is M.truth_value:
                return (
                    "I could not read that lemma as a rule; use"
                    + " 'lemma: P(x), Q(x) -> R(x)'."
                )
            learned_version = G.GraphVersion(
                M.Pair(
                    M.Pair(
                        M.Char("taught-rule"),
                        M.Pair(
                            P.RulePremises(lemma_rule)(),
                            M.Pair(
                                P.RuleReplacement(lemma_rule)(),
                                M.EmptyList,
                            ),
                        ),
                    ),
                    M.Pair(
                        M.Pair(
                            M.Char("lemma-rule"),
                            M.Pair(
                                P.RulePremises(lemma_rule)(),
                                M.Pair(
                                    P.RuleReplacement(lemma_rule)(),
                                    M.EmptyList,
                                ),
                            ),
                        ),
                        G.GraphNodes(learned_version)(),
                    ),
                ),
                G.GraphEdges(learned_version)(),
                G.GraphVersionInvariants(learned_version)(),
            )()
            if record:
                _log_lesson(line)
            _persist_talk_state()
            return (
                "The lemma turned into a rule: "
                + P.PrettyRule(lemma_rule, M.AllConstructors)()
                + "."
            )
        if lowered.startswith("prove that"):
            prove_target = line[11:].strip()
            # The two sides resolve by their provenance families: the
            # process rules installed from a keep/strike answer, and
            # the lemma rules installed by lemma:.
            process_rules = M.EmptyList
            lemma_rules = M.EmptyList
            substrate_rules = M.EmptyList
            rule_scan = G.InstalledTaughtRules(learned_version)()
            version_scan = G.GraphNodes(learned_version)()
            # provenance nodes carry the raw premises/replacement pairs
            prov_scan = version_scan
            lemma_pairs = M.EmptyList
            process_pairs = M.EmptyList
            while M.IdentityCompare(
                prov_scan, M.EmptyList,
            )() is M.false_value:
                prov_node = M.Head(prov_scan)()
                prov_scan = M.Tail(prov_scan)()
                if M.IsPair(prov_node)() is M.truth_value:
                    if M.Compare(
                        M.Head(prov_node)(), M.Char("lemma-rule"),
                    )() is M.truth_value:
                        lemma_pairs = M.Pair(
                            M.Pair(
                                M.Head(M.Tail(prov_node)())(),
                                M.Pair(
                                    M.Head(
                                        M.Tail(M.Tail(prov_node)())(),
                                    )(),
                                    M.EmptyList,
                                ),
                            ),
                            lemma_pairs,
                        )
                    elif M.Compare(
                        M.Head(prov_node)(), M.Char("process-rule"),
                    )() is M.truth_value:
                        process_pairs = M.Pair(
                            M.Pair(
                                M.Head(M.Tail(M.Tail(prov_node)())())(),
                                M.Pair(
                                    M.Head(
                                        M.Tail(
                                            M.Tail(
                                                M.Tail(prov_node)(),
                                            )(),
                                        )(),
                                    )(),
                                    M.EmptyList,
                                ),
                            ),
                            process_pairs,
                        )
            if M.IdentityCompare(lemma_pairs, M.EmptyList)() is M.truth_value:
                return (
                    "I have no lemma to apply; teach it with 'lemma:'."
                )
            if M.IdentityCompare(
                process_pairs, M.EmptyList,
            )() is M.truth_value:
                return (
                    "I have no process rules; answer a process question"
                    + " with 'keep ..., strike ...'."
                )
            # Backward closure: a predicate is process-reachable
            # when a rule concludes it; the closure walks one level
            # through the installed substrate. The leq family is
            # carried by the substrate (totality, transitivity, the
            # cofactor bridge) and the certified induction licenses
            # the bound.
            def _premise_heads_of(pair_chain):
                heads = M.EmptyList
                scan = pair_chain
                while M.IdentityCompare(
                    scan, M.EmptyList,
                )() is M.false_value:
                    one_pair = M.Head(scan)()
                    prem_scan = M.Head(one_pair)()
                    while M.IdentityCompare(
                        prem_scan, M.EmptyList,
                    )() is M.false_value:
                        prem = M.Head(prem_scan)()
                        if M.IsPair(prem)() is M.truth_value:
                            heads = M.Pair(M.Head(prem)(), heads)
                        prem_scan = M.Tail(prem_scan)()
                    scan = M.Tail(scan)()
                return heads
            def _closure_heads(seed_heads):
                closure = seed_heads
                seed_scan = seed_heads
                while M.IdentityCompare(
                    seed_scan, M.EmptyList,
                )() is M.false_value:
                    seed_head = M.Head(seed_scan)()
                    idx_scan = head_index
                    while M.IdentityCompare(
                        idx_scan, M.EmptyList,
                    )() is M.false_value:
                        idx_entry = M.Head(idx_scan)()
                        if M.Compare(
                            M.Head(idx_entry)(), seed_head,
                        )() is M.truth_value:
                            # add the concluding rule's premise heads
                            add_scan = P.RulePremises(
                                M.Head(M.Tail(idx_entry)())(),
                            )()
                            while M.IdentityCompare(
                                add_scan, M.EmptyList,
                            )() is M.false_value:
                                add_prem = M.Head(add_scan)()
                                if M.IsPair(add_prem)() is M.truth_value:
                                    closure = M.Pair(
                                        M.Head(add_prem)(), closure,
                                    )
                                add_scan = M.Tail(add_scan)()
                            idx_scan = M.EmptyList
                        else:
                            idx_scan = M.Tail(idx_scan)()
                    seed_scan = M.Tail(seed_scan)()
                return closure
            def _covers(covering, wanted_head):
                scan = covering
                while M.IdentityCompare(
                    scan, M.EmptyList,
                )() is M.false_value:
                    if M.Compare(
                        M.Head(scan)(), wanted_head,
                    )() is M.truth_value:
                        return True
                    scan = M.Tail(scan)()
                return False
            # installed rules indexed by replacement head
            head_index = M.EmptyList
            rule_walk = G.InstalledTaughtRules(learned_version)()
            while M.IdentityCompare(
                rule_walk, M.EmptyList,
            )() is M.false_value:
                installed_rule = M.Head(rule_walk)()
                replacement = P.RuleReplacement(installed_rule)()
                if M.IsPair(replacement)() is M.truth_value:
                    head_index = M.Pair(
                        M.Pair(
                            M.Head(replacement)(),
                            M.Pair(installed_rule, M.EmptyList),
                        ),
                        head_index,
                    )
                rule_walk = M.Tail(rule_walk)()
            lemma_heads = _premise_heads_of(lemma_pairs)
            process_heads = _premise_heads_of(process_pairs)
            process_closure = _closure_heads(process_heads)
            # Direction A: every lemma premise is process-reachable or
            # carried by the order machinery.
            missing_a = M.EmptyList
            prem_scan = lemma_heads
            while M.IdentityCompare(
                prem_scan, M.EmptyList,
            )() is M.false_value:
                prem_head = M.Head(prem_scan)()
                if M.Compare(prem_head, M.Char("leq"))() is M.truth_value:
                    prem_scan = M.Tail(prem_scan)()
                else:
                    if _covers(process_closure, prem_head) is False:
                        missing_a = M.Pair(prem_head, missing_a)
                    prem_scan = M.Tail(prem_scan)()
            # Direction B: each process rule's premises are
            # lemma-derivable -- transitively, through the installed
            # substrate: a head is derivable when the lemma side
            # carries it, when the leq family's substrate concludes
            # it, or when a rule concluding it has derivable premises.
            # A process rule that is not derivable names the
            # contraposition it still needs.
            def _b_derivable(head, depth_text):
                if M.Compare(head, M.Char("leq"))() is M.truth_value:
                    return True
                if _covers(lemma_heads, head) is True:
                    return True
                if G.GMPEqualText(depth_text, "0")() is M.truth_value:
                    return False
                next_depth = G.GMPSubText(depth_text, "1")()
                idx_scan = head_index
                while M.IdentityCompare(
                    idx_scan, M.EmptyList,
                )() is M.false_value:
                    idx_entry = M.Head(idx_scan)()
                    if M.Compare(
                        M.Head(idx_entry)(), head,
                    )() is M.truth_value:
                        prem_scan = P.RulePremises(
                            M.Head(M.Tail(idx_entry)())(),
                        )()
                        all_derivable = True
                        while M.IdentityCompare(
                            prem_scan, M.EmptyList,
                        )() is M.false_value:
                            prem = M.Head(prem_scan)()
                            if M.IsPair(prem)() is M.truth_value:
                                if _b_derivable(
                                    M.Head(prem)(), next_depth,
                                ) is False:
                                    all_derivable = False
                                    prem_scan = M.EmptyList
                                else:
                                    prem_scan = M.Tail(prem_scan)()
                            else:
                                prem_scan = M.Tail(prem_scan)()
                        if all_derivable is True:
                            return True
                        idx_scan = M.Tail(idx_scan)()
                    else:
                        idx_scan = M.Tail(idx_scan)()
                return False
            proven_process_pairs = M.EmptyList
            contraposition_pairs = M.EmptyList
            # The derivation search depth, as a machine text so the
            # reply can state the bound the check actually used.
            b_depth_text = "4"
            pair_scan = process_pairs
            while M.IdentityCompare(
                pair_scan, M.EmptyList,
            )() is M.false_value:
                process_pair = M.Head(pair_scan)()
                pp_heads = _premise_heads_of(
                    M.Pair(process_pair, M.EmptyList),
                )
                b_ok = M.truth_value
                head_scan = pp_heads
                while M.IdentityCompare(
                    head_scan, M.EmptyList,
                )() is M.false_value:
                    pp_head = M.Head(head_scan)()
                    if _b_derivable(pp_head, b_depth_text) is False:
                        b_ok = M.false_value
                        head_scan = M.EmptyList
                    else:
                        head_scan = M.Tail(head_scan)()
                if M.IdentityCompare(b_ok, M.truth_value)() is M.truth_value:
                    proven_process_pairs = M.Pair(
                        process_pair, proven_process_pairs,
                    )
                else:
                    contraposition_pairs = M.Pair(
                        process_pair, contraposition_pairs,
                    )
                pair_scan = M.Tail(pair_scan)()
            certificate_present = M.false_value
            certificate_node = M.EmptyList
            cert_scan = G.GraphNodes(learned_version)()
            while M.IdentityCompare(
                cert_scan, M.EmptyList,
            )() is M.false_value:
                cert_node = M.Head(cert_scan)()
                cert_scan = M.Tail(cert_scan)()
                if M.IsPair(cert_node)() is M.truth_value:
                    if M.Compare(
                        M.Head(cert_node)(), M.Char("inductive-law"),
                    )() is M.truth_value:
                        certificate_present = M.truth_value
                        certificate_node = cert_node
                        cert_scan = M.EmptyList
            def _chain_text(chain_heads):
                spoken = []
                scan = chain_heads
                while M.IdentityCompare(
                    scan, M.EmptyList,
                )() is M.false_value:
                    spoken.append(str(M.Head(scan)()()))
                    scan = M.Tail(scan)()
                return ", ".join(spoken)
            if M.IdentityCompare(
                missing_a, M.EmptyList,
            )() is M.false_value:
                return (
                    "The process side does not yet reach the lemma's"
                    + " premises: missing "
                    + _chain_text(missing_a)
                    + "."
                )
            if M.IdentityCompare(
                proven_process_pairs, M.EmptyList,
            )() is M.truth_value:
                return (
                    "No process rule is reachable from the lemma side;"
                    + " teach the connecting substrate first."
                )
            if M.IdentityCompare(
                certificate_present, M.false_value,
            )() is M.truth_value:
                return (
                    "The bound needs a certified induction; teach the"
                    + " base and step and certify with 'induction:'."
                )
            # record the equivalence proof
            certificate_record = M.Pair(
                M.Char("certificate"),
                M.Pair(
                    lemma_pairs,
                    M.Pair(certificate_node, M.EmptyList),
                ),
            )
            learned_version = G.GraphVersion(
                M.Pair(
                    M.Pair(
                        M.Char("equivalence-proven"),
                        M.Pair(
                            lemma_pairs,
                            M.Pair(
                                M.Reverse(proven_process_pairs)(),
                                M.Pair(
                                    M.Reverse(contraposition_pairs)(),
                                    M.EmptyList,
                                ),
                            ),
                        ),
                    ),
                    M.Pair(
                        certificate_record,
                        G.GraphNodes(learned_version)(),
                    ),
                ),
                G.GraphEdges(learned_version)(),
                G.GraphVersionInvariants(learned_version)(),
            )()
            if proof_runtime is M.EmptyList:
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
            proof_runtime.graph.add_derivation(
                lemma_pairs,
                M.Char(prove_target),
                certificate_node,
            )
            if record:
                _log_lesson(line)
            _persist_talk_state()
            # The caption states only what the checks established:
            # every rule is rendered from the recorded pairs, the
            # certificate from its node, and the remaining rules are
            # the pairs the derivation check rejected. No sentence
            # asserts content the graph did not compute.
            def _pair_rule_renders(pair_chain):
                rendered = []
                render_scan = pair_chain
                while M.IdentityCompare(
                    render_scan, M.EmptyList,
                )() is M.false_value:
                    render_pair = M.Head(render_scan)()
                    rendered.append(
                        P.PrettyRule(
                            P.MultiRule(
                                M.Head(render_pair)(),
                                M.Head(M.Tail(render_pair)())(),
                            )(),
                            M.AllConstructors,
                        )()
                    )
                    render_scan = M.Tail(render_scan)()
                return rendered
            lemma_render = "; ".join(_pair_rule_renders(lemma_pairs))
            proven_render = "; ".join(
                _pair_rule_renders(M.Reverse(proven_process_pairs)()),
            )
            contra_render = "; ".join(
                _pair_rule_renders(M.Reverse(contraposition_pairs)()),
            )
            certificate_line = ""
            if M.IdentityCompare(
                certificate_node, M.EmptyList,
            )() is M.false_value:
                cert_claim = M.Head(M.Tail(certificate_node)())()
                cert_bases = M.Head(
                    M.Tail(M.Tail(certificate_node)())(),
                )()
                cert_steps = M.Head(
                    M.Tail(M.Tail(M.Tail(certificate_node)())())(),
                )()
                base_renders = []
                base_scan = cert_bases
                while M.IdentityCompare(
                    base_scan, M.EmptyList,
                )() is M.false_value:
                    # Each entry is a premises/replacement pair; a
                    # certificate written before pairs were stored
                    # carries an opaque atom instead, and rendering
                    # skips what the wire could not carry.
                    base_entry = M.Head(base_scan)()
                    try:
                        base_renders.append(
                            P.PrettyRule(
                                P.MultiRule(
                                    M.Head(base_entry)(),
                                    M.Head(M.Tail(base_entry)())(),
                                )(),
                                M.AllConstructors,
                            )()
                        )
                    except Exception:
                        pass
                    base_scan = M.Tail(base_scan)()
                step_renders = []
                step_scan = cert_steps
                while M.IdentityCompare(
                    step_scan, M.EmptyList,
                )() is M.false_value:
                    step_entry = M.Head(step_scan)()
                    try:
                        step_renders.append(
                            P.PrettyRule(
                                P.MultiRule(
                                    M.Head(step_entry)(),
                                    M.Head(M.Tail(step_entry)())(),
                                )(),
                                M.AllConstructors,
                            )()
                        )
                    except Exception:
                        pass
                    step_scan = M.Tail(step_scan)()
                if base_renders or step_renders:
                    certificate_line = (
                        " The recorded induction over '"
                        + str(cert_claim()) + "': base "
                        + "; ".join(base_renders)
                        + "; step "
                        + "; ".join(step_renders) + "."
                    )
                else:
                    certificate_line = (
                        " The recorded induction over '"
                        + str(cert_claim()) + "'."
                    )
            contra_line = ""
            if contra_render != "":
                contra_line = (
                    " The remaining process rule(s) -- " + contra_render
                    + " -- have premises that did not derive from the"
                    + " lemma side under the installed rules (search"
                    + " depth " + b_depth_text + ")."
                )
            return (
                "Proven: " + prove_target + ", on the recorded rules."
                + " Every premise of the lemma rules -- " + lemma_render
                + " -- except the leq premises is reachable from the"
                + " process side. Every premise of the proven process"
                + " rules -- "
                + proven_render + " -- derives from the lemma side"
                + " under the installed rules." + certificate_line
                + contra_line
                + " The proof is recorded; ask 'why are these two"
                + " definitions equivalent?'"
            )
        if lowered.startswith("rule:"):
            if M.IdentityCompare(
                pending_rule, M.EmptyList,
            )() is M.false_value:
                return "Please approve or reject the pending rule first."
            known_constructors = G.RuleConstructors(
                learned_version,
                pack_concepts,
            )()
            case_prefix = M.Char(line[5:].strip()[:6].lower())
            if M.Compare(case_prefix, M.Char("one of"))() is M.truth_value:
                parsed_case = G.ParseRuleText(
                    line[5:].strip()[6:].strip(),
                    reading_policy,
                    reading_digits,
                    known_constructors,
                    M.Char("exactly-one"),
                )()
                case_split = M.Head(parsed_case)()
                case_reason = M.Head(M.Tail(parsed_case)())()
                if M.IdentityCompare(
                    case_split, M.EmptyList,
                )() is M.truth_value:
                    case_detail = M.EmptyList
                    if M.IsPair(case_reason)() is M.truth_value:
                        case_detail = M.Head(M.Tail(case_reason)())()
                    if M.IdentityCompare(
                        case_detail, M.EmptyList,
                    )() is M.false_value:
                        return (
                            "I could not parse that case split ("
                            + str(case_detail())
                            + "). Use one of P(a), Q(a), R(a)."
                        )
                    return "I could not parse that case split. Use one of P(a), Q(a), R(a)."
                exactly_one = G.CaseSplitExactlyOne(case_split)()
                split_warning = ""
                known_facts = G.InstalledTaughtFacts(learned_version)()
                known_rules = G.InstalledTaughtRules(learned_version)()
                split_check = G.CaseSplitQuery(
                    known_facts,
                    known_rules,
                    M.Pair(case_split, M.EmptyList),
                    M.EmptyList,
                )()
                if M.Compare(
                    M.Head(M.Tail(split_check)())(),
                    M.Char("all-branches-refuted"),
                )() is M.truth_value:
                    split_warning = (
                        " Warning: all branches of this split are already "
                        "refuted by the recorded facts."
                    )
                case_origin = M.Pair(
                    M.Char("case-split"),
                    M.Pair(exactly_one, M.EmptyList),
                )
                case_proposal = G.Proposal(
                    case_split,
                    case_origin,
                )()
                proposal_store = G.ProposalStoreSubmit(
                    proposal_store,
                    case_proposal,
                )()
                pending_rule = case_proposal
                if record:
                    _log_lesson(line)
                _persist_talk_state()
                return (
                    "I propose a case split over "
                    + line[5:].strip()[6:].strip()
                    + ". It creates one proof branch per candidate."
                    + split_warning
                    + " Approve? (yes/no)"
                )
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
            fresh_reversed = M.EmptyList
            rule_premises = P.RulePremises(rule)()
            rule_replacement = P.RuleReplacement(rule)()
            agenda_reversed = M.Pair(rule_replacement, M.EmptyList)
            premise_scan = rule_premises
            while M.IdentityCompare(
                premise_scan, M.EmptyList,
            )() is M.false_value:
                agenda_reversed = M.Pair(
                    M.Head(premise_scan)(), agenda_reversed,
                )
                premise_scan = M.Tail(premise_scan)()
            rule_term_scan = M.Reverse(agenda_reversed)()
            while M.IdentityCompare(
                rule_term_scan, M.EmptyList,
            )() is M.false_value:
                rule_term = M.Head(rule_term_scan)()
                rule_term_scan = M.Tail(rule_term_scan)()
                if M.IsPair(rule_term)() is M.truth_value:
                    rule_head = M.Head(rule_term)()
                    if M.IdentityCompare(
                        rule_head, M.VarTag,
                    )() is M.false_value:
                        head_known = M.false_value
                        constructor_scan = known_constructors
                        while M.IdentityCompare(
                            constructor_scan, M.EmptyList,
                        )() is M.false_value:
                            if M.Compare(
                                M.Head(
                                    M.Tail(M.Head(constructor_scan)())(),
                                )(),
                                rule_head,
                            )() is M.truth_value:
                                head_known = M.truth_value
                                constructor_scan = M.EmptyList
                            else:
                                constructor_scan = M.Tail(constructor_scan)()
                        if M.IdentityCompare(
                            head_known, M.false_value,
                        )() is M.truth_value:
                            already_listed = M.false_value
                            listed_scan = fresh_reversed
                            while M.IdentityCompare(
                                listed_scan, M.EmptyList,
                            )() is M.false_value:
                                if M.Compare(
                                    M.Head(listed_scan)(), rule_head,
                                )() is M.truth_value:
                                    already_listed = M.truth_value
                                    listed_scan = M.EmptyList
                                else:
                                    listed_scan = M.Tail(listed_scan)()
                            if M.IdentityCompare(
                                already_listed, M.false_value,
                            )() is M.truth_value:
                                fresh_reversed = M.Pair(
                                    rule_head, fresh_reversed,
                                )
                    argument_scan = M.Tail(rule_term)()
                    while M.IdentityCompare(
                        argument_scan, M.EmptyList,
                    )() is M.false_value:
                        nested_argument = M.Head(argument_scan)()
                        if M.IsPair(nested_argument)() is M.truth_value:
                            rule_term_scan = M.Pair(
                                nested_argument, rule_term_scan,
                            )
                        argument_scan = M.Tail(argument_scan)()
            fresh_predicates = M.Reverse(fresh_reversed)()
            fresh_text = ""
            fresh_scan = fresh_predicates
            while M.IdentityCompare(
                fresh_scan, M.EmptyList,
            )() is M.false_value:
                if fresh_text == "":
                    fresh_text = " It introduces the new predicate(s): "
                else:
                    fresh_text = fresh_text + ", "
                fresh_text = fresh_text + str(M.Head(fresh_scan)()())
                fresh_scan = M.Tail(fresh_scan)()
            if fresh_text != "":
                fresh_text = fresh_text + "."
            proposal = G.Proposal(law, rule_origin)()
            proposal_store = G.ProposalStoreSubmit(
                proposal_store,
                proposal,
            )()
            proposal_store = G.ProposalStoreAttach(
                proposal_store,
                proposal,
                G.JustifiedBy(
                    proposal,
                    M.Pair(
                        M.Char("surface"),
                        M.Pair(M.Char(line[5:].strip()), M.EmptyList),
                    ),
                )(),
            )()
            pending_rule = proposal
            if record:
                _log_lesson(line)
            _persist_talk_state()
            return (
                "I propose a deduction rule: "
                + line[5:].strip()
                + ". It keeps every premise and adds the conclusion."
                + fresh_text
                + " Approve? (yes/no)"
            )
        if lowered.startswith("induction:"):
            claim_text = line[10:].strip()
            claim = M.Char(claim_text)
            certified = G.CertifyInduction(claim, learned_version)()
            learned_version = M.Head(certified)()
            bases = M.Head(M.Tail(certified)())()
            steps = M.Head(M.Tail(M.Tail(certified)())())()
            universal = M.Head(
                M.Tail(M.Tail(M.Tail(certified)())())(),
            )()
            reason = M.Head(
                M.Tail(M.Tail(M.Tail(M.Tail(certified)())())())(),
            )()
            if M.IdentityCompare(reason, M.EmptyList)() is M.false_value:
                # When only the base is missing, the step is in hand
                # and the base follows from the step's own shape: the
                # claim at zero over the step's side premises. The
                # derived base is proposed, and the trainer decides.
                if M.Compare(
                    reason, M.Char("no-base"),
                )() is M.truth_value:
                    if M.IdentityCompare(
                        steps, M.EmptyList,
                    )() is M.false_value:
                        step_rule = M.Head(steps)()
                        step_replacement = P.RuleReplacement(
                            step_rule,
                        )()
                        if M.IsPair(
                            step_replacement,
                        )() is M.truth_value:
                            kept_reversed = M.EmptyList
                            premise_walk = P.RulePremises(step_rule)()
                            while M.IdentityCompare(
                                premise_walk, M.EmptyList,
                            )() is M.false_value:
                                step_premise = M.Head(premise_walk)()
                                keep_premise = M.truth_value
                                if M.IsPair(step_premise)() is M.truth_value:
                                    if M.Compare(
                                        M.Head(step_premise)(), claim,
                                    )() is M.truth_value:
                                        keep_premise = M.false_value
                                if M.IdentityCompare(
                                    keep_premise, M.truth_value,
                                )() is M.truth_value:
                                    kept_reversed = M.Pair(
                                        step_premise, kept_reversed,
                                    )
                                premise_walk = M.Tail(premise_walk)()
                            kept_premises = M.Reverse(kept_reversed)()
                            base_replacement = M.Pair(
                                claim,
                                M.Pair(
                                    M.Char("zero"),
                                    M.Tail(
                                        M.Tail(step_replacement)(),
                                    )(),
                                ),
                            )
                            if M.IdentityCompare(
                                kept_premises, M.EmptyList,
                            )() is M.false_value:
                                base_rule = P.MultiRule(
                                    kept_premises, base_replacement,
                                )()
                                base_law = G.CompileDeductionToLaw(
                                    base_rule,
                                )()
                                if M.IdentityCompare(
                                    base_law, M.EmptyList,
                                )() is M.false_value:
                                    base_origin = M.Pair(
                                        M.Char("dialogue-rule"),
                                        M.Pair(
                                            kept_premises,
                                            M.Pair(
                                                base_replacement,
                                                M.EmptyList,
                                            ),
                                        ),
                                    )
                                    base_proposal = G.Proposal(
                                        base_law, base_origin,
                                    )()
                                    proposal_store = (
                                        G.ProposalStoreSubmit(
                                            proposal_store,
                                            base_proposal,
                                        )()
                                    )
                                    pending_rule = base_proposal
                                    _persist_talk_state()
                                    return (
                                        "I could not certify an"
                                        + " induction over '"
                                        + claim_text
                                        + "' (no-base). The step is"
                                        + " recorded: "
                                        + P.PrettyRule(
                                            step_rule,
                                            M.AllConstructors,
                                        )()
                                        + ". From its own shape the"
                                        + " base would be: "
                                        + P.PrettyRule(
                                            base_rule,
                                            M.AllConstructors,
                                        )()
                                        + ". Approve? (yes/no)"
                                    )
                _persist_talk_state()
                return (
                    "I could not certify an induction over '"
                    + claim_text + "' ("
                    + str(reason())
                    + "). A base rule concludes it at a numeral; a step"
                    + " rule concludes it at a constructor over a variable"
                    + " it also assumes. Teach them with 'rule:' and"
                    + " certify again with 'induction:'."
                )
            if record:
                _log_lesson(line)
            _persist_talk_state()
            return (
                "Certified induction over '" + claim_text + "': "
                + P.PrettyRule(universal, M.AllConstructors)()
                + ". The certificate is recorded; spine instances of the"
                + " claim cite it in their derivations."
            )
        if lowered.startswith("training example:"):
            return _handle_training(line, record=record)
        if lowered.startswith("definition:"):
            return _handle_definition(line, record=record)
        if lowered.startswith("is "):
            question_answer = _question_graph_answer(line)
            if question_answer is not None:
                return question_answer
        if lowered.startswith("how many "):
            # Self-knowledge, counted from the state: how many rules,
            # facts, or definitions the machine holds. The count is
            # walked from the graph; the words are the machine's own.
            how_many_rest = lowered[len("how many "):].rstrip("?!. ")
            if how_many_rest.endswith("do you know"):
                how_many_noun_text = how_many_rest[
                    : -len("do you know")
                ].strip().rstrip("?!. ")
                if how_many_noun_text != "":
                    how_many_word = M.Char(how_many_noun_text)
                    how_many_singular = G.WordSingular(
                        how_many_word,
                    )()
                    if M.IdentityCompare(
                        how_many_singular, M.EmptyList,
                    )() is M.truth_value:
                        how_many_singular = how_many_word
                    how_many_kind = str(how_many_singular())
                    how_many_chain = M.EmptyList
                    if how_many_kind == "rule":
                        how_many_chain = G.InstalledTaughtRules(
                            learned_version,
                        )()
                    elif how_many_kind == "fact":
                        how_many_chain = G.InstalledTaughtFacts(
                            learned_version,
                        )()
                    elif how_many_kind == "definition":
                        how_many_chain = G.InstalledDefinitions(
                            learned_version,
                        )()
                    elif (
                        how_many_kind == "law"
                        or how_many_kind == "proposal"
                    ):
                        # Laws and pending proposals are read from the
                        # Step-50 self-model: the machine's own state
                        # rendered in its own substrate, quoted back to
                        # the dialogue instead of re-walked from the
                        # graph.
                        self_model = G.SelfModelVersion(
                            learned_version,
                            proposal_store,
                            M.EmptyList,
                        )()
                        self_subterms = M.Head(
                            M.Tail(self_model)(),
                        )()
                        self_term = M.EmptyList
                        self_scan = self_subterms
                        while M.IdentityCompare(
                            self_scan, M.EmptyList,
                        )() is M.false_value:
                            self_candidate = M.Head(self_scan)()
                            if M.IsPair(self_candidate)() is M.truth_value:
                                if M.Compare(
                                    M.Head(self_candidate)(),
                                    Lmod.SelfModelLabel,
                                )() is M.truth_value:
                                    self_term = self_candidate
                                    self_scan = M.EmptyList
                                else:
                                    self_scan = M.Tail(self_scan)()
                            else:
                                self_scan = M.Tail(self_scan)()
                        if M.IdentityCompare(
                            self_term, M.EmptyList,
                        )() is M.truth_value:
                            return (
                                "I could not render my own state;"
                                + " the self-model came back empty."
                            )
                        if how_many_kind == "law":
                            how_many_chain = M.Head(
                                M.Tail(self_term)(),
                            )()
                        else:
                            # Pair(label, Pair(laws, Pair(contracts,
                            # Pair(policy, Pair(schedule, Pair(safety,
                            # Pair(quoted, Pair(pending, Empty))))))))
                            pending_term = M.Head(
                                M.Tail(
                                    M.Tail(
                                        M.Tail(
                                            M.Tail(
                                                M.Tail(
                                                    M.Tail(
                                                        M.Tail(
                                                            self_term,
                                                        )(),
                                                    )(),
                                                )(),
                                            )(),
                                        )(),
                                    )(),
                                )(),
                            )()
                            if M.IdentityCompare(
                                pending_term, M.EmptyList,
                            )() is M.truth_value:
                                how_many_count = 0
                            else:
                                how_many_count = int(
                                    str(
                                        M.GMPRepText(pending_term)(),
                                    ),
                                )
                            if how_many_count == 1:
                                return (
                                    "I have one proposal"
                                    + " pending."
                                )
                            return (
                                "I have "
                                + _words_of_value_text(
                                    str(how_many_count),
                                )
                                + " proposals pending."
                            )
                    else:
                        return (
                            "I do not know the word: "
                            + how_many_noun_text
                            + ". I count rules, facts,"
                            + " definitions, laws, and proposals."
                        )
                    how_many_count = _count_chain(how_many_chain)
                    how_many_text = _words_of_value_text(
                        str(how_many_count),
                    )
                    if how_many_count == 1:
                        return "I know one " + how_many_kind + "."
                    return (
                        "I know " + how_many_text + " "
                        + how_many_kind + "s."
                    )
        if lowered.startswith("what are the "):
            # An enumeration question: "what are the <concept>s of
            # <number>". The concept and its meaning are the
            # trainer's -- a defined word plus a taught rule
            # concluding it from a divisibility -- and the machine
            # contributes the scan: every number it knows, tested by
            # its own division against the rule's premises.
            what_are_rest = lowered[len("what are the "):]
            of_position = what_are_rest.find(" of ")
            if of_position != -1:
                what_are_noun_text = what_are_rest[:of_position].strip()
                what_are_number_text = what_are_rest[
                    of_position + 4:
                ].strip().rstrip("?!. ")
                if what_are_noun_text != "":
                    if what_are_number_text != "":
                        noun_word = M.Char(what_are_noun_text)
                        concept_word = G.WordSingular(noun_word)()
                        if M.IdentityCompare(
                            concept_word, M.EmptyList,
                        )() is M.truth_value:
                            concept_word = noun_word
                        concept_defined = G.DefinitionFor(
                            learned_version, concept_word,
                        )()
                        if M.IdentityCompare(
                            concept_defined, M.EmptyList,
                        )() is M.truth_value:
                            return (
                                "I do not know the word: "
                                + what_are_noun_text
                                + ". Define it with 'definition: a "
                                + str(concept_word()) + " is ...'."
                            )
                        what_are_value = _numeral_value_text(
                            M.Char(what_are_number_text),
                        )
                        if what_are_value is M.EmptyList:
                            return (
                                "I do not know the number '"
                                + what_are_number_text + "'."
                            )
                        # The divisibility the machine can compute, in
                        # the word or through its bridge.
                        acceptable_heads = M.Pair(
                            M.Char("divisible"), M.EmptyList,
                        )
                        divisible_bridge = G.BridgeFor(
                            learned_version, M.Char("divisible"),
                        )()
                        if M.IdentityCompare(
                            divisible_bridge, M.EmptyList,
                        )() is M.false_value:
                            acceptable_heads = M.Pair(
                                G.BridgeConstructor(divisible_bridge)(),
                                acceptable_heads,
                            )
                        # The operative rule: its conclusion names the
                        # concept over two arguments, and every premise
                        # is computable -- a divisibility between the
                        # two arguments, or an order comparison between
                        # them.
                        operative_rule = M.EmptyList
                        rule_scan = G.InstalledTaughtRules(
                            learned_version,
                        )()
                        while M.IdentityCompare(
                            rule_scan, M.EmptyList,
                        )() is M.false_value:
                            scan_rule = M.Head(rule_scan)()
                            scan_replacement = P.RuleReplacement(
                                scan_rule,
                            )()
                            if M.IsPair(
                                scan_replacement,
                            )() is M.truth_value:
                                if M.Compare(
                                    M.Head(scan_replacement)(),
                                    concept_word,
                                )() is M.truth_value:
                                    scan_args = M.Tail(
                                        scan_replacement,
                                    )()
                                    if M.IdentityCompare(
                                        scan_args, M.EmptyList,
                                    )() is M.false_value:
                                        if M.IdentityCompare(
                                            M.Tail(scan_args)(),
                                            M.EmptyList,
                                        )() is M.false_value:
                                            if M.IdentityCompare(
                                                M.Tail(
                                                    M.Tail(scan_args)(),
                                                )(),
                                                M.EmptyList,
                                            )() is M.truth_value:
                                                scan_arg = M.Head(
                                                    scan_args,
                                                )()
                                                bound_arg = M.Head(
                                                    M.Tail(scan_args)(),
                                                )()
                                                premises_fit = (
                                                    M.truth_value
                                                )
                                                has_divisibility = (
                                                    M.false_value
                                                )
                                                premise_scan = (
                                                    P.RulePremises(
                                                        scan_rule,
                                                    )()
                                                )
                                                while M.IdentityCompare(
                                                    premise_scan,
                                                    M.EmptyList,
                                                )() is M.false_value:
                                                    scan_premise = (
                                                        M.Head(
                                                            premise_scan,
                                                        )()
                                                    )
                                                    if M.IsPair(
                                                        scan_premise,
                                                    )() is not M.truth_value:
                                                        premises_fit = (
                                                            M.false_value
                                                        )
                                                        premise_scan = (
                                                            M.EmptyList
                                                        )
                                                    else:
                                                        premise_head = (
                                                            M.Head(
                                                                scan_premise,
                                                            )()
                                                        )
                                                        head_matches = (
                                                            M.false_value
                                                        )
                                                        head_scan = (
                                                            acceptable_heads
                                                        )
                                                        while M.IdentityCompare(
                                                            head_scan,
                                                            M.EmptyList,
                                                        )() is M.false_value:
                                                            if M.Compare(
                                                                premise_head,
                                                                M.Head(
                                                                    head_scan,
                                                                )(),
                                                            )() is M.truth_value:
                                                                head_matches = (
                                                                    M.truth_value
                                                                )
                                                                head_scan = (
                                                                    M.EmptyList
                                                                )
                                                            else:
                                                                head_scan = (
                                                                    M.Tail(
                                                                        head_scan,
                                                                    )()
                                                                )
                                                        if M.IdentityCompare(
                                                            head_matches,
                                                            M.truth_value,
                                                        )() is M.truth_value:
                                                            prem_args = (
                                                                M.Tail(
                                                                    scan_premise,
                                                                )()
                                                            )
                                                            if M.IdentityCompare(
                                                                prem_args,
                                                                M.EmptyList,
                                                            )() is M.false_value:
                                                                if M.IdentityCompare(
                                                                    M.Tail(
                                                                        prem_args,
                                                                    )(),
                                                                    M.EmptyList,
                                                                )() is M.false_value:
                                                                    if M.IdentityCompare(
                                                                        M.Tail(
                                                                            M.Tail(
                                                                                prem_args,
                                                                            )(),
                                                                        )(),
                                                                        M.EmptyList,
                                                                    )() is M.truth_value:
                                                                        if M.Compare(
                                                                            M.Head(
                                                                                prem_args,
                                                                            )(),
                                                                            scan_arg,
                                                                        )() is M.truth_value:
                                                                            if M.Compare(
                                                                                M.Head(
                                                                                    M.Tail(
                                                                                        prem_args,
                                                                                    )(),
                                                                                )(),
                                                                                bound_arg,
                                                                            )() is M.truth_value:
                                                                                has_divisibility = (
                                                                                    M.truth_value
                                                                                )
                                                                            else:
                                                                                premises_fit = (
                                                                                    M.false_value
                                                                                )
                                                                    else:
                                                                        premises_fit = (
                                                                            M.false_value
                                                                        )
                                                                else:
                                                                    premises_fit = (
                                                                        M.false_value
                                                                    )
                                                            else:
                                                                premises_fit = (
                                                                    M.false_value
                                                                )
                                                        elif M.Compare(
                                                            premise_head,
                                                            M.Char("leq"),
                                                        )() is M.truth_value:
                                                            prem_args = (
                                                                M.Tail(
                                                                    scan_premise,
                                                                )()
                                                            )
                                                            if M.IdentityCompare(
                                                                prem_args,
                                                                M.EmptyList,
                                                            )() is M.false_value:
                                                                if M.IdentityCompare(
                                                                    M.Tail(
                                                                        prem_args,
                                                                    )(),
                                                                    M.EmptyList,
                                                                )() is M.false_value:
                                                                    if M.IdentityCompare(
                                                                        M.Tail(
                                                                            M.Tail(
                                                                                prem_args,
                                                                            )(),
                                                                        )(),
                                                                        M.EmptyList,
                                                                    )() is M.truth_value:
                                                                        first_is_scan = M.Compare(
                                                                            M.Head(
                                                                                prem_args,
                                                                            )(),
                                                                            scan_arg,
                                                                        )() is M.truth_value
                                                                        first_is_bound = M.Compare(
                                                                            M.Head(
                                                                                prem_args,
                                                                            )(),
                                                                            bound_arg,
                                                                        )() is M.truth_value
                                                                        second_is_scan = M.Compare(
                                                                            M.Head(
                                                                                M.Tail(
                                                                                    prem_args,
                                                                                )(),
                                                                            )(),
                                                                            scan_arg,
                                                                        )() is M.truth_value
                                                                        second_is_bound = M.Compare(
                                                                            M.Head(
                                                                                M.Tail(
                                                                                    prem_args,
                                                                                )(),
                                                                            )(),
                                                                            bound_arg,
                                                                        )() is M.truth_value
                                                                        args_are_the_two = (
                                                                            (
                                                                                first_is_scan
                                                                                and second_is_bound
                                                                            )
                                                                            or (
                                                                                first_is_bound
                                                                                and second_is_scan
                                                                            )
                                                                        )
                                                                        if args_are_the_two is not True:
                                                                            premises_fit = (
                                                                                M.false_value
                                                                            )
                                                                    else:
                                                                        premises_fit = (
                                                                            M.false_value
                                                                        )
                                                                else:
                                                                    premises_fit = (
                                                                        M.false_value
                                                                    )
                                                            else:
                                                                premises_fit = (
                                                                    M.false_value
                                                                )
                                                        else:
                                                            premises_fit = (
                                                                M.false_value
                                                            )
                                                        if M.IdentityCompare(
                                                            premise_scan,
                                                            M.EmptyList,
                                                        )() is M.false_value:
                                                            premise_scan = (
                                                                M.Tail(
                                                                    premise_scan,
                                                                )()
                                                            )
                                                if M.IdentityCompare(
                                                    premises_fit,
                                                    M.truth_value,
                                                )() is M.truth_value:
                                                    if M.IdentityCompare(
                                                        has_divisibility,
                                                        M.truth_value,
                                                    )() is M.truth_value:
                                                        operative_rule = (
                                                            scan_rule
                                                        )
                                                        rule_scan = (
                                                            M.EmptyList
                                                        )
                            if M.IdentityCompare(
                                rule_scan, M.EmptyList,
                            )() is M.false_value:
                                rule_scan = M.Tail(rule_scan)()
                        if M.IdentityCompare(
                            operative_rule, M.EmptyList,
                        )() is M.truth_value:
                            return (
                                "The word '" + what_are_noun_text
                                + "' is defined, but nothing teaches"
                                + " what it is: no rule concludes "
                                + str(concept_word())
                                + "(a, b) from a divisibility. Teach"
                                + " it with 'rule: divisible(a, b) -> "
                                + str(concept_word()) + "(a, b)'."
                            )
                        # The scan: every number the machine knows,
                        # from one up to the number asked, tested by
                        # division; the hits are the ones the rule's
                        # premises let stand.
                        scan_hits = []
                        scan_lines = []
                        word_entries = M.Head(
                            M.Tail(vocabulary)(),
                        )()
                        entry_scan = word_entries
                        while M.IdentityCompare(
                            entry_scan, M.EmptyList,
                        )() is M.false_value:
                            entry = M.Head(entry_scan)()
                            entry_word = M.Head(entry)()
                            entry_value = M.GMPRepText(
                                M.NatRepOf(
                                    M.Head(M.Tail(entry)())(),
                                    registry,
                                )(),
                            )()
                            if M.IdentityCompare(
                                G.GMPLessText(entry_value, "1")(),
                                M.truth_value,
                            )() is M.false_value:
                                if M.IdentityCompare(
                                    G.GMPLessText(
                                        what_are_value, entry_value,
                                    )(),
                                    M.truth_value,
                                )() is M.false_value:
                                    division = _division_texts(
                                        entry_value, what_are_value,
                                    )
                                    division_remainder = str(
                                        M.Head(
                                            M.Tail(division)(),
                                        )(),
                                    )
                                    passes = M.truth_value
                                    if M.IdentityCompare(
                                        G.GMPEqualText(
                                            division_remainder, "0",
                                        )(),
                                        M.truth_value,
                                    )() is not M.truth_value:
                                        passes = M.false_value
                                    if M.IdentityCompare(
                                        passes, M.truth_value,
                                    )() is M.truth_value:
                                        scan_hits.append(
                                            str(entry_word()),
                                        )
                                        scan_lines.append(
                                            str(entry_word())
                                            + " divides "
                                            + what_are_number_text
                                            + " exactly",
                                        )
                                    else:
                                        scan_lines.append(
                                            str(entry_word())
                                            + " leaves remainder "
                                            + _words_of_value_text(
                                                division_remainder,
                                            ),
                                        )
                            entry_scan = M.Tail(entry_scan)()
                        if not scan_hits:
                            return (
                                "By its own division: "
                                + "; ".join(scan_lines)
                                + ". No number from one to "
                                + what_are_number_text
                                + " divides it exactly, so it has no "
                                + what_are_noun_text + "."
                            )
                        return (
                            "By its own division: "
                            + "; ".join(scan_lines)
                            + ". The " + what_are_noun_text
                            + " of " + what_are_number_text
                            + " are " + ", ".join(scan_hits) + "."
                        )
        if lowered.startswith("what is "):
            spoken_definition = _handle_what_is(line)
            if spoken_definition is not None:
                return spoken_definition
        if lowered.strip() == "1":
            if M.IdentityCompare(
                pending_rule, M.EmptyList,
            )() is M.false_value:
                if G.IsInventedLemma(
                    G.ProposalLaw(pending_rule)(),
                )() is M.truth_value:
                    return _handle_decision("yes", record=record)
        if lowered in ("yes", "no"):
            if M.IdentityCompare(
                pending_rule, M.EmptyList,
            )() is M.false_value:
                return _handle_decision(lowered, record=record)
            if M.IdentityCompare(pending_queue, M.EmptyList)() is M.false_value:
                return _handle_decision(lowered, record=record)
            # A correspondence the daemon found is on the table: a bare
            # yes or no answers it, the same as any taught rule. The
            # finding may have landed while the prompt was already drawn
            # -- its question was printed above, but the answer arrives
            # here -- so the shared state is read once more before the
            # yes or no is declared answerless.
            if M.IdentityCompare(
                pending_machine, M.EmptyList,
            )() is M.truth_value:
                _adopt_daemon_state()
            if M.IdentityCompare(
                pending_machine, M.EmptyList,
            )() is M.false_value:
                return _handle_machine_decision(lowered, record=record)
            # No rule question is decidable. A bare yes or no still
            # answers the one question on the table when that question
            # is a bridge question: nothing else could be meant by it.
            _ensure_bridge_loaded()
            if M.IdentityCompare(
                pending_asks, M.EmptyList,
            )() is M.false_value:
                head_entry = M.Head(pending_asks)()
                if M.Compare(
                    M.Head(head_entry)(), M.Char("bridge"),
                )() is M.truth_value:
                    if M.IdentityCompare(
                        pending_bridge, M.EmptyList,
                    )() is M.false_value:
                        return _handle_bridge_decision(
                            "bridge " + lowered, record=record,
                        )
                return (
                    "A yes or no does not answer the question on the"
                    + " table." + _ask_next_line()
                )
            return "There is no question awaiting an answer."
        if lowered.strip() in ("bridge yes", "bridge no"):
            _ensure_bridge_loaded()
            return _handle_bridge_decision(lowered.strip(), record=record)
        if lowered.startswith("why are these two definitions equivalent"):
            proof_scan = G.GraphNodes(learned_version)()
            proof_record = M.EmptyList
            while M.IdentityCompare(
                proof_scan, M.EmptyList,
            )() is M.false_value:
                proof_node = M.Head(proof_scan)()
                proof_scan = M.Tail(proof_scan)()
                if M.IsPair(proof_node)() is M.truth_value:
                    if M.Compare(
                        M.Head(proof_node)(),
                        M.Char("equivalence-proven"),
                    )() is M.truth_value:
                        proof_record = proof_node
                        proof_scan = M.EmptyList
            if M.IdentityCompare(
                proof_record, M.EmptyList,
            )() is M.truth_value:
                return (
                    "No equivalence proof is recorded; ask me to prove"
                    + " one first."
                )
            proof_lemmas = M.Head(M.Tail(proof_record)())()
            proof_process = M.Head(
                M.Tail(M.Tail(proof_record)())(),
            )()
            proof_remaining = M.Head(
                M.Tail(M.Tail(M.Tail(proof_record)())())(),
            )()
            # The certificate the proof rested on, re-read from the
            # graph so the reply renders its base and step rules
            # instead of narrating them.
            certificate_node = M.EmptyList
            certificate_scan = G.GraphNodes(learned_version)()
            while M.IdentityCompare(
                certificate_scan, M.EmptyList,
            )() is M.false_value:
                certificate_candidate = M.Head(certificate_scan)()
                certificate_scan = M.Tail(certificate_scan)()
                if M.IsPair(certificate_candidate)() is M.truth_value:
                    if M.Compare(
                        M.Head(certificate_candidate)(),
                        M.Char("inductive-law"),
                    )() is M.truth_value:
                        certificate_node = certificate_candidate
                        certificate_scan = M.EmptyList

            def _recorded_rule_renders(pair_chain):
                rendered = []
                render_scan = pair_chain
                while M.IdentityCompare(
                    render_scan, M.EmptyList,
                )() is M.false_value:
                    render_pair = M.Head(render_scan)()
                    rendered.append(
                        P.PrettyRule(
                            P.MultiRule(
                                M.Head(render_pair)(),
                                M.Head(M.Tail(render_pair)())(),
                            )(),
                            M.AllConstructors,
                        )()
                    )
                    render_scan = M.Tail(render_scan)()
                return rendered
            proof_text = (
                "Proof: the recorded equivalence runs in both"
                + " directions. Direction one, process to lemma: every"
                + " premise of the lemma rules -- "
                + "; ".join(_recorded_rule_renders(proof_lemmas))
                + " -- except the leq premises is reachable from the"
                + " process side. Direction two, lemma to process:"
                + " every premise of the proven process rules -- "
                + "; ".join(_recorded_rule_renders(proof_process))
                + " -- derives from the lemma side under the installed"
                + " rules."
            )
            if M.IdentityCompare(
                certificate_node, M.EmptyList,
            )() is M.false_value:
                cert_claim = M.Head(M.Tail(certificate_node)())()
                cert_bases = M.Head(
                    M.Tail(M.Tail(certificate_node)())(),
                )()
                cert_steps = M.Head(
                    M.Tail(M.Tail(M.Tail(certificate_node)())())(),
                )()
                base_renders = []
                base_scan = cert_bases
                while M.IdentityCompare(
                    base_scan, M.EmptyList,
                )() is M.false_value:
                    # Each entry is a premises/replacement pair; a
                    # certificate written before pairs were stored
                    # carries an opaque atom instead, and rendering
                    # skips what the wire could not carry.
                    base_entry = M.Head(base_scan)()
                    try:
                        base_renders.append(
                            P.PrettyRule(
                                P.MultiRule(
                                    M.Head(base_entry)(),
                                    M.Head(M.Tail(base_entry)())(),
                                )(),
                                M.AllConstructors,
                            )()
                        )
                    except Exception:
                        pass
                    base_scan = M.Tail(base_scan)()
                step_renders = []
                step_scan = cert_steps
                while M.IdentityCompare(
                    step_scan, M.EmptyList,
                )() is M.false_value:
                    step_entry = M.Head(step_scan)()
                    try:
                        step_renders.append(
                            P.PrettyRule(
                                P.MultiRule(
                                    M.Head(step_entry)(),
                                    M.Head(M.Tail(step_entry)())(),
                                )(),
                                M.AllConstructors,
                            )()
                        )
                    except Exception:
                        pass
                    step_scan = M.Tail(step_scan)()
                if base_renders or step_renders:
                    proof_text = (
                        proof_text
                        + " The recorded induction over '"
                        + str(cert_claim()) + "': base "
                        + "; ".join(base_renders)
                        + "; step "
                        + "; ".join(step_renders) + "."
                    )
                else:
                    proof_text = (
                        proof_text
                        + " The recorded induction over '"
                        + str(cert_claim()) + "'."
                    )
            remaining_render = "; ".join(
                _recorded_rule_renders(proof_remaining),
            )
            if remaining_render != "":
                proof_text = (
                    proof_text
                    + " Outside the proof: " + remaining_render
                    + " -- their premises did not derive from the lemma"
                    + " side."
                )
            return proof_text
        if lowered.startswith("why:"):
            asked_text = line[4:].strip()
            asked_surface = G.Surface(_words(asked_text))()
            asked_scan = G.InstalledAskedQuestions(learned_version)()
            asked_gap = M.EmptyList
            asked_law = M.EmptyList
            while M.IdentityCompare(
                asked_scan, M.EmptyList,
            )() is M.false_value:
                asked_entry = M.Head(asked_scan)()
                asked_gap_candidate = M.Head(M.Tail(asked_entry)())()
                asked_surface_entry = M.Head(
                    M.Tail(M.Tail(asked_entry)())(),
                )()
                asked_law_entry = M.Head(
                    M.Tail(M.Tail(M.Tail(asked_entry)())())(),
                )()
                asked_chain = M.Head(M.Tail(asked_surface_entry)())()
                asked_normalized = G.Surface(
                    G.WordChainWithout(
                        asked_chain,
                        M.Pair(M.Char("?"), M.EmptyList),
                    )(),
                )()
                if M.Compare(asked_surface, asked_normalized)() is M.truth_value:
                    asked_gap = asked_gap_candidate
                    asked_law = asked_law_entry
                    asked_scan = M.EmptyList
                else:
                    asked_scan = M.Tail(asked_scan)()
            if M.IdentityCompare(asked_gap, M.EmptyList)() is M.false_value:
                render_name = "the gap question law"
                if M.Compare(
                    M.Head(asked_gap)(),
                    Lmod.UndefinedConceptLabel,
                )() is M.truth_value:
                    render_name = "the what-is render law"
                elif M.Compare(
                    M.Head(asked_gap)(),
                    Lmod.UngroundedModifierLabel,
                )() is M.truth_value:
                    render_name = "the define render law"
                elif M.Compare(
                    M.Head(asked_gap)(),
                    Lmod.NoUsageExampleLabel,
                )() is M.truth_value:
                    render_name = "the usage-example render law"
                return (
                    "asked because " + M.PrettyTerm(
                        asked_gap, M.AllConstructors,
                    )()
                    + " was detected; rendered via " + render_name
                )
            known_constructors = G.RuleConstructors(
                learned_version,
                pack_concepts,
            )()
            parsed_why = G.ParseRuleText(
                line[4:].strip(),
                reading_policy,
                reading_digits,
                known_constructors,
                M.truth_value,
            )()
            why_target = M.Head(parsed_why)()
            why_conclusions = G.InstalledCaseConclusions(learned_version)()
            why_conclusion = M.EmptyList
            while M.IdentityCompare(
                why_conclusions, M.EmptyList,
            )() is M.false_value:
                candidate_conclusion = M.Head(why_conclusions)()
                if M.Compare(
                    G.CaseConclusionCandidate(candidate_conclusion)(),
                    why_target,
                )() is M.truth_value:
                    why_conclusion = candidate_conclusion
                    why_conclusions = M.EmptyList
                else:
                    why_conclusions = M.Tail(why_conclusions)()
            if M.IdentityCompare(
                why_conclusion, M.EmptyList,
            )() is M.false_value:
                exact_one_term = G.CaseSplitExactlyOne(
                    G.CaseConclusionSplit(why_conclusion)(),
                )()
                return (
                    "case conclusion: " + line[4:].strip()
                    + " was established by the only consistent branch of "
                    + M.PrettyTerm(exact_one_term, M.AllConstructors)()
                    + "; refuted candidates: "
                    + M.PrettyTerm(
                        G.CaseConclusionRefuted(why_conclusion)(),
                        M.AllConstructors,
                    )()
                )
            why_derivations = G.InstalledTaughtDerivations(learned_version)()
            why_derivation = M.EmptyList
            while M.IdentityCompare(
                why_derivations, M.EmptyList,
            )() is M.false_value:
                candidate_derivation = M.Head(why_derivations)()
                derived_target = G.DerivationDerived(candidate_derivation)()
                why_matches = M.Compare(derived_target, why_target)()
                if M.IdentityCompare(
                    why_matches, M.truth_value,
                )() is M.false_value:
                    if M.IsPair(derived_target)() is M.truth_value:
                        if M.IsPair(why_target)() is M.truth_value:
                            if M.Compare(
                                M.Head(derived_target)(),
                                Lmod.SupportedLabel,
                            )() is M.truth_value:
                                if M.Compare(
                                    M.Head(why_target)(),
                                    Lmod.SupportedLabel,
                                )() is M.truth_value:
                                    target_arguments = M.Tail(why_target)()
                                    derived_arguments = M.Tail(derived_target)()
                                    if M.IdentityCompare(
                                        target_arguments, M.EmptyList,
                                    )() is M.false_value:
                                        if M.IdentityCompare(
                                            M.Tail(target_arguments)(),
                                            M.EmptyList,
                                        )() is M.truth_value:
                                            if M.IdentityCompare(
                                                derived_arguments, M.EmptyList,
                                            )() is M.false_value:
                                                if M.Compare(
                                                    M.Head(target_arguments)(),
                                                    M.Head(derived_arguments)(),
                                                )() is M.truth_value:
                                                    why_matches = M.truth_value
                if M.IdentityCompare(
                    why_matches, M.truth_value,
                )() is M.truth_value:
                    why_derivation = candidate_derivation
                    why_derivations = M.EmptyList
                else:
                    why_derivations = M.Tail(why_derivations)()
            if M.IdentityCompare(
                why_derivation, M.EmptyList,
            )() is M.false_value:
                derivation_tree = G.DerivationTree(
                    why_derivation,
                    learned_version,
                    "0",
                )()
                return (
                    "because " + G.DerivationTreeText(derivation_tree)()
                )
            return "There is no recorded derivation for " + line[4:].strip() + "."
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
            # The word may be defined as a term yet carry no law: its
            # definition never compiled, so the surface grammar does
            # not know it. Say that, with the words that block the
            # compilation, instead of bare deafness.
            unknown_word = M.Char(unknown)
            defined = G.DefinitionFor(learned_version, unknown_word)()
            if M.IdentityCompare(
                defined, M.EmptyList,
            )() is M.truth_value:
                singular = G.WordSingular(unknown_word)()
                if M.IdentityCompare(
                    singular, M.EmptyList,
                )() is M.false_value:
                    defined = G.DefinitionFor(
                        learned_version, singular,
                    )()
            if M.IdentityCompare(
                defined, M.EmptyList,
            )() is M.false_value:
                open_words = G.DefinitionOpenDependencies(
                    learned_version, defined, vocabulary, registry,
                )()
                spoken_open = []
                open_scan = open_words
                while M.IdentityCompare(
                    open_scan, M.EmptyList,
                )() is M.false_value:
                    spoken_open.append(
                        str(M.Head(open_scan)()()),
                    )
                    open_scan = M.Tail(open_scan)()
                body_chain = M.Head(
                    M.Tail(G.DefinitionBody(defined)())(),
                )()
                compiled_rules = G.DefinitionRulesFor(
                    learned_version, defined, vocabulary, registry,
                )()
                has_rules = M.false_value
                if M.IdentityCompare(
                    compiled_rules, M.EmptyList,
                )() is M.false_value:
                    has_rules = M.truth_value
                if spoken_open:
                    # The blocking words get their grounding offers
                    # right here: the packs or the taught rules may
                    # know them, and the offer is the way out.
                    _queue_open_word_candidates(spoken_open)
                    return (
                        "I have a definition of '" + unknown + "': "
                        + _speak_chain(body_chain)
                        + ". But it compiled to no law, so I cannot"
                        + " read it in a sentence: "
                        + " or ".join(
                            "'" + w + "'" for w in spoken_open
                        )
                        + " "
                        + ("is" if len(spoken_open) == 1 else "are")
                        + " not grounded. Define or ground "
                        + ("it" if len(spoken_open) == 1 else "them")
                        + " first." + _ask_next_line()
                    )
                if M.IdentityCompare(
                    has_rules, M.truth_value,
                )() is M.truth_value:
                    return (
                        "I have a definition of '" + unknown + "': "
                        + _speak_chain(body_chain)
                        + ". It compiled to laws the rule grammar"
                        + " knows, but the sentence grammar does not"
                        + " read the word yet; ask as 'query: "
                        + unknown + "(seven)'."
                    )
                # No laws and no open words: the blocker may be an
                # operator that still stands uninterpreted, or a body
                # with no template. Either gap is re-proposed here, at
                # the point of failure.
                defined_term = G.DefinitionTerm(defined)()
                if M.IdentityCompare(
                    _reraise_operator_gap(
                        defined_term, str(defined_term()),
                    ),
                    M.truth_value,
                )() is M.truth_value:
                    return (
                        "I have a definition of '" + unknown + "': "
                        + _speak_chain(body_chain)
                        + ". But its 'only' still stands uninterpreted,"
                        + " so it compiles to no law."
                        + _ask_next_line()
                    )
                if M.IdentityCompare(
                    _reraise_shape_gap(defined_term, defined),
                    M.truth_value,
                )() is M.truth_value:
                    return (
                        "I have a definition of '" + unknown + "': "
                        + _speak_chain(body_chain)
                        + ". But its body has no template yet, so it"
                        + " compiles to no law."
                        + _ask_next_line()
                    )
                return (
                    "I have a definition of '" + unknown + "': "
                    + _speak_chain(body_chain)
                    + ". But it compiled to no law, so I cannot read it"
                    + " in a sentence."
                )
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
    print("Ground words: 'word: mud means wet dirt' or 'word: shoes are wearable objects'.")
    print("Teach deductions: 'rule: Human(x), Adult(x) -> Sage(x)'.")
    print("Ask taught rules: 'query: Sage(alice)'.")
    print("Ask symbolic inequalities: 'query: x^4 + y^4 >= x^3*y + x*y^3'.")
    print("Ask witnessed Euclidean descent: 'query: gcd(1071,462)'.")
    print("Run the pair-schema story core: 'story demo', 'how is Alice connected to wolf?', or 'analogy'.")
    print("After a failed search: 'suggest lemmas'; old abduction: 'suggest premises'.")
    print("Inspect invented results: 'show lemmas'.")
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

    def _wait_for_daemon_fold():
        """Wait, bounded, for the daemon to take the inbox and write state.

        Teaching submits through the inbox and the daemon activates it on
        its next cycle. Without this wait the very next line can arrive
        before that cycle, and a phrase whose word was approved one line
        ago still fails to parse -- the state was there, just not yet.
        The wait ends when the inbox is gone and the checkpoint moved.
        """
        inbox_wait_path = os.path.join(
            SNAPSHOT_DIR, Dmn.DAEMON_INBOX_NAME,
        )
        if not os.path.exists(inbox_wait_path):
            return
        if not os.path.exists(daemon_live_path):
            return
        stamp_at_wait = 0.0
        if os.path.exists(talk_checkpoint_path):
            stamp_at_wait = os.path.getmtime(talk_checkpoint_path)
        deadline = time.time() + 8.0
        while time.time() < deadline:
            if not os.path.exists(inbox_wait_path):
                if os.path.exists(talk_checkpoint_path):
                    if os.path.getmtime(talk_checkpoint_path) > stamp_at_wait:
                        return
            time.sleep(0.25)

    while True:
        _adopt_daemon_state()
        try:
            line = input("you> ")
        except EOFError:
            print()
            break
        stripped = line.strip()
        if stripped == "" or stripped == "goodbye":
            print("hyge> goodbye")
            break
        # A submission from the previous line may still be in the inbox;
        # let the daemon take it and write the activated state before
        # this line is read, so teaching lands before it is used.
        _wait_for_daemon_fold()
        _adopt_daemon_state()
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

    if os.name == "nt":
        # The host shell cannot speak the POSIX spawn line: cmd.exe reads
        # 'HYGE_LIVE_DAEMON=1 exec ...' as a program named
        # HYGE_LIVE_DAEMON=1. On this platform the marker rides the
        # inherited environment, and the interpreter is spawned directly
        # -- no shell in between -- so terminate() below reaches the
        # daemon itself, exactly what 'exec' gives the POSIX branch.
        os.environ["HYGE_LIVE_DAEMON"] = "1"
        daemon_child = subprocess.Popen(
            [
                sys.executable,
                "-u",
                "-m",
                __package__ + ".main",
                "daemon",
                "--workers",
                str(requested_workers),
            ],
            cwd=import_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
    else:
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
        # The daemon is gone; the conversation is momentarily the only
        # process touching the shared state. Whatever still sits in the
        # inbox -- submitted after the daemon's last drain, or drained
        # but not yet written when it died -- is merged into the
        # checkpoint here, so no teaching is lost with the session. The
        # merge is the same idempotent union the daemon applies, so a
        # submission the daemon already folded in adds nothing.
        teardown_inbox = os.path.join(SNAPSHOT_DIR, Dmn.DAEMON_INBOX_NAME)
        teardown_taken = os.path.join(
            SNAPSHOT_DIR, Dmn.DAEMON_INBOX_NAME + ".taken",
        )
        teardown_paths = []
        if os.path.exists(teardown_inbox):
            teardown_paths.append(teardown_inbox)
        if os.path.exists(teardown_taken):
            # A submission the daemon took but never folded -- a kill
            # between its rename and its state write. It is teaching;
            # it drains with the rest.
            teardown_paths.append(teardown_taken)
        for teardown_path in teardown_paths:
            teardown_submitted = W.load_checkpoint(teardown_path)
            if M.IdentityCompare(
                teardown_submitted, M.EmptyList,
            )() is M.false_value:
                teardown_version = M.EmptyList
                teardown_store = G.ProposalStore(M.EmptyList)()
                teardown_ledger = G.FiringLedger(M.AllConstructors)
                teardown_path_state = os.path.join(SNAPSHOT_DIR, "talk_state.wire")
                if os.path.exists(teardown_path_state):
                    teardown_restored = W.load_checkpoint(teardown_path_state)
                    if M.IdentityCompare(
                        teardown_restored, M.EmptyList,
                    )() is M.false_value:
                        teardown_version = M.Head(teardown_restored)()
                        teardown_store = M.Head(
                            M.Tail(teardown_restored)(),
                        )()
                        teardown_ledger = M.Head(
                            M.Tail(M.Tail(teardown_restored)())(),
                        )()
                teardown_version = G.MergeGraphVersion(
                    teardown_version,
                    M.Head(teardown_submitted)(),
                )()
                teardown_merged = Dmn.DaemonMergeInbox(
                    teardown_store,
                    M.Head(M.Tail(teardown_submitted)())(),
                )()
                teardown_store = M.Head(teardown_merged)()
                W.save_checkpoint(
                    teardown_path_state,
                    teardown_version,
                    teardown_store,
                    teardown_ledger,
                )
                print("live mode: drained the inbox into the talk state.")
            os.remove(teardown_path)
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
