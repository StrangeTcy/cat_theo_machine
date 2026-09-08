#!/usr/bin/env python3
"""Focused check 1: does the existing worker-result manifest text
distinguish two different problems when debug tracing is disabled?

_write_search_worker_manifest renders start_text/goal_text through
_debug_term, and DebugTerm (proof.py) returns the empty string whenever
DEBUG_TRACE_STATE is false, which is its default. If so, two probes
with different goals write identical manifest texts and the manifest
cannot serve as an equality key across processes.

Usage: python3 <this file> /path/to/cat_theo_machine

Pinned base: arena/01a06542-cat-theo-machine @ b812db9
"""
import json
import os
import shutil
import sys
import tempfile

PKG = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "cat_theo_machine")
sys.path.insert(0, os.path.dirname(PKG))

from cat_theo_machine import testsuite as T
from cat_theo_machine import machine as M
from cat_theo_machine.proof import Rule
from cat_theo_machine.proof import DEBUG_TRACE_STATE

runtime = T.make_fresh_runtime()
graph = runtime.graph
registry = T._registry(graph)
empty = M.EmptyList

start = M.Pair(M.Char("s"), empty)
goal_one = M.Pair(M.Char("g"), empty)
goal_two = M.Pair(M.Char("z"), empty)
heuristic = M.Heuristic(M.BFSLabel, M.GoalHeadOrderLabel, M.three, M.one, M.one, M.one)()
rules_one = M.Pair(Rule(start, goal_one), empty)
rules_two = M.Pair(Rule(start, goal_two), empty)

probe_one = T._CompareSearchModesProbe(graph, start, goal_one, rules_one, heuristic, registry)
probe_two = T._CompareSearchModesProbe(graph, start, goal_two, rules_two, heuristic, registry)

work = tempfile.mkdtemp(prefix="csm-probe1-manifest-")
try:
    path_one = os.path.join(work, "one.snapshot.json")
    path_two = os.path.join(work, "two.snapshot.json")
    probe_one._write_search_worker_manifest(path_one)
    probe_two._write_search_worker_manifest(path_two)
    with open(probe_one._search_worker_result_manifest_path(path_one), "r", encoding="utf-8") as handle:
        manifest_one = json.load(handle)
    with open(probe_two._search_worker_result_manifest_path(path_two), "r", encoding="utf-8") as handle:
        manifest_two = json.load(handle)

    print("debug trace enabled at run:", DEBUG_TRACE_STATE.value is M.truth_value)
    print("problem one start_text:", repr(manifest_one["start_text"]))
    print("problem one goal_text: ", repr(manifest_one["goal_text"]))
    print("problem two start_text:", repr(manifest_two["start_text"]))
    print("problem two goal_text: ", repr(manifest_two["goal_text"]))
    same_start = manifest_one["start_text"] == manifest_two["start_text"]
    same_goal = manifest_one["goal_text"] == manifest_two["goal_text"]
    print("start_text equal across the two problems:", same_start)
    print("goal_text equal across DIFFERENT goals:   ", same_goal)
    if same_start and same_goal:
        print("VERDICT: manifest text COLLAPSES different problems at this base;")
        print("         debug rendering is diagnostic output, not an identity key.")
    else:
        print("VERDICT: manifest text distinguishes the problems at this base.")
finally:
    shutil.rmtree(work, ignore_errors=True)
