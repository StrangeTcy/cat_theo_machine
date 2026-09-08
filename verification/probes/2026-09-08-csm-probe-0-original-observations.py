#!/usr/bin/env python3
"""Consolidated reproduction of the original 2026-09-06 inspection
observations for the two red compare_search_modes tests.

Decides three things at the inspected base:
  1. identity semantics of TermEqual on freshly built literal terms
     (two fresh Char terms carrying the same symbol are NOT TermEqual);
  2. the snapshot-reuse gate chain for the matching checkpoint of the
     finds_reusable_worker_snapshot_dir fixture: the checkpoint writes,
     the loaded attempt is resume-ready with a non-empty worker_plan,
     yet the problem-match compare rejects it;
  3. the per-state conjuncts of the need-shared-root-wave gate for the
     fill_warms_resident_pool fixture: every fresh state passes all
     conjuncts except the packet-search phase.

Usage: python3 <this file> /path/to/cat_theo_machine
(the package directory of the checkout; its parent goes on sys.path)

Pinned base: arena/01a06542-cat-theo-machine @ b812db9
"""
import os
import shutil
import sys
import tempfile

PKG = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "cat_theo_machine")
sys.path.insert(0, os.path.dirname(PKG))

from cat_theo_machine import testsuite as T
from cat_theo_machine import machine as M
from cat_theo_machine.proof import Rule
from cat_theo_machine.main import _search_worker_checkpoint, _search_worker_mode_heuristic
import cat_theo_machine.proof as Pmod
import cat_theo_machine.search as Smod
from cat_theo_machine.search.serialization import SearchAttemptStatus
from cat_theo_machine.search.serialization import SearchRunningLabel
from cat_theo_machine.search.serialization import SearchPacketSearchPhaseLabel

empty = M.EmptyList

print("== 1. TermEqual identity semantics on fresh literals ==")
char_one = M.Char("s")
char_two = M.Char("s")
print("fresh Char('s') vs fresh Char('s') TermEqual:", M.TermEqual(char_one, char_two)() is M.truth_value)
print("fresh Char('s') vs itself TermEqual:        ", M.TermEqual(char_one, char_one)() is M.truth_value)
pair_one = M.Pair(char_one, empty)
pair_two = M.Pair(char_two, empty)
print("pairs over the two fresh Chars TermEqual:   ", M.TermEqual(pair_one, pair_two)() is M.truth_value)

print()
print("== 2. finds_reusable gate chain (matching checkpoint) ==")
runtime = T.make_fresh_runtime()
graph = runtime.graph
registry = T._registry(graph)
start = M.Pair(M.Char("s"), empty)
goal = M.Pair(M.Char("g"), empty)
heuristic = M.Heuristic(M.BFSLabel, M.GoalHeadOrderLabel, M.three, M.one, M.one, M.one)()
rules = M.Pair(Rule(start, goal), empty)
probe = T._CompareSearchModesProbe(graph, start, goal, rules, heuristic, registry)
work = tempfile.mkdtemp(prefix="csm-probe0-gates-")
try:
    run_dir = os.path.join(work, "snapshots", "search_compare", "run-1")
    os.makedirs(run_dir)
    worker_registry = T._registry(runtime.graph)
    worker_heuristic = _search_worker_mode_heuristic(runtime, "bfs", worker_registry)
    proof_cost = Pmod.ProofCost(M.Zero, M.Zero, M.Zero, M.Zero)()
    plan = M.Pair(M.Atom(), empty)
    cost_pair = Smod.BuildSearchCost(plan, M.one, M.Zero, M.one, Smod.SearchSuccessLabel, worker_registry)()
    search_cost = M.Head(cost_pair)()
    path = os.path.join(run_dir, "bfs.snapshot.json")
    probe._write_search_worker_manifest(path)
    _search_worker_checkpoint(
        runtime, path, start, goal, worker_heuristic, Smod.SearchSuccessLabel,
        M.EmptyList, proof_cost, search_cost, 1234, "running-derivation", plan,
    )
    print("checkpoint written beside manifest: ok")
    matched_pair = probe._search_worker_snapshot_matches_current_problem(M.BFSLabel, worker_heuristic, path)
    print("problem-match accepted:", M.Head(matched_pair)() is M.truth_value)
    attempt = M.Head(M.Tail(matched_pair)())()
    performance = M.Head(M.Tail(M.Tail(matched_pair)())())()
    print("loaded attempt status is success:",
          M.IdentityCompare(SearchAttemptStatus(attempt)(), Smod.SearchSuccessLabel)() is M.truth_value)
    print("loaded attempt is final: ", probe._loaded_worker_attempt_is_final(attempt) is M.truth_value)
    print("performance reason text: ", probe._performance_reason_text(performance))
    print("attempt is resume-ready: ", probe._partial_worker_attempt_is_resume_ready(attempt, performance, path) is M.truth_value)
    from cat_theo_machine.main import _runtime_namespace
    from cat_theo_machine.persistence import SnapshotCodec
    state = SnapshotCodec(_runtime_namespace()).load(path)
    worker_plan = state.roots.get("worker_plan", M.EmptyList)
    print("snapshot worker_plan non-empty:", M.Compare(worker_plan, M.EmptyList)() is M.false_value)
    print("scan returns reusable mappings:", probe._reusable_search_worker_result_paths(work))
finally:
    shutil.rmtree(work, ignore_errors=True)

print()
print("== 3. fill_warms need-wave conjuncts (fresh states) ==")
runtime_b = T.make_fresh_runtime()
graph_b = runtime_b.graph
registry_b = T._registry(graph_b)
start_b = M.Thingy()
goal_b = M.Atom()
heuristic_b = M.Heuristic(M.BFSLabel, M.InsertionOrderLabel, M.one, M.one, M.one, M.one)()
rules_b = M.Pair(Rule(start_b, goal_b), empty)
warm_probe = T._WarmRootWaveCompareProbe(graph_b, start_b, goal_b, rules_b, heuristic_b, registry_b)
warm_probe._comparison_machine_parallelism = M.one
states = warm_probe._comparison_states(warm_probe._mode_chain())
cursor = states
index = 0
while M.IdentityCompare(cursor, empty)() is M.false_value and index < 5:
    state = M.Head(cursor)()
    print("state " + str(index)
          + " running=" + str(warm_probe._comparison_state_status(state) is SearchRunningLabel)
          + " packet-phase=" + str(warm_probe._comparison_state_phase(state) is SearchPacketSearchPhaseLabel)
          + " active-zero=" + str(M.NatEq(warm_probe._comparison_state_active_packets(state), M.Zero, registry_b)() is M.truth_value)
          + " pending-empty=" + str(M.IdentityCompare(warm_probe._comparison_state_pending_packets(state), empty)() is M.truth_value)
          + " fresh-root-job=" + str(warm_probe._comparison_is_fresh_root_job(warm_probe._comparison_state_job(state)) is M.truth_value))
    cursor = M.Tail(cursor)()
    index = index + 1
print("need-wave over fresh states:", warm_probe._comparison_states_need_shared_root_wave(states) is M.truth_value)
filled = warm_probe._fill_parallel_workers(empty, empty, states, empty)
next_states = M.Head(filled)()
print("candidates-ready after direct fill:", warm_probe._comparison_shared_root_candidates_ready is M.truth_value)
print("need-wave after direct fill:      ",
      warm_probe._comparison_states_need_shared_root_wave(next_states) is M.truth_value)
