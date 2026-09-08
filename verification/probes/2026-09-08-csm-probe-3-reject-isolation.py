#!/usr/bin/env python3
"""Focused check 3: when _search_worker_snapshot_matches_current_problem
REJECTS a snapshot, does the parent's active state stay unchanged?

At this base the matcher loads the snapshot BEFORE the compatibility
compares (search/compare_subprocess.py), and the loader merges the decoded
constructor registry into the parent and replaces the parent graph's
constructor context. This probe writes a real checkpoint from a second
runtime for a DIFFERENT problem (start and goal both differ), lets the
parent reject it, and then checks the parent's registry and graph context
by object identity.

Usage: python3 <this file> /path/to/cat_theo_machine

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

runtime = T.make_fresh_runtime()
graph = runtime.graph
registry = T._registry(graph)
empty = M.EmptyList

start = M.Pair(M.Char("s"), empty)
goal = M.Pair(M.Char("g"), empty)
heuristic = M.Heuristic(M.BFSLabel, M.GoalHeadOrderLabel, M.three, M.one, M.one, M.one)()
rules = M.Pair(Rule(start, goal), empty)
probe = T._CompareSearchModesProbe(graph, start, goal, rules, heuristic, registry)

work = tempfile.mkdtemp(prefix="csm-probe3-reject-")
try:
    other_runtime = T.make_fresh_runtime()
    other_start = M.Pair(M.Char("q"), empty)
    other_goal = M.Pair(M.Char("x"), empty)
    other_registry = T._registry(other_runtime.graph)
    other_heuristic = _search_worker_mode_heuristic(other_runtime, "bfs", other_registry)
    proof_cost = Pmod.ProofCost(M.Zero, M.Zero, M.Zero, M.Zero)()
    other_plan = M.Pair(M.Atom(), empty)
    cost_pair = Smod.BuildSearchCost(other_plan, M.one, M.Zero, M.one, Smod.SearchSuccessLabel, other_registry)()
    other_search_cost = M.Head(cost_pair)()
    path = os.path.join(work, "bfs.snapshot.json")
    _search_worker_checkpoint(
        other_runtime, path, other_start, other_goal, other_heuristic, Smod.SearchSuccessLabel,
        M.EmptyList, proof_cost, other_search_cost, 1234, "running-derivation", other_plan,
    )
    print("foreign-problem checkpoint written (distinct second runtime)")

    registry_before = probe.registry
    context_before = probe.graph.context
    matched_pair = probe._search_worker_snapshot_matches_current_problem(
        M.BFSLabel, probe._heuristic_for_mode(M.BFSLabel), path
    )
    matched = M.Head(matched_pair)() is M.truth_value
    registry_same = M.IdentityCompare(registry_before, probe.registry)() is M.truth_value
    context_same = M.IdentityCompare(context_before, probe.graph.context)() is M.truth_value

    print("matcher accepted the foreign problem:", matched)
    print("parent registry unchanged after rejection: ", registry_same)
    print("parent graph context unchanged after rejection:", context_same)
    if matched:
        print("UNEXPECTED: foreign problem accepted; probe fixture is wrong for this base.")
    elif registry_same and context_same:
        print("VERDICT: rejection left the parent's active state unchanged at this base.")
    else:
        print("VERDICT: rejection MUTATED the parent's active state at this base:")
        print("         the decoded registry was merged and the constructor context")
        print("         replaced BEFORE the compatibility compares ran.")
finally:
    shutil.rmtree(work, ignore_errors=True)
