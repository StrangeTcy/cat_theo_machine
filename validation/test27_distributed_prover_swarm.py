"""W16 -- distributed prover swarm: partition, swarm, merge, and compare.

Run from the repository root (the machine's own interpreter, not the system one):

    PYTHONPATH=/home/user .venv/bin/python -u validation/test27_distributed_prover_swarm.py

What this suite claims, and how each claim is measured rather than argued:

1. **Partition is exact and reproducible.** `main.py swarm --role plan` expands
   `engel_e2` once and writes one unit snapshot per frontier node. The suite
   asserts disjointness and coverage *from the plan's own data* -- distinct
   digests, indices 0..n-1 with no gaps, shard sizes that sum to the frontier,
   every resharding k=1..4 a bijection onto the same units -- and then boots the
   baseline snapshot in *this* process and re-runs `partition_frontier`: the
   digests must equal the ones a different process computed. A partition
   function that is not reproducible in a fresh runtime is not a partition.

2. **The swarm reproduces the single-process proof.** The whole-frontier
   baseline runs alone in its own process; then two mesh workers (W2's mTLS
   mesh, `--swarm` runner) run the four units; `distributed_engine.merge` picks
   the lowest-index success, and its plan digest and proof-cost digest must
   equal the baseline's. Equality of the result, not merely success.

3. **Nothing is silently lost.** A worker is SIGKILLed mid-unit. The
   coordinator must record `member-lost`, `job-redispatched` for that unit, and
   the survivor's result for it must be identical to the result the same unit
   produced in the healthy run -- the unit's answer does not depend on which
   peer ran it, which is also the argument for scheduling independence.

4. **Speedup, honestly.** Baseline wall time against swarm wall time on the
   machine this runs on, plus the memory high-water mark of the children. On
   two vCPUs with two workers that each boot their own snapshot, a flat or
   negative number is a finding and is printed as such, not tuned away.

Timing budget (measured on 2 vCPU): plan ~80 s, in-process boot ~25 s,
baseline ~80 s, swarm run ~100 s, kill run ~70 s. The brief's ~180 s budget
assumed W16's faster box; the stages are printed with their own timings so a
regression in any one of them is visible rather than smeared.

Entry point is guarded: `persistence` restores snapshots through spawned
processes that re-import `__main__`, so an unguarded driver re-executes itself
inside every restore worker (see `search/distributed_engine.py`).

`--plan-dir DIR` re-uses an existing plan directory and skips only the plan
subprocess (development convenience; every assertion on the plan still runs).
"""

from __future__ import annotations

import itertools
import json
import os
import resource
import shutil
import signal
import subprocess
import sys
import tempfile
import time

PACKAGE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACKAGE_PARENT = os.path.dirname(PACKAGE_ROOT)
if PACKAGE_PARENT not in sys.path:
    sys.path.insert(0, PACKAGE_PARENT)

from cat_theo_machine import machine as M
from cat_theo_machine import mesh as MeshModule
from cat_theo_machine.networking import jobs as MeshJobs
from cat_theo_machine.networking import protocol
from cat_theo_machine.networking.peer import MeshPeer
from cat_theo_machine.search import distributed_engine as swarm

PROBLEM = "engel_e2"
BURST_STEPS = 3
SHARD_COUNT = 2
EXPECTED_FRONTIER = 4
PLAN_TIMEOUT = 600
BASELINE_TIMEOUT = 600
SWARM_TIMEOUT = 600
KILL_RUN_TIMEOUT = 480
SEMANTIC_KEYS = ("status", "worker_stage", "plan_digest", "derivation_digest", "derivation_bytes", "proof_cost_digest")


class Results:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.notes = []

    def check(self, label, condition, detail=""):
        if condition:
            self.passed += 1
            print("  PASS  %-60s %s" % (label, detail), flush=True)
        else:
            self.failed += 1
            print("  FAIL  %-60s %s" % (label, detail), flush=True)
        return bool(condition)

    def note(self, text):
        self.notes.append(text)
        print("  note  %s" % text, flush=True)


# ------------------------------------------------------------------ processes


def _environment():
    environment = dict(os.environ)
    environment["PYTHONPATH"] = PACKAGE_PARENT
    return environment


def _run_main(arguments, log_path, timeout):
    """Run `python -m cat_theo_machine.main ...` to completion, stdout to a log.

    The machine prints far more than a pipe buffer holds, so output goes to a
    file; capturing it through an unread pipe would block the child forever.
    Returns `(returncode, wall_seconds)`; a timeout kills the process group and
    reports -1 rather than hanging the suite.
    """
    with open(log_path, "w", encoding="utf-8") as log_handle:
        process = subprocess.Popen(
            [sys.executable, "-u", "-m", "cat_theo_machine.main"] + list(arguments),
            cwd=PACKAGE_PARENT,
            env=_environment(),
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=True,
        )
        started = time.time()
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            _kill_process(process)
            return -1, time.time() - started
        return process.returncode, time.time() - started


def _spawn_worker(directory, name, coordinator_address):
    """A swarm worker on W2's mesh: `main.py mesh --role worker --swarm`."""
    log_handle = open(os.path.join(directory, "%s.log" % name), "w", encoding="utf-8")
    return subprocess.Popen(
        [
            sys.executable,
            "-u",
            "-m",
            "cat_theo_machine.main",
            "mesh",
            "--role",
            "worker",
            "--bind",
            "127.0.0.1:0",
            "--coordinator",
            coordinator_address,
            "--cert-dir",
            directory,
            "--cert-name",
            name,
            "--modes",
            "dfs",
            "--swarm",
        ],
        cwd=PACKAGE_PARENT,
        env=_environment(),
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=True,
    )


def _kill_process(process):
    if process is None or process.poll() is not None:
        return
    try:
        os.killpg(os.getpgid(process.pid), signal.SIGKILL)
    except (ProcessLookupError, PermissionError, OSError):
        try:
            process.kill()
        except OSError:
            pass
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        pass


def _terminate(process):
    if process is None or process.poll() is not None:
        return
    try:
        process.terminate()
        process.wait(timeout=10)
    except (subprocess.TimeoutExpired, OSError):
        _kill_process(process)


def _high_water_kib(process):
    """VmHWM of a live child from /proc, in KiB (0 when unavailable)."""
    try:
        with open("/proc/%d/status" % process.pid, encoding="utf-8") as handle:
            for line in handle:
                if line.startswith("VmHWM:"):
                    return int(line.split()[1])
    except (OSError, ValueError, IndexError):
        pass
    return 0


def _children_high_water_mib():
    """Largest resident set any waited-for descendant reached, in MiB."""
    return resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1024.0


def _sweep_restore_scratch(since):
    """Remove restore scratch dirs a killed worker left in the package root.

    `persistence` restores a snapshot through spawned helpers that hand their
    answer over in a scratch directory beside the package and remove it when
    the boot completes. A worker SIGKILLed mid-boot never gets to that `finally`,
    so the kill phase can orphan one; only directories created during this run
    are swept, and only because every child of this suite is dead by then.
    """
    swept = []
    for name in os.listdir(PACKAGE_ROOT):
        if not (name.startswith("hyge-root-restore-") or name.startswith("hyge-registry-restore-")):
            continue
        path = os.path.join(PACKAGE_ROOT, name)
        try:
            if os.path.isdir(path) and os.path.getmtime(path) >= since:
                shutil.rmtree(path, ignore_errors=True)
                swept.append(name)
        except OSError:
            pass
    return swept


# ------------------------------------------------------------------------ mesh


def _has_member(peer, name):
    """A CLI peer is named after its certificate plus a random suffix."""
    return any(peer_id == name or peer_id.startswith(name + "-") for peer_id in peer.members().keys())


def _peer_named(peer_id, name):
    return peer_id == name or peer_id.startswith(name + "-")


def _job_from_spec(spec, result_ref=None):
    return protocol.Job(
        spec["job_id"],
        spec["mode"],
        dict(spec["manifest"]),
        result_ref or spec["result_ref"],
        scope_ids=tuple(spec.get("scope_ids", ())),
    )


def _projection(result_ref):
    try:
        return MeshJobs.project_result(result_ref)
    except Exception as error:  # an unreadable result is a finding, not a crash
        return {"error": repr(error)}


def _semantic(projection):
    return {key: projection.get(key) for key in SEMANTIC_KEYS}


def _proved(projection):
    return projection.get("status") == "success-plan-found"


def _merge_record(spec, outcome, projection):
    """What the merge sees for one unit: scheduling bookkeeping plus the answer.

    `status` is the *proof's* status, not the transport's: the mesh reports a
    unit `ok` whenever it reached a terminal status (W2's rule that a result is
    not a failure), while the merge must only crown a unit that proved the goal.
    """
    return {
        "unit_id": spec["job_id"],
        "frontier_index": spec["manifest"]["frontier_index"],
        "digest": spec["manifest"]["digest"],
        "status": "ok" if (outcome or {}).get("status") == protocol.STATUS_OK and _proved(projection) else "failed",
        "mesh_status": (outcome or {}).get("status"),
        "peer_id": (outcome or {}).get("peer_id", ""),
        "stolen_from": (outcome or {}).get("stolen_from", ""),
        "projection": projection,
    }


def _run_swarm(results, directory, specs, worker_names, label, wait_timeout, kill_after_start=None):
    """Coordinator in-process, workers as CLI peers; returns a run report.

    `kill_after_start`, when given, is `(unit_id, delay)`: once the coordinator
    sees `job-started` for that unit, the worker that started it is SIGKILLed
    `delay` seconds later -- mid-unit, with the unit's boot or search underway.
    """
    coordinator = MeshModule.build_peer(MeshPeer.ROLE_COORDINATOR, MeshModule.ensure_identity(directory, "coordinator"))
    address = coordinator.start()
    workers = {}
    report = {
        "wall": None,
        "outcomes": {},
        "events": {},
        "summary": {},
        "killed": "",
        "worker_hwm_kib": {},
        "all_terminal": False,
    }
    try:
        for name in worker_names:
            workers[name] = _spawn_worker(directory, name, address)
        joined = coordinator.wait_for(lambda peer: all(_has_member(peer, name) for name in worker_names), timeout=60)
        results.check("%s: %d workers joined the mesh" % (label, len(worker_names)), joined, str(sorted(coordinator.members().keys())))
        if not joined:
            return report

        started = time.time()
        for spec in specs:
            coordinator.submit(_job_from_spec(spec, spec.get("run_result_ref")))

        if kill_after_start is not None:
            victim_unit, delay = kill_after_start
            saw_start = coordinator.wait_for(
                lambda peer: any(event.get("job_id") == victim_unit for event in peer.events("job-started")),
                timeout=120,
            )
            results.check("%s: victim unit %s started on a worker" % (label, victim_unit[:12]), saw_start)
            if saw_start:
                start_event = [event for event in coordinator.events("job-started") if event.get("job_id") == victim_unit][0]
                owner = start_event.get("peer_id", "")
                victim_name = next((name for name in worker_names if _peer_named(owner, name)), "")
                time.sleep(delay)
                if victim_name:
                    report["killed"] = victim_name
                    report["killed_peer_id"] = owner
                    _kill_process(workers[victim_name])
                    results.note("%s: SIGKILLed %s (%s) %.0fs after it started %s" % (label, victim_name, owner, delay, victim_unit[:12]))
                else:
                    results.check("%s: start event names a known worker" % label, False, owner)

        report["all_terminal"] = coordinator.wait_for_terminal([spec["job_id"] for spec in specs], timeout=wait_timeout)
        report["wall"] = time.time() - started
        for name, process in workers.items():
            report["worker_hwm_kib"][name] = _high_water_kib(process)
        for spec in specs:
            report["outcomes"][spec["job_id"]] = dict(coordinator.outcome(spec["job_id"]) or {})
        for event_name in ("job-started", "job-result", "job-redispatched", "member-lost", "result-superseded", "dispatch-error"):
            report["events"][event_name] = [dict(event) for event in coordinator.events(event_name)]
        report["summary"] = dict(coordinator.summary())
        return report
    finally:
        try:
            coordinator.shutdown(timeout=10)
        except Exception as error:
            results.note("%s: coordinator shutdown raised %r" % (label, error))
        for process in workers.values():
            _terminate(process)
        for process in workers.values():
            _kill_process(process)


# ---------------------------------------------------------------- phase: plan


def phase_plan(results, directory, plan_dir):
    print("\n[phase 0] plan: expand once, ship units", flush=True)
    if plan_dir is None:
        plan_dir = os.path.join(directory, "plan")
        returncode, wall = _run_main(
            ["swarm", "--role", "plan", "--out", plan_dir, "--problem", PROBLEM, "--burst", str(BURST_STEPS), "--shards", str(SHARD_COUNT)],
            os.path.join(directory, "plan.log"),
            PLAN_TIMEOUT,
        )
        results.check("plan subprocess exited 0", returncode == 0, "rc=%s in %.1fs" % (returncode, wall))
        results.note("plan (pack boot + %d-step expansion + %d snapshots) took %.1fs" % (BURST_STEPS, EXPECTED_FRONTIER + 1, wall))
    else:
        results.note("re-using plan directory %s" % plan_dir)
    plan_path = os.path.join(plan_dir, "plan.json")
    if not results.check("plan.json written", os.path.exists(plan_path), plan_path):
        return None
    with open(plan_path, encoding="utf-8") as handle:
        plan = json.load(handle)
    jobs = plan.get("jobs", [])

    results.check("plan reports an exact partition", plan.get("exact") is True, str(plan.get("exact")))
    results.check(
        "frontier size is %d with one unit per node" % EXPECTED_FRONTIER,
        plan.get("frontier_size") == EXPECTED_FRONTIER and len(jobs) == EXPECTED_FRONTIER,
        "frontier_size=%s jobs=%d" % (plan.get("frontier_size"), len(jobs)),
    )
    results.check(
        "shard sizes sum to the frontier",
        sum(plan.get("shard_sizes", [])) == plan.get("frontier_size") and len(plan.get("shard_sizes", [])) == SHARD_COUNT,
        str(plan.get("shard_sizes")),
    )

    indices = [spec["manifest"]["frontier_index"] for spec in jobs]
    digests = [spec["manifest"]["digest"] for spec in jobs]
    results.check("coverage: indices are exactly 0..n-1", sorted(indices) == list(range(len(jobs))), str(indices))
    results.check("disjointness: no digest names two units", len(set(digests)) == len(digests), ", ".join(d[:10] for d in digests))
    results.check(
        "unit ids are derived from index and digest",
        all(spec["job_id"] == "unit-%03d-%s" % (spec["manifest"]["frontier_index"], spec["manifest"]["digest"][:10]) for spec in jobs),
    )
    results.check(
        "shard assignment is shard_of(digest, %d)" % SHARD_COUNT,
        all(spec["manifest"]["shard"] == swarm.shard_of(spec["manifest"]["digest"], SHARD_COUNT) for spec in jobs),
    )
    results.check(
        "scope ids follow the unit digest",
        all(spec.get("scope_ids") == ["swarm-" + spec["manifest"]["digest"][:16]] for spec in jobs),
    )
    results.check(
        "every unit snapshot and the baseline exist",
        all(os.path.exists(spec["manifest"]["unit_path"]) for spec in jobs) and os.path.exists(plan.get("baseline", "")),
    )

    # Resharding never changes the set of units: for every k the shards are a
    # partition of the same digests, so a different worker count is only a
    # different first offer, never a different search.
    reshard_ok = True
    for shard_count in range(1, 5):
        buckets = {}
        for digest in digests:
            shard = swarm.shard_of(digest, shard_count)
            if not 0 <= shard < shard_count:
                reshard_ok = False
            buckets.setdefault(shard, []).append(digest)
        if sorted(sum(buckets.values(), [])) != sorted(digests):
            reshard_ok = False
    results.check("resharding k=1..4 is a bijection onto the same units", reshard_ok)
    try:
        swarm.shard_of(digests[0], 0)
        results.check("shard_of rejects a zero shard count", False)
    except ValueError:
        results.check("shard_of rejects a zero shard count", True)

    with open(plan["baseline"], encoding="utf-8") as handle:
        baseline_header = json.load(handle).get("header", {})
    unit_headers = []
    for spec in jobs:
        with open(spec["manifest"]["unit_path"], encoding="utf-8") as handle:
            unit_headers.append(json.load(handle).get("header", {}))
    results.check(
        "unit snapshots carry the baseline's format version",
        all(header == baseline_header for header in unit_headers) and "version" in baseline_header,
        str(baseline_header),
    )
    plan["_dir"] = plan_dir
    return plan


# ----------------------------------------------------------- phase: partition


def phase_partition(results, plan):
    print("\n[phase 1] partition: reproduce the plan's keys in this process", flush=True)
    from cat_theo_machine import main as MA

    started = time.time()
    runtime, graph, registry, job = swarm.read_unit(plan["baseline"], MA._runtime_namespace())
    boot_seconds = time.time() - started
    results.note("baseline snapshot booted in-process in %.1fs" % boot_seconds)
    frontier = M.SearchJobFrontier(job)()
    size_before = swarm.size_of(frontier)
    units, size = swarm.partition_frontier(frontier, registry, SHARD_COUNT)
    again, _size_again = swarm.partition_frontier(frontier, registry, SHARD_COUNT)

    results.check("frontier in the baseline has %d nodes" % EXPECTED_FRONTIER, size == EXPECTED_FRONTIER == size_before, "size=%d" % size)
    results.check("partition_is_exact holds on the recomputed units", swarm.partition_is_exact(units, size))
    planned = [(spec["manifest"]["frontier_index"], spec["manifest"]["digest"], spec["manifest"]["shard"], spec["job_id"]) for spec in plan["jobs"]]
    recomputed = [(unit.frontier_index, unit.digest, unit.shard, unit.unit_id) for unit in units]
    results.check(
        "digests, shards and ids equal the plan computed in another process",
        recomputed == planned,
        "; ".join("%d:%s" % (index, digest[:10]) for index, digest, _shard, _unit in recomputed),
    )
    results.check("partitioning twice gives identical units (no mutation)", [u.digest for u in again] == [u.digest for u in units] and swarm.size_of(frontier) == size_before)

    # Purity boundary (DAG §5.2): nodes stay machine values; only the bookkeeping
    # that has no machine analogue -- a hash of a rendering -- is Python.
    nodes_are_machine = True
    rest = frontier
    while M.IdentityCompare(rest, M.EmptyList)() is M.false_value:
        state = M.Head(rest)()
        current = M.SearchStateCurrent(state)()
        if isinstance(state, (dict, list, tuple, str, int)) or isinstance(current, (dict, list, tuple, str, int)):
            nodes_are_machine = False
        if not isinstance(swarm.node_text(state, registry), str):
            nodes_are_machine = False
        rest = M.Tail(rest)()
    results.check("frontier nodes and their states are machine terms, texts are str", nodes_are_machine)
    results.check(
        "unit records hold only scheduling scalars (str/int)",
        all(all(isinstance(value, (str, int)) for value in unit.as_dict().values()) for unit in units),
    )
    results.check(
        "digest is sha256 of the canonical text and keys the shard",
        all(swarm.canonical_digest(unit.text) == unit.digest and len(unit.digest) == 64 for unit in units),
    )
    single = swarm.only_node(frontier, 2)
    results.check("only_node yields a one-node frontier holding the chosen node", swarm.size_of(single) == 1 and swarm.canonical_digest(swarm.node_text(M.Head(single)(), registry)) == units[2].digest)

    # Merge order-independence, over every permutation of a synthetic frontier
    # in which two units succeed: the lower index must win regardless of order.
    synthetic = [
        {"frontier_index": 0, "digest": "d0", "status": "failed"},
        {"frontier_index": 1, "digest": "d1", "status": "ok"},
        {"frontier_index": 2, "digest": "d2", "status": "failed"},
        {"frontier_index": 3, "digest": "d3", "status": "ok"},
    ]
    winners = set()
    orders = set()
    for permutation in itertools.permutations(synthetic):
        winner, ordered = swarm.merge(permutation)
        winners.add(winner["digest"] if winner else None)
        orders.add(tuple(record["digest"] for record in ordered))
    results.check("merge winner is the lowest successful index in all 24 orders", winners == {"d1"} and len(orders) == 1)
    results.check("merge of only failures has no winner", swarm.merge([synthetic[0], synthetic[2]])[0] is None)
    return {"boot_seconds": boot_seconds}


# ------------------------------------------------------------ phase: baseline


def phase_baseline(results, directory, plan):
    print("\n[phase 2] baseline: the whole frontier, alone, in its own process", flush=True)
    result_ref = os.path.join(directory, "baseline-result.json")
    returncode, wall = _run_main(
        ["--role", "worker", "swarm", plan["baseline"], result_ref, str(BASELINE_TIMEOUT)],
        os.path.join(directory, "baseline.log"),
        BASELINE_TIMEOUT,
    )
    results.check("baseline worker exited 0", returncode == 0, "rc=%s in %.1fs" % (returncode, wall))
    projection = _projection(result_ref) if os.path.exists(result_ref) else {}
    results.check("baseline proved the goal", _proved(projection), projection.get("status", "no result"))
    results.check(
        "baseline carries a plan digest and a proof-cost digest",
        projection.get("plan_digest", "-") != "-" and projection.get("proof_cost_digest", "-") != "-",
        "plan=%s cost=%s" % (projection.get("plan_digest", "-")[:16], projection.get("proof_cost_digest", "-")[:16]),
    )
    results.note("baseline wall %.1fs; children high-water so far %.0f MiB" % (wall, _children_high_water_mib()))
    return {"wall": wall, "projection": projection}


# --------------------------------------------------------------- phase: swarm


def phase_swarm(results, directory, plan, baseline):
    print("\n[phase 3] swarm: two mesh workers run the four units", flush=True)
    run_dir = os.path.join(directory, "run-a")
    os.makedirs(run_dir, exist_ok=True)
    specs = []
    for spec in plan["jobs"]:
        copy = dict(spec)
        copy["run_result_ref"] = os.path.join(run_dir, "result-%03d.json" % spec["manifest"]["frontier_index"])
        specs.append(copy)
    report = _run_swarm(results, run_dir, specs, ["worker-1", "worker-2"], "run A", SWARM_TIMEOUT)
    results.check("run A: every unit reached a terminal result", report["all_terminal"], "wall=%s" % (("%.1fs" % report["wall"]) if report["wall"] else "-"))
    if not report["all_terminal"]:
        return {"report": report, "records": [], "winner": None}

    records = []
    for spec in specs:
        outcome = report["outcomes"].get(spec["job_id"])
        projection = _projection(spec["run_result_ref"]) if os.path.exists(spec["run_result_ref"]) else {}
        records.append(_merge_record(spec, outcome, projection))
    results.check(
        "run A: the mesh reports every unit ok (a result is not a failure)",
        all(record["mesh_status"] == protocol.STATUS_OK for record in records),
        ", ".join("%d:%s" % (r["frontier_index"], r["mesh_status"]) for r in records),
    )
    results.check(
        "run A: every unit wrote a readable result",
        all("error" not in record["projection"] and record["projection"] for record in records),
    )
    result_counts = {}
    for event in report["events"]["job-result"]:
        result_counts[event.get("job_id")] = result_counts.get(event.get("job_id"), 0) + 1
    results.check("run A: exactly one job-result per unit", all(result_counts.get(spec["job_id"]) == 1 for spec in specs), str(sorted(result_counts.values())))
    results.check("run A: no member was lost", not report["events"]["member-lost"], str(report["summary"].get("redispatches")))

    winner, ordered = swarm.merge(records)
    reversed_winner, _ = swarm.merge(list(reversed(records)))
    results.check("run A: merge crowns the lowest-index proving unit", winner is not None and winner["frontier_index"] == 0, (winner or {}).get("unit_id", "none"))
    results.check("run A: merge is independent of arrival order", (winner or {}).get("unit_id") == (reversed_winner or {}).get("unit_id"))
    results.check(
        "run A: the other units report the same failure, not silence",
        all(record["status"] == "failed" and record["projection"].get("status") == "failure-search" for record in ordered[1:]),
        ", ".join(r["projection"].get("status", "?") for r in ordered[1:]),
    )
    if winner is not None:
        same_plan = winner["projection"].get("plan_digest") == baseline["projection"].get("plan_digest")
        same_cost = winner["projection"].get("proof_cost_digest") == baseline["projection"].get("proof_cost_digest")
        results.check(
            "swarm proof == baseline proof (plan digest)",
            same_plan and winner["projection"].get("plan_digest", "-") != "-",
            "%s vs %s" % (winner["projection"].get("plan_digest", "-")[:16], baseline["projection"].get("plan_digest", "-")[:16]),
        )
        results.check(
            "swarm proof == baseline proof (proof-cost digest)",
            same_cost,
            "%s vs %s" % (winner["projection"].get("proof_cost_digest", "-")[:16], baseline["projection"].get("proof_cost_digest", "-")[:16]),
        )
        results.check("swarm and baseline agree on every semantic key", _semantic(winner["projection"]) == _semantic(baseline["projection"]))

    steals = report["summary"].get("steals", 0)
    stolen = [record["unit_id"] for record in records if record["stolen_from"]]
    peers = sorted({record["peer_id"].rsplit("-", 1)[0] for record in records if record["peer_id"]})
    results.check("run A: both workers produced results", len(peers) == 2, ", ".join(peers))
    results.note("run A: steals=%s (%s), redispatches=%s" % (steals, ", ".join(stolen) or "none", report["summary"].get("redispatches")))
    speedup = baseline["wall"] / report["wall"] if report["wall"] else 0.0
    hwm = max(report["worker_hwm_kib"].values() or [0]) / 1024.0
    results.note(
        "speedup (baseline %.1fs / swarm %.1fs) = %.2fx on %d vCPU with 2 workers -- %s"
        % (baseline["wall"], report["wall"], speedup, os.cpu_count() or 0, "a real gain" if speedup > 1.05 else "flat or negative: reported, not tuned")
    )
    results.note("memory: worker high-water %.0f MiB each (max), largest child overall %.0f MiB" % (hwm, _children_high_water_mib()))
    results.check("speedup was measured and reported", speedup > 0.0, "%.2fx" % speedup)
    return {"report": report, "records": records, "winner": winner}


# ---------------------------------------------------------------- phase: kill


def phase_kill(results, directory, plan, run_a):
    print("\n[phase 4] kill: a worker dies mid-unit; the unit must not be lost", flush=True)
    run_dir = os.path.join(directory, "run-b")
    os.makedirs(run_dir, exist_ok=True)
    chosen = [spec for spec in plan["jobs"] if spec["manifest"]["frontier_index"] in (1, 2)]
    specs = []
    for spec in chosen:
        copy = dict(spec)
        copy["run_result_ref"] = os.path.join(run_dir, "result-%03d.json" % spec["manifest"]["frontier_index"])
        specs.append(copy)
    victim = specs[0]["job_id"]
    report = _run_swarm(results, run_dir, specs, ["worker-3", "worker-4"], "run B", KILL_RUN_TIMEOUT, kill_after_start=(victim, 3.0))
    results.check("run B: every unit still reached a terminal result", report["all_terminal"], "wall=%s" % (("%.1fs" % report["wall"]) if report["wall"] else "-"))
    killed_peer = report.get("killed_peer_id", "")
    lost = [event for event in report["events"]["member-lost"] if event.get("peer_id") == killed_peer]
    results.check("run B: the coordinator recorded member-lost for the killed worker", bool(lost), (lost[0].get("detail") if lost else "no event"))
    redispatched = [event for event in report["events"]["job-redispatched"] if event.get("job_id") == victim]
    results.check(
        "run B: the victim unit was re-dispatched, mid-job, not written off",
        bool(redispatched) and "mid-job" in redispatched[0].get("detail", ""),
        (redispatched[0].get("detail") if redispatched else "no event"),
    )
    outcome = report["outcomes"].get(victim, {})
    survivor = report["killed"] and ("worker-4" if report["killed"] == "worker-3" else "worker-3")
    results.check(
        "run B: the survivor handed in a real result for the victim unit",
        outcome.get("status") == protocol.STATUS_OK and bool(survivor) and _peer_named(outcome.get("peer_id", ""), survivor) and not outcome.get("provisional"),
        "%s by %s" % (outcome.get("status"), outcome.get("peer_id", "")),
    )
    results.check(
        "run B: no unit was lost silently (every outcome has a reason or a result)",
        all((report["outcomes"].get(spec["job_id"]) or {}).get("status") == protocol.STATUS_OK or (report["outcomes"].get(spec["job_id"]) or {}).get("reason") for spec in specs),
    )
    # A peer announces running work again whenever it refreshes membership, so
    # the ledger may hold several job-started entries per start; the claim is
    # about *who* started it: the victim and then, after the loss, the survivor.
    starters = []
    for event in report["events"]["job-started"]:
        if event.get("job_id") == victim and event.get("peer_id") not in starters:
            starters.append(event.get("peer_id"))
    results.check(
        "run B: the lost unit was started by two distinct peers, victim first",
        len(starters) == 2 and starters[0] == killed_peer,
        " -> ".join(starters),
    )
    # The unit's answer does not depend on which peer ran it, in which run, or
    # after how many attempts: compare run B's projections with run A's.
    by_id = {record["unit_id"]: record for record in run_a.get("records", [])}
    agree = []
    for spec in specs:
        projection = _projection(spec["run_result_ref"]) if os.path.exists(spec["run_result_ref"]) else {}
        earlier = by_id.get(spec["job_id"], {}).get("projection", {})
        agree.append((spec["job_id"][:12], bool(earlier) and _semantic(projection) == _semantic(earlier), projection.get("status")))
    results.check(
        "run B: each unit's result equals the same unit's result in run A",
        all(flag for _unit, flag, _status in agree),
        "; ".join("%s:%s" % (unit, "same" if flag else "differs(%s)" % status) for unit, flag, status in agree),
    )
    winner_b, _ordered_b = swarm.merge(
        [_merge_record(spec, report["outcomes"].get(spec["job_id"]), _projection(spec["run_result_ref"])) for spec in specs if os.path.exists(spec["run_result_ref"])]
    )
    winner_a_subset, _ = swarm.merge([record for record in run_a.get("records", []) if record["frontier_index"] in (1, 2)])
    results.check("run B: merge over the same units agrees with run A (no proof among them)", winner_b is None and winner_a_subset is None)
    results.note("run B: wall %.1fs, redispatches=%s, steals=%s" % (report["wall"] or 0.0, report["summary"].get("redispatches"), report["summary"].get("steals")))


# ------------------------------------------------------------------------ main


def main(argv):
    plan_dir = None
    if "--plan-dir" in argv:
        plan_dir = os.path.abspath(argv[argv.index("--plan-dir") + 1])
    results = Results()
    directory = tempfile.mkdtemp(prefix="hyge-test27-")
    suite_started = time.time()
    print("test27: distributed prover swarm (W16); artifacts in %s" % directory, flush=True)
    try:
        plan = phase_plan(results, directory, plan_dir)
        if plan is None:
            raise RuntimeError("no plan to test")
        phase_partition(results, plan)
        baseline = phase_baseline(results, directory, plan)
        run_a = phase_swarm(results, directory, plan, baseline)
        phase_kill(results, directory, plan, run_a)
    except Exception as error:
        results.check("suite ran to completion", False, repr(error))
        import traceback

        traceback.print_exc()
    finally:
        swept = _sweep_restore_scratch(suite_started)
        if swept:
            results.note("swept %d restore scratch dir(s) orphaned by the kill: %s" % (len(swept), ", ".join(swept)))
        keep = results.failed > 0 or os.environ.get("HYGE_TEST27_KEEP")
        if keep:
            print("artifacts kept in %s" % directory, flush=True)
        else:
            shutil.rmtree(directory, ignore_errors=True)
    print("\ntest27 summary: %d passed, %d failed, %.0fs" % (results.passed, results.failed, time.time() - suite_started), flush=True)
    for text in results.notes:
        print("  - " + text)
    print("test27: %s" % ("ALL PASS" if results.failed == 0 else "FAILURES"), flush=True)
    return 0 if results.failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
