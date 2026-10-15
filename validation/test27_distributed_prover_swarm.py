#!/usr/bin/env python3
"""TEST 27 — W16: a partitioned prover swarm over the W2 mesh.

What is asserted, and why each piece is here:

1. **Partitioning.** A frontier becomes one unit per node, with a digest-keyed
   shard assignment. Disjointness and coverage are asserted from the returned
   units (`partition_is_exact`), not assumed, and the partition function is
   checked for determinism and for insensitivity to shard count.
2. **Real work.** The units come from a real pack problem expanded by the real
   engine, and each unit is a snapshot a separate process can boot.
3. **Equality.** The merged result -- the lowest-index unit that proved
   anything -- must be the same proof as the unpartitioned search over the whole
   frontier. Compared through `networking.jobs.project_result`, so the comparison
   is of proofs rather than bytes.
4. **Nothing silently lost.** A worker is killed mid-unit. Every job must still
   reach a terminal record.
5. **Honest cost.** Wall clock and child high-water memory are measured and
   reported against the single-process baseline, whatever they turn out to be.

Transport caveat, measured and recorded in `search/distributed_engine.py`: a
snapshot round trip changes the plan a search goes on to find, though not what
the proof costs. So plan equality is asserted *within* one transport -- baseline
and units both booted from snapshots -- and proof-cost equality is asserted
across the partition. Asserting plan equality against a pack-booted search would
need two more ~85 s runs and would test the codec, not the swarm.
"""

from __future__ import annotations

import json
import os
import resource
import shutil
import subprocess
import sys
import threading
import time

PACKAGE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMPORT_ROOT = os.path.dirname(PACKAGE_ROOT)
if IMPORT_ROOT not in sys.path:
    sys.path.insert(0, IMPORT_ROOT)

from cat_theo_machine import machine as M
from cat_theo_machine import main as MA
from cat_theo_machine import mesh as MeshModule
from cat_theo_machine import proof as P
from cat_theo_machine.networking import jobs as MeshJobs
from cat_theo_machine.networking import protocol
from cat_theo_machine.networking.peer import MeshPeer
from cat_theo_machine.search import distributed_engine as swarm

PROBLEM = "engel_e2"
BURST_STEPS = 3
SHARD_COUNT = 2
WORKER_COUNT = 2


class Results:
    def __init__(self):
        self.passed = 0
        self.failed = 0

    def check(self, label, condition, detail=""):
        if condition:
            self.passed += 1
            print("  PASS  %-58s %s" % (label, detail))
        else:
            self.failed += 1
            print("  FAIL  %-58s %s" % (label, detail))
        return bool(condition)


def project(path):
    """The machine-semantic projection of a result snapshot."""
    from cat_theo_machine.networking.jobs import project_result

    try:
        return project_result(path)
    except Exception as error:  # a missing or unreadable result is itself a finding
        return {"status": "unreadable: %s" % error, "plan_digest": "-", "proof_cost_digest": "-"}


# ------------------------------------------------------------------- phase one


def phase_partition(results, directory):
    """Boot once, expand a real problem, and prove the partition is a partition."""
    print("\n[1] partitioning: disjointness, coverage, determinism")
    started = time.time()
    runtime, packs = MA.boot_from_packs(MA.PACK_PATHS, MA._runtime_namespace())
    graph = runtime.graph
    graph._search_disable_console = M.truth_value
    graph._search_disable_progress_ticker = M.false_value
    graph._search_stop_help_shown = M.truth_value
    graph._search_probe_disable_applicable_cache = M.false_value
    graph._search_probe_disable_applicable_shards = M.truth_value
    registry = M.FromContextGetConstructors(graph)()
    print("  booted in %.1fs" % (time.time() - started), flush=True)

    # A synthetic frontier first: it costs nothing, and it can carry the cases a
    # real frontier happens not to -- an empty frontier, and two nodes whose
    # canonical text is identical, which is what makes the digest a *key*.
    synthetic = M.EmptyList
    for name in ("alpha", "beta", "alpha", "gamma"):
        state = M.SearchState(M.Char(name), M.EmptyList, M.EmptyList, M.Zero)()
        synthetic = M.Pair(state, synthetic)
    units, size = swarm.partition_frontier(synthetic, registry, 2)
    digests = [unit.digest for unit in units]
    results.check(
        "a synthetic frontier partitions into one unit per node",
        swarm.partition_is_exact(units, size) and size == 4,
        "nodes=%d indices=%s" % (size, [unit.frontier_index for unit in units]),
    )
    results.check(
        "two nodes with the same canonical text get the same digest",
        len(set(digests)) == 3 and sorted(digests)[0] == sorted(digests)[1],
        "digests=%s" % [digest[:8] for digest in digests],
    )
    empty_units, empty_size = swarm.partition_frontier(M.EmptyList, registry, 3)
    results.check(
        "an empty frontier yields no units and no error",
        empty_units == [] and empty_size == 0,
        "units=%d" % len(empty_units),
    )
    same = True
    for shard_count in (1, 2, 3, 4):
        first, _size = swarm.partition_frontier(synthetic, registry, shard_count)
        second, _size2 = swarm.partition_frontier(synthetic, registry, shard_count)
        same = same and [unit.as_dict() for unit in first] == [unit.as_dict() for unit in second]
    results.check("re-partitioning is byte-identical for k=1..4", same)

    # Now the real thing: a real problem, expanded by the real engine.
    cases = [case for case in MA._theorem_agenda(packs, "all") if PROBLEM in case[0].lower()]
    results.check("the problem is on the agenda", bool(cases), "problem=%s" % PROBLEM)
    label, start, goal, _rules, _phi = cases[0]
    heuristic = MA._search_worker_mode_heuristic(runtime, "dfs", registry)
    start = P.NormalizeKnowledge(start, registry)()
    goal = P.NormalizeKnowledge(goal, registry)()
    rules = runtime.ordered_rules()
    job = swarm.root_job(start, goal, rules, heuristic, swarm.step_limit(graph, rules, registry))
    expanded_at = time.time()
    job, registry, units, size = swarm.expand_frontier(
        graph, job, registry, BURST_STEPS, shard_count=SHARD_COUNT
    )
    graph._replace_context(constructors=registry)
    print("  expanded in %.1fs" % (time.time() - expanded_at), flush=True)
    results.check(
        "a real problem leaves a frontier worth partitioning",
        size >= 2 and swarm.partition_is_exact(units, size),
        "problem=%s nodes=%d shards=%s" % (label, size, swarm.shard_sizes(units, SHARD_COUNT)),
    )
    results.check(
        "every shard assignment is in range",
        all(0 <= unit.shard < SHARD_COUNT for unit in units),
        "shards=%s" % sorted(set(unit.shard for unit in units)),
    )

    # Write the units out: one snapshot each, plus the unpartitioned baseline.
    frontier = M.SearchJobFrontier(job)()
    baseline_unit = os.path.join(directory, "baseline.json")
    swarm.write_unit(runtime, baseline_unit, MA._runtime_namespace(), job)
    unit_paths = []
    for unit in units:
        path = os.path.join(directory, "unit-%03d.json" % unit.frontier_index)
        node = swarm.only_node(frontier, unit.frontier_index)
        swarm.write_unit(runtime, path, MA._runtime_namespace(), swarm.rebuild_job(job, node))
        unit_paths.append(path)
    results.check(
        "every unit is written, and each is smaller than the whole frontier",
        all(os.path.exists(path) for path in unit_paths)
        and all(os.path.getsize(path) < os.path.getsize(baseline_unit) for path in unit_paths),
        "units=%s baseline=%d" % (len(unit_paths), os.path.getsize(baseline_unit)),
    )
    return {
        "runtime": runtime,
        "label": label,
        "units": units,
        "unit_paths": unit_paths,
        "baseline_unit": baseline_unit,
        "frontier_size": size,
    }


# ------------------------------------------------------------------- phase two


def phase_swarm(results, directory, plan):
    """Run the units over the mesh, kill a worker mid-unit, and merge."""
    print("\n[2] the swarm: dispatch, stealing, a killed worker, and the merge")
    cert_dir = os.path.join(directory, "certs")
    os.makedirs(cert_dir, exist_ok=True)
    jobs_path = os.path.join(directory, "jobs.json")
    entries = []
    for unit, path in zip(plan["units"], plan["unit_paths"]):
        entries.append(
            {
                "job_id": unit.unit_id,
                "mode": "dfs",
                "result_ref": os.path.join(directory, "result-%03d.json" % unit.frontier_index),
                "manifest": {"unit_path": path, "frontier_index": unit.frontier_index, "digest": unit.digest},
                "scope_ids": ["swarm-" + unit.digest[:16]],
            }
        )
    with open(jobs_path, "w", encoding="utf-8") as handle:
        json.dump({"jobs": entries}, handle)

    # The unpartitioned baseline runs concurrently, in this process, on its own
    # booted-from-snapshot runtime: same transport as the units, so the
    # comparison below is inside one transport (see the module docstring).
    baseline_result = os.path.join(directory, "baseline-result.json")
    baseline_error = {}

    def run_baseline():
        try:
            MA.run_swarm_worker_mode(plan["baseline_unit"], baseline_result, 600)
        except Exception as error:
            baseline_error["error"] = repr(error)

    baseline_thread = threading.Thread(target=run_baseline, daemon=True)
    python = os.path.join(PACKAGE_ROOT, ".venv", "bin", "python")
    if not os.path.exists(python):
        python = sys.executable
    environment = dict(os.environ)
    environment["PYTHONPATH"] = IMPORT_ROOT
    coordinator_log = open(os.path.join(directory, "coordinator.log"), "w", encoding="utf-8")
    coordinator = subprocess.Popen(
        [
            python, "-u", os.path.join(PACKAGE_ROOT, "main.py"), "mesh",
            "--role", "coordinator", "--bind", "127.0.0.1:0",
            "--cert-dir", cert_dir, "--jobs", jobs_path, "--run-seconds", "360",
        ],
        stdout=coordinator_log, stderr=subprocess.STDOUT, cwd=IMPORT_ROOT, env=environment,
    )
    baseline_thread.start()
    time.sleep(10)
    workers = []
    worker_logs = []
    for index in range(WORKER_COUNT):
        log = open(os.path.join(directory, "worker%d.log" % index), "w", encoding="utf-8")
        worker_logs.append(log)
        workers.append(
            subprocess.Popen(
                [
                    python, "-u", os.path.join(PACKAGE_ROOT, "main.py"), "mesh",
                    "--role", "worker", "--bind", "127.0.0.1:0",
                    "--cert-dir", cert_dir, "--cert-name", "swarm-%d" % index, "--swarm",
                ],
                stdout=log, stderr=subprocess.STDOUT, cwd=IMPORT_ROOT, env=environment,
            )
        )

    # Kill whichever worker picks up a unit first, mid-unit.
    victim = None
    victim_unit = ""
    deadline = time.time() + 120
    while time.time() < deadline and victim is None:
        time.sleep(2)
        for index in range(WORKER_COUNT):
            worker_logs[index].flush()
            with open(os.path.join(directory, "worker%d.log" % index), "r", encoding="utf-8") as handle:
                for line in handle:
                    if "running unit" in line:
                        victim = index
                        victim_unit = line.split("running unit")[-1].strip()
                        break
            if victim is not None:
                break
    killed_pid = None
    kill_time = time.time()
    if victim is not None:
        killed_pid = workers[victim].pid
        workers[victim].kill()
    print("  killed worker %s (pid %s) mid-unit %s" % (victim, killed_pid, victim_unit or "-"), flush=True)

    # Drain: every result must appear, or the run must end.
    expected = [entry["result_ref"] for entry in entries]
    drained = False
    deadline = time.time() + 300
    while time.time() < deadline:
        if all(os.path.exists(path) for path in expected):
            drained = True
            break
        if coordinator.poll() is not None:
            break
        time.sleep(5)
    baseline_thread.join(timeout=300)
    wall_clock = time.time() - phase_swarm.started
    for process in workers:
        if process.poll() is None:
            process.terminate()
    if coordinator.poll() is None:
        coordinator.terminate()
    coordinator.wait(timeout=60)
    coordinator_log.close()
    for log in worker_logs:
        log.close()
    child_memory_mb = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1024.0

    results.check("a worker was killed mid-unit", victim is not None and killed_pid is not None, "worker=%s" % victim)
    missing = [os.path.basename(path) for path in expected if not os.path.exists(path)]
    results.check(
        "every unit still produced a result after the kill",
        not missing,
        "missing=%s" % missing,
    )

    # The crash clause is asserted from what survives the kill, not from the
    # coordinator's own ledger: `mesh.write_state` runs on a clean shutdown and
    # this suite terminates the coordinator once the work is done, so reading the
    # ledger here would test shutdown ordering rather than the swarm. What has to
    # be true is observable on disk -- the unit the killed worker was running has
    # a result, written after the kill, which means somebody else finished it.
    killed_index = None
    if victim_unit:
        base = os.path.basename(victim_unit.split()[0])
        if base.startswith("unit-") and base.endswith(".json"):
            killed_index = int(base[len("unit-"):-len(".json")])
    killed_result = (
        os.path.join(directory, "result-%03d.json" % killed_index) if killed_index is not None else ""
    )
    results.check(
        "the killed worker's unit was finished by somebody else",
        bool(killed_result)
        and os.path.exists(killed_result)
        and os.path.getmtime(killed_result) >= kill_time,
        "unit=%s result=%s" % (victim_unit or "-", os.path.basename(killed_result) if killed_result else "-"),
    )
    summary = {}
    state_path = os.path.join(cert_dir, "peer-coordinator.json")
    if os.path.exists(state_path):
        with open(state_path, "r", encoding="utf-8") as handle:
            summary = json.load(handle).get("summary", {})

    # The merge: lowest frontier index that proved anything.
    records = []
    for unit, entry in zip(plan["units"], entries):
        projection = project(entry["result_ref"])
        proved = projection.get("status") == "success-plan-found"
        records.append(
            {
                "frontier_index": unit.frontier_index,
                "digest": unit.digest,
                "status": "ok" if proved else "failed",
                "plan": projection.get("plan_digest", "-"),
                "cost": projection.get("proof_cost_digest", "-"),
            }
        )
    winner, ordered = swarm.merge(records)
    baseline = project(baseline_result)
    results.check(
        "the unpartitioned baseline proved the goal",
        baseline.get("status") == "success-plan-found" and not baseline_error,
        "status=%s error=%s" % (baseline.get("status"), baseline_error.get("error", "")),
    )
    results.check(
        "the merge picks the lowest index that proved anything",
        winner is not None
        and winner["frontier_index"]
        == min(record["frontier_index"] for record in records if record["status"] == "ok"),
        "winner=%s order=%s" % (winner and winner["frontier_index"], [record["frontier_index"] for record in ordered]),
    )
    results.check(
        "the merged proof is the baseline's proof",
        winner is not None and winner["plan"] == baseline.get("plan_digest"),
        "merged=%s baseline=%s" % (winner and winner["plan"], baseline.get("plan_digest")),
    )
    proving_costs = set(record["cost"] for record in records if record["status"] == "ok")
    results.check(
        "the proof cost does not depend on how the work was split",
        len(proving_costs) == 1 and baseline.get("proof_cost_digest") in proving_costs,
        "costs=%s baseline=%s" % (sorted(proving_costs), baseline.get("proof_cost_digest")),
    )
    return {
        "wall_clock": wall_clock,
        "child_memory_mb": child_memory_mb,
        "summary": summary,
        "winner": winner,
        "baseline": baseline,
        "records": records,
    }


phase_swarm.started = 0.0


# ----------------------------------------------------------------- phase three


def phase_cli_and_cost(results, directory, plan, outcome):
    """The CLI path, and the speedup number reported honestly."""
    print("\n[3] the CLI worker, and what the partition actually cost")
    # The cheapest unit is a branch that fails fast, so the CLI is exercised for
    # the price of a snapshot boot rather than a full proof.
    loser = min(
        (record for record in outcome["records"] if record["status"] != "ok"),
        key=lambda record: record["frontier_index"],
        default=None,
    )
    if loser is not None:
        index = loser["frontier_index"]
        cli_result = os.path.join(directory, "cli-result-%03d.json" % index)
        python = os.path.join(PACKAGE_ROOT, ".venv", "bin", "python")
        if not os.path.exists(python):
            python = sys.executable
        environment = dict(os.environ)
        environment["PYTHONPATH"] = IMPORT_ROOT
        started = time.time()
        completed = subprocess.run(
            [
                python, os.path.join(PACKAGE_ROOT, "main.py"), "swarm",
                plan["unit_paths"][index], cli_result, "600", "--role", "worker",
            ],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            cwd=IMPORT_ROOT, env=environment, timeout=900,
        )
        elapsed = time.time() - started
        cli_projection = project(cli_result)
        mesh_projection = project(os.path.join(directory, "result-%03d.json" % index))
        results.check(
            "the CLI runs a unit on its own and writes a result",
            completed.returncode == 0 and not cli_projection.get("status", "").startswith("unreadable"),
            "rc=%s status=%s %.1fs" % (completed.returncode, cli_projection.get("status"), elapsed),
        )
        results.check(
            "the CLI and the mesh worker agree on the same unit",
            cli_projection.get("plan_digest") == mesh_projection.get("plan_digest")
            and cli_projection.get("proof_cost_digest") == mesh_projection.get("proof_cost_digest"),
            "cli=%s mesh=%s" % (cli_projection.get("plan_digest"), mesh_projection.get("plan_digest")),
        )
    else:
        results.check("a failing unit exists to exercise the CLI cheaply", False, "every unit proved the goal")

    print(
        "\n  cost, measured: swarm wall clock %.1fs for %d units over %d workers;"
        " child high-water memory %.0f MB"
        % (outcome["wall_clock"], len(outcome["records"]), WORKER_COUNT, outcome["child_memory_mb"]),
        flush=True,
    )
    results.check(
        "the swarm's cost is reported rather than hidden",
        outcome["wall_clock"] > 0 and outcome["child_memory_mb"] > 0,
        "wall=%.1fs memory=%.0fMB summary=%s"
        % (
            outcome["wall_clock"],
            outcome["child_memory_mb"],
            json.dumps(outcome["summary"], sort_keys=True),
        ),
    )


# ------------------------------------------------------------------------ main


def main():
    print("=== TEST 27: W16 partitioned prover swarm over the W2 mesh ===")
    started = time.time()
    results = Results()
    directory = os.path.join(
        os.environ.get("TMPDIR", "/tmp"), "hyge-test27-%d" % os.getpid()
    )
    os.makedirs(directory, exist_ok=True)
    timings = []
    try:
        for phase in (phase_partition, phase_swarm, phase_cli_and_cost):
            phase_started = time.time()
            if phase is phase_partition:
                plan = phase(results, directory)
            elif phase is phase_swarm:
                phase_swarm.started = phase_started
                outcome = phase(results, directory, plan)
            else:
                phase(results, directory, plan, outcome)
            timings.append((phase.__name__, round(time.time() - phase_started, 1)))
    finally:
        shutil.rmtree(directory, ignore_errors=True)
        print("\n  artifacts: %s (removed)" % directory)
    elapsed = time.time() - started
    print("\n  phase wall clock: %s" % ("  ".join("%s=%.1fs" % item for item in timings)))
    print("\n=== TEST 27 COMPLETE: %d passed, %d failed in %.1fs ===" % (results.passed, results.failed, elapsed))
    return 1 if results.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
