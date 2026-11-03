"""A Machine script that builds a hypergraph while it runs.

Run it yourself, in its own terminal. The visualiser does not start it, does not
orchestrate it and cannot stop it -- that separation is the point:

    python -m cat_theo_machine.visualiser.examples.machine_workload --delay 0.6

The script opts in to observation with ``observe(runtime)``, then does ordinary
Machine work: it builds Peano numbers through the machine's own arithmetic, adds
vertices through ``Hypergraph.add_node``, and adds hyperedges whose arguments are
machine terms. The observer watches the graph roots and appends what changed to
``visualiser/run/observed.jsonl``; the viewer reads that file.

Every vertex and edge here comes from the public Machine API, and every number
is computed by the machine (``NatFromRep``, ``ChainLength``), not by Python.
"""
import argparse
import os
import time

from cat_theo_machine import machine as M
from cat_theo_machine import playground as PG
from cat_theo_machine.runtime import make_fresh_runtime
from cat_theo_machine.visualiser.tap import observe

PACK_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "packs")

SMALL_PACKS = ("order-sign.pack.yaml", "arithmetic.pack.yaml")


def edge(relation, arguments):
    """Build a canonical hyperedge: Pair(relation, args...)."""
    built = M.EmptyList
    for term in reversed(arguments):
        built = M.Pair(term, built)
    return M.Pair(M.Char(relation), built)


def nat(runtime, registry, value):
    """A machine natural number, built by the machine's own constructor."""
    pair = M.NatFromRep(M.GMPRep(value), registry)()
    return M.Head(pair)(), M.Head(M.Tail(pair)())()


def step(delay, message):
    print("[workload] " + message, flush=True)
    if delay > 0:
        time.sleep(delay)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build a Machine hypergraph while the observer watches")
    parser.add_argument("--delay", type=float, default=0.6, help="pause between steps (seconds)")
    parser.add_argument("--rounds", type=int, default=8, help="how many growth rounds to run")
    parser.add_argument("--journal", default=None, help="observation journal path")
    parser.add_argument("--packs", action="store_true", help="also load two knowledge packs (slower start)")
    parser.add_argument("--no-observer", action="store_true", help="run without writing a journal")
    args = parser.parse_args(argv)

    runtime = make_fresh_runtime()
    graph = runtime.graph
    registry = M.FromContextGetConstructors(graph)()

    tap = None
    if not args.no_observer:
        tap = observe(
            runtime,
            journal_path=args.journal,
            interval=0.15,
            rule_cap=40,
            source_note="machine_workload.py",
        )
        print("[workload] observing to " + tap.journal_path, flush=True)

    if args.packs:
        for name in SMALL_PACKS:
            path = os.path.join(PACK_DIR, name)
            if os.path.exists(path):
                import cat_theo_machine.main as main_module

                runtime.load_pack(path, main_module._runtime_namespace())
                step(args.delay, "loaded pack " + name)

    point_a = graph.add_node(M.Char("point_a"))
    point_b = graph.add_node(M.Char("point_b"))
    circle_c = graph.add_node(M.Char("circle_c"))
    midpoint_m = graph.add_node(M.Char("midpoint_m"))
    step(args.delay, "declared four vertices")

    graph.add_edge(edge("LiesOn", [point_a, circle_c]))
    step(args.delay, "added a binary hyperedge LiesOn(point_a, circle_c)")

    graph.add_edge(edge("Between", [point_a, midpoint_m, point_b]))
    step(args.delay, "added a ternary hyperedge Between(point_a, midpoint_m, point_b)")

    graph.add_edge(edge("NullaryMark", []))
    step(args.delay, "added a nullary hyperedge NullaryMark()")

    two, registry = nat(runtime, registry, 2)
    graph.add_edge(edge("HasOrder", [midpoint_m, two]))
    step(args.delay, "added HasOrder(midpoint_m, 2) with a machine-computed natural")

    previous = None
    for index in range(1, args.rounds + 1):
        probe = graph.add_node(M.Char("probe_" + str(index)))
        value, registry = nat(runtime, registry, index)
        graph.add_edge(edge("Measures", [probe, value]))
        if previous is not None:
            graph.add_edge(edge("Follows", [previous, probe]))
        previous = probe
        step(args.delay, "round " + str(index) + ": probe_" + str(index) + " measured by the machine")

    chain = M.EmptyList
    for index in range(1, args.rounds + 1):
        chain = M.Pair(M.Char("probe_" + str(index)), chain)
    measured = PG.ChainLength(chain, registry)()
    measured_value = M.Head(measured)()
    measured_registry = M.Head(M.Tail(measured)())()
    graph.add_node(M.Pair(M.Char("ProbeChainLength"), M.Pair(measured_value, M.EmptyList)))
    step(args.delay, "recorded the machine-computed chain length " + str(M.NatRepOf(measured_value, measured_registry)()))

    if tap is not None:
        tap.stop("workload finished")
        print("[workload] journal closed: " + tap.journal_path, flush=True)
    print("[workload] done", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
