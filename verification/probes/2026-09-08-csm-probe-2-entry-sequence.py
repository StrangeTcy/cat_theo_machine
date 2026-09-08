#!/usr/bin/env python3
"""Focused check 2: is the fill_warms failure specific to the direct-call
fixture entry, or does it persist through the production entry order with
the shared-root mode setting enabled?

Production order (search/compare.py, resident path of _compare_all_modes):
  fresh states -> executor pool start and pre-fast-path grow ->
  _comparison_states_after_root_fast_paths (on a miss every running state
  moves to the packet-search phase) -> _fill_parallel_workers.

The shared-root mode setting is graph._search_compare_enable_shared_root_fast_paths;
it defaults to false everywhere in machine code, so the resident path (and
the fill) is entered only when it is set explicitly.

Part A: the red test's direct entry (fresh states straight to fill) on a
        miss-capable ruleset.
Part B: the production order on the same miss-capable ruleset.
Part C: the red test's own ruleset (goal immediately reachable) under the
        production order — it resolves in the fast path before packet
        search, so it cannot exercise the wave path at all.

Usage: python3 <this file> /path/to/cat_theo_machine

Pinned base: arena/01a06542-cat-theo-machine @ b812db9
"""
import os
import sys

PKG = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "cat_theo_machine")
sys.path.insert(0, os.path.dirname(PKG))

from cat_theo_machine import testsuite as T
from cat_theo_machine import machine as M
from cat_theo_machine.proof import Rule
from cat_theo_machine.search.serialization import SearchPacketSearchPhaseLabel

empty = M.EmptyList


def fresh_problem(rules):
    runtime = T.make_fresh_runtime()
    graph = runtime.graph
    registry = T._registry(graph)
    start = M.Thingy()
    goal = M.Atom()
    heuristic = M.Heuristic(M.BFSLabel, M.InsertionOrderLabel, M.one, M.one, M.one, M.one)()
    probe = T._WarmRootWaveCompareProbe(graph, start, goal, rules, heuristic, registry)
    probe._comparison_machine_parallelism = M.one
    return graph, probe


def report(tag, probe, states):
    print(tag + " need-wave:        ", probe._comparison_states_need_shared_root_wave(states) is M.truth_value)
    print(tag + " candidates-ready: ", probe._comparison_shared_root_candidates_ready is M.truth_value)


start = M.Thingy()
goal = M.Atom()
miss_rules = M.Pair(Rule(goal, start), empty)
hit_rules = M.Pair(Rule(start, goal), empty)

print("== A. direct entry (the red test's order), miss-capable ruleset ==")
graph_a, probe_a = fresh_problem(miss_rules)
states_a = probe_a._comparison_states(probe_a._mode_chain())
first_a = M.Head(states_a)()
print("A fresh-state phase is packet-search:", probe_a._comparison_state_phase(first_a) is SearchPacketSearchPhaseLabel)
report("A before fill:", probe_a, states_a)
filled_a = probe_a._fill_parallel_workers(empty, empty, states_a, empty)
next_a = M.Head(filled_a)()
print("A spawned during fill: ", probe_a._nat_text(probe_a.spawned))
report("A after fill: ", probe_a, next_a)
print("A next states need-wave:", probe_a._comparison_states_need_shared_root_wave(next_a) is M.truth_value)

print()
print("== B. production entry order, explicit mode setting, same ruleset ==")
graph_b, probe_b = fresh_problem(miss_rules)
graph_b._search_compare_enable_shared_root_fast_paths = M.truth_value
states_b = probe_b._comparison_states(probe_b._mode_chain())
probe_b._comparison_root_wave_idle_executors = empty
states_after_b = probe_b._comparison_states_after_root_fast_paths(states_b)
first_b = M.Head(states_after_b)()
print("B fast-path result:    ", probe_b._comparison_root_result_text(probe_b._comparison_state_root_fast_path_result(first_b)))
print("B phase is packet-search after fast paths:", probe_b._comparison_state_phase(first_b) is SearchPacketSearchPhaseLabel)
report("B before fill:", probe_b, states_after_b)
filled_b = probe_b._fill_parallel_workers(empty, empty, states_after_b, empty)
next_b = M.Head(filled_b)()
workers_b = M.Head(M.Tail(filled_b)())()
print("B spawned during fill: ", probe_b._nat_text(probe_b.spawned))
report("B after fill: ", probe_b, next_b)
print("B workers chain non-empty:", M.IdentityCompare(workers_b, empty)() is M.false_value)
print("B next states need-wave: ", probe_b._comparison_states_need_shared_root_wave(next_b) is M.truth_value)

print()
print("== C. the red test's own ruleset under the production order ==")
graph_c, probe_c = fresh_problem(hit_rules)
graph_c._search_compare_enable_shared_root_fast_paths = M.truth_value
states_c = probe_c._comparison_states(probe_c._mode_chain())
probe_c._comparison_root_wave_idle_executors = empty
states_after_c = probe_c._comparison_states_after_root_fast_paths(states_c)
first_c = M.Head(states_after_c)()
print("C fast-path result:    ", probe_c._comparison_root_result_text(probe_c._comparison_state_root_fast_path_result(first_c)))
print("C all states finished: ", probe_c._comparison_all_finished(states_after_c) is M.truth_value)
print("C phase is packet-search after fast paths:", probe_c._comparison_state_phase(first_c) is SearchPacketSearchPhaseLabel)
