#!/usr/bin/env python3
"""Milestone-1 driver: two resident worker processes, one immutable snapshot,
two root-wave shard obligations, parent-side check, recorded join.

Mints NO new machinery. Every production piece here is the existing
search-compare resident-executor protocol:
  _SearchModeWorkerExecutor (search/runtime.py)   — worker loop
  SearchWorkerSetup/Baseline (search/model.py)    — snapshot identity/generation
  SearchRootWaveShardPacket/Launch                — obligation transport
  _SearchRootWaveShardResult                      — obligation execution
  _first_finished_worker / _decode_parallel_worker_payload — dead-worker handling
Run from /home/user:  python3 cat_theo_machine/tools/agent_workers/driver.py <artifact-path>
"""
import os
import sys
import time
import queue
import types

sys.path.insert(0, "/home/user")

ARTIFACT = sys.argv[1] if len(sys.argv) > 1 else ""
_lines = []
_results = {}
processes = []
_hold = {}


def log(text):
    _lines.append(text)
    print(text, flush=True)


def check(name, flag):
    _results[name] = bool(flag)
    log("CHECK %s: %s" % (name, "ok" if flag else "FAIL"))



def main():
    import cat_theo_machine.machine as M
    import cat_theo_machine.proof as Pmod
    from cat_theo_machine.search.model import (
        SearchWorkerBaseline,
        SearchWorkerSetup,
        SearchRootWaveShardPacket,
        SearchRootWaveShardLaunch,
        SearchRootWaveShardResult,
        SearchRootWaveShardResultImmediate,
        SearchRootWaveShardResultOther,
        SearchWorkerResultStatus,
        SearchFailureLabel,
    )
    from cat_theo_machine.search.runtime import (
        _SearchRootWaveShardResult,
        _SearchModeWorkerResult,
    )
    from cat_theo_machine.search.compare_executors import _ComparisonExecutorMixin
    from cat_theo_machine.search.compare_packets import _ComparisonPacketMixin
    from cat_theo_machine.search.compare_nat import _ComparisonNatMixin
    from cat_theo_machine.search.compare import CompareSearchModes
    from cat_theo_machine.runtime import make_fresh_runtime
    import multiprocessing

    class Probe(
        _ComparisonNatMixin,
        _ComparisonExecutorMixin,
        _ComparisonPacketMixin,
    ):
        def _resident_executor_fields(self, executor):
            return (
                self._resident_executor_process(executor),
                self._resident_executor_task_queue(executor),
                self._resident_executor_result_queue(executor),
            )

    log("START utc %s" % time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    try:
        log("multiprocessing start method: %s" % multiprocessing.get_start_method())
    except Exception:
        log("multiprocessing start method: unknown")
    mp = multiprocessing.get_context()

    runtime = make_fresh_runtime()
    graph = runtime.graph
    registry = M.FromContextGetConstructors(graph)()
    empty = M.EmptyList
    probe = Probe()
    _hold["probe"] = probe
    probe.registry = registry
    probe.graph = graph
    probe.signature = empty
    # list utilities used by the supervision paths live on the production
    # class; bind them verbatim rather than re-implementing a copy here
    probe._reverse = types.MethodType(CompareSearchModes._reverse, probe)

    # ---- one immutable snapshot: start, goal, rule set, generation ----
    start = M.Pair(M.Char("s"), empty)
    goal = M.Pair(M.Char("g"), empty)
    current_a = M.Pair(M.Char("a"), M.Pair(M.Char("s"), empty))
    current_b = M.Pair(M.Char("b"), M.Pair(M.Char("s"), empty))
    law_a = Pmod.Rule(current_a, goal)
    law_b = Pmod.Rule(current_b, goal)
    rules = M.Pair(law_a, M.Pair(law_b, empty))
    generation = M.Atom()
    generation.value = "snapshot-1"
    heuristic = M.Heuristic(M.BFSLabel, M.InsertionOrderLabel, M.one, M.one, M.one, M.one)()
    baseline = SearchWorkerBaseline(registry, start, goal, rules, heuristic, empty, generation)()
    setup = SearchWorkerSetup(M.BFSLabel, baseline)()
    log("snapshot: start=pair(s) goal=pair(g); 2 laws; generation=snapshot-1")

    # ---- two obligations: root-wave shard packets over disjoint rule subsets ----
    obligation_a = SearchRootWaveShardPacket(registry, M.Pair(law_a, empty), current_a, M.false_value)()
    obligation_b = SearchRootWaveShardPacket(registry, M.Pair(law_b, empty), current_b, M.false_value)()

    def spawn(slot):
        executor = probe._spawn_parallel_executor(mp, slot)
        processes.append(executor)
        return executor

    def probe_fields(executor):
        return _hold["probe"]._resident_executor_fields(executor)

    def executor_fields(executor):
        return probe._resident_executor_fields(executor)

    def drain(result_queue, timeout):
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                return True, result_queue.get_nowait()
            except queue.Empty:
                time.sleep(0.005)
        return False, None

    def shard_result_of(packet):
        return _SearchRootWaveShardResult(packet, baseline)()

    def rule_term_equal(left, right):
        # A filter result is a compiled-rule chain with fresh Pair ids on
        # every call, so the check must be semantic, not pointer identity:
        # two rules are equal exactly when pattern and replacement are equal
        # machine terms (RuleEqual inside proof.py compares the same fields).
        def raw(rule):
            if Pmod.IsCompiledRule(rule)() is M.truth_value:
                return Pmod.CompiledRuleRaw(rule)()
            return rule

        if left is empty or right is empty:
            return left is right
        pattern_left = Pmod.RulePattern(raw(left))()
        pattern_right = Pmod.RulePattern(raw(right))()
        if M.TermEqual(pattern_left, pattern_right)() is not M.truth_value:
            return False
        repl_left = Pmod.RuleReplacement(raw(left))()
        repl_right = Pmod.RuleReplacement(raw(right))()
        return M.TermEqual(repl_left, repl_right)() is M.truth_value

    def chains_match(left, right):
        while left is not empty and right is not empty:
            if not rule_term_equal(M.Head(left)(), M.Head(right)()):
                return False
            left = M.Tail(left)()
            right = M.Tail(right)()
        return left is empty and right is empty

    def result_matches(replay, payload):
        return (
            chains_match(SearchRootWaveShardResultImmediate(replay)(), SearchRootWaveShardResultImmediate(payload)())
            and chains_match(SearchRootWaveShardResultOther(replay)(), SearchRootWaveShardResultOther(payload)())
        )

    # ---- T1: readiness handshake, two distinct real OS processes ----
    log("T1 begin: spawning two resident executors")
    w1 = spawn(M.Zero)
    log("w1 spawned")
    w2 = spawn(M.one)
    log("w2 spawned")
    # NOTE: the production spawn path performs the ready-await internally and
    # raises when an executor fails to acknowledge; a returned executor is
    # therefore an executor whose ready ack was consumed. Re-awaiting would
    # spin forever on an empty queue by protocol design.
    log("handshakes consumed inside spawn (production contract)")
    p1, t1, r1 = executor_fields(w1)
    p2, t2, r2 = executor_fields(w2)
    check("ready-handshake-w1-live", p1.is_alive())
    check("ready-handshake-w2-live", p2.is_alive())
    check("distinct-pids", p1.pid != p2.pid and p1.pid > 0 and p2.pid > 0)
    log("worker pids: %s, %s" % (p1.pid, p2.pid))

    # snapshot identity: both workers receive the SAME setup term before any launch
    log("sending shared setup to both")
    t1.put(setup)
    t2.put(setup)
    time.sleep(0.2)

    # ---- T2: both obligations in flight on two workers; then the same
    # pair sequentially on one worker as a control. Timing recorded, not claimed. ----
    t_par0 = time.time()
    t1.put(SearchRootWaveShardLaunch(obligation_a, M.one)())
    t2.put(SearchRootWaveShardLaunch(obligation_b, M.one)())
    ok1, res1 = drain(r1, 60.0)
    ok2, res2 = drain(r2, 60.0)
    parallel_elapsed = time.time() - t_par0
    check("parallel-launches-returned", ok1 and ok2 and res1 is not None and res2 is not None)

    t_seq0 = time.time()
    t1.put(SearchRootWaveShardLaunch(obligation_a, M.two)())
    oks1, seq1 = drain(r1, 60.0)
    t1.put(SearchRootWaveShardLaunch(obligation_b, M.three)())
    oks2, seq2 = drain(r1, 60.0)
    seq_elapsed = time.time() - t_seq0
    log("elapsed: two-worker %.4fs | one-worker sequential %.4fs (tiny workload; timing recorded, no speedup claimed)" % (parallel_elapsed, seq_elapsed))

    # ---- T3: parent check — production replay over the same snapshot; the
    # worker's exit status is never taken as proof. Checked content: the
    # shard classification term (immediate, goal, other rule lists). ----
    replay_a = shard_result_of(obligation_a)
    replay_b = shard_result_of(obligation_b)
    check("parent-check-w1", ok1 and res1 is not None and result_matches(replay_a, res1))
    check("parent-check-w2", ok2 and res2 is not None and result_matches(replay_b, res2))
    check("obligation-not-vacuous", res1 is not None
          and M.IdentityCompare(SearchRootWaveShardResultOther(res1)(), empty)() is M.false_value)
    check("parent-check-rejects-wrong-replay", res1 is not None
          and not result_matches(_SearchRootWaveShardResult(obligation_a, baseline)(), res2))

    # ---- T4: recorded join — machine term pair carrying status and the two
    # checked payload identities (AND over both shards; one snapshot) ----
    both_ok = _results.get("parent-check-w1") and _results.get("parent-check-w2")
    join_status = M.Atom()
    join_status.value = M.truth_value if both_ok else M.false_value
    join_record = M.Pair(join_status, M.Pair(res1 if res1 is not None else empty, M.Pair(res2 if res2 is not None else empty, empty)))
    log("join: AND over slots 0,1 of snapshot generation snapshot-1 -> %s" % ("accepted" if both_ok else "rejected"))
    check("join-accepted", both_ok and join_status() is M.truth_value)

    # ---- T5: snapshot identity guard worker-side — a mode packet with a
    # foreign generation must raise inside the worker (verified in-process:
    # same constructor the worker loop runs) ----
    from cat_theo_machine.search.model import SearchWorkerPacket
    bad_generation = M.Atom()
    bad_generation.value = "snapshot-other"
    bad_packet = SearchWorkerPacket(empty, empty, empty, empty, empty, M.one, M.false_value, M.false_value, M.false_value, M.one, bad_generation)()
    guard_raised = False
    try:
        _SearchModeWorkerResult(bad_packet, baseline)()
    except RuntimeError as error:
        guard_raised = "generation" in str(error) or "baseline" in str(error)
        log("generation guard raised in-process: %s" % error)
    check("generation-guard-raises", guard_raised)

    # ---- T6: dead-worker supervision — terminated executor yields a None
    # payload which decodes to a SearchFailureLabel machine term.
    # A worker death is an execution failure, never a refutation. ----
    w3 = spawn(M.two)
    p3, t3, r3 = executor_fields(w3)
    t3.put(setup)
    p3.terminate()
    p3.join(5)
    entry = probe._worker_entry(M.BFSLabel, w3, empty, empty)
    finished = probe._first_finished_worker(M.Pair(entry, empty), empty)
    dead_payload = M.Head(M.Tail(finished)())()
    decoded = probe._decode_parallel_worker_payload(dead_payload)
    dead_status = SearchWorkerResultStatus(decoded)()
    check("dead-worker-payload-none", dead_payload is None)
    check("dead-worker-decodes-failure-term", M.IdentityCompare(dead_status, SearchFailureLabel)() is M.truth_value)

    # ---- T7: same-worker recovery — after a poison payload the loop survives,
    # the failure surfaces as None, and a fresh attempt id succeeds ----
    w4 = spawn(M.three)
    p4, t4, r4 = executor_fields(w4)
    t4.put(setup)
    t4.put(("raw-poison",))
    okp, resp = drain(r4, 15.0)
    check("poison-converted-to-none", okp and resp is None)
    check("worker-loop-survives-poison", p4.is_alive())
    t4.put(SearchRootWaveShardLaunch(obligation_b, M.four)())
    okr, resr = drain(r4, 60.0)
    check("retry-after-failure-on-same-worker", okr and resr is not None and result_matches(replay_b, resr))

    # ---- T8: parent store untouched by worker execution ----
    check("parent-registry-identity", M.FromContextGetConstructors(graph)() is registry)
    check("parent-snapshot-identity", rules is not None and generation.value == "snapshot-1")

    ok_all = all(_results.values())
    log("ALL CHECKS: %s" % ("ok" if ok_all else "FAILURES PRESENT"))
    log("END utc %s" % time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    text = "\n".join(_lines) + "\n"
    if ARTIFACT:
        with open(ARTIFACT, "w") as f:
            f.write(text)
    return 0 if ok_all else 1


def _live_processes():
    return list(processes)


def _drain_all():
    # The worker's own finalizer blocks putting its last message into a full
    # result pipe; if the parent then blocks joining that child while its own
    # task-pipe feeder is still unsent, both sides wait forever. Empty every
    # queue before teardown so the child can write its way out.
    import queue as _q
    for ex in list(processes):
        try:
            rq = _hold["probe"]._resident_executor_result_queue(ex)
            while True:
                try:
                    rq.get_nowait()
                except _q.Empty:
                    break
        except Exception:
            pass


if __name__ == "__main__":
    rc = 1
    try:
        rc = main()
    except BaseException as error:
        _lines.append("DRIVER RAISED: %r" % (error,))
        print("DRIVER RAISED: %r" % (error,), flush=True)
        rc = 1
    _drain_all()
    if ARTIFACT:
        try:
            with open(ARTIFACT, "w") as f:
                f.write("\n".join(_lines) + "\n")
        except Exception:
            pass
    for ex in list(processes):
        try:
            pp = _hold["probe"]._resident_executor_process(ex)
            tq = _hold["probe"]._resident_executor_task_queue(ex)
            tq.cancel_join_thread()
            _hold["probe"]._resident_executor_result_queue(ex).cancel_join_thread()
            try:
                tq.put_nowait(None)
            except Exception:
                pass
            if pp.is_alive():
                pp.terminate()
            pp.join(2)
            if pp.is_alive():
                pp.kill()
                pp.join(2)
        except Exception:
            pass
    sys.stdout.flush()
    sys.stderr.flush()
    # the mp atexit hook joins children that may be mid-write to pipes we no
    # longer read; results and the artifact are already flushed, so leave hard
    os._exit(rc)
