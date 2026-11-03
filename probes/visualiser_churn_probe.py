"""Diagnostic: load every pack, one at a time, and report any removal the reader
would see. Run from anywhere with PYTHONPATH=/home/user:

    python probes/visualiser_churn_probe.py

It prints one line per pack per poll; total removed must be 0. This is the
measurement behind section 4 of verification/visualiser-round2-2026-11-03.log.
"""
import os, sys, glob
sys.path.insert(0, "/home/user")
from cat_theo_machine import machine as M
from cat_theo_machine.runtime import make_fresh_runtime
from cat_theo_machine.visualiser.events import GraphDigest
import cat_theo_machine.main as main_module

runtime = make_fresh_runtime(); graph = runtime.graph
digest = GraphDigest(graph, runtime=runtime, rule_cap=400)
prev = ({}, {})
total_removed = 0
for path in sorted(glob.glob("/home/user/cat_theo_machine/packs/*.pack.yaml")):
    runtime.load_pack(path, main_module._runtime_namespace())
    for tick in ("after load", "quiet"):
        read = digest.read()
        nodes, edges = read["nodes"], read["edges"]
        gone = [k for k in prev[0] if k not in nodes] + [k for k in prev[1] if k not in edges]
        total_removed += len(gone)
        print("%-26s %-11s nodes=%4d edges=%4d removed=%d %s" % (
            os.path.basename(path), tick, len(nodes), len(edges), len(gone), gone[:2]))
        prev = (nodes, edges)
print("total removed across all pack loads:", total_removed)
